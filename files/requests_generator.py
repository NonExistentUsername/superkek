
from files.auxiliary_tools import *
import random

class Requests:
    __userag = load_lines('resources/useragent.txt')

    __acpt = [
            "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\nAccept-Language: en-US,en;q=0.5\r\nAccept-Encoding: gzip, deflate\r\n",
            "Accept-Encoding: gzip, deflate\r\n",
            "Accept-Language: en-US,en;q=0.5\r\nAccept-Encoding: gzip, deflate\r\n",
            "Accept: text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8\r\nAccept-Language: en-US,en;q=0.5\r\nAccept-Charset: iso-8859-1\r\nAccept-Encoding: gzip\r\n",
            "Accept: application/xml,application/xhtml+xml,text/html;q=0.9, text/plain;q=0.8,image/png,*/*;q=0.5\r\nAccept-Charset: iso-8859-1\r\n",
            "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\nAccept-Encoding: br;q=1.0, gzip;q=0.8, *;q=0.1\r\nAccept-Language: utf-8, iso-8859-1;q=0.5, *;q=0.1\r\nAccept-Charset: utf-8, iso-8859-1;q=0.5\r\n",
            "Accept: image/jpeg, application/x-ms-application, image/gif, application/xaml+xml, image/pjpeg, application/x-ms-xbap, application/x-shockwave-flash, application/msword, */*\r\nAccept-Language: en-US,en;q=0.5\r\n",
            "Accept: text/html, application/xhtml+xml, image/jxr, */*\r\nAccept-Encoding: gzip\r\nAccept-Charset: utf-8, iso-8859-1;q=0.5\r\nAccept-Language: utf-8, iso-8859-1;q=0.5, *;q=0.1\r\n",
            "Accept: text/html, application/xml;q=0.9, application/xhtml+xml, image/png, image/webp, image/jpeg, image/gif, image/x-xbitmap, */*;q=0.1\r\nAccept-Encoding: gzip\r\nAccept-Language: en-US,en;q=0.5\r\nAccept-Charset: utf-8, iso-8859-1;q=0.5\r\n,"
            "Accept: text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8\r\nAccept-Language: en-US,en;q=0.5\r\n",
            "Accept-Charset: utf-8, iso-8859-1;q=0.5\r\nAccept-Language: utf-8, iso-8859-1;q=0.5, *;q=0.1\r\n",
            "Accept: text/html, application/xhtml+xml\r\n",
            "Accept-Language: en-US,en;q=0.5\r\n",
            "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\nAccept-Encoding: br;q=1.0, gzip;q=0.8, *;q=0.1\r\n",
            "Accept: text/plain;q=0.8,image/png,*/*;q=0.5\r\nAccept-Charset: iso-8859-1\r\n",
        ]

    __referers = load_lines('resources/referers.txt')

    def get_accept():
        return random.choice(Requests.__acpt)

    def get_useragent():
        return "User-Agent: " + random.choice(Requests.__userag) + "\r\n"

    def get_referer(url):
        return "Referer: " + random.choice(Requests.__referers) + url + "\r\n"

    def get_connect_request(target):
        return 'CONNECT ' + target.HOST + ':' + str(target.PORT) + ' HTTP/1.1\r\n\r\n'

    def get_extended_head(target):
        separator = "?"
        if "?" in target.PATH:
            separator = "&"
        get = "GET " + target.PROTOCOL + '://' + target.HOST + target.PATH + separator + str(random.randint(0, 20000)) + " HTTP/1.1\r\nHost: " + target.HOST + "\r\n"
        return get

    def get_simple_head(target):
        separator = "?"
        if "?" in target.PATH:
            separator = "&"
        get = "GET " + target.PATH + separator + str(random.randint(0, 20000)) + " HTTP/1.1\r\nHost: " + target.HOST + "\r\n"
        return get

    def gen_http_request(target, head=None):
        connection = "Connection: Keep-Alive\r\n"
        headers = Requests.get_referer(target.HOST + target.PATH) + \
                    Requests.get_useragent() + \
                    Requests.get_accept() + \
                    connection + "\r\n"
        if head == None:
            head = Requests.get_simple_head(target)
        return head + headers
