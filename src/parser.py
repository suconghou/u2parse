from urlparse import parse_qsl
import json
import re
import req

baseURL = "https://www.youtube.com"
videoPageHost = baseURL + "/watch?v={}"
playerURL = "https://youtubei.googleapis.com/youtubei/v1/player?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"


class videoParser:
    def __init__(self, vid):
        self.parser = infoParser(vid)

    def info(self):
        return self.parser.parse()

    def infoPart(self, itag):
        info = self.parser.parse()
        streams = info.get("streams")
        if not streams:
            raise ValueError("not found streams")
        itagInfo = streams.get(itag)
        if not itagInfo:
            raise ValueError("itag {} not found".format(itag))
        return {
            'url': itagInfo.get('url')
        }


class infoParser():

    def __init__(self, vid):
        self.decipher = None
        try:
            self.playerParse(vid)
        except:
            self.pageParse(vid)

    def playerParse(self, vid):
        obj = {
            "videoId": vid,
            "context": {
                "client": {
                    "hl": "en",
                    "gl": "US",
                    "clientName": "ANDROID",
                    "clientVersion": "16.02"
                }
            }
        }
        body = json.dumps(obj)
        res = req.doPost(playerURL, vid, body, 7200)

        videoDetails, streamingData = self.extract(res)

        self.title = videoDetails["title"]
        self.videoDetails = videoDetails
        self.streamingData = streamingData

    def pageParse(self, vid):
        jsPath = ""
        videoPageData = req.fetch(videoPageHost.format(vid), 7200)
        arr = re.search(r'"jsUrl":"(\/s\/player.*?base.js)"', videoPageData)
        if arr:
            jsPath = arr.group(1)
            req.cache.set("jsPath", jsPath, 604800)

        arr = re.search(
            r'ytInitialPlayerResponse\s+=\s+(.*}{3,});', videoPageData)
        if not arr:
            raise ValueError("ytInitialPlayerResponse not found")

        videoDetails, streamingData = self.extract(arr.group(1))

        self.title = videoDetails["title"]
        self.videoDetails = videoDetails
        self.streamingData = streamingData
        if jsPath:
            self.jsPath = jsPath
            req.cache.set("jsPath", self.jsPath, 604800)
        else:
            self.jsPath = req.cache.get("jsPath")

    def extract(self, jsonStr):
        data = json.loads(jsonStr)
        if not data or not data.has_key("playabilityStatus"):
            raise ValueError("parse ytInitialPlayerResponse error")
        ps = data.get("playabilityStatus")
        s = ps.get("status")
        if s != "OK":
            reason = ps.get('reason') or s
            subreason = ps.get('errorScreen', {}).get(
                'playerErrorMessageRenderer', {}).get('subreason', {}).get('runs')
            if subreason and subreason[0]:
                reason += ' ' + subreason[0].get('text')
            raise ValueError(reason)

        if not data.has_key("streamingData") or not data.has_key("videoDetails"):
            raise ValueError("invalid ytInitialPlayerResponse")
        videoDetails = data.get('videoDetails')
        if not videoDetails.has_key("title"):
            raise ValueError("videoPageData error")
        return videoDetails, data.get('streamingData')

    def parse(self):
        info = {
            "id": self.videoDetails.get("videoId"),
            "title": self.title,
            "duration": self.videoDetails.get("lengthSeconds"),
            "author": self.videoDetails.get("author")
        }
        streams = {}
        for item in self.streamingData.get("formats", {}):
            itag = item.get("itag")
            s = {
                "quality": item.get("qualityLabel", item.get("quality")),
                "type": item.get("mimeType"),
                "itag": itag,
                "len": item.get("contentLength"),
                "url": self.buildURL(item)
            }
            streams[itag] = s

        for item in self.streamingData.get("adaptiveFormats", {}):
            itag = item.get("itag")
            s = {
                "quality": item.get("qualityLabel", item.get("quality")),
                "type": item.get("mimeType"),
                "itag": itag,
                "len": item.get("contentLength"),
                "initRange":   item.get("initRange", {}),
                "indexRange": item.get("indexRange", {}),
                "url": self.buildURL(item)
            }
            streams[itag] = s
        info['streams'] = streams
        return info

    def buildURL(self, item):
        url = item.get("url")
        if url:
            return url
        url = item.get("signatureCipher") or item.get("cipher")
        if not url:
            raise ValueError("not found signatureCipher or cipher")
        u = dict(parse_qsl(url))
        url = u.get("url")
        if not url:
            raise ValueError("can not parse url")
        return url+self.signature(u)

    def signature(self, u):
        sp = u.get("sp", "signature")
        if u.get("s"):
            if not self.decipher:
                if not self.jsPath:
                    raise ValueError("jsPath not found")
                bodystr = req.fetch(baseURL+self.jsPath, 604800)
                self.decipher = decipher(bodystr)
            sig = self.decipher.decode(u.get("s"))
            return "&{}={}".format(sp, sig)
        elif u.get("sig"):
            return "&{}={}".format(sp, u.get("sig"))
        else:
            raise ValueError("can not decode")


class decipher:
    '''
        https://github.com/rylio/ytdl/blob/master/signature.go
    '''

    def __init__(self, bodystr):
        objResult = re.search(r'var ([a-zA-Z_\$][a-zA-Z_0-9]*)=\{((?:(?:[a-zA-Z_\$][a-zA-Z_0-9]*:function\(a\)\{(?:return )?a\.reverse\(\)\}|[a-zA-Z_\$][a-zA-Z_0-9]*:function\(a,b\)\{return a\.slice\(b\)\}|[a-zA-Z_\$][a-zA-Z_0-9]*:function\(a,b\)\{a\.splice\(0,b\)\}|[a-zA-Z_\$][a-zA-Z_0-9]*:function\(a,b\)\{var c=a\[0\];a\[0\]=a\[b(?:%a\.length)?\];a\[b(?:%a\.length)?\]=c(?:;return a)?\}),?\n?)+)\};', bodystr)
        if not objResult:
            raise ValueError("objResult not match")
        funcResult = re.search(
            r'function(?: [a-zA-Z_\$][a-zA-Z_0-9]*)?\(a\)\{a=a\.split\(""\);\s*((?:(?:a=)?[a-zA-Z_\$][a-zA-Z_0-9]*\.[a-zA-Z_\$][a-zA-Z_0-9]*\(a,\d+\);)+)return a\.join\(""\)\}', bodystr)
        if not funcResult:
            raise ValueError("funcResult not match")
        obj = objResult.group(1).replace('$', '\\$')
        objBody = objResult.group(2).replace('$', '\\$')
        funcBody = funcResult.group(1).replace('$', '\\$')
        result = re.search(
            r'(?:^|,)([a-zA-Z_\$][a-zA-Z_0-9]*):function\(a\)\{(?:return )?a\.reverse\(\)\}', objBody, re.MULTILINE)
        reverseKey = result.group(1).replace('$', '\\$') if result else ''
        result = re.search(
            r'(?:^|,)([a-zA-Z_\$][a-zA-Z_0-9]*):function\(a,b\)\{return a\.slice\(b\)\}', objBody, re.MULTILINE
        )
        sliceKey = result.group(1).replace('$', '\\$') if result else ''
        result = re.search(
            r'(?:^|,)([a-zA-Z_\$][a-zA-Z_0-9]*):function\(a,b\)\{a\.splice\(0,b\)\}', objBody, re.MULTILINE)
        spliceKey = result.group(1).replace('$', '\\$') if result else ''
        result = re.search(
            r'(?:^|,)([a-zA-Z_\$][a-zA-Z_0-9]*):function\(a,b\)\{var c=a\[0\];a\[0\]=a\[b(?:%a\.length)?\];a\[b(?:%a\.length)?\]=c(?:;return a)?\}', objBody, re.MULTILINE)
        swapKey = result.group(1).replace('$', '\\$') if result else ''

        regex = '(?:a=)?%s\\.(%s)\\(a,(\\d+)\\)' % (obj,
                                                    '|'.join(x for x in [reverseKey, sliceKey, spliceKey, swapKey] if x))

        result = re.findall(regex, funcBody)
        if not result:
            raise ValueError("result not match")
        tokens = []
        for item in result:
            if item[0] == swapKey:
                tokens.append('w'+item[1])
            elif item[0] == reverseKey:
                tokens.append("r")
            elif item[0] == sliceKey:
                tokens.append('s'+item[1])
            elif item[0] == spliceKey:
                tokens.append('p'+item[1])
        self.tokens = tokens

    def decode(self, sig):
        tokens = self.tokens
        sig = [x for x in sig]
        pos = 0
        for tok in tokens:
            if len(tok) > 1:
                pos = int(tok[1:])
            if tok[0] == "r":
                sig.reverse()
            elif tok[0] == "w":
                s = sig[0]
                sig[0] = sig[pos]
                sig[pos] = s
            elif tok[0] == "s":
                sig = sig[pos:]
            elif tok[0] == 'p':
                sig = sig[pos:]
        return ''.join(sig)
