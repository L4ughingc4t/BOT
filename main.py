import discord
import feedparser
import asyncio
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# セキュリティ関連 RSS フィード一覧
FEED_URLS = [
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.bleepingcomputer.com/feed/",
    "https://threatpost.com/feed/",
    "https://www.securityweek.com/feed/",
    "https://www.jpcert.or.jp/rss/jpcert.rdf",
    "https://medium.com/feed/tag/hacking",
    "https://medium.com/feed/tag/cybersecurity",
    "https://medium.com/feed/tag/bug-bounty",
    "https://medium.com/feed/tag/bug-bounty-tips",
    "https://www.hackerone.com/blog.atom",              # HackerOneブログ（Atom形式）
    "https://hackerone.com/hacktivity.atom",            # HackerOne Hacktivity（報告一覧）
    "https://www.bugcrowd.com/blog/feed/",              # BugcrowdブログRSS
    "https://portswigger.net/blog/rss",                  # PortSwiggerブログRSS
    "https://securitytrails.com/blog/feed",             # SecurityTrailsブログRSS
]

posted_links = set()

# Discord Bot クラス
class MyClient(discord.Client):
    async def setup_hook(self):
        self.bg_task = asyncio.create_task(self.fetch_and_post_news())

    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")

    async def fetch_and_post_news(self):
        await self.wait_until_ready()
        channel = self.get_channel(CHANNEL_ID)
        is_first_run = True  # 初回フラグ

        while not self.is_closed():
            for url in FEED_URLS:
                feed = feedparser.parse(url)

                for entry in feed.entries:
                    if entry.link not in posted_links:
                        if is_first_run:
                            # 初回は投稿せず、リンクを記録するだけ
                            posted_links.add(entry.link)
                            continue

                        # 通常の投稿処理
                        label = ""
                        if "medium.com" in entry.link:
                            tags = []
                            if "hacking" in url:
                                tags.append("#Hacking")
                            if "cybersecurity" in url:
                                tags.append("#Cybersecurity")
                            if "bug-bounty" in url or "bug-bounty-tips" in url:
                                tags.append("#BugBounty")
                            label = "📝 #Medium " + " ".join(tags)

                        msg = f"🛡️ **{entry.title}**\n{entry.link}\n{label}"
                        await channel.send(msg)
                        posted_links.add(entry.link)

            is_first_run = False
            await asyncio.sleep(3600)

intents = discord.Intents.default()
client = MyClient(intents=intents)

keep_alive()

async def main():
    async with client:
        await client.start(TOKEN)

asyncio.run(main())
