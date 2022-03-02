
class Config:
    def __init__(self, data):
        if 'THREAD_COUNT' in data:
            self.THREAD_COUNT = int(data['THREAD_COUNT'])
        if 'MAX_SIMPLE_CONNECTION_REQUESTS' in data:
            self.MAX_SIMPLE_CONNECTION_REQUESTS = int(data['MAX_SIMPLE_CONNECTION_REQUESTS'])
        if 'TIMEOUT' in data:
            self.TIMEOUT = float(data['TIMEOUT'])
        if 'ENABLE_CONSOLE_LOG' in data:
            if data['ENABLE_CONSOLE_LOG'].lower() == 'true':
                self.ENABLE_CONSOLE_LOG = True
            else:
                self.ENABLE_CONSOLE_LOG = False
        if 'CONSOLE_LOG_TIMEOUT' in data:
            self.CONSOLE_LOG_TIMEOUT = float(data['CONSOLE_LOG_TIMEOUT'])

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