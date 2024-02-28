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
from datetime import datetime as dt, timedelta

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
    




class ResetView(discord.ui.View):
    def __init__(self, connection: aiosqlite.Connection, member_target: discord.Member)->None:
        super().__init__()
        self.connection = connection
        self.member_target = member_target


    @discord.ui.button(label="Oui", style=discord.ButtonStyle.danger)
    async def confirmer(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        member = interaction.user

        if member.guild_permissions.administrator:
            res = "UPDATE Vocal SET time=0, afk=0, lvl=0, add_xp_counter=0, remove_xp_counter=0, added_xp=0, removed_xp=0 WHERE id==?"
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
        req = "UPDATE Vocal SET rang=DENSE_RANK() OVER (ORDER BY Vocal.time DESC) FROM Vocal t2 WHERE t2.id = Vocal.id"
        await self.connection.execute(req)
        await self.connection.commit()






@dataclass
class VocalProfile:
    id: int
    name: str
    time_spend: int
    afk: int
    lvl: int
    rang: int
    add_xp_counter: int
    remove_xp_counter: int
    added_xp: int
    removed_xp: int
    current_xp: int=0
    xp_needed: int=0

    
    def __post_init__(self)->None:
        """Calcule l'xp requit et l'xp avant le prochain lvl
        après l'initialisation de l'instance
        """
        self.check_lvl()
        next_lvl = self.lvl + 1
        self.xp_needed = 5 * (next_lvl ** 2) + (50 * next_lvl) + 100

        self.current_xp = self.time_spend - self.time_to_level(self.lvl)

    
    def check_lvl(self)->bool:
        """Calcule le niveau à partir de l'xp totale

        Returns:
            bool: Si on a rank up ou non
        """
        current_lvl = self.lvl
        
        if self.current_xp >= self.xp_needed:
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

    def print_tps(self, time_spend: int) -> str:
        if time_spend < 60:
            return f"{time_spend}min"
            
        tps = dt.min + timedelta(minutes=time_spend)
        tps_sliced =  {'j ': tps.day - 1, 'h': tps.hour, '': tps.minute}
        return "".join(
            f"{value}{title}" for title, value in tps_sliced.items() if value != 0
        )
        
    
    def create_progress_bar(self, color: int | tuple=0x000000)->discord.File:
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
        self.afk_channel = discord.VoiceChannel
        
    
    @commands.Cog.listener(name="on_ready")
    async def init_vocal(self):
        """Comme un __post_init__ mais sur l'event on_ready"""
        self.afk_channel = self.bot.get_channel(self.channels['afk'])




    @commands.hybrid_command(name='add_time')
    async def add_time(self, ctx: commands.Context, member_target: discord.Member, amout: int)->bool:
        """Ajoute de l'xp à un membre

        Args:
            ctx (commands.Context): Contexte de la commande
            member_target (discord.Member): Membre target
            amout (int): Quantité

        Returns:
            bool: L'opération a échoué ou non
        """
        member = ctx.author

        if member.guild_permissions.administrator:
            await self.manage_xp('add', member_target.id, amout)
            embed = discord.Embed(
                title="Ajout de temps",
                description=f"{amout}min ajouté à {member_target.display_name}",
                color=discord.Color.random()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("Tu n'as pas la permission pour ça", ephemeral=True)
        
        return member.guild_permissions.administrator

    
    @commands.hybrid_command(name='remove_time')
    async def remove_time(self, ctx: commands.Context, member_target: discord.Member, amout: int)->bool:
        """Retire de l'xp à un membre

        Args:
            ctx (commands.Context): Contexte de la commande
            member_target (discord.Member): Membre target
            amout (int): Quantité

        Returns:
            bool: L'opération a échoué ou non
        """
        member = ctx.author

        if member.guild_permissions.administrator:
            await self.manage_xp('remove', member_target.id, amout)
            embed = discord.Embed(
                title="Retrait de temps",
                description=f"{amout}min retiré à {member_target.display_name}",
                color=discord.Color.random()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("Tu n'as pas la permission pour ça", ephemeral=True)

        return member.guild_permissions.administrator

    
    @commands.hybrid_command(name='reset_time')
    async def reset_time(self, ctx: commands.Context, member_target: discord.Member)->bool:
        """Remet à 0 l'xp du membre

        Args:
            ctx (commands.Context): Contexte de la commande
            member_target (discord.Member): Membre target

        Returns:
            bool: L'opération a échoué ou non
        """
        member = ctx.author

        if member.guild_permissions.administrator:
            await ctx.send("Tu es sûr de vouloir faire ça ?", view=ResetView(self.connection,member_target))
        else:
            await ctx.send("Tu n'as pas la permission pour ça", ephemeral=True)
        
        return member.guild_permissions.administrator


    @commands.hybrid_command(name='vrang')
    async def vrang(self, ctx: commands.Context, member: discord.Member=None)->None:
        """Affiche les infos relative au membre

        Args:
            ctx (commands.Context): Contexte de la commande
            member (discord.Member, optional): Membre target. Defaults to Auteur de la commande.

        Returns:
            discord.Message: _description_
        """
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
            embed.add_field(name="", value=f"{stat.print_tps(stat.current_xp)} / {stat.print_tps(stat.xp_needed)}", inline=True)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)

            progress_bar = stat.create_progress_bar(int(color))
            embed.set_image(url="attachment://progress_bar.png")
            await ctx.send(embed=embed, file=progress_bar)

        else:
            await ctx.send("Tu ne t'es jamais connecté en vocal")


    @commands.hybrid_command(name='vleaderboard')
    async def leaderboard(self, ctx: commands.Context)->discord.Message:
        """Affiche les 5 premiers membres du classement

        Args:
            ctx (commands.Context): Contexte de la commande

        Returns:
            discord.Message: Message du leaderboard
        """
        embed = discord.Embed(
            title="Leaderboard vocal",
            color=discord.Color.random()
        )
        res = await self.get_leaderboard()
        embed.set_author(icon_url=ctx.author.avatar.url,name=ctx.author.display_name)
        for id , stat in res.items():
            member = self.bot.get_user(id)
            embed.add_field(name=f"{self.rank_emoji(stat.rang)} {member.display_name}", value=f"Total Tps: {stat.print_tps(stat.time_spend)} (level {stat.lvl})", inline=False)
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
                uzox = self.bot.get_user(760027263046909992)
                perms = discord.PermissionOverwrite()

                channel = await serveur.create_voice_channel(member.display_name,category=category, overwrites={uzox: perms})
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
        """Marque le début de la connection vocal

        Args:
            member (discord.Member): Memnre
            before (discord.VoiceState): État vocal avant la connexion
            after (discord.VoiceState): État vocal après la connexion
        """
        try:
            # Si le membre viens de se connecter
            if not before.channel or before.channel.id == self.afk_channel.id:
                # Si il n'est pas seul dans le channel
                if len(after.channel.members) >= 2:
                    self.voice_time_counter[member.id] = time.perf_counter()
        
        except AttributeError:
            pass    
    
    
    @commands.Cog.listener(name="on_voice_state_update")
    async def on_vocale_leave(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState)->None:
        """Compte le temps passé en vocal

        Args:
            member (discord.Member): Memnre
            before (discord.VoiceState): État vocal avant la connexion
            after (discord.VoiceState): État vocal après la connexion
        """
        try:
            # Si le membre viensde se déconnecter
            if not after.channel or after.channel.id == self.afk_channel.id:
                tps = [int(time.perf_counter() - self.voice_time_counter[member.id]) , 0]
                if before.channel.id == self.afk_channel.id:
                    tps.reverse()

                if profile := await self.get_member_stats(member.id):
                    await self.on_vocal_xp(profile, *tps)
                    self.voice_time_counter[member.id] = None
                else:
                    ic('else')
                    await self.create_vocal_profile(member)
                    await self.on_vocale_leave(member, before, after)

        except (AttributeError, KeyError, TypeError):
            pass
   
   
    @commands.Cog.listener(name="on_voice_state_update")
    async def anti_farm(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState)->None:
        """Annule la prise en compte du temps pour quelqu'un qui reste seul dans un channel

        Args:
            member (discord.Member): Membre
            before (discord.VoiceState): État vocal avant la connexion
            after (discord.VoiceState): État vocal après la connexion
        """
        # Sur une déconection
        if after.channel is None: 
    
            # Si le channel existe toujours et qu'il reste quelqu'un seul membre humain
            if before.channel and self.is_voice_channel_empty(before.channel):
                last_member = before.channel.members[0]
                await self.on_vocale_leave(last_member, before, after)
        
        # Sur une connection
        if before.channel is None: 
            
            # Si un deuxieme humain se connecte
            if after.channel and self.is_voice_channel_enought_fill(after.channel):
                for participant in after.channel.members:
                    if participant != member:
                        first_member = participant
                        break

                self.voice_time_counter[first_member.id] = time.perf_counter()
        
        ic(self.voice_time_counter)
    
    
    def is_voice_channel_empty(self, channel: discord.VoiceChannel) -> bool:
        """Check si le salon ne contient qu'un seul membre non bot

        Args:
            channel (_type_): Salon vocal

        Returns:
            bool: Résultat sous forme de boléen
        """
        return sum(int(not participant.bot) for participant in channel.members) == 1

    def is_voice_channel_enought_fill(self, channel: discord.VoiceChannel) -> bool:
        """Check si le salon ne contient plus d'un seul membre non bot

        Args:
            channel (_type_): Salon vocal

        Returns:
            bool: Résultat sous forme de boléen
        """
        return sum(int(not participant.bot) for participant in channel.members) > 1



    async def manage_xp(self, action: str, member_id: int, amount: int)->None:
        """Ajoute ou retire la quantité d'xp donné

        Args:
            action (str): Ajouter ou retirer de l'xp
            member_id (int): Id du membre
            amount (int): Quantité d'xp
        """
        stat = VocalProfile(*await self.get_member_stats(member_id))
        
        if action == 'add':
            stat.time_spend += amount
            xp_counter = stat.add_xp_counter + 1
            res = "UPDATE Vocal SET time=?, afk=?, lvl=?, add_xp_counteer=?, added_xp=? WHERE id==?"
        elif action == 'remove':
            stat.time_spend -= amount
            xp_counter = stat.remove_xp_counter + 1
            res = "UPDATE Vocal SET time=?, afk=?, lvl=?, remove_xp_counteer=?, removeed_xp=? WHERE id==?"
            
        stat.check_lvl()

        await self.connection.execute(res, (stat.time_spend, stat.afk, stat.lvl, xp_counter, amount, stat.id))
        await self.connection.commit()

        await self.update_classement()
    
    async def on_vocal_xp(self, stat: tuple | VocalProfile, time_spend: int, afk: int)->None:
        """Ajoute de l'xp au membre et regard si il a level up

        Args:
            stat (tuple | XpProfile): Stats du membre
            time_spend (int): Temps en seconde
            afk (int): Temps d'afk en seconde
        """
        if isinstance(stat, tuple):
            stat = VocalProfile(*stat)
        
        stat.time_spend += time_spend // 60
        stat.afk += afk
        req = "UPDATE Vocal SET time=?, afk=?, lvl=? WHERE id==?"
        
        if stat.check_lvl():
            channel = self.bot.get_channel(self.channels['rank'])
            await channel.send(f"<@{stat.id}> Tu viens de passer niveau {stat.lvl} en vocal !")
        
        await self.connection.execute(req, (stat.time_spend, afk, stat.lvl, stat.id))
        await self.connection.commit()

        await self.update_classement()
    
    async def update_classement(self)->None:
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
                return f"`#{rang}`"

   
 
   
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