import os
import sys
import json
import codecs
import xml.etree.ElementTree as etree
import html
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
from kodilanguages import *

ADDON = xbmcaddon.Addon()
ADDONID = ADDON.getAddonInfo('id')
ADDONNAME = ADDON.getAddonInfo('name')
AUTHOR = ADDON.getAddonInfo('author')
LANGUAGE = ADDON.getLocalizedString
AUTHOR_FILTER = ADDON.getSetting('author_filter')


def log(txt):
    message = '%s: %s' % (ADDONID, txt)
    xbmc.log(msg=message, level=xbmc.LOGDINFO)

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
        xbmc.executebuiltin("SetGUILanguage(resource.language.en_gb, true)")
        xbmc.executebuiltin("SetGUILanguage(resource.language.de_de, true)")

    def getAddon(self):
        json_query = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Addons.GetAddons", "params":{"properties":["enabled", "author"]}, "id":1}')
        json_response = json.loads(json_query)
        addons = []
        for item in json_response['result']['addons']:
             if item['enabled'] == True and (AUTHOR_FILTER == "" or item['author'] in AUTHOR_FILTER):
                 xbmc.log('%s : Author: %s' % (item['addonid'], item['author']), level=xbmc.LOGINFO)
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
        #fileToWrite = os.path.join(path, 'new-addon.xml')
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
        #with codecs.open(fileToWrite, 'w', encoding='utf-8') as addonxml:
        #    addonxml.write(content)
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
                    log('language "%s" is not supported by Kodi, please remove this folder' % folder)
                    #xmlfile = os.path.join(langpath, folder, 'strings.xml')
                    #pofile = os.path.join(langpath, folder, 'strings.po')
                    #if os.path.exists(xmlfile):
                    #    os.remove(xmlfile)
                    #if os.path.exists(pofile):
                    #    os.remove(pofile)
                    #os.rmdir(os.path.join(langpath, folder))
                    folders.remove(folder)
            return langpath, folders

    def updateFiles(self, langpath, folders, name, addonid, author):
        # parse = HTMLParser()
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
                engDict[sid] = html.unescape(string.text).replace('"', "'")
            locale = LANGUAGE_NAMES["English"]
            plural = PLURAL_HEADERS["English"]
            newText = comment + header % (locale, plural)
            for k in sorted(engDict):
                newText = newText + 'msgctxt "#' + k + '"\n' + 'msgid "' + engDict[k] + '"\nmsgstr ""\n\n'
            newFile1 = os.path.join(langpath, "English", "strings.po")
            langpath2 = os.path.join(langpath, "resource.language." + locale.lower())
            if not xbmcvfs.exists(langpath2):
                xbmcvfs.mkdirs(langpath2)
            newFile2 = os.path.join(langpath2, "strings.po")
            with codecs.open(newFile1, mode='w', encoding='utf-8') as f1:
                f1.write(newText)
            with codecs.open(newFile2, mode='w', encoding='utf-8') as f2:
                f2.write(newText)
            #os.remove(engFile)
            for folder in folders:
                if folder != 'English' and not folder.startswith('resource'):
                    langFile = os.path.join(langpath, folder, "strings.xml")
                    root = etree.parse(langFile).getroot()
                    strings = root.findall('string')
                    strDict = {}
                    for string in strings:
                        sid = string.get("id")
                        strDict[sid] = html.unescape(string.text).replace('"', "'")
                    locale = LANGUAGE_NAMES[folder]
                    plural = PLURAL_HEADERS[folder]
                    newText = comment + header % (locale, plural)
                    for k in sorted(strDict):
                        if k in engDict:
                            newText = newText + 'msgctxt "#' + k + '"\n' + 'msgid "' + engDict[k] + '"\nmsgstr "' + strDict[k] + '"\n\n'
                    newFile1 = os.path.join(langpath, folder, "strings.po")
                    langpath2 = os.path.join(langpath, "resource.language." + locale.lower())
                    if not xbmcvfs.exists(langpath2):
                        xbmcvfs.mkdirs(langpath2)
                    newFile2 = os.path.join(langpath2, "strings.po")
                    with codecs.open(newFile1, mode='w', encoding='utf-8') as f1:
                        f1.write(newText)
                    with codecs.open(newFile2, mode='w', encoding='utf-8') as f2:
                        f2.write(newText)
                    #os.remove(langFile)

    def updateFolders(self, langpath, folders):
        return
        for folder in folders:
            if not folder.startswith('resource'):
                locale = LANGUAGE_NAMES[folder]
                oldpath = os.path.join(langpath, folder)
                newpath = os.path.join(langpath, "resource.language." + locale.lower())
                os.rename(oldpath, newpath)


if (__name__ == '__main__'):
    Main()
