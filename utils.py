#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright ©  2016
# Peng Liu, <myme5261314@gmail.com>
#
# Distributed under terms of the gplv3 license.

"""

"""


import providers.providers as prv

def gen_prv(queue, proxy_set=None):
    providers = []
    proxy_set = proxy_set or set()
    providers.append(prv.Provider(queue, proxy_set, url='https://getproxy.net/en/'))
    providers.append(prv.Provider(queue, proxy_set, url='http://www.proxylists.net/'))
    providers.append(prv.Provider(queue, proxy_set, url='http://ipaddress.com/proxy-list/'))
    providers.append(prv.Provider(queue, proxy_set, url='http://www.sslproxies.org/'))
    providers.append(prv.Provider(queue, proxy_set, url='http://2-proxy.com/proxylist?sort=last&order=DESC&maxtime=30000&perpage=1000'))
    providers.append(prv.Provider(queue, proxy_set, url='http://marcosbl.com/lab/proxies/'))
    providers.append(prv.Provider(queue, proxy_set, url='https://freshfreeproxylist.wordpress.com/'))
    providers.append(prv.Provider(queue, proxy_set, url='http://proxytime.ru/http'))
    providers.append(prv.Provider(queue, proxy_set, url='http://socks24.ru/proxy/httpProxies.txt'))
    providers.append(prv.Provider(queue, proxy_set, url='http://fineproxy.org/eng/?p=6'))
    # providers.append(prv.Provider(queue, proxy_set, url='http://www.socks-proxy.net/'))
    providers.append(prv.Provider(queue, proxy_set, url='http://www.sslproxies.org/'))
    providers.append(prv.Provider(queue, proxy_set, url='http://www.cybersyndrome.net/pla.html'))
    providers.append(prv.Provider(queue, proxy_set, url='http://codediaries.com/list.php'))
    providers.append(prv.Provider(queue, proxy_set, url='http://httptunnel.ge/ProxyListForFree.aspx'))
    providers.append(prv.Provider(queue, proxy_set, url='http://txt.proxyspy.net/proxy.txt'))
    providers.append(prv.Provider(queue, proxy_set, url='http://www.ip-adress.com/proxy_list/?k=time'))
    providers.append(prv.Provider(queue, proxy_set, url='http://myproxylists.com/free-proxy-list'))
    providers.append(prv.Provider(queue, proxy_set, url='http://cn-proxy.com/'))
    providers.append(prv.Provider(queue, proxy_set, url='http://hugeproxies.com/home/'))
    providers.append(prv.Provider(queue, proxy_set, url='http://proxy.rufey.ru/'))
    providers.append(prv.Provider(queue, proxy_set, url='http://mitituti.com/content/proxy.txt'))
    providers.append(prv.Provider(queue, proxy_set, url='http://geekelectronics.org/my-servisy/proxy'))
    providers.append(prv.Proxy_list_org(queue, proxy_set))
    providers.append(prv.Xseo_in(queue, proxy_set))
    providers.append(prv.Spys_ru(queue, proxy_set))
    providers.append(prv.Proxylistplus_com(queue, proxy_set))
    providers.append(prv.Proxz_com(queue, proxy_set, max_conn=2))
    providers.append(prv.Proxymore_com(queue, proxy_set))
    providers.append(prv.Proxylist_me(queue, proxy_set))
    providers.append(prv.Foxtools_ru(queue, proxy_set, max_conn=1))
    providers.append(prv.Gatherproxy_com(queue, proxy_set))
    providers.append(prv.Nntime_com(queue, proxy_set))
    providers.append(prv.Proxynova_com(queue, proxy_set))
    providers.append(prv.Blogspot_com(queue, proxy_set))
    # providers.append(prv.Gatherproxy_com_socks(queue))
    # providers.append(prv.Blogspot_com_socks(queue))
    providers.append(prv.Tools_rosinstrument_com(queue, proxy_set))
    # providers.append(prv.Tools_rosinstrument_com_socks(queue))
    providers.append(prv.My_proxy_com(queue, proxy_set, max_conn=2))
    providers.append(prv.Checkerproxy_net(queue, proxy_set))
    providers.append(prv.Aliveproxy_com(queue, proxy_set))
    providers.append(prv.Freeproxylists_com(queue, proxy_set))
    providers.append(prv.Webanetlabs_net(queue, proxy_set))
    providers.append(prv.Maxiproxies_com(queue, proxy_set))
    providers.append(prv._50kproxies_com(queue, proxy_set))
    providers.append(prv.Kuaidaili(queue, proxy_set))
    providers.append(prv.Xicidaili(queue, proxy_set))
    # providers.append(prv.Freeproxylists_net(queue))
    providers.append(prv.Cnproxy(queue, proxy_set))
    providers.append(prv.Proxy_com_ru(queue, proxy_set))
    # # Bad...
    # Provider(url='http://go4free.xyz/Free-Proxy/', proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),  # 196
    # Provider(url='http://blackstarsecurity.com/proxy-list.txt'),  # 7014
    # Provider(url='http://www.get-proxy.net/proxy-archives'),  # 519
    # Free_proxy_cz(),  # 420
    # Proxyb_net(proto=('HTTP', 'CONNECT:80', 'HTTPS', 'CONNECT:25')),               # 857
    return providers
