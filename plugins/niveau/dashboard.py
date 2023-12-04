import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO


class ProgressCircle():
    def __init__(self, progress, label: str="") -> None:
        self.fig, self.ax = plt.subplots()
        self.progress = progress
        self.label = label
        self.draw()


    def draw(self):
        # Ajouter un cercle extérieur
        width = 0.47
        circle_outer = plt.Circle((0.5, 0.5), width, color='lightgray', fill=False, linewidth=12)
        self.ax.add_patch(circle_outer)

        # Ajouter un arc de progression
        theta_start = 360 * (1 - self.progress / 100)
        wedge = patches.Wedge((0.5, 0.5), width + 0.02, theta_start + 90, 360 + 90, color='blue', width=0.04)
        self.ax.add_patch(wedge)

        # Ajouter du texte pour afficher le pourcentage de progression
        self.ax.text(0.5, 0.5, f'{self.label}', ha='center', va='center', fontsize=150)

        # Paramètres d'affichage
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.axis('off')
        
    
    def resize_to_byte(self):
        buf = BytesIO()
        self.fig.savefig(buf, format='PNG')
        buf.seek(0)
        return buf




def main():
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        st.text("🥇")
        
    with c2:
        pass

    with c3:
        st.text("jiitey")
    
    with c4:
        st.write("2.6k")
    
    with c5:
        st.write("51.8k")
    
    with c6:
        circ = ProgressCircle(progress=30, label=88)
        img_buf = circ.resize_to_byte()
        img_height = 100  # Ajustez la hauteur selon vos besoins
        st.image(img_buf, width=50, use_column_width=False)

    


if __name__=='__main__':
    main()