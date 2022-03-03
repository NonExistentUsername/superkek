import logging

console_log = logging.getLogger('console')
file_log = logging.getLogger('file')

class Config:
    def __load_config(self, data):
        if 'THREAD_COUNT' in data:
            self.THREAD_COUNT = int(data['THREAD_COUNT'])
            file_log.debug('Config loaded THREAD_COUNT {0}'.format(self.THREAD_COUNT))
        if 'MAX_SIMPLE_CONNECTION_REQUESTS' in data:
            self.MAX_SIMPLE_CONNECTION_REQUESTS = int(data['MAX_SIMPLE_CONNECTION_REQUESTS'])
            file_log.debug('Config loaded MAX_SIMPLE_CONNECTION_REQUESTS {0}'.format(self.MAX_SIMPLE_CONNECTION_REQUESTS))
        if 'TIMEOUT' in data:
            self.TIMEOUT = float(data['TIMEOUT'])
            file_log.debug('Config loaded TIMEOUT {0}'.format(self.TIMEOUT))
        if 'CONSOLE_LOG_TIMEOUT' in data:
            self.CONSOLE_LOG_TIMEOUT = float(data['CONSOLE_LOG_TIMEOUT'])
            file_log.debug('Config loaded CONSOLE_LOG_TIMEOUT {0}'.format(self.CONSOLE_LOG_TIMEOUT))

    def __init__(self, data):
        self.MAX_SIMPLE_CONNECTION_REQUESTS = 20
        self.THREAD_COUNT = 20
        self.TIMEOUT = 2.0
        self.CONSOLE_LOG_TIMEOUT = 60.0

        self.__load_config(data)

def load_config(file_path = 'config.txt'):
    result = {}
    try:
        lines = open(file_path, 'r').read().split('\n')
        for i in lines:
            i = i.replace(' ', '')
            i = i.split('=')
            if len(i) == 2:
                result[i[0]] = i[1]
    except OSError as err:
        print("OS error while loading config: {0}".format(err))
    return Config(result)