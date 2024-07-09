# -*- coding: utf-8 -*-

from . import _
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Components.ActionMap import ActionMap
from Components.config import ConfigSubsection, getConfigListEntry, ConfigSelection
from Components.config import config, NoSave, ConfigNothing
from Components.ConfigList import ConfigListScreen
from Components.Sources.Progress import Progress
from Tools.Downloader import downloadWithProgress
from Components.Sources.StaticText import StaticText
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.AVSwitch import AVSwitch
# from twisted.web.client import getPage
from Tools.Directories import fileExists
import os
import sys
from enigma import ePicLoad

PY3 = sys.version_info.major >= 3
if PY3:
    bytes = bytes
    unicode = str
    from urllib.request import urlopen
    from urllib.request import Request

else:
    from urllib2 import urlopen
    from urllib2 import Request


version = '1.08'

config.plugins.AglareNss = ConfigSubsection()
config.plugins.AglareNss.colorSelector = ConfigSelection(default='head', choices=[
 ('head', _('Default')),
 ('color1', _('Black')),
 ('color2', _('Brown')),
 ('color3', _('Green')),
 ('color4', _('Magenta')),
 ('color5', _('Blue')),
 ('color6', _('Red')),
 ('color7', _('Purple'))])
config.plugins.AglareNss.FontStyle = ConfigSelection(default='basic', choices=[
 ('basic', _('Default')),
 ('font1', _('HandelGotD')),
 ('font2', _('KhalidArtboldRegular')),
 ('font3', _('BebasNeue'))])
config.plugins.AglareNss.skinSelector = ConfigSelection(default='base', choices=[
 ('base', _('Default'))])
config.plugins.AglareNss.InfobarStyle = ConfigSelection(default='infobar_no_posters', choices=[
 ('infobar_no_posters', _('Infobar_NO_Posters')),
 ('infobar_posters_meteo', _('Infobar_Posters_Meteo')),
 ('infobar_posters', _('Infobar_Posters'))])
config.plugins.AglareNss.SecondInfobarStyle = ConfigSelection(default='secondinfobar_no_posters', choices=[
 ('secondinfobar_no_posters', _('SecondInfobar_NO_Posters')),
 ('secondinfobar_posters', _('SecondInfobar_Posters'))])
config.plugins.AglareNss.ChannSelector = ConfigSelection(default='channellist_no_posters', choices=[
 ('channellist_no_posters', _('ChannelSelection_NO_Posters')),
 ('channellist_np_full', _('ChannelSelection_NO_Posters_Full')),
 ('channellist_no_posters_no_picon', _('ChannelSelection_NO_Posters_NO_Picon')),
 ('channellist_1_poster', _('ChannelSelection_1_Poster')),
 ('channellist_3_posters_v', _('ChannelSelection_3_Posters_V')),
 ('channellist_4_posters', _('ChannelSelection_4_Posters')),
 ('channellist_big_mini_tv', _('ChannelSelection_big_mini_tv'))])
config.plugins.AglareNss.EventView = ConfigSelection(default='eventview_no_posters', choices=[
 ('eventview_no_posters', _('EventView_NO_Posters')),
 ('eventview_7_posters', _('EventView_7_Posters')),
 ('eventview_banner', _('EventView_Banner'))])

config.plugins.AglareNss.VolumeBar = ConfigSelection(default='volume1', choices=[
 ('volume1', _('Default')),
 ('volume2', _('volume2'))])


def Plugins(**kwargs):
    return PluginDescriptor(name='NSS Skin Setup', description=_('Customization tool for Aglare-FHD-NSS Skin'), where=PluginDescriptor.WHERE_PLUGINMENU, icon='plugin.png', fnc=main)


def main(session, **kwargs):
    session.open(AglareSetup)


def str_encode(text, encoding="utf8"):
    if not PY3:
        if isinstance(text, unicode):
            return text.encode(encoding)
        else:
            return text
    else:
        return text


class AglareSetup(ConfigListScreen, Screen):
    # skin = '<screen name="AglareSetup" position="center,center" size="1000,640" title="Aglare-FHD-NSS Skin Controler">\n\t\t  <eLabel font="Regular; 24" foregroundColor="#00ff4A3C" halign="center" position="20,598" size="120,26" text="Cancel" />\n\t\t  <eLabel font="Regular; 24" foregroundColor="#0056C856" halign="center" position="220,598" size="120,26" text="Save" />\n\t\t  <widget name="Preview" position="997,690" size="498, 280" zPosition="1" />\n\t\t <widget name="config" font="Regular; 24" itemHeight="40" position="5,5" scrollbarMode="showOnDemand" size="990,550" />\n\t\t\n\t\t  </screen>'
    skin = '''<screen name="AglareSetup" position="center,center" size="1000,640" title="Aglare-FHD-NSS Skin Controler">
                <eLabel font="Regular; 24" foregroundColor="#00ff4A3C" halign="center" position="20,598" size="120,26" text="Cancel" />
                <eLabel font="Regular; 24" foregroundColor="#0056C856" halign="center" position="220,598" size="120,26" text="Save" />
                <widget name="Preview" position="1022,-58" size="498, 280" zPosition="1" />
                <widget name="config" font="Regular; 24" itemHeight="40" position="5,5" scrollbarMode="showOnDemand" size="990,550" />
              </screen>'''

    def __init__(self, session):
        self.version = '.Aglare-FHD-NSS'
        Screen.__init__(self, session)
        self.session = session
        self.skinFile = '/usr/share/enigma2/Aglare-FHD-NSS/skin.xml'
        self.previewFiles = '/usr/lib/enigma2/python/Plugins/Extensions/Aglare/sample/'
        self['Preview'] = Pixmap()
        list = []
        list.append(getConfigListEntry(_('Color Style:'), config.plugins.AglareNss.colorSelector))
        list.append(getConfigListEntry(_('Select Your Font:'), config.plugins.AglareNss.FontStyle))
        list.append(getConfigListEntry(_('Skin Style:'), config.plugins.AglareNss.skinSelector))
        list.append(getConfigListEntry(_('InfoBar Style:'), config.plugins.AglareNss.InfobarStyle))
        list.append(getConfigListEntry(_('SecondInfobar Style:'), config.plugins.AglareNss.SecondInfobarStyle))
        list.append(getConfigListEntry(_('ChannelSelection Style:'), config.plugins.AglareNss.ChannSelector))
        list.append(getConfigListEntry(_('EventView Style:'), config.plugins.AglareNss.EventView))
        list.append(getConfigListEntry(_('VolumeBar Style:'), config.plugins.AglareNss.VolumeBar))

        ConfigListScreen.__init__(self, list)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'DirectionActions',
                                     'InputActions',
                                     'ColorActions'], {'left': self.keyLeft,
                                                       'down': self.keyDown,
                                                       'up': self.keyUp,
                                                       'right': self.keyRight,
                                                       'red': self.keyExit,
                                                       'green': self.keySave,
                                                       'yellow': self.checkforUpdate,
                                                       'blue': self.info,
                                                       'cancel': self.keyExit}, -1)
        self.onLayoutFinish.append(self.UpdateComponents)
        self.PicLoad = ePicLoad()
        self.Scale = AVSwitch().getFramebufferScale()
        try:
            self.PicLoad.PictureData.get().append(self.DecodePicture)
        except:
            self.PicLoad_conn = self.PicLoad.PictureData.connect(self.DecodePicture)

    def GetPicturePath(self):
        try:
            returnValue = self['config'].getCurrent()[1].value
            path = '/usr/lib/enigma2/python/Plugins/Extensions/Aglare/screens/' + returnValue + '.png'
            if fileExists(path):
                return path
            else:
                return '/usr/lib/enigma2/python/Plugins/Extensions/Aglare/screens/default.png'
        except:
            return '/usr/lib/enigma2/python/Plugins/Extensions/Aglare/screens/default.png'

    def UpdatePicture(self):
        self.PicLoad.PictureData.get().append(self.DecodePicture)
        self.onLayoutFinish.append(self.ShowPicture)

    def ShowPicture(self, data=None):
        if self["Preview"].instance:
            width = 498
            height = 280
            self.PicLoad.setPara([width, height, self.Scale[0], self.Scale[1], 0, 1, "ff000000"])
            if self.PicLoad.startDecode(self.GetPicturePath()):
                self.PicLoad = ePicLoad()
                try:
                    self.PicLoad.PictureData.get().append(self.DecodePicture)
                except:
                    self.PicLoad_conn = self.PicLoad.PictureData.connect(self.DecodePicture)
            return

    def DecodePicture(self, PicInfo=None):
        ptr = self.PicLoad.getData()
        if ptr is not None:
            self["Preview"].instance.setPixmap(ptr)
            self["Preview"].instance.show()
        return

    def UpdateComponents(self):
        self.UpdatePicture()

    def info(self):
        aboutbox = self.session.open(MessageBox, _('Setup Plugin for Aglare-FHD-NSS v.%s\n mod by Lululla') % version, MessageBox.TYPE_INFO)
        aboutbox.setTitle(_('Info...'))

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self.ShowPicture()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self.ShowPicture()

    def keyDown(self):
        self['config'].instance.moveSelection(self['config'].instance.moveDown)
        self.ShowPicture()

    def keyUp(self):
        self['config'].instance.moveSelection(self['config'].instance.moveUp)
        self.ShowPicture()

    # def restartGUI(self, answer):
        # if answer is True:
            # self.session.open(TryQuitMainloop, 3)
        # else:
            # self.close()

    def keySave(self):
        if not fileExists(self.skinFile + self.version):
            for x in self['config'].list:
                x[1].cancel()

            self.close()
            return
        for x in self['config'].list:
            x[1].save()

        try:
            skin_lines = []
            head_file = self.previewFiles + 'head-' + config.plugins.AglareNss.colorSelector.value + '.xml'
            skFile = open(head_file, 'r')
            head_lines = skFile.readlines()
            skFile.close()
            for x in head_lines:
                skin_lines.append(x)

            font_file = self.previewFiles + 'font-' + config.plugins.AglareNss.FontStyle.value + '.xml'
            skFile = open(font_file, 'r')
            font_lines = skFile.readlines()
            skFile.close()
            for x in font_lines:
                skin_lines.append(x)

            skn_file = self.previewFiles + 'infobar-' + config.plugins.AglareNss.InfobarStyle.value + '.xml'
            skFile = open(skn_file, 'r')
            file_lines = skFile.readlines()
            skFile.close()
            for x in file_lines:
                skin_lines.append(x)

            skn_file = self.previewFiles + 'secondinfobar-' + config.plugins.AglareNss.SecondInfobarStyle.value + '.xml'
            skFile = open(skn_file, 'r')
            file_lines = skFile.readlines()
            skFile.close()
            for x in file_lines:
                skin_lines.append(x)

            skn_file = self.previewFiles + 'channellist-' + config.plugins.AglareNss.ChannSelector.value + '.xml'
            skFile = open(skn_file, 'r')
            file_lines = skFile.readlines()
            skFile.close()
            for x in file_lines:
                skin_lines.append(x)

            skn_file = self.previewFiles + 'eventview-' + config.plugins.AglareNss.EventView.value + '.xml'
            skFile = open(skn_file, 'r')
            file_lines = skFile.readlines()
            skFile.close()
            for x in file_lines:
                skin_lines.append(x)

            skn_file = self.previewFiles + 'vol-' + config.plugins.AglareNss.VolumeBar.value + '.xml'
            skFile = open(skn_file, 'r')
            file_lines = skFile.readlines()
            skFile.close()
            for x in file_lines:
                skin_lines.append(x)

            base_file = self.previewFiles + 'base.xml'
            if config.plugins.AglareNss.skinSelector.value == 'base1':
                base_file = self.previewFiles + 'base1.xml'
            if config.plugins.AglareNss.skinSelector.value == 'base':
                base_file = self.previewFiles + 'base.xml'
            skFile = open(base_file, 'r')
            file_lines = skFile.readlines()
            skFile.close()
            for x in file_lines:
                skin_lines.append(x)

            xFile = open(self.skinFile, 'w')
            for xx in skin_lines:
                xFile.writelines(xx)
            xFile.close()
        except:
            self.session.open(MessageBox, _('Error by processing the skin file !!!'), MessageBox.TYPE_ERROR)

        restartbox = self.session.openWithCallback(self.restartGUI, MessageBox, _('GUI needs a restart to apply a new skin.\nDo you want to Restart the GUI now?'), MessageBox.TYPE_YESNO)
        restartbox.setTitle(_('Restart GUI now?'))

    def restartGUI(self, answer):
        if answer is True:
            self.session.open(TryQuitMainloop, 3)
        else:
            self.close()

    def checkforUpdate(self):
        try:
            fp = ''
            destr = '/tmp/AglareUpdate.txt'
            req = Request('http://nonsolosat.net/AglareImage/AglareUpdate.txt')
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
            fp = urlopen(req)
            fp = fp.read().decode('utf-8')
            print('fp read:', fp)
            with open(destr, 'w') as f:
                f.write(str(fp))  # .decode("utf-8"))
                f.seek(0)
                f.close()
            if os.path.exists(destr):
                with open(destr, 'r') as cc:
                    s1 = cc.readline()  # .decode("utf-8")
                    vers = s1.split('#')[0]
                    url = s1.split('#')[1]
                    version_server = vers.strip()
                    self.updateurl = url.strip()
                    cc.close()
                    if str(version_server) == str(version):
                        message = '%s %s\n%s %s\n\n%s' % (_('Server version:'),
                         version_server,
                         _('Version installed:'),
                         version,
                         _('You have the current version Aglare!'))
                        self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
                    elif version_server > version:
                        message = '%s %s\n%s %s\n\n%s' % (_('Server version:'),
                         version_server,
                         _('Version installed:'),
                         version,
                         _('The update is available!\n\nDo you want to run the update now?'))
                        self.session.openWithCallback(self.update, MessageBox, message, MessageBox.TYPE_YESNO)
                    else:
                        self.session.open(MessageBox, _('You have version %s!!!') % version, MessageBox.TYPE_ERROR)
        except Exception as e:
            print('error: ', str(e))

    def update(self, answer):
        if answer is True:
            self.session.open(AglareUpdater, self.updateurl)
        else:
            return

    def keyExit(self):
        for x in self['config'].list:
            x[1].cancel()
        self.close()


class AglareUpdater(Screen):

    def __init__(self, session, updateurl):
        self.session = session
        skin = '''
                <screen name="AglareUpdater" position="center,center" size="840,360" flags="wfNoBorder" backgroundColor="background">
                    <widget name="status" position="20,10" size="800,70" transparent="1" font="Regular;16" foregroundColor="foreground" backgroundColor="background" valign="center" halign="left" noWrap="1" />
                    <widget source="progress" render="Progress" position="100,153" size="400,6" transparent="1" borderWidth="0" />
                    <widget source="progresstext" render="Label" position="333,184" zPosition="2" font="Regular;18" halign="center" transparent="1" size="180,20" foregroundColor="foreground" backgroundColor="background" />
                </screen>
                '''
        self.skin = skin
        Screen.__init__(self, session)
        self.updateurl = updateurl
        print('self.updateurl', self.updateurl)
        self['status'] = Label()
        self['progress'] = Progress()
        self['progresstext'] = StaticText()
        self.icount = 0
        self.downloading = False
        self.last_recvbytes = 0
        self.error_message = None
        self.download = None
        self.aborted = False
        self.startUpdate()

    def startUpdate(self):
        self['status'].setText(_('Downloading Aglare...'))
        self.dlfile = '/tmp/xxx.tar'
        print('self.dlfile', self.dlfile)
        self.download = downloadWithProgress(self.updateurl, self.dlfile)
        self.download.addProgress(self.downloadProgress)
        self.download.start().addCallback(self.downloadFinished).addErrback(self.downloadFailed)

    def downloadFinished(self, string=''):
        self['status'].setText(_('Installing updates!'))
        os.system('cd /tmp/; tar -xvf xxx.tar -C /; sync')
        os.system('rm /tmp/xxx*.*')
        os.system('sync')
        restartbox = self.session.openWithCallback(self.restartGUI, MessageBox, _('Aglare update was done!!!\nDo you want to restart the GUI now?'), MessageBox.TYPE_YESNO)
        restartbox.setTitle(_('Restart GUI now?'))

    def downloadFailed(self, failure_instance=None, error_message=''):
        text = _('Error downloading files!')
        if error_message == '' and failure_instance is not None:
            error_message = failure_instance.getErrorMessage()
            text += ': ' + error_message
        self['status'].setText(text)
        return

    def downloadProgress(self, recvbytes, totalbytes):
        self['status'].setText(_('Download in progress...'))
        self['progress'].value = int(100 * self.last_recvbytes / float(totalbytes))
        self['progresstext'].text = '%d of %d kBytes (%.2f%%)' % (self.last_recvbytes / 1024, totalbytes / 1024, 100 * self.last_recvbytes / float(totalbytes))
        self.last_recvbytes = recvbytes

    def restartGUI(self, answer):
        if answer is True:
            self.session.open(TryQuitMainloop, 3)
        else:
            self.close()
