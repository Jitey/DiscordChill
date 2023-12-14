import discord
from discord.ext import commands
import asyncio

from pathlib import Path
parent_folder = Path(__file__).resolve().parent
import json

from dataclasses import dataclass
import aiosqlite
import time
import math
from PIL import Image, ImageDraw
from io import BytesIO

from icecream import ic


def round_it(x:float, sig: int)->float:
    """Arrondi à nombre au neme chiffre signifactif

    Args:
        x (int | float): Nombre à arrondir
        sig (int): Nombre de chiffre significatif à garder

    Returns:
        int | float: _descNombre arrondiription_
    """
    return x if x == 0 else round(x, sig - int(math.floor(math.log10(abs(x)))) - 1)

def format_float(number):
    # Convertir le nombre en chaîne de caractères
    str_number = str(number)

    return str_number.rstrip('0').rstrip('.') if '.' in str_number else str_number
    






@dataclass
class VocalProfile:
    id: int
    name: str
    time_spend: int
    afk: int
    lvl: int
    rang: int
    current_xp: int=0
    xp_needed: int=0

    
    def __post_init__(self):
        next_lvl = self.lvl + 1
        self.xp_needed = 5 * (next_lvl ** 2) + (50 * next_lvl) + 100

        self.current_xp = self.time_spend - self.time_to_level(self.lvl)

    
    def check_lvl(self)->bool:
        """Calcule le niveau à partir de l'xp totale

        Returns:
            bool: Si on a rank up ou non
        """
        current_lvl = self.lvl
        
        if self.current_xp > self.xp_needed:
            self.lvl += 1
            self.__post_init__()

        return self.lvl > current_lvl

    def time_to_level(self, lvl_target: int)->int:
        """Calcule l'xp nécessaire pour un niveau donné

        Args:
            lvl_target (int): Niveau souhaité

        Returns:
            int: Xp total requit pour le niveau
        """
        return sum(5 * (i ** 2) + (50 * i) + 100 for i in range(lvl_target))

    def print_tps(self, xp: int)->str:
        rounded_tps = round_it(xp, 3)
        return rounded_tps if rounded_tps < 1e3 else f"{format_float(rounded_tps/1e3)}K"
    
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





class Vocal(commands.Cog):
    def __init__(self, bot: commands.Bot, connection: aiosqlite.Connection)->None:
        self.bot = bot
        self.connection = connection
        self.channels = self.load_json('channels')
        self.own_channels = {}
        self.voice_time_counter = {}
        self.afk_time_counter = {}
        
    
    @commands.Cog.listener(name="on_ready")
    async def init_vocal(self):
        self.afk_channel = self.bot.get_channel(self.channels['afk'])



    @commands.hybrid_command(name='vrang')
    async def vrang(self, ctx: commands.Context, member: discord.Member=None)->discord.Message:
        if member is None:
            member = ctx.author

        await self.update_classement()
        
        # Valeues attendue : id , name , msg , xp , lvl
        if profile := await self.get_member_stats(member.id):
            stat = VocalProfile(*profile)
            
            color = discord.Color.random()
            embed = discord.Embed(
                title=f"VRank #{stat.rang}\t\tLevel {stat.lvl}",
                color=color
            )
            embed.set_thumbnail(url=member.avatar.url)
            embed.add_field(name="",value=f"{member.display_name}", inline=True)
            embed.add_field(name="", value="", inline=True)
            embed.add_field(name="", value=f"{stat.print_tps(stat.current_xp)} / {stat.print_tps(stat.xp_needed)} min", inline=True)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)

            # progress_bar = stat.create_progress_bar(int(color))
            # embed.set_image(url="attachment://progress_bar.png")
            # await ctx.send(embed=embed, file=progress_bar)
            await ctx.send(embed=embed)

        else:
            await ctx.send("Tu ne t'es jamais connecté en vocal")


    @commands.hybrid_command(name='vleaderboard')
    async def leaderboard(self, ctx: commands.Context)->discord.Message:
        embed = discord.Embed(
            title="Leaderboard",
            color=discord.Color.random()
        )
        res = await self.get_leaderboard()
        embed.set_author(icon_url=ctx.author.avatar.url,name=ctx.author.display_name)
        for id , stat in res.items():
            member = self.bot.get_user(id)
            embed.add_field(name=f"{self.rank_emoji(stat.rang)} {member.display_name}", value=f"Total Tps: {stat.print_tps(stat.time_spend)}", inline=False)
        embed.set_footer()
        
        return await ctx.send(embed=embed)


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
                channel = await serveur.create_voice_channel(member.display_name,category=category)
                self.own_channels[channel.id] = channel
                await member.move_to(self.own_channels[channel.id])
            
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
            if channel := self.own_channels[before.channel.id]:
                if before.channel.id == channel.id and not channel.members: 
                    await self.own_channels[channel.id].delete()
                    del self.own_channels[channel.id]

        except (AttributeError, KeyError):
            pass
   
   
    @commands.Cog.listener(name="on_voice_state_update")
    async def on_vocale_join(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState)->None:
        try:
            if not before.channel or before.channel.id == self.afk_channel.id:
                if after.channel.id != self.afk_channel.id:
                    self.voice_time_counter[member.id] = time.perf_counter()

                else:
                    self.afk_time_counter[member.id] = time.perf_counter()
        
        except AttributeError:
            pass    
    
    
    @commands.Cog.listener(name="on_voice_state_update")
    async def on_vocale_leave(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState)->None:
        try:
            if not after.channel or after.channel.id == self.afk_channel.id:
                if before.channel.id != self.afk_channel.id:
                    time_spend = int(time.perf_counter() - self.voice_time_counter[member.id])
                    afk = 0

                else:
                    time_spend = 0
                    afk = int(time.perf_counter() - self.afk_time_counter[member.id])

                if profile := await self.get_member_stats(member.id):
                    await self.on_vocal_xp(profile, time_spend, afk)
                else:
                    await self.create_vocal_profile(member)
                    await self.on_vocale_leave(member, before, after)
                       
        except (AttributeError,KeyError):
            pass
   
   
    @commands.Cog.listener(name="on_voice_state_update")
    async def anti_farm(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # Sur une déconection
        if after.channel is None: 
    
            await asyncio.sleep(60)
            if len(before.channel.members) == 1:
                member = before.channel.members[0]
                await member.move_to(None)
                await member.send("Tu es resté trop longtemps seul dans un salon. Tu as été déconnecté.")
        
        # Sur une connection
        if before.channel is None: 
            
            await asyncio.sleep(60)
            if len(after.channel.members) == 1:
                member = after.channel.members[0]
                await member.move_to(None)
                await member.send("Tu es resté trop longtemps seul dans un salon. Tu as été déconnecté.")
    

    async def on_vocal_xp(self, stat: tuple | VocalProfile, time_spend: int, afk: int)->None:
        """Ajoute de l'xp au membre et regard si il a level up

        Args:
            stat (tuple | XpProfile): Stats du membre
        """
        if isinstance(stat, tuple):
            stat = VocalProfile(*stat)
        
        stat.time_spend += time_spend
        stat.afk += afk
        req = "UPDATE Vocal SET time=?, afk=? WHERE id==?"
        
        if stat.check_lvl():
            channel = self.bot.get_channel(self.channel['rank'])
            await channel.send(f"<@{stat.id}> Tu viens de passer niveau {stat.lvl} en vocal !")
        
        await self.connection.execute(req, (stat.time_spend, afk, stat.id))
        await self.connection.commit()

        await self.update_classement()
    
    async def update_classement(self):
        """Range par odre décroissant de temps passé en vocal les membrs dans la bdd
        """
        req = "UPDATE Vocal SET rang=DENSE_RANK() OVER (ORDER BY Vocal.time DESC) FROM Vocal t2 WHERE t2.id = Vocal.id"
        await self.connection.execute(req)
        await self.connection.commit()
    
    async def create_vocal_profile(self, member: discord.Member)->None:
        """Ajoutes une ligne à la base de donnée pour le membre

        Args:
            member (discord.Member): Membre discord
        """
        if member.id == self.bot.user.id:
            return

        req = "INSERT INTO Vocal (id, name, time, afk, lvl) VALUES (?,?,?,?,?)"
        await self.connection.execute(req, (member.id, member.name, 0, 0, 0))
        await self.connection.commit()

    async def get_member_stats(self, member_id: int)->VocalProfile:
        """Renvoie les stats d'un membre

        Args:
            member_id (int): Id du membre

        Returns:
            VocalProfile: Stats du membre
        """
        req = "SELECT * FROM Vocal WHERE id==?"
        curseur = await self.connection.execute(req, (member_id,))

        # Valeues attendue : id , time , afk , rang , name
        return await curseur.fetchone()
    
    async def get_leaderboard(self) -> dict[VocalProfile]:
        """Renvoie un dictionnaire de tout les profils

        Returns:
            dict[VocalProfile]: Profils de tout les membres
        """
        req = "SELECT * FROM Vocal ORDER BY rang LIMIT 5"
        stats = await self.connection.execute_fetchall(req)

        return {stat[0]: VocalProfile(*stat) for stat in stats}
   
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
    await bot.add_cog(Vocal(bot, bot.connection))