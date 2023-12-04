import discord
from discord.ext import commands

from pathlib import Path
parent_folder = Path(__file__).resolve().parent
import json
import aiosqlite

from dataclasses import dataclass
from numpy import random as rd
from datetime import datetime as dt


from PIL import Image, ImageDraw
from io import BytesIO
import math


def round_it(x:float, sig: int)->float:
    """Arrondi à nombre au neme chiffre signifactif

    Args:
        x (int | float): Nombre à arrondir
        sig (int): Nombre de chiffre significatif à garder

    Returns:
        int | float: _descNombre arrondiription_
    """
    return round(x, sig - int(math.floor(math.log10(abs(x)))) - 1)

def format_float(number):
    # Convertir le nombre en chaîne de caractères
    str_number = str(number)

    return str_number.rstrip('0').rstrip('.') if '.' in str_number else str_number
    





class ResetView(discord.ui.View):
    def __init__(self, connection: aiosqlite.Connection, member_target: discord.Member)->None:
        super().__init__()
        self.connection = connection
        self.member_target = member_target


    @discord.ui.button(label="Oui", style=discord.ButtonStyle.danger)
    async def confirmer(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        member = interaction.user

        if member.guild_permissions.administrator:
            res = "UPDATE Rank SET msg=0, xp=0, lvl=0 WHERE id==?"
            await self.connection.execute(res, (self.member_target.id,))
            await self.connection.commit()
            
            await self.update_classement()
            await self.disable_all_buttons(interaction)
            await interaction.response.defer()
        else:
            await interaction.response.send_message("Tu n'as pas la permission pour ça", ephemeral=True)


    @discord.ui.button(label="Non", style=discord.ButtonStyle.danger)
    async def annuler(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        member = interaction.user

        if member.guild_permissions.administrator:
            await self.disable_all_buttons(interaction)
            await interaction.response.defer()
        else:
            await interaction.response.send_message("Tu n'as pas la permission pour ça", ephemeral=True)


    async def disable_all_buttons(self, interaction: discord.Interaction)->None:
        for child in self.children:
            if type(child) == discord.ui.Button:
                child.disabled = True
        
        await interaction.message.edit(view=self)
        
        
    async def update_classement(self):
        """Range par odre décroissant d'xp les membrs dans a bdd
        """
        req = "UPDATE Rank SET rang=DENSE_RANK() OVER (ORDER BY Rank.xp DESC) FROM Rank t2 WHERE t2.id = Rank.id"
        await self.connection.execute(req)
        await self.connection.commit()





@dataclass
class XpProfile:
    id: int
    name: str
    msg: int
    xp: int
    lvl: int
    rang: int
    add_xp_counter: int
    remove_xp_counter: int
    added_xp: int
    removed_xp: int
    xp_needed: int=0
    current_xp: int=0
    
    def __post_init__(self):
        next_lvl = self.lvl + 1
        self.xp_needed = 5 * (next_lvl ** 2) + (50 * next_lvl) + 100

        self.current_xp = self.xp - self.xp_to_level(self.lvl)


    def check_lvl(self)->bool:
        """Calcule le niveau à partir de l'xp totale

        Returns:
            bool: _description_
        """
        current_lvl = self.lvl
        
        if self.current_xp > self.xp_needed:
            self.lvl += 1
            self.__post_init__()

        return self.lvl > current_lvl

    def xp_to_level(self, lvl_target: int)->int:
        """Calcule l'xp nécessaire pour un niveau donné

        Args:
            lvl_target (int): Niveau souhaité

        Returns:
            int: Xp total requit pour le niveau
        """
        return sum(5 * (i ** 2) + (50 * i) + 100 for i in range(lvl_target))

    def print_xp(self, xp: int)->str:
        rounded_xp = round_it(xp, 3)
        return rounded_xp if rounded_xp < 1e3 else f"{format_float(rounded_xp/1e3)}K"
    
    def create_progress_bar(self, color: int | tuple=0x000000):
        if isinstance(color, int):
            color = self.color_hexa_to_rgb(color)
            
        width = 295
        height = 20
        corner_radius = 0
        progress = self.current_xp/self.xp_needed
        
        # Créer une image avec un fond blanc
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)

        # Dessiner la barre de fond
        draw.rounded_rectangle([0, 0, width, height], fill='white', radius=corner_radius)

        # Calculer la largeur de la barre de progression
        progress_width = int(width * progress)
        # Dessiner la barre de progression
        draw.rounded_rectangle([0, 0, progress_width, height], fill=color, radius=corner_radius)
    
        return self.discord_image(image, "progress_bar")
    
    def color_hexa_to_rgb(self, couleur: int)->tuple[int]:
        """Transforme une couleur hexadécimal coder sur 3 octets
        en tuple de int rgb correspondant à un octet chacun

        Args:
            couleur (int): Couleurs hexa (ex: 0xFF001E)

        Returns:
            tuple[int]: Couleurs en int (ex: (255 , 0 , 30))
        """
        r = couleur >> 16 & 0xFF
        g = couleur >> 8 & 0xFF
        b = couleur & 0xFF
        return r , g , b

    def discord_image(self, image: Image, name: str)->discord.File:
        """Convertie une image PIL en fichier envoyable sur discord

        Args:
            image (Image): Image à convertir
            name (str): Nom à donner à l'image

        Returns:
            discord.File: Image au format discord.File
        """
        image_byte = BytesIO()
        image.save(image_byte, format='PNG')
        image_byte.seek(0)
        return discord.File(image_byte, filename=f'{name}.png') 




class Rank(commands.Cog):
    def __init__(self, bot: commands.Bot, connection: aiosqlite.Connection)->None:
        self.bot = bot
        self.connection = connection
        self.last_message_time = {}
        self.channel = self.load_json('channels')


    
    @commands.hybrid_command(name='add_xp')
    async def add_xp(self, ctx: commands.Context, member_target: discord.Member, amout: int)->discord.Message:
        member = ctx.author

        if member.guild_permissions.administrator:
            await self.manage_xp('add', member_target.id, amout)
            embed = discord.Embed(
                title="Ajout d'XP",
                description=f"{amout}XP ajouté à {member_target.display_name}",
                color=discord.Color.random()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("Tu n'as pas la permission pour ça", ephemeral=True)

    
    @commands.hybrid_command(name='remove_xp')
    async def remove_xp(self, ctx: commands.Context, member_target: discord.Member, amout: int)->discord.Message:
        member = ctx.author

        if member.guild_permissions.administrator:
            await self.manage_xp('remove', member_target.id, amout)
            embed = discord.Embed(
                title="Retrait d'XP",
                description=f"{amout}XP retiré à {member_target.display_name}",
                color=discord.Color.random()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("Tu n'as pas la permission pour ça", ephemeral=True)

    
    @commands.hybrid_command(name='reset_xp')
    async def reset_xp(self, ctx: commands.Context, member_target: discord.Member)->discord.Message:
        member = ctx.author

        if member.guild_permissions.administrator:
            await ctx.send("Tu es sûr de vouloir faire ça ?", view=ResetView(self.connection,member_target))
        else:
            await ctx.send("Tu n'as pas la permission pour ça", ephemeral=True)

    
    @commands.hybrid_command(name='rang')
    async def rang(self, ctx: commands.Context, member: discord.Member=None)->discord.Message:
        if not member:
            member = ctx.author
        
        # Valeues attendue : id , name , msg , xp , lvl
        if profile := await self.get_member_stats(member.id):
            stat = XpProfile(*profile)
            
            color = discord.Color.random()
            embed = discord.Embed(
                title=f"Rank #{stat.rang}\t\tLevel {stat.lvl}",
                color=color
            )
            embed.set_thumbnail(url=member.avatar.url)
            embed.add_field(name="",value=f"{member.display_name}", inline=True)
            embed.add_field(name="", value="", inline=True)
            embed.add_field(name="", value=f"{stat.print_xp(stat.current_xp)} / {stat.print_xp(stat.xp_needed)} XP", inline=True)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)

            progress_bar = stat.create_progress_bar(int(color))
            embed.set_image(url="attachment://progress_bar.png")
            await ctx.send(embed=embed, file=progress_bar)

        else:
            await ctx.send("Tu n'as jamais envoyé de message")


    @commands.hybrid_command(name='leaderboard')
    async def leaderboard(self, ctx: commands.Context)->discord.Message:
        embed = discord.Embed(
            title="Leaderboard",
            color=discord.Color.random()
        )
        res = await self.get_leaderboard()
        embed.set_author(icon_url=ctx.author.avatar.url,name=ctx.author.display_name)
        for id , stat in res.items():
            member = self.bot.get_user(id)
            embed.add_field(name=f"{self.rank_emoji(stat.rang)} {member.display_name}", value=f"Total XP: {stat.print_xp(stat.xp)}", inline=False)
        embed.set_footer()
        
        return await ctx.send(embed=embed)


    @commands.hybrid_command(name='dashboard')
    async def dashboard(self, ctx: commands.Context)->discord.Message:
        return await ctx.send("Commande en cours de développement")
        
        
    @commands.Cog.listener(name='on_message')
    async def message_sent(self, message: discord.Message)->None:
        member = message.author
        current_time = dt.now()

        # Ignore les messages du bot et dans les channels choisit
        if member.bot or message.channel.id in self.channel['ignore'].values():
            return
    
        # Cooldown
        if (member.id in self.last_message_time 
                and (current_time - self.last_message_time[member.id]).seconds < 20
                ):
            return
        
        # Ajoute de l'xp au membre ou l'ajoute à la bdd si il est nouveau
        if profile := await self.get_member_stats(member.id):
            await self.on_message_xp(profile)

            self.last_message_time[member.id] = current_time
        else:
            await self.create_xp_profile(member)
            await self.message_sent(message)
    
    
    async def manage_xp(self, action: str, member_id: int, amount: int):
        """Ajoute ou retire la quantité d'xp donné

        Args:
            action (str): Ajouter ou retirer de l'xp
            member_id (int): Id du membre
            amount (int): Quantité d'xp
        """
        stat = self.get_all_member_stats(member_id)
        
        if action == 'add':
            stat.xp += amount
            xp_counter = stat.add_xp_counter + 1
            res = "UPDATE Rank SET xp=?, lvl=?, add_xp_counteer=?, added_xp=? WHERE id==?"
        elif action == 'remove':
            stat.xp -= amount
            xp_counter = stat.remove_xp_counter + 1
            res = "UPDATE Rank SET xp=?, lvl=?, remove_xp_counteer=?, removeed_xp=? WHERE id==?"
            
        stat.check_lvl()

        await self.connection.execute(res, (stat.msg, stat.xp, stat.lvl, xp_counter, amount, stat.id))
        await self.connection.commit()

        await self.update_classement()
    
    async def on_message_xp(self, stat: tuple | XpProfile):
        """Ajoute de l'xp au membre et regard si il a level up

        Args:
            stat (tuple | XpProfile): Stats du membre
        """
        if isinstance(stat, tuple):
            stat = XpProfile(*stat)
        
        stat.msg += 1
        stat.xp += rd.randint(15,25 + 1)
        
        if stat.check_lvl():
                channel = self.bot.get_channel(self.channel['rank'])
                await channel.send(f"<@{stat.id}> Tu viens de passer niveau {stat.lvl} !")

        res = "UPDATE Rank SET msg=?, xp=?, lvl=? WHERE id==?"
        await self.connection.execute(res, (stat.msg, stat.xp, stat.lvl, stat.id))
        await self.connection.commit()

        await self.update_classement()

    async def update_classement(self):
        """Range par odre décroissant d'xp les membrs dans a bdd
        """
        req = "UPDATE Rank SET rang=DENSE_RANK() OVER (ORDER BY Rank.xp DESC) FROM Rank t2 WHERE t2.id = Rank.id"
        await self.connection.execute(req)
        await self.connection.commit()
    
    async def create_xp_profile(self, member: discord.Member)->None:
        """Ajoutes une ligne à la base de donnée pour le membre

        Args:
            member (discord.Member): Membre discord
        """
        if member.id == self.bot.user.id:
            return

        req = "INSERT INTO Rank (id, name, msg, xp, lvl) VALUES (?,?,?,?,?)"
        await self.connection.execute(req, (member.id, member.name, 0, 0, 0))

        await self.connection.commit()

    async def get_member_stats(self, member_id: int)->XpProfile:
        """Renvoie les stats d'un membre

        Args:
            member_id (int): Id du membre

        Returns:
            XpProfile: Stats du membre
        """
        req = "SELECT * FROM Rank WHERE id==?"
        curseur = await self.connection.execute(req, (member_id,))

        # Valeues attendue : id , name , msg , xp , lvl , rang , add_xp_counter ...
        return await curseur.fetchone()
    
    async def get_all_member_stats(self) -> dict[XpProfile]:
        """Renvoie un dictionnaire de tout les profils

        Returns:
            dict[XpProfile]: Profils de tout les membres
        """
        req = "SELECT * FROM Rank"
        stats = await self.connection.execute_fetchall(req)

        return {stat[0]: XpProfile(*stat) for stat in stats}
   
    async def get_leaderboard(self) -> dict[XpProfile]:
        """Renvoie un dictionnaire de tout les profils

        Returns:
            dict[XpProfile]: Profils de tout les membres
        """
        req = "SELECT * FROM Rank ORDER BY rang LIMIT 5"
        stats = await self.connection.execute_fetchall(req)

        return {stat[0]: XpProfile(*stat) for stat in stats}
   
    def rank_emoji(self, rang: int)->str:
       match rang:
            case 1:
               return ':first_place:'
            case 2:
                return ':second_place:' 
            case 3:
                return ':third_place:'
            case _:
                return f"{rang}:"

   
   
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
    await bot.add_cog(Rank(bot, bot.connection))