import sqlite3
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import requests
from datetime import date
from bs4 import BeautifulSoup
import random

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DB_FILE = "streaks.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS streaks
    (
        user_id        TEXT PRIMARY KEY,
        streaks        INTEGER NOT NULL,
        last_done      TEXT    NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT streak, last_done FROM streaks WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_user(user_id, streak, last_done):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
                   INSERT INTO streaks (user_id, streak, last_done)
                   VALUES (?, ?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET
                                                      streak=excluded.streak,
                                                      last_done=excluded.last_done
                   """, (user_id, streak, last_done))
    conn.commit()
    conn.close()

@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user.name}")

#test function
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

#daily code for today's leetcode problem
@bot.command()
async def daily(ctx):
    query = """
    {
      activeDailyCodingChallengeQuestion {
        date
        link
        question {
          questionFrontendId
          title
          difficulty
        }
      }
    }
    """
    response = requests.post("https://leetcode.com/graphql", json={"query": query})
    data = response.json()["data"]["activeDailyCodingChallengeQuestion"]

    q = data["question"]
    url = f"https://leetcode.com{data['link']}"

    await ctx.send(f"""
**Name:** {q['title']}
**Difficulty:** {q['difficulty']}
**Link:** {url}
""")

@bot.command()
async def done(ctx):
    init_db()
    today = date.today()
    user_id = ctx.author.id
    info = get_user(user_id)
    if info is None:
        streak = 1
        last_done = today
        await ctx.send("Welcome, streak = 1!")
    else:

        await ctx.send("placeholder")

    await ctx.send(f"{user_id}")

#sends a motivational quote scraped from the web
@bot.command()
async def motivate(ctx):
    html = requests.get("https://liamporritt.com/blog/100-inspirational-study-quotes").text
    soup = BeautifulSoup(html,"html.parser")

    quotes = []
    for block in soup.find_all("blockquote", {"data-animation-role": "quote"}):
        quotes.append(block.text.strip())

    index = random.randrange(len(quotes))
    quote = quotes[index]
    if not quote:
        await ctx.send(f"found none")
    else:
        await ctx.send(f"{quote}")


bot.run(token, log_handler=handler, log_level=logging.DEBUG)