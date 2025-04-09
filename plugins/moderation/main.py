import discord
from discord.ext import commands

from pathlib import Path
import json
import pickle
import shelve

import logging
from icecream import ic


parent_folder = Path(__file__).resolve().parent


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot)->None:
        self.bot = bot
        self.channels = self.load_channels()
    
    
    @commands.Cog.listener(name='on_ready')
    async def on_ready(self):
        self.channels = self.load_channels()


    @commands.hybrid_command(name='clear', description="Efface les messages d'un channel")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, nombre: int=1):
        await ctx.defer()
        await ctx.channel.purge(limit=nombre + 1)
        logging.info(f"{ctx.guild.name} ({ctx.channel.name}): {ctx.author.name} a effacé {nombre} messages")
    
        
    @commands.Cog.listener(name='on_message')
    async def wrong_chat_pokemon(self, msg: discord.Message):
        """Alerte un utilisateur quand il joue au jeu pokemon dans le mauvais channel

        Args:
            msg (discord.Message): Message de mudae
        """
        channel = msg.channel
        server = channel.guild
        if msg.author.id == 432610292342587392 and channel.id != self.channels[server.name]["pokemon"].id:
            async for previous_msg in channel.history(limit=1, before=msg):
                await msg.delete()
                await previous_msg.reply(f"Attention tu ne peux pas faire ça ici ! Utilise plutôt le channel dédié <#1191499973670486076>", delete_after=10)
                await previous_msg.delete(delay=10)
                break
    
    
    @commands.hybrid_command(name='test')
    async def test(self, ctx: commands.Context)->None:
        guild_name = ic(ctx.guild.name)
        ic(self.channels[guild_name])
        await ctx.reply("test")
    
    
    def load_channels(self) -> dict[str, dict[str, discord.TextChannel|discord.VoiceChannel]]:
        """Renvoie un dictionnaire contenant les channels du serveur avec comme clé leur nom

        Returns:
            dict[str, discord.TextChannel|discord.VoiceChannel]: dictionaire des channels
        """
        json_file: dict[str, dict[str, int]] = self.load_json('channels')
        return {server_name: {
                channel_name: self.bot.get_channel(channel_id)
                for channel_name, channel_id in server_channels.items()
            }
            for server_name, server_channels in json_file.items()
        }
    
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