#!/usr/bin/python
# -*- coding: utf-8 -*-

# by digiteng...07.2021,
# 08.2021(stb lang support),
# 09.2021 mini fixes
# edit by lululla 07.2022
# recode from lululla 2023
# © Provided that digiteng rights are protected, all or part of the code can be used, modified...
# russian and py3 support by sunriser...
# downloading in the background while zaping...
# by beber...03.2022,
# 03.2022 several enhancements : several renders with one queue thread, google search (incl. molotov for france) + autosearch & autoclean thread ...
# for infobar,
# <widget source="session.Event_Now" render="AglareBackdropX" position="100,100" size="680,1000" />
# <widget source="session.Event_Next" render="AglareBackdropX" position="100,100" size="680,1000" />
# <widget source="session.Event_Now" render="AglareBackdropX" position="100,100" size="680,1000" nexts="2" />
# <widget source="session.CurrentService" render="AglareBackdropX" position="100,100" size="680,1000" nexts="3" />
# for ch,
# <widget source="ServiceEvent" render="AglareBackdropX" position="100,100" size="680,1000" nexts="2" />
# <widget source="ServiceEvent" render="AglareBackdropX" position="100,100" size="185,278" nexts="2" />
# for epg, event
# <widget source="Event" render="AglareBackdropX" position="100,100" size="680,1000" />
# <widget source="Event" render="AglareBackdropX" position="100,100" size="680,1000" nexts="2" />
# or put tag -->  path="/media/hdd/backdrop"
from __future__ import print_function
from Components.Renderer.Renderer import Renderer
from Components.Renderer.AglareBackdropXDownloadThread import AglareBackdropXDownloadThread
from Components.Sources.CurrentService import CurrentService
from Components.Sources.Event import Event
from Components.Sources.EventInfo import EventInfo
from Components.Sources.ServiceEvent import ServiceEvent
from Components.config import config
from ServiceReference import ServiceReference
from enigma import ePixmap, loadJPG, eEPGCache
from enigma import eTimer
import NavigationInstance
import os
import re
import socket
import sys
import time
import shutil


PY3 = False
if sys.version_info[0] >= 3:
    PY3 = True
    unicode = str
    unichr = chr
    long = int
    import queue
    import html
    html_parser = html
    from _thread import start_new_thread
    from urllib.error import HTTPError, URLError
    from urllib.request import urlopen
    from urllib.parse import quote_plus
else:
    import Queue
    from thread import start_new_thread
    from urllib2 import HTTPError, URLError
    from urllib2 import urlopen
    from urllib import quote_plus
    from HTMLParser import HTMLParser
    html_parser = HTMLParser()


def isMountReadonly(mnt):
    mount_point = ''
    with open('/proc/mounts') as f:
        for line in f:
            line = line.split(',')[0]
            line = line.split()
            print('line ', line)
            try:
                device, mount_point, filesystem, flags = line
            except Exception as err:
                print("Error: %s" % err)
            if mount_point == mnt:
                return 'ro' in flags
    return "mount: '%s' doesn't exist" % mnt


def isMountedInRW(path):
    testfile = path + '/tmp-rw-test'
    os.system('touch ' + testfile)
    if os.path.exists(testfile):
        os.system('rm -f ' + testfile)
        return True
    return False


path_folder = "/tmp/backdrop"
if os.path.exists("/media/hdd"):
    if isMountedInRW("/media/hdd"):
        path_folder = "/media/hdd/backdrop"
if os.path.exists("/media/usb"):
    if isMountedInRW("/media/usb"):
        path_folder = "/media/usb/backdrop"
if os.path.exists("/media/mmc"):
    if isMountedInRW("/media/mmc"):
        path_folder = "/media/mmc/backdrop"
if not os.path.exists(path_folder):
    os.makedirs(path_folder)


epgcache = eEPGCache.getInstance()
apdb = dict()


try:
    lng = config.osd.language.value
    lng = lng[:-3]
except:
    lng = 'en'
    pass


# SET YOUR PREFERRED BOUQUET FOR AUTOMATIC BACKDROP GENERATION
# WITH THE NUMBER OF ITEMS EXPECTED (BLANK LINE IN BOUQUET CONSIDERED)
# IF NOT SET OR WRONG FILE THE AUTOMATIC BACKDROP GENERATION WILL WORK FOR
# THE CHANNELS THAT YOU ARE VIEWING IN THE ENIGMA SESSION


def SearchBouquetTerrestrial():
    import glob
    import codecs
    file = '/etc/enigma2/userbouquet.favourites.tv'
    for file in sorted(glob.glob('/etc/enigma2/*.tv')):
        with codecs.open(file, "r", encoding="utf-8") as f:
            file = f.read()
            x = file.strip().lower()
            if x.find('eeee') != -1:
                if x.find('82000') == -1 and x.find('c0000') == -1:
                    return file
                    break


if SearchBouquetTerrestrial():
    autobouquet_file = SearchBouquetTerrestrial()
else:
    autobouquet_file = '/etc/enigma2/userbouquet.favourites.tv'
# print('autobouquet_file = ', autobouquet_file)
autobouquet_count = 70
# Short script for Automatic poster generation on your preferred bouquet
if not os.path.exists(autobouquet_file):
    autobouquet_file = None
    autobouquet_count = 0
else:
    with open(autobouquet_file, 'r') as f:
        lines = f.readlines()
    if autobouquet_count > len(lines):
        autobouquet_count = len(lines)
    for i in range(autobouquet_count):
        if '#SERVICE' in lines[i]:
            line = lines[i][9:].strip().split(':')
            if len(line) == 11:
                value = ':'.join((line[3], line[4], line[5], line[6]))
                if value != '0:0:0:0':
                    service = ':'.join((line[0], line[1], line[2], line[3], line[4], line[5], line[6], line[7], line[8], line[9], line[10]))
                    apdb[i] = service


try:
    folder_size = sum([sum(map(lambda fname: os.path.getsize(os.path.join(path_folder, fname)), files)) for folder_p, folders, files in os.walk(path_folder)])
    agposter = "%0.f" % (folder_size / (1024 * 1024.0))
    if agposter >= "5":
        shutil.rmtree(path_folder)
except:
    pass


def OnclearMem():
    try:
        os.system('sync')
        os.system('echo 1 > /proc/sys/vm/drop_caches')
        os.system('echo 2 > /proc/sys/vm/drop_caches')
        os.system('echo 3 > /proc/sys/vm/drop_caches')
    except:
        pass


REGEX = re.compile(
    r'([\(\[]).*?([\)\]])|'
    r'(: odc.\d+)|'
    r'(\d+: odc.\d+)|'
    r'(\d+ odc.\d+)|(:)|'
    r'( -(.*?).*)|(,)|'
    r'!|'
    r'/.*|'
    r'\|\s[0-9]+\+|'
    r'[0-9]+\+|'
    r'\s\*\d{4}\Z|'
    r'([\(\[\|].*?[\)\]\|])|'
    r'(\"|\"\.|\"\,|\.)\s.+|'
    r'\"|:|'
    r'Премьера\.\s|'
    r'(х|Х|м|М|т|Т|д|Д)/ф\s|'
    r'(х|Х|м|М|т|Т|д|Д)/с\s|'
    r'\s(с|С)(езон|ерия|-н|-я)\s.+|'
    r'\s\d{1,3}\s(ч|ч\.|с\.|с)\s.+|'
    r'\.\s\d{1,3}\s(ч|ч\.|с\.|с)\s.+|'
    r'\s(ч|ч\.|с\.|с)\s\d{1,3}.+|'
    r'\d{1,3}(-я|-й|\sс-н).+|', re.DOTALL)


def intCheck():
    try:
        response = urlopen("http://google.com", None, 5)
        response.close()
    except HTTPError:
        return False
    except URLError:
        return False
    except socket.timeout:
        return False
    else:
        return True


def remove_accents(string):
    if type(string) is not unicode:
        string = unicode(string, encoding='utf-8')
    string = re.sub(u"[àáâãäå]", 'a', string)
    string = re.sub(u"[èéêë]", 'e', string)
    string = re.sub(u"[ìíîï]", 'i', string)
    string = re.sub(u"[òóôõö]", 'o', string)
    string = re.sub(u"[ùúûü]", 'u', string)
    string = re.sub(u"[ýÿ]", 'y', string)
    return string


def get_safe_filename(filename, fallback=''):
    '''Convert filename to safe filename'''
    import unicodedata
    import six
    name = filename  # .replace(' ', '_').replace('/', '_')
    if isinstance(name, six.text_type):
        name = name.encode('utf-8')
    name = unicodedata.normalize('NFKD', six.text_type(name, 'utf_8', errors='ignore')).encode('ASCII', 'ignore')
    name = re.sub(b'[^a-z0-9-_]', b' ', name.lower())
    if not name:
        name = fallback
    return six.ensure_str(name)


def UNAC(string):
    if not PY3:
        if type(string) is not unicode:
            string = unicode(string, encoding='utf-8')
    string = re.sub(u"u0026", "&", string)
    string = re.sub(u"u003d", "=", string)
    string = html_parser.unescape(string)
    string = re.sub(r"[,!?\.\"]", ' ', string)
    string = re.sub(r"[-/:']", '', string)
    string = re.sub(u"[ÀÁÂÃÄàáâãäåª]", 'a', string)
    string = re.sub(u"[ÈÉÊËèéêë]", 'e', string)
    string = re.sub(u"[ÍÌÎÏìíîï]", 'i', string)
    string = re.sub(u"[ÒÓÔÕÖòóôõöº]", 'o', string)
    string = re.sub(u"[ÙÚÛÜùúûü]", 'u', string)
    string = re.sub(u"[Ññ]", 'n', string)
    string = re.sub(u"[Çç]", 'c', string)
    string = re.sub(u"[Ÿýÿ]", 'y', string)
    string = re.sub(r"[^a-zA-Z0-9 ]", "", string)
    string = string.lower()
    string = re.sub(r'\s{1,}', ' ', string)
    string = string.strip()
    return string


def unicodify(s, encoding='utf-8', norm=None):
    if not isinstance(s, unicode):
        s = unicode(s, encoding)
    if norm:
        from unicodedata import normalize
        s = normalize(norm, s)
    return s


def str_encode(text, encoding="utf8"):
    if not PY3:
        if isinstance(text, unicode):
            return text.encode(encoding)
        # else:
            # return text
    # else:
    return text


def cutName(eventName=""):
    if eventName:
        eventName = eventName.replace('"', '').replace('Х/Ф', '').replace('М/Ф', '').replace('Х/ф', '').replace('.', '').replace(' | ', '')
        eventName = eventName.replace('(18+)', '').replace('18+', '').replace('(16+)', '').replace('16+', '').replace('(12+)', '')
        eventName = eventName.replace('12+', '').replace('(7+)', '').replace('7+', '').replace('(6+)', '').replace('6+', '')
        eventName = eventName.replace('(0+)', '').replace('0+', '').replace('+', '')
        return eventName
    return ""


def getCleanTitle(eventitle=""):
    # save_name = re.sub('\\(\d+\)$', '', eventitle)
    # save_name = re.sub('\\(\d+\/\d+\)$', '', save_name)  # remove episode-number " (xx/xx)" at the end
    # # save_name = re.sub('\ |\?|\.|\,|\!|\/|\;|\:|\@|\&|\'|\-|\"|\%|\(|\)|\[|\]\#|\+', '', save_name)
    save_name = eventitle.replace(' ^`^s', '').replace(' ^`^y', '')
    return save_name


def quoteEventName(eventName):
    try:
        text = eventName.decode('utf8').replace(u'\x86', u'').replace(u'\x87', u'').encode('utf8')
    except:
        text = eventName
    return quote_plus(text, safe="+")


def dataenc(data):
    if PY3:
        data = page.decode("utf-8")
    else:
        data = page.encode("utf-8")
    return data


def convtext(text=''):
    try:
        if text != '' or text is not None or text != 'None':
            print('original text: ', text)
            text = remove_accents(text)
            print('remove_accents text: ', text)
            text = UNAC(text)
            text = cutName(text)
            text = getCleanTitle(text)
            text = get_safe_filename(text)

            # text = text.replace("\xe2\x80\x93", "").replace('\xc2\x86', '').replace('\xc2\x87', '')  # replace special
            text = text.lower()
            text = text.replace('1^ visione rai', '').replace('1^ visione', '').replace('primatv', '').replace('1^tv', '')
            text = text.replace('prima visione', '').replace('1^ tv', '').replace('((', '(').replace('))', ')')
            text = text.replace('live:', '')
            if 'studio aperto' in text:
                text = 'studio aperto'
            if 'josephine ange gardien' in text:
                text = 'josephine ange gardien'
            if 'elementary' in text:
                text = 'elementary'
            if 'squadra speciale cobra 11' in text:
                text = 'squadra speciale cobra 11'
            if 'criminal minds' in text:
                text = 'criminal minds'
            if 'i delitti del barlume' in text:
                text = 'i delitti del barlume'
            if 'senza traccia' in text:
                text = 'senza traccia'
            if 'hudson e rex' in text:
                text = 'hudson e rex'
            if 'ben-hur' in text:
                text = 'ben-hur'
            if 'la7' in text:
                text = 'la7'
            if 'skytg24' in text:
                text = 'skytg24'
            # for oden2014
            if ' - ح - ' in text:
                print('1 text episode:', text)
                text = text.partition(' - ح - ')[0] 
                print('2 text episode:', text)

            if text.endswith("the"):
                text.rsplit(" ", 1)[0]
                text = text.rsplit(" ", 1)[0]
                text = "the " + str(text)
            text = text + 'FIN'
            if re.search(r'[Ss][0-9][Ee][0-9]+.*?FIN', text):
                text = re.sub(r'[Ss][0-9][Ee][0-9]+.*?FIN', '', text)
            if re.search(r'[Ss][0-9] [Ee][0-9]+.*?FIN', text):
                text = re.sub(r'[Ss][0-9] [Ee][0-9]+.*?FIN', '', text)
            text = re.sub(r'(odc.\s\d+)+.*?FIN', '', text)
            text = re.sub(r'(odc.\d+)+.*?FIN', '', text)
            text = re.sub(r'(\d+)+.*?FIN', '', text)
            text = text.partition("(")[0] + 'FIN'  # .strip()
            text = text.partition("(")[0]  # .strip()
            text = text.partition(":")[0]  # .strip()
            text = text.partition(" -")[0]  # .strip()
            text = re.sub(' - +.+?FIN', '', text)  # all episodes and series ????
            text = re.sub('FIN', '', text)
            text = re.sub(r'^\|[\w\-\|]*\|', '', text)
            text = re.sub(r"[-,?!/\.\":]", '', text)  # replace (- or , or ! or / or . or " or :) by space

            text = text.strip()
            text = text.capitalize()
            # print('Final text: ', text)
        else:
            text = text
        return text
    except Exception as e:
        print('convtext error: ', e)
        pass


if PY3:
    pdb = queue.LifoQueue()
else:
    pdb = Queue.LifoQueue()


class BackdropDB(AglareBackdropXDownloadThread):
    def __init__(self):
        AglareBackdropXDownloadThread.__init__(self)
        self.logdbg = None

    def run(self):
        self.logDB("[QUEUE] : Initialized")
        while True:
            canal = pdb.get()
            self.logDB("[QUEUE] : {} : {}-{} ({})".format(canal[0], canal[1], canal[2], canal[5]))
            self.pstcanal = convtext(canal[5])
            if self.pstcanal and self.pstcanal != 'None' or self.pstcanal is not None:
                dwn_backdrop = path_folder + '/' + self.pstcanal + ".jpg"
                if os.path.exists(dwn_backdrop):
                    os.utime(dwn_backdrop, (time.time(), time.time()))
                if lng == "fr":
                    if not os.path.exists(dwn_backdrop):
                        val, log = self.search_molotov_google(dwn_backdrop, canal[5], canal[4], canal[3], canal[0])
                        self.logDB(log)
                    if not os.path.exists(dwn_backdrop):
                        val, log = self.search_programmetv_google(dwn_backdrop, canal[5], canal[4], canal[3], canal[0])
                        self.logDB(log)
                if not os.path.exists(dwn_backdrop):
                    val, log = self.search_tmdb(dwn_backdrop, self.pstcanal, canal[4], canal[3])
                    self.logDB(log)
                elif not os.path.exists(dwn_backdrop):
                    val, log = self.search_tvdb(dwn_backdrop, self.pstcanal, canal[4], canal[3])
                    self.logDB(log)
                elif not os.path.exists(dwn_backdrop):
                    val, log = self.search_fanart(dwn_backdrop, self.pstcanal, canal[4], canal[3])
                    self.logDB(log)
                elif not os.path.exists(dwn_backdrop):
                    val, log = self.search_imdb(dwn_backdrop, self.pstcanal, canal[4], canal[3])
                    self.logDB(log)
                elif not os.path.exists(dwn_backdrop):
                    val, log = self.search_google(dwn_backdrop, self.pstcanal, canal[4], canal[3], canal[0])
                    self.logDB(log)
                pdb.task_done()

    def logDB(self, logmsg):
        try:
            w = open("/tmp/BackdropDB.log", "a+")
            w.write("%s\n" % logmsg)
            w.close()
        except Exception as e:
            print('logDB exceptions', str(e))


threadDB = BackdropDB()
threadDB.start()


class BackdropAutoDB(AglareBackdropXDownloadThread):
    def __init__(self):
        AglareBackdropXDownloadThread.__init__(self)
        self.logdbg = None

    def run(self):
        self.logAutoDB("[AutoDB] *** Initialized")
        while True:
            time.sleep(7200)  # 7200 - Start every 2 hours
            self.logAutoDB("[AutoDB] *** Running ***")
            pstcanal = ''
            # AUTO ADD NEW FILES - 1440 (24 hours ahead)
            for service in apdb.values():
                try:
                    events = epgcache.lookupEvent(['IBDCTESX', (service, 0, -1, 1440)])
                    newfd = 0
                    newcn = None
                    for evt in events:
                        canal = [None, None, None, None, None, None]
                        if PY3:
                            canal[0] = ServiceReference(service).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
                        else:
                            canal[0] = ServiceReference(service).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '').encode('utf-8')
                        if evt[1] is None or evt[4] is None or evt[5] is None or evt[6] is None:
                            self.logAutoDB("[AutoDB] *** missing epg for {}".format(canal[0]))
                        else:
                            canal[1] = evt[1]
                            canal[2] = evt[4]
                            canal[3] = evt[5]
                            canal[4] = evt[6]
                            canal[5] = canal[2]
                            pstcanal = convtext(canal[5])
                            pstrNm = path_folder + '/' + pstcanal + ".jpg"
                            self.pstcanal = str(pstrNm)
                            dwn_backdrop = self.pstcanal
                            if os.path.exists(dwn_backdrop):
                                os.utime(dwn_backdrop, (time.time(), time.time()))
                            if lng == "fr":
                                if not os.path.exists(dwn_backdrop):
                                    val, log = self.search_molotov_google(dwn_backdrop, pstcanal, canal[4], canal[3], canal[0])
                                    if val and log.find("SUCCESS"):
                                        newfd += 1
                                if not os.path.exists(dwn_backdrop):
                                    val, log = self.search_programmetv_google(dwn_backdrop, pstcanal, canal[4], canal[3], canal[0])
                                    if val and log.find("SUCCESS"):
                                        newfd += 1
                            if not os.path.exists(dwn_backdrop):
                                val, log = self.search_tmdb(dwn_backdrop, pstcanal, canal[4], canal[3], canal[0])
                                if val and log.find("SUCCESS"):
                                    newfd += 1
                            elif not os.path.exists(dwn_backdrop):
                                val, log = self.search_tvdb(dwn_backdrop, pstcanal, canal[4], canal[3], canal[0])
                                if val and log.find("SUCCESS"):
                                    newfd += 1
                            elif not os.path.exists(dwn_backdrop):
                                val, log = self.search_fanart(dwn_backdrop, pstcanal, canal[4], canal[3], canal[0])
                                if val and log.find("SUCCESS"):
                                    newfd += 1
                            elif not os.path.exists(dwn_backdrop):
                                val, log = self.search_imdb(dwn_backdrop, pstcanal, canal[4], canal[3], canal[0])
                                if val and log.find("SUCCESS"):
                                    newfd += 1
                            elif not os.path.exists(dwn_backdrop):
                                val, log = self.search_google(dwn_backdrop, pstcanal, canal[4], canal[3], canal[0])
                                if val and log.find("SUCCESS"):
                                    newfd += 1
                            newcn = canal[0]
                    self.logAutoDB("[AutoDB] {} new file(s) added ({})".format(newfd, newcn))
                except Exception as e:
                    self.logAutoDB("[AutoDB] *** service error ({})".format(e))
            # AUTO REMOVE OLD FILES
            now_tm = time.time()
            emptyfd = 0
            oldfd = 0
            for f in os.listdir(path_folder):
                diff_tm = now_tm - os.path.getmtime(path_folder + '/' + f)
                if diff_tm > 120 and os.path.getsize(path_folder + '/' + f) == 0:  # Detect empty files > 2 minutes
                    os.remove(path_folder + '/' + f)
                    emptyfd += 1
                if diff_tm > 31536000:  # Detect old files > 365 days old
                    os.remove(path_folder + '/' + f)
                    oldfd = oldfd + 1
            self.logAutoDB("[AutoDB] {} old file(s) removed".format(oldfd))
            self.logAutoDB("[AutoDB] {} empty file(s) removed".format(emptyfd))
            self.logAutoDB("[AutoDB] *** Stopping ***")

    def logAutoDB(self, logmsg):
        try:
            w = open("/tmp/BackdropAutoDB.log", "a+")
            w.write("%s\n" % logmsg)
            w.close()
        except Exception as e:
            print('error logAutoDB 2 ', e)


threadAutoDB = BackdropAutoDB()
threadAutoDB.start()


class AglareBackdropX(Renderer):
    def __init__(self):
        adsl = intCheck()
        if not adsl:
            return
        Renderer.__init__(self)
        self.nxts = 0
        self.path = path_folder  # + '/'
        self.canal = [None, None, None, None, None, None]
        self.oldCanal = None
        self.logdbg = None
        self.pstcanal = ''
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.showBackdrop)
        except:
            self.timer.callback.append(self.showBackdrop)
        self.timer.start(10, True)

    def applySkin(self, desktop, parent):
        attribs = []
        for (attrib, value,) in self.skinAttributes:
            if attrib == "nexts":
                self.nxts = int(value)
            if attrib == "path":
                self.path = str(value)
            attribs.append((attrib, value))
        self.skinAttributes = attribs
        return Renderer.applySkin(self, desktop, parent)

    GUI_WIDGET = ePixmap

    def changed(self, what):
        if not self.instance:
            return
        if what[0] == self.CHANGED_CLEAR:
            if self.instance:
                self.instance.hide()
            return
        if what[0] != self.CHANGED_CLEAR:
            servicetype = None
            try:
                service = None
                if isinstance(self.source, ServiceEvent):  # source="ServiceEvent"
                    service = self.source.getCurrentService()
                    servicetype = "ServiceEvent"
                elif isinstance(self.source, CurrentService):  # source="session.CurrentService"
                    service = self.source.getCurrentServiceRef()
                    servicetype = "CurrentService"
                elif isinstance(self.source, EventInfo):  # source="session.Event_Now" or source="session.Event_Next"
                    service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
                    servicetype = "EventInfo"
                elif isinstance(self.source, Event):  # source="Event"
                    if self.nxts:
                        service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
                    else:
                        self.canal[0] = None
                        self.canal[1] = self.source.event.getBeginTime()
                        if PY3:
                            self.canal[2] = self.source.event.getEventName().replace('\xc2\x86', '').replace('\xc2\x87', '')
                        else:
                            self.canal[2] = self.source.event.getEventName().replace('\xc2\x86', '').replace('\xc2\x87', '').encode('utf-8')
                        self.canal[3] = self.source.event.getExtendedDescription()
                        self.canal[4] = self.source.event.getShortDescription()
                        self.canal[5] = self.canal[2]
                    servicetype = "Event"
                if service is not None:
                    events = epgcache.lookupEvent(['IBDCTESX', (service.toString(), 0, -1, -1)])
                    if PY3:
                        self.canal[0] = ServiceReference(service).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')  # .encode('utf-8')
                    else:
                        self.canal[0] = ServiceReference(service).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '').encode('utf-8')
                    self.canal[1] = events[self.nxts][1]
                    self.canal[2] = events[self.nxts][4]
                    self.canal[3] = events[self.nxts][5]
                    self.canal[4] = events[self.nxts][6]
                    self.canal[5] = self.canal[2]
                    if not autobouquet_file:
                        if self.canal[0] not in apdb:
                            apdb[self.canal[0]] = service.toString()
            except Exception as e:
                self.logBackdrop("Error (service) : " + str(e))
                if self.instance:
                    self.instance.hide()
                return
            if not servicetype or servicetype is None:
                self.logBackdrop("Error service type undefined")
                if self.instance:
                    self.instance.hide()
                return
            try:
                curCanal = "{}-{}".format(self.canal[1], self.canal[2])
                if curCanal == self.oldCanal:
                    return
                self.oldCanal = curCanal
                self.logBackdrop("Service: {} [{}] : {} : {}".format(servicetype, self.nxts, self.canal[0], self.oldCanal))
                pstcanal = convtext(self.canal[5])
                backrNm = self.path + '/' + str(pstcanal) + ".jpg"
                self.backrNm = str(backrNm)
                if os.path.exists(self.backrNm):
                    self.timer.start(10, True)
                else:
                    canal = self.canal[:]
                    pdb.put(canal)
                    start_new_thread(self.waitBackdrop, ())
            except Exception as e:
                self.logBackdrop("Error (eFile): " + str(e))
                if self.instance:
                    self.instance.hide()
                return

    def showBackdrop(self):
        if self.instance:
            self.instance.hide()
        if self.canal[5]:
            if not os.path.exists(self.backrNm):
                pstcanal = convtext(self.canal[5])
                backrNm = self.path + '/' + str(pstcanal) + ".jpg"
                self.backrNm = str(backrNm)
            if os.path.exists(self.backrNm):
                self.logBackdrop("[LOAD : showBackdrop] {}".format(self.backrNm))
                self.instance.setPixmap(loadJPG(self.backrNm))
                self.instance.setScale(1)
                self.instance.show()

    def waitBackdrop(self):
        if self.instance:
            self.instance.hide()
        if self.canal[5]:
            if not os.path.exists(self.backrNm):
                pstcanal = convtext(self.canal[5])
                backrNm = self.path + '/' + str(pstcanal) + ".jpg"
                self.backrNm = str(backrNm)
            loop = 180
            found = None
            self.logBackdrop("[LOOP: waitBackdrop] {}".format(self.backrNm))
            while loop >= 0:
                if os.path.exists(self.backrNm):
                    loop = 0
                    found = True
                time.sleep(0.5)
                loop = loop - 1
            if found:
                self.timer.start(20, True)

    def logBackdrop(self, logmsg):
        try:
            w = open("/tmp/AglareBackdropX.log", "a+")
            w.write("%s\n" % logmsg)
            w.close()
        except Exception as e:
            print('logBackdrop error', e)
