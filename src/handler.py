from parser import videoParser
import req


class proxy():

    @classmethod
    def videojson(cls, args, vid):
        try:
            parser = videoParser(vid)
            data = parser.info()
            return data, 200, {"Cache-Control": "public, max-age=604800", "Access-Control-Allow-Origin": "*"}
        except Exception as e:
            return str(e), 500, {"Content-Type": "text/plain"}

    @classmethod
    def videopart(cls, args, vid, itag):
        try:
            parser = videoParser(vid)
            data = parser.infoPart(itag)
            return data, 200, {"Cache-Control": "public, max-age=3600"}
        except Exception as e:
            return str(e), 500, {"Content-Type": "text/plain"}
