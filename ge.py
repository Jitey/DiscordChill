# |----------Module d'environnement-----------|
from os import getenv
from dotenv import load_dotenv
from pathlib import Path
# |----------Module du projet-----------|
import discord
from discord.ext import commands



parent_folder = Path(__file__).resolve().parent
load_dotenv(dotenv_path=f"{parent_folder}/.env")

PREFIX = '='


bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user.name}")


@bot.event
async def on_message(message : discord.Message):
    print(message.content)
    if "bonjour" in message.content:
        await message.channel.send("bonjour")



bot.run(getenv("BOT_TOKEN"))