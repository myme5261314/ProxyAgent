#! /usr/bin/env python3.5
# -*- coding: utf-8 -*-
#
# Copyright © 2016 Peng Liu <myme5261314@gmail.com>
#
# Distributed under terms of the gplv3 license.

"""
This file defines the basic proxy class.
"""

class Proxy(object):
    """
    """

    def __init__(self, host, port, timeout):
        """Proxy Base class initialize function.
        Keyword Arguments:
        self     --
        host     -- proxy host IP, str.
        port     -- proxy port, int.
        """
        self.host = host
        self.port = port
        if self.port > 65535:
            raise ValueError('The port of proxy cannot be greater than 65535')
        self.timeout = timeout

        self.checked = False
        self.types = []
        self.n_requests = 0
        self.errors = []
