# Python 3.11

# |----------Module d'environnement-----------|
from os import getenv, sep
from os.path import join
from dotenv import load_dotenv
from pathlib import Path
import glob
# |----------Module du projet-----------|
import discord
from discord.ext import commands
import aiosqlite

from logs.logger_config import setup_logger


logger = setup_logger()


# env const
PARENT_FOLDER = Path(__file__).resolve().parent
load_dotenv(dotenv_path=join(PARENT_FOLDER,".env"))



# Discord const
PREFIX = '+'
IGNORED_EXTENSIONS = ['ping', 'dashboard']
DEV_IDS = [306081415643004928]

 
        


class ChillBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix=PREFIX, intents=discord.Intents.all())
        self.IGNORED_EXTENSIONS = IGNORED_EXTENSIONS
        self.DEV_IDS = DEV_IDS
    
    
    async def setup_hook(self) -> None:
        self.connections = await self.connect_to_db()
        for connection in self.connections.values():
            await self.create_table(connection)
        
        await self.load_all_extensions()
        synced = await self.tree.sync()
        logger.info(f"{len(synced)} commandes synchroisées")

    async def on_ready(self) -> None:
        activity = discord.CustomActivity("En train de chill")
        await self.change_presence(status=discord.Status.online, activity=activity)
        
        logger.info(f'Connecté en tant que {self.user.name}')
    
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Fonction appelée lorsque le bot rejoint un serveur.

        Args:
            guild (discord.Guild): Le serveur sur lequel le bot a été ajouté.
        """
        # Check if the guild is already in the database
        list_db = glob.glob(join(self.WORKSPACE,'databases','**'))
        if guild.name in list_db:
            logger.info(f"Le serveur {guild.name} est déjà dans la base de données.")
        else:
            # Create a new database for the guild
            logger.info(f"Ajout du serveur {guild.name} à la base de données.")
            self.create_db(guild.name)
    
    
    async def load_all_extensions(self):
        for plugin in glob.glob(join(PARENT_FOLDER,"plugins","**")): 
            extention = plugin.split(sep)[-1]
            if extention not in self.IGNORED_EXTENSIONS:
                try:
                    await self.load_extension(f"plugins.{extention}.main")
                    logger.info(f"Extension {extention} chargée")
                except Exception as error:
                    logger.error(error)
    
    async def connect_to_db(self) -> dict[str, aiosqlite.Connection]:
        """Connecte le bot aux bases de données

        Returns:
            list[aiosqlite.Connection]: liste des connexions aux bases de données
        """
        connections = {}
        for server_db in glob.glob(join(PARENT_FOLDER,'databases','**')):
            server_name = server_db.split(sep)[-1][:-7]
            logger.info(f"Connection à la BDD {server_name}")
            connection = await aiosqlite.connect(server_db)
            connections[server_name] = connection
        
        return connections

    async def create_db(self, server: discord.Guild) -> None:
        connection = await aiosqlite.connect(join(PARENT_FOLDER,'databases',f'{server.name}.sqlite'))
        await self.create_table(connection)
        self.connections[server.name] = connection
    
    async def create_table(self, connection: aiosqlite.Connection) -> None:
        req = "CREATE TABLE IF NOT EXISTS Rank (id INTEGER PRIMARY KEY, name str, msg int, xp int, lvl int, rang int, add_xp_counter int, remove_xp_counter int, added_xp int, removed_xp int)"
        await connection.execute(req)
        await connection.commit()   
        
        req = "CREATE TABLE IF NOT EXISTS Vocal (id INTEGER PRIMARY KEY, name str, time int, afk int, lvl int, rang int, add_xp_counter int, remove_xp_counter int, added_xp int, removed_xp int)"
        await connection.execute(req)
        await connection.commit()   
        
    @commands.hybrid_command(name='reload_db')
    async def reload_db(self, ctx: commands.Context) -> None:
        """Recharge la base de données du serveur

        Args:
            ctx (commands.Context): Contete de la commande
        """
        server = ctx.guild.name
        if ctx.author.guild_permissions.administrator or ctx.author.id in self.DEV_IDS:
            # On ferme la connexion à la base de données
            self.connections[server].close()

            # On recharge la base de données
            logger.info(f"Reloading database for {server}")
            self.connections[server] = await aiosqlite.connect(join(PARENT_FOLDER,'databases',f'{server}.sqlite'))
            await self.create_table(self.connections[server])
            await ctx.reply(f"Base de données {server} rechargée")
        else:
            ctx.send("Tu n'as pas la permission pour ça", ephemeral=True)
    
    
    async def send_ctx_error(self, ctx: commands.Context, error: Exception) -> discord.Message:
        embed = discord.Embed(
                        title=f"{type(error).__name__}",
                        description=error,
                    )
        return await ctx.reply(embed=embed, mention_author=False)

    async def send_interaction_error(self, interaction: discord.Interaction, error: Exception) -> discord.Message:
        embed = discord.Embed(
                        title=f"{type(error).__name__}",
                        description=error,
                    )
        return await interaction.reply(embed=embed)

    def safe_get(data: dict | list, dot_chained_keys: str):
        """Renvoie un élément précis de données au format json

        data = {'a':{'b':[{'c':1}]}}
        safe_get(data, 'a.b.0.C') -> 1
        Args:
            data (dict | list): Les données à traiter
            dot_chained_keys (str): Les clés d'accès sous forme de chaine str

        Returns:
            _type_: L'élément cherché
        """
        keys = dot_chained_keys.split('.')
        for key in keys:
            try:
                data = data[int(key)] if isinstance(data,list) else data[key]
            except (KeyError, TypeError, IndexError, ValueError) as error:
                logger.error(f"{error.__class__.__name__} {error}")
        return data


if __name__=='__main__':
    bot = ChillBot()
    try:
        bot.run(getenv("BOT_TOKEN"))
    except ConnectionResetError as error:
        logger.fatal(error)