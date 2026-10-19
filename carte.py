class Carte:
    def __init__(self, id_carte, nom):
        self.id = id_carte
        self.nom = nom  # Nom du fichier de la carte sur le Drive

    @classmethod
    def depuis_ligne(cls, ligne):
        """Crée une instance de Carte à partir d'une ligne du Google Sheet."""
        return cls(
            id_carte=str(ligne.get("ID")),
            nom=ligne.get("Nom")
        )