# |----------Module d'environnement-----------|
from os import getenv
from dotenv import load_dotenv
from pathlib import Path
import glob
# |----------Module du projet-----------|
import discord
from discord.ext import commands


parent_folder = Path(__file__).resolve().parent
load_dotenv(dotenv_path=f"{parent_folder}/.env")

PREFIX = '='

async def load_all_extensions(bot: commands.Bot):
    for plugin in glob.glob(f"{parent_folder}/plugins/**"):
        await bot.load_extension(f"plugins.{plugin.split('/')[-1]}.main")
        


class ChillBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix=PREFIX, intents=discord.Intents.all())
    
    
    async def setup_hook(self) -> None:
        await load_all_extensions(self)
        synced = await self.tree.sync()
        print(f"{len(synced)} commandes synchroisées")

    
    async def on_ready(self) -> None:
        activity = discord.CustomActivity("En train de chill")
        await self.change_presence(status=discord.Status.online, activity=activity)
        
        print(f'Connecté en tant que {self.user.name}')




if __name__=='__main__':
    bot = ChillBot()
    bot.run(getenv("BOT_TOKEN"))