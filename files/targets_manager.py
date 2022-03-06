from files.auxiliary_tools import *
import random
import logging

logger = logging.getLogger('logger')

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

    def __len__(self):
        return len(self.__targets)

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
                except ValueError:
                    good = False
                    break
            return good
        else:
            return False

    def create_target_from_url(url):
        if len(url) == 0:
            return None
        url = url.lower()

        if url[:8] == 'https://':
            url = url[8:]
            protocol = 'https'
        elif url[:7] == 'http://':
            url = url[7:]
            protocol = 'http'
        elif url[:6] == 'tcp://':
            url = url[6:]
            protocol = 'tcp'
        elif url[:6] == 'udp://':
            url = url[6:]
            protocol = 'udp'
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
            elif protocol == 'udp':
                port = 53
            else:
                return None
        else:
            port = tmp[1]

        path = url.replace(url.split('/')[0], '', 1)

        if len(path) == 0:
            path = '/'

        return Target(host, port, path, protocol)


    def load_from_list(self, lines):
        for line in lines:
            res = TargetManager.create_target_from_url(line)
            if res != None:
                logger.debug('Added target: ' + str(res))
                self.__targets.append(res)
    
    def load_from_file(self, file_path):
        try:
            lines = load_lines(file_path)
            self.load_from_list(lines)
        except OSError as err:
            logger.critical("OS error: {0}".format(err))
        except Exception as e:
            logger.exception(e)

    def get_rand(self):
        return random.choice(self.__targets)
