import datetime
import json
import os
import re
import time

import feedparser
from bs4 import BeautifulSoup


class NewsDownloader:
    LAST_POST_DATE_FILENAME = 'jobs/latest_known_post.dat'
    NEWS_FILENAME = 'jobs/posts.json'
    GOW_FEED_URL = 'https://gemsofwar.com/feed/'

    def __init__(self):
        self.last_post_date = datetime.datetime.min
        self.get_last_post_date()

    @staticmethod
    def remove_tags(text):
        soup = BeautifulSoup(text, 'html5lib')
        images = soup.findAll('img')
        image = None
        for i in images:
            source = i['src']
            if 'dividerline' not in source:
                image = source
                break
        html_tags = re.compile(r'<.*?>')
        tags_removed = re.sub(html_tags, '', text)

        return image, tags_removed

    @staticmethod
    def reformat_html_summary(e):
        content = e.content[0]['value']
        image, tags_removed = NewsDownloader.remove_tags(content)
        return image, tags_removed.strip()

    def get_last_post_date(self):
        if os.path.exists(self.LAST_POST_DATE_FILENAME):
            with open(self.LAST_POST_DATE_FILENAME) as f:
                self.last_post_date = datetime.datetime.fromisoformat(f.read())

    def process_news_feed(self):
        feed = feedparser.parse(self.GOW_FEED_URL)
        new_last_post_date = self.last_post_date

        posts = []
        for entry in feed['entries']:
            is_nintendo = 'Nintendo Switch' in entry.title
            is_pc = not is_nintendo

            posted_date = datetime.datetime.fromtimestamp(time.mktime(entry.published_parsed))
            if posted_date <= self.last_post_date:
                continue

            if is_pc:
                image, content = self.reformat_html_summary(entry)
                posts.append({
                    'author': entry.author,
                    'title': entry.title,
                    'url': entry.link,
                    'content': content,
                    'image': image,
                })

            new_last_post_date = max(new_last_post_date, posted_date)

        if posts:
            with open('jobs/posts.json', 'w') as f:
                json.dump(posts, f, indent=2)

            with open(self.LAST_POST_DATE_FILENAME, 'w') as f:
                f.write(new_last_post_date.isoformat())
