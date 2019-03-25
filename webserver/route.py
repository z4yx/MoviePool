from flask import render_template, Response, request
from urllib import unquote
import requests
import db.db as db
import logging
import json

from . import app

@app.route('/')
def index():
    search = request.args.get('search')
    if search is None:
        return app.send_static_file('html/index.html')
    else:
        return app.send_static_file('html/list.html')

@app.route('/movie/<id>')
def movie(id):
    return app.send_static_file('html/movie.html')

@app.route('/api/image-cache')
def image_cache_api():
    uri = request.args.get('url')
    resp = requests.request(
        method=request.method,
        url=unquote(uri),
        allow_redirects=True)
    #print(unquote(uri))

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)
    return response


@app.route('/api/search')
def search_api():
    search = request.args.get('search')
    results = db.search(search, start=0, count=20)
    return json.dumps(results)

@app.route('/api/pop')
def pop_api():
    results = db.getpop(count=8)
    return json.dumps(results)

@app.route('/api/movie/<id>')
def movie_api(id):
    data = db.getDoubanAdvance(id)
    if data is None:
        return ""
    try:
        del data['_id']
    except:
        pass
    return json.dumps(data)

@app.route('/api/imdb/<IMDBID>')
def imdb_api(IMDBID):
    data = db.getIMDBBasic(IMDBID)
    if data is None:
        return ""
    try:
        del data['_id']
    except:
        pass
    return json.dumps(data)

@app.route('/api/resources/<id>')
def resources_api(id):
    return json.dumps(db.getMovieResources(id))

@app.route('/api/cache/<res_id>')
def cache_api(res_id):
    return json.dumps(db.cacheResources(res_id))

@app.route('/api/progress/<res_id>')
def progress_api(res_id):
    return json.dumps(db.getProgress(res_id))

@app.route('/api/download/<res_id>')
def download_api(res_id):
    return json.dumps(db.getDownloaded(res_id))
    

