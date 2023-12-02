import discord
from discord.ext import commands

from pathlib import Path
parent_folder = Path(__file__).resolve().parent
import json




class Vocal(commands.Cog):
    def __init__(self, bot: commands.Bot)->None:
        self.bot = bot
        self.channels = self.load_json('channels')
        self.own_channels = {}

    
    @commands.Cog.listener(name="on_voice_state_update")
    async def create_your_channel(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState)->None:
        """Créer un salon à la connexion dans '➕ Créer ton salon'

        Args:
            member (discord.Member): Membre du serveur
            before (discord.VoiceState): État vocal avant la connexion
            after (discord.VoiceState): État vocal après la connexion
        """
        serveur = member.guild
        category = discord.utils.get(serveur.categories, id=self.channels['gaming_category'])
        try:
            if after.channel.id == self.channels['main_salon']:
                self.own_channels[member.id] = await serveur.create_voice_channel(member.display_name,category=category)
                await member.move_to(self.own_channels[member.id])
            
        except AttributeError:
            pass
        
        
    @commands.Cog.listener(name="on_voice_state_update")
    async def end_your_channel(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState)->None:
        """Supprime un channel vocal temporaire après deconnexion de tout les participants

        Args:
            member (discord.Member): Membre du serveur
            before (discord.VoiceState): État vocal avant la connexion
            after (discord.VoiceState): État vocal après la connexion
        """
        try:
            if channel := self.own_channels[member.id]:
                if before.channel.id == channel.id and not channel.members: 
                    await self.own_channels[member.id].delete()

        except (AttributeError, KeyError):
            pass
   
   
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
    await bot.add_cog(Vocal(bot))