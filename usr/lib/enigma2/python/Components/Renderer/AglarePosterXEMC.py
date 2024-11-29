# -*- coding: utf-8 -*-
# by digiteng...07.2021,
# 08.2021(stb lang support),
# 09.2021 mini fixes
# © Provided that digiteng rights are protected, all or part of the code can be used, modified...
# russian and py3 support by sunriser...
# downloading in the background while zaping...
# by beber...03.2022,
# 03.2022 specific for EMC plugin ...
#
# for emc plugin,
# <widget source="Service" render="AglarePosterXEMC" position="100,100" size="185,278" />

from Components.Renderer.Renderer import Renderer
from enigma import ePixmap, eTimer, loadJPG, eEPGCache
from ServiceReference import ServiceReference
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.CurrentService import CurrentService
from Components.Sources.EventInfo import EventInfo
from Components.Sources.Event import Event
from Components.Renderer.AglarePosterXDownloadThread import AglarePosterXDownloadThread
from six import text_type

import os
import sys
import re
import time
import socket
from re import search, sub, I, S, escape

PY3 = False
if sys.version_info[0] >= 3:
    PY3 = True
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


try:
    from urllib import unquote, quote
except ImportError:
    from urllib.parse import unquote, quote


epgcache = eEPGCache.getInstance()
try:
    from Components.config import config
    lng = config.osd.language.value
except:
    lng = None
    pass


# def isMountedInRW(path):
    # testfile = path + '/tmp-rw-test'
    # os.system('touch ' + testfile)
    # if os.path.exists(testfile):
        # os.system('rm -f ' + testfile)
        # return True
    # return False


def isMountedInRW(mount_point):
    with open("/proc/mounts", "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) > 1 and parts[1] == mount_point:
                return True
    return False


path_folder = "/tmp/imovie"
if os.path.exists("/media/hdd"):
    if isMountedInRW("/media/hdd"):
        path_folder = "/media/hdd/imovie"
elif os.path.exists("/media/usb"):
    if isMountedInRW("/media/usb"):
        path_folder = "/media/usb/imovie"
elif os.path.exists("/media/mmc"):
    if isMountedInRW("/media/mmc"):
        path_folder = "/media/mmc/imovie"

if not os.path.exists(path_folder):
    os.makedirs(path_folder)


if PY3:
    pdbemc = queue.LifoQueue()
else:
    pdbemc = Queue.LifoQueue()


def quoteEventName(eventName):
    try:
        text = eventName.decode('utf8').replace(u'\x86', u'').replace(u'\x87', u'').encode('utf8')
    except:
        text = eventName
    return quote_plus(text, safe="+")


REGEX = re.compile(
    r'[\(\[].*?[\)\]]|'                    # Parentesi tonde o quadre
    r':?\s?odc\.\d+|'                      # odc. con o senza numero prima
    r'\d+\s?:?\s?odc\.\d+|'                # numero con odc.
    r'[:!]|'                               # due punti o punto esclamativo
    r'\s-\s.*|'                            # trattino con testo successivo
    r',|'                                  # virgola
    r'/.*|'                                # tutto dopo uno slash
    r'\|\s?\d+\+|'                         # | seguito da numero e +
    r'\d+\+|'                              # numero seguito da +
    r'\s\*\d{4}\Z|'                        # * seguito da un anno a 4 cifre
    r'[\(\[\|].*?[\)\]\|]|'                # Parentesi tonde, quadre o pipe
    r'(?:\"[\.|\,]?\s.*|\"|'               # Testo tra virgolette
    r'\.\s.+)|'                            # Punto seguito da testo
    r'Премьера\.\s|'                       # Specifico per il russo
    r'[хмтдХМТД]/[фс]\s|'                  # Pattern per il russo con /ф o /с
    r'\s[сС](?:езон|ерия|-н|-я)\s.*|'      # Stagione o episodio in russo
    r'\s\d{1,3}\s[чсЧС]\.?\s.*|'           # numero di parte/episodio in russo
    r'\.\s\d{1,3}\s[чсЧС]\.?\s.*|'         # numero di parte/episodio in russo con punto
    r'\s[чсЧС]\.?\s\d{1,3}.*|'             # Parte/Episodio in russo
    r'\d{1,3}-(?:я|й)\s?с-н.*',            # Finale con numero e suffisso russo
    re.DOTALL)


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
    return True


def remove_accents(string):
    if not isinstance(string, text_type):
        string = text_type(string, 'utf-8')
    string = sub(u"[àáâãäå]", 'a', string)
    string = sub(u"[èéêë]", 'e', string)
    string = sub(u"[ìíîï]", 'i', string)
    string = sub(u"[òóôõö]", 'o', string)
    string = sub(u"[ùúûü]", 'u', string)
    string = sub(u"[ýÿ]", 'y', string)
    return string


def unicodify(s, encoding='utf-8', norm=None):
    if not isinstance(s, text_type):
        s = text_type(s, encoding)
    if norm:
        from unicodedata import normalize
        s = normalize(norm, s)
    return s


def str_encode(text, encoding="utf8"):
    if not PY3:
        if isinstance(text, text_type):
            return text.encode(encoding)
    return text


def cutName(eventName=""):
    if eventName:
        eventName = eventName.replace('"', '').replace('.', '').replace(' | ', '')  # .replace('Х/Ф', '').replace('М/Ф', '').replace('Х/ф', '')
        eventName = eventName.replace('(18+)', '').replace('18+', '').replace('(16+)', '').replace('16+', '').replace('(12+)', '')
        eventName = eventName.replace('12+', '').replace('(7+)', '').replace('7+', '').replace('(6+)', '').replace('6+', '')
        eventName = eventName.replace('(0+)', '').replace('0+', '').replace('+', '')
        eventName = eventName.replace('المسلسل العربي', '')
        eventName = eventName.replace('مسلسل', '')
        eventName = eventName.replace('برنامج', '')
        eventName = eventName.replace('فيلم وثائقى', '')
        eventName = eventName.replace('حفل', '')
        return eventName
    return ""


def getCleanTitle(eventitle=""):
    # save_name = sub('\\(\d+\)$', '', eventitle)
    # save_name = sub('\\(\d+\/\d+\)$', '', save_name)  # remove episode-number " (xx/xx)" at the end
    # # save_name = sub('\ |\?|\.|\,|\!|\/|\;|\:|\@|\&|\'|\-|\"|\%|\(|\)|\[|\]\#|\+', '', save_name)
    save_name = eventitle.replace(' ^`^s', '').replace(' ^`^y', '')
    return save_name


def dataenc(data):
    if PY3:
        data = data.decode("utf-8")
    else:
        data = data.encode("utf-8")
    return data


def sanitize_filename(filename):
    # Replace spaces with underscores and remove invalid characters (like ':')
    sanitized = sub(r'[^\w\s-]', '', filename)  # Remove invalid characters
    # sanitized = sanitized.replace(' ', '_')      # Replace spaces with underscores
    # sanitized = sanitized.replace('-', '_')      # Replace dashes with underscores
    return sanitized.strip()


def convtext(text=''):
    try:
        if text is None:
            print('return None original text: ' + str(type(text)))
            return
        if text == '':
            print('text is an empty string')
        else:
            print('original text:' + text)
            text = text.lower()
            print('lowercased text:' + text)
            text = text.lstrip()

            # text = cutName(text)
            # text = getCleanTitle(text)

            if text.endswith("the"):
                text = "the " + text[:-4]

            # Modifiche personalizzate
            if 'giochi olimpici parigi' in text:
                text = 'olimpiadi di parigi'
            if 'bruno barbieri' in text:
                text = text.replace('bruno barbieri', 'brunobarbierix')
            if "anni '60" in text:
                text = "anni 60"
            if 'tg regione' in text:
                text = 'tg3'
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
            if 'alessandro borghese - 4 ristoranti' in text:
                text = 'alessandroborgheseristoranti'
            if 'alessandro borghese: 4 ristoranti' in text:
                text = 'alessandroborgheseristoranti'

            cutlist = ['x264', '720p', '1080p', '1080i', 'pal', 'german', 'english', 'ws', 'dvdrip', 'unrated',
                       'retail', 'web-dl', 'dl', 'ld', 'mic', 'md', 'dvdr', 'bdrip', 'bluray', 'dts', 'uncut', 'anime',
                       'ac3md', 'ac3', 'ac3d', 'ts', 'dvdscr', 'complete', 'internal', 'dtsd', 'xvid', 'divx', 'dubbed',
                       'line.dubbed', 'dd51', 'dvdr9', 'dvdr5', 'h264', 'avc', 'webhdtvrip', 'webhdrip', 'webrip',
                       'webhdtv', 'webhd', 'hdtvrip', 'hdrip', 'hdtv', 'ituneshd', 'repack', 'sync', '1^tv', '1^ tv',
                       '1^ visione rai', '1^ visione', ' - prima tv', ' - primatv', 'prima visione',
                       'film -', 'de filippi', 'first screening',
                       'live:', 'new:', 'film:', 'première diffusion', 'nouveau:', 'en direct:',
                       'premiere:', 'estreno:', 'nueva emisión:', 'en vivo:'
                       ]
            for word in cutlist:
                text = text.replace(word, '')
            text = ' '.join(text.split())
            print(text)

            text = cutName(text)
            text = getCleanTitle(text)

            text = text.partition("-")[0]  # Mantieni solo il testo prima del primo "-"

            # Pulizia finale
            text = text.replace('.', ' ').replace('-', ' ').replace('_', ' ').replace('+', '')

            # Rimozione pattern specifici
            if search(r'[Ss][0-9]+[Ee][0-9]+', text):
                text = sub(r'[Ss][0-9]+[Ee][0-9]+.*[a-zA-Z0-9_]+', '', text, flags=S | I)
            text = sub(r'\(.*\)', '', text).rstrip()
            text = text.partition("(")[0]
            text = sub(r"\\s\d+", "", text)
            text = text.partition(":")[0]
            text = sub(r'(odc.\s\d+)+.*?FIN', '', text)
            text = sub(r'(odc.\d+)+.*?FIN', '', text)
            text = sub(r'(\d+)+.*?FIN', '', text)
            text = sub('FIN', '', text)
            # remove episode number in arabic series
            text = sub(r' +ح', '', text)
            # remove season number in arabic series
            text = sub(r' +ج', '', text)
            # remove season number in arabic series
            text = sub(r' +م', '', text)

            # # Rimuovi accenti e normalizza
            text = remove_accents(text)
            print('remove_accents text: ' + text)

            # Forzature finali
            text = text.replace('XXXXXX', '60')
            text = text.replace('brunobarbierix', 'bruno barbieri - 4 hotel')
            text = text.replace('alessandroborgheseristoranti', 'alessandro borghese - 4 ristoranti')
            text = text.replace('il ritorno di colombo', 'colombo')

            # text = sanitize_filename(text)
            # print('sanitize_filename text: ' + text)
            return text.capitalize()
    except Exception as e:
        print('convtext error: ' + str(e))
        pass


class PosterDBEMC(AglarePosterXDownloadThread):
    def __init__(self):
        AglarePosterXDownloadThread.__init__(self)
        self.logdbg = None
        self.pstcanal = None

    def run(self):
        self.logDB("[QUEUE] : Initialized")
        while True:
            canal = pdbemc.get()
            self.logDB("[QUEUE] : {} : {}-{} ({})".format(canal[0], canal[1], canal[2], canal[5]))
            self.pstcanal = convtext(canal[5])
            if self.pstcanal != 'None' or self.pstcanal is not None:
                dwn_poster = path_folder + '/' + self.pstcanal + ".jpg"
            else:
                print('none type xxxxxxxxxx- posterx')
                return
            if os.path.exists(dwn_poster):
                os.utime(dwn_poster, (time.time(), time.time()))
            '''
            # if lng == "fr":
                # if not os.path.exists(dwn_poster):
                    # val, log = self.search_molotov_google(dwn_poster, canal[5], canal[4], canal[3], canal[0])
                    # self.logDB(log)
                # if not os.path.exists(dwn_poster):
                    # val, log = self.search_programmetv_google(dwn_poster, canal[5], canal[4], canal[3], canal[0])
                    # self.logDB(log)
            '''
            if not os.path.exists(dwn_poster):
                val, log = self.search_tmdb(dwn_poster, self.pstcanal, canal[4], canal[3])
                self.logDB(log)
            elif not os.path.exists(dwn_poster):
                val, log = self.search_tvdb(dwn_poster, self.pstcanal, canal[4], canal[3])
                self.logDB(log)
            elif not os.path.exists(dwn_poster):
                val, log = self.search_fanart(dwn_poster, self.pstcanal, canal[4], canal[3])
                self.logDB(log)
            elif not os.path.exists(dwn_poster):
                val, log = self.search_imdb(dwn_poster, self.pstcanal, canal[4], canal[3])
                self.logDB(log)
            elif not os.path.exists(dwn_poster):
                val, log = self.search_google(dwn_poster, self.pstcanal, canal[4], canal[3], canal[0])
                self.logDB(log)
            pdbemc.task_done()

    def logDB(self, logmsg):
        import traceback
        try:
            with open("/tmp/AglarePosterXEMC.log", "a") as w:
                w.write("%s\n" % logmsg)
        except Exception as e:
            print('logDB error:', str(e))
            traceback.print_exc()


threadDBemc = PosterDBEMC()
threadDBemc.start()


class AglarePosterXEMC(Renderer):
    def __init__(self):
        Renderer.__init__(self)
        adsl = intCheck()
        if not adsl:
            return
        self.canal = [None, None, None, None, None, None]
        self.logdbg = None
        self.pstcanal = None

        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.showPoster)
        except:
            self.timer.callback.append(self.showPoster)

    def applySkin(self, desktop, parent):
        attribs = []
        for (attrib, value,) in self.skinAttributes:
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
            try:
                if isinstance(self.source, ServiceEvent):  # source="Service"
                    self.canal[0] = None
                    self.canal[1] = self.source.event.getBeginTime()
                    self.canal[2] = self.source.event.getEventName()
                    self.canal[3] = self.source.event.getExtendedDescription()
                    self.canal[4] = self.source.event.getShortDescription()
                    self.canal[5] = self.source.service.getPath().split(".ts")[0] + ".jpg"
                elif isinstance(self.source, CurrentService):  # source="session.CurrentService"
                    self.canal[0] = None
                    self.canal[1] = None
                    self.canal[2] = None
                    self.canal[3] = None
                    self.canal[4] = None
                    self.canal[5] = self.source.getCurrentServiceReference().getPath().split(".ts")[0] + ".jpg"
                else:
                    self.logPoster("Service : Others")
                    self.canal = [None, None, None, None, None, None]
                    if self.instance:
                        self.instance.hide()
                    return
            except Exception as e:
                self.logPoster("Error (service) : " + str(e))
                if self.instance:
                    self.instance.hide()
                return
            try:
                cn = re.findall(".*? - (.*?) - (.*?).jpg", self.canal[5])
                if cn and len(cn) > 0 and len(cn[0]) > 1:
                    self.canal[0] = cn[0][0].strip()
                    if not self.canal[2]:
                        self.canal[2] = cn[0][1].strip()
                self.logPoster("Service : {} - {} => {}".format(self.canal[0], self.canal[2], self.canal[5]))
                if self.canal[5]:                             
                    self.timer.start(100, True)
                elif self.canal[0] and self.canal[2]:
                    self.logPoster("Downloading poster...")
                    canal = self.canal[:]
                    pdbemc.put(canal)
                    start_new_thread(self.waitPoster, ())
                else:
                    self.logPoster("Not detected...")
                    if self.instance:
                        self.instance.hide()
                    return
            except Exception as e:
                self.logPoster("Error (reading file) : " + str(e))
                if self.instance:
                    self.instance.hide()
                return

    def showPoster(self):
        if self.instance:
            self.instance.hide()
        if self.canal[5]:
            # if self.pstcanal is not None and not os.path.exists(self.pstcanal):
            self.pstcanal = convtext(self.canal[5])
            self.pstrNm = self.path + '/' + str(self.pstcanal) + ".jpg"
            self.pstcanal = str(self.pstrNm)
            if self.pstrNm and os.path.exists(self.pstrNm):
                # if os.path.exists(self.pstrNm):
                print('showPoster----')
                self.logPoster("[LOAD : showPoster] {}".format(self.pstcanal))
                self.instance.setPixmap(loadJPG(self.pstcanal))
                self.instance.setScale(1)
                self.instance.show()

    def waitPoster(self):
        if self.instance:
            self.instance.hide()
        if self.canal[5]:
            # if self.pstcanal is not None and not os.path.exists(self.pstcanal):
            self.pstcanal = convtext(self.canal[5])
            self.pstrNm = self.path + '/' + str(self.pstcanal) + ".jpg"
            self.pstcanal = str(self.pstrNm)
            loop = 180
            found = None
            self.logPoster("[LOOP: waitPoster] {}".format(self.pstcanal))
            while loop >= 0:
                if self.pstrNm and os.path.exists(self.pstrNm):
                    # if os.path.exists(self.pstrNm):
                    loop = 0
                    found = True
                    time.sleep(0.5)
                    loop -= 1
            if found:
                self.timer.start(50, True)

    def logPoster(self, logmsg):
        import traceback
        try:
            with open("/tmp/AglarePosterXEMC.log", "a") as w:
                w.write("%s\n" % logmsg)
        except Exception as e:
            print('logPoster error:', str(e))
            traceback.print_exc()
