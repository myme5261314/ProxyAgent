#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright ©  2016
# Peng Liu, <myme5261314@gmail.com>
#
# Distributed under terms of the gplv3 license.

"""

"""

checker_pages = [
        'http://httpbin.org/get?show_env', 'https://httpbin.org/get?show_env',
        # 'smtp://smtp.gmail.com', 'smtp://aspmx.l.google.com',
        'http://azenv.net/', 'https://www.proxy-listen.de/azenv.php',
        'http://www.proxyfire.net/fastenv', 'http://proxyjudge.us/azenv.php',
        'http://ip.spys.ru/', 'http://www.ingosander.net/azenv.php',
        'http://www.proxy-listen.de/azenv.php']

class Checker(Object):
