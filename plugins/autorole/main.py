from typing import Optional, Union
import discord
from discord.emoji import Emoji
from discord.enums import ButtonStyle
from discord.ext import commands

from pathlib import Path
import contextlib
import json

from icecream import ic




parent_folder = Path(__file__).resolve().parent


class RoleView(discord.ui.View):
    def __init__(self, roles) -> None:
        super().__init__()
        
        for role in roles:
            self.add_item(RoleButton(role))



# class RoleSelectMenu(discord.ui.RoleSelect["RoleView"]):
#     def __init__(self) -> None:
#         super().__init__(
#             placeholder="Choisit tes rôles ici",
#             max_values=25
#             )

        
#     async def callback(self, interaction: discord.Interaction):
#         new_view = RoleView()

#         for role in self.values:
#             new_view.add_item(RoleButton(role))

#         embed = discord.Embed(
#             title="Role Select", 
#             description="Clique sur les boutons pour obtenir tes rôles",
#             color=discord.Color.random()
#         )

#         embed.set_thumbnail(url=interaction.guild.icon.url)

#         await interaction.response.edit_message(embed=embed, view=new_view)


class RoleButton(discord.ui.Button['RoleView']):
    def __init__(self, role: discord.Role)->None:
        super().__init__(
            label=role.name,
            custom_id=f"button_{role.name}",
            style=discord.ButtonStyle.blurple
        )
        
        self.role = role

    
    async def callback(self, interaction: discord.Interaction)->None:
        user = interaction.user

        if isinstance(user, discord.User):
            return

        try:
            if self.role in user.roles:
                await user.remove_roles(self.role)

                return await interaction.response.send_message(f"{self.role.name} retiré", ephemeral=True)
            
            await user.add_roles(self.role)

            return await interaction.response.send_message(f"{self.role.name} ajouté", ephemeral=True)

        except discord.Forbidden:
            return await interaction.response.send_message(f"Tu n'as pas la permission pour ce role", ephemeral=True)
            


class AutoRole(commands.Cog):
    def __init__(self, bot: commands.Bot)->None:
        self.bot = bot
        
    
    @commands.hybrid_command(name="role", description="Créer un menu pour choisir ses rôles")
    async def role(self, ctx: commands.Context)->discord.Message:
        user = ctx.author
        if not ctx.guild:
            raise commands.NoPrivateMessage()

        game_roles = [role for role in self.game_roles(ctx.guild)]


        # view = RoleView().add_item(RoleSelectMenu())
        view = RoleView(game_roles)

        embed = discord.Embed(
            title='Role Select',
            description="Cliquez sur les boutons pour selectionner un rôle",
            color=discord.Color.random()
        )

        embed.set_author(icon_url=user.display_avatar.url, name=user.display_name)
        embed.set_thumbnail(url=ctx.guild.icon.url)

        return await ctx.reply(embed=embed,view=view)


    def game_roles(self, serveur: discord.Guild)->discord.Role:
        """Renvoie un itérateur des rôles avec 'Tryhard' dedans

        Args:
            serveur (discord.Guild): serveur discord

        Yields:
            Iterator[discord.Role]
        """
        for role in serveur.roles:
            if 'Tryhard' in role.name:
                yield role

    def load_json(self, file: str)->dict:
        """"Récupère les données du fichier json

        Args:
            file (str): Nom du fichier

        Returns:
            dict: Données enregistrées
        """
        with open(f"{parent_folder}/{file}.json", 'r') as f:
            return json.load(f)

    def update_logs(self, data: dict, path: str)->None:
        """Enregistre le fichier logs

        Args:
            data (dict): Données à enregistrer
            path (str): Chemin du fichier à enregistrer
        """
        with open(f"{parent_folder}/{path}.json", 'w') as f:
            json.dump(data,f,indent=2) 







async def setup(bot: commands.Bot)->None:
    await bot.add_cog(AutoRole(bot))