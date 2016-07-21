#! /usr/bin/env python3.5
# -*- coding: utf-8 -*-
#
# Copyright © 2016 Peng Liu <myme5261314@gmail.com>
#
# Distributed under terms of the gplv3 license.

"""

"""

import asyncio
import aiohttp
from providers.providers import Provider, Freeproxylists_com, Blogspot_com, Webanetlabs_net, Checkerproxy_net, Proxz_com, Proxy_list_org

def main():
    fetched_pool = asyncio.Queue(1000)
    providers = []
    # providers.append(Providers(fetched_pool, "http://cn-proxy.com"))
    # providers.append(Providers(fetched_pool, "http://proxytime.ru/http"))
    # providers.append(Providers(fetched_pool, "http://cn-proxy.com"))
    # providers.append(Providers(fetched_pool, "http://proxytime.ru/http"))
    # providers.append(Freeproxylists_com(fetched_pool))
    # providers.append(Blogspot_com(fetched_pool))
    # providers.append(Webanetlabs_net(fetched_pool))
    # providers.append(Checkerproxy_net(fetched_pool))
    # providers.append(Proxz_com(fetched_pool))
    providers.append(Proxy_list_org(fetched_pool))
    tasks = [_.loop_fetch_proxies() for _ in providers]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()


if __name__ == '__main__':
    main()
