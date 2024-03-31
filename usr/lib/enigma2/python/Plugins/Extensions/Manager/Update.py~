#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os
PY3 = sys.version_info.major >= 3
print("Update.py")


def upd_done():
    from os import popen, system
    cmd01 = "wget --no-cache --no-dns-cache http://patbuweb.com/tvManager/tvmanager.tar -O /tmp/tvmanager.tar --post-data='action=purge';tar -xvf /tmp/tvmanager.tar -C /;rm -rf /tmp/tvmanager.tar"
    cmd02 = "wget --no-check-certificate --no-cache --no-dns-cache -U 'Enigma2 - tvmanager Plugin' -c 'http://patbuweb.com/tvManager/tvmanager.tar' -O '/tmp/tvmanager.tar' --post-data='action=purge';tar -xvf /tmp/tvmanager.tar -C /;rm -rf /tmp/tvmanager.tar"
    cmd22 = 'find /usr/bin -name "wget"'
    res = popen(cmd22).read()
    if 'wget' not in res.lower():
        if os.path.exists('/etc/opkg'):
            cmd23 = 'opkg update && opkg install wget'
        else:
            cmd23 = 'apt-get update && apt-get install wget'
        popen(cmd23)
    try:
        popen(cmd02)
    except:
        popen(cmd01)
    system('rm -rf /tmp/tvmanager.tar')
    return


'''
import os
import sys
from twisted.web.client import downloadPage
PY3 = sys.version_info.major >= 3
print("Update.py")
fdest = "/tmp/tvmanager.tar"


def upd_done():
    print("In upd_done")
    xfile = 'http://patbuweb.com/tvManager/tvmanager.tar'
    # print('xfile: ', xfile)
    if PY3:
        xfile = b"http://patbuweb.com/tvManager/tvmanager.tar"
        print("Update.py in PY3")
    import requests
    response = requests.head(xfile)
    if response.status_code == 200:
        # print(response.headers['content-length'])
        # print("Code 200 upd_done xfile =", xfile)
        downloadPage(xfile, fdest).addCallback(upd_last)
    elif response.status_code == 404:
        print("Error 404")
    else:
        return


def upd_last(fplug):
    import time
    import os
    time.sleep(5)
    if os.path.isfile(fdest) and os.stat(fdest).st_size > 10000:
        cmd = "tar -xvf /tmp/tvmanager.tar -C /"
        print("cmd A =", cmd)
        os.system(cmd)
        os.remove('/tmp/tvmanager.tar')
    return
'''