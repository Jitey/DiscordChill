import streamlit as st
import pandas as pd

def main():
    st.title("Votre leaderboard")

    # Exemple de données (remplacez cela par votre logique pour récupérer les données)
    data = {
        "Utilisateur": ["Utilisateur1", "Utilisateur2", "Utilisateur3"],
        "Points": [100, 75, 50]
    }

    # Créez un DataFrame pandas avec vos données
    df = pd.DataFrame(data)

    # Affichez le tableau avec les données
    st.table(df)

if __name__ == "__main__":
    main()
