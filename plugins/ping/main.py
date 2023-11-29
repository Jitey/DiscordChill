import discord
from discord.ext import commands

from pathlib import Path
import contextlib
import json

PREFIX = '='

class Ping(commands.Bot):

    def __init__(self, bot: commands.Bot)->None:
        super().__init__(command_prefix=PREFIX, intents=discord.Intents.all())

    async def getPing():
        ping = bot.latency * 1000
        await ctx.send(f'Ping du bot -> {round(ping)}ms !')