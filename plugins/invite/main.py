import discord
from discord.ext import commands

from pathlib import Path
parent_folder = Path(__file__).resolve().parent
import json
import aiosqlite
from sqlite3 import IntegrityError

from PIL import Image, ImageDraw
from io import BytesIO

from icecream import ic




class Invite(commands.Cog):
    def __init__(self, bot: commands.Bot, connection: aiosqlite.Connection)->None:
        self.bot = bot
        self.connection = connection
        
    
    @commands.Cog.listener(name="on_invite_create")
    async def on_invite_create(self, invite: discord.Invite) -> None:
        req = "INSERT INTO Invites (code, inviter_id, inviter_name, usage_count) VALUES (?,?,?,?)"

        try:
            await self.connection.execute(req, (invite.code, invite.inviter.id, invite.inviter.name, invite.uses))
            await self.connection.commit()
        except IntegrityError:
            pass
        
    
    @commands.hybrid_command(name="graph")
    async def inviter_graph(self, ctx: commands.Context):
        for id in await self.connection.execute_fetchall("SELECT id FROM Members"):
            res = await self.connection.execute_fetchall(f"SELECT name, (SELECT count(*) FROM Members WHERE invited_by=={id[0]}) FROM Members WHERE id=={id[0]}")
            name, count = res[0]
            if count != 0:
                ic(name,count)
        embed = discord.Embed(
            title="Répartition des inviters"
        )
        return await ctx.send(embed=embed)
        
    
    
    def load_json(self, file: str)->dict:
        """Récupère le fichier logs

        Returns:
            dict: Données logs enregistrées
        """
        with open(f"{parent_folder}/{file}.json", 'r') as f:
            return json.load(f)

    def write_json(self, data: dict, path: str):
        """Enregistre le fichier logs

        Args:
            data (dict): Données à enregistrer
        """
        with open(f"{parent_folder}/{path}.json", 'w') as f:
            json.dump(data,f,indent=2) 





async def setup(bot: commands.Bot)->None:
    await bot.add_cog(Invite(bot, bot.connection))