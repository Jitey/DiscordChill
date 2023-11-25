import discord
from discord.ext import commands

from pathlib import Path
import json

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests

parent_folder = Path(__file__).resolve().parent




class Bienvenue(commands.Cog):
    def __init__(self, bot: commands.Bot)->None:
        self.bot = bot
        

    @commands.Cog.listener(name='event')
    async def on_member_join(self, member):
        logs = self.load_logs()
        serveur = member.guild
        user = member
        
        #|----------Message de bienvenue----------|
        msg = f"Yo ! Bienvenue {member.mention}, je t'invite à choisir tes rôles dans {self.channels['role'].jump_url}"
        image = self.image_bienvenue(user, serveur)
        
        await self.channels['information'].send(msg, file=image)
            
        #|----------Member count----------|
        if member.bot:
            self.logs['bot_count'] += 1
            self.update_logs(logs)
        await  self.channels['member_count'].edit(name=f"{self.member_count(serveur)} membres")

    @commands.Cog.listener(name='event')
    async def on_member_remove(self, member):
        logs = self.load_logs()
        serveur = member.guild
        
        #|----------Message de départ----------|
        await self.channels['information'].send(f"**{member.display_name}** viens juste de quitter le serveur...")
            
        #|----------Member count----------|
        if member.bot:
            logs['bot_count'] -= 1
            self.update_logs(logs)
        await  self.channels['member_count'].edit(name=f"{self.member_count(serveur)} membres")

        
    def member_count(self, serveur: discord.Guild)->int:
        """Renvoie le nombre de membre d'un serveur sans compter les bots

        Args:
            serveur (discord.Guild): Serveur discord

        Returns:
            int: Nombre de membre
        """
        logs = self.load_logs()
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
        
    def ecrire_on_image(self, image: Image, text: str, taille: int, pos: tuple, couleur: int=0xFFFFFF)->Image:
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
        r , g , b = self.color_hexa_to_rgb(couleur)

        font = ImageFont.truetype(font='Verdana', size=taille)
        _ , _ , w , h = draw.textbbox((0, 0), text, font)

        x , y = image.size    
        draw.text((x//2 - w//2, pos), text, font=font, fill=(r, g, b))

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

    def image_bienvenue(self, user: discord.user, serveur: discord.Guild)->Image:
        """Génère une image de bienvenue aux nouveaux arrivant

        Args:
            user (discord.user): Nouveau membre sur le serveur
            serveur (discord.Guild): Serveur où le membre viens d'arriver

        Returns:
            Image: L'image de bienvenue générée
        """
        # Récupère l'avatar du membre et le rogne
        avatar = self.rogner_image(self.get_image_from_url(user.avatar.url).resize((240,240)))
        avatar_y = 60

        # Génère le contour de couleur de l'image
        image = Image.new('RGB', (1100,500), self.color_hexa_to_rgb(0x17181E))

        # Si le mebre a discord nitro sa bannière est prise pour le fond
        if banner :=user.banner:
            background = self.get_image_from_url(banner.url).resize((100,460))
        # Sinon le fond est noir
        else:
            background = Image.new('RGB', (1000,460), self.color_hexa_to_rgb(0x060608))
        image.paste(background, self.centrer_image(image,background))

        # Dessine une bordure blanche autour de l'avatar
        border = ImageDraw.Draw(image)                                                      
        xp , yp = self.centrer_image(image,avatar)
        x , y = avatar.size
        offset = 5
        border.ellipse((xp-offset, avatar_y-offset, xp+x+offset, avatar_y+y+offset), fill=(255,255,255))
        
        # Copie de l'avatar sur l'image en dernière pour qu'il soit au premier plan
        image.paste(avatar, (xp, avatar_y), avatar)
        
        # Texte de bienvenue
        image = self.ecrire_on_image(image, f"{user.name} viens chill avec nous", taille=36, pos=350)
        image = self.ecrire_on_image(image, f"Membre #{self.member_count(serveur)}", taille=30, pos=406, couleur=0xB4B4B4)
        
        return self.discord_image(image, "card")

    def member_count(self, serveur: discord.Guild)->int:
        """Renvoie le nombre de membre d'un serveur sans compter les bots

        Args:
            serveur (discord.Guild): Serveur discord

        Returns:
            int: Nombre de membre
        """
        logs = self.load_logs()
        return serveur.member_count - logs['bot_count']

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
    await bot.add_cog(Bienvenue(bot))