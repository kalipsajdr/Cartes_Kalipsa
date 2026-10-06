class Marqueur:
    def __init__(self, x: int, y: int, description: str = "", lien: str = None):
        """
        Représente un point d'intérêt sur une carte JDR.
        :param x: Position X sur l'image (en pixels)
        :param y: Position Y sur l'image (en pixels)
        :param description: Texte descriptif du lieu
        :param lien: Identifiant ou URL vers une sous-carte
        """
        self.coord = (x, y)
        self.description = description
        self.lien = lien

    def est_clique(self, click_x: int, click_y: int, tolerance: int = 20) -> bool:
        """Vérifie si un clic Streamlit est proche du marqueur."""
        mx, my = self.coord
        return abs(mx - click_x) <= tolerance and abs(my - click_y) <= tolerance

    def __repr__(self):
        return f"Marqueur(coord={self.coord}, desc='{self.description}')"