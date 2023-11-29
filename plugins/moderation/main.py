import discord
from discord.ext import commands

from pathlib import Path
import json
import pickle
import shelve

from icecream import ic


parent_folder = Path(__file__).resolve().parent


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot)->None:
        self.bot = bot


    @commands.hybrid_command(name='clear', description="Efface les messages d'un channel")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def clear(self, ctx: commands.Context, nombre: int):
        await ctx.defer()
        await ctx.channel.purge(limit=nombre + 1)
        
    
    @commands.command(name='test')
    async def test(self, ctx: commands.Context)->discord.Message:
        file = 'channels'
        logs = self.load_json(file)
        channel = ctx.channel
        
        logs[channel.name] = channel.id
        self.write_json(logs, file)
        await ctx.reply("Channel sauvegardé") 
    
    
    def load_json(self, file: str)->dict:
        """Récupère le fichier logs

        Returns:
            dict: Données logs enregistrées
        """
        with open(f"{parent_folder}/{file}.json", 'r') as f:
            return json.load(f)

    def write_json(self, data: dict, path: str):
        """Enregistre le fichier logs

        Args:
            data (dict): Données à enregistrer
        """
        with open(f"{parent_folder}/{path}.json", 'w') as f:
            json.dump(data,f,indent=2) 





async def setup(bot: commands.Bot)->None:
    await bot.add_cog(Moderation(bot))