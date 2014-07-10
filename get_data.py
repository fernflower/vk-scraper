import pycurl
import json
import os
from urllib.parse import urlparse
from io import BytesIO
from settings import OWNER_ID, DOMAIN, STORE_DIR, API_URL


class Post:
    def __init__(self, data):
        self.id = data['id']
        self.date = data['date']
        self.pics = [{"name": urlparse(attach['photo']['photo_604']).path.split('/')[-1],
                      "url": attach['photo']['photo_604']}
                     for attach in data.get('attachments', [])
                     if attach['type'] == 'photo']
        self.text = data['text']

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
                f.write(self._fetch_img(pic['url']))

    def __str__(self):
        return "Date:{}\n{}".format(self.date, self.text)

    def _fetch_img(self, pic_url):
        buf = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.WRITEFUNCTION, buf.write)
        c.setopt(c.URL, pic_url)
        c.perform()
        result = buf.getvalue()
        buf.close()
        return result


class VkScraper:
    def scrape_wall(self, count, save=False):
        buf = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, API_URL.format('wall.get?count={}&domain={}&owner_id={}&v=5.23&format=JSON'.\
                 format(count, DOMAIN, OWNER_ID)))
        c.setopt(c.WRITEFUNCTION, buf.write)
        c.setopt(c.VERBOSE, True)
        c.setopt(pycurl.HTTPHEADER, [b'Content-Type: text/html; charset=UTF-8'])
        c.perform()
        data = json.loads(buf.getvalue().decode('utf-8'))
        buf.close()
        posts = [Post(d) for d in data['response']['items']]
        if save:
            if not os.path.exists(STORE_DIR):
                os.makedirs(STORE_DIR)
            for p in posts:
                p.save(STORE_DIR)
            return True
        return posts



def main():
    scraper = VkScraper()
    """ Test len(result)
    >>> len(scraper.scrape_wall(5))
    5
    """
    scraper.scrape_wall(5, save=True)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
    main()
