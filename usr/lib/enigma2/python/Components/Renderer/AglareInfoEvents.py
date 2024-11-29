#!/usr/bin/python
# -*- coding: utf-8 -*-

# by digiteng...04.2020, 11.2020, 06.2021
# file by sunriser 07.2021
# <widget source="session.Event_Now" render="AglareInfoEvents"/>
# <widget source="session.Event_Next" render="AglareInfoEvents"/>
# <widget source="Event" render="AglareInfoEvents"/>
# edit by lululla 07.2022
# recode from lululla 2023
from __future__ import absolute_import
from Components.Renderer.Renderer import Renderer
from Components.VariableText import VariableText
from Components.config import config
from six import text_type
from enigma import (
    eLabel,
            
    eEPGCache,
    eTimer,
)
from time import gmtime
import json
import os
import re
             
import socket
import sys
import NavigationInstance
from re import search, sub, I, S, escape

global my_cur_skin, path_folder


PY3 = False
if sys.version_info[0] >= 3:
    PY3 = True
    from urllib.parse import quote_plus
    from urllib.request import urlopen
    from _thread import start_new_thread
    from urllib.error import HTTPError, URLError
    import html
    html_parser = html


                                       
else:
    from urllib import quote_plus
    from urllib2 import urlopen
    from thread import start_new_thread
    from urllib2 import HTTPError, URLError
    from HTMLParser import HTMLParser
    html_parser = HTMLParser()


try:
    from urllib import unquote, quote
except ImportError:
    from urllib.parse import unquote, quote


tmdb_api = "3c3efcf47c3577558812bb9d64019d65"
omdb_api = "cb1d9f55"
thetvdbkey = 'D19315B88B2DE21F'
# thetvdbkey = "a99d487bb3426e5f3a60dea6d3d3c7ef"
epgcache = eEPGCache.getInstance()
my_cur_skin = False
cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')


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


                                                                  
                                                               
path_folder = "/tmp/poster"
if os.path.exists("/media/hdd"):
    if isMountedInRW("/media/hdd"):
        path_folder = "/media/hdd/poster"
elif os.path.exists("/media/usb"):
    if isMountedInRW("/media/usb"):
        path_folder = "/media/usb/poster"
elif os.path.exists("/media/mmc"):
    if isMountedInRW("/media/mmc"):
        path_folder = "/media/mmc/poster"

if not os.path.exists(path_folder):
    os.makedirs(path_folder)


                                  
             


try:
    if my_cur_skin is False:
        skin_paths = {
            "tmdb_api": "/usr/share/enigma2/{}/tmdbkey".format(cur_skin),
            "omdb_api": "/usr/share/enigma2/{}/omdbkey".format(cur_skin),
            "thetvdbkey": "/usr/share/enigma2/{}/thetvdbkey".format(cur_skin)
        }
        for key, path in skin_paths.items():
            if os.path.exists(path):
                with open(path, "r") as f:
                    value = f.read().strip()
                    if key == "tmdb_api":
                        tmdb_api = value
                    elif key == "omdb_api":
                        omdb_api = value
                    elif key == "thetvdbkey":
                        thetvdbkey = value
                my_cur_skin = True
except Exception as e:
    print("Errore nel caricamento delle API:", str(e))
    my_cur_skin = False


def OnclearMem():
    try:
        os.system('sync')
        os.system('echo 1 > /proc/sys/vm/drop_caches')
        os.system('echo 2 > /proc/sys/vm/drop_caches')
        os.system('echo 3 > /proc/sys/vm/drop_caches')
    except:
        pass


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


class AglareInfoEvents(Renderer, VariableText):

    def __init__(self):
                                                                                                                    
                                                                                                                   
                                                    
        Renderer.__init__(self)
        VariableText.__init__(self)
        adsl = intCheck()
        if not adsl:
            return
        self.text = ""
                                                       
                                    

                                         
                    
                                                    
                                 
                                      
                                
                                      
                                           
                                     
                                                        

    GUI_WIDGET = eLabel

    def changed(self, what):
                             
                  
        if what[0] == self.CHANGED_CLEAR:
            return self.text
        if what[0] != self.CHANGED_CLEAR:
            if self.instance:
                self.instance.hide()
            self.showInfos()

    def showInfos(self):
        self.event = self.source.event
        if self.event and self.event != 'None' or self.event is not None:
            self.evnt = self.event.getEventName().replace('\xc2\x86', '').replace('\xc2\x87', '')
            if not PY3:
                self.evnt = self.evnt.encode('utf-8')
            self.evntNm = convtext(self.evnt)
            self.infos_file = "{}/{}".format(path_folder, self.evntNm)
            self.text = ''
            if not os.path.exists(self.infos_file):
                self.downloadInfos()
            if os.path.exists(self.infos_file):
                try:
                    with open(self.infos_file, 'r') as f:
                        data = json.load(f)
                        Title = data.get("Title", "")
                        imdbRating = data.get("imdbRating", "")
                        Country = data.get("Country", "")
                        Year = data.get("Year", "")
                        Rated = data.get("Rated", "")
                        Genre = data.get("Genre", "")
                        Awards = data.get("Awards", "")
                        Director = data.get("Director", "")
                        Writer = data.get("Writer", "")
                        Actors = data.get("Actors", "")

                        if Title and Title != "N/A":
                            with open("/tmp/rating", "w") as f_rating:
                                f_rating.write("%s\n%s" % (imdbRating, Rated))
                            self.text = "Title: %s\nYear: %s\nCountry: %s\nGenre: %s\nDirector: %s\nAwards: %s\nWriter: %s\nCast: %s\nRated: %s\nImdb: %s" % (
                                str(Title), str(Year), str(Country), str(Genre), str(Director),
                                str(Awards), str(Writer), str(Actors), str(Rated), str(imdbRating)
                            )
                            print("iInfoEvents self.text= ", self.text)
                            self.instance.show()
                        else:
                            if os.path.exists("/tmp/rating"):
                                os.remove("/tmp/rating")
                                print('/tmp/rating removed')
                        return self.text
                except Exception as e:
                    print(e)
            else:
                return self.text

    def downloadInfos(self):
        self.year = self.filterSearch()
        try:
            url_tmdb = "https://api.themoviedb.org/3/search/{}?api_key={}&query={}".format(self.srch, tmdb_api, quoteEventName(self.evntNm))
            if self.year:
                url_tmdb += "&year={}".format(self.year)
            print('downloadInfos url_tmdb=', url_tmdb)
            try:
                response_tmdb = urlopen(url_tmdb)
                data_tmdb = json.load(response_tmdb)
                try:
                    title = data_tmdb["results"][0]["title"]
                except KeyError:
                    title = data_tmdb["results"][0]["original_name"]
                print('downloadInfos Title: ', title)
                url_omdb = "http://www.omdbapi.com/?apikey={}&t={}".format(omdb_api, quoteEventName(title))
                print('downloadInfos url_omdb=', url_omdb)
                response_omdb = urlopen(url_omdb)
                data_omdb = json.load(response_omdb)
                with open(self.infos_file, "w") as f:
                    f.write(json.dumps(data_omdb))
            except Exception as e:
                print("Errore durante il download delle informazioni: ", str(e))

        except Exception as e:
            print("Errore generale: ", str(e))

    def filterSearch(self):
        try:
            self.srch = "multi"
            sd = "%s\n%s\n%s" % (self.event.getEventName(), self.event.getShortDescription(), self.event.getExtendedDescription())
            keywords = [
                "t/s", "Т/s", "SM", "d/s", "D/s", "stagione",
                "Sig.", "episodio", "serie TV", "serie"
            ]
            for keyword in keywords:
                if keyword in sd:
                    self.srch = "tv"
                    break
            years = re.findall(r'\d{4}', sd)
            valid_years = [_y for _y in years if '1930' <= _y <= str(gmtime().tm_year)]
            return valid_years[-1] if valid_years else None
        except Exception as e:
            print("Errore in filterSearch:", str(e))
            return False

    def epgs(self):
        try:
            events = None
            ref = NavigationInstance.instance.getCurrentlyPlayingServiceReference().toString()
            events = epgcache.lookupEvent(['IBDCT', (ref, 0, -1, -1)])
            for i in range(9):
                titleNxt = events[i][4]
                self.evntNm = convtext(titleNxt)
                self.infos_file = "{}/{}".format(path_folder, self.evntNm)
                if not os.path.exists(self.infos_file):
                    self.downloadInfos()
        except:
            pass

    def delay2(self):
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.dwn)
        except:
            self.timer.callback.append(self.dwn)
        self.timer.start(10, True)

    def dwn(self):
        start_new_thread(self.epgs, ())
