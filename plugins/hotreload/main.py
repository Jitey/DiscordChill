import os
import pathlib
import glob

import discord
from discord.ext import commands, tasks

import git
import json
from datetime import datetime as dt

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')



IGNORE_EXTENSIONS = ['ping']
plugins_folder = '/'.join(str(pathlib.Path(__file__).resolve().parent).split('/')[:-1])
parent_folder = pathlib.Path(__file__).resolve().parent
GITHUB_REPOSITORY = "/home/container/DiscordChill"
GITHUB_REPOSITORY = "/Users/jitey/Documents/Python/Bot/Discord/DiscordChill"




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
        """Pull automatiquement sur les nouveaux commit

        Args:
            repository_path (str, optional): Chemin local du répertoire
        """
        try:
            repo = git.Repo(repository_path)
            
            with open(f"{parent_folder}/save.json", 'r') as f:
                last_commit_saved_str = json.load(f)['last_commit']
            last_commit_saved = dt.strptime(last_commit_saved_str, "%Y-%m-%d %H:%M:%S%z")
            try:
                last_commit = repo.head.commit
                if last_commit.committed_datetime > last_commit_saved:
                    repo.git.pull() 
                    with open(f"{parent_folder}/save.json", 'w') as f:
                        json.dump({'last_commit': f"{last_commit.committed_datetime}"}, f, indent=2)
                    logging.info("Pull réussi")
            except git.GitCommandError as e:
                logging.info(f"Erreur lors du pull : {e}")
        except Exception as e:
            logging.info(e.__class__)
            logging.error(e)


                
    @tasks.loop(seconds=3)
    async def hot_reload_loop(self):
        for extension in list(self.bot.extensions.keys()):
            extension_name = extension.split('.')[1]
            if extension_name in IGNORE_EXTENSIONS:
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
        for plugin in glob.glob(f"{plugins_folder}/**"):
            extension = '.'.join(plugin.split('/')[-2:]) + '.main'
            path = path_from_extension(extension)
            time = os.path.getmtime(path)
            
            extension_name = extension.split('.')[1]
            if extension in self.bot.extensions or extension_name in IGNORE_EXTENSIONS:
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


    @pull_from_github.before_loop
    async def demarage(self):
        await self.bot.wait_until_ready()
        with open(f"{parent_folder}/save.json", 'r') as f:
            self.last_commit = json.load(f)['last_commit']


    @load_new_cogs_loop.before_loop
    @hot_reload_loop.before_loop
    async def cache_last_modified_time(self):
        await self.bot.wait_until_ready()
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