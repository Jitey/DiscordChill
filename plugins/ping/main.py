import discord
from discord.ext import commands

class Ping(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='ping')
    async def get_ping(self, ctx):

        ping = self.bot.latency * 1000

        # Créez un objet Embed pour le message
        embed = discord.Embed(
            title=f'Ping du bot -> {round(ping)}ms !'
        )

        # Envoyez le message avec l'objet Embed
        await ctx.send(embed=embed)

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Ping(bot))
