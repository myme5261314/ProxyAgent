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
import providers.providers as prv


def gen_prv(queue):
    providers = []
    providers.append(prv.Provider(queue, url='https://getproxy.net/en/'))
    providers.append(prv.Provider(queue, url='http://www.proxylists.net/'))
    providers.append(prv.Provider(queue, url='http://ipaddress.com/proxy-list/'))
    providers.append(prv.Provider(queue, url='http://www.sslproxies.org/'))
    providers.append(prv.Provider(queue, url='http://2-proxy.com/proxylist?sort=last&order=DESC&maxtime=30000&perpage=1000'))
    providers.append(prv.Provider(queue, url='http://marcosbl.com/lab/proxies/'))
    providers.append(prv.Provider(queue, url='https://freshfreeproxylist.wordpress.com/'))
    providers.append(prv.Provider(queue, url='http://proxytime.ru/http'))
    providers.append(prv.Provider(queue, url='http://socks24.ru/proxy/httpProxies.txt'))
    providers.append(prv.Provider(queue, url='http://fineproxy.org/eng/?p=6'))
    providers.append(prv.Provider(queue, url='http://www.socks-proxy.net/'))
    providers.append(prv.Provider(queue, url='http://www.cybersyndrome.net/pla.html'))
    providers.append(prv.Provider(queue, url='http://codediaries.com/list.php'))
    providers.append(prv.Provider(queue, url='http://httptunnel.ge/ProxyListForFree.aspx'))
    providers.append(prv.Provider(queue, url='http://txt.proxyspy.net/proxy.txt'))
    providers.append(prv.Provider(queue, url='http://www.ip-adress.com/proxy_list/?k=time'))
    providers.append(prv.Provider(queue, url='http://myproxylists.com/free-proxy-list'))
    providers.append(prv.Provider(queue, url='http://cn-proxy.com/'))
    providers.append(prv.Provider(queue, url='http://hugeproxies.com/home/'))
    providers.append(prv.Provider(queue, url='http://proxy.rufey.ru/'))
    providers.append(prv.Provider(queue, url='http://mitituti.com/content/proxy.txt'))
    providers.append(prv.Provider(queue, url='http://geekelectronics.org/my-servisy/proxy'))
    providers.append(prv.Proxy_list_org(queue))
    providers.append(prv.Xseo_in(queue))
    providers.append(prv.Spys_ru(queue))
    providers.append(prv.Proxylistplus_com(queue))
    providers.append(prv.Proxz_com(queue, max_conn=2))
    providers.append(prv.Proxymore_com(queue))
    providers.append(prv.Proxylist_me(queue))
    providers.append(prv.Foxtools_ru(queue, max_conn=1))
    providers.append(prv.Gatherproxy_com(queue))
    providers.append(prv.Nntime_com(queue))
    providers.append(prv.Proxynova_com(queue))
    providers.append(prv.Blogspot_com(queue))
    # providers.append(prv.Gatherproxy_com_socks(queue))
    # providers.append(prv.Blogspot_com_socks(queue))
    providers.append(prv.Tools_rosinstrument_com(queue))
    # providers.append(prv.Tools_rosinstrument_com_socks(queue))
    providers.append(prv.My_proxy_com(queue, max_conn=2))
    providers.append(prv.Checkerproxy_net(queue))
    providers.append(prv.Aliveproxy_com(queue))
    providers.append(prv.Freeproxylists_com(queue))
    providers.append(prv.Webanetlabs_net(queue))
    providers.append(prv.Maxiproxies_com(queue))
    providers.append(prv._50kproxies_com(queue))
    providers.append(prv.Kuaidaili(queue))
    providers.append(prv.Xicidaili(queue))
    # providers.append(prv.Freeproxylists_net(queue))
    providers.append(prv.Cnproxy(queue))
    providers.append(prv.Proxy_com_ru(queue))
    # # Bad...
    # Provider(url='http://go4free.xyz/Free-Proxy/', proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 196
    # Provider(url='http://blackstarsecurity.com/proxy-list.txt'),  # 7014
    # Provider(url='http://www.get-proxy.net/proxy-archives'),  # 519
    # Free_proxy_cz(),  # 420
    # Proxyb_net(proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),               # 857
    return providers

def main():
    fetched_pool = asyncio.Queue(10)
    providers = gen_prv(fetched_pool)
    # providers.append(Providers(fetched_pool, "http://cn-proxy.com"))
    # providers.append(Providers(fetched_pool, "http://proxytime.ru/http"))
    # providers.append(Providers(fetched_pool, "http://cn-proxy.com"))
    # providers.append(Providers(fetched_pool, "http://proxytime.ru/http"))
    # providers.append(Freeproxylists_com(fetched_pool))
    # providers.append(Blogspot_com(fetched_pool))
    # providers.append(Webanetlabs_net(fetched_pool))
    # providers.append(Checkerproxy_net(fetched_pool))
    # providers.append(Proxz_com(fetched_pool))
    # providers.append(Proxy_list_org(fetched_pool))
    # providers.append(Aliveproxy_com(fetched_pool))
    # providers.append(Maxiproxies_com(fetched_pool))
    # providers.append(_50kproxies_com(fetched_pool))
    # providers.append(Proxymore_com(fetched_pool))
    # providers.append(Proxylist_me(fetched_pool))
    # providers.append(Gatherproxy_com(fetched_pool))
    # providers.append(Tools_rosinstrument_com(fetched_pool)) # host name need resolve.
    # providers.append(Xseo_in(fetched_pool))
    # providers.append(Nntime_com(fetched_pool))
    # providers.append(Proxynova_com(fetched_pool))
    # providers.append(Spys_ru(fetched_pool))
    # providers.append(My_proxy_com(fetched_pool))
    # providers.append(Proxyb_net(fetched_pool))
    # providers.append(Proxylistplus_com(fetched_pool))
    # providers.append(Kuaidaili(fetched_pool))
    # providers.append(Xicidaili(fetched_pool))
    # providers.append(Cnproxy(fetched_pool))
    # providers.append(Proxy_com_ru(fetched_pool))
    tasks = [_.loop_fetch_proxies() for _ in providers]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()


if __name__ == '__main__':
    main()
