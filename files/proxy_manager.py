import random
import requests
from threading import Lock
from files.workers_pool import *

console_log = logging.getLogger('console')
file_log = logging.getLogger('file')

class Node:
    def __init__(self, id, value = 0, left = None, right = None):
        self.left = left
        self.right = right
        self.id = id
        self.value = value

    def recalc(self):
        self.value = 0
        if self.left != None:
            self.value += self.left.value
        if self.right != None:
            self.value += self.right.value

    def build(self, l, r, value = 0):
        if l == r:
            return

        m = (l + r) // 2
        if self.left == None:
            self.left = Node(self.id * 2, value)
        self.left.build(l, m, value)
        if m + 1 <= r:
            if self.right == None:
                self.right = Node(self.id * 2 + 1, value)
            self.right.build(m + 1, r, value)

        self.recalc()

    def upd(self, l, r, pos, value):
        if l == r:
            self.value += value
            return
        
        m = (l + r) // 2
        if pos <= m:
            if self.left == None:
                self.left = Node(2 * self.id)
            self.left.upd(l, m, pos, value)
        else:
            if self.right == None:
                self.right = Node(2 * self.id + 1)
            self.right.upd(m + 1, r, pos, value)
        
        self.recalc()

    def get(self, l, r, tl, tr):
        if l > r or r < tl or tr < l:
            return 0
        if tl <= l and r <= tr:
            return self.value
        m = (l + r) // 2
        result = 0
        if self.left != None:
            result += self.left.get(l, m, tl, tr)
        if self.right != None:
            result += self.right.get(m + 1, r, tl, tr)
        return result

    def find(self, l, r, sum):
        if l == r:
            return l
        
        m = (l + r) // 2
        if self.left.value < sum and self.right != None:
            return self.right.find(m + 1, r, sum - self.left.value)
        else:
            return self.left.find(l, m, sum)

    def get_cnt(self, l, r, sum):
        if l == r:
            if self.value >= sum:
                return 1
            return 0
        
        m = (l + r) // 2
        result = 0
        if self.left != None:
            result += self.left.get_cnt(l, m, sum)
        if self.right != None:
            result += self.right.get_cnt(m + 1, r, sum)
        return result

class SumTree:
    def __init__(self, size):
        self.root = Node(1)
        self.root.build(1, size, 1)
        self.size = size

    def add_value(self, pos, value = 1):
        self.root.upd(1, self.size, pos, value)

    def find_pos(self, sum):
        return self.root.find(1, self.size, sum * self.root.get(1, self.size, 1, self.size))

    def get_cnt_good(self):
        return self.root.get_cnt(1, self.size, self.root.get(1, self.size, 1, self.size) // self.size)

class Proxy:
    def __init__(self, ip, port, type):
        self.IP = ip
        self.PORT = port
        self.TYPE = type

    def __str__(self):
        return '<' + self.TYPE + '>' + self.IP + ':' + self.PORT

class Checker:
    __links = ['https://dropbox.com/robots.txt', 'https://www.google.com/robots.txt']

    def __init__(self, config):
        self.__lock = Lock()
        self.__new_list = None
        self.__config = config
        self.__cnt_checked = 0

    def __add_good_proxy(self, proxy):
        self.__lock.acquire()
        self.__new_list.append(proxy)
        file_log.debug('Added proxy: {0}'.format(proxy))
        self.__lock.release()

    def __checked(self):
        self.__lock.acquire()
        self.__cnt_checked += 1
        self.__lock.release()

    def __check_simple(self, proxy_str):
        try:
            ip = proxy_str.split(':')[0]
            port = proxy_str.split(':')[1]
        except IndexError:
            file_log.debug('Bad line: {0}'.format(proxy_str))
            self.__checked()
            return

        for protocol in ['http', 'socks4', 'socks5']:
            proxy_dict = {
                'https': f'{protocol}://{proxy_str}',
                'http': f'{protocol}://{proxy_str}',
            }
            try:
                response = requests.get(random.choice(Checker.__links), proxies=proxy_dict, timeout = 2 * self.__config.TIMEOUT)
                if response.status_code == 200:
                    self.__add_good_proxy(Proxy(ip, port, protocol))
            except:
                pass
        self.__checked()

    def __print_progress(self, list_size, step = 5):
        checked = self.__cnt_checked
        total = 0
        console_log.info('Proxy checking progress: {0}%'.format(total))
        while checked < list_size:
            checked = self.__cnt_checked
            if checked / list_size * 100 >= total + step:
                total += step
                console_log.info('Proxy checking progress: {0}%'.format(total))

    def gen_good_list_from_lines(self, lines):
        self.__new_list = []
        pool = WorkersPool(max(100, self.__config.THREAD_COUNT))
        for i in lines:
            pool.add_task(Task(self.__check_simple, args=(i, )))
        progress_printing_thread = threading.Thread(target=self.__print_progress, args=(len(lines),))
        progress_printing_thread.start()
        pool.start()
        pool.join()
        progress_printing_thread.join()
        return self.__new_list

class ProxyManager:
    def __init__(self):
        self.__proxies = []

    def __str__(self):
        result = '['
        first = True
        for i in self.__proxies:
            if first:
                first = False
            else:
                result += ', \n'
            result += str(i)
        return result + ']'

    def __len__(self):
        return len(self.__proxies)

    def build_tree(self):
        file_log.debug('ProxyManager.build_tree start')
        self.__tree = SumTree(len(self.__proxies))
        self.__proxy_to_id = {}
        for i in range(len(self.__proxies)):
            self.__proxy_to_id[self.__proxies[i]] = i
        file_log.debug('ProxyManager.build_tree done')

    def get_good_proxies_count(self):
        return self.__tree.get_cnt_good()

    def add_good_connection(self, proxy):
        if proxy in self.__proxy_to_id:
            self.__tree.add_value(self.__proxy_to_id[proxy] + 1)

    def get_rand(self):
        # return random.choice(self.__proxies)
        r = random.random()
        id = self.__tree.find_pos(r)
        id -= 1
        return self.__proxies[id]

    def load_from_list(self, lines, config):
        lines = list(dict.fromkeys(lines))
        console_log.info('Proxy lines: {0}'.format(len(lines)))
        checker = Checker(config)
        good_proxies = checker.gen_good_list_from_lines(lines)
        self.__proxies += good_proxies

    def load_from_file(self, file_path, config):
        try:
            self.load_from_list(open(file_path, 'r').read().split('\n'), config)
        except OSError as err:
            console_log.critical("OS error: {0}".format(err))
        except Exception as e:
            console_log.exception(e)

