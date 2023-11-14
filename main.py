from bs4 import BeautifulSoup as bs
from discord_webhook import DiscordWebhook

import datetime
import os
import requests
import sqlite3
import sys


# for testing. make sure you remove before commiting! :)
TESTING_WEBHOOK_URL = ''
WEBHOOK_URLS = {
    'main': os.environ.get('DISCORD_WEBHOOK_MAIN_URL', TESTING_WEBHOOK_URL),
}

DQX_TWITTER = "https://nitter.net/DQ_X"


def notify_webhook(content: str):
    """Triggers a Discord webhook URL."""
    webhook = DiscordWebhook(
        url=WEBHOOK_URLS['main'],
        username=f'[nitter] DQ_X',
        content=content
    )

    webhook.execute()


db_file = 'state.db'
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# sorry nitter! we're a low traffic bot :S
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

response = requests.get(url=DQX_TWITTER, headers=headers)
if response.status_code != 200:
    print(f'Could not get nitter data.')
    sys.exit(1)

soup = bs(response.text, 'html.parser')
posts = soup.find_all(attrs={'class': 'timeline-item'})

for post in posts:
    uri = post.find(attrs={'class': 'tweet-link'})['href']
    tweet_id = uri.split('/')[-1].replace('#m', '')

    query = f"SELECT id FROM tweets WHERE id = {tweet_id}"
    cursor.execute(query)
    results = cursor.fetchone()

    if not results:
        cur_time = datetime.datetime.now()

        fx_link = f'https://fxtwitter.com/DQ_X/status/{tweet_id}/en'

        insert = f"INSERT INTO tweets (date, id, link) VALUES ('{cur_time}', {tweet_id}, '{fx_link}')"
        cursor.execute(insert)
        conn.commit()
    
        if WEBHOOK_URLS['main']:
            print(f'Posting webhook for {fx_link}.')
            notify_webhook(content=fx_link)
