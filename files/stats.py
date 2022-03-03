from threading import Lock

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