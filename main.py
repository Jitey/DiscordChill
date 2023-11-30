# |----------Module d'environnement-----------|
from os import getenv
from dotenv import load_dotenv
from pathlib import Path
import glob
# |----------Module du projet-----------|
import discord
from discord.ext import commands
import aiosqlite


parent_folder = Path(__file__).resolve().parent
load_dotenv(dotenv_path=f"{parent_folder}/.env")

PREFIX = '='

IGNORE_EXTENSIONS = ['ping']

async def load_all_extensions(bot: commands.Bot):
    for plugin in glob.glob(f"{parent_folder}/plugins/**"):
        extention = plugin.split('/')[-1]
        if extention not in IGNORE_EXTENSIONS:
            await bot.load_extension(f"plugins.{extention}.main")
        


class ChillBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix=PREFIX, intents=discord.Intents.all())
    
    
    async def setup_hook(self) -> None:
        self.connection = await aiosqlite.connect('main.sqlite')
        await self.create_table(self.connection)
        
        await load_all_extensions(self)
        synced = await self.tree.sync()
        print(f"{len(synced)} commandes synchroisées")

    
    async def on_ready(self) -> None:
        activity = discord.CustomActivity("En train de chill")
        await self.change_presence(status=discord.Status.online, activity=activity)
        
        print(f'Connecté en tant que {self.user.name}')
    
    
    async def create_table(self, connection: aiosqlite.Connection)->None:
        req = "CREATE TABLE IF NOT EXISTS Rank (id INTEGER PRIMARY KEY, name str, msg int, xp int, lvl int, rang int)"
        await connection.execute(req)
        await connection.commit()   
        
    @commands.hybrid_command(name='reload_db')
    async def reload_databse(self, ctx: commands.Context)->None:
        self.connection = await aiosqlite.connect('main.sqlite')



if __name__=='__main__':
    bot = ChillBot()
    bot.run(getenv("BOT_TOKEN"))