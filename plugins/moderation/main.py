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
    async def clear(self, ctx: commands.Context, nombre: int=1):
        await ctx.defer()
        await ctx.channel.purge(limit=nombre + 1)
    
        
    @commands.Cog.listener(name='on_message')
    async def wrong_chat_pokemon(self, msg: discord.Message):
        if msg.author.id == 432610292342587392 and msg.channel.id != 1191499973670486076:
            async for previous_msg in msg.channel.history(limit=1, before=msg):
                await msg.delete()
                await previous_msg.reply(f"Attention tu ne peux pas faire ça ici ! Utilise plutôt le channel dédié <#1191499973670486076>")
    
    
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