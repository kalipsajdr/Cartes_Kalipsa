class Marque:
    def __init__(self, id_marque, nom, coordonee):
        self.id = id_marque
        self.nom = nom
        self.coordonee = coordonee  # Ex: coordonnées X, Y sur la carte

    @classmethod
    def depuis_ligne(cls, ligne):
        """Crée une instance de Marque à partir d'une ligne du Google Sheet."""
        return cls(
            id_marque=ligne.get("ID"),
            nom=ligne.get("Nom"),
            coordonee=ligne.get("Coordonee", "")
        )