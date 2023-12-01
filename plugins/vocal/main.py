import discord
from discord.ext import commands

from pathlib import Path
parent_folder = Path(__file__).resolve().parent
import json
import aiosqlite

from icecream import ic






class Vocal(commands.Cog):
    def __init__(self, bot: commands.Bot)->None:
        self.bot = bot
        self.main_salon_id = 1179547113487605761
        self.category_id = 1178410507187802222
        self.own_channels = {}

    
    # @commands.Cog.listener(name="on_voice_state_update")
    # async def create_your_channel(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState)->None:
    #     serveur = member.guild
    #     if after.channel.id == 1179547113487605761:
    #         self.own_channels[member.id] = await serveur.create_voice_channel(member.display_name)
    #         await member.move_to(self.own_channels[member.id])
            
        
        
    # @commands.Cog.listener(name="on_voice_state_update")
    # async def end_your_channel(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState)->None:
    #     serveur = member.guild
    #     ic(before)
    #     try:
    #         if before.channel.id == self.own_channels[member.id]:
    #             await serveur._remove_channel(self.own_channels[member.id])
                
    #     except AttributeError:
    #         pass
   
   
    def load_json(self, file: str)->dict:
        """"Récupère les données du fichier json

        Args:
            file (str): Nom du fichier

        Returns:
            dict: Données enregistrées
        """
        with open(f"{parent_folder}/{file}.json", 'r') as f:
            return json.load(f)

    def update_logs(self, data: dict | list, path: str)->None:
        """Enregistre le fichier logs

        Args:
            data (dict): Données à enregistrer
            path (str): Chemin du fichier à enregistrer
        """
        with open(f"{parent_folder}/{path}.json", 'w') as f:
            json.dump(data,f,indent=2) 





async def setup(bot: commands.Bot)->None:
    await bot.add_cog(Vocal(bot))