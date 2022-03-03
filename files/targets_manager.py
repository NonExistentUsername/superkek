from files.auxiliary_tools import *
import random
import traceback
import logging

console_log = logging.getLogger('console')
file_log = logging.getLogger('file')
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
                file_log.debug('Added target: ' + str(res))
                self.__targets.append(res)
    
    def load_from_file(self, file_path):
        try:
            lines = load_lines(file_path)
            self.load_from_list(lines)
        except OSError as err:
            console_log.critical("OS error: {0}".format(err))
        except Exception as e:
            console_log.exception(e)

    def get_rand(self):
        return random.choice(self.__targets)
