import os
import sys
import json
import codecs
import xml.etree.ElementTree as etree
from html.parser import HTMLParser
import xbmcgui
import xbmcaddon
from kodilanguages import *

ADDON = xbmcaddon.Addon()
ADDONID = ADDON.getAddonInfo('id')
ADDONNAME = ADDON.getAddonInfo('name')
LANGUAGE = ADDON.getLocalizedString


def log(txt):
    message = '%s: %s' % (ADDONID, txt)
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

class Main:
    def __init__(self):
        addon, path = self.getAddon()
        if not path:
            return
        name, addonid, author = self.updateAddonXML(path)
        langpath, folders = self.getFolders(path, addonid)
        if not folders:
            return
        self.updateFiles(langpath, folders, name, addonid, author)
        self.updateFolders(langpath, folders)
        xbmcgui.Dialog().ok(ADDONNAME, LANGUAGE(30002))

    def getAddon(self):
        json_query = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Addons.GetAddons", "params":{"properties":["enabled"]}, "id":1}')
        json_response = json.loads(json_query)
        addons = []
        for item in json_response['result']['addons']:
             if item['enabled']:
                 addons.append(item['addonid'])
        addonlist = sorted(addons)
        dialog = xbmcgui.Dialog()
        addon = dialog.select(LANGUAGE(30001), addonlist)
        if addon != -1:
            path = xbmcaddon.Addon(addonlist[addon]).getAddonInfo('path') 
            return addon, path
        else:
            return None, None

    def updateAddonXML(self, path):
        fileToSearch = os.path.join(path, 'addon.xml')
        with codecs.open(fileToSearch, 'r', encoding='utf-8') as addonxml:
            filedata = addonxml.read()
        data = etree.parse(fileToSearch).getroot()
        name = data.get('name')
        addonid = data.get('id')
        author = data.get('provider-name')
        for line in data.iter('summary'):
            cur = line.get('lang')
            if cur in LANGUAGE_ISO:
                line.set('lang', LANGUAGE_ISO[cur])
        for line in data.iter('description'):
            cur = line.get('lang')
            if cur in LANGUAGE_ISO:
                line.set('lang', LANGUAGE_ISO[cur])
        for line in data.iter('disclaimer'):
            cur = line.get('lang')
            if cur in LANGUAGE_ISO:
                line.set('lang', LANGUAGE_ISO[cur])
        header = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        content = header + etree.tostring(data, encoding="unicode")
        with codecs.open(fileToSearch, 'w', encoding='utf-8') as addonxml:
            addonxml.write(content)
        return name, addonid, author

    def getFolders(self, path, addonid):
        if addonid.startswith('skin.'):
            langpath = os.path.join(path, "language")
        else:
            langpath = os.path.join(path, "resources", "language")
        if os.path.isdir(langpath):
            folders = next(os.walk(langpath))[1]
            for folder in folders:
                if folder not in LANGUAGE_NAMES and not folder.startswith('resource'):
                    log('language "%s" is not supported by Kodi, removing this folder' % folder)
                    xmlfile = os.path.join(langpath, folder, 'strings.xml')
                    pofile = os.path.join(langpath, folder, 'strings.po')
                    if os.path.exists(xmlfile):
                        os.remove(xmlfile)
                    if os.path.exists(pofile):
                        os.remove(pofile)
                    os.rmdir(os.path.join(langpath, folder))
                    folders.remove(folder)
            return langpath, folders

    def updateFiles(self, langpath, folders, name, addonid, author):
        parse = HTMLParser()
        comment = '# Kodi Media Center language file\n# Addon Name: %s\n# Addon id: %s\n# Addon Provider: %s\n' % (name, addonid, author)
        header = 'msgid ""\nmsgstr ""\n'
        header += '"Project-Id-Version: Kodi Addons\\n"\n'
        header += '"Report-Msgid-Bugs-To: https://forum.kodi.tv/\\n"\n'
        header += '"POT-Creation-Date: YEAR-MO-DA HO:MI+ZONE\\n"\n'
        header += '"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"\n'
        header += '"Last-Translator: Kodi Translation Team\\n"\n'
        header += '"Language-Team: Team-Kodi\\n"\n'
        header += '"MIME-Version: 1.0\\n"\n'
        header += '"Content-Type: text/plain; charset=UTF-8\\n"\n'
        header += '"Content-Transfer-Encoding: 8bit\\n"\n'
        header += '"Language: %s\\n"\n'
        header += '"Plural-Forms: %s\\n"\n\n'
        engFile = os.path.join(langpath, "English", "strings.xml")
        if os.path.exists(engFile):
            root = etree.parse(engFile).getroot()
            strings = root.findall('string')
            engDict = {}
            for string in strings:
                if not string.text:
                    continue
                sid = string.get("id")
                text = parse.unescape(string.text)
                engDict[sid] = text
            locale = LANGUAGE_NAMES["English"]
            plural = PLURAL_HEADERS["English"]
            newText = comment + header % (locale, plural)
            for k in sorted(engDict):
                newText = newText + 'msgctxt "#' + k + '"\n' + 'msgid "' + engDict[k] + '"\nmsgstr ""\n\n'
            newFile = os.path.join(langpath, "English", "strings.po")
            with codecs.open(newFile, 'w') as f:
                f.write(newText)
            os.remove(engFile)
            for folder in folders:
                if folder != 'English' and not folder.startswith('resource'):
                    langFile = os.path.join(langpath, folder, "strings.xml")
                    root = etree.parse(langFile).getroot()
                    strings = root.findall('string')
                    strDict = {}
                    for string in strings:
                        sid = string.get("id")
                        text = parse.unescape(string.text)
                        strDict[sid] = text
                    locale = LANGUAGE_NAMES[folder]
                    plural = PLURAL_HEADERS[folder]
                    newText = comment + header % (locale, plural)
                    for k in sorted(strDict):
                        if k in engDict:
                            newText = newText + 'msgctxt "#' + k + '"\n' + 'msgid "' + engDict[k] + '"\nmsgstr "' + strDict[k] + '"\n\n'
                    newFile = os.path.join(langpath, folder, "strings.po")
                    with codecs.open(newFile, 'w') as f:
                        f.write(newText)
                    os.remove(langFile)

    def updateFolders(self, langpath, folders):
        for folder in folders:
            if not folder.startswith('resource'):
                locale = LANGUAGE_NAMES[folder]
                oldpath = os.path.join(langpath, folder)
                newpath = os.path.join(langpath, "resource.language." + locale.lower())
                os.rename(oldpath, newpath)


if (__name__ == '__main__'):
    Main()
