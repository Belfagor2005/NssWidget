#!/usr/bin/env python
# -*- coding: utf-8 -*-

# --------------------#
#   coded by Lululla  #
#      11/08/2024     #
# --------------------#
# imported from tvAddon Panel
from __future__ import print_function
from . import (
    _,
    epk,
    Host,
    wgetsts,
    pblk,
    ptrs,
    ptmov,
    data_xml,
)
from .Console import Console as tvConsole
from .lib import Utils
from .lib.Utils import RequestAgent
from .lib.Downloader import downloadWithProgress
from .lib.Lcn import (
    LCN,
    LCNBuildHelper,
    terrestrial,
    terrestrial_rest,
    ReloadBouquets,
    keepiptv,
    copy_files_to_enigma2,
)
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.ConfigList import ConfigListScreen
from Components.config import (
    config,
    getConfigListEntry,
    ConfigYesNo,
    configfile,
    ConfigSubsection,
)
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import (MultiContentEntryText, MultiContentEntryPixmapAlphaTest)
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
# from Components.ScrollLabel import ScrollLabel
from Components.Sources.Progress import Progress
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
# from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import (SCOPE_PLUGINS, fileExists, resolveFilename)
from enigma import (
    RT_HALIGN_LEFT,
    RT_VALIGN_CENTER,
    loadPNG,
    gFont,
    eTimer,
    getDesktop,
    eListboxPythonMultiContent,
    eConsoleAppContainer,
)
from os import chmod, listdir, mkdir
from twisted.web.client import (downloadPage, getPage)
import codecs
import glob
import os
import re
import shutil
import six
import ssl
import subprocess
import sys
from xml.dom import minidom

global skin_path, sets, category
# mmkpicon = config.usage.picon_dir.value()
PY3 = sys.version_info.major >= 3
if PY3:
    from urllib.error import URLError
    from urllib.request import (urlopen, Request)
    from urllib.parse import urlparse
    unicode = str
    unichr = chr
    long = int
    PY3 = True
else:
    from urllib2 import (urlopen, Request, URLError)
    from urlparse import urlparse


if sys.version_info >= (2, 7, 9):
    try:
        sslContext = ssl._create_unverified_context()
    except:
        sslContext = None


try:
    wgetsts()
except:
    pass


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
            link = requests.get(url, headers={'User-Agent': RequestAgent()}, timeout=10, verify=False, stream=True).text
            # return link
    except ImportError:
        req = Request(url)
        req.add_header('User-Agent', 'E2 Plugin nss Panel')
        response = urlopen(req, None, 10)
        link = response.read().decode('utf-8')
        response.close()
        # return link
    return link


def check_gzip(url):
    from io import StringIO
    import gzip
    hdr = {"User-Agent": RequestAgent()}
    response = None
    request = Request(url, headers=hdr)
    try:
        response = urlopen(request, timeout=10)
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


AgentRequest = RequestAgent()
# ================config
global sets
config.plugins.nssaddon = ConfigSubsection()
config.plugins.nssaddon.strtext = ConfigYesNo(default=True)
config.plugins.nssaddon.strtmain = ConfigYesNo(default=False)
# config.plugins.nssaddon.mmkpicon = ConfigDirectory(default='/picon/')
# config.plugins.nssaddon.ipkpth = ConfigSelection(default="/tmp", choices=mountipkpth())
mmkpicon = config.usage.picon_dir.value.strip()
currversion = '1.0.0'
title_plug = 'NSS Addon V. %s' % currversion
name_plug = 'NSS Addon'
name_cam = 'NSS Cam Manager'
category = 'lululla.xml'
sets = 0
regexC = '<plugins cont="(.*?)"'
regexL = 'href="(.+?)">.+?alt=.+?">(.+?)</a>.+?data.+?">(.+?)</td>'
host_trs = Utils.b64decoder(ptrs)
host_blk = Utils.b64decoder(pblk)
host_mov = Utils.b64decoder(ptmov)
xml_path = Utils.b64decoder(data_xml)
plugin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('nssaddon'))
ico_path = os.path.join(plugin_path, 'logo.png')
no_cover = os.path.join(plugin_path, 'no_coverArt.png')
ee2ldb = '/etc/enigma2/lamedb'

plugin_temp = os.path.join(plugin_path, 'temp')
if not os.path.exists(plugin_temp):
    try:
        os.makedirs(plugin_temp)
    except OSError as e:
        print(('Error creating directory %s:\n%s') % (plugin_temp, str(e)))


ServiceListNewLamedb = plugin_path + '/temp/ServiceListNewLamedb'
TrasponderListNewLamedb = plugin_path + '/temp/TrasponderListNewLamedb'
ServOldLamedb = plugin_path + '/temp/ServiceListOldLamedb'
TransOldLamedb = plugin_path + '/temp/TrasponderListOldLamedb'
TerChArch = plugin_path + '/temp/TerrestrialChannelListArchive'


screenwidth = getDesktop(0).size()
if screenwidth.width() == 2560:
    skin_path = plugin_path + '/res/skins/uhd/'
elif screenwidth.width() == 1920:
    skin_path = plugin_path + '/res/skins/fhd/'
else:
    skin_path = plugin_path + '/res/skins/hd/'

os.system('rm -fr ' + plugin_path + '/temp/*')
if mmkpicon.endswith('/'):
    mmkpicon = mmkpicon[:-1]
if not os.path.exists(mmkpicon):
    try:
        os.makedirs(mmkpicon)
    except OSError as e:
        print(('Error creating directory %s:\n%s') % (mmkpicon, str(e)))

Panel_list2 = [
    ('SAVE DTT BOUQUET'),
    ('RESTORE DTT BOUQUET'),
    ('UPDATE SATELLITES.XML'),
    ('UPDATE TERRESTRIAL.XML'),
    ('SETTINGS CIEFP'),
    ('SETTINGS MANUTEK'),
    ('SETTINGS MORPHEUS'),
    ('SETTINGS VHANNIBAL'),
    ('SETTINGS VHANNIBAL 2')]

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
            textfont = int(34)
            self.l.setFont(0, gFont('Regular', textfont))
        else:
            self.l.setItemHeight(40)
            textfont = int(22)
            self.l.setFont(0, gFont('Regular', textfont))


pngs = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/settingoff.png".format('nssaddon'))  # ico1_path
if status_site():
    pngs = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/settingon.png".format('nssaddon'))  # ico1_path


def nssListEntry(name, idx):
    res = [name]
    if screenwidth.width() == 2560:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 10), size=(40, 40), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(80, 0), size=(1200, 50), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    elif screenwidth.width() == 1920:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(40, 40), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(70, 0), size=(1000, 50), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(3, 0), size=(40, 40), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(50, 0), size=(500, 40), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res


def showlistNss(data, list):
    icount = 0
    plist = []
    for line in data:
        name = data[icount]
        plist.append(nssListEntry(name, icount))
        icount += 1
        list.setList(plist)


class HomeNss(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'HomeNss.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = (name_plug)
        # self['list'] = nssList([])

        self['list'] = MenuList([])
        self.epk = epk
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
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/info'):
            self.timer_conn = self.timer.timeout.connect(self.downloadxmlpage)
        else:
            self.timer.callback.append(self.downloadxmlpage)
        self.timer.start(500, 1)
        self.onFirstExecBegin.append(self.check_dependencies)
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        if status_site():
            self['statusgreen'].show()
            self['statusred'].hide()
            self['status'].setText('SERVER ON')
        else:
            self['statusgreen'].hide()
            self['statusred'].show()
            self['status'].setText('SERVER OFF')
        self.setTitle(name_plug)
        self['info'].setText(_('Please select ...'))

    def downloadxmlpage(self):
        url = epk
        if PY3:
            url = url.encode()
        getPage(url).addCallback(self._gotPageLoad).addErrback(self.errorLoad)

    def errorLoad(self, error):
        print('are here error:', str(error))
        self['info'].setText(_('Addons Download Failure\nNo internet connection or server down !'))
        # self.downloading = False

    def _gotPageLoad(self, data):
        self.xml = data
        # print('self.xml=', self.xml)
        self.list = []
        self.names = []
        try:
            if self.xml:
                # self.names.append('Setting Channel Nss')
                self.names.append('Daily Settings')
                self.names.append('Daily Picons')
                # self.names.append('Plugin Script')
                self.xmlparse = minidom.parseString(self.xml)
                for plugins in self.xmlparse.getElementsByTagName('plugins'):
                    if config.ParentalControl.configured.value:
                        if 'adult' in str(plugins.getAttribute('cont')).lower():
                            continue
                    if not os.path.exists('/var/lib/dpkg/info'):
                        if 'dreamos' in str(plugins.getAttribute('cont')).lower():
                            continue

                    if os.path.exists('/var/lib/dpkg/info'):
                        if 'dreamos' not in str(plugins.getAttribute('cont')).lower():
                            continue
                    self.names.append(str(plugins.getAttribute('cont')))
                self['info'].setText('Select')
                self["list"].l.setList(self.names)
                # showlistNss(self.names, self['list'])
        except:
            self['info'].setText(_('Error processing server addons data'))

    def okRun(self):
        global category
        selection = str(self['list'].getCurrent())
        if 'Daily Settings' in selection:
            self.session.open(NssDailySetting)

        elif 'Daily Picons' in selection:
            self.session.open(SelectPiconz)

        # elif 'Plugin Script' in selection:
            # category = 'PlugiScript.xml'
            # xml1 = str(xml_path) + category
            # xm = check_gzip(xml1)
            # print('xml:', xm)
            # self.xmlparse = minidom.parseString(xm)
            # self.session.open(AddonPackagesGroups, self.xmlparse, selection)

        # elif 'Setting Channel Nss' in selection:
            # category = 'Settingchannelnss.xml'
            # xml1 = str(xml_path) + category
            # xm = check_gzip(xml1)
            # print('xml:', xm)
            # self.xmlparse = minidom.parseString(xm)
            # self.session.open(AddonPackagesGroups, self.xmlparse, selection)

        else:
            self.session.open(AddonPackagesGroups, self.xmlparse, selection)

    def check_dependencies(self):
        dependencies = True
        try:
            import requests
        except ImportError:
            dependencies = False
        if dependencies is False:
            chmod("/usr/lib/enigma2/python/Plugins/Extensions/nssaddon/dependencies.sh", 0o0755)
            cmd1 = "/usr/lib/enigma2/python/Plugins/Extensions/nssaddon/dependencies.sh"
            self.session.openWithCallback(self.starts, tvConsole, title="Checking Python Dependencies", cmdlist=[cmd1], closeOnSuccess=False)
        else:
            self.starts()

    def starts(self, res=None):
        Utils.OnclearMem()

    def closerm(self):
        ReloadBouquets(0)
        Utils.deletetmp()
        self.close()

    def goConfig(self):
        self.session.open(nssConfig)

    def ipkDs(self):
        self.session.open(NssRemove)

    def NSSCamsManager(self):
        tvman = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('nssaddon'))
        if os.path.exists(tvman):
            from Plugins.Extensions.Manager.plugin import Manager
            self.session.openWithCallback(self.passe, Manager)
        else:
            self.session.open(MessageBox, ("NSSCamsManager Not Installed!!\nInstall First"), type=MessageBox.TYPE_INFO, timeout=3)

    def passe(self, ret=None):
        self.close()

    def NssIPK(self):
        self.session.open(NssIPK)


class AddonPackagesGroups(Screen):

    def __init__(self, session, xmlparse, selection):
        Screen.__init__(self, session)
        skin = os.path.join(skin_path, 'HomeNss.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

        self.xmlparse = xmlparse
        self.selection = selection
        self['info'] = Label(_('Welcome , Please Wait..'))

        self['key_green'] = Button()
        self['key_red'] = Button()
        self['key_yellow'] = Button()
        self["key_blue"] = Button()
        self['key_green'].hide()
        self['key_red'].hide()
        self['key_yellow'].hide()
        self["key_blue"].hide()
        self['statusgreen'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'] = Pixmap()
        self['statusred'].hide()
        self['status'] = Label('Please wait..')
        self['title'] = Label(name_plug)

        self.list = []
        adlist = []
        for plugins in self.xmlparse.getElementsByTagName('plugins'):
            if str(plugins.getAttribute('cont')) == self.selection:
                for plugin in plugins.getElementsByTagName('plugin'):
                    adlist.append(str(plugin.getAttribute('name')))
                continue

        adlist.sort()

        self['list'] = MenuList(adlist)

        self['actions'] = ActionMap(['OkCancelActions'], {'cancel': self.close,
                                                          'ok': self.msginstal,
                                                          }, -2)
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        if status_site():
            self['statusgreen'].show()
            self['statusred'].hide()
            self['status'].setText('SERVER ON')
        else:
            self['statusgreen'].hide()
            self['statusred'].show()
            self['status'].setText('SERVER OFF')
        self.setTitle(name_plug)
        self['info'].setText(_('Please select ...'))

    def msginstal(self):
        self.session.openWithCallback(self.selclicked, MessageBox, _('Do you install this plugin ?'), MessageBox.TYPE_YESNO)

    def selclicked(self, result):
        if result:
            try:
                selection_country = self['list'].getCurrent()
                for plugins in self.xmlparse.getElementsByTagName('plugins'):
                    if str(plugins.getAttribute('cont')) == self.selection:
                        for plugin in plugins.getElementsByTagName('plugin'):
                            if str(plugin.getAttribute('name')) == selection_country:
                                self.com = str(plugin.getElementsByTagName('url')[0].childNodes[0].data)
                                self.dom = str(plugin.getAttribute('name'))
                                # test lululla
                                self.com = self.com.replace('"', '')
                                if ".deb" in self.com:
                                    if not os.path.exists('/var/lib/dpkg/info'):
                                        self.session.open(MessageBox,
                                                          _('Unknow Image!'),
                                                          MessageBox.TYPE_INFO,
                                                          timeout=5)
                                        return
                                    n2 = self.com.find("_", 0)
                                    self.dom = self.com[:n2]

                                if ".ipk" in self.com:
                                    if os.path.exists('/var/lib/dpkg/info'):
                                        self.session.open(MessageBox,
                                                          _('Unknow Image!'),
                                                          MessageBox.TYPE_INFO,
                                                          timeout=5)
                                        return
                                    n2 = self.com.find("_", 0)
                                    self.dom = self.com[:n2]
                                elif ".zip" in self.com:
                                    self.dom = self.com
                                elif ".tar" in self.com or ".gz" in self.com or "bz2" in self.com:
                                    self.dom = self.com
                                print('self.prombt self.com: ', self.com)
                                self.prombt()
                            else:
                                print('Return from prompt ')
                                self['info'].setText('Select')
                            continue
            except Exception as e:
                print('error prompt ', e)
                self['info'].setText('Error')
                return

    def prombt(self):
        self.plug = self.com.split("/")[-1]
        self.folddest = '/tmp/' + self.plug
        if ".deb" in self.plug:
            cmd2 = "dpkg -i '/tmp/" + self.plug + "'"
        if ".ipk" in self.plug:
            cmd2 = "opkg install --force-reinstall --force-overwrite '/tmp/" + self.plug + "'"
        elif ".zip" in self.plug:
            cmd2 = "unzip -o -q '/tmp/" + self.plug + "' -d /"
        elif ".tar" in self.plug and "gz" in self.plug:
            cmd2 = "tar -xvf '/tmp/" + self.plug + "' -C /"
        elif ".bz2" in self.plug and "gz" in self.plug:
            cmd2 = "tar -xjvf '/tmp/" + self.plug + "' -C /"
        cmd3 = "rm '/tmp/" + self.plug + "'"
        cmd = cmd2 + " && " + cmd3
        cmd00 = "wget --no-check-certificate -U '%s' -c '%s' -O '%s';%s > /dev/null" % (AgentRequest, str(self.com), self.folddest, cmd)
        title = (_("Installing %s\nPlease Wait...") % self.dom)
        self.session.open(tvConsole, _(title), [cmd00], closeOnSuccess=False)


class NssDailySetting(Screen):
    def __init__(self, session):

        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'HomeNss.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('DAILY SETTINGS')
        self.setTitle(name_plug)

        self['list'] = nssList([])
        # self['list'] = MenuList([])

        self['title'] = Label(self.setup_title)
        self['statusgreen'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'] = Pixmap()
        self['statusred'].hide()
        self['status'] = Label('Please wait..')

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
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        if status_site():
            self['statusgreen'].show()
            self['statusred'].hide()
            self['status'].setText('SERVER ON')
        else:
            self['statusgreen'].hide()
            self['statusred'].show()
            self['status'].setText('SERVER OFF')
        self.setTitle(name_plug)
        self['info'].setText(_('Please select ...'))

    def Lcn(self):
        '''
        sets = 0
        # if self.LcnOn:
            # lcn = LCN()
            # lcn.read()
            # if len(lcn.lcnlist) >= 1:
                # lcn.writeBouquet()
                # ReloadBouquets(sets)
                # self.session.open(MessageBox, _('Sorting Terrestrial channels with Lcn rules Completed'),
                                  # MessageBox.TYPE_INFO,
                                  # timeout=5)
        '''

        try:
            lcn = LCNBuildHelper()
            lcn.buildAfterScan()
            self.session.open(MessageBox, _('Sorting Terrestrial Executed!'),
                              MessageBox.TYPE_INFO,
                              timeout=5)
        except Exception as e:
            print(e)
            self.session.open(MessageBox, _('Sorting Terrestrial not Executed!'),
                              MessageBox.TYPE_INFO,
                              timeout=5)

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

    def okRun(self):
        self.keyNumberGlobalCB(self['list'].getSelectedIndex())

    def keyNumberGlobalCB(self, idx):
        sel = self.menu_list[idx]
        if sel == ('SAVE DTT BOUQUET'):
            self.terrestrialsave()
        elif sel == ('RESTORE DTT BOUQUET'):
            self.terrestrial_restore()
        elif sel == ('SETTINGS CIEFP'):
            self.session.open(SettingCiefpz)
        elif sel == ('SETTINGS MANUTEK'):
            self.session.open(SettingManutekz)
        elif sel == ('SETTINGS MORPHEUS'):
            self.session.open(SettingMorpheusz)
        elif sel == ('SETTINGS VHANNIBAL'):
            self.session.open(SettingVhan11)
        elif sel == ('SETTINGS VHANNIBAL 2'):
            self.session.open(SettingVhan22)
        elif sel == _('UPDATE SATELLITES.XML'):
            self.okSATELLITE()
        elif sel == _('UPDATE TERRESTRIAL.XML'):
            self.okTERRESTRIAL()
        else:
            return

    def terrestrial_restore(self):
        self.session.openWithCallback(self.terrestrial_restore2, MessageBox, _("This operation restore your Favorite channel Dtt\nfrom =>>THISPLUGIN/temp/TerrestrialChannelListArchive\nDo you really want to continue?"), MessageBox.TYPE_YESNO)

    def terrestrial_restore2(self, answer=False):
        if answer:
            terrestrial_rest()

    def terrestrialsave(self):
        self.session.openWithCallback(self.terrestrialsave2, MessageBox, _("This operation save your Favorite channel Dtt\nto =>>/tmp/*_enigma2settingsbackup.tar.gz\nDo you really want to continue?"), MessageBox.TYPE_YESNO)

    def terrestrialsave2(self, answer=False):
        if answer:
            terrestrial()

    def okSATELLITE(self):
        self.session.openWithCallback(self.okSATELLITE2, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okSATELLITE2(self, answer=False):
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

    def okTERRESTRIAL2(self, answer=False):
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


class SettingCiefpz(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'HomeNss.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('Setting Ciefp')
        self.setTitle(name_plug)
        self.list = []
        self['list'] = nssList([])
        # self['list'] = MenuList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['statusgreen'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'] = Pixmap()
        self['statusred'].hide()
        self['status'] = Label('Please wait..')
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
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        if status_site():
            self['statusgreen'].show()
            self['statusred'].hide()
            self['status'].setText('SERVER ON')
        else:
            self['statusgreen'].hide()
            self['statusred'].show()
            self['status'].setText('SERVER OFF')
        self.setTitle(name_plug)
        self['info'].setText(_('Please select ...'))

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
                if name in self.names:
                    continue
                if url.find('.zip') != -1:
                    url = url.replace('blob', 'raw')
                    url = 'https://github.com' + url
                    self.urls.append(Utils.str_encode(url.strip()))
                    self.names.append(Utils.str_encode(name.strip()))
                    self.downloading = True
            self['key_green'].show()

            showlistNss(self.names, self['list'])
            # self['list'].setList(self.names)

        except Exception as e:
            print('downxmlpage get failed: ', str(e))
            self['info'].setText(_('Download page get failed ...'))

    def okRun(self):
        self.session.openWithCallback(self.okRun1, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okRun1(self, answer=False):
        if answer:
            global sets
            sets = 0
            if self.downloading is True:
                idx = self["list"].getSelectionIndex()
                url = self.urls[idx]
                dest = "/tmp/settings.zip"
                self.namel = ''
                if 'dtt' not in url.lower():
                    sets = 1
                    terrestrial()
                if keepiptv():
                    print('-----save iptv channels-----')

                from six.moves.urllib.request import urlretrieve
                urlretrieve(url, dest)

                if os.path.exists(dest) and '.zip' in dest:
                    fdest1 = "/tmp/unzipped"
                    fdest2 = "/etc/enigma2"
                    if os.path.exists("/tmp/unzipped"):
                        os.system('rm -rf /tmp/unzipped')
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
                    self.session.openWithCallback(self.yes, tvConsole, title=_(title), cmdlist=["wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /tmp/inst.txt 2>&1 &"], closeOnSuccess=False)
                    self['info'].setText(_('Settings Installed ...'))
                else:
                    self['info'].setText(_('Settings Not Installed (dest)...'))
            else:
                self['info'].setText(_('Settings Not Installed ...'))

    def yes(self, call=None):
        copy_files_to_enigma2()
        ReloadBouquets(sets)


class SettingManutekz(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'HomeNss.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('Manutek Setting')
        self.setTitle(name_plug)
        self.list = []
        self['list'] = nssList([])
        # self['list'] = MenuList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['statusgreen'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'] = Pixmap()
        self['statusred'].hide()
        self['status'] = Label('Please wait..')
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
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        if status_site():
            self['statusgreen'].show()
            self['statusred'].hide()
            self['status'].setText('SERVER ON')
        else:
            self['statusgreen'].hide()
            self['statusred'].show()
            self['status'].setText('SERVER OFF')
        self.setTitle(name_plug)
        self['info'].setText(_('Please select ...'))

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
                name = url.replace("NemoxyzRLS_Manutek_", "").replace("_", " ").replace("%20", " ")
                if name in self.names:
                    continue
                url = 'http://www.manutek.it/isetting/enigma2/' + url + '.zip'
                self.urls.append(Utils.str_encode(url.strip()))
                self.names.append(Utils.str_encode(name.strip()))
                self.downloading = True
            self['key_green'].show()

            showlistNss(self.names, self['list'])
            # self['list'].setList(self.names)

        except Exception as e:
            print('downxmlpage get failed: ', str(e))
            self['info'].setText(_('Download page get failed ...'))

    def okRun(self):
        self.session.openWithCallback(self.okRun1, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okRun1(self, answer=False):
        if answer:
            global sets
            sets = 0
            if self.downloading is True:
                idx = self["list"].getSelectionIndex()
                self.name = self.names[idx]
                url = self.urls[idx]
                dest = "/tmp/settings.zip"
                self.namel = ''

                if 'dtt' not in url.lower():
                    sets = 1
                    terrestrial()
                if keepiptv():
                    print('-----save iptv channels-----')

                from six.moves.urllib.request import urlretrieve
                urlretrieve(url, dest)
                if os.path.exists(dest) and '.zip' in dest:
                    fdest1 = "/tmp/unzipped"
                    fdest2 = "/etc/enigma2"
                    if os.path.exists("/tmp/unzipped"):
                        os.system('rm -rf /tmp/unzipped')
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
                    self.session.openWithCallback(self.yes, tvConsole, title=_(title), cmdlist=["wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /tmp/inst.txt 2>&1 &"], closeOnSuccess=False)
                    self['info'].setText(_('Settings Installed ...'))
                else:
                    self['info'].setText(_('Settings Not Installed (dest)...'))
            else:
                self['info'].setText(_('Settings Not Installed ...'))

    def yes(self, call=None):
        copy_files_to_enigma2()
        ReloadBouquets(sets)


class SettingMorpheusz(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'HomeNss.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('Setting Morpheus')
        self.setTitle(name_plug)
        self.list = []
        self['list'] = nssList([])
        # self['list'] = MenuList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['statusgreen'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'] = Pixmap()
        self['statusred'].hide()
        self['status'] = Label('Please wait..')
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
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        if status_site():
            self['statusgreen'].show()
            self['statusred'].hide()
            self['status'].setText('SERVER ON')
        else:
            self['statusgreen'].hide()
            self['statusred'].show()
            self['status'].setText('SERVER OFF')
        self.setTitle(name_plug)
        self['info'].setText(_('Please select ...'))

    def downxmlpage(self):
        url = 'https://github.com/morpheus883/enigma2-zipped'
        data = make_req(url)
        if PY3:
            data = six.ensure_str(data)
        r = data
        self.names = []
        self.urls = []
        try:
            # regex = 'name":"E2_Morph883_(.*?).zip".*?path":"(.*?)"'
            regex = 'title="E2_Morph883_(.*?).zip".*?href="(.*?)"'
            # n1 = r.find('title="README.txt', 0)
            # n2 = r.find('href="#readme">', n1)
            # r = r[n1:n2]
            match = re.compile(regex).findall(r)
            print('match:', match)
            for name, url in match:
                if url.find('.zip') != -1:
                    name = 'Morph883 ' + name
                    if name in self.names:
                        continue
                    url = url.replace('blob', 'raw')
                    url = 'https://github.com' + url
                self.urls.append(Utils.str_encode(url.strip()))
                self.names.append(Utils.str_encode(name.strip()))
                self.downloading = True
            self['key_green'].show()

            showlistNss(self.names, self['list'])
            # self['list'].setList(self.names)

        except Exception as e:
            print('downxmlpage get failed: ', str(e))
            self['info'].setText(_('Download page get failed ...'))

    def okRun(self):
        self.session.openWithCallback(self.okRun1, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okRun1(self, answer=False):
        if answer:
            global sets
            sets = 0
            if self.downloading is True:
                idx = self["list"].getSelectionIndex()
                url = self.urls[idx]
                dest = "/tmp/settings.zip"
                self.namel = ''

                if 'dtt' not in url.lower():
                    sets = 1
                    terrestrial()
                if keepiptv():
                    print('-----save iptv channels-----')

                from six.moves.urllib.request import urlretrieve
                urlretrieve(url, dest)

                if os.path.exists(dest) and '.zip' in dest:
                    fdest1 = "/tmp/unzipped"
                    fdest2 = "/etc/enigma2"
                    if os.path.exists("/tmp/unzipped"):
                        os.system('rm -rf /tmp/unzipped')
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
                    self.session.openWithCallback(self.yes, tvConsole, title=_(title), cmdlist=["wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /tmp/inst.txt 2>&1 &"], closeOnSuccess=False)
                    self['info'].setText(_('Settings Installed ...'))
                else:
                    self['info'].setText(_('Settings Not Installed (dest)...'))
            else:
                self['info'].setText(_('Settings Not Installed ...'))

    def yes(self, call=None):
        copy_files_to_enigma2()
        ReloadBouquets(sets)


class SettingVhan11(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'HomeNss.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('Setting Vhannibal')
        self.setTitle(name_plug)
        self.list = []

        self['list'] = nssList([])
        # self['list'] = MenuList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['statusgreen'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'] = Pixmap()
        self['statusred'].hide()
        self['status'] = Label('Please wait..')
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
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        if status_site():
            self['statusgreen'].show()
            self['statusred'].hide()
            self['status'].setText('SERVER ON')
        else:
            self['statusgreen'].hide()
            self['statusred'].show()
            self['status'].setText('SERVER OFF')
        self.setTitle(name_plug)
        self['info'].setText(_('Please select ...'))

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
                name = str(name) + ' ' + date
                if name in self.names:
                    continue
                url = "https://www.vhannibal.net/" + url
                self.urls.append(Utils.str_encode(url.strip()))
                self.names.append(Utils.str_encode(name.strip()))
            self.downloading = True
            # self['info'].setText(_('Please select ...'))
            self['key_green'].show()
            showlistNss(self.names, self['list'])
        except Exception as e:
            print('downxmlpage get failed: ', str(e))
            self['info'].setText(_('Download page get failed ...'))

    def okRun(self):
        self.session.openWithCallback(self.okRun1, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okRun1(self, answer=False):
        if answer:
            global sets
            sets = 0
            if self.downloading is True:
                idx = self["list"].getSelectionIndex()
                self.name = self.names[idx]
                url = self.urls[idx]
                dest = "/tmp/settings.zip"
                self.namel = ''

                if 'dtt' not in url.lower():
                    sets = 1
                    terrestrial()
                if keepiptv():
                    print('-----save iptv channels-----')

                from six.moves.urllib.request import urlretrieve
                urlretrieve(url, dest)

                if os.path.exists(dest) and '.zip' in dest:
                    fdest1 = "/tmp/unzipped"
                    fdest2 = "/etc/enigma2"
                    if os.path.exists("/tmp/unzipped"):
                        os.system('rm -rf /tmp/unzipped')
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
                    self.session.openWithCallback(self.yes, tvConsole, title=_(title), cmdlist=["wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /tmp/inst.txt 2>&1 &"], closeOnSuccess=False)
                    self['info'].setText(_('Settings Installed ...'))
                else:
                    self['info'].setText(_('Settings Not Installed (dest)...'))
            else:
                self['info'].setText(_('Settings Not Installed ...'))

    def yes(self, call=None):
        copy_files_to_enigma2()
        ReloadBouquets(sets)


class SettingVhan22(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'HomeNss.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('Setting Vhannibal')
        self.setTitle(name_plug)
        self.list = []
        self['list'] = nssList([])
        # self['list'] = MenuList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['statusgreen'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'] = Pixmap()
        self['statusred'].hide()
        self['status'] = Label('Please wait..')
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
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        if status_site():
            self['statusgreen'].show()
            self['statusred'].hide()
            self['status'].setText('SERVER ON')
        else:
            self['statusgreen'].hide()
            self['statusred'].show()
            self['status'].setText('SERVER OFF')
        self.setTitle(name_plug)
        self['info'].setText(_('Please select ...'))

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
                name = "Vhannibal" + url.replace('&#127381;', '').replace("%20", " ")
                if name in self.names:
                    continue
                url = "http://sat.alfa-tech.net/upload/settings/vhannibal/Vhannibal" + url + '.zip'
                self.urls.append(Utils.str_encode(url.strip()))
                self.names.append(Utils.str_encode(name.strip()))
                self.downloading = True
            self['key_green'].show()
            showlistNss(self.names, self['list'])

        except Exception as e:
            print('downxmlpage get failed: ', str(e))
            self['info'].setText(_('Download page get failed ...'))

    def okRun(self):
        self.session.openWithCallback(self.okRun1, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def okRun1(self, answer=False):
        if answer:
            global sets
            sets = 0
            if self.downloading is True:
                try:
                    idx = self["list"].getSelectionIndex()
                    self.name = self.names[idx]
                    url = self.urls[idx]
                    dest = "/tmp/settings.zip"
                    if 'dtt' not in url.lower():
                        sets = 1
                        terrestrial()
                    if keepiptv():
                        print('-----save iptv channels-----')
                    # from six.moves.urllib.request import urlretrieve
                    # urlretrieve(url, dest)
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
            if os.path.exists(dest) and '.zip' in dest:
                self.namel = ''
                fdest1 = "/tmp/unzipped"
                fdest2 = "/etc/enigma2"
                if os.path.exists("/tmp/unzipped"):
                    os.system('rm -rf /tmp/unzipped')
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
                self.session.openWithCallback(self.yes, tvConsole, title=_(title), cmdlist=["wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /tmp/inst.txt 2>&1 &"], closeOnSuccess=False)
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

    def yes(self, call=None):
        copy_files_to_enigma2()
        ReloadBouquets(sets)


class NssInstall(Screen):
    def __init__(self, session, data, name, selection=None):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('NSS CONSOLE')
        self.setTitle(name_plug)
        self.selection = selection
        self['info'] = Label(_('... please wait'))
        self['pth'] = Label()
        self['pform'] = Label()
        self['progress'] = ProgressBar()
        self["progress"].hide()
        self['progresstext'] = StaticText()
        self['progress'].setRange((0, 100))
        self['progress'].setValue(0)
        list = []
        list.sort()
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
        # self['list'] = MenuList([])
        self['title'] = Label(self.setup_title)
        self['key_red'] = Button(_('Back'))
        self['key_green'] = Button(_('Install'))
        self['key_yellow'] = Button(_('Download'))
        self["key_blue"] = Button()
        self['key_blue'].hide()
        self['key_green'].hide()
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.message1,
                                                       'green': self.message1,
                                                       'red': self.exitY,
                                                       'yellow': self.okDown,
                                                       'cancel': self.exitY}, -2)
        self.onLayoutFinish.append(self.start)

    def exitY(self):
        self.addondel()
        self.close()

    def start(self):
        showlistNss(self.names, self['list'])
        self['info'].setText(_('Please install ...'))
        self['key_green'].show()

    def message1(self):
        self.session.openWithCallback(self.message, MessageBox, _("Do you want to install?"), MessageBox.TYPE_YESNO)

    def message(self, answer=False):
        if answer:
            idx = self["list"].getSelectionIndex()
            dom = self.names[idx]
            com = self.urls[idx]
            self.prombt(com, dom)
        else:
            return

    def prombt(self, com, dom):
        self.timer = eTimer()
        global sets
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
                if not os.path.exists('/var/lib/dpkg/info'):
                    self.session.open(MessageBox, _('Unknow Image!'), MessageBox.TYPE_INFO, timeout=5)
                    self['info'].setText(_('Installation canceled!'))
                else:
                    cmd = "wget -U '%s' -c '%s' -O '%s';dpkg -i %s > /dev/null" % (AgentRequest, str(self.com), self.dest, self.dest)
                    if "https" in str(self.com):
                        cmd = "wget --no-check-certificate -U '%s' -c '%s' -O '%s';dpkg -i %s > /dev/null" % (AgentRequest, str(self.com), self.dest, self.dest)
                    self.session.open(tvConsole, _('Downloading-installing: %s') % self.dom, [cmd], closeOnSuccess=False)
                    self['info'].setText(_('Installation done !!!'))

            elif extension == "ipk":
                if os.path.exists('/var/lib/dpkg/info'):
                    self.session.open(MessageBox, _('Unknow Image!'), MessageBox.TYPE_INFO, timeout=5)
                    self['info'].setText(_('Installation canceled!'))
                else:
                    cmd = "wget -U '%s' -c '%s' -O '%s';opkg --force-reinstall --force-overwrite install %s > /dev/null" % (AgentRequest, str(self.com), self.dest, self.dest)
                    if "https" in str(self.com):
                        cmd = "wget --no-check-certificate -U '%s' -c '%s' -O '%s';opkg --force-reinstall --force-overwrite install %s > /dev/null" % (AgentRequest, str(self.com), self.dest, self.dest)
                    self.session.open(tvConsole, _('Downloading-installing: %s') % self.dom, [cmd], closeOnSuccess=False)
                    self['info'].setText(_('Installation done !!!'))
            elif self.com.endswith('.zip'):
                if 'setting' in self.dom.lower():
                    if not os.path.exists('/var/lib/dpkg/info'):
                        sets = 1
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
                elif 'picon' in self.dom.lower():
                    cmd = ["unzip -o -q %s -d %s > /dev/null" % (down, str(mmkpicon))]
                    self.session.open(tvConsole, _('Downloading-installing: %s') % self.dom, [cmd], closeOnSuccess=False)
                    self['info'].setText(_('Installation done !!!'))
                else:
                    self['info'].setText(_('Downloading the selected file in /tmp') + self.dom + _('... please wait'))
                    cmd = ["wget --no-cache --no-dns-cache -U '%s' -c '%s' -O '%s --post-data='action=purge' > /dev/null' " % (RequestAgent(), str(self.com), down)]
                    self.session.open(tvConsole, _('Downloading: %s') % self.dom, cmd, closeOnSuccess=False)
                    self['info'].setText(_('Download done !!!'))
                    self.session.open(MessageBox, _('Download file in /tmp successful!'), MessageBox.TYPE_INFO, timeout=5)
                    self['info'].setText(_('Download file in /tmp successful!!'))
            else:
                self['info'].setText(_('Download Failed!') + self.dom + _('... Not supported'))
            self.timer.start(3000, 1)

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
            handler = urlopen(req, timeout=10)
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

    def okDownll(self, answer=False):
        if answer:
            self['info'].setText(_('... please wait'))
            idx = self["list"].getSelectionIndex()
            self.dom = self.names[idx]
            self.com = self.urls[idx]
            self.downplug = self.com.split("/")[-1]
            self.dest = '/tmp/' + str(self.downplug)

            if os.path.exists(self.dest):
                os.remove(self.dest)

            if self.com is not None:
                extensionlist = self.com.split('.')
                extension = extensionlist[-1].lower()
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
                    cmd = "wget --no-cache --no-dns-cache -q -O '%s' '%s' --post-data='action=purge';" + self.command[0] % (self.dest, str(self.com))
                    print('command:', cmd)
                    self.session.open(tvConsole, _('Downloading-installing: %s') % self.dom, [cmd], closeOnSuccess=False)
                    self['info'].setText(_('Installation done !!!'))
                    return

                if extension == "deb" and not os.path.exists('/var/lib/dpkg/info'):
                    self.session.open(MessageBox, _('Unknow Image!'), MessageBox.TYPE_INFO, timeout=5)
                    self['info'].setText(_('Download canceled!'))
                    return

                elif extension == ".ipk" and os.path.exists('/var/lib/dpkg/info'):
                    self.session.open(MessageBox, _('Unknow Image!'), MessageBox.TYPE_INFO, timeout=5)
                    self['info'].setText(_('Download canceled!'))
                    return
                else:
                    if os.path.exists('/var/lib/dpkg/info'):
                        cmd = ["wget --no-check-certificate -U '%s' -c '%s' -O '%s' --post-data='action=purge' > /dev/null" % (RequestAgent(), str(self.com), self.dest)]
                        print('command:', cmd)
                        subprocess.Popen(cmd[0], shell=True, executable='/bin/bash')
                        self.session.openWithCallback(self.tvIPK, MessageBox, _('Download file in /tmp successful!'), MessageBox.TYPE_INFO, timeout=5)
                        return
                    # else:
                    self.download = downloadWithProgress(self.com, self.dest)
                    self.download.addProgress(self.downloadProgress)
                    self.download.start().addCallback(self.install).addErrback(self.download_failed)

            else:
                self['info'].setText(_('Download Failed!') + self.dom + _('... Not supported'))

    def downloadProgress(self, recvbytes, totalbytes):
        self['info'].setText(_('Download in progress...'))
        self["progress"].show()
        self['progress'].value = int(100 * self.last_recvbytes / float(totalbytes))
        self['progresstext'].text = '%d of %d kBytes (%.2f%%)' % (self.last_recvbytes / 1024, totalbytes / 1024, 100 * self.last_recvbytes / float(totalbytes))
        self.last_recvbytes = recvbytes

    # ok oe2
    def downloadProgress2(self, recvbytes, totalbytes):
        try:
            self['info'].setText(_('Download in progress...'))
            self["progress"].show()
            self['progress'].value = int(100 * self.last_recvbytes / float(totalbytes))
            self['progresstext'].text = '%d of %d kBytes (%.2f%%)' % (self.last_recvbytes / 1024, totalbytes / 1024, 100 * self.last_recvbytes / float(totalbytes))
            self.last_recvbytes = recvbytes
        except ZeroDivisionError:
            self['info'].setText(_('Download Failed!'))
            self["progress"].hide()
            self['progress'].setRange((0, 100))
            self['progress'].setValue(0)

    def showError(self):
        print("download error ")
        self.downloading = False
        self.close()

    def download_failed(self, failure_instance=None, error_message=""):
        self.error_message = error_message
        if error_message == "" and failure_instance is not None:
            self.error_message = failure_instance.getErrorMessage()
        self.downloading = False
        info = _('Download Failed!') + str(self.error_message)
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

    def abort(self, ret=None):
        print("aborting", self.url)
        if self.download:
            self.download.stop()
        self.aborted = True

    def download_finished(self, string=""):
        if self.aborted:
            self.finish(aborted=True)

    def NssIPK(self, string=None):
        self.install('None')

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
                self.session.openWithCallback(self.passe, NssIPK)

    def passe(self, ret=None):
        self.close()


class NssIPK(Screen):
    def __init__(self, session, title=None, cmdlist=None, finishedCallback=None, closeOnSuccess=False):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'NssIPK.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setTitle(name_plug)
        self.setup_title = ('Extensions Install')

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

        self['info1'] = Label(_('Path /tmp\n\nPut .ipk .tar.gz .deb .zip and install'))
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
        for x in self.list:
            del self.list[0]
        for x in self.names:
            del self.names[0]
        del self.names[:]
        del self.list[:]
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

    def msgipkrmv(self, answer=False):
        if len(self.names) >= 0:
            idx = self['list'].getSelectionIndex()
            self.sel = self.names[idx]
            self.com = self.ipkpth + '/' + self.sel
            if answer is False:
                self.session.openWithCallback(self.msgipkrmv, MessageBox, (_('Do you really want to remove selected?\n') + self.sel), MessageBox.TYPE_YESNO)
            else:
                self['info'].setText(_('... please wait'))
                self.com = self.ipkpth + '/' + self.sel
                if fileExists(self.com):
                    os.remove(self.com)
                    # i = len(self.list)
                    # del self.list[0:i]
                    self.list = []
                    self.names = []
                    for x in self.list:
                        del self.list[0]
                    for x in self.names:
                        del self.names[0]
                    del self.names[:]
                    del self.list[:]
                    self.session.open(MessageBox, (_("%s has been successfully deleted\nwait time to refresh the list...") % self.sel), MessageBox.TYPE_INFO, timeout=5)
                else:
                    self.session.open(MessageBox, (_("%s not exist!\nwait time to refresh the list...") % self.sel), MessageBox.TYPE_INFO, timeout=5)
                self.close()

    def getfreespace(self):
        try:
            fspace = Utils.freespace()
            self['info'].setText(str(fspace))
        except Exception as e:
            print(e)

    def goConfig(self):
        self.session.open(nssConfig)

    def ipkinst(self, answer=False):
        if len(self.names) >= 0:
            idx = self['list'].getSelectionIndex()
            self.sel = self.names[idx]
            if answer is False:
                self.session.openWithCallback(self.ipkinst, MessageBox, (_('Do you really want to install the selected Addon?\n') + self.sel), MessageBox.TYPE_YESNO)
            else:
                self['info'].setText(_('... please wait'))
                self.dest = self.ipkpth + '/' + self.sel
                try:
                    if self.sel.endswith('.ipk'):
                        cmd0 = 'echo "Sistem Update .... PLEASE WAIT ::.....";echo ":Install ' + self.dest + '";opkg --force-reinstall --force-overwrite install ' + self.dest + ' > /dev/null'
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
                            if not os.path.exists('/var/lib/dpkg/info'):
                                global sets
                                sets = 1
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
        if fileExists(dest):
            os.system('rm -rf ' + dest)
        self.refreshlist()

    def msgipkinst(self, answer=False):
        if answer is False:
            self.session.openWithCallback(self.msgipkinst, MessageBox, _('Restart Enigma to load the installed plugin?'), MessageBox.TYPE_YESNO)
        else:
            self.session.open(TryQuitMainloop, 3)


class NssRemove(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setTitle(name_plug)
        self.setup_title = ('Extensions Remove')
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
        self['pform'] = Label()
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
            if len(self.names) >= 1:
                self['info'].setText(_('Please Remove ...'))
                self['key_green'].show()
            showlistNss(self.names, self['list'])
        except Exception as e:
            print(e)

    def message1(self):
        self.session.openWithCallback(self.message11, MessageBox, _('Do you want to remove?'), MessageBox.TYPE_YESNO)

    def message11(self, answer=False):
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

    def msgipkrst(self, answer=False):
        if answer is False:
            self.session.openWithCallback(self.msgipkrst, MessageBox, _('Do you want restart enigma2 ?'), MessageBox.TYPE_YESNO)
        else:
            epgpath = '/media/hdd/epg.dat'
            epgbakpath = '/media/hdd/epg.dat.bak'
            if os.path.exists(epgbakpath):
                os.remove(epgbakpath)
            if os.path.exists(epgpath):
                shutil.copyfile(epgpath, epgbakpath)
            self.session.open(TryQuitMainloop, 3)


class nssConfig(ConfigListScreen, Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'nssConfig.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setTitle("NSS Addon Config")
        self.setup_title = ('Config Panel')
        self.onChangedEntry = []
        self.list = []
        self['title'] = Label(self.setup_title)
        self['description'] = Label()
        self['info'] = Label(_('SELECT YOUR CHOICE'))
        self['key_yellow'] = Button(_('Update'))
        self['key_green'] = Button(_('Save'))
        self['key_red'] = Button(_('Back'))
        self["key_blue"] = Button()
        self['key_blue'].hide()
        self['key_yellow'].hide()
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
        self.createSetup()
        self["setupActions"] = ActionMap(['OkCancelActions',
                                          'DirectionActions',
                                          'ColorActions',
                                          # 'VirtualKeyboardActions',
                                          'ActiveCodeActions'], {'cancel': self.extnok,
                                                                 'red': self.extnok,
                                                                 'back': self.close,
                                                                 # "showVirtualKeyboard": self.KeyText,
                                                                 'green': self.msgok}, -1)
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
            python = os.popen('python -V').read().strip('\n\r')
            ifg = os.popen('wget -qO - ifconfig.me').read().strip('\n\r')
            img = img.replace('\\l', '')
            libs = os.popen('ls -l /usr/lib/libss*.*').read().strip('\n\r')
            if libs:
                libsssl = libs
            info = 'Current IP Wan: %s\nImage Mounted: %sCpu: %s\nPython:%s\nInfo Hardware: %s\nLibssl(oscam):\n%s\n' % (ifg, img, arc, python, arkFull, libsssl)
            self['info'].setText(info)
        except Exception as e:
            print("Error ", e)
            self['info'].setText(_(':) by Lululla '))

    def createSetup(self):
        self.editListEntry = None
        self.list = []
        # self.list.append(getConfigListEntry(_("Set the path to the Picons folder"), mmkpicon, _("Configure folder containing picons files")))
        # self.list.append(getConfigListEntry(_("Path for Picons folder"), mmkpicon, _("Folder containing picons files")))
        # self.list.append(getConfigListEntry(_("Set the path to the Picons folder"), config.usage.picon_dir, _("Configure folder containing picons files")))
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

    def msgok(self):
        if self['config'].isChanged():
            for x in self["config"].list:
                x[1].save()
            configfile.save()
            self.session.open(MessageBox, _('Successfully saved configuration'), MessageBox.TYPE_INFO, timeout=4)
        else:
            self.close(True)

    def cancelConfirm(self, result=False):
        if result is False:
            return
        for x in self['config'].list:
            x[1].cancel()
        self.close()

    def extnok(self):
        if self['config'].isChanged():
            self.session.openWithCallback(self.cancelConfirm, MessageBox, _('Really close without saving the settings?'), MessageBox.TYPE_YESNO)
        else:
            self.close()


class ScriptExecuter(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'scriptpanel.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setTitle(name_plug)
        self.setup_title = ('Scriptpanel')
        self.mlist = []
        self.populateScript()
        self['list'] = List(self.mlist)
        # self['list'] = MenuList([])
        self['list'].onSelectionChanged.append(self.schanged)
        self['info'] = Label(_('NO SCRIPT FOUND'))
        self['labstatus'] = Label(_('SELECT'))
        self['statusgreen'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'] = Pixmap()
        self['statusred'].hide()
        self['status'] = Label('Please wait..')
        self['key_green'] = Button(_('Execute'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button()
        self["key_blue"] = Button()
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self['actions'] = ActionMap(['WizardActions',
                                     'ColorActions'], {'ok': self.startScript,
                                                       'back': self.close,
                                                       'green': self.startScript,
                                                       'red': self.close})
        self.onLayoutFinish.append(self.script_sel)
        # self.onLayoutFinish.append(self.populateScript)
        self.onShown.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setTitle(name_plug)

    def script_sel(self):
        self['list'].index = 1
        self['list'].index = 0
        self['info'].setText('SELECT')

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
                with codecs.open(myfil, "rb", encoding="latin-1") as f:
                    for line in f.readlines():
                        if line.find('#DESCRIPTION=') != -1:
                            line = line.strip()
                            desc = line[13:]
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
                chmod(mysel2, 0o0777)
                mytitle = 'NonSoloSat Script: ' + mysel
                self.session.open(tvConsole, title=mytitle, cmdlist=[mysel2])


class SelectPiconz(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'HomeNss.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('NSS Addon Picons')
        self.setTitle(name_plug)
        self['list'] = nssList([])
        # self['list'] = MenuList([])

        self['info'] = Label()
        self['info'].setText(_('Loading data... Please wait'))
        self['key_green'] = Button(_('Select'))
        self['key_red'] = Button(_('Back'))
        self['key_yellow'] = Button(_('Remove'))
        self["key_blue"] = Button()
        # self['key_yellow'].hide()
        self['key_blue'].hide()
        self['key_green'].hide()

        self['statusgreen'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'] = Pixmap()
        self['statusred'].hide()
        self['status'] = Label('Please wait..')

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

    def remove1(self, answer=False):
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
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'HomeNss.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('NSS Addon Picons')
        self.setTitle(name_plug)
        self.list = []
        self['list'] = nssList([])
        # self['list'] = MenuList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['statusgreen'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'] = Pixmap()
        self['statusred'].hide()
        self['status'] = Label('Please wait..')
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
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('NSS Addon Picons')
        self.setTitle(name_plug)
        self.list = []
        self['list'] = nssList([])
        # self['list'] = MenuList([])

        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label()
        self['pth'].setText(_('Folder picons ') + str(mmkpicon))
        self['pform'] = Label()
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
        self.movie = movie
        self.url = url
        self.name = name
        self.error_message = ""
        self.last_recvbytes = 0
        self.progclear = 0
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
                # print('url333: ', url)
                if os.path.exists(dest) and '.zip' in dest:
                    os.remove(dest)
                try:
                    myfile = Utils.ReadUrl(url)
                    # print('response: ', myfile)
                    regexcat = 'href="https://download(.*?)"'
                    match = re.compile(regexcat, re.DOTALL).findall(myfile)
                    # print("match =", match[0])
                    # myfile = checkMyFile(url)
                    # print('myfile222:  ', myfile)
                    url = 'https://download' + str(match[0])
                    # print("url final =", url)
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
        if self.last_recvbytes == recvbytes:
            self.getfreespace()

    def download_failed(self, failure_instance=None, error_message=""):
        self.error_message = error_message
        if error_message == "" and failure_instance is not None:
            self.error_message = failure_instance.getErrorMessage()
        self.downloading = False
        info = _('Download Failed!') + str(self.error_message)
        self['info'].setText(info)
        self.session.open(MessageBox, _(info), MessageBox.TYPE_INFO, timeout=5)

    def abort(self):
        print("aborting", self.url)
        if self.download:
            self.download.stop()
            self.getfreespace()
        self.downloading = False
        self.aborted = True

    def download_finished(self, string=""):
        if self.aborted:
            self.finish(aborted=True)
        self['info'].setText(_('Picons installed...'))
        self.getfreespace()

    def install(self, string=''):
        if self.aborted:
            self.finish(aborted=True)
        else:
            self['info'].setText(_('File Downloaded ...'))
            if os.path.exists('/tmp/download.zip'):
                self['info'].setText(_('Install ...'))
                self['info'].setText(_('Please select ...'))
                myCmd = "unzip -o -q '/tmp/download.zip' -d %s/" % str(mmkpicon)
                subprocess.Popen(myCmd, shell=True, executable='/bin/bash')
                info = 'Successfully Picons Installed'
                self.session.open(MessageBox, _(info), MessageBox.TYPE_INFO, timeout=5)
        self.close()


class OpenPicons(Screen):
    def __init__(self, session, name, url):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'tvall.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('OpenPicons')
        self.setTitle(name_plug)
        self.list = []
        self['list'] = nssList([])
        # self['list'] = MenuList([])
        self['info'] = Label(_('Loading data... Please wait'))
        self['pth'] = Label()
        self['pth'].setText(_('Folder picons ') + str(mmkpicon))
        self['pform'] = Label()
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
        self.progclear = 0
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
            self.downloading = False
            self['progresstext'].text = ''
            self['progress'].setValue(self.progclear)
            self["progress"].hide()
            self['info'].setText(_('Please select ...'))
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
                # https://openpicons.com/picons/full-motor-srp/hardlink/srp-full.100x60-86x46.light.on.transparent_2024-08-10--16-32-09.hardlink.tar.xz
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

    def okRun1(self, answer=False):
        if answer:
            if self.downloading is True:
                idx = self["list"].getSelectionIndex()
                self.name = self.names[idx]
                url = self.urls[idx]
                print('1 url type=', type(url))
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

    def download_failed(self, failure_instance=None, error_message=""):
        self.error_message = error_message
        if error_message == "" and failure_instance is not None:
            self.error_message = failure_instance.getErrorMessage()
        self.downloading = False
        info = _('Download Failed!') + str(self.error_message)
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
            self.getfreespace()

    def install(self, string=''):
        if self.aborted:
            self.finish(aborted=True)
        else:
            self['info'].setText(_('File Downloaded ...'))
            if os.path.exists(self.dest):
                self.namel = ''
                self['info'].setText(_('Install ...'))
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
        self.getfreespace()


def autostartsoftcam(reason, session=None, **kwargs):
    """called with reason=1 to during shutdown, with reason=0 at startup?"""
    print("[Softcam] Started")
    if reason == 0:
        print('reason 0')
        if session is not None:
            try:
                print('ok started autostart')
                if fileExists('/etc/init.d/dccamd'):
                    os.system('mv /etc/init.d/dccamd /etc/init.d/dccamdOrig &')
                if fileExists('/usr/bin/dccamd'):
                    os.system("mv /usr/bin/dccamd /usr/bin/dccamdOrig &")
                os.system("ln -sf /usr/bin /var/bin")
                os.system("ln -sf /usr/keys /var/keys")
                os.system("ln -sf /usr/scce /var/scce")
                os.system("sleep 2")
                cmd2 = 'chmod 755 /etc/startcam.sh &'
                os.system(cmd2)
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


def cfgcam(menuid, **kwargs):
    return [(name_cam, main2, 'www.nonsolosat.net NSS Cam Manager', 44)] if menuid == "cam" else []


def cfgmain(menuid, **kwargs):
    return [('Nss Addons', main, 'www.nonsolosat.net (Addons Panel)', 44)] if menuid == "mainmenu" else []


def main2(session, **kwargs):
    from Plugins.Extensions.Manager.plugin import Manager
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


# ===== by lululla
