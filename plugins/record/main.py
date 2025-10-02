import discord
from discord.ext import commands
import asyncio

from pathlib import Path
parent_folder = Path(__file__).resolve().parent
import json

from dataclasses import dataclass
import aiosqlite


from icecream import ic





class Record(commands.Cog):
    def __init__(self, bot: commands.Bot, connections: dict[str, aiosqlite.Connection])->None:
        self.bot = bot
        self.connections = connections
        self.channels = self.load_channels()
        self.voice_time_counter = {}
        self.vc = None
        
    
    @commands.Cog.listener(name="on_ready")
    async def init_vocal(self):
        """Comme un __post_init__ mais sur l'event on_ready"""
        self.channels = self.load_json('channels')


    @commands.hybrid_command(name="joinvc")
    async def join_channel(self, ctx: commands.Context)->None:
        """Le bot se connecte au salon vocal où se trouve le membre
        
        Args:
            ctx: (commands.Context): COntexte de la commande
        """
        author = ctx.author
        if voice_state := author.voice:
            await voice_state.channel.connect()
        else:
            return await ctx.send("Tu n'es pas connecté en vocal")
    
    
    @commands.hybrid_command(name="leavevc")
    async def leave_channel(self, ctx: commands.Context)->None:
        """Le bot se déconnecte du salon vocal
        
        Args:
            ctx: (commands.Context): Contexte de la commande
        """
        if voice_clients := self.bot.voice_clients:
            await voice_clients[0].disconnect()
        else:
            return await ctx.send("Je ne suis pas connecté en vocal")
    
    
    @commands.Cog.listener(name="on_voice_state_update")
    async def auto_leave_channel(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState)->None:
        """Le bot se déconnecte automatique du salon vocal si plus personne n'y est
        
        Args:
            ctx: (commands.Context): Contexte de la commande
        """
        if voice_clients := self.bot.voice_clients:
            if before.channel == voice_clients[0] and not self.voice_channel_enought_filled(before):
                await self.stop_record()
                await self.bot.voice_clients[0].disconnect()
    
    
    @commands.hybrid_command(name="record")
    async def start_record(self, ctx: commands.Context)->None:
        """Le bot se déconnecte du salon vocal
        
        Args:
            ctx: (commands.Context): Contexte de la commande
        """
        if self.bot.voice_clients:
            await self.bot.voice_clients
    
    
    @commands.hybrid_command(name="stop_record")
    async def stop_record(self, ctx: commands.Context=None)->None:
        """Le bot se déconnecte du salon vocal
        
        Args:
            ctx: (commands.Context): Contexte de la commande
        """
        if self.bot.voice_clients:
            await self.bot.voice_clients
   

    
    # def actual_channel(self, server: discord.Guild) -> discord.VoiceProtocol:
    #     for voice_client in self.bot.voice_clients:
    #         if voice_client.channel.client == server:
    #             return guild
    
    
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
        """"Récupère les données du fichier json

        Args:
            file (str): Nom du fichier

        Returns:
            dict: Données enregistrées
        """
        with open(f"{parent_folder}/{file}.json", 'r') as f:
            return json.load(f)





async def setup(bot: commands.Bot)->None:
    await bot.add_cog(Record(bot, bot.connections))