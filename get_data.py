import sys
import pycurl
import json
import os
from urllib.parse import urlparse
from io import BytesIO
from settings import OWNER_ID, DOMAIN, STORE_DIR, API_URL, APP_ID, APP_SECRET, \
    AUTHORIZE_URL, REDIRECT_URI


def get_response(url):
    buf = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.WRITEFUNCTION, buf.write)
    c.setopt(c.URL, url)
    c.setopt(c.VERBOSE, True)
    c.setopt(pycurl.HTTPHEADER, [b'Content-Type: text/html; charset=UTF-8'])
    c.perform()
    result = buf.getvalue()
    buf.close()
    return result


class Post:
    def __init__(self, data):
        self.id = data['id']
        self.date = data['date']
        self.pics = [{"name": urlparse(attach['photo']['photo_604']).path.split('/')[-1],
                      "url": attach['photo']['photo_604']}
                     for attach in data.get('attachments', [])
                     if attach['type'] == 'photo']
        self.videos = [{"owner_id": attach['video']['owner_id'],
                        "video_id": attach['video']['id'],
                        "access_key": attach['video']['access_key'],
                        "title": attach['video']['title']}
                       for attach in data.get('attachments', [])
                       if attach['type'] == 'video']
        self.text = data['text']

    def save(self, directory, token):
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
        # save videos
        #for video in self.videos:
            #with open(os.path.join(dirname, 'videos'), mode='wb+') as f:
                #f.write(self._fetch_video(video['owner_id'], video['video_id'],
                                          #video['access_key'], token))

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

    def _fetch_video(self, owner_id, video_id, access_key, token):
        videos = "{}_{}_{}".format(owner_id, video_id, access_key)
        response = get_response(API_URL.format(
            'video.get?count=1&owner_id={}&videos={}&v=5.23&format=JSON'.
            format(OWNER_ID, videos, token)))


class VkScraper:
    def __init__(self):
        self._token = None
        self._app_token = None

    @property
    def token(self):
        if not self._token:
            r = get_response(ACCESS_TOKEN_URL.format(
                '?client_id={}&client_secret={}&v=5.23&grant_type=client_credentials'.
                format(APP_ID, APP_SECRET)))
            self._token = json.loads(r.decode('utf-8'))['access_token']
        return self._token

    @property
    def app_token(self):
        if not self._app_token:
            r = get_response(AUTHORIZE_URL.format(
                '?client_id={}&scope=video&v=5.23&redirect_uri={}&response_type=token'.
                format(APP_ID, REDIRECT_URI)))
            # TODO FIXME how can we login user with minimum effort?
        return self._app_token

    def scrape_wall(self, count, upload_dir, offset=0, save=False):
        buf = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, API_URL.format(
            'wall.get?count={}&domain={}&owner_id={}&v=5.23&format=JSON&offset={}'.\
            format(count, DOMAIN, OWNER_ID, offset)))
        c.setopt(c.WRITEFUNCTION, buf.write)
        c.setopt(c.VERBOSE, True)
        c.setopt(pycurl.HTTPHEADER, [b'Content-Type: text/html; charset=UTF-8'])
        c.perform()
        data = json.loads(buf.getvalue().decode('utf-8'))
        buf.close()
        posts = [Post(d) for d in data['response']['items']]
        if save:
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            for p in posts:
                p.save(upload_dir, self.app_token)
            return True
        return posts



def main():
    scraper = VkScraper()
    """ Test len(result)
    >>> len(scraper.scrape_wall(5))
    5
    """
    count = sys.argv[1] if len(sys.argv) > 1 else 5
    upload_dir = sys.argv[2] if len(sys.argv) > 2 else STORE_DIR
    if '--offset' in sys.argv:
        i = sys.argv.index('--offset')
        sys.argv.pop(i)
        offset = int(sys.argv[i])
    else:
        offset = 0
    scraper.scrape_wall(count, upload_dir, offset=offset, save=True)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
    main()
