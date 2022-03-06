import threading
import logging

logger = logging.getLogger('logger')

class Task:
    def __init__(self, func, args=()):
        self.__func = func
        self.__args = args

    def call(self):
        self.__func(*self.__args)

class Worker(threading.Thread):
    def __init__(self, pool):
        threading.Thread.__init__(self)
        self.__pool = pool

    def run(self):
        while self.__pool.is_working():
            task = self.__pool.get_task()
            if task != None:
                try:
                    task.call()
                except Exception as e:
                    logger.exception(e)
                    logger.critical('Thread crashed!')

class WorkersPool:
    def __gen_threads(self, cnt):
        logger.debug('WorkersPool.__gen_threads({0}) started'.format(cnt))
        for id in range(cnt):
            worker = Worker(self)
            self.__threads.append(worker)
        logger.debug('WorkersPool.__gen_threads({0}) done'.format(cnt))

    def __init__(self, cnt):
        self.__lock = threading.Lock()
        self.__threads = []
        self.__tasks = []
        self.__is_working = False

        self.__gen_threads(cnt)

    def start(self):
        logger.debug('WorkersPool.start() started')
        self.__is_working = True
        for thread in self.__threads:
            thread.start()
        logger.debug('WorkersPool.start() done')

    def join(self):
        logger.debug('WorkersPool.join() started')
        self.__is_working = False
        for thread in self.__threads:
            thread.join()
        logger.debug('WorkersPool.join() done')

    def is_working(self):
        self.__lock.acquire()
        result = (self.__is_working or len(self.__tasks) > 0)
        self.__lock.release()
        return result

    def get_task(self):
        self.__lock.acquire()
        if len(self.__tasks) > 0:
            result = self.__tasks.pop()
        else:
            result = None
        self.__lock.release()
        return result

    def get_len(self):
        self.__lock.acquire()
        result = len(self.__tasks)
        self.__lock.release()
        return result

    def add_task(self, func):
        self.__lock.acquire()
        self.__tasks.append(func)
        self.__lock.release()