import os
import pathlib
import glob

import discord
from discord.ext import commands, tasks

import git

from icecream import ic
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')



IGNORE_EXTENSIONS = []
parent_folder = '/'.join(str(pathlib.Path(__file__).resolve().parent).split('/')[:-1])
GITHUB_REPOSITORY = "/home/container/DiscordChill"



def path_from_extension(extension: str) -> pathlib.Path:
    return pathlib.Path(extension.replace('.', os.sep)+'.py')



class HotReload(commands.Cog):
    """
    Cog for reloading extensions as soon as the file is edited
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.hot_reload_loop.start()
        self.load_new_cogs_loop.start()
        self.pull_from_github.start()


    def cog_unload(self):
        self.hot_reload_loop.stop()
        self.load_new_cogs_loop.stop()
        self.pull_from_github.stop()

    
    

    @tasks.loop(seconds=5)
    async def pull_from_github(self, repository_path: str=GITHUB_REPOSITORY)->None:
        # Ouvrir le référentiel existant
        repo = git.Repo(repository_path)

        try:
            # Effectuer un pull depuis la branche actuelle
            if repo.is_dirty():
                repo.git.pull() 
                logging.info("Pull réussi")
        except git.GitCommandError as e:
            logging.info(f"Erreur lors du pull : {e}")



                
    @tasks.loop(seconds=3)
    async def hot_reload_loop(self):
        
        for extension in list(self.bot.extensions.keys()):
            if extension in IGNORE_EXTENSIONS:
                continue
            path = path_from_extension(extension)
            time = os.path.getmtime(path)

            try:
                if self.last_modified_time[extension] == time:
                    continue
            except KeyError:
                self.last_modified_time[extension] = time

            try:
                await self.bot.reload_extension(extension)
            except commands.ExtensionError:
                print(f"Couldn't reload extension: {extension.split('.')[1]}")
            except commands.ExtensionNotLoaded:
                continue
            else:
                print(f"Reloaded extension: {extension.split('.')[1]}")
            finally:
                self.last_modified_time[extension] = time

            
    @tasks.loop(seconds=3)
    async def load_new_cogs_loop(self):
        for plugin in glob.glob(f"{parent_folder}/**"):
            extension = '.'.join(plugin.split('/')[-2:]) + '.main'
            path = path_from_extension(extension)
            time = os.path.getmtime(path)
            
            if extension in self.bot.extensions:
                continue
            
            try:
                await self.bot.load_extension(extension)
            except commands.ExtensionError:
                print(f"Couldn't load extension: {extension.split('.')[1]}")
            except commands.ExtensionNotLoaded:
                continue
            else:
                print(f"Loaded extension: {extension.split('.')[1]}")
            finally:
                self.last_modified_time[extension] = time


    @load_new_cogs_loop.before_loop
    @hot_reload_loop.before_loop
    @pull_from_github.before_loop
    async def demarage(self):
        await self.bot.wait_until_ready()


    @load_new_cogs_loop.before_loop
    @hot_reload_loop.before_loop
    async def cache_last_modified_time(self):
        self.last_modified_time = {}
        # Mapping = {extension: timestamp}
        for extension in self.bot.extensions.keys():
            if extension in IGNORE_EXTENSIONS:
                continue
            path = path_from_extension(extension)
            time = os.path.getmtime(path)
            self.last_modified_time[extension] = time





async def setup(bot: commands.Bot)->None:
    await bot.add_cog(HotReload(bot))