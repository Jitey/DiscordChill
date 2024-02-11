import discord
from discord.ext import commands

from pathlib import Path
parent_folder = Path(__file__).resolve().parent
import json
import math
from sqlite3 import *

import streamlit as st
import pandas as pd


# |----------Anexes----------|
def round_it(x:float, sig: int) -> float:
    """Arrondi à nombre au neme chiffre signifactif

    Args:
        x (int | float): Nombre à arrondir
        sig (int): Nombre de chiffre significatif à garder

    Returns:
        int | float: Nombre arrondi
    """
    return round(x, sig - int(math.floor(math.log10(abs(x)))) - 1)

def format_float(number: int) -> str:
    """Convertir le nombre en chaîne de caractères

    Args:
        number (int | float): Nombre à convertir

    Returns:
        str: Nombre en str
    """
    str_number = str(number)

    return str_number.rstrip('0').rstrip('.') if '.' in str_number else str_number
    
def pretty_print(xp: int)->str:
    """Afficher les nombres arrondi à e3

    Args:
        xp (int): Nombre à arrondir

    Returns:
        str: Nombre arrondi

    Example:
        1543 -> 1,54k
    """
    rounded_xp = round_it(xp, 3)
    return rounded_xp if rounded_xp < 1e3 else f"{format_float(rounded_xp/1e3)}k"

def ordinal(n: int):
    """Renvoie le nombre ordinaire correspondant pour un entier passé

    Args:
        n (int): Entier

    Returns:
        _type_: Nombre ordinaire correspondant
    """
    match n:
        case 1:
            return '1st'
        case 2:
            return '2nd'
        case 3:
            return '3rd'
        case _:
            return f'{n}th'


def rank_image(data: pd.DataFrame) -> list:
    img = []
    for _ , row in data.iterrows():
        match row["rang"]:
            case 1:
                img.append(f"<img src='https://mee6.xyz/assets/1st_place-e4d1acfc.svg'>")
            case 2:
                img.append(f"<img src='https://mee6.xyz/assets/2nd_place-b8abf0ce.svg'>")
            case 3:
                img.append(f"<img src='https://mee6.xyz/assets/3rd_place-5212c9ca.svg'>")
            case _:
                img.append(f"<h4> {row['rang']} </h4>")
    return img

def init_streamlit_page() -> None:
    st.set_page_config(layout="wide",
                       page_title="Leaderboard",
                       page_icon="📊"
                       )
    st.title('Leaderboard') 
    st.header('Salons textuels') 
    st.sidebar.success("Classement à afficher")
    # with st.container():
        # st.markdown("""<style> 
        #                 body{bakgroun-color=#F792E5;}
        #                 </style>
        #             """, unsafe_allow_html=True)

def top_border():
    with st.container():
        # Style de l'entête
        st.markdown(
            f"""<div style="display: flex;">
                    <div style="width:83%; display: flex;"> 
                        <div style="width:5%;"> </div>
                        <div>
                            <p class="text-sm text-dark-300 w-14 flex justify-center">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="text-dark-700 h-6 w-6">
                                    <circle cx="12" cy="7.2" r="3.2" fill="#9195AB"> </circle>
                                    <ellipse cx="12" cy="16" rx="5.6" ry="3.2" fill="#9195AB"> </ellipse>
                                </svg>
                            </p>
                        </div>
                    </div>
                    <div style="width:17%; display: flex;">
                    <div style="width:5%;"> </div>
                        <div style="width:33%; display: flex;">
                            <p class="text-sm text-dark-300 text-center hidden lg:block">
                                <svg width="24" height="24" viewBox=" 0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="text-dark-700 h-6 w-6 m-auto">
                                    <path d="M3.776 9.226c.676-2.942 2.88-5.229 5.69-5.901l.224-.054a9.853 9.853 0 014.593 0l.381.092c2.713.649 4.842 2.857 5.495 5.698l.089.386a9.955 9.955 0 010 4.455c-.678 2.948-3.19 5.025-6.076 5.025h-1.061a.866.866 0 00-.797.563c-.481 1.23-1.825 1.835-2.998 1.333l-.118-.05c-2.711-1.16-4.732-3.646-5.419-6.635a11.008 11.008 0 01-.003-4.912z"
                                        fill="#9195AB">
                                    </path>
                                    <path d=="M12.314 19.49l-.698-.273.698.273zM3.78 14.138l-.73.168.73-.168zm-.003-4.912l-.731-.168.73.168zm16.472.221l.73-.168-.73.168zm0 4.455l-.731-.168.73.168zM9.316 20.823l.295-.69-.295.69zM9.69 3.271l.174.73-.174-.73zm4.593 0l-.175.73.175-.73zM9.198 20.773l-.295.69.295-.69zm5.466-17.41l.175-.73-.175.73zM20.16 9.06l-.731.168.73-.168zM9.466 3.325l-.174-.73.174.73zm-.77 4.983a.75.75 0 000 1.5v-1.5zm6.032 1.5a.75.75 0 100-1.5v1.5zm-6.032 1.956a.75.75 0 000 1.5v-1.5zm3.839 1.5a.75.75 0 000-1.5v1.5zM9.64 4.054l.223-.053-.35-1.459-.222.053.35 1.46zm4.467-.053l.381.091.35-1.459-.381-.091-.35 1.459zM9.611 20.134l-.118-.05-.59 1.378.118.05.59-1.378zm9.817-10.905l.089.386 1.462-.336-.09-.386-1.461.336zm-5.256 8.948h-1.061v1.5h1.061v-1.5zm-1.061 0c-.679 0-1.258.434-1.495 1.04l1.397.546c.028-.07.079-.086.098-.086v-1.5zM4.51 13.97a10.259 10.259 0 01-.003-4.576l-1.462-.336a11.758 11.758 0 00.003 5.248l1.462-.336zm15.007-4.355a9.205 9.205 0 010 4.12l1.462.335a10.705 10.705 0 000-4.79l-1.462.335zM9.02 21.513c1.592.68 3.368-.155 3.992-1.75l-1.397-.546c-.34.867-1.251 1.24-2.005.917l-.59 1.379zM9.864 4a9.103 9.103 0 014.244 0l.35-1.459a10.603 10.603 0 00-4.943 0l.35 1.459zm-.371 16.082c-2.478-1.06-4.347-3.345-4.983-6.113l-1.462.336c.738 3.209 2.911 5.898 5.855 7.156l.59-1.379zm10.024-6.349c-.605 2.63-2.831 4.443-5.345 4.443v1.5c3.26 0 6.056-2.342 6.807-5.607l-1.462-.336zM14.49 4.092c2.42.58 4.345 2.557 4.938 5.137l1.462-.336c-.713-3.103-3.046-5.54-6.051-6.26l-.35 1.459zM9.291 2.595c-3.102.743-5.51 3.259-6.247 6.463l1.462.336c.616-2.68 2.617-4.737 5.134-5.34l-.35-1.459zm-.596 7.213h6.032v-1.5H8.696v1.5zm0 3.456h4.839v-1.5H8.696v1.5z"
                                        fill="currentColor">
                                    </path>
                                </svg>
                            </p> 
                        </div>
                        <div style="width:33%;">
                            <p class="text-sm text-dark-300 text-center">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="text-dark-700 h-6 w-6 m-auto">
                                    <path fill-rule="evenodd" clip-rule="evenodd" d="M12 20C15.5346 20 18.4 17.1346 18.4 13.6C18.4 10.0653 15.5346 7.19995 12 7.19995C8.46538 7.19995 5.6 10.0653 5.6 13.6C5.6 17.1346 8.46538 20 12 20ZM12 11.2C11.7728 11.2 11.6208 11.4726 11.3168 12.018L11.2381 12.159C11.1517 12.314 11.1085 12.3915 11.0412 12.4426C10.9738 12.4937 10.89 12.5127 10.7222 12.5507L10.5695 12.5852C9.97917 12.7188 9.684 12.7856 9.61378 13.0114C9.54356 13.2372 9.74478 13.4725 10.1472 13.9431L10.2513 14.0649C10.3657 14.1986 10.4229 14.2655 10.4486 14.3482C10.4743 14.4309 10.4657 14.5201 10.4484 14.6986L10.4327 14.861C10.3718 15.4889 10.3414 15.8028 10.5252 15.9424C10.7091 16.082 10.9854 15.9547 11.5382 15.7002L11.6812 15.6344C11.8382 15.5621 11.9168 15.5259 12 15.5259C12.0832 15.5259 12.1618 15.5621 12.3188 15.6344L12.4618 15.7002C13.0146 15.9547 13.2909 16.082 13.4748 15.9424C13.6586 15.8028 13.6282 15.4889 13.5673 14.861L13.5516 14.6986C13.5343 14.5201 13.5257 14.4309 13.5514 14.3482C13.5771 14.2655 13.6343 14.1986 13.7487 14.0649L13.8528 13.9431C14.2552 13.4725 14.4564 13.2372 14.3862 13.0114C14.316 12.7856 14.0208 12.7188 13.4305 12.5852L13.2778 12.5507C13.11 12.5127 13.0262 12.4937 12.9588 12.4426C12.8915 12.3915 12.8483 12.314 12.7619 12.159L12.6832 12.018C12.3792 11.4726 12.2272 11.2 12 11.2Z" fill="#9195AB"></path><path d="M11.2 4H12.8C14.3085 4 15.0627 4 15.5314 4.46863C15.9934 4.93064 15.9999 5.67027 16 7.13657C14.8382 6.41602 13.4677 6 12 6C10.5323 6 9.16184 6.41602 8 7.13657C8.00009 5.67027 8.00662 4.93064 8.46863 4.46863C8.93726 4 9.69151 4 11.2 4Z"
                                        fill="#9195AB">
                                    </path>
                                </svg>
                            </p> 
                        </div>
                    </div>
            """, unsafe_allow_html=True
        )

def leaderboard(data: pd.DataFrame) -> None:
    img = rank_image(data)
    # Pour chaque joueur dans le leaderboard
    for index , row in data.iterrows():
        # Conteneur avec les infos du joueur
        with st.container():
            # Style du bandeau
            st.markdown(
                f"""<div style="background-color: #1D1E24; padding: 1px; border-radius: 10px; margin-bottom: 30px; display: flex;">
                        <div style="width:83%; display: flex;">
                            <div style="width:1%;"> </div>
                            <div style="width:3%;"> {img[index]} </div>
                            <div style="width:80%;"> <h4> {row["name"]} </h4> </div> 
                        </div>
                        <div style="width:17%; display: flex;">
                            <div style="width:33%;"> <h4> {pretty_print(row["msg"])} </h4> </div>
                            <div style="width:33%;"> <h4> {pretty_print(row["xp"])} </h4> </div>
                            <div style="width:33%;"> <h4> {row["lvl"]} </h4> </div>
                        </div>
                    </div>""",
                unsafe_allow_html=True
            )


def main():
    with open(f"{parent_folder}/mee6.html") as f:
        print(f.read())
        
    with connect("/Users/jitey/Documents/Python/Bot/Discord/DiscordChill/main.sqlite") as connection:
        req = "SELECT * FROM Rank ORDER BY rang"
        leaderboard_data = pd.read_sql(req, connection)

    init_streamlit_page()
    top_border()
    leaderboard(leaderboard_data)



if __name__ == '__main__':
    main()