#! /usr/bin/env python3.5
# -*- coding: utf-8 -*-
#
# Copyright © 2016 Peng Liu <myme5261314@gmail.com>
#
# Distributed under terms of the gplv3 license.

"""
This file defines the basic proxy class.
"""
import asyncio

class Proxy(object):
    """
    """

    def __init__(self, host, port):
        """Proxy Base class initialize function.
        Keyword Arguments:
        self     --
        host     -- proxy host IP, str.
        port     -- proxy port, int.
        """
        self.host = host
        self.port = port
        if int(self.port) > 65535:
            raise ValueError('The port of proxy cannot be greater than 65535')

        self.checked = False
        self.types = []
        self.n_requests = 0
        self.errors = []
        self.runtimes = []

    @property
    def error_rate(self):
        if self.n_requests==0:
            return 0
        else:
            return len(self.errors) / float(self.n_requests)

    @property
    def avg_resp_time(self):
        if self.n_requests==0:
            return 0.0
        else:
            return sum(self.runtimes) / len(self.runtimes)

    @property
    def priority(self):
        if self.n_requests==0:
            return 0.0
        else:
            return self.avg_resp_time * self.error_rate / self.n_requests

    def record_error(self, e):
        self.n_requests += 1
        self.errors.append(e)

    def record_resp_time(self, resp_time):
        self.n_requests += 1
        self.runtimes.append(resp_time)

    async def put_pool(self, pool):
        if isinstance(pool, asyncio.PriorityQueue):
            await pool.put((self.priority, self))
        elif isinstance(pool, asyncio.Queue):
            await pool.put(self)
        else:
            raise Exception("need asyncio queues.")
