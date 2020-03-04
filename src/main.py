from flask import Flask, render_template, request
from handler import proxy
app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video/<string:vid>.json")
def videojson(vid):
    return proxy.videojson(request.args, vid)


@app.route("/video/<string:vid>/<int:itag>.json")
def videopart(vid, itag):
    return proxy.videopart(request.args, vid, itag)


@app.errorhandler(404)
def page_not_found(error):
    return render_template("index.html")


@app.errorhandler(500)
def server_error(error):
    return str(error), 500, {"Content-Type": "text/plain"}


@app.after_request
def apply_caching(response):
    if response.status == 200:
        response.headers["Cache-Control"] = "public, max-age=3600"
    return response


if __name__ == "__main__":
    app.run()
