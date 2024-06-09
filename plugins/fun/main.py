from discord.ext import commands

from pathlib import Path
import json

from numpy import random as rd

from icecream import ic


parent_folder = Path(__file__).resolve().parent



class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot)->None:
        self.bot = bot


    @commands.hybrid_command(name='golmon', description="Reformule le message avec des majuscules aléatoirement")
    async def golmon(msg: str, occurence: float=1/3)->str:
        assert msg != "", "le message est vide"
        
        res = []
        for c in msg:
            if rd.binomial(1,occurence):
                res.append(c.upper())
            else:
                res.append(c)
        
        return "".join(res)
    
    
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
    await bot.add_cog(Fun(bot))