import discord
from discord.ext import commands

from pathlib import Path
parent_folder = Path(__file__).resolve().parent
import math
import aiosqlite
import subprocess



# |----------Anexes----------|
def round_it(x:float, sig: int) -> float:
    """Arrondi à nombre au neme chiffre signifactif

    Args:
        x (int | float): Nombre à arrondir
        sig (int): Nombre de chiffre significatif à garder

    Returns:
        int | float: Nombre arrondi
    """
    return round(x, sig - int(math.floor(math.log10(abs(x)))) - 1)

def format_float(number: int) -> str:
    """Convertir le nombre en chaîne de caractères

    Args:
        number (int | float): Nombre à convertir

    Returns:
        str: Nombre en str
    """
    str_number = str(number)

    return str_number.rstrip('0').rstrip('.') if '.' in str_number else str_number
    
def pretty_print(xp: int)->str:
    """Afficher les nombres arrondi à e3

    Args:
        xp (int): Nombre à arrondir

    Returns:
        str: Nombre arrondi

    Example:
        1543 -> 1,54k
    """
    rounded_xp = round_it(xp, 3)
    return rounded_xp if rounded_xp < 1e3 else f"{format_float(rounded_xp/1e3)}k"

def ordinal(n: int):
    """Renvoie le nombre ordinaire correspondant pour un entier passé

    Args:
        n (int): Entier

    Returns:
        _type_: Nombre ordinaire correspondant
    """
    match n:
        case 1:
            return '1st'
        case 2:
            return '2nd'
        case 3:
            return '3rd'
        case _:
            return f'{n}th'
        


class Dashboard(commands.Cog):
    def __init__(self, bot: commands.Bot, connection: aiosqlite.Connection) -> None:
        self.bot = bot
        self.connection = connection

    @commands.hybrid_command(name="dashboard", description="Affiche le leaderboard complet")
    async def leaderboard(self, ctx: commands.Context) -> discord.Message:
        """Affiche le leaderboard complet

        Args:
            ctx (commands.Context): Contexte de la commande

        Returns:
            discord.Message: Message
        """
        subprocess.run(['streamlit', 'run', f'{parent_folder}/leaderboard.py'])
        membre = ctx.author

        await self.init_streamlit_page()
        self.leaderboard(await self.load_data_from_sql())

        embed = discord.Embed(
            title=f"Leaderboard {self.leaderboard_version[type].lower()}",
            description="Accède au classement [ici](https://discordchill-test.streamlit.app/)",
            color=discord.Color.blurple()
        )
        embed.set_author(name=membre.display_name, icon_url=membre.avatar)
        await ctx.reply(embed=embed)
   

async def setup(bot: commands.Bot)->None:
    await bot.add_cog(Dashboard(bot, bot.connection))