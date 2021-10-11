from parser import videoParser


class proxy():

    @classmethod
    def videojson(cls, args, vid):
        try:
            parser = videoParser(vid)
            data = parser.info()
            streams = data.get('streams', {})
            for key in streams:
                del streams[key]['url']
            return data, 200, {"Cache-Control": "public, max-age=604800", "Access-Control-Allow-Origin": "*"}
        except Exception as e:
            return {'code': -1, 'msg': u'{0}'.format(e)}, 200, {"Cache-Control": "public, max-age=3600", "Access-Control-Allow-Origin": "*"}

    @classmethod
    def videopart(cls, args, vid, itag):
        try:
            parser = videoParser(vid)
            data = parser.infoPart(itag)
            return data, 200, {"Cache-Control": "public, max-age=3600"}
        except Exception as e:
            return {'code': -1, 'msg': u'{0}'.format(e)}, 200, {"Cache-Control": "public, max-age=3600", "Access-Control-Allow-Origin": "*"}
