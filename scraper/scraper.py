import json
import logging
import os
import urllib.parse
import urllib.request

from .settings import (OWNER_ID, DOMAIN, API_URL)

# setup logging stuff here
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)
LOG = logging.getLogger('scraper')
fh = logging.FileHandler('scrape.log')
fh.setFormatter(logging.Formatter(LOG_FORMAT))
LOG.addHandler(fh)


def fetch_data(url, headers=None, json_loads=False):
    headers = headers or {}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        data = response.read()
        if json_loads:
            data = json.loads(data.decode('utf-8'))
        return data


class Post:
    def __init__(self, data):
        self.id = data['id']
        self.date = data['date']
        self.text = data['text']
        self.pics = []

        for attach in data.get('attachments', []):
            if attach['type'] == 'photo':
                pic_url = attach['photo']['photo_604']
                pic = {"name": (urllib.parse.urlparse(pic_url).
                                path.split('/')[-1]),
                       "url": pic_url}
                self.pics.append(pic)

    def save(self, directory):
        name = "{}_{}".format(self.id, self.date)
        dirname = os.path.join(directory, name)
        filename = os.path.join(dirname, 'text')
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, mode='w') as f:
            f.write(self.text)
        # save pictures
        for pic in self.pics:
            with open(os.path.join(dirname, pic['name']), mode='wb') as f:
                f.write(fetch_data(pic['url']))

    def __str__(self):
        return "Date:{}\n{}".format(self.date, self.text)

    def __repr__(self):
        return self.__str__()


class VkScraper:
    def scrape_wall(self, count, upload_dir=None, offset=0, save=False):
        wall_url = API_URL.format('wall.get?count={}&domain={}&owner_id={}'
                                  '&v=5.23&format=JSON&offset={}'.
                                  format(count, DOMAIN, OWNER_ID, offset))
        data = fetch_data(wall_url,
                          headers={'Content-Type': 'text/html; charset=UTF-8'},
                          json_loads=True)
        posts = [Post(d) for d in data['response']['items']]
        if save:
            if upload_dir is None:
                LOG.warn("Save option is specified but no upload directory "
                         "given - scraped posts won't be saved.")
                return posts
            if not os.path.exists(upload_dir):
                LOG.info("Creating directory: %s" % upload_dir)
                os.makedirs(upload_dir)
            for p in posts:
                p.save(upload_dir)
        return posts
