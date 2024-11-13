#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import absolute_import
from os import path, system
from datetime import datetime
import re
import unicodedata
import six


append2file = False
imageType = None

PYversion = None


if six.PY2:
    unicode_type = unicode
else:
    unicode_type = str


def WhatPythonVersion():
    import sys
    return sys.version_info[0]


def isPY2():
    global PYversion
    if PYversion is None:
        if WhatPythonVersion() == 3:
            PYversion = False
        else:
            PYversion = True
    return PYversion


def ensure_binary(text, encoding='utf-8', errors='strict'):
    if isPY2():
        return text
    else:
        if isinstance(text, bytes):
            return text
        if isinstance(text, str):
            try:
                return text.encode(encoding, errors)
            except Exception:
                return text.encode(encoding, 'ignore')
    return text


def ensure_str(text, encoding='utf-8', errors='strict'):
    if type(text) is str:
        return text
    if isPY2():
        if isinstance(text, unicode):
            try:
                return text.encode(encoding, errors)
            except Exception:
                return text.encode(encoding, 'ignore')
    else:
        if isinstance(text, bytes):
            try:
                return text.decode(encoding, errors)
            except Exception:
                return text.decode(encoding, 'ignore')
    return text


def clearCache():
    with open("/proc/sys/vm/drop_caches", "w") as f:
        f.write("1\n")


def getImageType():
    return imageType


def isImageType(imgName=''):
    global imageType
    if imageType is None:
        if path.exists('/etc/opkg/all-feed.conf'):
            with open('/etc/opkg/all-feed.conf', 'r') as file:
                fileContent = file.read()
                file.close()
                fileContent = fileContent.lower()
                if fileContent.find('VTi') > -1:
                    imageType = 'vti'
                elif fileContent.find('code.vuplus.com') > -1:
                    imageType = 'vuplus'
                elif fileContent.find('openpli-7') > -1:
                    imageType = 'openpli7'
                elif fileContent.find('openatv') > -1:
                    imageType = 'openatv'
                    if fileContent.find('/5.3/') > -1:
                        imageType += '5.3'
    if imageType is None:
        if path.exists('/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/'):
            imageType = 'vti'
        elif path.exists('/usr/lib/enigma2/python/Plugins/Extensions/Infopanel/'):
            imageType = 'openatv'
        elif path.exists('/usr/lib/enigma2/python/Blackhole'):
            imageType = 'blackhole'
        elif path.exists('/etc/init.d/start_pkt.sh'):
            imageType = 'pkt'
        else:
            imageType = 'unknown'
    if imgName.lower() == imageType.lower():
        return True
    else:
        return False


def AGDEBUG(myText=None, Append=True, myDEBUG='/tmp/AglareComponents.log'):
    global append2file
    if myDEBUG is None:
        return
    if myText is None:
        return
    try:
        if append2file is False or Append is False:
            append2file = True
            f = open(myDEBUG, 'w')
        else:
            f = open(myDEBUG, 'a')
        f.write('%s\t%s\n' % (str(datetime.now()), myText))
        f.close()
        if path.getsize(myDEBUG) > 100000:
            system('sed -i -e 1,10d %s' % myDEBUG)
    except Exception as e:
        system('echo "Exception:%s" >> %s' % (str(e), myDEBUG))
    return


def logMissing(myText=None, Append=True, myDEBUG='/tmp/AglareComponents.log'):
    global append2file
    if myDEBUG is None:
        return
    if myText is None:
        return
    try:
        if append2file is False or Append is False:
            append2file = True
            f = open(myDEBUG, 'w')
        else:
            f = open(myDEBUG, 'a')
        f.write('%s\t%s\n' % (str(datetime.now()), myText))
        f.close()
        if path.getsize(myDEBUG) > 100000:
            system('sed -i -e 1,10d %s' % myDEBUG)
    except Exception as e:
        print(e)
        pass
    return


def isINETworking(addr='8.8.8.8', port=53):
    try:
        import socket
        if addr[:1].isdigit():
            addr = socket.gethostbyname(addr)
        socket.setdefaulttimeout(0.5)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((addr, port))
        return True
    except Exception as e:
        print(e)
        pass
    return False


def CHname_2_piconName(serName, iptvStream=False):
    piconName = serName.lower()
    if iptvStream:
        piconName = piconName.replace(' fhd', ' hd').replace(' uhd', ' hd')
    piconName = unicodedata.normalize('NFKD', unicode(piconName, 'utf_8', errors='ignore')).encode('ASCII', 'ignore')
    piconName = re.sub('[^a-z0-9]', '', piconName.replace('&', 'and').replace('+', 'plus').replace('*', 'star'))
    return piconName


try:
    # Python 2 imports
    from urlparse import urljoin, urlparse, urlunparse, urlsplit, urlunsplit, parse_qs, parse_qsl
    from urllib import addinfourl as urllib_addinfourl, quote as urllib_quote, quote_plus as urllib_quote_plus
    from urllib import unquote as urllib_unquote, unquote_plus as urllib_unquote_plus, urlencode as urllib_urlencode
    from urllib import urlopen as urllib_urlopen, urlretrieve as urllib_urlretrieve
    from urllib2 import BaseHandler as urllib2_BaseHandler, build_opener as urllib2_build_opener
    from urllib2 import HTTPCookieProcessor as urllib2_HTTPCookieProcessor, HTTPError as urllib2_HTTPError
    from urllib2 import HTTPHandler as urllib2_HTTPHandler, HTTPRedirectHandler as urllib2_HTTPRedirectHandler
    from urllib2 import HTTPSHandler as urllib2_HTTPSHandler, ProxyHandler as urllib2_ProxyHandler
    from urllib2 import Request as urllib2_Request, URLError as urllib2_URLError, urlopen as urllib2_urlopen
    from urllib2 import install_opener as urllib2_install_opener

    isPY2 = True
except ImportError:
    # Python 3 imports
    from urllib.parse import urljoin, urlparse, urlunparse, urlsplit, urlunsplit, parse_qs, parse_qsl
    from urllib.parse import quote as urllib_quote, quote_plus as urllib_quote_plus
    from urllib.parse import unquote as urllib_unquote, unquote_plus as urllib_unquote_plus, urlencode as urllib_urlencode
    from urllib.request import addinfourl as urllib_addinfourl, build_opener as urllib2_build_opener
    from urllib.request import BaseHandler as urllib2_BaseHandler, HTTPCookieProcessor as urllib2_HTTPCookieProcessor
    from urllib.request import HTTPHandler as urllib2_HTTPHandler, HTTPRedirectHandler as urllib2_HTTPRedirectHandler
    from urllib.request import HTTPSHandler as urllib2_HTTPSHandler, ProxyHandler as urllib2_ProxyHandler
    from urllib.request import Request as urllib2_Request, urlopen as urllib2_urlopen, urlopen as urllib_urlopen
    from urllib.request import urlretrieve as urllib_urlretrieve, install_opener as urllib2_install_opener
    from urllib.error import HTTPError as urllib2_HTTPError, URLError as urllib2_URLError

    isPY2 = False
