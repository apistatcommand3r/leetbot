"""
Discord Leetbot

A discord bot that generates daily problems from Leetcode, tracks user streaks, and share
motivational quotes

Features:
- Streak tracking achieved using SQLite
- Daily coding problems using LeetCode GraphQL API
- Web scraped motivational quotes

Resources used:
- Python
- Discord.py
- SQLite
- BeautifulSoup
- API
- dotenv
- Render

Created by Huizhi Zou
"""

import sqlite3
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import requests
from datetime import date, timedelta, datetime
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
    """Initializes the SQLite database and creates the streaks table if it does not exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS streaks
                   (
                       user_id   TEXT PRIMARY KEY,
                       streaks   INTEGER NOT NULL,
                       last_done TEXT    NOT NULL
                   )
                   """)
    conn.commit()
    conn.close()


def get_user(user_id):
    """Fetches streak information for a given user from the database.

    Args:
        user_id (str): Discord user ID

    Returns:
        tuple if the user exists, otherwise None
    """

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT streaks, last_done FROM streaks WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def update_user(user_id, streak, last_done):
    """Inserts or updates a user's streak record in the database.

    Args:
        user_id (str): Discord user ID
        streak (int): Current streak count
        last_done (str): Last completion date in YYYY-MM-DD format

    Returns:
        None
    """

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
                   INSERT INTO streaks (user_id, streaks, last_done)
                   VALUES (?, ?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET streaks=excluded.streaks,
                                                      last_done=excluded.last_done
                   """, (user_id, streak, last_done))
    conn.commit()
    conn.close()


@bot.command()
async def done(ctx):
    """Handles the !done command: Tracks daily streaks and updates the database.

    Args:
        ctx (Context): The Discord command context

    Returns:
        None
    """

    init_db()
    today = date.today()
    user_id = str(ctx.author.id)
    info = get_user(user_id)

    if info is None:
        streak = 1
        await ctx.send("Welcome! streak = 1")
    else:
        last_done = datetime.strptime(info[1], "%Y-%m-%d").date()
        streak = info[0]
        if last_done == today:
            await ctx.send("Already logged today!")
        elif last_done == today - timedelta(days=1):
            streak = streak + 1
            await ctx.send(f"Streak continued! Streak:{streak}")
        else:
            streak = 1
            await ctx.send(f"Missed a day, streak restarted! Streak:1")

    update_user(user_id, streak, str(today))


@bot.event
async def on_ready():
    """Triggered when the bot is ready and connected."""
    print(f"Bot is ready! Logged in as {bot.user.name}")


# daily code for today's leetcode problem
@bot.command()
async def daily(ctx):
    """Fetches the daily LeetCode problem and sends it as a Discord message.

    Args:
        ctx (Context): The Discord command context

    Returns:
        None
    """

    try:
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
    except Exception as e:
        await ctx.send("Encountered error fetching today's problem, try again later.")


# sends a motivational quote scraped from the web
@bot.command()
async def motivate(ctx):
    """Scrapes a motivational quote from liamporritt.com and sends it as a Discord message.

    Args:
        ctx (Context): The Discord command context

    Returns:
        None
    """

    try:
        html = requests.get("https://liamporritt.com/blog/100-inspirational-study-quotes").text
        soup = BeautifulSoup(html, "html.parser")

        quotes = []
        for block in soup.find_all("blockquote", {"data-animation-role": "quote"}):
            quotes.append(block.text.strip())

        index = random.randrange(len(quotes))
        quote = quotes[index]
        if not quote:
            await ctx.send(f"found none")
        else:
            await ctx.send(f"{quote}")
    except Exception as e:
        await ctx.send("Encountered error fetching quotes, try again later.")


bot.run(token, log_handler=handler, log_level=logging.DEBUG)
