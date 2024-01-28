from discord_webhook import DiscordWebhook

import datetime
import os
import requests
import sqlite3
import sys
import xml.etree.ElementTree as ET

# for testing. make sure you remove before commiting! :)
TESTING_WEBHOOK_URL = ''
WEBHOOK_URLS = {
    'main': os.environ.get('DISCORD_WEBHOOK_MAIN_URL', TESTING_WEBHOOK_URL),
}

DQX_TWITTER = "https://twiiit.com/DQ_X/rss"


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

response = requests.get(url=DQX_TWITTER)
if response.status_code != 200:
    print(f'Could not get nitter data.')
    sys.exit(1)

tweets = []
rss_data = ET.fromstring(response.text)
for row in rss_data[0].iter('item'):
    link = row.find('link').text
    tweet = link.split('/')[-1].rstrip('#m')
    tweets.append(tweet)

for tweet in tweets:
    query = f"SELECT id FROM tweets WHERE id = {tweet}"
    cursor.execute(query)
    results = cursor.fetchone()

    if not results:
        cur_time = datetime.datetime.now()

        fx_link = f'https://fxtwitter.com/DQ_X/status/{tweet}/en'

        insert = f"INSERT INTO tweets (date, id, link) VALUES ('{cur_time}', {tweet}, '{fx_link}')"
        cursor.execute(insert)
        conn.commit()

        if WEBHOOK_URLS['main']:
            print(f'Posting webhook for {fx_link}.')
            notify_webhook(content=fx_link)
