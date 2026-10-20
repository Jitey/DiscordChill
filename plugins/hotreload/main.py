import os
import pathlib
import glob

import discord
from discord.ext import commands, tasks
from bot import ChillBot


from icecream import ic
from logs.logger_config import setup_logger


logger = setup_logger()



IGNORE_EXTENSIONS = ['ping','dashboard']
plugins_folder = '/'.join(str(pathlib.Path(__file__).resolve().parent).split('/')[:-1])
PARENT_FOLDER = pathlib.Path(__file__).resolve().parent




def path_from_extension(extension: str) -> pathlib.Path:
    """Convertit une extension de module en un chemin vers le fichier main
    Par exemple, 'plugins.hotreload.main' devient 'plugins/hotreload/main.py'

    Args:
        extension (str): Le nom de l'extension à convertir

    Returns:
        pathlib.Path: Le chemin vers le fichier main de l'extension
    """
    return pathlib.Path(extension.replace('.', os.sep)+'.py')



class HotReload(commands.Cog):
    """
    Cog for reloading extensions as soon as the file is edited
    """

    def __init__(self, bot: ChillBot):
        self.bot = bot
        self.hot_reload_loop.start()
        self.load_new_cogs_loop.start()


    def cog_unload(self):
        self.hot_reload_loop.stop()
        self.load_new_cogs_loop.stop()

    
    

    @tasks.loop(seconds=3)
    async def hot_reload_loop(self):
        for extension in list(self.bot.extensions.keys()):
            extension_name = extension.split('.')[1]
            if extension_name in self.bot.IGNORED_EXTENSIONS:
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
                logger.warning(f"Couldn't reload extension: {extension.split('.')[1]}")
            except commands.ExtensionNotLoaded:
                continue
            else:
                logger.info(f"Reloaded extension: {extension.split('.')[1]}")
            finally:
                self.last_modified_time[extension] = time

            
    @tasks.loop(seconds=3)
    async def load_new_cogs_loop(self):
        for plugin in glob.glob(f"{plugins_folder}/**"):
            extension = '.'.join(plugin.split('/')[-2:]) + '.main'
            path = path_from_extension(extension)
            time = os.path.getmtime(path)
            
            extension_name = extension.split('.')[1]
            if extension in self.bot.extensions or extension_name in self.bot.IGNORED_EXTENSIONS:
                continue
            
            try:
                await self.bot.load_extension(extension)
            except commands.ExtensionError:
                logger.warning(f"Couldn't load extension: {extension.split('.')[1]}")
            except commands.ExtensionNotLoaded:
                continue
            else:
                logger.info(f"Loaded extension: {extension.split('.')[1]}")
            finally:
                self.last_modified_time[extension] = time


    @load_new_cogs_loop.before_loop
    @hot_reload_loop.before_loop
    async def cache_last_modified_time(self):
        await self.bot.wait_until_ready()
        self.last_modified_time = {}
        # Mapping = {extension: timestamp}
        for extension in self.bot.extensions.keys():
            if extension in self.bot.IGNORED_EXTENSIONS:
                continue
            path = path_from_extension(extension)
            time = os.path.getmtime(path)
            self.last_modified_time[extension] = time





async def setup(bot: commands.Bot)->None:
    await bot.add_cog(HotReload(bot))