#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# --------------------#
#  coded by Lululla  #
#     update to      #
#     27/02/2025     #
# --------------------#
from __future__ import print_function
from . import _, wgetsts
from .data.Utils import RequestAgent, b64decoder, checkGZIP
from .data.GetEcmInfo import GetEcmInfo
from .data.Console import Console
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Button import Button
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Sources.List import List
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap
from enigma import (
	eTimer,
	getDesktop,
)
from os import mkdir, access, X_OK, system, popen, chmod, remove, walk, stat
from os.path import dirname, join, exists, islink
from time import sleep
from twisted.web.client import getPage
from xml.dom import minidom
import codecs
import subprocess
import sys
import time

global active, skin_path, local
global _session


active = False
_session = None
PY3 = sys.version_info.major >= 3
currversion = '1.0'
name_plug = 'NSS Cam Manager'
title_plug = "..:: " + name_plug + " V. %s ::.." % currversion
plugin_path = dirname(sys.modules[__name__].__file__)
res_plugin_path = join(plugin_path, "res")
emu_plugin = join(plugin_path, "emu")
iconpic = join(plugin_path, 'logo.png')
data_path = plugin_path + '/data'
dir_work = '/usr/lib/enigma2/python/Screens'
FILE_XML = join(plugin_path, 'Manager.xml')
FTP_CFG = 'http://nonsolosat.net/Manager/cfg.txt'
xmml = 'aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL2xldmktNDUvTXVsdGljYW0vbWFpbi9DYW1pbnN0YWxsZXIueG1s'
xlm = b64decoder(xmml)
local = True
ECM_INFO = "/tmp/ecm.info"
EMPTY_ECM_INFO = ("", "0", "0", "0")
old_ecm_time = time.time()
info = {}
ecm = ""
SOFTCAM = 0
CCCAMINFO = 1
OSCAMINFO = 2
AgentRequest = RequestAgent()
runningcam = None


headers = {
	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
	"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", "Accept-Encoding": "deflate"
}


try:
	wgetsts()
except:
	pass


def install_package():
	try:
		check_cmd = ["opkg", "list-installed"]
		output = subprocess.check_output(check_cmd, stderr=subprocess.DEVNULL).decode("utf-8")

		if "libusb-1.0-0" in output:
			print("Package libusb-1.0-0 is already installed.")
			return

		print("Updating opkg...")
		subprocess.run(["opkg", "update"], check=True)

		print("Installing libusb-1.0-0...")
		subprocess.run(["opkg", "install", "libusb-1.0-0"], check=True)

		print("Installation completed.")

	except subprocess.CalledProcessError as e:
		print("Error executing opkg:", e)
	except Exception as e:
		print("Unexpected error:", e)


install_package()


def checkdir():
	keys = "/usr/keys"
	camscript = "/usr/camscript"
	if not exists(keys):
		mkdir("/usr/keys")
	if not exists(camscript):
		mkdir("/usr/camscript")


checkdir()
screenwidth = getDesktop(0).size()
if screenwidth.width() == 2560:
	skin_path = plugin_path + "/res/skins/uhd/"
elif screenwidth.width() == 1920:
	skin_path = plugin_path + "/res/skins/fhd/"
else:
	skin_path = plugin_path + "/res/skins/hd/"
if exists("/usr/bin/apt-get"):
	skin_path = skin_path + "dreamOs/"

if not exists("/etc/clist.list"):
	with open("/etc/clist.list", "w"):
		print("/etc/clist.list as been create")
		system("chmod 755 /etc/clist.list")


class Manager(Screen):

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		global _session, runningcam
		runningcam = None
		_session = session
		skin = join(skin_path, 'Manager.xml')
		with codecs.open(skin, "r", encoding="utf-8") as f:
			self.skin = f.read()
		self.namelist = []
		self.softcamslist = []
		self.oldService = ""
		try:
			self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		except:
			self.oldService = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		self["NumberActions"] = NumberActionMap(
			["NumberActions"],
			{
				"0": self.keyNumberGlobal,
				"1": self.keyNumberGlobal,
				"2": self.keyNumberGlobal,
				"8": self.keyNumberGlobal
			},
		)
		self["actions"] = ActionMap(
			[
				"OkCancelActions",
				"ColorActions",
				"EPGSelectActions",
				"MenuActions"
			],
			{
				"ok": self.action,
				"cancel": self.close,
				"menu": self.configtv,
				"blue": self.Blue,
				"yellow": self.download,
				"green": self.action,
				"info": self.CfgInfo,
				"red": self.stop
			},
			-1
		)
		self.setTitle(_(title_plug))
		self["title"] = Label(_(title_plug))
		self["key_green"] = Label(_("Start"))
		self["key_yellow"] = Label(_("Cam Download"))
		self["key_red"] = Label(_("Stop"))
		self["key_blue"] = Label()
		self["key_blue"].setText("Softcam")
		self["description"] = Label(_("Scanning and retrieval list softcam ..."))
		self["info"] = Label()
		self["list"] = List([])
		self.curCam = None
		self.curCam = self.readCurrent()
		self.readScripts()
		self.BlueAction = "SOFTCAM"
		runningcam = "softcam"
		self.setBlueKey()
		self.timer = eTimer()
		try:
			self.timer_conn = self.timer.timeout.connect(self.cgdesc)
		except:
			self.timer.callback.append(self.cgdesc)
		self.timer.start(300, 1)
		self.EcmInfoPollTimer = eTimer()
		try:
			self.EcmInfoPollTimer_conn = self.EcmInfoPollTimer.timeout.connect(self.setEcmInfo)
		except:
			self.EcmInfoPollTimer.callback.append(self.setEcmInfo)
		self.EcmInfoPollTimer.start(200)
		self.onShown.append(self.ecm)
		self.onShown.append(self.setBlueKey)
		self.onHide.append(self.stopEcmInfoPollTimer)

	def setBlueKey(self):
		global runningcam
		self.curCam = self.readCurrent()
		self["key_blue"].setText("Softcam")
		self.BlueAction = None  # Default action
		if self.curCam is not None:
			cam_name = str(self.curCam).lower()
			print("cam_name=", cam_name)
			cam_info = {
				"oscam": ("OSCAMINFO", "OScamInfo"),
				"cccam": ("CCCAMINFO", "CCcamInfo"),
				"movicam": ("MOVICAMINFO", "OScamInfo"),
				"ncam": ("NCAMINFO", "NcamInfo")
			}
			for key, (action, file_name) in cam_info.items():
				if key in cam_name:
					print("%s detected in cam_name" % key)
					runningcam = key
					self.BlueAction = action
					self["key_blue"].setText(action)

					if exists(join(plugin_path, "data/%s.pyo" % file_name)) or exists(join(plugin_path, "data/%s.pyc" % file_name)):
						print("existe %s" % file_name)
					break
			# Debug info
			print("[setBlueKey] self.curCam=", self.curCam)
			print("[setBlueKey] self.BlueAction=", self.BlueAction)
			print("[setBlueKey] runningcam=", runningcam)
			print("[setBlueKey] file_name=", file_name)

	def Blue(self):
		print("[Blue] self.BlueAction:", self.BlueAction)
		cam_name = str(self.curCam).lower()
		print("cam_name=", cam_name)
		print("plugin_path + /data/=", plugin_path + "/data/")
		try:
			if "oscam" in str(self.curCam).lower():
				try:
					try:
						from Screens.OScamInfo import OSCamInfo
						print("[cccam 1] OScamInfo")
						self.session.open(OSCamInfo)
					except ImportError:
						from .data.OScamInfo import OSCamInfo
						print("[cccam 2] OScamInfo")
						self.session.open(OSCamInfo)
				except Exception as e:
					print("[cccam] OScamInfo e:", e)
					pass

			elif "ccam" in str(self.curCam).lower():
				try:

					from Screens.CCcamInfo import CCcamInfoMain
					print("[cccam 12] CCcamInfo")
					self.session.open(CCcamInfoMain)
				except ImportError:
					from .data.CCcamInfo import CCcamInfoMain
					print("[cccam 2] CCcamInfo")
					self.session.open(CCcamInfoMain)

			elif "ncam" in cam_name:
				try:
					try:
						from Screens.NcamInfo import NcamInfoMenu
					except ImportError:
						from .data.NcamInfo import NcamInfoMenu
					print("[Blue] Opening NcamInfo")
					self.session.open(NcamInfoMenu)
				except Exception as e:
					print("[Blue] Error in NcamInfo handling:", e)

			elif "movicam" in cam_name:
				try:
					try:
						from Screens.OScamInfo import OSCamInfo
					except ImportError:
						from .data.OScamInfo import OSCamInfo
					print("[Blue] Opening MovicamInfo (OScamInfo)")
					self.session.open(OSCamInfo)
				except Exception as e:
					print("[Blue] Error in MovicamInfo handling:", e)

			else:
				print("[Blue] Default action: CCcam")
				self.cccam()
		except Exception as e:
			print("[Blue] General Error:", e)

	def callbackx(self, call=None):
		print("call:", call)
		pass

	def open_plugin(self, screen_import, fallback_import, callback=None):
		"""
		Funzione generica per aprire un plugin con gestione dell"importazione.
		"""
		try:
			plugin_screen = __import__(screen_import, fromlist=[""])
			print("[open_plugin] Successfully imported:", screen_import)
		except ImportError:
			try:
				plugin_screen = __import__(fallback_import, fromlist=[""])
				print("[open_plugin] Fallback imported:", fallback_import)
			except ImportError as e:
				print("[open_plugin] ImportError:", e)
				self.session.open(
					MessageBox,
					_("Failed to load plugin: %s" % fallback_import),
					MessageBox.TYPE_ERROR,
					timeout=5
				)
				return

		if callback:
			print("[open_plugin] Opening with callback:", callback)
			self.session.openWithCallback(callback, plugin_screen)
		else:
			print("[open_plugin] Opening plugin:", plugin_screen)
			self.session.open(plugin_screen)

	def cccam(self):
		self.open_plugin(
			screen_import="Screens.CCcamInfo.CCcamInfoMain",
			fallback_import=".data.CCcamInfo.CCcamInfoMain"
		)

	def oscam(self):
		self.open_plugin(
			screen_import="Screens.OScamInfo.OSCamInfo",
			fallback_import=".data.OScamInfo.OSCamInfo"
		)

	def ncam(self):
		self.open_plugin(
			screen_import="Screens.NcamInfo.NcamInfoMenu",
			fallback_import=".data.NcamInfo.NcamInfoMenu"
		)

	def keyNumberGlobal(self, number):
		print("pressed", number)
		if number == 0:
			self.messagekd()
		elif number == 1:
			self.cccam()
		elif number == 2:
			self.oscam()
		elif number == 3:
			self.ncam()
		else:
			return

	def setEcmInfo(self):
		try:
			self.ecminfo = GetEcmInfo()
			newEcmFound, ecmInfo = self.ecminfo.getEcm()
			if newEcmFound:
				self["info"].setText("".join(ecmInfo))
			else:
				self.ecm()
		except Exception as e:
			print(e)

	def ecm(self):
		try:
			ecmf = ""
			if exists(ECM_INFO):
				try:
					with open(ECM_INFO) as f:
						self["info"].text = f.read()
				except IOError:
					pass
			else:
				self["info"].setText(ecmf)
		except Exception as e:
			print("error ecm: ", e)

	def stopEcmInfoPollTimer(self):
		self.EcmInfoPollTimer.stop()

	def messagekd(self):
		self.session.openWithCallback(self.keysdownload, MessageBox, _("Update SoftcamKeys from google search?"), MessageBox.TYPE_YESNO)

	def keysdownload(self, result):
		if result:
			script = join(plugin_path, "auto")
			if not access(script, X_OK):
				chmod(script, 493)
			if exists("/usr/keys/SoftCam.Key"):
				system("rm -rf /usr/keys/SoftCam.Key")
			# self.session.open(MessageBox, _("SoftcamKeys Updated!"), MessageBox.TYPE_INFO, timeout=5)
			cmd = script
			title = _("Installing Softcam Keys\nPlease Wait...")
			self.session.open(Console, _(title), [cmd], closeOnSuccess=False)

	def CfgInfo(self):
		self.session.open(nssInfoCfg)

	def configtv(self):
		from Plugins.Extensions.tvManager.data.datas import tv_config
		self.session.open(tv_config)

	def cgdesc(self):
		if len(self.namelist) >= 1:
			self["description"].setText(_("Select a cam to run ..."))
		else:
			self["description"].setText(_("Install Cam first!!!"))
			self.updateList()

	def getcont(self):
		cont = "Your Config:\n"
		arc = ""
		arkFull = ""
		libsssl = ""
		python = popen("python -V").read().strip("\n\r")
		arcx = popen("uname -m").read().strip("\n\r")
		libs = popen("ls -l /usr/lib/libss*.*").read().strip("\n\r")
		if arcx:
			arc = arcx
			print("arc= ", arc)
		if self.arckget():
			print("arkget= ", arkFull)
			arkFull = self.arckget()
		if libs:
			libsssl = libs
		cont += " ------------------------------------------ \n"
		cont += "Cpu: %s\nArchitecture info: %s\nPython V.%s\nLibssl(oscam):\n%s" % (arc, arkFull, python, libsssl)
		cont += " ------------------------------------------ \n"
		cont += "Button Info for Other Info\n"
		return cont

	def arckget(self):
		zarcffll = "by Lululla"
		try:
			if exists("/usr/bin/apt-get"):
				zarcffll = popen("dpkg --print-architecture | grep -iE 'arm|aarch64|mips|cortex|sh4|sh_4'").read().strip("\n\r")
			else:
				zarcffll = popen("opkg print-architecture | grep -iE 'arm|aarch64|mips|cortex|h4|sh_4'").read().strip("\n\r")
			return str(zarcffll)
		except Exception as e:
			print("Error ", e)

	def updateList(self):
		poPup = self.getcont()
		_session.open(MessageBox, poPup, MessageBox.TYPE_INFO, timeout=10)

	def openTest(self):
		pass

	def download(self):
		self.session.open(nssGetipk)
		self.onShown.append(self.readScripts)

	def getLastIndex(self):
		a = 0
		if len(self.namelist) >= 0:
			for x in self.namelist[0]:
				if x == self.curCam:
					return a
				a += 1
				print("aa=", a)
		# else:
			# return -1
		# return -1

	def action(self):
		i = len(self.softcamslist)
		if i < 1:
			return
		try:
			self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		except:
			self.oldService = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		self.session.nav.stopService()
		self.last = self.getLastIndex()
		if self["list"].getCurrent():
			self.var = self["list"].getIndex()
			"""
			# self.var = self["list"].getSelectedIndex()
			# # self.var = self["list"].getSelectionIndex()
			print("self var=== ", self.var)
			"""
			system("chmod 755 /usr/camscript/*.*")
			curCam = self.readCurrent()
			if self.last is not None:
				try:
					foldcurr = "/usr/bin/" + str(curCam)
					foldscrpt = "/usr/camscript/" + str(curCam) + ".sh"
					chmod(foldcurr, 0o755)
					chmod(foldscrpt, 0o755)
				except OSError:
					pass

				if self.last == self.var:
					self.cmd1 = "/usr/camscript/" + self.softcamslist[self.var][0] + ".sh" + " cam_res &"
					_session.open(MessageBox, _("Please wait..\nRESTART CAM"), MessageBox.TYPE_INFO, timeout=5)
					system(self.cmd1)
					sleep(1)
				else:
					self.cmd1 = "/usr/camscript/" + self.softcamslist[self.last][0] + ".sh" + " cam_down &"
					_session.open(MessageBox, _("Please wait..\nSTOP & RESTART CAM"), MessageBox.TYPE_INFO, timeout=5)
					system(self.cmd1)
					sleep(1)
					self.cmd1 = "/usr/camscript/" + self.softcamslist[self.var][0] + ".sh" + " cam_up &"
					system(self.cmd1)
			else:
				try:
					self.cmd1 = "/usr/camscript/" + self.softcamslist[self.var][0] + ".sh" + " cam_up &"
					_session.open(MessageBox, _("Please wait..\nSTART UP CAM"), MessageBox.TYPE_INFO, timeout=5)
					system(self.cmd1)
					sleep(1)
				except:
					self.close()
			if self.last != self.var:
				try:
					self.curCam = self.softcamslist[self.var][0]
					self.writeFile()
				except:
					self.close()
		self.session.nav.playService(self.oldService)
		self.EcmInfoPollTimer.start(200)
		self.readScripts()

	def writeFile(self):
		if self.curCam != "" or self.curCam is not None:
			print("self.curCam= 2 ", self.curCam)
			if sys.version_info[0] == 3:
				clist = open("/etc/clist.list", "w", encoding="UTF-8")
			else:
				clist = open("/etc/clist.list", "w")
			chmod("/etc/clist.list", 755)
			clist.write(str(self.curCam))
			clist.close()

		if sys.version_info[0] == 3:
			stcam = open("/etc/startcam.sh", "w", encoding="UTF-8")
		else:
			stcam = open("/etc/startcam.sh", "w")
		stcam.write("#!/bin/sh\n" + self.cmd1)
		stcam.close()
		chmod("/etc/startcam.sh", 755)
		return

	def stop(self):
		i = len(self.softcamslist)
		if i < 1:
			return
		global runningcam
		try:
			self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		except:
			self.oldService = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		self.session.nav.stopService()
		if self.curCam != "None" or self.curCam is not None:
			self.EcmInfoPollTimer.stop()
			self.last = self.getLastIndex()
			if self.last is not None:  # or self.curCam != "no":
				self.cmd1 = "/usr/camscript/" + self.softcamslist[self.last][0] + ".sh" + " cam_down &"
				system(self.cmd1)
				self.curCam = None
				self.writeFile()
				sleep(1)
				if exists(ECM_INFO):
					remove(ECM_INFO)
				_session.open(MessageBox, _("Please wait..\nSTOP CAM"), MessageBox.TYPE_INFO, timeout=5)
				self["info"].setText("CAM STOPPED")
				self.BlueAction = "SOFTCAM"
				runningcam = "softcam"
				self.readScripts()
		self.session.nav.playService(self.oldService)

	def readScripts(self):
		try:
			scriptlist = []
			pliste = []
			self.index = 0
			s = 0
			pathscript = "/usr/camscript/"
			for root, dirs, files in walk(pathscript):
				for name in files:
					scriptlist.append(name)
					s += 1
			i = len(self.softcamslist)
			del self.softcamslist[0:i]
			png1 = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/tvManager/res/img/{}".format("actcam.png")))
			png2 = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/tvManager/res/img/{}".format("defcam.png")))
			if s >= 1:
				for lines in scriptlist:
					dat = pathscript + lines
					if sys.version_info[0] == 3:
						sfile = open(dat, "r", encoding="UTF-8")
					else:
						sfile = open(dat, "r")
					for line in sfile:
						if line[0:3] == "OSD":
							nam = line[5:len(line) - 2]
							print("We are in Manager and cam is type  = ", nam)
							if self.curCam != "None" or self.curCam is not None:
								if nam == self.curCam:
									self.softcamslist.append((nam,  png1, "(Active)"))
									pliste.append((nam, "(Active)"))
								else:
									self.softcamslist.append((nam, png2, ""))
									pliste.append((nam, ""))
							else:
								self.softcamslist.append(nam, png2, "")
								pliste.append(nam, "")
							self.index += 1
				sfile.close()
				self.softcamslist.sort(key=lambda i: i[2], reverse=True)
				pliste.sort(key=lambda i: i[1], reverse=True)
				self.namelist = pliste
				print("self.namelist:", self.namelist)
				self["list"].setList(self.softcamslist)
			self.setBlueKey()
		except Exception as e:
			print("error scriptlist: ", e)

	def readCurrent(self):
		currCam = None
		self.FilCurr = ""
		if exists("/etc/CurrentBhCamName"):
			self.FilCurr = "/etc/CurrentBhCamName"
		else:
			self.FilCurr = "/etc/clist.list"
		if stat(self.FilCurr).st_size > 0:
			try:
				if sys.version_info[0] == 3:
					clist = open(self.FilCurr, "r", encoding="UTF-8")
				else:
					clist = open(self.FilCurr, "r")
			except:
				return
			if clist is not None:
				for line in clist:
					currCam = line
				clist.close()
		return currCam

	"""
	def autocam(self):
		current = None
		try:
			# clist = open("/etc/clist.list", "r")
			if sys.version_info[0] == 3:
				clist = open("/etc/clist.list", "r", encoding="UTF-8")
			else:
				clist = open("/etc/clist.list", "r")
			print("found list")
		except:
			return

		if clist is not None:
			for line in clist:
				current = line
			clist.close()
		print("current =", current)
		if os.path.isfile("/etc/autocam.txt") is False:
			if sys.version_info[0] == 3:
				alist = open("/etc/autocam.txt", "w", encoding="UTF-8")
			else:
				alist = open("/etc/autocam.txt", "w")
			alist.close()
		self.cleanauto()
		if sys.version_info[0] == 3:
			alist = open("/etc/autocam.txt", "a", encoding="UTF-8")
		else:
			alist = open("/etc/autocam.txt", "a")
		alist.write(self.oldService.toString() + "\n")
		# last = self.getLastIndex()
		alist.write(current + "\n")
		alist.close()
		self.session.openWithCallback(self.callback, MessageBox, _("Autocam assigned to the current channel"), type=1, timeout=10)
		return

	def cleanauto(self):
		delemu = "no"
		if os.path.isfile("/etc/autocam.txt") is False:
			return
		if sys.version_info[0] == 3:
			myfile = open("/etc/autocam.txt", "r", encoding="UTF-8")
		else:
			myfile = open("/etc/autocam.txt", "r")

		if sys.version_info[0] == 3:
			myfile2 = open("/etc/autocam2.txt", "w", encoding="UTF-8")
		else:
			myfile2 = open("/etc/autocam2.txt", "w")
		icount = 0
		for line in myfile.readlines():
			if line[:-1] == self.oldService.toString():
				delemu = "yes"
				icount = icount + 1
				continue
			if delemu == "yes":
				delemu = "no"
				icount = icount + 1
				continue
			myfile2.write(line)
			icount = icount + 1
		myfile.close()
		myfile2.close()
		system("rm /etc/autocam.txt")
		system("cp /etc/autocam2.txt /etc/autocam.txt")
		"""

	def cancel(self):
		self.close()


class nssGetipk(Screen):

	def __init__(self, session):
		self.session = session
		skin = join(skin_path, 'nssGetipklist.xml')
		with codecs.open(skin, "r", encoding="utf-8") as f:
			self.skin = f.read()
		Screen.__init__(self, session)
		self.names = []
		self.names_1 = []
		self.list = []
		self["list"] = MenuList([])
		self.setTitle(_(title_plug))
		self["title"] = Label(_(title_plug))
		self["description"] = Label(_("Getting the list, please wait ..."))
		self["key_red"] = Button(_("Back"))
		self["key_green"] = Button(_("Load"))
		self["key_yellow"] = Button()
		self["key_blue"] = Button()
		self["key_green"].hide()
		if exists(FILE_XML):
			self["key_green"].show()
		self["key_yellow"].hide()
		self["key_blue"].hide()
		self.addon = "emu"
		self.url = ""
		global local
		local = False
		self.icount = 0
		self.downloading = False
		self.timer = eTimer()
		if exists("/usr/bin/apt-get"):
			self.timer_conn = self.timer.timeout.connect(self._gotPageLoad)
		else:
			self.timer.callback.append(self._gotPageLoad)
		self.timer.start(500, 1)
		self["actions"] = ActionMap(
			[
				"OkCancelActions",
				"ColorActions"
			],
			{
				"ok": self.okClicked,
				"cancel": self.close,
				"green": self.loadpage,
				"red": self.close
			},
			-1
		)
		self.onShown.append(self.pasx)

	def pasx(self):
		pass

	def loadpage(self):
		global local
		if exists(FILE_XML):
			self.lists = []
			del self.names[:]
			del self.list[:]
			self["list"].l.setList(self.list)
			with open(FILE_XML, "r") as f:
				self.xml = f.read()
				local = True
			self._gotPageLoad()

	def _gotPageLoad(self):
		global local
		self.xml = "https://raw.githubusercontent.com/levi-45/Multicam/main/Caminstaller.xml"
		if PY3:
			self.xml = self.xml.encode()
		if local is False:
			if exists("/usr/bin/apt-get"):
				print("have a dreamOs!!!")
				self.data = checkGZIP(self.xml)
				self.downloadxmlpage(self.data)
			else:
				print("have a Atv-PLi - etc..!!!")
				getPage(self.xml).addCallback(self.downloadxmlpage).addErrback(self.errorLoad)

	def downloadxmlpage(self, data):
		self.xml = data
		self.list = []
		self.names = []
		try:
			if self.xml:
				self.xmlparse = minidom.parseString(self.xml)
				for plugins in self.xmlparse.getElementsByTagName("plugins"):
					if not exists("/usr/bin/apt-get"):
						if "deb" in str(plugins.getAttribute("cont")).lower():
							continue

					if exists("/usr/bin/apt-get"):
						if "deb" not in str(plugins.getAttribute("cont")).lower():
							continue
					self.names.append(str(plugins.getAttribute("cont")))
				# self["list"].l.setItemHeight(50)
				self["list"].l.setList(self.names)
				self["description"].setText(_("Please select ..."))
				self.downloading = True

		except Exception as e:
			print("error:", e)
			self["description"].setText(_("Error processing server addons data"))

	def errorLoad(self, error):
		print(str(error))
		self["description"].setText(_("Try again later ..."))
		self.downloading = False

	def okClicked(self):
		try:
			if self.downloading is True:
				selection = str(self["list"].getCurrent())
				self.session.open(nssGetipklist, self.xmlparse, selection)
			else:
				self.close()
		except:
			return


class nssGetipklist(Screen):
	def __init__(self, session, xmlparse, selection):
		Screen.__init__(self, session)
		self.session = session
		skin = join(skin_path, "nssGetipklist.xml")
		with codecs.open(skin, "r", encoding="utf-8") as f:
			self.skin = f.read()
		self.xmlparse = xmlparse
		self.selection = selection
		self.list = []
		adlist = []
		for plugins in self.xmlparse.getElementsByTagName("plugins"):
			if str(plugins.getAttribute("cont")) == self.selection:
				for plugin in plugins.getElementsByTagName("plugin"):
					adlist.append(str(plugin.getAttribute("name")))
				continue
		adlist.sort()
		self["list"] = MenuList(adlist)
		self.setTitle(_(title_plug))
		self["title"] = Label(_(title_plug))
		self["description"] = Label(_("Select and Install"))
		self["key_red"] = Button(_("Back"))
		self["key_green"] = Button("Remove")
		self["key_yellow"] = Button("Restart")
		self["key_blue"] = Button()
		self["key_green"].hide()
		# self["key_yellow"].hide()
		self["key_blue"].hide()
		self["actions"] = ActionMap(
			[
				"OkCancelActions",
				"ColorActions"
			],
			{
				"ok": self.message,
				"cancel": self.close,
				"green": self.remove,
				"yellow": self.restart
			},
			-1
		)
		self.onLayoutFinish.append(self.start)

	def start(self):
		pass

	def message(self):
		self.session.openWithCallback(self.selclicked, MessageBox, _("Do you install this plugin ?"), MessageBox.TYPE_YESNO)

	def selclicked(self, result):
		if result:
			try:
				selection_country = self["list"].getCurrent()
				for plugins in self.xmlparse.getElementsByTagName("plugins"):
					if str(plugins.getAttribute("cont")) == self.selection:
						for plugin in plugins.getElementsByTagName("plugin"):
							if str(plugin.getAttribute("name")) == selection_country:
								self.com = str(plugin.getElementsByTagName("url")[0].childNodes[0].data)
								self.dom = str(plugin.getAttribute("name"))
								# test lululla
								self.com = self.com.replace('"', "")
								if ".deb" in self.com:
									if not exists("/usr/bin/apt-get"):
										self.session.open(MessageBox, _("Unknow Image!"), MessageBox.TYPE_INFO, timeout=5)
										return
									n2 = self.com.find("_", 0)
									self.dom = self.com[:n2]

								if ".ipk" in self.com:
									if exists("/usr/bin/apt-get"):
										self.session.open(MessageBox, _("Unknow Image!"), MessageBox.TYPE_INFO, timeout=5)
										return
									n2 = self.com.find("_", 0)
									self.dom = self.com[:n2]
								elif ".zip" in self.com:
									self.dom = self.com
								elif ".tar" in self.com or ".gz" in self.com or "bz2" in self.com:
									self.dom = self.com
								print("self.prombt self.com: ", self.com)
								self.prombt()
							else:
								print("Return from prompt ")
								self["description"].setText("Select")
							continue
			except Exception as e:
				print("error prompt ", e)
				self["description"].setText("Error")
				return

	def prombt(self):
		self.plug = self.com.split("/")[-1]
		dest = "/tmp"
		if not exists(dest):
			system("ln -sf  /var/volatile/tmp /tmp")
		self.folddest = "/tmp/" + self.plug
		cmd2 = ""
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
		cmd = cmd2
		cmd00 = "wget --no-check-certificate -U '%s' -c '%s' -O '%s';%s > /dev/null" % (AgentRequest, str(self.com), self.folddest, cmd)
		print("cmd00:", cmd00)
		title = (_("Installing %s\nPlease Wait...") % self.dom)
		self.session.open(Console, _(title), [cmd00], closeOnSuccess=False)

	def remove(self):
		self.session.openWithCallback(self.removenow, MessageBox, _("Do you want to remove?"), MessageBox.TYPE_YESNO)

	def removenow(self, answer=False):
		if answer:
			selection_country = self["list"].getCurrent()
			for plugins in self.xmlparse.getElementsByTagName("plugins"):
				if str(plugins.getAttribute("cont")) == self.selection:
					for plugin in plugins.getElementsByTagName("plugin"):
						if str(plugin.getAttribute("name")) == selection_country:
							self.com = str(plugin.getElementsByTagName("url")[0].childNodes[0].data)
							self.dom = str(plugin.getAttribute("name"))
							# test lululla
							self.com = self.com.replace('"', "")
							cmd = ""

							if ".deb" in self.com:
								if not exists("/usr/bin/apt-get"):
									self.session.open(MessageBox, _("Unknow Image!"), MessageBox.TYPE_INFO, timeout=5)
									return
								self.plug = self.com.split("/")[-1]
								n2 = self.plug.find("_", 0)
								self.dom = self.plug[:n2]
								cmd = "dpkg -r " + self.dom  # + """
								print("cmd deb remove:", cmd)
							if ".ipk" in self.com:
								if exists("/usr/bin/apt-get"):
									self.session.open(MessageBox, _("Unknow Image!"), MessageBox.TYPE_INFO, timeout=5)
									return
								self.plug = self.com.split("/")[-1]
								n2 = self.plug.find("_", 0)
								self.dom = self.plug[:n2]
								cmd = "opkg remove " + self.dom  # + """
								print("cmd ipk remove:", cmd)

							title = (_("Removing %s") % self.dom)
							self.session.open(Console, _(title), [cmd])

	def restart(self):
		self.session.openWithCallback(self.restartnow, MessageBox, _("Do you want to restart Gui Interface?"), MessageBox.TYPE_YESNO)

	def restartnow(self, answer=False):
		if answer:
			self.session.open(TryQuitMainloop, 3)


class nssInfoCfg(Screen):
	def __init__(self, session):
		self.session = session
		skin = join(skin_path, "nssInfoCfg.xml")
		with codecs.open(skin, "r", encoding="utf-8") as f:
			self.skin = f.read()
		Screen.__init__(self, session)
		self.list = []
		self.setTitle(_(title_plug))
		self["list"] = Label()
		self["actions"] = ActionMap(
			[
				'WizardActions',
				'OkCancelActions',
				'DirectionActions',
				'ColorActions'
			],
			{
				"ok": self.close,
				"back": self.close,
				"cancel": self.close,
				"red": self.close
			},
			-1
		)
		self["key_red"] = Button(_("Back"))
		self["key_green"] = Button()
		self["key_yellow"] = Button()
		self["key_blue"] = Button()
		self["key_green"].hide()
		self["key_yellow"].hide()
		self["key_blue"].hide()

		self["title"] = Label(_(title_plug))
		self["description"] = Label(_("Path Configuration Folder"))
		self.onShown.append(self.updateList)

	def getcont(self):
		cont = " ---- Type Cam For Your Box--- \n"
		cont += " ------------------------------------------ \n"
		cont += "/etc/CCcam.cfg -> CCcam\n"
		cont += "/etc/tuxbox/config/oscam.server -> Oscam\n"
		cont += "/etc/tuxbox/config/Oscamicam/oscam.server -> Oscamicam\n"
		cont += "/etc/tuxbox/config/oscam-emu/oscam.server -> oscam-emu\n"
		cont += "/etc/tuxbox/config/ncam.server -> Ncam\n"
		cont += "/etc/tuxbox/config/gcam.server -> Gcam\n"
		cont += " ------------------------------------------ \n"
		cont += "Config NSS Manager(Oscam):\n"
		arc = ""
		arkFull = ""
		libsssl = ""
		arcx = popen("uname -m").read().strip("\n\r")
		python = popen("python -V").read().strip("\n\r")
		libs = popen("ls -l /usr/lib/libss*.*").read().strip("\n\r")
		if arcx:
			arc = arcx
			print("arc= ", arc)
		if self.arckget():
			print("arkget= ", arkFull)
			arkFull = self.arckget()
		if libs:
			libsssl = libs
		cont += " ------------------------------------------ \n"
		cont += "Cpu: %s\nArchitecture info: %s\nPython V.%s\nLibssl(oscam):\n%s\n" % (arc, arkFull, python, libsssl)
		cont += " ------------------------------------------ \n"
		return cont

	def updateList(self):
		self["list"].setText(self.getcont())

	def arckget(self):
		zarcffll = "by Lululla"
		try:
			zarcffll = popen("opkg print-architecture | grep -iE 'arm|aarch64|mips|cortex|h4|sh_4'").read().strip("\n\r")
			return str(zarcffll)
		except Exception as e:
			print("Error ", e)

	def Down(self):
		self["list"].pageDown()

	def Up(self):
		self["list"].pageUp()


class DreamCCAuto:
	def __init__(self):
		self.readCurrent()

	def readCurrent(self):
		current = None
		self.FilCurr = "/etc/CurrentBhCamName" if exists("/etc/CurrentBhCamName") else "/etc/clist.list"
		try:
			with open(self.FilCurr, "r", encoding="UTF-8") as clist:
				for line in clist:
					current = line.strip()
		except Exception as e:
			print("Error reading current cam file:", e)
			return

		print("Current cam name:", current)

		scriptliste = []
		path = "/usr/camscript/"
		if not exists(path):
			print("Path does not exist:", path)
			return

		for root, dirs, files in walk(path):
			for name in files:
				scriptliste.append(name)

		for script in scriptliste:
			dat = join(path, script)
			try:
				with open(dat, "r") as file:
					for line in file:
						if line.startswith("OSD"):
							nam = line[5:].strip()
							if current == nam:
								if exists("/etc/init.d/dccamd"):
									system("mv /etc/init.d/dccamd /etc/init.d/dccamdOrig &")
								for link, target in [("/var/bin", "/usr/bin"), ("/var/keys", "/usr/keys"), ("/var/scce", "/usr/scce"), ("/var/script", "/usr/script")]:
									if not islink(link):
										system("ln -sf %s %s" % (target, link))
								if system("/etc/startcam.sh") != 0:
									print("Error starting the cam with /etc/startcam.sh")
								else:
									print("*** running autostart ***")
								return
			except Exception as e:
				print("Error reading script file:", e)

		print("pass autostart")
		return


def autostartsoftcam(reason, session=None, **kwargs):
	print("[Softcam] Started")
	if reason == 0 and session is not None:
		print("reason 0")
		try:
			if exists("/etc/init.d/dccamd"):
				system("mv /etc/init.d/dccamd /etc/init.d/dccamdOrig &")
			DreamCCAuto()
		except Exception as e:
			print("Error during autostart:", e)


def main(session, **kwargs):
	try:
		session.open(Manager)
	except:
		import traceback
		traceback.print_exc()
		pass


def StartSetup(menuid, **kwargs):
	return [(name_plug, main, 'NSS Cam  Manager', 44)] if menuid == "mainmenu" else []


def startConfig(session, **kwargs):
	session.open(Manager)


def mainmenu(menuid):
	if menuid != 'setup':
		return []
	else:
		return [(_('NSS Cam Manager'),
				 startConfig,
				 'NSS Cam Manager',
				 None)]


def Plugins(**kwargs):
	iconpic = "logo.png"
	return [
		PluginDescriptor(
			name=_(name_plug),
			where=PluginDescriptor.WHERE_MENU,
			fnc=mainmenu,
		),
		PluginDescriptor(
			name=_(name_plug),
			description=_(title_plug),
			where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART],
			needsRestart=True,
			fnc=autostartsoftcam,
		),
		PluginDescriptor(
			name=_(name_plug),
			description=_(title_plug),
			where=PluginDescriptor.WHERE_PLUGINMENU,
			icon=iconpic,
			fnc=main,
		),
		PluginDescriptor(
			name=_(name_plug),
			description=_(title_plug),
			where=PluginDescriptor.WHERE_EXTENSIONSMENU,
			fnc=main,
		),
	]
