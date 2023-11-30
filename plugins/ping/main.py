import discord
from discord.ext import commands

from pathlib import Path
import contextlib
import json

class Ping(commands.Bot):

    @commands.command(name='getPing')
    async def get_ping(self, ctx, *args):
        ping = self.bot.latency * 1000
       
        #|---------Ping---------|
        embed = discord.Embed(
            resPing=f'Ping du bot -> {round(ping)}ms !'
        )
        await self.channel.send( embed=embed)
            