# twitter-notifier

Scrapes a public nitter to get the latest tweets from the DQ_X Twitter account.

## how does it work

`main.py` is executed in this repository through GitHub Actions every 10~ minutes to check on any new tweets. `state.db` is used as our state to determine if we've seen a tweet before. This tweet is then sent to DeepL to be translated. New, translated tweets are posted to the [DQX Worldwide Discord](https://discord.gg/dragonquestx) server in the #dqx-announcements channel via a Discord webhook.

10~ minutes is approximate as we're utilizing GitHub Actions cron as a free way to run our job. GitHub does not guarantee it will run every 10 minutes exactly, but will provide a best effort in doing so.

## repository variables

- `DISCORD_WEBHOOK_MAIN_URL`: Discord webhook URL.
- `DEEPL_API_KEY`: Key to interact with DeepL's API.
