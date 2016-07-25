#! /usr/bin/env python3.5
# -*- coding: utf-8 -*-
#
# Copyright © 2016 Peng Liu <myme5261314@gmail.com>
#
# Distributed under terms of the gplv3 license.

"""

"""
# import os
# os.environ['PYTHONASYNCIODEBUG'] = '1'
import asyncio
import aiohttp
import utils
import logging
import concurrent



def main():
    # asyncio.BaseEventLoop.set_debug(True)
    # logging.basicConfig(level=logging.DEBUG)
    try:
        fetched_pool = asyncio.Queue(10)
        fetched_set = set()
        providers = utils.gen_prv(fetched_pool, fetched_set)
        tasks = asyncio.wait([_.loop_fetch_proxies() for _ in providers])
        loop = asyncio.get_event_loop()
        loop.run_until_complete(tasks)
    except KeyboardInterrupt as e:
        print("Caught keyboard interrupt. Canceling %d tasks..." % len([_ for _ in asyncio.Task.all_tasks() if not _.done()]))
        for task in asyncio.Task.all_tasks():
            if not task.cancelled():
                task.cancel()
        loop.run_forever()
        for task in asyncio.Task.all_tasks():
            try:
                if not task.cancelled():
                    task.exception()
            except concurrent.futures.CancelledError as e:
                pass
        loop.stop()
    finally:
        loop.close()


if __name__ == '__main__':
    main()
