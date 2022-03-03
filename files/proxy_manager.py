import random
import requests
from threading import Lock
from files.workers_pool import *

console_log = logging.getLogger('console')
file_log = logging.getLogger('file')

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
        file_log.info('Added proxy: {0}'.format(proxy))
        self.__lock.release()

    def __checked(self):
        self.__lock.acquire()
        self.__cnt_checked += 1
        self.__lock.release()

    def __check_simple(self, proxy_str):
        ip = proxy_str.split(':')[0]
        port = proxy_str.split(':')[1]
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
        pool = WorkersPool(100)
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

    def get_rand(self):
        return random.choice(self.__proxies)

    def load_from_file(self, file_path, config):
        try:
            checker = Checker(config)
            good_proxies = checker.gen_good_list_from_lines(open(file_path, 'r').read().split('\n'))
            self.__proxies += good_proxies
        except OSError as err:
            console_log.critical("OS error: {0}".format(err))
        except Exception as e:
            console_log.exception(e)
