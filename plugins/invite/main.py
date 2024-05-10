import discord
from discord.ext import commands

from pathlib import Path
parent_folder = Path(__file__).resolve().parent

import aiosqlite

from icecream import ic




class Invite(commands.Cog):
    def __init__(self, bot: commands.Bot, connection: aiosqlite.Connection)->None:
        self.bot = bot
        self.connection = connection
        


async def setup(bot: commands.Bot)->None:
    await bot.add_cog(Invite(bot, bot.connection))