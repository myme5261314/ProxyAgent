#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright ©  2016
# Peng Liu, <myme5261314@gmail.com>
#
# Distributed under terms of the gplv3 license.

"""

"""


import re
import socket
import asyncio
import warnings
from math import sqrt
from html import unescape
from base64 import b64decode
from urllib.parse import unquote, urlparse
import logging
import concurrent

import aiohttp

# from .errors import *
# from .utils import log, get_headers, IPPattern, IPPortPatternGlobal
# from .resolver import Resolver

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, sdch",
    "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36",
}

IPPattern = re.compile(
    r'(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)')

IPPortPatternLine = re.compile(
    r'^.*?(?P<ip>(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)).*?(?P<port>[1-9]\d{1,4}).*$',
    flags=re.MULTILINE)

IPPortPatternGlobal = re.compile(
    r'(?P<ip>(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?))'
    r'(?=.*?(?:(?:(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?))|(?P<port>[1-9]\d{1,4})))',
    flags=re.DOTALL)

class Provider:
    """Proxy provider.

    Provider - a website that publish free public proxy lists.

    :param str url: Url of page where to find proxies
    :param tuple proto:
        (optional) List of the types (protocols) that may be supported
        by proxies returned by the provider. Then used as :attr:`Proxy.types`
    :param int max_conn:
        (optional) The maximum number of concurrent connections on the provider
    :param int max_tries:
        (optional) The maximum number of attempts to receive response
    :param int timeout:
        (optional) Timeout of a request in seconds
    """

    _pattern = IPPortPatternGlobal

    def __init__(self, pool, proxy_set=None, url=None, proto=(), max_conn=4,
                 max_tries=3, timeout=20, loop=None):
        self.pool = pool
        if url:
            self.domain = urlparse(url).netloc
        self.url = url
        self.url_pool = asyncio.Queue(20)
        self.proto = proto
        self._max_tries = max_tries
        self._timeout = timeout
        self.fetched_proxies = proxy_set or set()
        # concurrent connections on the current provider
        self._loop = loop or asyncio.get_event_loop()
        self.session = aiohttp.ClientSession()
        conn = aiohttp.ProxyConnector(proxy="http://localhost:8118")
        self.proxy_session = aiohttp.ClientSession(connector=conn)
        self.max_conn = max_conn
        self.blocked = False
        self.consume_tasks = []
        self.produce_url_task = None

    def __del__(self):
        self.session.close()
        self.proxy_session.close()

    def stop(self):
        if self.produce_url_task and not self.produce_url_task.done():
            self.produce_url_task.cancel()
        for task in self.consume_tasks:
            if not task.done():
                task.cancel()

    async def loop_fetch_proxies(self):
        """Receive proxies from the provider and return them.

        :return: :attr:`.proxies`
        """
        logging.debug('Try to get proxies from %s' % self.domain)
        self.produce_url_task = asyncio.ensure_future(self.gen_urls(self.url))
        while True:
            try:
                while len(self.consume_tasks) <= self.max_conn:
                    url = await self.url_pool.get()
                    task = asyncio.ensure_future(self.fetch_on_page(url))
                    self.consume_tasks.append(task)
                self.consume_tasks = list(filter(lambda t: not t.done(), self.consume_tasks))
                if self.consume_tasks:
                    await asyncio.sleep(10)
            except concurrent.futures.CancelledError as e:
                logging.debug("%s canceled from working." % (self.__class__.__name__))
                break;
            except (Exception) as e:
                logging.error("Loop for %s error with %s.%s" % (self.__class__.__name__, e, type(e)))
                break;
                # return [self.fetch_on_page(url) for url in self.url2urls(self.url)]

    async def gen_urls(self, url):
        try:
            while True:
                if self.url_pool.empty():
                    for _ in await self.url2urls(url):
                        await self.url_pool.put(_)
                await asyncio.sleep(1)
        except KeyboardInterrupt as e:
            raise e

    async def url2urls(self, url):
        if url is None:
            warnings.warn("Please Implement the url2urls function of <%s>" % self.__class__.__name__)
        return [url]

    async def fetch_on_page(self, url, data=None, headers=None, method='GET'):
        try:
            if isinstance(url, dict):
                data = url.get("data")
                headers = url.get("headers")
                method = url.get("method") or "GET"
                url = url.get("url")
            page = await self.get(url, data=data, headers=headers, method=method)
            # try:
            received = self.find_proxies(page)
            # except Exception as e:
            #     received = []
            #     logging.error('Error when executing find_proxies.'
                          # 'Domain: %s; Error: %r' % (self.domain, e))
            for proxy in received:
                if proxy[1] != "" and proxy not in self.fetched_proxies:
                    self.fetched_proxies.add(proxy)
                    await self.pool.put(proxy)
                    logging.info(str(proxy) + "from " + url)
        except concurrent.futures.CancelledError as e:
            logging.debug("Cancelled with %s." % (url))
        except Exception as e:
            logging.error("%s in fetch_on_page, error with %s." % (type(e), e))

    async def get(self, url, data=None, headers=None, method='GET'):
        for _ in range(self._max_tries):
            page = await self._get(url, data=data, headers=headers, method=method)
            if page:
                break
        return page

    async def _get(self, url, data=None, headers=None, method='GET'):
        page = ''
        if not self.blocked:
            try:
                with aiohttp.Timeout(self._timeout, loop=self._loop):
                    async with self.session.request(method, url, data=data,
                                                     headers=headers) as resp:
                        if resp.status == 200:
                            page = await resp.text()
                        else:
                            error_page = await resp.text()
                            logging.error('url: %s\nheaders: %s\ncookies: %s\nstatus_code:%d\npage:\n%s' % (
                                      url, resp.headers, resp.cookies, resp.status, error_page))
                            if resp.status in range(500, 510):
                                await asyncio.sleep(3)
                            # raise BadStatusError('Status: %s' % resp.status)

            except (UnicodeDecodeError, asyncio.TimeoutError,
                    aiohttp.ClientOSError, aiohttp.ClientResponseError,
                    aiohttp.ServerDisconnectedError) as e:
                logging.error('%s is failed. Error: %r;' % (url, e))
            except KeyboardInterrupt as e:
                raise e
        if page == "":
            try:
                with aiohttp.Timeout(self._timeout, loop=self._loop):
                    async with self.proxy_session.request(method, url, data=data, headers=headers) as resp:
                        if resp.status == 200:
                            page = await resp.text()
                        else:
                            error_page = await resp.text()
                            logging.error('url: %s\nheaders: %s\ncookies: %s\nstatus_code:%d\npage:\n%s' % (
                                      url, resp.headers, resp.cookies, resp.status, error_page))
                            if resp.status in range(500, 510):
                                await asyncio.sleep(3)
                                # raise BadStatusError('Status: %s' % resp.status)
            except (UnicodeDecodeError, asyncio.TimeoutError,
                    aiohttp.ClientOSError, aiohttp.ClientResponseError,
                    aiohttp.ServerDisconnectedError) as e:
                logging.error('%s is failed. Error: %r;' % (url, e))
            except KeyboardInterrupt as e:
                raise e
        return page

    def find_proxies(self, page):
        return self._find_proxies(page)

    def _find_proxies(self, page):
        proxies = self._pattern.findall(page)
        return proxies

class BlockedProvider(Provider):
    def __init__(self, *args, **kwargs):
        super(BlockedProvider, self).__init__(*args, **kwargs)
        self.blocked = True


class Freeproxylists_com(BlockedProvider):
    domain = 'freeproxylists.com'
    url = "freeproxylists.com"

    async def url2urls(self, url):
        exp = r'''href\s*=\s*['"](?P<t>[^'"]*)/(?P<uts>\d{10})[^'"]*['"]'''
        tpl = 'http://www.freeproxylists.com/load_{}_{}.html'
        # example: http://www.freeproxylists.com/socks/1448724717.html
        # urls = ['http://www.freeproxylists.com/socks.html',
        urls = ['http://www.freeproxylists.com/elite.html',
                'http://www.freeproxylists.com/anonymous.html']
        params = []
        for task in asyncio.as_completed([self.get(url) for url in urls]):
            page = await task
            params += re.findall(exp, page)
        urls = [tpl.format(t, uts) for t, uts in params]
        return urls


class Blogspot_com_base(BlockedProvider):
    _cookies = {'NCR': 1}
    domain = "blogspot.com"
    domains = []

    async def url2urls(self, url):
        exp = r'''<a href\s*=\s*['"]([^'"]*\.\w+/\d{4}/\d{2}/[^'"#]*)['"]>'''
        urls = set()
        for task in asyncio.as_completed([self.get("http://%s/" % d) for d in self.domains]):
            page = await task
            urls.union(set(re.findall(exp, page)))
        return list(urls)


class Blogspot_com(Blogspot_com_base):
    domain = 'blogspot.com'
    domains = ['sslproxies24.blogspot.com', 'proxyserverlist-24.blogspot.com',
               'newfreshproxies24.blogspot.com', 'irc-proxies24.blogspot.com',
               # 'freeschoolproxy.blogspot.com', # stop update since Feb,2016
               'googleproxies24.blogspot.com',]
               # 'getdailyfreshproxy.blogspot.com', # stop update since March,2016


# Need no socks proxy for now, mabye in the future.
# class Blogspot_com_socks(Blogspot_com_base):
#     domain = 'blogspot.com^socks'
#     domains = ['www.proxyocean.com', 'www.socks24.org']


class Webanetlabs_net(Provider):
    domain = 'webanetlabs.net'

    async def url2urls(self, url):
        exp = r'''href\s*=\s*['"]([^'"]*proxylist_at_[^'"]*)['"]'''
        page = await self.get('http://webanetlabs.net/publ/24')
        urls = ['http://webanetlabs.net%s' % path
                for path in set(re.findall(exp, page))]
        return urls


class Checkerproxy_net(BlockedProvider):
    domain = 'checkerproxy.net'

    async def url2urls(self, url):
        exp = r'''href\s*=\s*['"]([^'"]?\d{2}-\d{2}-\d{4}[^'"]*)['"]'''
        page = await self.get('http://checkerproxy.net/')
        urls = ['http://checkerproxy.net%s' % path
                for path in set(re.findall(exp, page))]
        return urls


class Proxz_com(BlockedProvider):
    domain = 'proxz.com'

    def find_proxies(self, page):
        return self._find_proxies(unquote(page))

    async def url2urls(self, url):
        exp = r'''href\s*=\s*['"]([^'"]?proxy_list_high_anonymous_[^'"]*)['"]'''
        url = 'http://www.proxz.com/proxy_list_high_anonymous_0.html'
        page = await self.get(url)
        urls = ['http://www.proxz.com/%s' % path
                for path in set(re.findall(exp, page))]
        return urls


class Proxy_list_org(BlockedProvider):
    domain = 'proxy-list.org'
    _pattern = re.compile(r'''Proxy\('([\w=]+)'\)''')

    def find_proxies(self, page):
        return [tuple(b64decode(hp).decode().split(':'))
                for hp in self._find_proxies(page)]

    async def url2urls(self, url):
        exp = r'''href\s*=\s*['"]\./([^'"]?index\.php\?p=\d+[^'"]*)['"]'''
        url = 'http://proxy-list.org/english/index.php?p=1'
        page = await self.get(url)
        urls = ['http://proxy-list.org/english/%s' % path
                for path in set(re.findall(exp, page))]
        return urls


class Aliveproxy_com(BlockedProvider):
    # more: http://www.aliveproxy.com/socks-list/socks5.aspx/United_States-us
    domain = 'aliveproxy.com'
    _pattern = re.compile(r'''(?P<ip>(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)):(?P<port>\d{2,5})''')

    async def url2urls(self, url):
        paths = [
            'high-anonymity-proxy-list', 'anonymous-proxy-list',
            'fastest-proxies', 'us-proxy-list', 'gb-proxy-list', 'fr-proxy-list',
            'de-proxy-list', 'jp-proxy-list', 'ca-proxy-list', 'ru-proxy-list',
            'proxy-list-port-80', 'proxy-list-port-81', 'proxy-list-port-3128',
            'proxy-list-port-8000', 'proxy-list-port-8080']
        urls = ['http://www.aliveproxy.com/%s/' % path for path in paths]
        return urls


class Maxiproxies_com(Provider):
    domain = 'maxiproxies.com'

    async def url2urls(self, url):
        exp = r'''<a href\s*=\s*['"]([^'"]*example[^'"#]*)['"]>'''
        page = await self.get('http://maxiproxies.com/category/proxy-lists/')
        urls = re.findall(exp, page)
        return urls


class _50kproxies_com(Provider):
    domain = '50kproxies.com'

    async def url2urls(self, url):
        exp = r'''<a href\s*=\s*['"]([^'"]*-proxy-list-[^'"#]*)['"]>'''
        page = await self.get('http://50kproxies.com/category/proxy-list/')
        urls = re.findall(exp, page)
        return urls


class Proxymore_com(Provider):
    domain = 'proxymore.com'

    async def url2urls(self, url):
        urls = ['http://www.proxymore.com/proxy-list-%d.html' % n
                for n in range(1, 56)]
        return urls


class Proxylist_me(BlockedProvider):
    domain = 'proxylist.me'

    async def url2urls(self, url):
        exp = r'''href\s*=\s*['"][^'"]*/proxys/index/(\d+)['"]'''
        page = await self.get('http://proxylist.me/')
        lastId = max([int(n) for n in re.findall(exp, page)])
        urls = ['http://proxylist.me/proxys/index/%d' %
                n for n in range(lastId, -20, -20)]
        return urls


class Foxtools_ru(Provider):
    domain = 'foxtools.ru'

    async def url2urls(self, url):
        urls = ['http://api.foxtools.ru/v2/Proxy.txt?page=%d' % n
                for n in range(1, 6)]
        return urls


class Gatherproxy_com(BlockedProvider):
    domain = 'gatherproxy.com'
    _pattern_h = re.compile(
        r'''(?P<ip>(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?))'''
        r'''(?=.*?(?:(?:(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?))|'(?P<port>[\d\w]+)'))''',
        flags=re.DOTALL)

    def find_proxies(self, page):
        # if 'gp.dep' in page:
        #     proxies = self._pattern_h.findall(page)  # for http(s)
        #     proxies = [(host, str(int(port, 16))) for host, port in proxies if port]
        # else:
        #     proxies = self._find_proxies(page)  # for socks
        return [(host, str(int(port, 16)))
                for host, port in self._pattern_h.findall(page) if port]

    async def url2urls(self, url):
        url = 'http://www.gatherproxy.com/proxylist/anonymity/'
        expNumPages = r'href="#(\d+)"'
        method = 'POST'
        # hdrs = {'Content-Type': 'application/x-www-form-urlencoded'}
        urls = []
        for t in ['anonymous', 'elite']:
            data = {'Type': t, 'PageIdx': 1}
            page = await self.get(url, data=data, method=method)
            if not page:
                continue
            lastPageId = max([int(n) for n in re.findall(expNumPages, page)])
            urls = [{'url': url, 'data': {'Type': t, 'PageIdx': pid},
                     'method': method} for pid in range(1, lastPageId + 1)]
        # urls.append({'url': 'http://www.gatherproxy.com/sockslist/',
        #              'method': method})
        return urls


# Need no socks proxy now, maybe future.
# class Gatherproxy_com_socks(Provider):
#     domain = 'gatherproxy.com^socks'

#     async def _pipe(self):
#         urls = [{'url': 'http://www.gatherproxy.com/sockslist/',
#                  'method': 'POST'}]
#         await self._find_on_pages(urls)


class Tools_rosinstrument_com_base(Provider):
    # more: http://tools.rosinstrument.com/cgi-bin/
    #       sps.pl?pattern=month-1&max=50&nskip=0&file=proxlog.csv
    domain = 'tools.rosinstrument.com'
    sqrtPattern = re.compile(r'''sqrt\((\d+)\)''')
    bodyPattern = re.compile(r'''hideTxt\(\n*'(.*)'\);''')
    _pattern = re.compile(
        r'''(?:(?P<domainOrIP>(?:[a-z0-9\-.]+\.[a-z]{2,6})|'''
        r'''(?:(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}'''
        r'''(?:25[0-5]|2[0-4]\d|[01]?\d\d?))))(?=.*?(?:(?:'''
        r'''[a-z0-9\-.]+\.[a-z]{2,6})|(?:(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)'''
        r'''\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?))|(?P<port>\d{2,5})))''',
        flags=re.DOTALL)

    def find_proxies(self, page):
        x = self.sqrtPattern.findall(page)
        if not x:
            return []
        x = round(sqrt(float(x[0])))
        hiddenBody = self.bodyPattern.findall(page)[0]
        hiddenBody = unquote(hiddenBody)
        toCharCodes = [ord(char) ^ (x if i % 2 else 0)
                       for i, char in enumerate(hiddenBody)]
        fromCharCodes = ''.join([chr(n) for n in toCharCodes])
        page = unescape(fromCharCodes)
        return self._find_proxies(page)


class Tools_rosinstrument_com(Tools_rosinstrument_com_base):
    domain = 'tools.rosinstrument.com'

    async def url2urls(self, url):
        tpl = 'http://tools.rosinstrument.com/raw_free_db.htm?%d&t=%d'
        urls = [tpl % (pid, t) for pid in range(51) for t in range(1, 3)]
        return urls


# Need no socks proxy now, maybe future.
# class Tools_rosinstrument_com_socks(Tools_rosinstrument_com_base):
#     domain = 'tools.rosinstrument.com^socks'

#     async def _pipe(self):
#         tpl = 'http://tools.rosinstrument.com/raw_free_db.htm?%d&t=3'
#         urls = [tpl % pid for pid in range(51)]
#         await self._find_on_pages(urls)


class Xseo_in(Provider):
    domain = 'xseo.in'
    charEqNum = {}

    def char_js_port_to_num(self, matchobj):
        chars = matchobj.groups()[0]
        num = ''.join([self.charEqNum[ch] for ch in chars if ch != '+'])
        return num

    def find_proxies(self, page):
        expPortOnJS = r'\(""\+(?P<chars>[a-z+]+)\)'
        expCharNum = r'\b(?P<char>[a-z])=(?P<num>\d);'
        self.charEqNum = {char: i for char, i in re.findall(expCharNum, page)}
        page = re.sub(expPortOnJS, self.char_js_port_to_num, page)
        return self._find_proxies(page)

    async def url2urls(self, url):
        return [{"url":'http://xseo.in/proxylist', "data":{'submit': 1}, "method":'POST'}]


class Nntime_com(Provider):
    domain = 'nntime.com'
    charEqNum = {}
    _pattern = re.compile(
        r'''\b(?P<ip>(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}'''
        r'''(?:25[0-5]|2[0-4]\d|[01]?\d\d?))(?=.*?(?:(?:(?:(?:25'''
        r'''[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)'''
        r''')|(?P<port>\d{2,5})))''',
        flags=re.DOTALL)

    def char_js_port_to_num(self, matchobj):
        chars = matchobj.groups()[0]
        num = ''.join([self.charEqNum[ch] for ch in chars if ch != '+'])
        return num

    def find_proxies(self, page):
        expPortOnJS = r'\(":"\+(?P<chars>[a-z+]+)\)'
        expCharNum = r'\b(?P<char>[a-z])=(?P<num>\d);'
        self.charEqNum = {char: i for char, i in re.findall(expCharNum, page)}
        page = re.sub(expPortOnJS, self.char_js_port_to_num, page)
        return self._find_proxies(page)

    async def url2urls(self, url):
        tpl = 'http://www.nntime.com/proxy-updated-{:02}.htm'
        urls = [tpl.format(n) for n in range(1, 31)]
        return urls


class Proxynova_com(Provider):
    domain = 'proxynova.com'

    async def url2urls(self, url):
        expCountries = r'"([a-z]{2})"'
        page = await self.get('http://www.proxynova.com/proxy-server-list/')
        tpl = 'http://www.proxynova.com/proxy-server-list/country-%s/'
        urls = [tpl % isoCode for isoCode in re.findall(expCountries, page)
                if isoCode != 'en']
        return urls


class Spys_ru(Provider):
    domain = 'spys.ru'
    charEqNum = {}

    def char_js_port_to_num(self, matchobj):
        chars = matchobj.groups()[0].split('+')
        # ex: '+(i9w3m3^k1y5)+(g7g7g7^v2e5)+(d4r8o5^i9u1)+(y5c3e5^t0z6)'
        # => ['', '(i9w3m3^k1y5)', '(g7g7g7^v2e5)', '(d4r8o5^i9u1)', '(y5c3e5^t0z6)']
        # => ['i9w3m3', 'k1y5'] => int^int
        num = ''
        for numOfChars in chars[1:]:  # first - is ''
            var1, var2 = numOfChars.strip('()').split('^')
            digit = self.charEqNum[var1] ^ self.charEqNum[var2]
            num += str(digit)
        return num

    def find_proxies(self, page):
        expPortOnJS = r'(?P<js_port_code>(?:\+\([a-z0-9^+]+\))+)'
        # expCharNum = r'\b(?P<char>[a-z\d]+)=(?P<num>[a-z\d\^]+);'
        expCharNum = r'[>;]{1}(?P<char>[a-z\d]{4,})=(?P<num>[a-z\d\^]+)'
        # self.charEqNum = {char: i for char, i in re.findall(expCharNum, page)}
        res = re.findall(expCharNum, page)
        for char, num in res:
            if '^' in num:
                digit, tochar = num.split('^')
                num = int(digit) ^ self.charEqNum[tochar]
            self.charEqNum[char] = int(num)
        page = re.sub(expPortOnJS, self.char_js_port_to_num, page)
        return self._find_proxies(page)

    async def url2urls(self, url):
        expSession = r"'([a-z0-9]{32})'"
        url = 'http://spys.ru/proxies/'
        page = await self.get(url)
        sessionId = re.findall(expSession, page)[0]
        data = {'xf0': sessionId,  # session id
                'xpp': 3,          # 3 - 200 proxies on page
                'xf1': None}       # 1 = ANM & HIA; 3 = ANM; 4 = HIA
        method = 'POST'
        urls = [{'url': url, 'data': {**data, 'xf1': lvl},
                 'method': method} for lvl in [3, 4]]
        return urls
        # expCountries = r'>([A-Z]{2})<'
        # url = 'http://spys.ru/proxys/'
        # page = await self.get(url)
        # links = ['http://spys.ru/proxys/%s/' %
        #          isoCode for isoCode in re.findall(expCountries, page)]


class My_proxy_com(BlockedProvider):
    domain = 'my-proxy.com'

    async def url2urls(self, url):
        exp = r'''href\s*=\s*['"]([^'"]?free-[^'"]*)['"]'''
        url = 'http://www.my-proxy.com/free-proxy-list.html'
        page = await self.get(url)
        urls = ['http://www.my-proxy.com/%s' % path
                for path in re.findall(exp, page)]
        urls.append(url)
        return urls


# Need verify with recaptcha
# class Free_proxy_cz(Provider):
#     domain = 'free-proxy.cz'
#     _pattern = re.compile(
#         r'''decode\("([\w=]+)".*?\("([\w=]+)"\)''', flags=re.DOTALL)

#     def find_proxies(self, page):
#         return [(b64decode(h).decode(), b64decode(p).decode())
#                 for h, p in self._find_proxies(page)]

#     async def _pipe(self):
#         tpl = 'http://free-proxy.cz/en/proxylist/main/date/%d'
#         urls = [tpl % n for n in range(1, 15)]
#         await self._find_on_pages(urls)
#         # _urls = []
#         # for url in urls:
#         #     if len(_urls) == 15:
#         #         await self._find_on_pages(_urls)
#         #         print('sleeping on 61 sec')
#         #         await asyncio.sleep(61)
#         #         _urls = []
#         #     _urls.append(url)
#         # =========
#         # expNumPages = r'href="/en/proxylist/main/(\d+)"'
#         # page = await self.get('http://free-proxy.cz/en/')
#         # if not page:
#         #     return
#         # lastPageId = max([int(n) for n in re.findall(expNumPages, page)])
#         # tpl = 'http://free-proxy.cz/en/proxylist/main/date/%d'
#         # urls = [tpl % pid for pid in range(1, lastPageId+1)]
#         # _urls = []
#         # for url in urls:
#         #     if len(_urls) == 15:
#         #         await self._find_on_pages(_urls)
#         #         print('sleeping on 61 sec')
#         #         await asyncio.sleep(61)
#         #         _urls = []
#         #     _urls.append(url)


class Proxyb_net(Provider):
    domain = 'proxyb.net'
    _port_pattern_b64 = re.compile(r"stats\('([\w=]+)'\)")
    _port_pattern = re.compile(r"':(\d+)'")

    def find_proxies(self, page):
        if not page:
            return []
        _hosts, _ports = page.split('","ports":"')
        hosts, ports = [], []
        for host in _hosts.split('<\/tr><tr>'):
            host = IPPattern.findall(host)
            if not host:
                continue
            hosts.append(host[0])
        ports = [self._port_pattern.findall(b64decode(port).decode())[0]
                 for port in self._port_pattern_b64.findall(_ports)]
        return [(host, port) for host, port in zip(hosts, ports)]

    async def url2urls(self, url):
        url = 'http://proxyb.net/ajax.php'
        method = 'POST'
        data = {'action': 'getProxy', 'p': 0,
                'page': '/anonimnye_proksi_besplatno.html'}
        hdrs = {'X-Requested-With': 'XMLHttpRequest'}
        urls = [{'url': url, 'data': {**data, 'p': p},
                 'method': method, 'headers': hdrs} for p in range(0, 151)]
        return urls


class Proxylistplus_com(BlockedProvider):
    domain = 'list.proxylistplus.com'

    async def url2urls(self, url):
        urls = ['http://list.proxylistplus.com/Fresh-HTTP-Proxy-List-%d' % n
                for n in range(1, 7)]
        return urls


class Kuaidaili(Provider):
    domain = "kuaidaili.com"

    async def url2urls(self, url):
        urls = ["http://www.kuaidaili.com/free/inha/%d" % n for n in range(1, 21)]
        urls += ["http://www.kuaidaili.com/free/outha/%d" % n for n in range(1, 21)]
        return urls


class Xicidaili(Provider):
    domain = "xicidaili.com"

    async def url2urls(self, url):
        urls = [{"url": "http://www.xicidaili.com/nn/%d" % n, "headers": headers} for n in range(1, 21)]
        urls += [{"url": "http://www.xicidaili.com/wn/%d" % n, "headers": headers} for n in range(1, 21)]
        return urls

# Need reptcha verify.
# class Freeproxylists_net(Provider):
#     domain = "freeproxylists.net"

#     async def url2urls(self, url):
#         urls = ["http://www.freeproxylists.net/zh/?pr=HTTPS&a[]=2&page=%d" % n for n in [1, 2]]
#         return urls


class Cnproxy(BlockedProvider):
    domain = "cnproxy.com"

    async def url2urls(self, url):
        urls = ["http://www.cnproxy.com/proxy%d.html" % n for n in range(1, 11)]
        return urls


class Proxy_com_ru(BlockedProvider):
    domain = "proxy.com.ru"

    async def url2urls(self, url):
        urls = ["http://www.proxy.com.ru/gaoni/", "http://www.proxy.com.ru/niming/"]
        return urls

class ProxyProvider(Provider):
    def __init__(self, *args, **kwargs):
        warnings.warn('`ProxyProvider` is deprecated, use `Provider` instead.',
                      DeprecationWarning)
        super().__init__(*args, **kwargs)



# PROVIDERS = [
#     Provider(url='https://getproxy.net/en/',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 25
#     Provider(url='http://www.proxylists.net/',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 44
#     Provider(url='http://ipaddress.com/proxy-list/',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 53
#     Provider(url='http://www.sslproxies.org/',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 100
#     Provider(url='http://2-proxy.com/proxylist?sort=last'
#                  '&order=DESC&maxtime=30000&perpage=1000',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 109
#     Provider(url='http://marcosbl.com/lab/proxies/',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 89
#     Provider(url='https://freshfreeproxylist.wordpress.com/',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 178
#     Provider(url='http://proxytime.ru/http',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 547
#     # Need send post to get list now.
#     # Provider(url='http://free-proxy-list.net/',
#     #          proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 300
#     # Redirect to another website.
#     # Provider(url='http://www.proxyservers.eu/',
#     #          proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 1875
#     Provider(url='http://socks24.ru/proxy/httpProxies.txt',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 1601
#     Provider(url='http://fineproxy.org/eng/?p=6',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 1819
#     Provider(url='http://www.socks-proxy.net/',
#              proto=('SOCKS4', 'SOCKS5')),                           # 80
#     Provider(url='http://www.cybersyndrome.net/pla.html',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 1100
#     Provider(url='http://codediaries.com/list.php',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 75
#     Provider(url='http://httptunnel.ge/ProxyListForFree.aspx',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 100
#     Provider(url='http://txt.proxyspy.net/proxy.txt',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 300
#     Provider(url='http://www.ip-adress.com/proxy_list/?k=time',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 57
#     Provider(url='http://myproxylists.com/free-proxy-list',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 9
#     Provider(url='http://cn-proxy.com/',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 48
#     Provider(url='http://hugeproxies.com/home/',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 569
#     Provider(url='http://proxy.rufey.ru/',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 153
#     Provider(url='http://mitituti.com/content/proxy.txt',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 227
#     Provider(url='http://geekelectronics.org/my-servisy/proxy',
#              proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 395
#     Proxy_list_org(proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 140
#     Xseo_in(proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),                  # 252
#     Spys_ru(proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),                  # 674
#     Proxylistplus_com(proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),        # 301
#     Proxz_com(proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25'), max_conn=2),    # 443
#     Proxymore_com(proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),            # 1375
#     Proxylist_me(proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),             # 2872
#     Foxtools_ru(proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25'), max_conn=1),  # 500
#     Gatherproxy_com(proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),          # 3212
#     Nntime_com(proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),               # 1050
#     Proxynova_com(proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),            # 818
#     Blogspot_com(proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),             # 24800
#     Gatherproxy_com_socks(proto=('SOCKS4', 'SOCKS5')),                             # 30
#     Blogspot_com_socks(proto=('SOCKS4', 'SOCKS5')),                                # 1486
#     Tools_rosinstrument_com(proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 4347
#     Tools_rosinstrument_com_socks(proto=('SOCKS4', 'SOCKS5')),                     # 1362
#     My_proxy_com(max_conn=2),                                                      # 891
#     Checkerproxy_net(),                                                            # 15803
#     Aliveproxy_com(),                                                              # 210
#     Freeproxylists_com(),                                                          # 1338
#     Webanetlabs_net(),                                                             # 2615
#     Maxiproxies_com(),                                                             # 543
#     _50kproxies_com(),                                                             # 822

#     Kuaidaili(),
#     Xicidaili(),
#     Freeproxylists_net(),
#     Cnproxy(),
#     Proxy_com_ru(),
#     # # Bad...
#     # Provider(url='http://go4free.xyz/Free-Proxy/', proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 196
#     # Provider(url='http://blackstarsecurity.com/proxy-list.txt'),  # 7014
#     # Provider(url='http://www.get-proxy.net/proxy-archives'),  # 519
#     # Free_proxy_cz(),  # 420
#     # Proxyb_net(proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),               # 857
# ]
