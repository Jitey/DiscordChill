import discord
from discord.ext import commands

from pathlib import Path
from os.path import join
import json
import aiosqlite
from sqlite3 import IntegrityError, OperationalError
parent_folder = Path(__file__).resolve().parent

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
from datetime import datetime as dt

from numpy import random as rd

from icecream import ic
from logger_config import setup_logger


logger = setup_logger()




class Bienvenue(commands.Cog):
    def __init__(self, bot: commands.Bot, connections: dict[str, aiosqlite.Connection])->None:
        self.bot = bot
        self.connections = connections
        self.channels = self.load_channels()
        self.left_msg = self.load_json('left_msg')
        
    
    @commands.Cog.listener(name='on_ready')
    async def on_ready(self):
        self.channels = self.load_channels()


    @commands.Cog.listener(name='on_member_join')
    async def message_bienvenue(self, member: discord.Member):
        serveur = member.guild
        invite = await self.update_invites(member.guild)
        inviter = invite.inviter
        connection = self.connections[serveur.name]
        channels = self.channels[serveur.name]
        
        if not member.bot:
            #|----------Message de bienvenue----------|
            embed = discord.Embed(
                title=f"Bienvenue {member.display_name} !",
                # description=f"Choisis tes rôles dans {self.channels['role'].jump_url} avec la commande `/role`",
                description=f"Choisis tes rôles dans `Salons et rôles`",
                color=discord.Color.blurple()
            )
            embed.set_thumbnail(url=member.guild.icon.url)
            embed.set_footer(icon_url=inviter.avatar.url ,text=f"Invité par {inviter.display_name} | Membre {self.member_count(serveur)}")

            image = self.image_bienvenue(member, serveur)
            embed.set_image(url="attachment://welcome_card.png")
            
            await channels['bienvenue'].send( embed=embed, file=image)

            #|----------Update de la DB----------|
            req1 = "INSERT INTO Members (id, name, invited_by, join_method, join_date) VALUES (?,?,?,?,?)"
            req2 = "UPDATE Members set invite_count = invite_count + 1"
            try:
                await connection.execute(req1, (member.id,member.name,inviter.id,invite.code,member.joined_at))
                await connection.execute(req2)
                await connection.commit()
            except IntegrityError:
                pass
            await connection.commit()
                
        else:
            logs = self.load_json('logs')
            logs['bot_count'] += 1
            self.update_logs(logs, 'logs')

        #|----------Member count----------|
        await  channels['member_count'].edit(name=f"{self.member_count(serveur)} membres")


    @commands.Cog.listener(name='on_member_remove')
    async def message_au_revoir(self, member: discord.Member):
        serveur = member.guild
        channels = self.channels[serveur.name]
        connection = self.connections[serveur.name]
        
        #|----------Message de départ----------|
        if not member.bot:
            await channels['bienvenue'].send(f"**{member.display_name}** {rd.choice(self.left_msg[serveur.name])} !")

            #|----------Member count----------|
            await channels['member_count'].edit(name=f"{self.member_count(serveur)} membres")
            
            try:
                req1 = "DELETE FROM Members WHERE id == ?"
                req2 = "UPDATE Members set invite_count = invite_count - 1"

                await connection.execute(req1, (member.id,))
                await connection.commit()
                await connection.execute(req2)
                await connection.commit()
            except OperationalError as error:
                logger.info(f"{error.__class__.__name__} {member.display_name} {error}")

                
        else:
            logs = self.load_json('logs')
            logs['bot_count'] -= 1
            self.update_logs(logs, 'logs')
        

     
     
    async def update_invites(self, server: discord.Guild) -> discord.Invite:
        connection = self.connections[server.name]
        req1 = "SELECT uses FROM Invites WHERE code == ?"
        req2 = "UPDATE Invites SET uses=?, inviter_name=? WHERE code == ?"
        req3 = "INSERT INTO Invites (code, inviter_id, inviter_name, uses) VALUES (?,?,?,?)"

        for invite in await server.invites():
            if uses := await connection.execute_fetchall(req1, (invite.code,)):
                if uses[0][0] != invite.uses:
                    await connection.execute(req2, (invite.uses,invite.inviter.name,invite.code))
                    await connection.commit()

                    return invite 
            else:
                await connection.execute(req3, (invite.code,invite.inviter.id,invite.inviter.name,invite.uses))
                await connection.commit()
                
                return invite
                
            
    def member_count(self, serveur: discord.Guild)->int:
        """Renvoie le nombre de membre d'un serveur sans compter les bots

        Args:
            serveur (discord.Guild): Serveur discord

        Returns:
            int: Nombre de membre
        """
        logs = self.load_json('logs')[serveur.name]
        return serveur.member_count - logs['bot_count']

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

    def centrer_image(self, parent: Image, enfant: Image)->tuple[int]:
        """Renvoie les coordonnées pour centrer une image sur une autre

        Args:
            parent (Image): L'image de fond
            enfant (Image): L'image à centrer

        Returns:
            tuple[int]: Les coordonnées à donner à l'image à centrer
        """
        xp , yp = parent.size
        xe , ye = enfant.size
        return xp//2 - xe//2 , yp//2 - ye//2

    def get_image_from_url(self, url: str)->Image:
        """Télécharge une image viens son lien

        Args:
            url (str): Lien de l'image

        Returns:
            Image: Image téléchargé
        """
        response = requests.get(url)
        image_content = BytesIO(response.content)
        return Image.open(image_content)

    def rogner_image(self, image: Image)->Image:
        """Arrondi une image carré au format PNG

        Args:
            image (Image): Image à rogner

        Returns:
            Image: Image rognée
        """
        side_length = min(image.size)

        # Créer un masque circulaire
        mask = Image.new('L', (side_length, side_length), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, side_length, side_length), fill=255)

        # Appliquer le masque à l'image d'origine
        cropped_image = Image.new('RGBA', (side_length, side_length))
        cropped_image.paste(image, mask=mask)
        
        return cropped_image
        
    def write_on_image(self, image: Image, text: str, size: int, pos: tuple, text_color: int=0xFFFFFF, border_size: int=0, border_color: int=0x000000)->Image:
        """Écris du texte centrée en x sur une image à une position y données

        Args:
            image (Image): Image sur laquelle écrire
            text (str): Texte à écrire
            taille (int): Taille de la police
            pos (tuple): Position en y
            couleur (int, optional): Couleur du texte. Default blanc.

        Returns:
            Image: Image avec le texte écrit dessus
        """
        draw = ImageDraw.Draw(image)
        r , g , b = self.color_hexa_to_rgb(text_color)

        font = ImageFont.truetype(f"{parent_folder}/font/chillow.ttf", size,)
        _ , _ , w , h = draw.textbbox((0, 0), text, font)

        x , y = image.size
        draw.multiline_text((x//2 - w//2, pos), text, font=font, fill=(r, g, b), stroke_width=border_size, stroke_fill=self.color_hexa_to_rgb(border_color))

        return image

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

    def image_bienvenue(self, user: discord.Member, serveur: discord.Guild)->Image:
        """Génère une image de bienvenue aux nouveaux arrivant

        Args:
            user (discord.user): Nouveau membre sur le serveur
            serveur (discord.Guild): Serveur où le membre viens d'arriver

        Returns:
            Image: L'image de bienvenue générée
        """
        # Récupère l'avatar du membre et le rogne
        avatar = self.rogner_image(self.get_image_from_url(user.avatar.url).resize((200,200)))
        avatar_y = 35

        # Image de fond
        if banner := user.banner:
            # Bannière nitro si existante
            background = self.get_image_from_url(banner.url)
        else:
            # Sinon le fond default
            try:
                background = Image.open(f"{parent_folder}/image/{serveur.name}.png")
            except FileNotFoundError:
                background = Image.open(f"{parent_folder}/image/default.png")
        background.resize((1100,500)).convert('RGBA')
            
        # Dessine une bordure blanche autour de l'avatar
        border = ImageDraw.Draw(background)                                                      
        xp , yp = self.centrer_image(background,avatar)
        x , y = avatar.size
        offset = 5
        border.ellipse((xp-offset, avatar_y-offset, xp+x+offset, avatar_y+y+offset), fill=(255,255,255))
        
        # Copie de l'avatar sur l'image en dernière pour qu'il soit au premier plan
        background.paste(avatar, (xp, avatar_y), avatar)
        
        # Texte de bienvenue
        card = self.write_on_image(background, f"{user.name} viens chill avec nous", size=40, pos=270, border_size=4)
        
        return self.discord_image(card, "welcome_card")

    def member_count(self, serveur: discord.Guild)->int:
        """Renvoie le nombre de membre d'un serveur sans compter les bots

        Args:
            serveur (discord.Guild): Serveur discord

        Returns:
            int: Nombre de membre
        """
        ic(serveur)
        ic(serveur.name)
        logs = self.load_json('logs')[serveur.name]
        return serveur.member_count - logs['bot_count']

    def find_invite(self):
        self.connection.execute()


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
        with open(f"{parent_folder}/datafile/{file}.json", 'r') as f:
            return json.load(f)

    def update_logs(self, data: dict, path: str)->None:
        """Enregistre le fichier logs

        Args:
            data (dict): Données à enregistrer
            path (str): Chemin du fichier à enregistrer
        """
        with open(join(parent_folder,"datafile","path",".json"), 'w') as f:
            json.dump(data,f,indent=2) 







async def setup(bot: commands.Bot)->None:
    await bot.add_cog(Bienvenue(bot, bot.connections))