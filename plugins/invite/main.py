import discord
from discord.ext import commands

from pathlib import Path
parent_folder = Path(__file__).resolve().parent
import json
import aiosqlite
from sqlite3 import IntegrityError

from icecream import ic




class Invite(commands.Cog):
    def __init__(self, bot: commands.Bot, connections: dict[str, aiosqlite.Connection])->None:
        self.bot = bot
        self.connections = connections
        
    
    @commands.Cog.listener(name="on_invite_create")
    async def on_invite_create(self, invite: discord.Invite) -> None:
        """Ajoute une nouvelle invite à la base de données si elle n'existe pas déjà

        Args:
            invite (discord.Invite): Invite à ajouter
        """
        connection = self.connections[invite.guild.name]
        req = "INSERT INTO Invites (code, inviter_id, inviter_name, usage_count) VALUES (?,?,?,?)"

        try:
            await connection.execute(req, (invite.code, invite.inviter.id, invite.inviter.name, invite.uses))
            await connection.commit()
        except IntegrityError:
            pass
        
    
    @commands.hybrid_command(name="graph")
    async def inviter_graph(self, ctx: commands.Context):
        connection = self.connections[ctx.guild.name]
        embed = discord.Embed(
            title="Répartition des inviters",
            color=discord.Color.random()
        )
        embed.set_author(icon_url=ctx.author.avatar.url,name=ctx.author.display_name)

        req = "SELECT id, invite_count FROM Members WHERE invite_count > 0 ORDER BY invite_count DESC"
        for rang, res in enumerate(await connection.execute_fetchall(req)):
            member_id, count = res
            member = self.bot.get_user(member_id)
            embed.add_field(name=f"{self.rank_emoji(rang+1)} {member.display_name}", value=f"{count} membres invités", inline=False)
            ic(member.name,count)

        return await ctx.send(embed=embed)
    
    
    async def pages_count(self, serveur: discord.Guild) -> int:
        """Renvoie le nombre de page totale du leaderboard

        Returns:
            int: Nombre de page totale
        """
        connection = self.connections[serveur.name]
        req = f"SELECT count(*) FROM Rank"
        res = await connection.execute(req)
        tamp = (await res.fetchone())[0]

        if tamp % 5:
            return  tamp // 5 + 1
        else:
            return  tamp // 5
        
    def rank_emoji(self, rang)->str:
        match rang:
            case 1:
                return ':first_place:'
            case 2:
                return ':second_place:' 
            case 3:
                return ':third_place:'
            case _:
                return f"{rang}:"
        
    
    
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
    await bot.add_cog(Invite(bot, bot.connections))