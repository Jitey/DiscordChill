import discord
from discord.ext import commands

from pathlib import Path
parent_folder = Path(__file__).resolve().parent
import json
import aiosqlite

from dataclasses import dataclass


from icecream import ic





@dataclass
class XpProfile:
    id: int
    name: str
    msg: int
    xp: int
    lvl: int
    xp_needed: int

    
    def check_lvl(self):
        current_lvl = self.lvl
        
        while not self.xp < self.xp_to_next_level():
            self.lvl += 1
        
        self.xp_needed = self.xp_to_next_level() - self.xp

        return self.lvl > current_lvl
    
    def xp_to_next_level(self):
        return 5 * (self.lvl ** 2) + (50 * self.lvl) + 100



class Rank(commands.Cog):
    def __init__(self, bot: commands.Bot, connection: aiosqlite.Connection)->None:
        self.bot = bot
        self.connection = connection



    @commands.hybrid_command(name='rang')
    async def rang(self, ctx: commands.Context)->discord.Message:
        member = ctx.author

        req = "SELECT * FROM Rank WHERE id==?"
        curseur = await self.connection.execute(req, (member.id,))

        # Valeues attendue : id , name , msg , xp , lvl
        if profile := await curseur.fetchone():
            return await ctx.send(f"{profile}")



    @commands.hybrid_command(name='leaderboard')
    async def leaderboard(self, ctx: commands.Context)->discord.Message:
        return await ctx.send("Commande en cours de développement")


    @commands.hybrid_command(name='dashboard')
    async def dashboard(self, ctx: commands.Context)->discord.Message:
        return await ctx.send("Commande en cours de développement")
        
        
    @commands.Cog.listener(name='on_message')
    async def message_sent(self, message: discord.Message)->None:
        member = message.author
        if member.id == self.bot.user.id:
            return
        
        if profile := await self.get_member_stats(member.id):
            ic(profile)
            stat = XpProfile(*profile)
            stat.msg += 1
            stat.xp += 50

            res = "UPDATE Rank SET msg=?, xp=?, lvl=? WHERE id==?"
            await self.connection.execute(res, (stat.msg, stat.xp, stat.lvl, member.id))
            await self.connection.commit()
        else:
            await self.create_xp_profile(member)
    
    

    
    async def create_xp_profile(self, member: discord.Member)->None:
        """Ajoutes une ligne à la base de donnée pour le membre

        Args:
            member (discord.Member): Membre discord
        """
        if member.id == self.bot.user.id:
            return

        req = "INSERT INTO Rank (id, name, msg, xp, lvl) VALUES (?,?,?,?,?)"
        await self.connection.execute(req, (member.id, member.name, 0, 0, 0))

        await self.connection.commit()

    async def get_member_stats(self, member_id: int)->XpProfile:
        """Renvoie les stats d'un membre

        Args:
            member_id (int): Id du membre

        Returns:
            XpProfile: Stats du membre
        """
        req = "SELECT * FROM Rank WHERE id==?"
        curseur = await self.connection.execute(req, (member_id,))

        # Valeues attendue : id , name , msg , xp , lvl
        return await curseur.fetchone()
    
    async def get_all_member_stats(self) -> dict[XpProfile]:
        """Renvoie un dictionnaire de tout les profils

        Returns:
            dict[XpProfile]: Profils de tout les membres
        """
        req = "SELECT * FROM Rank"
        profiles = await self.connection.execute_fetchall(req)

        return {id: XpProfile(id,tamp) for id, tamp in profiles}
   
   
    def load_json(self, file: str)->dict:
        """"Récupère les données du fichier json

        Args:
            file (str): Nom du fichier

        Returns:
            dict: Données enregistrées
        """
        with open(f"{parent_folder}/datafile/{file}.json", 'r') as f:
            return json.load(f)

    def update_logs(self, data: dict | list, path: str)->None:
        """Enregistre le fichier logs

        Args:
            data (dict): Données à enregistrer
            path (str): Chemin du fichier à enregistrer
        """
        with open(f"{parent_folder}/datafile/{path}.json", 'w') as f:
            json.dump(data,f,indent=2) 





async def setup(bot: commands.Bot)->None:
    await bot.add_cog(Rank(bot, bot.connection))