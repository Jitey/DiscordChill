import discord
from discord.ext import commands

from pathlib import Path
import json
parent_folder = Path(__file__).resolve().parent

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests





class Bienvenue(commands.Cog):
    def __init__(self, bot: commands.Bot)->None:
        self.bot = bot


    @commands.Cog.listener(name='on_ready')
    async def initialisation(self):
        self.channels = self.load_channels()
        

    @commands.Cog.listener(name='on_member_join')
    async def message_bienvenue(self, member: discord.Member):
        serveur = member.guild
        
        #|----------Message de bienvenue----------|
        if not member.bot:
            embed = discord.Embed(
                title=f"Bienvenue {member.display_name} !",
                description=f"Choisis tes rôles dans {self.channels['role'].jump_url} avec la commande `/role`",
                color=discord.Color.blurple()
            )
            embed.set_thumbnail(url=member.guild.icon.url)
            embed.set_footer(icon_url=member.avatar.url ,text=f"{member.display_name} | Membre {self.member_count(serveur)}")

            image = self.image_bienvenue(member, serveur)
            embed.set_image(url="attachment://welcome_card.png")
            
            await self.channels['information'].send( embed=embed, file=image)
                
        else:
            logs = self.load_json('logs')
            logs['bot_count'] += 1
            self.update_logs(logs, 'logs')

        #|----------Member count----------|
        await  self.channels['member_count'].edit(name=f"{self.member_count(serveur)} membres")


    @commands.Cog.listener(name='on_member_remove')
    async def message_au_revoir(self, member: discord.Member):
        logs = self.load_json('logs')
        serveur = member.guild
        
        #|----------Message de départ----------|
        if not member.bot:
            await self.channels['information'].send(f"**{member.display_name}** s'en est allé vers d'autres horizons...")
            
        else:
            logs['bot_count'] -= 1
            self.update_logs(logs, 'logs')

        #|----------Member count----------|
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
        
    def ecrire_on_image(self, image: Image, text: str, size: int, pos: tuple, text_color: int=0xFFFFFF, border_size: int=0, border_color: int=0x000000)->Image:
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

        font = ImageFont.truetype(f"{parent_folder}/font/chillow.ttf", size)
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
        avatar = self.rogner_image(self.get_image_from_url(user.avatar.url).resize((240,240)))
        avatar_y = 60

        # Image de fond
        if banner := user.banner:
            # Bannière nitro si existante
            background = self.get_image_from_url(banner.url).resize((1000,460))
        else:
            # Sinon le fond default
            background = Image.open(f"{parent_folder}/image/background.gif").resize((1100,500)).convert('RGBA')
            
        # Dessine une bordure blanche autour de l'avatar
        border = ImageDraw.Draw(background)                                                      
        xp , yp = self.centrer_image(background,avatar)
        x , y = avatar.size
        offset = 5
        border.ellipse((xp-offset, avatar_y-offset, xp+x+offset, avatar_y+y+offset), fill=(255,255,255))
        
        # Copie de l'avatar sur l'image en dernière pour qu'il soit au premier plan
        background.paste(avatar, (xp, avatar_y), avatar)
        
        # Texte de bienvenue
        card = self.ecrire_on_image(background, f"{user.name} viens chill avec nous", size=60, pos=350, border_size=4)
        
        return self.discord_image(card, "welcome_card")

    def member_count(self, serveur: discord.Guild)->int:
        """Renvoie le nombre de membre d'un serveur sans compter les bots

        Args:
            serveur (discord.Guild): Serveur discord

        Returns:
            int: Nombre de membre
        """
        logs = self.load_json('logs')
        return serveur.member_count - logs['bot_count']

    def load_channels(self) -> dict:
        return {
            channel_name: self.bot.get_channel(channel_id)
            for channel_name, channel_id in self.load_json('channels').items()
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
        with open(f"{parent_folder}/datafile/{path}.json", 'w') as f:
            json.dump(data,f,indent=2) 







async def setup(bot: commands.Bot)->None:
    await bot.add_cog(Bienvenue(bot))