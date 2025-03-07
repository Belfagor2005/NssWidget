# -*- coding: utf-8 -*-

from __future__ import absolute_import
__author__ = "Lululla"
__email__ = "ekekaz@gmail.com"
__copyright__ = 'Copyright (c) 2024 Lululla'
__license__ = "GPL-v2"
__version__ = "1.0.0"

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext
import os


PluginLanguageDomain = 'nssaddon'
PluginLanguagePath = 'Extensions/nssaddon/locale'


def wgetsts():
	wgetsts = False
	cmd22 = 'find /usr/bin -name "wget"'
	res = os.popen(cmd22).read()
	if 'wget' not in res.lower():
		if os.path.exists("/var/lib/dpkg/status"):
			cmd23 = 'apt-get update && apt-get install wget'
			os.popen(cmd23)
			wgetsts = True
		else:
			cmd23 = 'opkg update && opkg install wget'
			os.popen(cmd23)
			wgetsts = True
		return wgetsts


isDreamOS = False
if os.path.exists("/usr/bin/apt-get"):
	isDreamOS = True


def localeInit():
	if isDreamOS:
		lang = language.getLanguage()[:2]
		os.environ["LANGUAGE"] = lang
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


if isDreamOS:
	def _(txt):
		return gettext.dgettext(PluginLanguageDomain, txt) if txt else ""
else:
	def _(txt):
		translated = gettext.dgettext(PluginLanguageDomain, txt)
		if translated:
			return translated
		else:
			print(("[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt)))
			return gettext.gettext(txt)

localeInit()
language.addCallback(localeInit)


# linuxsat panel
epk = 'https://github.com/Belfagor2005/upload/raw/main/fill/addons_2024.xml'
Host = 'https://www.nonsolosat.net'
pblk = 'aHR0cHM6Ly93d3cubWVkaWFmaXJlLmNvbS9hcGkvMS41L2ZvbGRlci9nZXRfY29udGVudC5waHA/Zm9sZGVyX2tleT1vdnowNG1ycHpvOXB3JmNvbnRlbnRfdHlwZT1mb2xkZXJzJmNodW5rX3NpemU9MTAwMCZyZXNwb25zZV9mb3JtYXQ9anNvbg== '
ptrs = 'aHR0cHM6Ly93d3cubWVkaWFmaXJlLmNvbS9hcGkvMS41L2ZvbGRlci9nZXRfY29udGVudC5waHA/Zm9sZGVyX2tleT10dmJkczU5eTlocjE5JmNvbnRlbnRfdHlwZT1mb2xkZXJzJmNodW5rX3NpemU9MTAwMCZyZXNwb25zZV9mb3JtYXQ9anNvbg== '
ptmov = 'aHR0cHM6Ly93d3cubWVkaWFmaXJlLmNvbS9hcGkvMS41L2ZvbGRlci9nZXRfY29udGVudC5waHA/Zm9sZGVyX2tleT1uazh0NTIyYnY0OTA5JmNvbnRlbnRfdHlwZT1maWxlcyZjaHVua19zaXplPTEwMDAmcmVzcG9uc2VfZm9ybWF0PWpzb24= '
data_xml = 'aHR0cHM6Ly93d3cubm9uc29sb3NhdC5uZXQveG1sLw=='
