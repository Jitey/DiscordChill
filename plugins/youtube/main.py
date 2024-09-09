from typing import Optional
import discord
from discord.ext import commands, tasks

from pathlib import Path

from discord.utils import MISSING
parent_folder = Path(__file__).resolve().parent
import json

import scrapetube

from icecream import ic


class RegisterView(discord.ui.View):
    def __init__(self, ytb: commands.Cog, name: str) -> None:
        super().__init__()
        self.ytb = ytb
        self.name = name
        
        
    @discord.ui.button(label="Enregistrer", emoji="💾")
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        await interaction.response.send_modal(RegisterModal(self.ytb,self.name))
    
    
    @discord.ui.button(label="Annuler", emoji="❌")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        await self.desable_all_buttons(interaction)
        await interaction.response.defer()
    
    
    async def desable_all_buttons(self, interaction: discord.Interaction)->None:
        for child in self.children:
            if type(child) == discord.ui.Button:
                child.disabled = True
        
        await interaction.message.edit(view=self)
    
    

class RegisterModal(discord.ui.Modal, title="Notification YouTube"):
    def __init__(self, ytb: commands.Cog, name: str) -> None:
        super().__init__(timeout=60)
        self.ytb = ytb
        self.name = name
        
    url = discord.ui.TextInput(
        label="Enregistrer une chaîne",
        placeholder="Rentrer l'url ici"
    )
    
    async def on_submit(self, interaction: discord.Interaction)->None:
        ytb_channels = self.ytb.load_json('channel_ytb')
        
        ytb_channels[self.name] = {"url": self.url.value,
                                    "last_video": next(scrapetube.get_channel(channel_url=self.url.value))['videoId']
                                    }
        
        self.ytb.write_json(ytb_channels, 'channel_ytb')
        
        await interaction.response.send_message(f"La châine **{self.name}** a bien été enregistrée")
        # await interaction.response.defer()




class YouTube(commands.Cog):
    def __init__(self, bot: commands.Bot)->None:
        self.bot = bot
        self.channels = self.load_json('channels')
        self.on_video_upload.start()
        

    @commands.hybrid_command(name="notif_ytb", description="Enregistre une nouvelle chaîne ytb à la liste de notification")
    async def register(self, ctx: commands.Context, name: str)->None:
        """Enregistre une nouvelle chaîne ytb à la liste de notification

        Args:
            ctx (commands.Context): Contexte de la commande
            name (str): Nom de la chaîne ytb qui sera afficher dans le message
        """
        embed = discord.Embed(
            title="YouTube notification",
            description=f"Le nom d'affichage de la chaîne sera **{name}**",
            color=discord.Color.random()
        )
        embed.add_field(name="Format", value="Dans le formulaire il faut rentrer l'url de la chaîne")

        await ctx.send(embed=embed, view=RegisterView(self,name))
    
    
    @tasks.loop(minutes=1)
    async def on_video_upload(self):
        ytb_channels = self.load_json('channel_ytb')

        for nom , content in ytb_channels.items():
            try:
                video = next(scrapetube.get_channel(channel_url=content['url']))
                video_id = video['videoId']

                if ytb_channels[nom]['last_video'] != video_id:
                    channel = self.bot.get_channel(self.channels['partage'])
                    await channel.send(f"**{nom}** a posté une nouvelle vidéo ! Allez la voir !\nhttps://www.youtube.com/watch?v={video_id}")
                    
                    ytb_channels[nom]['last_video'] = video_id
                    self.write_json(ytb_channels, "channel_ytb")
            except StopIteration:
                pass

    
    
    @on_video_upload.before_loop
    async def demarage(self):
        await self.bot.wait_until_ready()
        
        
   
    def load_json(self, file: str)->dict:
        """"Récupère les données du fichier json

        Args:
            file (str): Nom du fichier

        Returns:
            dict: Données enregistrées
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
    await bot.add_cog(YouTube(bot))