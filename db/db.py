# encoding: utf8
import pymongo
from pymongo import MongoClient
import logging
import json
import time
from crawler import searchMovieDouban, fetchDouban, \
    searchByrResources, getMoviePopDouban, fetchIMDB
from downloader import getDownloadStatusEach, startNewDownload, getOfflineDownloadPath
from webserver import app


DB = "MovieDB"
DownloadBasic = 'DownloadBasic'  #unique 'byr_id'
DoubanBasic = 'DoubanBasic'      #unique "id"
DoubanAdvance = 'DoubanAdvance'  #unique "id"
IMDBBasic = 'IMDBBasic'          #unique "IMDBid"
IDCvt = 'IDConvert'              #unique "id" "IMDBid"

TIME_STAMP = 'TIME_STAMP'
TIME_OUT = 24 * 3600

pop = None
pop_time = 0

def get_db_client():
    return MongoClient(app.config['DB_URI'])

def search(query, start=0, count=5):
    data = searchMovieDouban(query, start, count)
    if data is None:
        return None
    coll = get_db_client()[DB][DoubanBasic]
    for item in data:
        result = coll.update_one({'id': item['id']}, {'$set': item}, upsert=True)
        logging.info('updating '+item['id'])
    return data

def getpop(count=8):
    global pop
    global pop_time
    if (not pop is None) and (pop_time + TIME_OUT < time.time()):
        return pop
    data = getMoviePopDouban(count)
    if data is None:
        return None
    coll = get_db_client()[DB][DoubanBasic]
    for item in data:
        result = coll.update_one({'id': item['id']}, {'$set': item}, upsert=True)
        logging.info(result)
    pop = data
    pop_time = time.time()
    return data


def getDoubanBasic(doubanID):
    coll = get_db_client()[DB][DoubanBasic]
    cur = coll.find({'id': doubanID})
    logging.debug(doubanID+' '+str(cur.count()))
    if cur.count() > 0:
        return cur[0]
    else:
        return None

def getDoubanAdvance(doubanID):
    coll = get_db_client()[DB][DoubanAdvance]
    coll2 = get_db_client()[DB][IDCvt]
    cur = coll.find({'id': doubanID})
    data = None
    if cur.count() > 0:
        data = cur[0]
    if (data is None) or (data[TIME_STAMP] + TIME_OUT < time.time()):
        ndata = fetchDouban(doubanID)
        if ndata is None:
            return data
        ndata.update({TIME_STAMP : time.time()})
        result = coll.update_one({'id': doubanID}, {'$set': ndata}, upsert=True)
        logging.info(result)
        if ndata.has_key('IMDB'):
            result = coll2.update_one({'id': doubanID}, {'$set': {'IMDBid':ndata['IMDB']}}, upsert=True)
            logging.info(result)
        data = ndata
    return data

def getIMDBBasic(IMDBID):
    coll = get_db_client()[DB][IMDBBasic]
    cur = coll.find({'IMDBid': IMDBID})
    data = None
    if cur.count() > 0:
        data = cur[0]
    if (data is None) or (data[TIME_STAMP] + TIME_OUT < time.time()):
        ndata = fetchIMDB(IMDBID)
        if ndata is None:
            return data
        ndata.update({TIME_STAMP : time.time()})
        result = coll.update_one({'IMDBid': IMDBID}, {'$set': ndata}, upsert=True)
        logging.info(result)
        data = ndata
    return data

def getIMDBID(doubanID):
    pass

def getDoubanID(IMDBID):
    pass

def getResourcesHash(r):
    coll = get_db_client()[DB][DownloadBasic]
    for item in r:
        cur = coll.find({'byr_id': item['download_id']})
        if cur.count() > 0:
            item['bt_hash'] = cur[0]['bt_hash']
        else:
            item['bt_hash'] = None

def getMovieResources(doubanId):
    douban = getDoubanAdvance(doubanId)
    if douban is None:
        return []
    r = searchByrResources(douban['IMDB'], douban['title'])
    getResourcesHash(r)
    getDownloadStatusEach(r)

    return r

def cacheResources(resId):
    coll = get_db_client()[DB][DownloadBasic]
    cur = coll.find({'byr_id': resId})
    if cur.count() > 0:
        return {'reason': 1}
    else:
        ret,h = startNewDownload(resId)
        if not ret:
            return {'reason': 2}
        else:
            coll = get_db_client()[DB][DownloadBasic]
            data = {'byr_id': resId,'bt_hash': h}
            coll.update_one({'byr_id': resId}, {'$set': data}, upsert=True)
            return {'reason': 0}

def getProgress(resId):
    coll = get_db_client()[DB][DownloadBasic]
    cur = coll.find({'byr_id': resId})
    if cur.count() > 0:
        item = {'download_id': resId}
        item['bt_hash'] = cur[0]['bt_hash']
        getDownloadStatusEach([item])
        return {'reason': 0, 'status': item}
    else:
        return {'reason': 1}

def getDownloaded(resId):
    coll = get_db_client()[DB][DownloadBasic]
    cur = coll.find({'byr_id': resId})
    if cur.count() > 0:
        p = getOfflineDownloadPath(cur[0]['bt_hash'])
        if p:
            return {'reason': 0, 'path': p}
        return {'reason': 2}
    else:
        return {'reason': 1}

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,\
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',\
        datefmt='%m-%d %H:%M')
    # print search(u"速度与激情")
    # print getDoubanBasic('6537500')
    # print getDoubanAdvance('6537500')
