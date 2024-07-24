from bs4 import BeautifulSoup
from discord_webhook import DiscordEmbed, DiscordWebhook

import datetime
import deepl
import os
import requests
import sqlite3
import sys
import xml.etree.ElementTree as ET

WEBHOOK_URL =  os.environ.get("DISCORD_WEBHOOK_MAIN_URL", "")
TRANSLATE_KEY = os.environ.get("DEEPL_API_KEY", "")

TWITTER = "http://twiiit.com"  # picks a random, online-only nitter instance
DQX_TWITTER = f"{TWITTER}/DQ_X"
RSS_FEED = DQX_TWITTER + "/rss"
TWEET_STATUS = DQX_TWITTER + "/status"


def notify_webhook(content: DiscordEmbed):
    if WEBHOOK_URL:
        webhook = DiscordWebhook(url=WEBHOOK_URL)
        embed = content
        webhook.add_embed(embed)

        response = webhook.execute()
    else:
        response = "No webhook URL configured. Unable to send message to Discord."
    return response


def get_tweet_contents(url: str) -> dict:
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.find(class_="tweet-content media-body").text
    image = soup.find(class_="still-image").get("href")
    if image:
        image = TWITTER + image

    return {
        "text": content,
        "image": image
    }


def translate_tweet(text: str) -> str:
    if not TRANSLATE_KEY:
        return text
    translator = deepl.Translator(TRANSLATE_KEY)
    response = translator.translate_text(
        text = text,
        source_lang = "ja",
        target_lang = "en-us",
        preserve_formatting = True
    )

    return response.text


db_file = "state.db"
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

response = requests.get(url=RSS_FEED)
if response.status_code != 200:
    print(f"Could not get nitter data.")
    sys.exit(1)


rss_data = ET.fromstring(response.text)
for row in rss_data[0].iter("item"):

    # get tweet id to see if we've seen it before.
    link = row.find("link").text
    nitter_instance = link.split('/')[2]
    tweet = link.split('/')[-1].rstrip('#m')

    query = f"SELECT id FROM tweets WHERE id = {tweet}"
    cursor.execute(query)
    results = cursor.fetchone()

    if not results:
        print(f"Nitter instance: {nitter_instance}")
        print(f"New tweet: {tweet}")

        # get the tweet image first (if it exists)
        tweet_description = row.find("description").text
        soup = BeautifulSoup(tweet_description, "html.parser")

        image = soup.get("img", {}).get("src", "")
        if image:
            # "x" (twitter) images link from this domain. will be more reliable than nitter.
            image = "https://pbs.twimg.com/media/" + image.split('%2F')[-1] + "?format=jpg"
            print(f"Tweet has image: {image}")

        # get the tweet text
        tweet_text = row.find('title').text

        print("Translating text...")
        trl_text = translate_tweet(tweet_text)

        tweet_url = f"https://x.com/DQ_X/status/{tweet}"

        embed = DiscordEmbed(
            title = "Dragon Quest X Official (@DQ_X)",
            url = tweet_url,
            description = trl_text,
        )
        embed.set_author(
            name = "twitter_notifier",
            url = "https://github.com/dqx-translation-project/twitter-notifier"
        )
        if image:
            embed.set_image(url=image)

        print("Posting to webhook...")
        response = notify_webhook(content=embed)

        # only insert into the db if we were able to notify Discord. otherwise, we will try again next run.
        if response.status_code == 200:
            cur_time = datetime.datetime.now()
            insert = f"INSERT INTO tweets (date, id, link) VALUES ('{cur_time}', {tweet}, '{tweet_url}')"
            cursor.execute(insert)
            conn.commit()

cursor.close()
