from files.auxiliary_tools import *
import random

class Target:
    def __init__(self, host, port, path, protocol):
        self.HOST = host
        self.PORT = port
        self.PATH = path
        self.PROTOCOL = protocol

    def __str__(self):
        return self.PROTOCOL + '://' + self.HOST + ':' + str(self.PORT) + self.PATH

class TargetManager:
    def __init__(self):
        self.__targets = list()

    def __str__(self):
        result = '['
        first = True
        for i in self.__targets:
            if first:
                first = False
            else:
                result += ', \n'
            result += str(i)
        return result + ']'

    def is_ip(str):
        data = str.split('.')
        if len(data) == 4:
            good = True
            for i in range(len(data)):
                try:
                    data[i] = int(data[i])
                    if not (0 <= data[i] and data[i] < 256):
                        good = False
                        break
                except:
                    good = False
                    break
            return good
        else:
            return False

    def create_target_from_url(url):
        if url[:8] == 'https://':
            url = url[8:]
            protocol = 'https'
        elif url[:7] == 'http://':
            url = url[7:]
            protocol = 'http'
        else:
            if TargetManager.is_ip(url.split('/')[0].split(':')[0]):
                protocol = 'unknown'
            else:
                protocol = 'http'
        
        tmp = url.split('/')[0].split(':')
        host = tmp[0]

        if len(tmp) == 1:
            if protocol == 'http':
                port = 80
            elif protocol == 'https':
                port = 443
        else:
            port = tmp[1]

        path = url.replace(url.split('/')[0], '', 1)

        if len(path) == 0:
            path = '/'

        print(host)
        print(port)
        print(path)
        print(protocol)
        return Target(host, port, path, protocol)

    def load_from_file(self, file_path):
        try:
            lines = load_lines(file_path)
            result = []
            for str in lines:
                result.append(TargetManager.create_target_from_url(str))
            self.__targets += result
        except:
            pass

    def get_rand(self):
        return random.choice(self.__targets)
