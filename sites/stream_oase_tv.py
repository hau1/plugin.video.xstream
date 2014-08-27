# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.util import cUtil
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
import logger
from ParameterHandler import *
from resources.lib.config import cConfig

    
SITE_IDENTIFIER = 'stream_oase_tv'
SITE_NAME = 'Stream-Oase.tv'
SITE_ICON = 'stream_oase_tv.png'

URL_MAIN = 'http://stream-oase.tv'
URL_HD_GENRE = 'http://stream-oase.tv/index.php/hd-oase'

def load():
    oGui = cGui()
    
    oGui.addFolder(cGuiElement('HD-Filme', SITE_IDENTIFIER, 'showGenres'))
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()
  
def showMovies():
    oParams = ParameterHandler()
    if oParams.getValue('siteUrl'):
        sUrl = URL_MAIN + oParams.getValue('siteUrl')     
    else:
        return  
    oGui = cGui()    
       
    oRequestHandler = cRequestHandler(sUrl)
    sHtmlContent = oRequestHandler.request()

    sPattern = '<div id="inner_content".*?<div class="clr">'
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, sPattern)
    if not aResult[0]:
        return
    # parse movie entries
    __parseMovieList(oGui, str(aResult[1][0]), oParams = oParams)
    # check for next site
    aResult = oParser.parse(sHtmlContent, 'href="([^"]+)" title="Weiter"')
    if aResult[0]:
        oParams = ParameterHandler()
        oParams.setParam('siteUrl',aResult[1][0])
        oGui.addNextPage(SITE_IDENTIFIER, 'showMovies', oParams)
    oGui.setView('movies')
    oGui.setEndOfDirectory()

def showGenres():
    oGui = cGui()
    oParams = ParameterHandler()
    
    oParams.setParam('siteUrl','/index.php/hd-oase/video/latest')
    oGuiElement = cGuiElement('Neuste', SITE_IDENTIFIER, 'showMovies')
    oGui.addFolder(oGuiElement, oParams)
    
    sUrl = URL_HD_GENRE
    oRequestHandler = cRequestHandler(sUrl)
    sHtmlContent = oRequestHandler.request()
    sPattern = '<div id="inner_content".*?<div class="clr">'
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, sPattern)
    if not aResult[0]:
        return
    sPattern = '<div class="avs_thumb".*?href="([^"]+)".*?<span class="name">(.*?)</span>'   
    aResult = oParser.parse(aResult[1][0], sPattern)
    if not aResult[0]:
        return
    sFunction = 'showMovies'
    iTotal = len(aResult[1])
    for aEntry in aResult[1]:
        sLabel = aEntry[1]
        sUrl = aEntry[0]
        oParams.setParam('siteUrl',sUrl)
        oGuiElement = cGuiElement(sLabel, SITE_IDENTIFIER, sFunction)
        oGui.addFolder(oGuiElement, oParams, iTotal = iTotal+1)
    oGui.setEndOfDirectory()

    
def showSearch():
    oGui = cGui()

    sSearchText = oGui.showKeyBoard()
    if (sSearchText != False and sSearchText != ''):
        _search(oGui, sSearchText)
    else:
        return
    oGui.setEndOfDirectory()
    
def _search(oGui, sSearchString):
    searchUrl = 'http://stream-oase.tv/index.php/component/allvideoshare/search'
    
    oRequest = cRequestHandler(searchUrl)
    oRequest.addParameters('avssearch',sSearchString)
    sHtml = oRequest.request()

    sPattern = '<div id="inner_content".*?<div class="clr">'
    oParser = cParser()
    aResult = oParser.parse(sHtml, sPattern)
    if not aResult[0]:
        return
    ###### parse entries
    __parseMovieList(oGui, str(aResult[1][0]))
    

def __parseMovieList(oGui, sHtml, oParams = False):
    if not oParams:
        oParams = ParameterHandler()
    sPattern = '<div class="avs_thumb".*?href="([^"]+)".*?class="image" src="([^"]+)".*?<span class="title">([^<]+)</span>'
    oParser = cParser()
    aResult = oParser.parse(sHtml, sPattern)
    if not aResult[0]:
        return
    sFunction = 'getHosters'
    iTotal = len(aResult[1])
    for aEntry in aResult[1]:
        sLabel = aEntry[2].split('(')
        sTitle = sLabel[0].strip()
        sNextUrl = aEntry[0]
        sThumb = aEntry[1] 
        oParams.setParam('siteUrl',sNextUrl)
        oParams.setParam('Title', sTitle)
        oGuiElement = cGuiElement(sTitle, SITE_IDENTIFIER, sFunction)
        oGuiElement.setThumbnail(sThumb)
        oGuiElement.setMediaType('movie')
        if len(sLabel)>1:
            year = sLabel[-1].replace(')','')
            oGuiElement.setYear(year)
        oGui.addFolder(oGuiElement, oParams, bIsFolder = False, iTotal = iTotal)
                
 

def __createInfo(oGui, sHtmlContent, sTitle):
    sPattern = '<div id="desc_spoiler">([^<]+)</div>.*?<img src="([^"]+)" alt="Cover"/>'
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, sPattern)
    
    if (aResult[0] == True):
        for aEntry in aResult[1]:
            sDescription = cUtil().unescape(aEntry[0].decode('utf-8')).encode('utf-8').strip()
            oGuiElement = cGuiElement('info (press Info Button)',SITE_IDENTIFIER,'dummyFolder')
            sMovieTitle = __getMovieTitle(sHtmlContent)
            oGuiElement.setDescription(sDescription)
            oGuiElement.setThumbnail(URL_MAIN+'/'+aEntry[1])
            oGui.addFolder(oGuiElement)

def dummyFolder():
    return


def getHosters():
    oParams = ParameterHandler()
    sTitle = oParams.getValue('Title')
    sUrl = oParams.getValue('siteUrl')   
    
    logger.info("%s: hosters for movie '%s' " % (SITE_IDENTIFIER, sTitle)) 
    
    oRequestHandler = cRequestHandler(URL_MAIN+sUrl)
    sHtmlContent = oRequestHandler.request();

    sPattern = '<iframe src="([^"]+)"'
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent.lower(), sPattern)
    hosters = []
    sFunction='getHosterUrl'
    if (aResult[0] == True):
        for aEntry in aResult[1]:
            hoster = {}
            hoster['link'] = aEntry
            # extract domain name
            temp = aEntry.split('//')
            temp = str(temp[-1]).split('/')
            temp = str(temp[0]).split('.')
            hoster['name'] = temp[-2]
            hosters.append(hoster)
    hosters.append(sFunction)
    return hosters
            

def getHosterUrl(sStreamUrl):
    results = []
    result = {}
    result['streamUrl'] = sStreamUrl
    result['resolved'] = False
    results.append(result)
    return results


