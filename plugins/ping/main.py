import discord
from discord.ext import commands

from pathlib import Path
import contextlib
import json

class Ping(commands.Bot):

    def __init__(self, bot: commands.Bot)->None:
        self.bot = bot

    @commands.hybrid_command() (name='ping')
    async def get_ping(self, ctx, *args):
        ping = self.bot.latency * 1000
       
        #|---------Ping---------|
        embed = discord.Embed(
            title =f'Ping du bot -> {round(ping)}ms !'
        )
        await self.channel.send(embed=embed)
        

async def setup(bot: commands.Bot)->None:
    await bot.add_cog(Ping(bot))

    