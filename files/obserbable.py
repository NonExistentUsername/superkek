from threading import Lock

class Observable:
    def __init__(self):
        self.__lock = Lock()
        self.__observer_list = []

    def add_observer(self, observer):
        self.__lock.acquire()
        if not observer in self.__observer_list:
            self.__observer_list.append(observer)
        self.__lock.release()

    def remove_observer(self, observer):
        self.__lock.acquire()
        self.__observer_list.remove(observer)
        self.__lock.release()

    def notify(self, message):
        self.__lock.acquire()
        for observer in self.__observer_list:
            observer.notify(message)
        self.__lock.release()