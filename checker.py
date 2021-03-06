#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright ©  2016
# Peng Liu, <myme5261314@gmail.com>
#
# Distributed under terms of the gplv3 license.

"""

"""

import random
import requests as rs
import re
import asyncio
import aiohttp
import logging
import traceback
import time

from proxies import proxy

LOG = logging.getLogger(__name__)

checker_pages = [
        # 'http://httpbin.org/get?show_env',
        'https://httpbin.org/get?show_env',
        # 'smtp://smtp.gmail.com', 'smtp://aspmx.l.google.com',
        # 'http://azenv.net/',
        'https://www.proxy-listen.de/azenv.php',
        # 'http://www.proxyfire.net/fastenv', 'http://proxyjudge.us/azenv.php',
        # 'http://ip.spys.ru/', 'http://www.ingosander.net/azenv.php',
        # 'http://www.proxy-listen.de/azenv.php',
        'https://www.proxy-listen.de/azenv.php',
        "https://userpage.fu-berlin.de/benutzer/env.cgi",
        "https://proxyjudge.info/",
        # "https://bromargo.pl/azenv.php",
        "https://www.omgwallhack.org/toys/env.cgi",
        # "https://www.nucleoproducoes.com.br/1/azenv.php",
]

IPPattern = re.compile(
    r'(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)')


def get_headers():
    v = random.randint(1, 100000)
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, sdch",
        "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36",
        "valid": "%d" % v,
    }
    return headers, v

def reslove_ext_ip(retry_times=10):
    url = 'http://httpbin.org/get?show_env'
    for _ in range(retry_times):
        try:
            headers, v = get_headers()
            response = rs.get(url, headers=headers)
            if response.status_code == 200:
                content = response.text
                return re.findall(IPPattern, content)[0]
        except Exception as e:
            LOG.warning("Raw IP reslove failed. %s:%s" % (type(e), e))
            return None

class Checker(object):

    def __init__(self, in_pool, out_pool, ext_ip=None, max_conn=20):
        """
        Keyword Arguments:
        self   --
        ext_ip --
        """
        # self.url = url
        self.ext_ip = ext_ip if ext_ip else reslove_ext_ip()
        self.in_pool = in_pool
        self.out_pool = out_pool
        self.max_conn = max_conn
        self.tasks = []


    def check(self,):
        for _ in range(self.max_conn):
            task = asyncio.ensure_future(self._check())
            self.tasks.append(task)

    async def _check(self,):
        # ip, port = "41.38.113.210", "3128"
        # result = await self.check_proxy((ip, port))
        # print([result]*10)
        while True:
            ip, port= await self.in_pool.get()
            p = proxy.Proxy(ip, port)
            result = await self.check_proxy(p)
            if result:
                await p.put_pool(self.out_pool)
                LOG.info("check proxy %s:%s successfully." % (ip, port))
            else:
                LOG.debug("check proxy %s:%s Failed." % (ip, port))


    async def check_proxy(self, proxy):
        max_attempts = 3
        for _ in range(max_attempts):
            try:
                ip, port = proxy.host, proxy.port
                headers, v = get_headers()
                conn = aiohttp.ProxyConnector(proxy=("http://%s:%s" % (ip, port)))
                verify_url = random.choice(checker_pages)
                with aiohttp.Timeout(10):
                    with aiohttp.ClientSession(connector=conn, headers=headers) as sess:
                        start = time.time()
                        async with sess.get(verify_url) as resp:
                            resp_time = time.time() - start
                            content = await resp.text()
                            if not resp.status == 200:
                                LOG.debug("Failed verify proxy %s:%s with %s, status_code %d, reason: %s, content: %s" % (ip, port, verify_url, resp.status, resp.reason, content))
                                proxy.record_error(Exception(resp.reason))
                                continue
                            if not str(v) in content:
                                msg = "%s:%s, No random number verified on response." % (ip, port)
                                LOG.debug(msg)
                                proxy.record_error(Exception(msg))
                                return False
                            if self.ext_ip in content:
                                msg = "%s:%s, Raw IP appear in the response." % (ip, port)
                                LOG.debug(msg)
                                proxy.record_error(Exception(msg))
                                return False
                            proxy.record_resp_time(resp_time)
                            return True
            except (aiohttp.errors.DisconnectedError, aiohttp.errors.HttpProcessingError, aiohttp.errors.ClientError, asyncio.TimeoutError) as e:
                LOG.debug("Failed verify proxy %s:%s, get %s, %s" % (ip, port, type(e), e))
            # except Exception as e:
            #     print(e)
            #     print(traceback.print_exc())
        return False
