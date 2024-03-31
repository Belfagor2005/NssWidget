#!/usr/bin/env python
# -*- coding: utf-8 -*-

# --------------------#
#   coded by Lululla  #
#      24/11/2023     #
# --------------------#
# imported from tvAddon Panel
from __future__ import print_function
from . import _
from .lib import Utils
from .lib.Utils import RequestAgent
from .lib.Lcn import LCN
from .lib.Downloader import downloadWithProgress
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigIP
from Components.config import ConfigYesNo, ConfigSubsection
from Components.config import ConfigDirectory, ConfigText, ConfigInteger
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.MultiContent import MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
# from Components.ScrollLabel import ScrollLabel
from Components.Sources.Progress import Progress
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.Console import Console as tvConsole
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import SCOPE_PLUGINS
from Tools.Directories import fileExists, resolveFilename
# from Tools.Downloader import downloadWithProgress
from enigma import RT_HALIGN_LEFT, RT_VALIGN_CENTER
from enigma import loadPNG, gFont
from enigma import eTimer
from enigma import getDesktop
from enigma import eListboxPythonMultiContent, eConsoleAppContainer
from os import chmod
from os import listdir, mkdir
from twisted.web.client import downloadPage, getPage
import codecs
import os
import re
import sys
import shutil
import ssl
import glob
import six
import subprocess


global skin_path, mmkpicon, set, category


PY3 = sys.version_info.major >= 3
if PY3:
    from urllib.error import URLError
    from urllib.request import urlopen, Request
    from urllib.parse import urlparse
    unicode = str
    unichr = chr
    long = int
    PY3 = True
else:
    from urllib2 import urlopen, Request, URLError
    from urlparse import urlparse


if sys.version_info >= (2, 7, 9):
    try:
        sslContext = ssl._create_unverified_context()
    except:
        sslContext = None


def ssl_urlopen(url):
    if sslContext:
        return urlopen(url, context=sslContext)
    else:
        return urlopen(url)


try:
    from twisted.internet import ssl
    from twisted.internet._sslverify import ClientTLSOptions
    sslverify = True
except:
    sslverify = False


if sslverify:
    class SNIFactory(ssl.ClientContextFactory):
        def __init__(self, hostname=None):
            self.hostname = hostname

        def getContext(self):
            ctx = self._contextFactory(self.method)
            if self.hostname:
                ClientTLSOptions(self.hostname, ctx)
            return ctx


def status_site():
    global status
    import requests
    try:
        Host = 'https://www.nonsolosat.net'
        # response = requests.get(Host, headers={'User-Agent': RequestAgent()}, verify=False)
        response = requests.get(Host, verify=False, timeout=5)
        if response.status_code == 200:
            status = True
            print('Web site exists')
        else:
            status = False
            print('Web site does not exist')
    except Exception as e:
        print(e)
        status = False
    return status


def checkMyFile(url):
    return []
    myfile = None
    try:
        req = Request(url)
        req.add_header('User-Agent', RequestAgent())
        # req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
        req.add_header('Referer', 'https://www.mediafire.com')
        req.add_header('X-Requested-With', 'XMLHttpRequest')
        page = urlopen(req)
        r = page.read()
        # if PY3:
            # n1 = r.find('"download_link'.encode(), 0)
            # n2 = r.find('downloadButton'.encode(), n1)
        # else:
            # n1 = r.find('"download_link', 0)
            # n2 = r.find('downloadButton', n1)
        n1 = r.find('"download_link', 0)
        n2 = r.find('downloadButton', n1)
        r2 = r[n1:n2]
        regexcat = 'href="https://download(.*?)"'
        match = re.compile(regexcat, re.DOTALL).findall(r2)
        myfile = match[0]
    except:
        e = URLError
        if hasattr(e, 'code'):
            print('We failed with error code - %s.' % e.code)
        if hasattr(e, 'reason'):
            print('Reason: ', e.reason)
    return myfile


def make_req(url):
    try:
        import requests
        response = requests.get(url, verify=False, timeout=5)
        if response.status_code == 200:
            link = requests.get(url, headers={'User-Agent': RequestAgent()}, timeout=15, verify=False, stream=True).text
        return link
    except ImportError:
        req = Request(url)
        req.add_header('User-Agent', 'E2 Plugin nss Panel')
        response = urlopen(req, None, 10)
        link = response.read().decode('utf-8')
        response.close()
        return link
    return


def check_gzip(url):
    from io import StringIO
    import gzip
    hdr = {"User-Agent": RequestAgent()}
    response = None
    request = Request(url, headers=hdr)
    try:
        response = urlopen(request, timeout=15)
        if response.info().get('Content-Encoding') == 'gzip':
            buffer = StringIO(response.read())
            deflatedContent = gzip.GzipFile(fileobj=buffer)
            if PY3:
                return deflatedContent.read().decode('utf-8')
            else:
                return deflatedContent.read()
        else:
            if PY3:
                return response.read().decode('utf-8')
            else:
                return response.read()
    except Exception as e:
        print(e)
        return None


def ReloadBouquets():
    from enigma import eDVBDB
    print("\n----Reloading bouquets----")
    global set
    if set == 1:
        set = 0
        print("\n----Reloading Terrestrial----")
        terrestrial_rest()
    if eDVBDB:
        eDVBDB.getInstance().reloadServicelist()
        eDVBDB.getInstance().reloadBouquets()
        print("eDVBDB: bouquets reloaded...")
    else:
        os.system("wget -qO - http://127.0.0.1/web/servicelistreload?mode=2 > /dev/null 2>&1 &")
        os.system("wget -qO - http://127.0.0.1/web/servicelistreload?mode=4 > /dev/null 2>&1 &")
        print("wGET: bouquets reloaded...")


# def mountipkpth():
    # ipkpth = []
    # if os.path.isfile('/proc/mounts'):
        # for line in open('/proc/mounts'):
            # if '/dev/sd' in line or '/dev/disk/by-uuid/' in line or '/dev/mmc' in line or '/dev/mtdblock' in line:
                # drive = line.split()[1].replace('\\040', ' ') + '/'
                # if drive not in ipkpth:
                    # ipkpth.append(drive)
    # ipkpth.append('/tmp')
    # return ipkpth


AgentRequest = RequestAgent()
# ================config
global set
config.plugins.nssaddon = ConfigSubsection()
config.plugins.nssaddon.strtext = ConfigYesNo(default=True)
config.plugins.nssaddon.mmkpicon = ConfigDirectory(default='/picon/')
config.plugins.nssaddon.strtmain = ConfigYesNo(default=False)
# config.plugins.nssaddon.ipkpth = ConfigSelection(default="/tmp", choices=mountipkpth())
mmkpicon = config.plugins.nssaddon.mmkpicon.value.strip()
currversion = '1.0.0'
title_plug = 'NSS Addon V. %s' % currversion
name_plug = 'NSS Addon'
name_cam = 'NSS Cam Manager'
category = 'lululla.xml'
set = 0
pblk = 'aHR0cHM6Ly93d3cubWVkaWFmaXJlLmNvbS9hcGkvMS41L2ZvbGRlci9nZXRfY29udGVudC5waHA/Zm9sZGVyX2tleT1vdnowNG1ycHpvOXB3JmNvbnRlbnRfdHlwZT1mb2xkZXJzJmNodW5rX3NpemU9MTAwMCZyZXNwb25zZV9mb3JtYXQ9anNvbg== '
ptrs = 'aHR0cHM6Ly93d3cubWVkaWFmaXJlLmNvbS9hcGkvMS41L2ZvbGRlci9nZXRfY29udGVudC5waHA/Zm9sZGVyX2tleT10dmJkczU5eTlocjE5JmNvbnRlbnRfdHlwZT1mb2xkZXJzJmNodW5rX3NpemU9MTAwMCZyZXNwb25zZV9mb3JtYXQ9anNvbg== '
ptmov = 'aHR0cHM6Ly93d3cubWVkaWFmaXJlLmNvbS9hcGkvMS41L2ZvbGRlci9nZXRfY29udGVudC5waHA/Zm9sZGVyX2tleT1uazh0NTIyYnY0OTA5JmNvbnRlbnRfdHlwZT1maWxlcyZjaHVua19zaXplPTEwMDAmcmVzcG9uc2VfZm9ybWF0PWpzb24= '
data_xml = 'aHR0cHM6Ly93d3cubm9uc29sb3NhdC5uZXQveG1sLw=='
regexC = '<plugins cont="(.*?)"'
regexL = 'href="(.+?)">.+?alt=.+?">(.+?)</a>.+?data.+?">(.+?)</td>'
host_trs = Utils.b64decoder(ptrs)
host_blk = Utils.b64decoder(pblk)
host_mov = Utils.b64decoder(ptmov)
xml_path = Utils.b64decoder(data_xml)
plugin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('nssaddon'))
ico_path = os.path.join(plugin_path, 'logo.png')
no_cover = os.path.join(plugin_path, 'no_coverArt.png')
_firstStarttvspro = True
ee2ldb = '/etc/enigma2/lamedb'
ServOldLamedb = plugin_path + '/temp/ServiceListOldLamedb'
TransOldLamedb = plugin_path + '/temp/TrasponderListOldLamedb'
TerChArch = plugin_path + '/temp/TerrestrialChannelListArchive'
# SelBack = plugin_path + '/SelectBack'
# SSelect = plugin_path + '/Select'
# DIGTV = 'eeee0000'

screenwidth = getDesktop(0).size()
if screenwidth.width() == 2560:
    skin_path = plugin_path + '/res/skins/uhd/'
elif screenwidth.width() == 1920:
    skin_path = plugin_path + '/res/skins/fhd/'
else:
    skin_path = plugin_path + '/res/skins/hd/'
if os.path.exists('/var/lib/dpkg/info'):
    skin_path = skin_path + 'dreamOs/'

os.system('rm -fr ' + plugin_path + '/temp/*')
if mmkpicon.endswith('/'):
    mmkpicon = mmkpicon[:-1]
if not os.path.exists(mmkpicon):
    try:
        os.makedirs(mmkpicon)
    except OSError as e:
        print(('Error creating directory %s:\n%s') % (mmkpicon, str(e)))


Panel_list = [
 _('LULULLA CORNER'),
 _('DAILY PICONS'),
 _('DAILY SETTINGS'),
 _('SETTING CHANNEL NSS'),
 _('DEPENDENCIES'),
 _('DRIVERS'),
 _('PLUGIN BACKUP'),
 _('PLUGIN EPG'),
 _('PLUGIN EMULATORS CAMS'),
 _('PLUGIN GAME'),
 _('PLUGIN MULTIBOOT'),
 _('PLUGIN MULTIMEDIA'),
 _('PLUGIN PICONS'),
 _('PLUGIN PPANEL'),
 _('PLUGIN SETTINGS PANEL'),
 _('PLUGIN SCRIPT'),
 _('PLUGIN SKINS'),
 _('PLUGIN SPORT'),
 _('PLUGIN UTILITY'),
 _('PLUGIN WEATHER')]

Panel_list2 = [
 ('SAVE DTT BOUQUET'),
 ('RESTORE DTT BOUQUET'),
 ('UPDATE SATELLITES.XML'),
 ('UPDATE TERRESTRIAL.XML'),
 ('SETTINGS BI58'),
 ('SETTINGS CIEFP'),
 ('SETTINGS CYRUS'),
 ('SETTINGS MANUTEK'),
 # ('SETTINGS MILENKA61'),
 ('SETTINGS MORPHEUS'),
 ('SETTINGS PREDRAG'),
 ('SETTINGS VHANNIBAL'),
 ('SETTINGS VHANNIBAL 2')
]

Panel_list3 = [
 _('MMARK PICONS BLACK'),
 _('MMARK PICONS TRANSPARENT'),
 _('MMARK PICONS MOVIE'),
 _('OPEN PICONS')]


class nssList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        if screenwidth.width() == 2560:
            self.l.setItemHeight(60)
            textfont = int(44)
            self.l.setFont(0, gFont('Regular', textfont))
        elif screenwidth.width() == 1920:
            self.l.setItemHeight(50)
            textfont = int(32)
            self.l.setFont(0, gFont('Regular', textfont))
        else:
            self.l.setItemHeight(42)
            textfont = int(24)
            self.l.setFont(0, gFont('Regular', textfont))


pngs = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/settingoff.png".format('nssaddon'))  # ico1_path
if status_site():
    pngs = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/settingon.png".format('nssaddon'))  # ico1_path


def nssListEntry(name, idx):
    res = [name]
    if screenwidth.width() == 2560:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 10), size=(40, 40), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(80, 0), size=(1200, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    elif screenwidth.width() == 1920:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(40, 40), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(70, 0), size=(1000, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(3, 10), size=(40, 40), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(50, 0), size=(500, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res


def oneListEntry(name):
    res = [name]
    if screenwidth.width() == 2560:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 10), size=(40, 40), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(80, 0), size=(1950, 60), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    elif screenwidth.width() == 1920:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(40, 40), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(70, 0), size=(1000, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(3, 10), size=(40, 40), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(50, 0), size=(500, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res


def showlistNss(data, list):
    icount = 0
    plist = []
    for line in data:
        name = data[icount]
        plist.append(oneListEntry(name))
        icount += 1
        list.setList(plist)


class HomeNss(Screen):
    def __init__(self, session):
        self.session = session
        skin = os.path.join(skin_path, 'HomeNss.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = (name_plug)
        Screen.__init__(self, session)
        self['list'] = nssList([])
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Extensions Installer'))
        self['key_yellow'] = Button(_('Uninstall'))
        self["key_blue"] = Button(_("NSS Cams Manager"))
        # self['key_blue'].hide()
        self['info'] = Label(_('Loading data... Please wait'))
        self['statusgreen'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'] = Pixmap()
        self['statusred'].hide()
        self['status'] = Label('Please wait..')
        self['title'] = Label(name_plug)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'green': self.NssIPK,
                                                           'menu': self.goConfig,
                                                           'blue': self.NSSCamsManager,
                                                           'yellow': self.ipkDs,
                                                           'red': self.closerm,
                                                           'back': self.closerm,
                                                           'cancel': self.closerm}, -1)
        self.onFirstExecBegin.append(self.check_dependencies)
        self.onLayoutFinish.append(self.updateMenuList)

    def __layoutFinished(self):
        if status_site():
            self['statusgreen'].show()
            self['statusred'].hide()
            self['status'].setText('SERVER ON')
        else:
            self['statusgreen'].hide()
            self['statusred'].show()
            self['status'].setText('SERVER OFF')
        self.setTitle(self.setup_title)
        self['info'].setText(_('Please select ...'))

    def check_dependencies(self):
        dependencies = True
        try:
            import requests
        except:
            dependencies = False
        if dependencies is False:
            chmod("/usr/lib/enigma2/python/Plugins/Extensions/nssaddon/dependencies.sh", 0o0755)
            cmd1 = "/usr/lib/enigma2/python/Plugins/Extensions/nssaddon/dependencies.sh"
            self.session.openWithCallback(self.starts, tvConsole, title="Checking Python Dependencies", cmdlist=[cmd1], closeOnSuccess=False)
        else:
            self.starts()

    def starts(self):
        Utils.OnclearMem()

    def closerm(self):
        ReloadBouquets()
        Utils.deletetmp()
        self.close()

    def goConfig(self):
        self.session.open(nssConfig)

    def updateMenuList(self):
        self.menu_list = []
        for x in self.menu_list:
            del self.menu_list[0]
        list = []
        idx = 0
        for x in Panel_list:
            list.append(nssListEntry(x, idx))
            self.menu_list.append(x)
            idx += 1
        self['list'].setList(list)
        self.timer2 = eTimer()
        if os.path.exists('/var/lib/dpkg/info'):
            self.timer2_conn = self.timer2.timeout.connect(self.__layoutFinished)
        else:
            self.timer2.callback.append(self.__layoutFinished)
        self.timer2.start(200, 1)

    def okRun(self):
        self.keyNumberGlobalCB(self['list'].getSelectedIndex())

    def ipkDs(self):
        self.session.open(NssRemove)

    def NSSCamsManager(self):
        tvman = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('nssaddon'))
        if os.path.exists(tvman):
            # from Plugins.Extensions.nssaddon.CamEx import NSSCamsManager
            # self.session.openWithCallback(self.close, NSSCamsManager)
            from Plugins.Extensions.Manager.plugin import Manager
            self.session.openWithCallback(self.close, Manager)            
        else:
            self.session.open(MessageBox, ("NSSCamsManager Not Installed!!\nInstall First"), type=MessageBox.TYPE_INFO, timeout=3)

    def NssIPK(self):
        self.session.open(NssIPK)

    def keyNumberGlobalCB(self, idx):
        global category
        sel = self.menu_list[idx]
        if sel == _('DAILY SETTINGS'):
            self.session.open(NssDailySetting)
        if sel == _('SETTING CHANNEL NSS'):
            category = 'Settingchannelnss.xml'
            self.session.open(nssCategories, category)
        if sel == _('DAILY PICONS'):
            self.session.open(SelectPiconz)
        if sel == _('LULULLA CORNER'):
            category = 'lululla.xml'
            self.session.open(nssCategories, category)
        if sel == _('DRIVERS'):
            category = 'Drivers.xml'
            self.session.open(nssCategories, category)
        if sel == _('DEPENDENCIES'):
            category = 'Dependencies.xml'
            self.session.open(nssCategories, category)
        if sel == _('PLUGIN BACKUP'):
            category = 'PluginBackup.xml'
            self.session.open(nssCategories, category)
        if sel == _('PLUGIN EMULATORS CAMS'):
            category = 'PluginEmulators.xml'
            self.session.open(nssCategories, category)
        if sel == _('PLUGIN EPG'):
            category = 'PluginEpg.xml'
            self.session.open(nssCategories, category)
        if sel == _('PLUGIN GAME'):
            category = 'PluginGame.xml'
            self.session.open(nssCategories, category)
        if sel == _('PLUGIN MULTIBOOT'):
            category = 'PluginMultiboot.xml'
            self.session.open(nssCategories, category)
        if sel == _('PLUGIN MULTIMEDIA'):
            category = 'PluginMultimedia.xml'
            self.session.open(nssCategories, category)
        if sel == _('PLUGIN PICONS'):
            category = 'Picons.xml'
            self.session.open(nssCategories, category)
        if sel == _('PLUGIN PPANEL'):
            category = 'PluginPpanel.xml'
            self.session.open(nssCategories, category)
        if sel == _('PLUGIN SCRIPT'):
            category = 'PlugiScript.xml'
            self.session.open(nssCategories, category)
        if sel == _('PLUGIN SETTINGS PANEL'):
            category = 'PluginSettings.xml'
            self.session.open(nssCategories, category)
        if sel == _('PLUGIN SKINS'):
            category = 'PluginSkins.xml'
            self.session.open(nssCategories, category)
        if sel == _('PLUGIN SPORT'):
            category = 'PluginSport.xml'
            self.session.open(nssCategories, category)
        if sel == _('PLUGIN UTILITY'):
            category = 'PluginUtility.xml'
            self.session.open(nssCategories, category)
        if sel == _('PLUGIN WEATHER'):
            category = 'PluginWeather.xml'
            self.session.open(nssCategories, category)
        else:
            return


class nssCategories(Screen):
    def __init__(self, session, category):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = (category)
        Screen.__init__(self, session)
        self.list = []
        self['list'] = nssList([])
        self.category = category
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pform'] = Label('')
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['key_green'] = Button(_('Extensions Installer'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button(_('Uninstall'))
        self["key_blue"] = Button(_("NSS Cam Manager"))
        # self['key_blue'].hide()
        self.Update = False
        self.downloading = False
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/info'):
            self.timer_conn = self.timer.timeout.connect(self._gotPageLoad)
        else:
            self.timer.callback.append(self._gotPageLoad)
        self.timer.start(500, 1)
        self['title'] = Label(name_plug)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'MenuActions',
                                     'DirectionActions'], {'ok': self.okRun,
                                                           'green': self.NssIPK,
                                                           'menu': self.goConfig,
                                                           'blue': self.NSSCamsManager,
                                                           'yellow': self.ipkDs,
                                                           'red': self.close,
                                                           'cancel': self.close}, -2)

    def _gotPageLoad(self):
        xml = str(xml_path) + self.category
        self.xml = check_gzip(xml)
        try:
            match = re.compile(regexC, re.DOTALL).findall(self.xml)
            for name in match:
                name = six.ensure_str(name)
                print('name: ', name)
                self.list.append(name)
                self['info'].setText(_('Please select ...'))
            showlistNss(self.list, self['list'])
            self['key_green'].show()
            self.downloading = True
        except Exception as e:
            print('error: ', str(e))

    def NssIPK(self):
        self.session.open(NssIPK)

    def ipkDs(self):
        self.session.open(NssRemove)

    def NSSCamsManager(self):
        tvman = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('nssaddon'))
        if os.path.exists(tvman):
            # from Plugins.Extensions.nssaddon.CamEx import NSSCamsManager
            # self.session.openWithCallback(self.close, NSSCamsManager)
            from Plugins.Extensions.Manager.plugin import Manager
            self.session.openWithCallback(self.close, Manager)
        else:
            self.session.open(MessageBox, ("NSSCamsManager Not Installed!!\nInstall First"), type=MessageBox.TYPE_INFO, timeout=3)

    def goConfig(self):
        self.session.open(nssConfig)

    def okRun(self):
        if self.downloading is True:
            try:
                idx = self["list"].getSelectionIndex()
                name = self.list[idx]
                self.session.open(NssInstall, self.xml, name)
            except Exception as e:
                print('error: ', str(e))
        else:
            self.close()


class NssDailySetting(Screen):
    def __init__(self, session):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('DAILY SETTINGS')
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        self['list'] = nssList([])
        self['title'] = Label(self.setup_title)
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['pth'] = Label('')
        self['pform'] = Label('')
        self['info'] = Label(_('Loading data... Please wait'))
        self['key_green'] = Button(_('Select'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self['key_yellow'].hide()
        self['key_green'].hide()
        self.LcnOn = False
        if os.path.exists('/etc/enigma2/lcndb'):
            self['key_yellow'].show()
            self['key_yellow'] = Button('Lcn')
            self.LcnOn = True
        self["key_blue"] = Button()
        self['key_blue'].hide()
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'green': self.okRun,
                                                       'back': self.closerm,
                                                       'red': self.closerm,
                                                       'yellow': self.Lcn,
                                                       'cancel': self.closerm}, -1)
        self.onLayoutFinish.append(self.updateMenuList)

    def Lcn(self):
        if self.LcnOn:
            lcn = LCN()
            lcn.read()
            if len(lcn.lcnlist) > 0:
                lcn.writeBouquet()
                lcn.ReloadBouquets()
                self.session.open(MessageBox, _('Sorting Terrestrial channels with Lcn rules Completed'), MessageBox.TYPE_INFO, timeout=5)

    def closerm(self):
        self.close()

    def updateMenuList(self):
        self.menu_list = []
        for x in self.menu_list:
            del self.menu_list[0]
        list = []
        idx = 0
        for x in Panel_list2:
            list.append(nssListEntry(x, idx))
            self.menu_list.append(x)
            idx += 1
        self['list'].setList(list)
        self['key_green'].show()
        self['info'].setText(_('Please select ...'))

    def okRun(self):
        self.keyNumberGlobalCB(self['list'].getSelectedIndex())

    def keyNumberGlobalCB(self, idx):
        sel = self.menu_list[idx]
        if sel == ('SAVE DTT BOUQUET'):
            self.terrestrialsave()
        elif sel == ('RESTORE DTT BOUQUET'):
            self.terrestrial_restore()
        elif sel == ('SETTINGS CIEFP'):
            self.session.open(SettingCiefp)
        elif sel == ('SETTINGS CYRUS'):
            self.session.open(SettingCyrus)
        elif sel == ('SETTINGS BI58'):
            self.session.open(SettingBi58)
        elif sel == ('SETTINGS MANUTEK'):
            self.session.open(SettingManutek)
        elif sel == ('SETTINGS MILENKA61'):
            self.session.open(Milenka61)
        elif sel == ('SETTINGS MORPHEUS'):
            self.session.open(SettingMorpheus)
        elif sel == ('SETTINGS PREDRAG'):
            self.session.open(SettingPredrag)
        elif sel == ('SETTINGS VHANNIBAL'):
            self.session.open(SettingVhan)
        elif sel == ('SETTINGS VHANNIBAL 2'):
            self.session.open(SettingVhan2)
        elif sel == _('UPDATE SATELLITES.XML'):
            self.okSATELLITE()
        elif sel == _('UPDATE TERRESTRIAL.XML'):
            self.okTERRESTRIAL()
        else:
            return

    def terrestrial_restore(self):
        self.session.openWithCallback(self.terrestrial_restore2, MessageBox, _("This operation restore your Favorite channel Dtt\nfrom =>>THISPLUGIN/temp/TerrestrialChannelListArchive\nDo you really want to continue?"), MessageBox.TYPE_YESNO)

    def terrestrial_restore2(self, answer):
        if answer:
            terrestrial_rest()

    def terrestrialsave(self):
        self.session.openWithCallback(self.terrestrialsave2, MessageBox, _("This operation save your Favorite channel Dtt\nto =>>/tmp/*_enigma2settingsbackup.tar.gz\nDo you really want to continue?"), MessageBox.TYPE_YESNO)

    def terrestrialsave2(self, answer):
        if answer:
            terrestrial()

    def okSATELLITE(self):
        self.session.openWithCallback(self.okSATELLITE2, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okSATELLITE2(self, answer):
        if answer:
            if Utils.checkInternet():
                try:
                    url_sat_oealliance = 'http://raw.githubusercontent.com/oe-alliance/oe-alliance-tuxbox-common/master/src/satellites.xml'
                    link_sat = ssl_urlopen(url_sat_oealliance)
                    dirCopy = '/etc/tuxbox/satellites.xml'
                    import requests
                    r = requests.get(link_sat)
                    with open(dirCopy, 'wb') as f:
                        f.write(r.content)
                    self.session.open(MessageBox, _('Satellites.xml Updated!'), MessageBox.TYPE_INFO, timeout=5)
                    self['info'].setText(_('Installation done !!!'))
                except Exception as e:
                    print('error: ', str(e))
            else:
                self.session.open(MessageBox, "No Internet", MessageBox.TYPE_INFO)

    def okTERRESTRIAL(self):
        self.session.openWithCallback(self.okTERRESTRIAL2, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okTERRESTRIAL2(self, answer):
        if answer:
            if Utils.checkInternet():
                try:
                    url_sat_oealliance = 'https://raw.githubusercontent.com/oe-alliance/oe-alliance-tuxbox-common/master/src/terrestrial.xml'
                    link_ter = ssl_urlopen(url_sat_oealliance)
                    dirCopy = '/etc/tuxbox/terrestrial.xml'
                    import requests
                    r = requests.get(link_ter)
                    with open(dirCopy, 'wb') as f:
                        f.write(r.content)
                    self.session.open(MessageBox, _('Terrestrial.xml Updated!'), MessageBox.TYPE_INFO, timeout=5)
                    self['info'].setText(_('Installation done !!!'))
                except Exception as e:
                    print('error: ', str(e))
            else:
                self.session.open(MessageBox, "No Internet", MessageBox.TYPE_INFO)


class SettingVhan(Screen):
    def __init__(self, session):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('Vhannibal Setting')
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        self.list = []
        self['list'] = nssList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pform'] = Label('PLEASE VISIT VHANNIBAL.NET SITE')
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['key_green'] = Button(_('Install'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self["key_blue"] = Button()
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.downloading = False
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/info'):
            self.timer_conn = self.timer.timeout.connect(self.downxmlpage)
        else:
            self.timer.callback.append(self.downxmlpage)
        self.timer.start(500, 1)
        self['title'] = Label(self.setup_title)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'green': self.okRun,
                                                       'red': self.close,
                                                       'cancel': self.close}, -2)

    def downxmlpage(self):
        self.names = []
        self.urls = []
        try:
            urlsat = 'https://www.vhannibal.net/asd.php'
            data = make_req(urlsat)
            if PY3:
                data = six.ensure_str(data)
            match = re.compile('<td><a href="(.+?)">(.+?)</a></td>.*?<td>(.+?)</td>', re.DOTALL).findall(data)
            for url, name, date in match:
                name = name.replace('&#127381;', '') + ' ' + date
                url = "https://www.vhannibal.net/" + url
                self.urls.append(Utils.str_encode(url.strip()))
                self.names.append(Utils.str_encode(name.strip()))
            self.downloading = True
            self['info'].setText(_('Please select ...'))
            self['key_green'].show()
            showlistNss(self.names, self['list'])
        except Exception as e:
            print('downxmlpage get failed: ', str(e))
            self['info'].setText(_('Download page get failed ...'))

    def okRun(self):
        self.session.openWithCallback(self.okRun1, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okRun1(self, answer):
        if answer:
            global set
            set = 0
            if self.downloading is True:
                idx = self["list"].getSelectionIndex()
                self.name = self.names[idx]
                url = self.urls[idx]
                dest = "/tmp/settings.zip"
                self.namel = ''
                import requests
                r = requests.get(url)
                with open(dest, 'wb') as f:
                    f.write(r.content)
                if 'dtt' not in self.name.lower():
                    set = 1
                    terrestrial()
                if os.path.exists(dest):
                    fdest1 = "/tmp/unzipped"
                    fdest2 = "/etc/enigma2"
                    if os.path.exists("/tmp/unzipped"):
                        cmd = "rm -rf '/tmp/unzipped'"
                        os.system(cmd)
                    os.makedirs('/tmp/unzipped')
                    cmd2 = "unzip -o -q '/tmp/settings.zip' -d " + fdest1
                    os.system(cmd2)
                    for root, dirs, files in os.walk(fdest1):
                        for name in dirs:
                            self.namel = name
                    os.system('rm -rf /etc/enigma2/lamedb')
                    os.system('rm -rf /etc/enigma2/*.radio')
                    os.system('rm -rf /etc/enigma2/*.tv')
                    os.system('rm -rf /etc/enigma2/*.del')
                    os.system("cp -rf  '/tmp/unzipped/" + str(self.namel) + "/'* " + fdest2)
                    title = _("Installation Settings")
                    self.session.openWithCallback(self.yes, tvConsole, title=_(title), cmdlist=["wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /tmp/inst.txt 2>&1 &; sleep 3"], closeOnSuccess=False)
                    self['info'].setText(_('Settings Installed ...'))
                else:
                    self['info'].setText(_('Settings Not Installed ...'))
            else:
                self['info'].setText(_('No Downloading ...'))

    def yes(self):
        ReloadBouquets()


class SettingVhan2(Screen):
    def __init__(self, session):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('Vhannibal Setting')
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        self.list = []
        self['list'] = nssList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pform'] = Label('PLEASE VISIT VHANNIBAL.NET SITE')
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['key_green'] = Button(_('Install'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self["key_blue"] = Button()
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.downloading = False
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/info'):
            self.timer_conn = self.timer.timeout.connect(self.downxmlpage)
        else:
            self.timer.callback.append(self.downxmlpage)
        self.timer.start(500, 1)
        self['title'] = Label(self.setup_title)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'green': self.okRun,
                                                       'red': self.close,
                                                       'cancel': self.close}, -2)

    def downxmlpage(self):
        url = 'http://sat.alfa-tech.net/upload/settings/vhannibal/'
        data = make_req(url)
        if PY3:
            data = six.ensure_str(data)
        self.names = []
        self.urls = []
        try:
            regex = '<a href="Vhannibal(.*?).zip"'
            match = re.compile(regex).findall(data)
            for url in match:
                if '.php' in url.lower():
                    continue
                name = "Vhannibal" + url
                name = name.replace('&#127381;', '').replace("%20", " ")
                url = "http://sat.alfa-tech.net/upload/settings/vhannibal/Vhannibal" + url + '.zip'
                self.urls.append(Utils.str_encode(url.strip()))
                self.names.append(Utils.str_encode(name.strip()))
                self.downloading = True
            self['info'].setText(_('Please select ...'))
            self['key_green'].show()
            showlistNss(self.names, self['list'])
        except Exception as e:
            print('downxmlpage get failed: ', str(e))
            self['info'].setText(_('Download page get failed ...'))

    def okRun(self):
        self.session.openWithCallback(self.okRun1, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okRun1(self, answer):
        if answer:
            global set
            set = 0
            if self.downloading is True:
                try:
                    idx = self["list"].getSelectionIndex()
                    self.name = self.names[idx]
                    url = self.urls[idx]
                    dest = "/tmp/settings.zip"

                    if 'dtt' not in url.lower():
                        set = 1
                        terrestrial()

                    # if PY3:
                        # url = six.ensure_binary(url)
                    if url.startswith(b"https") and sslverify:
                        parsed_uri = urlparse(url)
                        domain = parsed_uri.hostname
                        sniFactory = SNIFactory(domain)
                        downloadPage(url, dest, sniFactory, timeout=5).addCallback(self.download, dest).addErrback(self.downloadError)
                    else:
                        downloadPage(url, dest).addCallback(self.download, dest).addErrback(self.downloadError)
                except Exception as e:
                    print('error: ', str(e))

    def download(self, data, dest):
        try:
            if os.path.exists(dest):
                self.namel = ''
                fdest1 = "/tmp/unzipped"
                fdest2 = "/etc/enigma2"
                if os.path.exists("/tmp/unzipped"):
                    cmd = "rm -rf '/tmp/unzipped'"
                    os.system(cmd)
                os.makedirs('/tmp/unzipped')
                cmd2 = "unzip -o -q '/tmp/settings.zip' -d " + fdest1
                os.system(cmd2)
                for root, dirs, files in os.walk(fdest1):
                    for name in dirs:
                        self.namel = name
                os.system('rm -rf /etc/enigma2/lamedb')
                os.system('rm -rf /etc/enigma2/*.radio')
                os.system('rm -rf /etc/enigma2/*.tv')
                os.system('rm -rf /etc/enigma2/*.del')
                os.system("cp -rf  '/tmp/unzipped/" + str(self.namel) + "/'* " + fdest2)
                title = _("Installation Settings")
                self.session.openWithCallback(self.yes, tvConsole, title=_(title), cmdlist=["wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /tmp/inst.txt 2>&1 &; sleep 3"], closeOnSuccess=False)
                self['info'].setText(_('Settings Installed ...'))
            else:
                self['info'].setText(_('Settings Not Installed ...'))

        except Exception as e:
            print('error: ', str(e))
            self['info'].setText(_('Not Installed ...'))

    def downloadError(self, png):
        try:
            if not fileExists(png):
                self.poster_resize(no_cover)
        except Exception as e:
            print('error: ', str(e))

    def yes(self):
        ReloadBouquets()


class Milenka61(Screen):
    def __init__(self, session):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('Milenka61 Setting')
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        self.list = []
        self['list'] = nssList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pform'] = Label('PLEASE VISIT LINUXSAT-SUPPORT SITE')
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['key_green'] = Button(_('Install'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self["key_blue"] = Button()
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.downloading = False
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/info'):
            self.timer_conn = self.timer.timeout.connect(self.downxmlpage)
        else:
            self.timer.callback.append(self.downxmlpage)
        self.timer.start(500, 1)
        self['title'] = Label(self.setup_title)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'green': self.okRun,
                                                       'red': self.close,
                                                       'cancel': self.close}, -2)

    def downxmlpage(self):
        url = 'http://178.63.156.75/tarGz/'
        data = make_req(url)
        if PY3:
            data = six.ensure_str(data)
        r = data
        self.names = []
        self.urls = []
        try:
            regex = '<a href="Satvenus(.+?)".*?align="right">(.*?) </td>'
            match = re.compile(regex).findall(r)
            for url, txt in match:
                if url.find('.tar.gz') != -1:
                    name = url.replace('_EX-YU_Lista_za_milenka61_', '')
                    date = re.search("(.+?)-(.+?)-(.+?) ", txt).group()
                    name = name + ' ' + date
                    name = name.replace("_", " ").replace(".tar.gz", "")
                    url = "http://178.63.156.75/tarGz/Satvenus" + url
                    self.urls.append(Utils.str_encode(url.strip()))
                    self.names.append(Utils.str_encode(name.strip()))
                self.downloading = True
            self['info'].setText(_('Please select ...'))
            self['key_green'].show()
            showlistNss(self.names, self['list'])
        except Exception as e:
            print('downxmlpage get failed: ', str(e))
            self['info'].setText(_('Download page get failed ...'))

    def okRun(self):
        self.session.openWithCallback(self.okRun1, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okRun1(self, answer):
        if answer:
            global set
            set = 0
            if self.downloading is True:
                idx = self["list"].getSelectionIndex()
                url = self.urls[idx]
                dest = "/tmp/settings.tar.gz"
                if 'dtt' not in url.lower():
                    set = 1
                    terrestrial()
                import requests
                r = requests.get(url)
                with open(dest, 'wb') as f:
                    f.write(r.content)
                if os.path.exists('/tmp/settings.tar.gz'):
                    os.system('rm -rf /etc/enigma2/lamedb')
                    os.system('rm -rf /etc/enigma2/*.radio')
                    os.system('rm -rf /etc/enigma2/*.tv')
                    os.system('rm -rf /etc/enigma2/*.del')
                    title = _("Installation Settings")
                    self.session.openWithCallback(self.yes, tvConsole, title=_(title), cmdlist=["tar -xvf /tmp/settings.tar.gz -C /; wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /tmp/inst.txt 2>&1 &"], closeOnSuccess=False)
                self['info'].setText(_('Settings Installed ...'))
            else:
                self['info'].setText(_('Settings Not Installed ...'))

    def yes(self):
        ReloadBouquets()


class SettingManutek(Screen):
    def __init__(self, session):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('Manutek Setting')
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        self.list = []
        self['list'] = nssList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pform'] = Label('PLEASE VISIT SAT.TECHNOLOGY SITE')
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['key_green'] = Button(_('Install'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self["key_blue"] = Button()
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.downloading = False
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/info'):
            self.timer_conn = self.timer.timeout.connect(self.downxmlpage)
        else:
            self.timer.callback.append(self.downxmlpage)
        self.timer.start(500, 1)
        self['title'] = Label(self.setup_title)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'green': self.okRun,
                                                       'red': self.close,
                                                       'cancel': self.close}, -2)

    def downxmlpage(self):
        url = 'http://www.manutek.it/isetting/index.php'
        data = make_req(url)
        if PY3:
            data = six.ensure_str(data)
        r = data
        self.names = []
        self.urls = []
        try:
            regex = 'href="/isetting/.*?file=(.+?).zip">'
            match = re.compile(regex).findall(r)
            for url in match:
                name = url
                url = 'http://www.manutek.it/isetting/enigma2/' + url + '.zip'
                name = name.replace("NemoxyzRLS_Manutek_", "").replace("_", " ").replace("%20", " ")
                self.urls.append(Utils.str_encode(url.strip()))
                self.names.append(Utils.str_encode(name.strip()))
                self.downloading = True
            self['info'].setText(_('Please select ...'))
            self['key_green'].show()
            showlistNss(self.names, self['list'])
        except Exception as e:
            print('downxmlpage get failed: ', str(e))
            self['info'].setText(_('Download page get failed ...'))

    def okRun(self):
        self.session.openWithCallback(self.okRun1, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okRun1(self, answer):
        if answer:
            global set
            set = 0
            if self.downloading is True:
                idx = self["list"].getSelectionIndex()
                url = self.urls[idx]
                dest = "/tmp/settings.zip"
                self.namel = ''
                if 'dtt' not in url.lower():
                    set = 1
                    terrestrial()
                import requests
                r = requests.get(url)
                with open(dest, 'wb') as f:
                    f.write(r.content)
                if os.path.exists(dest):
                    fdest1 = "/tmp/unzipped"
                    fdest2 = "/etc/enigma2"
                    if os.path.exists("/tmp/unzipped"):
                        cmd = "rm -rf '/tmp/unzipped'"
                        os.system(cmd)
                    os.makedirs('/tmp/unzipped')
                    cmd2 = "unzip -o -q '/tmp/settings.zip' -d " + fdest1
                    os.system(cmd2)
                    for root, dirs, files in os.walk(fdest1):
                        for name in dirs:
                            self.namel = name
                    os.system('rm -rf /etc/enigma2/lamedb')
                    os.system('rm -rf /etc/enigma2/*.radio')
                    os.system('rm -rf /etc/enigma2/*.tv')
                    os.system('rm -rf /etc/enigma2/*.del')
                    os.system("cp -rf  '/tmp/unzipped/" + str(self.namel) + "/'* " + fdest2)
                    title = _("Installation Settings")
                    self.session.openWithCallback(self.yes, tvConsole, title=_(title), cmdlist=["wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /tmp/inst.txt 2>&1 &; sleep 3"], closeOnSuccess=False)
                    self['info'].setText(_('Settings Installed ...'))
            else:
                self['info'].setText(_('Settings Not Installed ...'))

    def yes(self):
        ReloadBouquets()


class SettingMorpheus(Screen):
    def __init__(self, session):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('Morpheus Setting')
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        self.list = []
        self['list'] = nssList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pform'] = Label('PLEASE VISIT MORPHEUS883.ALTERVISTA.ORG SITE')
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['key_green'] = Button(_('Install'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self["key_blue"] = Button()
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.downloading = False
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/info'):
            self.timer_conn = self.timer.timeout.connect(self.downxmlpage)
        else:
            self.timer.callback.append(self.downxmlpage)
        self.timer.start(500, 1)
        self['title'] = Label(self.setup_title)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'green': self.okRun,
                                                       'red': self.close,
                                                       'cancel': self.close}, -2)

    def downxmlpage(self):
        url = 'https://github.com/morpheus883/enigma2-zipped'
        data = make_req(url)
        if PY3:
            data = six.ensure_str(data)
        r = data
        self.names = []
        self.urls = []
        try:
            regex = 'name":"E2_Morph883_(.*?).zip".*?path":"(.*?)"'
            # regex = 'title="E2_Morph883_(.*?).zip".*?href="(.*?)"'
            match = re.compile(regex).findall(r)
            for name, url in match:
                if url.find('.zip') != -1:
                    url = url.replace('blob', 'raw')
                    url = 'https://github.com/morpheus883/enigma2-zipped/raw/master/' + url
                    name = 'Morph883 ' + name
                    self.urls.append(Utils.str_encode(url.strip()))
                    self.names.append(Utils.str_encode(name.strip()))
                    self.downloading = True
            self['key_green'].show()
            self['info'].setText(_('Please select ...'))
            showlistNss(self.names, self['list'])
        except Exception as e:
            print('downxmlpage get failed: ', str(e))
            self['info'].setText(_('Download page get failed ...'))

    def okRun(self):
        self.session.openWithCallback(self.okRun1, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okRun1(self, answer):
        if answer:
            global set
            set = 0
            if self.downloading is True:
                idx = self["list"].getSelectionIndex()
                url = self.urls[idx]
                dest = "/tmp/settings.zip"
                self.namel = ''
                if 'dtt' not in url.lower():
                    set = 1
                    terrestrial()
                import requests
                r = requests.get(url)
                with open(dest, 'wb') as f:
                    f.write(r.content)
                if os.path.exists(dest):
                    # fdest1 = "/tmp/unzipped"
                    fdest2 = "/etc/enigma2"
                    if os.path.exists("/tmp/unzipped"):
                        os.system('rm -rf /tmp/unzipped')
                    os.makedirs('/tmp/unzipped')
                    os.system('unzip -o -q /tmp/settings.zip -d /tmp/unzipped')
                    path = '/tmp/unzipped'
                    # pth = ''
                    for root, dirs, files in os.walk(path):
                        for name in dirs:
                            self.namel = name
                    os.system('rm -rf /etc/enigma2/lamedb')
                    os.system('rm -rf /etc/enigma2/*.radio')
                    os.system('rm -rf /etc/enigma2/*.tv')
                    os.system('rm -rf /etc/enigma2/*.del')
                    os.system("cp -rf  '/tmp/unzipped/" + str(self.namel) + "/'* " + fdest2)
                    title = _("Installation Settings")
                    self.session.openWithCallback(self.yes, tvConsole, title=_(title), cmdlist=["wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /tmp/inst.txt 2>&1 &"], closeOnSuccess=False)
                    self['info'].setText(_('Settings Installed ...'))
            else:
                self['info'].setText(_('Settings Not Installed ...'))

    def yes(self):
        ReloadBouquets()


class SettingCiefp(Screen):
    def __init__(self, session):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('Ciefp Setting')
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        self.list = []
        self['list'] = nssList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pform'] = Label('PLEASE VISIT GITHUB.COM/CIEFP SITE')
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['key_green'] = Button(_('Install'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self["key_blue"] = Button()
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.downloading = False
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/info'):
            self.timer_conn = self.timer.timeout.connect(self.downxmlpage)
        else:
            self.timer.callback.append(self.downxmlpage)
        self.timer.start(500, 1)
        self['title'] = Label(self.setup_title)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'green': self.okRun,
                                                       'red': self.close,
                                                       'cancel': self.close}, -2)

    def downxmlpage(self):
        url = 'https://github.com/ciefp/ciefpsettings-enigma2-zipped'
        data = make_req(url)
        if PY3:
            data = six.ensure_str(data)
        r = data
        self.names = []
        self.urls = []
        try:
            n1 = r.find('title="README.txt', 0)
            n2 = r.find('href="#readme">', n1)
            r = r[n1:n2]
            regex = 'title="ciefp-E2-(.*?).zip".*?href="(.*?)"'
            match = re.compile(regex).findall(r)
            for name, url in match:
                if url.find('.zip') != -1:
                    url = url.replace('blob', 'raw')
                    url = 'https://github.com' + url
                    self.urls.append(Utils.str_encode(url.strip()))
                    self.names.append(Utils.str_encode(name.strip()))
                    self.downloading = True
            self['key_green'].show()
            self['info'].setText(_('Please select ...'))
            showlistNss(self.names, self['list'])
        except Exception as e:
            print('downxmlpage get failed: ', str(e))
            self['info'].setText(_('Download page get failed ...'))

    def okRun(self):
        self.session.openWithCallback(self.okRun1, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okRun1(self, answer):
        if answer:
            global set
            set = 0
            if self.downloading is True:
                idx = self["list"].getSelectionIndex()
                url = self.urls[idx]
                dest = "/tmp/settings.zip"
                self.namel = ''
                if 'dtt' not in url.lower():
                    set = 1
                    terrestrial()
                import requests
                r = requests.get(url)
                with open(dest, 'wb') as f:
                    f.write(r.content)
                if os.path.exists(dest):
                    fdest2 = "/etc/enigma2"
                    if os.path.exists("/tmp/unzipped"):
                        os.system('rm -rf /tmp/unzipped')
                    os.makedirs('/tmp/unzipped')
                    os.system('unzip -o -q /tmp/settings.zip -d /tmp/unzipped')
                    path = '/tmp/unzipped'
                    for root, dirs, files in os.walk(path):
                        for name in dirs:
                            self.namel = name
                    os.system('rm -rf /etc/enigma2/lamedb')
                    os.system('rm -rf /etc/enigma2/*.radio')
                    os.system('rm -rf /etc/enigma2/*.tv')
                    os.system('rm -rf /etc/enigma2/*.del')
                    os.system("cp -rf  '/tmp/unzipped/" + str(self.namel) + "/'* " + fdest2)
                    title = _("Installation Settings")
                    self.session.openWithCallback(self.yes, tvConsole, title=_(title), cmdlist=["wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /tmp/inst.txt 2>&1 &"], closeOnSuccess=False)
                    self['info'].setText(_('Settings Installed ...'))
            else:
                self['info'].setText(_('Settings Not Installed ...'))

    def yes(self):
        ReloadBouquets()


class SettingBi58(Screen):
    def __init__(self, session):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('Bi58 Setting')
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        self.list = []
        self['list'] = nssList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pform'] = Label('PLEASE VISIT LINUXSAT-SUPPORT SITE')
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['key_green'] = Button(_('Install'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self["key_blue"] = Button()
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.downloading = False
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/info'):
            self.timer_conn = self.timer.timeout.connect(self.downxmlpage)
        else:
            self.timer.callback.append(self.downxmlpage)
        self.timer.start(500, 1)
        self['title'] = Label(self.setup_title)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'green': self.okRun,
                                                       'red': self.close,
                                                       'cancel': self.close}, -2)

    def downxmlpage(self):
        url = 'http://178.63.156.75/paneladdons/Bi58/'
        data = make_req(url)
        if PY3:
            data = six.ensure_str(data)
        r = data
        self.names = []
        self.urls = []
        try:
            regex = '<a href="bi58-e2(.*?)".*?align="right">(.*?) </td>'
            match = re.compile(regex).findall(r)
            for url, txt in match:
                if url.find('.tar.gz') != -1:
                    name = url.replace('-settings-', 'bi58 ')
                    date = re.search("(.+?)-(.+?)-(.+?) ", txt).group()
                    name = name + ' ' + date
                    name = name.replace(".tar.gz", "").replace("%20", " ")
                    url = "http://178.63.156.75/paneladdons/Bi58/bi58-e2" + url
                    self.urls.append(Utils.str_encode(url.strip()))
                    self.names.append(Utils.str_encode(name.strip()))
                    self.downloading = True
            self['key_green'].show()
            self['info'].setText(_('Please select ...'))
            showlistNss(self.names, self['list'])
        except Exception as e:
            print('downxmlpage get failed: ', str(e))
            self['info'].setText(_('Download page get failed ...'))

    def okRun(self):
        self.session.openWithCallback(self.okRun1, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okRun1(self, answer):
        if answer:
            global set
            set = 0
            if self.downloading is True:
                idx = self["list"].getSelectionIndex()
                url = self.urls[idx]
                dest = "/tmp/settings.tar.gz"
                if 'dtt' not in url.lower():
                    set = 1
                    terrestrial()
                import requests
                r = requests.get(url)
                with open(dest, 'wb') as f:
                    f.write(r.content)
                if os.path.exists('/tmp/settings.tar.gz'):
                    os.system('rm -rf /etc/enigma2/lamedb')
                    os.system('rm -rf /etc/enigma2/*.radio')
                    os.system('rm -rf /etc/enigma2/*.tv')
                    os.system('rm -rf /etc/enigma2/*.del')
                    title = _("Installation Settings")
                    self.session.openWithCallback(self.yes, tvConsole, title=_(title), cmdlist=["tar -xvf /tmp/settings.tar.gz -C /; wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /tmp/inst.txt 2>&1 &"], closeOnSuccess=False)
                    self['info'].setText(_('Settings Installed ...'))
            else:
                self['info'].setText(_('Settings Not Installed ...'))

    def yes(self):
        ReloadBouquets()


class SettingPredrag(Screen):
    def __init__(self, session):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('Predrag Setting')
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        self.list = []
        self['list'] = nssList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pform'] = Label('PLEASE VISIT LINUXSAT-SUPPORT SITE')
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['key_green'] = Button(_('Install'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self["key_blue"] = Button()
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.downloading = False
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/info'):
            self.timer_conn = self.timer.timeout.connect(self.downxmlpage)
        else:
            self.timer.callback.append(self.downxmlpage)
        self.timer.start(500, 1)
        self['title'] = Label(self.setup_title)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'green': self.okRun,
                                                       'red': self.close,
                                                       'cancel': self.close}, -2)

    def downxmlpage(self):
        url = 'http://178.63.156.75/paneladdons/Predr@g/'
        data = make_req(url)
        if PY3:
            data = six.ensure_str(data)
        r = data
        self.names = []
        self.urls = []
        try:
            regex = '<a href="predrag(.*?)".*?align="right">(.*?) </td>'
            match = re.compile(regex).findall(r)
            for url, txt in match:
                if url.find('.tar.gz') != -1:
                    name = url.replace('-settings-e2-', 'Predrag ')
                    date = re.search("(.+?)-(.+?)-(.+?) ", txt).group()
                    name = name + ' ' + date
                    name = name.replace(".tar.gz", "").replace("%20", " ")
                    url = "http://178.63.156.75/paneladdons/Predr@g/predrag" + url
                    self.urls.append(Utils.str_encode(url.strip()))
                    self.names.append(Utils.str_encode(name.strip()))
                    self.downloading = True
            self['key_green'].show()
            self['info'].setText(_('Please select ...'))
            showlistNss(self.names, self['list'])
        except Exception as e:
            print('downxmlpage get failed: ', str(e))
            self['info'].setText(_('Download page get failed ...'))

    def okRun(self):
        self.session.openWithCallback(self.okRun1, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okRun1(self, answer):
        if answer:
            global set
            set = 0
            if self.downloading is True:
                idx = self["list"].getSelectionIndex()
                url = self.urls[idx]
                dest = "/tmp/settings.tar.gz"
                if 'dtt' not in url.lower():
                    set = 1
                    terrestrial()
                import requests
                r = requests.get(url)
                with open(dest, 'wb') as f:
                    f.write(r.content)
                if os.path.exists('/tmp/settings.tar.gz'):
                    os.system('rm -rf /etc/enigma2/lamedb')
                    os.system('rm -rf /etc/enigma2/*.radio')
                    os.system('rm -rf /etc/enigma2/*.tv')
                    os.system('rm -rf /etc/enigma2/*.del')
                    title = _("Installation Settings")
                    self.session.openWithCallback(self.yes, tvConsole, title=_(title), cmdlist=["tar -xvf /tmp/settings.tar.gz -C /; wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /tmp/inst.txt 2>&1 &"], closeOnSuccess=False)
                    self['info'].setText(_('Settings Installed ...'))
            else:
                self['info'].setText(_('Settings Not Installed ...'))

    def yes(self):
        ReloadBouquets()


class SettingCyrus(Screen):
    def __init__(self, session):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('Cyrus Setting')
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        self.list = []
        self['list'] = nssList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pform'] = Label('PLEASE VISIT CYRUSSETTINGS.COM SITE')
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['key_green'] = Button(_('Install'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self["key_blue"] = Button()
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.downloading = False
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/info'):

            self.timer_conn = self.timer.timeout.connect(self.downxmlpage)
        else:
            self.timer.callback.append(self.downxmlpage)
        self.timer.start(500, 1)
        self['title'] = Label(self.setup_title)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'green': self.okRun,
                                                       'red': self.close,
                                                       'cancel': self.close}, -2)

    def downxmlpage(self):
        url = 'http://www.cyrussettings.com/Set_29_11_2011/Dreambox-IpBox/Config.xml'
        data = make_req(url)
        if PY3:
            data = six.ensure_str(data)
        r = data
        self.names = []
        self.urls = []
        try:
            n1 = r.find('name="Sat">', 0)
            n2 = r.find("/ruleset>", n1)
            r = r[n1:n2]
            regex = 'Name="(.*?)".*?Link="(.*?)".*?Date="(.*?)"><'
            match = re.compile(regex).findall(r)
            for name, url, date in match:
                if url.find('.zip') != -1:
                    if 'ddt' in name.lower():
                        continue
                    if 'Sat' in name.lower():
                        continue
                    name = name + ' ' + date
                    self.urls.append(Utils.str_encode(url.strip()))
                    self.names.append(Utils.str_encode(name.strip()))
                    self.downloading = True
            self['key_green'].show()
            self['info'].setText(_('Please select ...'))
            showlistNss(self.names, self['list'])
        except Exception as e:
            print('downxmlpage get failed: ', str(e))
            self['info'].setText(_('Download page get failed ...'))

    def okRun(self):
        self.session.openWithCallback(self.okRun1, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okRun1(self, answer):
        if answer:
            global set
            set = 0
            if self.downloading is True:
                idx = self["list"].getSelectionIndex()
                url = self.urls[idx]
                dest = "/tmp/settings.zip"
                self.namel = ''
                if 'dtt' not in url.lower():
                    set = 1
                    terrestrial()
                import requests
                r = requests.get(url)
                with open(dest, 'wb') as f:
                    f.write(r.content)
                if os.path.exists(dest):
                    fdest2 = "/etc/enigma2"
                    if os.path.exists("/tmp/unzipped"):
                        os.system('rm -rf /tmp/unzipped')
                    os.makedirs('/tmp/unzipped')
                    os.system('unzip -o -q /tmp/settings.zip -d /tmp/unzipped')
                    path = '/tmp/unzipped'
                    for root, dirs, files in os.walk(path):
                        for name in dirs:
                            self.namel = name
                    os.system('rm -rf /etc/enigma2/lamedb')
                    os.system('rm -rf /etc/enigma2/*.radio')
                    os.system('rm -rf /etc/enigma2/*.tv')
                    os.system('rm -rf /etc/enigma2/*.del')
                    os.system("cp -rf  '/tmp/unzipped/" + str(self.namel) + "/'* " + fdest2)
                    title = _("Installation Settings")
                    self.session.openWithCallback(self.yes, tvConsole, title=_(title), cmdlist=["wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /tmp/inst.txt 2>&1 &"], closeOnSuccess=False)
                    self['info'].setText(_('Settings Installed ...'))
            else:
                self['info'].setText(_('Settings Not Installed ...'))

    def yes(self):
        ReloadBouquets()


class NssInstall(Screen):
    def __init__(self, session, data, name, selection=None):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('NSS CONSOLE')
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        self.selection = selection
        self['info'] = Label('')
        self['pth'] = Label('')
        self['pform'] = Label('')

        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()

        self['progress'].setRange((0, 100))
        self['progress'].setValue(0)

        list = []
        list.sort()
        self['info'].setText(_('... please wait'))
        n1 = data.find(name, 0)
        n2 = data.find("</plugins>", n1)
        data1 = data[n1:n2]
        self.names = []
        self.urls = []
        self.error_message = ""
        self.last_recvbytes = 0
        self.error_message = None
        self.download = None
        self.aborted = False
        self.downloading = False
        regex = '<plugin name="(.*?)".*?url>"(.*?)"</url'
        match = re.compile(regex, re.DOTALL).findall(data1)
        for name, url in match:
            self.names.append(name)
            self.urls.append(url)
        self['list'] = nssList([])
        self['info'].setText(_('Please install ...'))
        self['title'] = Label(self.setup_title)
        self['key_red'] = Button(_('Back'))
        self['key_green'] = Button(_('Install'))
        self['key_yellow'] = Button(_('Download'))
        self["key_blue"] = Button()
        self['key_blue'].hide()
        self['key_green'].hide()
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.message,
                                                       'green': self.message,
                                                       'red': self.close,
                                                       'yellow': self.okDown,
                                                       'cancel': self.close}, -2)
        self.onLayoutFinish.append(self.start)

    def start(self):
        showlistNss(self.names, self['list'])
        self['key_green'].show()

    def message(self, answer=None):
        if answer is None:
            self.session.openWithCallback(self.message, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)
        elif answer:
            idx = self["list"].getSelectionIndex()
            dom = self.names[idx]
            com = self.urls[idx]
            self.prombt(com, dom)
        else:
            return

    def prombt(self, com, dom):
        self.timer = eTimer()
        global set
        self.com = com
        self.dom = dom
        self.downplug = self.com.split("/")[-1]
        down = self.dowfil()
        self['info'].setText(_('Installing ') + self.dom + _('... please wait'))
        if self.com is not None:
            extensionlist = self.com.split('.')
            extension = extensionlist[-1]  # .lower()
            if len(extensionlist) > 1:
                tar = extensionlist[-2]
            if extension in ["gz", "bz2"] and tar == "tar":
                self.command = ['']
                if extension == "gz":
                    self.command = ["tar -xvf " + down + " -C /"]
                elif extension == "bz2":
                    self.command = ["tar -xjvf " + down + " -C /"]

                cmd = "wget --no-cache --no-dns-cache -U '%s' -c '%s' -O '%s' --post-data='action=purge';%s > /dev/null" % (AgentRequest, str(self.com), down, self.command[0])
                if "https" in str(self.com):
                    cmd = "wget --no-check-certificate --no-cache --no-dns-cache -U '%s' -c '%s' -O '%s' --post-data='action=purge';%s > /dev/null" % (AgentRequest, str(self.com), down, self.command[0])

                self.session.open(tvConsole, title='Installation %s' % self.dom, cmdlist=[cmd, 'sleep 5'])  # , finishedCallback=self.msgipkinst)
                self['info'].setText(_('Installation done !!!'))

            elif extension == "deb":
                if not os.path.exists('/var/lib/dpkg/status'):
                    self.session.open(MessageBox, _('Unknow Image!'), MessageBox.TYPE_INFO, timeout=5)
                    self['info'].setText(_('Installation canceled!'))
                else:
                    cmd22 = 'find /usr/bin -name "wget"'
                    res = os.popen(cmd22).read()
                    if 'wget' not in res.lower():
                        cmd23 = 'apt-get update && apt-get install wget'
                        os.popen(cmd23)
                    # cmd = 'dpkg -i %s' % down
                    cmd = 'apt-get -f -y --force-yes install %s' % down
                    # cmd = 'dpkg --install --force-overwrite %s' % self.dest
                    # cmd = "wget -U '%s' -c '%s' -O '%s';apt-get install -f -y %s" % (RequestAgent(), str(self.com), self.dest, self.dest)
                    # if "https" in str(self.com):
                        # cmd = "wget --no-check-certificate -U '%s' -c '%s' -O '%s';apt-get install -f -y %s" % (RequestAgent(), str(self.com), self.dest, self.dest)
                    self.session.open(tvConsole, _('Downloading-installing: %s') % self.dom, [cmd], closeOnSuccess=False)
                    self['info'].setText(_('Installation done !!!'))
            elif extension == "ipk":
                if os.path.exists('/var/lib/dpkg/info'):
                    self.session.open(MessageBox, _('Unknow Image!'), MessageBox.TYPE_INFO, timeout=5)
                    self['info'].setText(_('Installation canceled!'))
                else:
                    cmd = "opkg install --force-reinstall %s > /dev/null" % down
                    # cmd = "wget -U '%s' -c '%s' -O '%s';opkg install --force-reinstall %s > /dev/null" % (RequestAgent(), str(self.com), self.dest, self.dest)
                    # if "https" in str(self.com):
                        # cmd = "wget --no-check-certificate -U '%s' -c '%s' -O '%s';opkg install --force-reinstall %s > /dev/null" % (RequestAgent(), str(self.com), self.dest, self.dest)
                    self.session.open(tvConsole, _('Downloading-installing: %s') % self.dom, [cmd], closeOnSuccess=False)
                    self['info'].setText(_('Installation done !!!'))
            elif self.com.endswith('.zip'):
                if 'setting' in self.dom.lower():
                    if not os.path.exists('/var/lib/dpkg/status'):
                        set = 1
                        terrestrial()
                    if os.path.exists("/tmp/unzipped"):
                        os.system('rm -rf /tmp/unzipped')
                    os.makedirs('/tmp/unzipped')
                    cmd = []
                    cmd1 = 'unzip -o -q /tmp/settings.zip -d /tmp/unzipped'
                    cmd.append(cmd1)
                    cmd2 = 'rm -rf /etc/enigma2/lamedb'
                    cmd.append(cmd2)
                    cmd3 = 'rm -rf /etc/enigma2/*.radio'
                    cmd.append(cmd3)
                    cmd4 = 'rm -rf /etc/enigma2/*.tv'
                    cmd.append(cmd4)
                    cmd5 = 'cp -rf /tmp/unzipped/*.tv /etc/enigma2'
                    cmd.append(cmd5)
                    cmd6 = 'cp -rf /tmp/unzipped/*.radio /etc/enigma2'
                    cmd.append(cmd6)
                    cmd7 = 'cp -rf /tmp/unzipped/lamedb /etc/enigma2'
                    cmd.append(cmd7)
                    if not os.path.exists("/etc/enigma2/blacklist"):
                        cmd8 = 'cp -rf /tmp/unzipped/blacklist /etc/tuxbox/'
                        cmd.append(cmd8)
                    if not os.path.exists("/etc/enigma2/whitelist"):
                        cmd9 = 'cp -rf /tmp/unzipped/whitelist /etc/tuxbox/'
                        cmd.append(cmd9)
                    cmd10 = 'cp -rf /tmp/unzipped/satellites.xml /etc/tuxbox/'
                    cmd.append(cmd10)
                    cmd11 = 'cp -rf /tmp/unzipped/terrestrial.xml /etc/tuxbox/'
                    cmd.append(cmd11)
                    terrestrial_rest()
                    self.session.open(tvConsole, _('SETTING - install: %s') % self.dom, [cmd], closeOnSuccess=False)
                    self['info'].setText(_('Installation done !!!'))
                    # return
                elif 'picon' in self.dom.lower():
                    cmd = ["unzip -o -q %s -d %s > /dev/null" % (down, str(mmkpicon))]
                    # cmd = ["wget -U '%s' -c '%s' -O '%s';unzip -o -q %s -d %s > /dev/null" % (RequestAgent(), str(self.com), self.dest, self.dest, str(mmkpicon))]
                    # if "https" in str(self.com):
                        # cmd = ["wget --no-check-certificate -U '%s' -c '%s' -O '%s';unzip -o -q %s -d %s > /dev/null" % (RequestAgent(), str(self.com), self.dest, self.dest, str(mmkpicon))]
                    self.session.open(tvConsole, _('Downloading-installing: %s') % self.dom, [cmd], closeOnSuccess=False)
                    self['info'].setText(_('Installation done !!!'))
                    # return
                else:
                    self['info'].setText(_('Downloading the selected file in /tmp') + self.dom + _('... please wait'))
                    cmd = ["wget --no-cache --no-dns-cache -U '%s' -c '%s' -O '%s --post-data='action=purge' > /dev/null' " % (RequestAgent(), str(self.com), down)]
                    # cmd = ["wget -U '%s' -c '%s' -O '%s > /dev/null' " % (RequestAgent(), str(self.com), self.dest)]
                    # if "https" in str(self.com):
                        # cmd = ["wget --no-check-certificate -U '%s' -c '%s' -O '%s'" % (RequestAgent(), str(self.com), self.dest)]
                    # self.session.open(tvConsole, _('Downloading: %s') % self.dom, [cmd], closeOnSuccess=False)
                    self.session.open(tvConsole, _('Downloading: %s') % self.dom, cmd, closeOnSuccess=False)
                    self['info'].setText(_('Download done !!!'))
                    self.session.open(MessageBox, _('Download file in /tmp successful!'), MessageBox.TYPE_INFO, timeout=5)
                    # self.timer.start(1000, True)
                    self['info'].setText(_('Download file in /tmp successful!!'))
                    # return
            else:
                self['info'].setText(_('Download Failed!!!') + self.dom + _('... Not supported'))
            self.timer.start(3000, 1)
            self.addondel()

    def dowfil(self):
        self.dest = '/tmp/' + self.downplug
        if os.path.exists(self.dest):
            os.remove(self.dest)
        if PY3:
            import urllib.request as urllib2
            import http.cookiejar as cookielib
        else:
            import urllib2
            import cookielib
        headers = {'User-Agent': RequestAgent()}
        cookie_jar = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
        urllib2.install_opener(opener)
        try:
            req = Request(self.com, data=None, headers=headers)
            handler = urlopen(req, timeout=15)
            data = handler.read()
            with open(self.dest, 'wb') as f:
                f.write(data)
            print('MYDEBUG - download ok - URL: %s , filename: %s' % (self.com, self.dest))
        except:
            print('MYDEBUG - download failed - URL: %s , filename: %s' % (self.com, self.dest))
            self.dest = ''
        return self.dest

    def okDown(self):
        self.session.openWithCallback(self.okDownll, MessageBox, _("Do you want to Download?\nIt could take a few minutes, wait .."), MessageBox.TYPE_YESNO)

    def okDownll(self, answer):
        if answer:
            self['info'].setText(_('... please wait'))
            idx = self["list"].getSelectionIndex()
            self.dom = self.names[idx]
            self.com = self.urls[idx]
            print('1 self.com type=', type(self.com))
            # self.com = six.ensure_binary(self.com)
            # print('2 self.com type=', type(self.com))
            # if PY3:
                # self.com = self.com.encode()
            self.downplug = self.com.split("/")[-1]
            self.dest = '/tmp/' + str(self.downplug)
            if os.path.exists(self.dest):
                os.remove(self.dest)
            if self.com is not None:
                # print('self.com not none', self.com)
                extensionlist = self.com.split('.')
                extension = extensionlist[-1].lower()
                # print('extension', extension)
                if len(extensionlist) > 1:
                    tar = extensionlist[-2].lower()
                if extension in ["gz", "bz2"] and tar == "tar":
                    self.command = ['']
                    if extension == "gz":
                        self.command = ["tar -xvf " + self.dest + " -C /"]
                    elif extension == "bz2":
                        self.command = ["tar -xjvf " + self.dest + " -C /"]
                    self.timer = eTimer()
                    self.timer.start(1000, True)
                    cmd = 'wget --no-cache --no-dns-cache -q -O %s %s --post-data="action=purge";' + self.command[0] % (self.dest, str(self.com))
                    self.session.open(tvConsole, _('Downloading-installing: %s') % self.dom, [cmd], closeOnSuccess=False)
                    self['info'].setText(_('Installation done !!!'))
                    return
                if extension == "deb" and not os.path.exists('/var/lib/dpkg/status'):
                    # if not os.path.exists('/var/lib/dpkg/status'):
                    self.session.open(MessageBox, _('Unknow Image!'), MessageBox.TYPE_INFO, timeout=5)
                    self['info'].setText(_('Download canceled!'))
                    return
                # elif self.com.endswith(".ipk"):
                elif extension == ".ipk" and os.path.exists('/var/lib/dpkg/info'):
                    # if os.path.exists('/var/lib/dpkg/info'):
                    self.session.open(MessageBox, _('Unknow Image!'), MessageBox.TYPE_INFO, timeout=5)
                    self['info'].setText(_('Download canceled!'))
                    return
                # if os.path.exists('/var/lib/dpkg/info'):
                    # self.session.open(MessageBox, _('There is currently a problem with this image.\nBetter not to download.\nTry installing directly with the OK button!'), MessageBox.TYPE_INFO, timeout=5)
                    # self['info'].setText(_('Download canceled!'))
                    # return
                # else:
                self.download = downloadWithProgress(self.com, self.dest)
                self.download.addProgress(self.downloadProgress)
                self.download.start().addCallback(self.install).addErrback(self.download_failed)
            else:
                self['info'].setText(_('Download Failed!!!') + self.dom + _('... Not supported'))

    def downloadProgress(self, recvbytes, totalbytes):
        self['info'].setText(_('Download in progress...'))
        self["progress"].show()
        self['progress'].value = int(100 * self.last_recvbytes / float(totalbytes))
        self['progresstext'].text = '%d of %d kBytes (%.2f%%)' % (self.last_recvbytes / 1024, totalbytes / 1024, 100 * self.last_recvbytes / float(totalbytes))
        self.last_recvbytes = recvbytes

    def showError(self):
        print("download error ")
        self.downloading = False
        self.close()

    def download_failed(self, failure_instance=None, error_message=""):
        self.error_message = error_message
        if error_message == "" and failure_instance is not None:
            self.error_message = failure_instance.getErrorMessage()
        self.downloading = False
        info = 'Download Failed!!! ' + self.error_message
        self['info'].setText(info)
        self.session.open(MessageBox, _(info), MessageBox.TYPE_INFO, timeout=5)
        return

    def addondel(self):
        try:
            AA = ['.ipk, .deb, .tar']
            for root, dirs, files in os.walk('/tmp'):
                for name in files:
                    for x in AA:
                        if x in name:
                            os.remove(x)
            print(_('All file Downloaded in /tmp are removed!'))
        except OSError as e:
            print('Error: %s' % (e.strerror))

    def cancel(self):
        if self.downloader is not None:
            info = 'You are going to abort download, are you sure ?'
            self.session.openWithCallback(self.abort, MessageBox, _(info), MessageBox.TYPE_YESNO)
        else:
            self.aborted = True
            self.close()
        return

    def abort(self):
        print("aborting", self.url)
        if self.download:
            self.download.stop()
        self.aborted = True

    def download_finished(self, string=""):
        if self.aborted:
            self.finish(aborted=True)

    def NssIPK(self):
        self.session.openWithCallback(self.close, NssIPK)

    def install(self, string=''):
        if self.aborted:
            self.finish(aborted=True)
        else:
            self.progclear = 0
            self['info'].setText(_('Please select ...'))
            if os.path.exists(self.dest):
                self.downloading = False
                self['progresstext'].text = ''
                self['progress'].setValue(self.progclear)
                self["progress"].hide()
                self['info'].setText(_('File Downloaded ...'))
                self.NssIPK()


class NssIPK(Screen):
    def __init__(self, session, title=None, cmdlist=None, finishedCallback=None, closeOnSuccess=False):
        self.session = session
        skin = os.path.join(skin_path, 'NssIPK.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = (name_plug)
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        # self.ipkpth = str(config.plugins.nssaddon.ipkpth.value)
        self.ipkpth = '/tmp'
        self.list = []
        self.names = []
        self['key_red'] = Button(_('Back'))
        self['key_green'] = Button(_('Install'))
        self['key_green'].hide()
        self['key_yellow'] = Button(_('Script'))
        self["key_blue"] = Button('Remove')
        self['key_blue'].hide()
        self['title'] = Label(self.setup_title)
        self['info'] = Label('...')  
        self['list'] = nssList([])  
        self['info1'] = Label(_('Path /tmp\nPut .ipk .tar.gz .deb .zip and install'))
        self['actions'] = ActionMap(['OkCancelActions',
                                     'WizardActions',
                                     'ColorActions',
                                     'MenuActions'], {'ok': self.ipkinst,
                                                      'green': self.ipkinst,
                                                      'yellow': self.scriptrun,
                                                      'blue': self.msgipkrmv,
                                                      'red': self.close,
                                                      'menu': self.goConfig,
                                                      'cancel': self.close}, -1)
        self.onLayoutFinish.append(self.refreshlist)

    def scriptrun(self):
        self.session.open(ScriptExecuter)

    def refreshlist(self):
        self.list = []
        self.names = []
        del self.names[:]
        del self.list[:]
        for x in self.list:
            del self.list[0]
        path = self.ipkpth
        for root, dirs, files in os.walk(path):
            if files is not None:
                files.sort()
                for name in files:
                    if name.endswith('.ipk') or name.endswith('.deb') or name.endswith('.zip') or name.endswith('.tar.gz') or name.endswith('.tar'):
                        print('name ipk:', str(name))
                        self.names.append(name)
                        
                self.names.sort(key=lambda x: x, reverse=False)
        if len(self.names) >= 0:
            self['info'].setText(_('Please install ...'))
            self['key_green'].show()
            self['key_blue'].show()
        showlistNss(self.names, self['list'])
        self.getfreespace()

    def msgipkrmv(self, answer=None):
        if len(self.names) >= 0:
            idx = self['list'].getSelectionIndex()
            self.sel = self.names[idx]
            if answer is None:
                self.session.openWithCallback(self.msgipkrmv, MessageBox, (_('Do you really want to remove selected?\n') + self.sel), MessageBox.TYPE_YESNO)
            else:
                self['info'].setText(_('... please wait'))
                self.com = self.ipkpth + '/' + self.sel
                if fileExists(self.com):
                    os.remove(self.com)
                    self.session.open(MessageBox, (_("%s has been successfully deleted\nwait time to refresh the list...") % self.sel), MessageBox.TYPE_INFO, timeout=5)
                    i = len(self.list)
                    del self.list[0:i]
                else:
                    self.session.open(MessageBox, (_("%s not exist!\nwait time to refresh the list...") % self.sel), MessageBox.TYPE_INFO, timeout=5)
            self.refreshlist()

    def getfreespace(self):
        try:
            fspace = Utils.freespace()
            self['info'].setText(str(fspace))
        except Exception as e:
            print(e)

    def goConfig(self):
        self.session.open(nssConfig)

    def ipkinst(self, answer=None):
        if len(self.names) >= 0:
            idx = self['list'].getSelectionIndex()
            self.sel = self.names[idx]
            if answer is None:
                self.session.openWithCallback(self.ipkinst, MessageBox, (_('Do you really want to install the selected Addon?\n') + self.sel), MessageBox.TYPE_YESNO)
            else:
                self['info'].setText(_('... please wait'))
                self.dest = self.ipkpth + '/' + self.sel
                try:
                    if self.sel.endswith('.ipk'):
                        cmd0 = 'echo "Sistem Update .... PLEASE WAIT ::.....";echo ":Install ' + self.dest + '";opkg install --force-reinstall ' + self.dest + ' > /dev/null'
                        self.session.open(tvConsole, title='IPK Local Installation', cmdlist=[cmd0, 'sleep 5'], closeOnSuccess=False)
                    elif self.sel.endswith('.tar.gz'):
                        cmd0 = 'tar -xvf ' + self.dest + ' -C /'
                        self.session.open(tvConsole, title='TAR GZ Local Installation', cmdlist=[cmd0, 'sleep 5'], closeOnSuccess=False)
                    elif self.sel.endswith('.deb'):
                        if os.path.exists('/var/lib/dpkg/info'):
                            # apt-get install -f -y
                            cmd0 = 'echo "Sistem Update .... PLEASE WAIT ::.....";echo ":Install ' + self.dest + '";apt-get -f -y --force-yes install %s > /dev/null' % self.dest
                            self.session.open(tvConsole, title='DEB Local Installation', cmdlist=[cmd0], closeOnSuccess=False)
                        else:
                            self.session.open(MessageBox, _('Unknow Image!'), MessageBox.TYPE_INFO, timeout=5)
                    elif self.sel.endswith('.zip'):
                        if 'picon' in self.sel.lower():
                            self.timer = eTimer()
                            self.timer.start(500, True)
                            cmd = ['unzip -o -q %s -d %s' % (self.dest, str(mmkpicon))]
                            self.session.open(tvConsole, _('Installing: %s') % self.dest, cmdlist=[cmd], closeOnSuccess=False)
                        elif 'setting' in self.sel.lower():
                            if not os.path.exists('/var/lib/dpkg/status'):
                                global set
                                set = 1
                                terrestrial()
                            if os.path.exists("/tmp/unzipped"):
                                os.system('rm -rf /tmp/unzipped')
                            os.makedirs('/tmp/unzipped')
                            cmd = []
                            cmd1 = 'unzip -o -q %s -d /tmp/unzipped' % self.dest
                            cmd.append(cmd1)
                            cmd2 = 'rm -rf /etc/enigma2/lamedb'
                            cmd.append(cmd2)
                            cmd3 = 'rm -rf /etc/enigma2/*.radio'
                            cmd.append(cmd3)
                            cmd4 = 'rm -rf /etc/enigma2/*.tv'
                            cmd.append(cmd4)
                            cmd5 = 'cp -rf /tmp/unzipped/*.tv /etc/enigma2'
                            cmd.append(cmd5)
                            cmd6 = 'cp -rf /tmp/unzipped/*.radio /etc/enigma2'
                            cmd.append(cmd6)
                            cmd7 = 'cp -rf /tmp/unzipped/lamedb /etc/enigma2'
                            cmd.append(cmd7)
                            if not os.path.exists("/etc/enigma2/blacklist"):
                                cmd8 = 'cp -rf /tmp/unzipped/blacklist /etc/tuxbox/'
                                cmd.append(cmd8)
                            if not os.path.exists("/etc/enigma2/whitelist"):
                                cmd9 = 'cp -rf /tmp/unzipped/whitelist /etc/tuxbox/'
                                cmd.append(cmd9)
                            cmd10 = 'cp -rf /tmp/unzipped/satellites.xml /etc/tuxbox/'
                            cmd.append(cmd10)
                            cmd11 = 'cp -rf /tmp/unzipped/terrestrial.xml /etc/tuxbox/'
                            cmd.append(cmd11)
                            self.timer = eTimer()
                            terrestrial_rest()
                            self.timer.start(500, True)
                            self.session.open(tvConsole, _('SETTING - install: %s') % self.dest, cmdlist=[cmd], closeOnSuccess=False)
                    else:
                        self.session.open(MessageBox, _('Unknow Error!'), MessageBox.TYPE_ERROR, timeout=10)
                    self['info'].setText(_('Please install ...'))
                except Exception as e:
                    print('error: ', str(e))
                    self.delFile(self.dest)
                    self['info1'].text = _('File: %s\nInstallation failed!') % self.dest

    def delFile(self, dest):
        if fileExists(self.dest):
            os.system('rm -rf ' + self.dest)
        self.refreshlist()

    def finished(self, result):
        self['info'].setText(_('Please select ...'))
        return

    def msgipkinst(self, answer=None):
        if answer is None:
            self.session.openWithCallback(self.msgipkinst, MessageBox, _('Restart Enigma to load the installed plugin?'), MessageBox.TYPE_YESNO)
        else:
            self.session.open(TryQuitMainloop, 3)


class NssRemove(Screen):
    def __init__(self, session):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = (name_plug)
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        self.list = []
        self.names = []
        self.container = eConsoleAppContainer()
        try:
            self.container.appClosed.append(self.runFinished)
        except:
            self.appClosed_conn = self.container.appClosed.connect(self.runFinished)

        self['list'] = nssList([])
        self['key_green'] = Button(_('Uninstall'))
        self['key_yellow'] = Button(_('Restart'))
        self['key_red'] = Button(_('Back'))
        self["key_blue"] = Button('Script')
        self['key_blue'].hide()
        self['key_green'].hide()
        self['title'] = Label(self.setup_title)
        self['pform'] = Label('')
        self['info'] = Label('Select')
        self['pth'] = Label('Remove not necessary addon')
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'green': self.message1,
                                                       'ok': self.message1,
                                                       'yellow': self.msgipkrst,
                                                       'blue': self.scriptrun,
                                                       'red': self.close,
                                                       'cancel': self.close}, -1)
        self.onLayoutFinish.append(self.getfreespace)

    def PluginDownloadBrowserClosed(self):
        self.openList()

    def runFinished(self, retval):
        self['pth'].setText(_('Addons Packege removed successfully.'))
        self.getfreespace()

    def scriptrun(self):
        self.session.open(ScriptExecuter)

    def cancel(self):
        if not self.container.running():
            del self.container.appClosed[:]
            del self.container
            self.close()
        else:
            self.container.kill()
            self['pth'].setText(_('Process Killed by user.Addon not removed completly!'))

    def openList(self):
        self.list = []
        # not refreshing list !!!
        del self.names[:]
        del self.list[:]
        for x in self.list:
            print('xxxx= ', x)
            del self.list[0:x]
        i = len(self.list)
        del self.list[0:i]
        o = len(self.names)
        del self.names[0:o]
        self.list = self.names
        # oh my head

        self["list"].l.setList(self.list)
        path = ('/var/lib/opkg/info')
        if os.path.exists('/var/lib/dpkg/info'):
            path = ('/var/lib/dpkg/info')
        try:
            for root, dirs, files in os.walk(path):
                if files is not None:
                    for name in files:
                        if name.endswith('.postinst') or name.endswith('.preinst') or name.endswith('.prerm') or name.endswith('.postrm'):
                            continue
                        if name.endswith('.md5sums') or name.endswith('.conffiles') or name.endswith('~'):
                            continue
                        if os.path.exists('/var/lib/dpkg/info'):
                            if name.endswith('.list'):
                                name = name.replace('.list', '')
                        else:
                            if name.endswith('.control'):
                                name = name.replace('.control', '')
                            if name.endswith('.list'):
                                continue
                        if name.startswith('enigma2-plugin-'):
                            self.names.append(str(name))
                self.names.sort(key=lambda x: x, reverse=False)
            if len(self.names) > -1:
                self['info'].setText(_('Please Remove ...'))
                self['key_green'].show()
            showlistNss(self.names, self['list'])
        except Exception as e:
            print(e)

    def message1(self):
        self.session.openWithCallback(self.message11, MessageBox, _('Do you want to remove?'), MessageBox.TYPE_YESNO)

    def message11(self, answer):
        if answer:
            idx = self['list'].getSelectionIndex()
            dom = self.names[idx]
            com = dom
            if os.path.exists('/var/lib/dpkg/info'):
                try:
                    cmd = 'echo "Sistem Update .... PLEASE WAIT ::.....";echo ":Remove %s";dpkg -P %s' % (com, com)
                    self.session.open(tvConsole, title='DEB Local Remove', cmdlist=[cmd], closeOnSuccess=False)
                except:
                    cmd = 'echo "Sistem Update .... PLEASE WAIT ::.....";echo ":Remove %s";apt-get purge %s' % (com, com)
                    self.session.open(tvConsole, title='DEB Local Remove', cmdlist=[cmd], closeOnSuccess=False)
            else:
                try:
                    self.session.open(tvConsole, _('Removing: %s') % dom, ['opkg remove %s' % com], closeOnSuccess=True)
                except:
                    self.session.open(tvConsole, _('Removing: %s') % dom, ['opkg remove --force-removal-of-dependent-packages %s' % com], closeOnSuccess=True)
            self.close()

    def getfreespace(self):
        try:
            fspace = Utils.freespace()
            self['pform'].setText(str(fspace))
            self.openList()
        except Exception as e:
            print(e)

    def msgipkrst(self, answer=None):
        if answer is None:
            self.session.openWithCallback(self.msgipkrst, MessageBox, _('Do you want restart enigma2 ?'), MessageBox.TYPE_YESNO)
        else:
            epgpath = '/media/hdd/epg.dat'
            epgbakpath = '/media/hdd/epg.dat.bak'
            if os.path.exists(epgbakpath):
                os.remove(epgbakpath)
            if os.path.exists(epgpath):
                shutil.copyfile(epgpath, epgbakpath)
            self.session.open(TryQuitMainloop, 3)


class ScriptExecuter(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)

        self.session = session
        skin = os.path.join(skin_path, 'scriptpanel.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setTitle(name_plug)

        self['labstatus'] = Label(_('NO SCRIPT FOUND'))
        self['key_red'] = Label(_('Exit'))
        self['key_green'] = Label(_('Execute'))
        self.mlist = []
        self.populateScript()
        self['list'] = List(self.mlist)
        self['list'].onSelectionChanged.append(self.schanged)
        self['actions'] = ActionMap(['WizardActions',
                                     'ColorActions'], {'ok': self.startScript,
                                                       'back': self.close,
                                                       'green': self.startScript,
                                                       'red': self.close})
        self.onLayoutFinish.append(self.script_sel)
        self.onShown.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setTitle(name_plug)

    def script_sel(self):
        self['list'].index = 1
        self['list'].index = 0

    def populateScript(self):
        try:
            if not os.path.exists('/usr/script'):
                mkdir('/usr/script', 493)
        except:
            pass

        myscripts = listdir('/usr/script')
        for fil in myscripts:
            if fil.find('.sh') != -1:
                fil2 = fil[:-3]
                desc = 'N/A'
                myfil = '/usr/script/' + str(fil)
                # os.system("sed -i -e 's/\r$//' %s" % myfil)
                # os.system("sed -i -e 's/^M$//' %s" % myfil)
                # lululla fixed encode crash on atv py3
                with codecs.open(myfil, "rb", encoding="latin-1") as f:
                    for line in f.readlines():
                        if line.find('#DESCRIPTION=') != -1:
                            line = line.strip()
                            desc = line[13:]
                f.close()
                res = (fil2, desc)
                self.mlist.append(res)

    def schanged(self):
        mysel = self['list'].getCurrent()
        if mysel:
            mytext = ' ' + mysel[1]
            self['labstatus'].setText(str(mytext))

    def startScript(self):
        if len(self.mlist) >= 0:
            mysel = self['list'].getCurrent()
            if mysel:
                mysel = mysel[0]
                mysel2 = '/usr/script/' + mysel + '.sh'
                chmod(mysel2, 0o0755)
                mytitle = 'NonSoloSat Script: ' + mysel
                self.session.open(tvConsole, title=mytitle, cmdlist=[mysel2])


class nssConfig(Screen, ConfigListScreen):
    def __init__(self, session):
        skin = os.path.join(skin_path, 'nssConfig.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.setup_title = _("NSS Addon Config")
        self.onChangedEntry = []
        self.session = session
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
        self.setTitle(self.setup_title)
        self['description'] = Label('')
        self['info'] = Label(_('Config Panel Addon'))
        # self['info'] = ScrollLabel('')
        self['key_yellow'] = Button(_('Update'))
        self['key_green'] = Button(_('Save'))
        self['key_red'] = Button(_('Back'))
        self["key_blue"] = Button()
        self['key_blue'].hide()
        self['key_yellow'].hide()
        self['title'] = Label(self.setup_title)
        self["setupActions"] = ActionMap(['OkCancelActions',
                                          'DirectionActions',
                                          'ColorActions',
                                          'VirtualKeyboardActions',
                                          'ActiveCodeActions'], {'cancel': self.extnok,
                                                                 'red': self.extnok,
                                                                 'back': self.close,
                                                                 'left': self.keyLeft,
                                                                 'right': self.keyRight,
                                                                 # 'yellow': self.tvUpdate,
                                                                 "showVirtualKeyboard": self.KeyText,
                                                                 'ok': self.Ok_edit,
                                                                 'green': self.msgok}, -1)
        self.createSetup()
        self.onLayoutFinish.append(self.layoutFinished)
        if self.setInfo not in self['config'].onSelectionChanged:
            self['config'].onSelectionChanged.append(self.setInfo)

    def arckget(self):
        zarcffll = ''
        try:
            zarcffll = os.popen('opkg print-architecture | grep -iE "arm|aarch64|mips|cortex|h4|sh_4"').read().strip('\n\r')
        except Exception as e:
            print("Error ", e)
        return str(zarcffll)

    def layoutFinished(self):
        try:
            arkFull = ''
            if self.arckget():
                arkFull = self.arckget()
                print('arkget= ', arkFull)
            img = os.popen('cat /etc/issue').read().strip('\n\r')
            arc = os.popen('uname -m').read().strip('\n\r')
            ifg = os.popen('wget -qO - ifconfig.me').read().strip('\n\r')
            img = img.replace('\\l', '')
            libs = os.popen('ls -l /usr/lib/libss*.*').read().strip('\n\r')
            if libs:
                libsssl = libs
            info = 'Current IP Wan: %s\nImage Mounted: %s Cpu: %s\nArchitecture information: %s\nLibssl(oscam):\n%s\n' % (ifg, img, arc, arkFull, libsssl)
            self['info'].setText(info)
        except Exception as e:
            print("Error ", e)
            self['info'].setText(_(':) by Lululla '))

    def createSetup(self):
        self.editListEntry = None
        self.list = []
        self.list.append(getConfigListEntry(_("Set the path to the Picons folder"), config.plugins.nssaddon.mmkpicon, _("Configure folder containing picons files")))
        # self.list.append(getConfigListEntry(_('Addon Installation Path'), config.plugins.nssaddon.ipkpth, _("Path to the addon installation folder")))
        self.list.append(getConfigListEntry(_('Link in Extensions Menu'), config.plugins.nssaddon.strtext, _("Link in Extensions button")))
        self.list.append(getConfigListEntry(_('Link in Main Menu'), config.plugins.nssaddon.strtmain, _("Link in Main Menu")))
        self["config"].list = self.list
        self["config"].l.setList(self.list)
        self.setInfo()

    def setInfo(self):
        try:
            sel = self['config'].getCurrent()[2]
            if sel:
                self['description'].setText(str(sel))
            else:
                self['description'].setText(_('SELECT YOUR CHOICE'))
            return
        except Exception as e:
            print("Error ", e)

    def changedEntry(self):
        for x in self.onChangedEntry:
            x()

    def getCurrentEntry(self):
        return self["config"].getCurrent()[0]

    def getCurrentValue(self):
        return str(self["config"].getCurrent()[1].getText())

    def createSummary(self):
        from Screens.Setup import SetupSummary
        return SetupSummary

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        print("current selection:", self["config"].l.getCurrentSelection())
        self.createSetup()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        print("current selection:", self["config"].l.getCurrentSelection())
        self.createSetup()

    def msgok(self):
        # if os.path.exists(config.plugins.nssaddon.ipkpth.value) is False:
            # self.session.open(MessageBox, _('Device not detected!'), MessageBox.TYPE_INFO, timeout=4)
        if self['config'].isChanged():
            for x in self["config"].list:
                x[1].save()
            self.session.open(MessageBox, _('Successfully saved configuration'), MessageBox.TYPE_INFO, timeout=4)
        else:
            self.close(True)

    def Ok_edit(self):
        # ConfigListScreen.keyOK(self)
        sel = self['config'].getCurrent()[1]
        if sel == config.plugins.nssaddon.mmkpicon:
            self.setting = 'mmkpicon'
            mmkpth = config.plugins.nssaddon.mmkpicon.value
            self.openDirectoryBrowser(mmkpth)
        # if sel == config.plugins.nssaddon.ipkpth:
            # self.setting = 'ipkpth'
            # ipkpth = config.plugins.nssaddon.ipkpth.value
            # self.openDirectoryBrowser(ipkpth)
        else:
            pass

    def openDirectoryBrowser(self, path):
        try:
            self.session.openWithCallback(
                self.openDirectoryBrowserCB,
                LocationBox,
                windowTitle=_("Choose Directory:"),
                text=_("Choose directory"),
                currDir=str(path),
                bookmarks=config.movielist.videodirs,
                autoAdd=False,
                editDir=True,
                inhibitDirs=["/bin", "/boot", "/dev", "/home", "/lib", "/proc", "/run", "/sbin", "/sys", "/var"],
                minFree=15)
        except Exception as e:
            print('error: ', str(e))

    def openDirectoryBrowserCB(self, path):
        if path is not None:
            if self.setting == 'mmkpicon':
                config.plugins.nssaddon.mmkpicon.setValue(path)
            # if self.setting == 'ipkpth':
                # config.plugins.nssaddon.ipkpth.setValue(path)
        return

    def KeyText(self):
        sel = self['config'].getCurrent()
        if sel:
            self.session.openWithCallback(self.VirtualKeyBoardCallback, VirtualKeyBoard, title=self['config'].getCurrent()[0], text=self['config'].getCurrent()[1].value)

    def VirtualKeyBoardCallback(self, callback=None):
        if callback is not None and len(callback):
            self['config'].getCurrent()[1].value = callback
            self['config'].invalidate(self['config'].getCurrent())
        return

    def cancelConfirm(self, result):
        if not result:
            return
        for x in self['config'].list:
            x[1].cancel()
        self.close()

    def extnok(self):
        if self['config'].isChanged():
            self.session.openWithCallback(self.cancelConfirm, MessageBox, _('Really close without saving the settings?'), MessageBox.TYPE_YESNO)
        else:
            self.close()


class SelectPiconz(Screen):
    def __init__(self, session):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('NSS Addon Picons')
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        self['list'] = nssList([])
        self['pth'] = Label('')
        self['pth'].setText(_('Folder picons ') + str(mmkpicon))
        self['pform'] = Label('')
        self['info'] = Label('')
        self['info'].setText(_('Loading data... Please wait'))
        self['key_green'] = Button(_('Select'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button(_('Remove'))
        self["key_blue"] = Button()
        # self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['title'] = Label(self.setup_title)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'green': self.okRun,
                                                       'red': self.close,
                                                       'cancel': self.close}, -2)
        self.onLayoutFinish.append(self.updateMenuList)

    def getfreespace(self):
        try:
            fspace = Utils.freespace()
            self['pform'].setText(str(fspace))
        except Exception as e:
            print(e)

    def closerm(self):
        self.close()

    def updateMenuList(self):
        self.menu_list = []
        for x in self.menu_list:
            del self.menu_list[0]
        list = []
        idx = 0
        for x in Panel_list3:
            list.append(nssListEntry(x, idx))
            self.menu_list.append(x)
            idx += 1
        self['key_green'].show()
        self['list'].setList(list)
        self['info'].setText(_('Please select'))
        self.getfreespace()

    def okRun(self):
        self.keyNumberGlobalCB(self['list'].getSelectedIndex())

    def keyNumberGlobalCB(self, idx):
        sel = self.menu_list[idx]
        if sel == ('MMARK PICONS BLACK'):
            self.session.open(MMarkFolderz, host_blk)
        elif sel == 'MMARK PICONS TRANSPARENT':
            self.session.open(MMarkFolderz, host_trs)
        elif sel == ('MMARK PICONS MOVIE'):
            self.session.open(MMarkPiconsf, 'MMark-Picons', host_mov, True)
        elif sel == ('OPEN PICONS'):  # https://openpicons.com/picons/full-motor-srp/hardlink/ # https://openpicons.com/picons/?dir=full-motor-srp/ipk
            # return
            host_open = 'https://openpicons.com/picons/?dir=full-motor-srp/hardlink'
            self.session.open(OpenPicons, 'OpenPicons', host_open)
        else:
            return

    def remove(self):
        self.session.openWithCallback(self.remove1, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def remove1(self, answer):
        if answer:
            self['info'].setText(_('Erase %s... please wait' % str(mmkpicon)))
            piconsx = glob.glob(str(mmkpicon) + '/*.png')
            for f in piconsx:
                try:
                    os.remove(f)
                except OSError as e:
                    print("Error: %s : %s" % (f, e.strerror))
        self.session.open(MessageBox, _('%s it has been cleaned' % str(mmkpicon)), MessageBox.TYPE_INFO, timeout=4)
        self['info'].setText(_('Please select ...'))


class MMarkFolderz(Screen):
    def __init__(self, session, url):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('NSS Addon Picons')
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        self.list = []
        self['list'] = nssList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pth'].setText(_('Folder picons ') + str(mmkpicon))
        self['pform'] = Label('')
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['key_green'] = Button(_('Select'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self["key_blue"] = Button()
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.url = url
        self.downloading = False
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/info'):
            self.timer_conn = self.timer.timeout.connect(self.downxmlpage)
        else:
            self.timer.callback.append(self.downxmlpage)
        self.timer.start(500, 1)
        self['title'] = Label(self.setup_title)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'green': self.okRun,
                                                       'red': self.close,
                                                       'cancel': self.close}, -2)
        self.onLayoutFinish.append(self.getfreespace)

    def getfreespace(self):
        try:
            fspace = Utils.freespace()
            self['pform'].setText(str(fspace))
        except Exception as e:
            print(e)

    def downxmlpage(self):
        url = six.ensure_binary(self.url)
        getPage(url).addCallback(self._gotPageLoad).addErrback(self.errorLoad)

    def errorLoad(self):
        self['info'].setText(_('Try again later ...'))
        self.downloading = False

    def _gotPageLoad(self, data):
        r = data
        if PY3:
            r = six.ensure_str(data)
        self.names = []
        self.urls = []
        try:
            n1 = r.find('"folderkey"', 0)
            n2 = r.find('more_chunks', n1)
            data2 = r[n1:n2]
            regex = '{"folderkey":"(.*?)".*?"name":"(.*?)".*?"created":"(.*?)"'
            match = re.compile(regex, re.DOTALL).findall(data2)
            for url, name, data in match:
                url = 'https://www.mediafire.com/api/1.5/folder/get_content.php?folder_key=' + url + '&content_type=files&chunk_size=1000&response_format=json'
                url = url.replace('\\', '')
                name = 'Picons-' + name
                self.urls.append(url)
                self.names.append(name)
            self['info'].setText(_('Please select ...'))
            self['key_green'].show()
            showlistNss(self.names, self['list'])
            self.downloading = True
        except:
            self.downloading = False

    def okRun(self):
        i = len(self.names)
        if i < 0:
            return
        idx = self['list'].getSelectionIndex()
        name = self.names[idx]
        url = self.urls[idx]
        self.session.open(MMarkPiconsf, name, url)

    def cancel(self, result=None):
        self.downloading = False
        self.close(None)
        return


class MMarkPiconsf(Screen):
    def __init__(self, session, name, url, movie=False):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('NSS Addon Picons')
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        self.list = []
        self['list'] = nssList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pth'].setText(_('Folder picons ') + str(mmkpicon))
        self['pform'] = Label('')
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['key_green'] = Button(_('Install'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self["key_blue"] = Button()
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.getfreespace()
        self.downloading = False
        self.movie = movie
        self.url = url
        self.name = name
        self.error_message = ""
        self.last_recvbytes = 0
        self.error_message = None
        self.download = None
        self.aborted = False
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/info'):
            self.timer_conn = self.timer.timeout.connect(self.downxmlpage)
        else:
            self.timer.callback.append(self.downxmlpage)
        self.timer.start(500, 1)
        self['title'] = Label(self.setup_title)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'green': self.okRun,
                                                       'red': self.close,
                                                       'cancel': self.close}, -2)
        self.onLayoutFinish.append(self.getfreespace)

    def getfreespace(self):
        try:
            fspace = Utils.freespace()
            self['pform'].setText(str(fspace))
        except Exception as e:
            print(e)

    def downxmlpage(self):
        url = six.ensure_binary(self.url)
        getPage(url).addCallback(self._gotPageLoad).addErrback(self.errorLoad)

    def errorLoad(self):
        self['info'].setText(_('Try again later ...'))
        self.downloading = False

    def _gotPageLoad(self, data):
        r = data
        if PY3:
            r = six.ensure_str(data)
        self.names = []
        self.urls = []
        try:
            n1 = r.find('"quickkey":', 0)
            n2 = r.find('more_chunks', n1)
            data2 = r[n1:n2]
            regex = 'filename":"(.*?)".*?"created":"(.*?)".*?"downloads":"(.*?)".*?"normal_download":"(.*?)"'
            match = re.compile(regex, re.DOTALL).findall(data2)
            for name, data, download, url in match:
                if '.zip' in url:
                    url = url.replace('\\', '')
                    if self.movie:
                        name = name.replace('_', ' ').replace('-', ' ').replace('mmk', '').replace('.zip', '')
                        name = name + ' ' + data[0:10] + ' ' + 'Down: ' + download
                    else:
                        name = name.replace('_', ' ').replace('mmk', 'MMark').replace('.zip', '')
                        name = name + ' ' + data[0:10] + ' ' + 'Down:' + download
                    self.urls.append(url)
                    self.names.append(name)
            self['info'].setText(_('Please select ...'))
            self['key_green'].show()
            showlistNss(self.names, self['list'])
            self.downloading = True
        except:
            self.downloading = False

    def okRun(self):
        self.session.openWithCallback(self.okRun1, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okRun1(self, result):
        self['info'].setText(_('... please wait'))
        if result:
            if self.downloading is True:
                idx = self["list"].getSelectionIndex()
                self.name = self.names[idx]
                url = self.urls[idx]
                dest = "/tmp/download.zip"
                print('url333: ', url)
                if os.path.exists(dest):
                    os.remove(dest)
                try:
                    myfile = Utils.ReadUrl(url)
                    print('response: ', myfile)
                    regexcat = 'href="https://download(.*?)"'
                    match = re.compile(regexcat, re.DOTALL).findall(myfile)
                    print("match =", match[0])
                    # myfile = checkMyFile(url)
                    # print('myfile222:  ', myfile)
                    url = 'https://download' + str(match[0])
                    print("url final =", url)
                    # myfile = checkMyFile(url)
                    # print('myfile222:  ', myfile)
                    # # url =  'https://download' + str(myfile)
                    self.download = downloadWithProgress(url, dest)
                    self.download.addProgress(self.downloadProgress)
                    self.download.start().addCallback(self.install).addErrback(self.download_failed)
                except Exception as e:
                    print('error: ', str(e))
                    print("Error: can't find file or read data")
            else:
                self['info'].setText(_('Picons Not Installed ...'))

    def downloadProgress(self, recvbytes, totalbytes):
        self['info'].setText(_('Download in progress...'))
        self["progress"].show()
        self['progress'].value = int(100 * self.last_recvbytes / float(totalbytes))
        self['progresstext'].text = '%d of %d kBytes (%.2f%%)' % (self.last_recvbytes / 1024, totalbytes / 1024, 100 * self.last_recvbytes / float(totalbytes))
        self.last_recvbytes = recvbytes

    def showError(self):
        print("download error ")
        self.downloading = False
        self.close()

    def download_failed(self, failure_instance=None, error_message=""):
        self.error_message = error_message
        if error_message == "" and failure_instance is not None:
            self.error_message = failure_instance.getErrorMessage()
        self.downloading = False
        info = 'Download Failed!!! ' + self.error_message
        self['info'].setText(info)
        self.session.open(MessageBox, _(info), MessageBox.TYPE_INFO, timeout=5)

    def abort(self):
        print("aborting", self.url)
        if self.download:
            self.download.stop()
        self.downloading = False
        self.aborted = True

    def download_finished(self, string=""):
        if self.aborted:
            self.finish(aborted=True)

    def install(self, string=''):
        if self.aborted:
            self.finish(aborted=True)
        else:
            self.progclear = 0
            self['info'].setText(_('File Downloaded ...'))
            if os.path.exists('/tmp/download.zip'):
                self['info'].setText(_('Install ...'))
                self.downloading = False
                self['progresstext'].text = ''
                self['progress'].setValue(self.progclear)
                self["progress"].hide()
                self['info'].setText(_('Please select ...'))
                myCmd = "unzip -o -q '/tmp/download.zip' -d %s/" % str(mmkpicon)
                subprocess.Popen(myCmd, shell=True, executable='/bin/bash')
                info = 'Successfully Picons Installed'
                self.session.open(MessageBox, _(info), MessageBox.TYPE_INFO, timeout=5)


class OpenPicons(Screen):
    def __init__(self, session, name, url):
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('OpenPicons')
        Screen.__init__(self, session)
        self.setTitle(self.setup_title)
        self.list = []
        self['list'] = nssList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label('')
        self['pth'].setText(_('Folder picons ') + str(mmkpicon))
        self['pform'] = Label('')
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['key_green'] = Button(_('Install'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self["key_blue"] = Button()
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()
        self.getfreespace()
        self.downloading = False
        self.url = url
        self.name = name
        self.error_message = ""
        self.last_recvbytes = 0
        self.error_message = None
        self.download = None
        self.aborted = False
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/info'):
            self.timer_conn = self.timer.timeout.connect(self.downxmlpage)
        else:
            self.timer.callback.append(self.downxmlpage)
        self.timer.start(500, 1)
        self['title'] = Label(self.setup_title)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'green': self.okRun,
                                                       'red': self.close,
                                                       'cancel': self.close}, -2)
        self.onLayoutFinish.append(self.getfreespace)

    def getfreespace(self):
        try:
            # from Components.PluginComponent import plugins
            # plugins.clearPluginList()
            # plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
            fspace = Utils.freespace()
            self['pform'].setText(str(fspace))
        except Exception as e:
            print(e)

    def downxmlpage(self):
        try:
            data = make_req(self.url)
            if PY3:
                data = six.ensure_str(data)
            self._gotPageLoad(data)
        except Exception as e:
            print('no link valid: ', e)
        # getPage(url).addCallback(self._gotPageLoad).addErrback(self.errorLoad)
        # https://openpicons.com/picons/?dir=full-motor-srp

    def errorLoad(self):
        self['info'].setText(_('Try again later ...'))
        self.downloading = False

    def _gotPageLoad(self, data):
        r = data
        if PY3:
            r = six.ensure_str(data)
        self.names = []
        self.urls = []
        try:
            regex = 'full-motor-srp/hardlink/(.*?).tar.xz"'
            match = re.compile(regex, re.DOTALL).findall(r)
            for url in match:
                # full-motor-srp/hardlink/srp-full.100x60-86x46.dark.on.blue_2023-12-12--23-58-23.hardlink.tar.xz"
                name = url.replace('.hardlink', '').replace('.', '-').replace('_', '-')
                url = 'https://openpicons.com/picons/full-motor-srp/hardlink/' + url + '.tar.xz'
                self.urls.append(url)
                self.names.append(Utils.str_encode(name))
            self['info'].setText(_('Please select ...'))
            self['key_green'].show()
            showlistNss(self.names, self['list'])
            self.downloading = True
        except:
            self.downloading = False

    def okRun(self):
        self.session.openWithCallback(self.okRun1, MessageBox, _("Do you want to install?\nATTENTION: MAKE SURE YOU HAVE ENOUGH SPACE\nTHERE ARE A LOT OF PICONS AND IT TAKES TIME!!!"), MessageBox.TYPE_YESNO)

    def okRun1(self, answer):
        if answer:
            if self.downloading is True:
                idx = self["list"].getSelectionIndex()
                self.name = self.names[idx]
                url = self.urls[idx]
                print('1 url type=', type(url))
                # url = six.ensure_binary(url)
                # print('2 url type=', type(url))
                # if PY3:
                    # url = url.encode()
                self.dest = "/tmp/download.tar.xz"
                if os.path.exists(self.dest):
                    os.remove(self.dest)
                self.download = downloadWithProgress(url, self.dest)
                self.download.addProgress(self.downloadProgress)
                self.download.start().addCallback(self.install).addErrback(self.download_failed)
            else:
                self['info'].setText(_('Picons Not Installed ...'))

    def downloadProgress(self, recvbytes, totalbytes):
        self['info'].setText(_('Download in progress...'))
        self["progress"].show()
        self['progress'].value = int(100 * self.last_recvbytes / float(totalbytes))
        self['progresstext'].text = '%d of %d kBytes (%.2f%%)' % (self.last_recvbytes / 1024, totalbytes / 1024, 100 * self.last_recvbytes / float(totalbytes))
        self.last_recvbytes = recvbytes

    def showError(self):
        print("download error ")
        self.downloading = False
        self.close()

    def download_failed(self, failure_instance=None, error_message=""):
        self.error_message = error_message
        if error_message == "" and failure_instance is not None:
            self.error_message = failure_instance.getErrorMessage()
        self.downloading = False
        info = 'Download Failed!!! ' + self.error_message
        self['info'].setText(info)
        self.session.open(MessageBox, _(info), MessageBox.TYPE_INFO, timeout=5)

    def abort(self):
        print("aborting", self.url)
        if self.download:
            self.download.stop()
        self.downloading = False
        self.aborted = True

    def download_finished(self, string=""):
        if self.aborted:
            self.finish(aborted=True)

    def install(self, string=''):
        if self.aborted:
            self.finish(aborted=True)
        else:
            self.progclear = 0
            self['info'].setText(_('File Downloaded ...'))
            if os.path.exists(self.dest):
                self.namel = ''
                self['info'].setText(_('Install ...'))
                self.downloading = False
                self['progresstext'].text = ''
                self['progress'].setValue(self.progclear)
                self["progress"].hide()
                self['info'].setText(_('Please select ...'))
                if os.path.exists("/tmp/unzipped"):
                    os.system('rm -rf /tmp/unzipped')
                os.makedirs('/tmp/unzipped')
                os.system('tar -xvf ' + self.dest + ' -C /tmp/unzipped')
                path = '/tmp/unzipped'
                for root, dirs, files in os.walk(path):
                    for name in dirs:
                        if not os.path.isdir(os.path.join(path, name)):
                            continue
                        self.namel = name
                # folder is long name.. truk for this
                path2 = '/tmp/unzipped/' + str(self.namel)
                for root, dirs, files in os.walk(path2):
                    for name in files:
                        Cmd = "cp -rf  '" + path2 + "/" + name + "' " + str(mmkpicon)
                        os.system(Cmd)
                info = 'Successfully Picons Installed'
                self.session.open(MessageBox, _(info), MessageBox.TYPE_INFO, timeout=5)


# def autostart(reason, session=None, **kwargs):
    # """called with reason=1 to during shutdown, with reason=0 at startup?"""
    # print("[Softcam] Started")
    # if reason == 0:
        # print('reason 0')
        # if session is not None:
            # print('session not none')
            # try:
                # print('ok started autostart')
                # if fileExists('/etc/init.d/dccamd'):
                    # os.system('mv /etc/init.d/dccamd /etc/init.d/dccamdOrig &')
                # if fileExists('/usr/bin/dccamd'):
                    # os.system("mv /usr/bin/dccamd /usr/bin/dccamdOrig &")
                # os.system("ln -sf /usr/bin /var/bin")
                # os.system("ln -sf /usr/keys /var/keys")
                # os.system("ln -sf /usr/scce /var/scce")
                # os.system("sleep 2")
                # os.system("/etc/startcam.sh")
                # print("*** running startcam ***")
            # except:
                # print('except autostart')
            # os.system('sleep 2')

        # else:
            # print('pass autostart')
    # return


def autostartsoftcam(reason, session=None, **kwargs):
    """called with reason=1 to during shutdown, with reason=0 at startup?"""
    print("[Softcam] Started")
    # global DreamCC_auto
    # global autoStartTimertvsman
    # global _firstStarttvsman
    if reason == 0:
        print('reason 0')
        if session is not None:
            try:
                # if fileExists('/etc/init.d/dccamd'):
                    # os.system('mv /etc/init.d/dccamd /etc/init.d/dccamdOrig &')
                # DreamCC_auto = DreamCCAuto()
                print('ok started autostart')
                if fileExists('/etc/init.d/dccamd'):
                    os.system('mv /etc/init.d/dccamd /etc/init.d/dccamdOrig &')
                if fileExists('/usr/bin/dccamd'):
                    os.system("mv /usr/bin/dccamd /usr/bin/dccamdOrig &")
                os.system("ln -sf /usr/bin /var/bin")
                os.system("ln -sf /usr/keys /var/keys")
                os.system("ln -sf /usr/scce /var/scce")
                os.system("sleep 2")
                self.cmd2 = 'chmod 755 /etc/startcam.sh &'
                os.system(self.cmd2)
                os.system("/etc/startcam.sh &")                
                print("*** running startcam ***")
            except:
                print('except autostart')
            os.system('sleep 2')

def main(session, **kwargs):
    try:
        session.open(HomeNss)
    except:
        pass


def cfgmain(menuid, **kwargs):
    if menuid == 'mainmenu':
        return [(_('Nss Addons'), main, 'Nss Addon', 4)]
    else:
        return []


def cfgcam(menuid, **kwargs):
    if menuid == 'cam':
        from Tools.BoundFunction import boundFunction
        return [(_(name_cam),
                 boundFunction(main2, showExtentionMenuOption=True),
                 'NSS Cam Manager',
                 -1)]
    else:
        return []


def main2(session, **kwargs):
    # from Plugins.Extensions.nssaddon.CamEx import NSSCamsManager
    # session.open(NSSCamsManager)
    from Plugins.Extensions.Manager.plugin import Manager
    # self.session.openWithCallback(self.close, Manager)   
    session.open(Manager)


def mainmenu(session, **kwargs):
    main(session, **kwargs)


def Plugins(**kwargs):
    extDescriptor = PluginDescriptor(name=name_plug, description=title_plug, where=PluginDescriptor.WHERE_EXTENSIONSMENU, icon=ico_path, fnc=main)
    mainDescriptor = PluginDescriptor(name=name_plug, description=title_plug, where=PluginDescriptor.WHERE_MENU, icon=ico_path, fnc=cfgmain)
    result = [PluginDescriptor(name=_(name_plug), description=_(title_plug), where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], needsRestart=True, fnc=autostartsoftcam),
              # PluginDescriptor(name=name_plug, description=title_plug, where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart),
              PluginDescriptor(name=name_cam, description="Start Your Cam", where=[PluginDescriptor.WHERE_MENU], fnc=cfgcam),
              PluginDescriptor(name=name_plug, description=title_plug, where=PluginDescriptor.WHERE_PLUGINMENU, icon=ico_path, fnc=main)]
    if config.plugins.nssaddon.strtext.value:
        result.append(extDescriptor)
    if config.plugins.nssaddon.strtmain.value:
        result.append(mainDescriptor)
    return result


def terrestrial():
    SavingProcessTerrestrialChannels = StartSavingTerrestrialChannels()
    import time
    now = time.time()
    ttime = time.localtime(now)
    tt = str('{0:02d}'.format(ttime[2])) + str('{0:02d}'.format(ttime[1])) + str(ttime[0])[2:] + '_' + str('{0:02d}'.format(ttime[3])) + str('{0:02d}'.format(ttime[4])) + str('{0:02d}'.format(ttime[5]))
    os.system('tar -czvf /tmp/' + tt + '_enigma2settingsbackup.tar.gz' + ' -C / /etc/enigma2/*.tv /etc/enigma2/*.radio /etc/enigma2/lamedb')
    if SavingProcessTerrestrialChannels:
        print('SavingProcessTerrestrialChannels')
    return


def terrestrial_rest():
    if LamedbRestore():
        TransferBouquetTerrestrialFinal()
        # terrr = os.path.join(plugin_path, 'temp/TerrestrialChannelListArchive')
        terrr = plugin_path + '/temp/TerrestrialChannelListArchive'
        if os.path.exists(terrr):
            os.system("cp -rf " + plugin_path + "/temp/TerrestrialChannelListArchive /etc/enigma2/userbouquet.terrestrial.tv")
        os.system('cp -rf /etc/enigma2/bouquets.tv /etc/enigma2/backup_bouquets.tv')
        with open('/etc/enigma2/bouquets.tv', 'r+') as f:
            bouquetTvString = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.terrestrial.tv" ORDER BY bouquet\n'
            if bouquetTvString not in f:
                new_bouquet = open('/etc/enigma2/new_bouquets.tv', 'w')
                new_bouquet.write('#NAME User - bouquets (TV)\n')
                new_bouquet.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.terrestrial.tv" ORDER BY bouquet\n')
                file_read = open('/etc/enigma2/bouquets.tv').readlines()
                for line in file_read:
                    if line.startswith("#NAME"):
                        continue
                    new_bouquet.write(line)
                new_bouquet.close()
                os.system('cp -rf /etc/enigma2/bouquets.tv /etc/enigma2/backup_bouquets.tv')
                os.system('mv -f /etc/enigma2/new_bouquets.tv /etc/enigma2/bouquets.tv')
        if os.path.exists('/etc/enigma2/lcndb'):
            lcnstart()


def lcnstart():
    print(' lcnstart ')
    if os.path.exists('/etc/enigma2/lcndb'):
        lcn = LCN()
        lcn.read()
        if len(lcn.lcnlist) > 0:
            lcn.writeBouquet()
            ReloadBouquets()
    return


def StartSavingTerrestrialChannels():

    def ForceSearchBouquetTerrestrial():
        for file in sorted(glob.glob("/etc/enigma2/*.tv")):
            f = open(file, "r").read()
            x = f.strip().lower()
            if x.find('eeee') != -1:
                return file
                break
            # if x.find('eeee0000') != -1:
                # if x.find('82000') == -1 or x.find('c0000') == -1:
                    # return file
                    # break
        return

    def ResearchBouquetTerrestrial(search):
        for file in sorted(glob.glob("/etc/enigma2/*.tv")):
            f = open(file, "r").read()
            x = f.strip().lower()
            x1 = f.strip()
            if x1.find("#NAME") != -1:
                if x.lower().find(search.lower()) != -1:
                    if x.find('eeee') != -1:
                        return file
                        break
        return

    def SaveTrasponderService():
        TrasponderListOldLamedb = open(TransOldLamedb, 'w')
        ServiceListOldLamedb = open(ServOldLamedb, 'w')
        Trasponder = False
        inTransponder = False
        inService = False
        try:
            LamedbFile = open(ee2ldb, 'r')
            while 1:
                line = LamedbFile.readline()
                if not line:
                    break
                if not (inTransponder or inService):
                    if line.find('transponders') == 0:
                        inTransponder = True
                    if line.find('services') == 0:
                        inService = True
                if line.find('end') == 0:
                    inTransponder = False
                    inService = False
                line = line.lower()
                if line.find('eeee') != -1:
                    Trasponder = True
                    if inTransponder:
                        TrasponderListOldLamedb.write(line)
                        line = LamedbFile.readline()
                        TrasponderListOldLamedb.write(line)
                        line = LamedbFile.readline()
                        TrasponderListOldLamedb.write(line)
                    if inService:
                        tmp = line.split(':')
                        ServiceListOldLamedb.write(tmp[0] + ":" + tmp[1] + ":" + tmp[2] + ":" + tmp[3] + ":" + tmp[4] + ":0\n")
                        line = LamedbFile.readline()
                        ServiceListOldLamedb.write(line)
                        line = LamedbFile.readline()
                        ServiceListOldLamedb.write(line)
            TrasponderListOldLamedb.close()
            ServiceListOldLamedb.close()
            if not Trasponder:
                os.system('rm -fr ' + TransOldLamedb)
                os.system('rm -fr ' + ServOldLamedb)
        except:
            pass
        return Trasponder

    def CreateBouquetForce():
        WritingBouquetTemporary = open(TerChArch, 'w')
        WritingBouquetTemporary.write('#NAME terrestre\n')
        ReadingTempServicelist = open(ServOldLamedb, 'r').readlines()
        for jx in ReadingTempServicelist:
            if jx.find('eeee') != -1:
                String = jx.split(':')
                WritingBouquetTemporary.write('#SERVICE 1:0:%s:%s:%s:%s:%s:0:0:0:\n' % (hex(int(String[4]))[2:], String[0], String[2], String[3], String[1]))
        WritingBouquetTemporary.close()

    def SaveBouquetTerrestrial():
        NameDirectory = ResearchBouquetTerrestrial('terr')
        if not NameDirectory:
            NameDirectory = ForceSearchBouquetTerrestrial()
        try:
            shutil.copyfile(NameDirectory, TerChArch)
            return True
        except:
            pass
        return
    Service = SaveTrasponderService()
    if Service:
        if not SaveBouquetTerrestrial():
            CreateBouquetForce()
        return True
    return


def LamedbRestore():
    try:
        TrasponderListNewLamedb = open(plugin_path + '/temp/TrasponderListNewLamedb', 'w')
        ServiceListNewLamedb = open(plugin_path + '/temp/ServiceListNewLamedb', 'w')
        inTransponder = False
        inService = False
        infile = open(ee2ldb, 'r')
        while 1:
            line = infile.readline()
            if not line:
                break
            if not (inTransponder or inService):
                if line.find('transponders') == 0:
                    inTransponder = True
                if line.find('services') == 0:
                    inService = True
            if line.find('end') == 0:
                inTransponder = False
                inService = False
            if inTransponder:
                TrasponderListNewLamedb.write(line)
            if inService:
                ServiceListNewLamedb.write(line)
        TrasponderListNewLamedb.close()
        ServiceListNewLamedb.close()
        WritingLamedbFinal = open(ee2ldb, "w")
        WritingLamedbFinal.write("eDVB services /4/\n")
        TrasponderListNewLamedb = open(plugin_path + '/temp/TrasponderListNewLamedb', 'r').readlines()
        for x in TrasponderListNewLamedb:
            WritingLamedbFinal.write(x)
        try:
            TrasponderListOldLamedb = open(TransOldLamedb, 'r').readlines()
            for x in TrasponderListOldLamedb:
                WritingLamedbFinal.write(x)
        except:
            pass
        WritingLamedbFinal.write("end\n")
        ServiceListNewLamedb = open(plugin_path + '/temp/ServiceListNewLamedb', 'r').readlines()
        for x in ServiceListNewLamedb:
            WritingLamedbFinal.write(x)
        try:
            ServiceListOldLamedb = open(ServOldLamedb, 'r').readlines()
            for x in ServiceListOldLamedb:
                WritingLamedbFinal.write(x)
        except:
            pass
        WritingLamedbFinal.write("end\n")
        WritingLamedbFinal.close()
        return True
    except:
        return False


def TransferBouquetTerrestrialFinal():

    def RestoreTerrestrial():
        for file in os.listdir("/etc/enigma2/"):
            if re.search('^userbouquet.*.tv', file):
                f = open("/etc/enigma2/" + file, "r")
                x = f.read()
                if re.search('#NAME Digitale Terrestre', x, flags=re.IGNORECASE) or re.search('#NAME DTT', x, flags=re.IGNORECASE):  # for disa51
                    return "/etc/enigma2/" + file
        return

    try:
        TerrestrialChannelListArchive = open(TerChArch, 'r').readlines()
        DirectoryUserBouquetTerrestrial = RestoreTerrestrial()
        if DirectoryUserBouquetTerrestrial:
            TrasfBouq = open(DirectoryUserBouquetTerrestrial, 'w')
            for Line in TerrestrialChannelListArchive:
                if Line.lower().find('#name') != -1:
                    TrasfBouq.write('#NAME Digitale Terrestre\n')
                else:
                    TrasfBouq.write(Line)
            TrasfBouq.close()
            return True
    except:
        return False
    return
