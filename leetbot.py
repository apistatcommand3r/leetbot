import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from datetime import date
import requests
from bs4 import BeautifulSoup

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

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
          titleSlug
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



bot.run(token, log_handler=handler, log_level=logging.DEBUG)