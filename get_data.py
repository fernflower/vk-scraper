import sys

import argparse

from scraper import settings
from scraper import scraper


def main():
    s = scraper.VkScraper()
    """ Test len(result)
    >>> len(scraper.scrape_wall(5))
    5
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--offset', type=int, default=0,
                        help='An offset for the first post to download.')
    parser.add_argument('count', type=int, nargs='?', default=5,
                        help='Number of posts to download, 5 by default.')
    parser.add_argument('--upload-dir', default=settings.STORE_DIR,
                        help='Directory to store downloaded posts.')
    parsed = parser.parse_args(sys.argv[1:])
    s.scrape_wall(parsed.count, upload_dir=parsed.upload_dir,
                  offset=parsed.offset, save=True)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
    main()
