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


def isMountedInRW(path):
    testfile = path + '/tmp-rw-test'
    os.system('touch ' + testfile)
    if os.path.exists(testfile):
        os.system('rm -f ' + testfile)
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
    string = re.sub(u"[àáâãäå]", 'a', string)
    string = re.sub(u"[èéêë]", 'e', string)
    string = re.sub(u"[ìíîï]", 'i', string)
    string = re.sub(u"[òóôõö]", 'o', string)
    string = re.sub(u"[ùúûü]", 'u', string)
    string = re.sub(u"[ýÿ]", 'y', string)
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
        eventName = eventName.replace('episode', '')
        eventName = eventName.replace('مسلسل', '')
        eventName = eventName.replace('فيلم وثائقى', '')
        eventName = eventName.replace('حفل', '')
        return eventName
    return ""


def getCleanTitle(eventitle=""):
    # save_name = re.sub('\\(\d+\)$', '', eventitle)
    # save_name = re.sub('\\(\d+\/\d+\)$', '', save_name)  # remove episode-number " (xx/xx)" at the end
    # # save_name = re.sub('\ |\?|\.|\,|\!|\/|\;|\:|\@|\&|\'|\-|\"|\%|\(|\)|\[|\]\#|\+', '', save_name)
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
    sanitized = re.sub(r'[^\w\s-]', '', filename)  # Remove invalid characters
    # sanitized = sanitized.replace(' ', '_')      # Replace spaces with underscores
    # sanitized = sanitized.replace('-', '_')      # Replace dashes with underscores
    return sanitized.strip()


def convtext(text=''):
    text = text.lower()
    print('text lower init=', text)
    text = text.replace("\xe2\x80\x93", "").replace('\xc2\x86', '').replace('\xc2\x87', '')  # replace special
    text = text.replace('1^ visione rai', '').replace('1^ visione', ''.replace(' - prima tv', '')).replace(' - primatv', '')
    text = text.replace('prima visione', '').replace('1^tv', '').replace('1^ tv', '')
    text = text.replace('((', '(').replace('))', ')')
    # Inglese
    text = text.replace('first screening', '').replace('premiere:', '').replace('live:', '').replace('new:', '')
    # Francese
    text = text.replace('première diffusion', '').replace('nouveau:', '').replace('en direct:', '')
    # Spagnolo
    text = text.replace('estreno:', '').replace('nueva emisión:', '').replace('en vivo:', '')

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
    if 'la7 ' in text:
        text = 'la7'
    if 'skytg24' in text:
        text = 'skytg24'
    cutlist = ['x264', '720p', '1080p', '1080i', 'PAL', 'GERMAN', 'ENGLiSH', 'WS', 'DVDRiP', 'UNRATED', 'RETAIL', 'Web-DL', 'DL', 'LD', 'MiC', 'MD', 'DVDR', 'BDRiP', 'BLURAY', 'DTS', 'UNCUT', 'ANiME',
               'AC3MD', 'AC3', 'AC3D', 'TS', 'DVDSCR', 'COMPLETE', 'INTERNAL', 'DTSD', 'XViD', 'DIVX', 'DUBBED', 'LINE.DUBBED', 'DD51', 'DVDR9', 'DVDR5', 'h264', 'AVC',
               'WEBHDTVRiP', 'WEBHDRiP', 'WEBRiP', 'WEBHDTV', 'WebHD', 'HDTVRiP', 'HDRiP', 'HDTV', 'ITUNESHD', 'REPACK', 'SYNC']
    text = text.replace('.wmv', '').replace('.flv', '').replace('.ts', '').replace('.m2ts', '').replace('.mkv', '').replace('.avi', '').replace('.mpeg', '').replace('.mpg', '').replace('.iso', '').replace('.mp4', '')

    for word in cutlist:
        text = sub(r'(\_|\-|\.|\+)' + escape(word.lower()) + r'(\_|\-|\.|\+)', '+', text, flags=I)
    text = text.replace('.', ' ').replace('-', ' ').replace('_', ' ').replace('+', '').replace(" Director's Cut", "").replace(" director's cut", "").replace("[Uncut]", "").replace("Uncut", "")

    text_split = text.split()
    if text_split and text_split[0].lower() in ("new:", "live:"):
        text_split.pop(0)  # remove annoying prefixes
    text = " ".join(text_split)

    if search(r'[Ss][0-9]+[Ee][0-9]+', text):
        text = sub(r'[Ss][0-9]+[Ee][0-9]+.*[a-zA-Z0-9_]+', '', text, flags=S | I)
    text = sub(r'\(.*\)', '', text).rstrip()  # remove episode number from series, like "series name (234)"

    # # List of bad strings to remove
    # bad_strings = [
        # "ae|", "al|", "ar|", "at|", "ba|", "be|", "bg|", "br|", "cg|", "ch|", "cz|", "da|", "de|", "dk|",
        # "ee|", "en|", "es|", "eu|", "ex-yu|", "fi|", "fr|", "gr|", "hr|", "hu|", "in|", "ir|", "it|", "lt|",
        # "mk|", "mx|", "nl|", "no|", "pl|", "pt|", "ro|", "rs|", "ru|", "se|", "si|", "sk|", "sp|", "tr|",
        # "uk|", "us|", "yu|",
        # "1080p-dual-lat-cine-calidad.com", "1080p-dual-lat-cine-calidad.com-1",
        # "1080p-dual-lat-cinecalidad.mx", "1080p-lat-cine-calidad.com", "1080p-lat-cine-calidad.com-1",
        # "1080p-lat-cinecalidad.mx", "1080p.dual.lat.cine-calidad.com", "3d", "'", "#", "[]",  # "/", "(", ")", "-",
        # "4k", "aac", "blueray", "ex-yu:", "fhd", "hd", "hdrip", "hindi", "imdb", "multi:", "multi-audio",
        # "multi-sub", "multi-subs", "multisub", "ozlem", "sd", "top250", "u-", "uhd", "vod", "x264"
    # ]

    # # Remove numbers from 1900 to 2030
    # bad_strings.extend(map(str, range(1900, 2030)))
    # # Construct a regex pattern to match any of the bad strings
    # bad_strings_pattern = re.compile('|'.join(map(re.escape, bad_strings)))
    # # Remove bad strings using regex pattern
    # text = bad_strings_pattern.sub('', text)
    # # List of bad suffixes to remove
    # bad_suffix = [
        # " al", " ar", " ba", " da", " de", " en", " es", " eu", " ex-yu", " fi", " fr", " gr", " hr", " mk",
        # " nl", " no", " pl", " pt", " ro", " rs", " ru", " si", " swe", " sw", " tr", " uk", " yu"
    # ]
    # # Construct a regex pattern to match any of the bad suffixes at the end of the string
    # bad_suffix_pattern = re.compile(r'(' + '|'.join(map(re.escape, bad_suffix)) + r')$')
    # # Remove bad suffixes using regex pattern
    # text = bad_suffix_pattern.sub('', text)
    # # Replace ".", "_", "'" with " "
    # text = re.sub(r'[._\']', ' ', text)

    text = remove_accents(text)
    print('remove_accents text: ', text)
    text = text + 'FIN'
    text = re.sub(r'(odc.\s\d+)+.*?FIN', '', text)
    text = re.sub(r'(odc.\d+)+.*?FIN', '', text)
    text = re.sub(r'(\d+)+.*?FIN', '', text)
    text = text.partition("(")[0] + 'FIN'
    text = re.sub(r"\\s\d+", "", text)
    text = re.sub('FIN', '', text)

    text = sanitize_filename(text)

    # forced
    text = text.replace('XXXXXX', '60')
    text = text.replace('brunobarbierix', 'bruno barbieri - 4 hotel')
    text = quote(text, safe="")
    print('text final: ', text)
    return unquote(text).capitalize()


def convtextPAUSED(text=''):
    try:
        if text is None:
            print('return None original text: ', type(text))
            return  # Esci dalla funzione se text è None
        if text == '':
            print('text is an empty string')
        else:
            print('original text: ', text)
            text = text.lower()
            print('lowercased text: ', text)
            text = text.partition("-")[0]
            text = remove_accents(text)
            print('remove_accents text: ', text)
            # #
            text = cutName(text)
            text = getCleanTitle(text)
            # #
            if text.endswith("the"):
                text = "the " + text[:-4]

            # text = re.sub(r'^\w{4}:', '', text)

            text_split = text.split()
            if text_split and text_split[0].lower() in ("new:", "live:"):
                text_split.pop(0)  # remove annoying prefixes
            text = " ".join(text_split)

            text = text.replace("\xe2\x80\x93", "").replace('\xc2\x86', '').replace('\xc2\x87', '')  # replace special
            text = text.replace('1^ visione rai', '').replace('1^ visione', ''.replace(' - prima tv', '')).replace('primatv', '')
            text = text.replace('prima visione', '').replace('1^tv', '').replace('1^ tv', '')
            text = text.replace('live:', '').replace('new:', '').replace('((', '(').replace('))', ')')
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
            if 'la7 ' in text:
                text = 'la7'
            if 'skytg24' in text:
                text = 'skytg24'
            # remove xx: at start
            text = re.sub(r'^\w{2}:', '', text)
            # remove xx|xx at start
            text = re.sub(r'^\w{2}\|\w{2}\s', '', text)
            # remove xx - at start
            text = re.sub(r'^.{2}\+? ?- ?', '', text)
            # remove all leading content between and including ||
            text = re.sub(r'^\|\|.*?\|\|', '', text)
            text = re.sub(r'^\|.*?\|', '', text)
            # remove everything left between pipes.
            text = re.sub(r'\|.*?\|', '', text)
            # remove all content between and including () multiple times
            text = re.sub(r'\(\(.*?\)\)|\(.*?\)', '', text)
            # remove all content between and including [] multiple times
            text = re.sub(r'\[\[.*?\]\]|\[.*?\]', '', text)
            # remove episode number in arabic series
            text = re.sub(r' +ح', '', text)
            # remove season number in arabic series
            text = re.sub(r' +ج', '', text)
            # remove season number in arabic series
            text = re.sub(r' +م', '', text)
            # List of bad strings to remove
            bad_strings = [
                "ae|", "al|", "ar|", "at|", "ba|", "be|", "bg|", "br|", "cg|", "ch|", "cz|", "da|", "de|", "dk|",
                "ee|", "en|", "es|", "eu|", "ex-yu|", "fi|", "fr|", "gr|", "hr|", "hu|", "in|", "ir|", "it|", "lt|",
                "mk|", "mx|", "nl|", "no|", "pl|", "pt|", "ro|", "rs|", "ru|", "se|", "si|", "sk|", "sp|", "tr|",
                "uk|", "us|", "yu|",
                "1080p", "1080p-dual-lat-cine-calidad.com", "1080p-dual-lat-cine-calidad.com-1",
                "1080p-dual-lat-cinecalidad.mx", "1080p-lat-cine-calidad.com", "1080p-lat-cine-calidad.com-1",
                "1080p-lat-cinecalidad.mx", "1080p.dual.lat.cine-calidad.com", "3d", "'", "#", "[]",  # "/", "(", ")", "-",
                "4k", "720p", "aac", "blueray", "ex-yu:", "fhd", "hd", "hdrip", "hindi", "imdb", "multi:", "multi-audio",
                "multi-sub", "multi-subs", "multisub", "ozlem", "sd", "top250", "u-", "uhd", "vod", "x264"
            ]

            # Remove numbers from 1900 to 2030
            bad_strings.extend(map(str, range(1900, 2030)))
            # Construct a regex pattern to match any of the bad strings
            bad_strings_pattern = re.compile('|'.join(map(re.escape, bad_strings)))
            # Remove bad strings using regex pattern
            text = bad_strings_pattern.sub('', text)
            # List of bad suffixes to remove
            bad_suffix = [
                " al", " ar", " ba", " da", " de", " en", " es", " eu", " ex-yu", " fi", " fr", " gr", " hr", " mk",
                " nl", " no", " pl", " pt", " ro", " rs", " ru", " si", " swe", " sw", " tr", " uk", " yu"
            ]
            # Construct a regex pattern to match any of the bad suffixes at the end of the string
            bad_suffix_pattern = re.compile(r'(' + '|'.join(map(re.escape, bad_suffix)) + r')$')
            # Remove bad suffixes using regex pattern
            text = bad_suffix_pattern.sub('', text)
            # Replace ".", "_", "'" with " "
            text = re.sub(r'[._\']', ' ', text)
            # recoded lulu
            text = text + 'FIN'
            '''
            if re.search(r'[Ss][0-9][Ee][0-9]+.*?FIN', text):
                text = re.sub(r'[Ss][0-9][Ee][0-9]+.*?FIN', '', text)
            if re.search(r'[Ss][0-9] [Ee][0-9]+.*?FIN', text):
                text = re.sub(r'[Ss][0-9] [Ee][0-9]+.*?FIN', '', text)
            '''
            text = re.sub(r'(odc.\s\d+)+.*?FIN', '', text)
            text = re.sub(r'(odc.\d+)+.*?FIN', '', text)
            text = re.sub(r'(\d+)+.*?FIN', '', text)
            text = text.partition("(")[0] + 'FIN'
            text = re.sub(r"\\s\d+", "", text)
            text = text.partition("(")[0]
            # text = text.partition(":")[0]  # not work on csi: new york (only-->  csi)
            text = text.partition(" -")[0]
            text = re.sub(' - +.+?FIN', '', text)  # all episodes and series ????
            text = re.sub('FIN', '', text)
            text = re.sub(r"[\<\>\:\"\/\\\|\?\*!]", "_", str(text))
            # text = re.sub(r'^\|[\w\-\|]*\|', '', text)
            text = re.sub(r"[-,?!+/\.\":]", '', text)  # replace (- or , or ! or / or . or " or :) by space
            # recoded  end
            text = text.strip(' -')
            # forced
            text = text.replace('XXXXXX', '60')
            text = text.replace('brunobarbierix', 'bruno barbieri - 4 hotel')
            text = quote(text, safe="")
            print('text safe: ', text)
        return unquote(text).capitalize()
    except Exception as e:
        print('convtext error: ', e)
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
                # Gestisci il caso in cui self.pstcanal è None o non valido
                # dwn_poster = path_folder + '/default.jpg'  # Esempio di fallback
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
        adsl = intCheck()
        if not adsl:
            return
        Renderer.__init__(self)
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
                # self.pstcanal = convtext(self.canal[5])
                # if self.pstcanal is not None:
                    # self.pstrNm = self.path + '/' + str(self.pstcanal) + ".jpg"
                    # self.pstcanal = str(self.pstrNm)
                # if os.path.exists(self.pstcanal):

                if os.path.exists(self.canal[5]):
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
            if self.pstcanal is not None and not os.path.exists(self.pstcanal):
                self.pstcanal = convtext(self.canal[5])
                self.pstrNm = self.path + '/' + str(self.pstcanal) + ".jpg"
                self.pstcanal = str(self.pstrNm)
            if self.pstcanal is not None and os.path.exists(self.pstcanal):
                print('showPoster----')
                self.logPoster("[LOAD : showPoster] {}".format(self.pstcanal))
                self.instance.setPixmap(loadJPG(self.pstcanal))
                self.instance.setScale(1)
                self.instance.show()

    def waitPoster(self):
        if self.instance:
            self.instance.hide()
        if self.canal[5]:
            if self.pstcanal is not None and not os.path.exists(self.pstcanal):
                self.pstcanal = convtext(self.canal[5])
                self.pstrNm = self.path + '/' + str(self.pstcanal) + ".jpg"
                self.pstcanal = str(self.pstrNm)
            loop = 180
            found = None
            self.logPoster("[LOOP: waitPoster] {}".format(self.pstcanal))
            while loop >= 0:
                if self.pstcanal is not None and os.path.exists(self.pstcanal):
                    loop = 0
                    found = True
                time.sleep(0.5)
                loop = loop - 1
            if found:
                self.timer.start(20, True)

    def logPoster(self, logmsg):
        import traceback
        try:
            with open("/tmp/AglarePosterXEMC.log", "a") as w:
                w.write("%s\n" % logmsg)
        except Exception as e:
            print('logPoster error:', str(e))
            traceback.print_exc()
