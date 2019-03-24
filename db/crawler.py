# encoding: utf8
import requests
import logging
import sys
import json
import traceback
import urlparse
from bs4 import BeautifulSoup
import re
from webserver import app

URL = 'https://api.douban.com'
BYR_SEARCH_URL = 'https://bt.byr.cn/torrents.php'
BYR_DOWNLOAD_URL = 'https://bt.byr.cn/download.php'

def searchByrResources(imdbId):
    try:
        arg = {'search': imdbId, 'search_area': 4}
        r = requests.get(BYR_SEARCH_URL, params=arg, headers={'cookie': app.config['BYR_COOKIE']}, timeout=3)
        assert r.status_code == 200

        result = []
        soup = BeautifulSoup(r.text, "html.parser")
        for row in soup.select('table.torrents tr'):
            cols = row.find_all('td', class_='rowfollow')
            if not len(cols) or len(cols)<9:
                continue
            download_id = urlparse.parse_qs(urlparse.urlparse(cols[1].find_all('a')[0].get('href')).query)['id'][0]
            name = cols[1].select('a b')[0].contents[0]
            size = ''.join(filter(lambda s:isinstance(s, unicode), cols[4].contents))
            up = (cols[5].find_all('font') or cols[5].find_all('a') or cols[5].find_all('span'))[0].contents[0]
            down = (cols[6].find_all('a') or [cols[6]])[0].contents[0]
            result.append({
                'download_id': download_id,
                'name': name,
                'size': size,
                'uploading': up,
                'downloading': down
            })

        return result
    except Exception, e:
        logging.warning('searchByrResources {} {}'.format(imdbId, e))
        traceback.print_exc()
    return []

def getByrTorrent(ByrId):
    try:
        arg = {'id': ByrId}
        r = requests.get(BYR_DOWNLOAD_URL, params=arg, headers={'cookie': app.config['BYR_COOKIE']}, timeout=3)
        assert r.status_code == 200
        return r.content
    except Exception, e:
        logging.warning('getByrTorrent {}'.format(ByrId))
        traceback.print_exc()
    return None

def searchMovieDouban(query, start=0, count=5):
    '''
    This function returns json[subjects].
    visit https://api.douban.com/v2/movie/search?q=%7B%E9%80%9F%E5%BA%A6%E4%B8%8E%E6%BF%80%E6%83%85%7D for an example.
    '''
    data = {'q' : '{' + query + '}',
            'start' : start,
            'count' : count
            }
    try:
        r = requests.get(URL + '/v2/movie/search', params=data, timeout=3)
        assert r.status_code == 200
    except:
        logging.warning(query + 'Search Failed')
        return None

    return json.loads(r.text)['subjects']

def getMoviePopDouban(count=8):
    try:
        r = requests.get(URL + '/v2/movie/in_theaters', timeout=3)
        assert r.status_code == 200
    except:
        logging.warning('getMoviePopDouban Failed')
        return None
    return json.loads(r.text)['subjects'][:count]

def fetchDouban(doubanID):
    try:
        r = requests.get(URL + '/v2/movie/subject/' + doubanID, timeout=3)
        assert r.status_code == 200
        data = json.loads(r.text)
        try:
            r = requests.get('https://movie.douban.com/subject/' + doubanID, timeout=3)
            assert r.status_code == 200
            soup = BeautifulSoup(r.text, 'lxml')
            imdb = soup.find(id='info').find('a', href=re.compile("imdb.com"), text=re.compile("tt\\d*")).text
            data.update({'IMDB': imdb})
        except:
            logging.warning("ERROR in load IMDB ID")
            traceback.print_exc()
    except:
        logging.warning(doubanID + 'fetchdata failed')
        return None
    return data

def fetchIMDB(IMDBID):
    try:
        r = requests.get('http://www.imdb.com/title/' + IMDBID, timeout=3)
        assert r.status_code == 200
        soup = BeautifulSoup(r.text, 'lxml')
        imdbScore = soup.find(class_='ratingValue').text
        storyline = soup.find(id='titleStoryLine').find('p').text
        data = {'score' : imdbScore.split('/')[0], 'summary': storyline }
    except:
        logging.warning("ERROR in IMDB Score")
    return data

if __name__ == '__main__':
    print searchMovieDoubanID(u"速度与激情")
