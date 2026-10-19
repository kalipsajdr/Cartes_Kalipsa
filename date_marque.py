class DateMarque:
    def __init__(self, id_marque, debut, fin, descriptif, id_cartes):
        self.id_marque = id_marque
        self.debut = debut
        self.fin = fin
        self.descriptif = descriptif
        self.id_cartes = id_cartes

    @classmethod
    def depuis_ligne(cls, ligne):
        """Crée une instance de DateMarque à partir d'une ligne du Google Sheet."""
        return cls(
            id_marque=ligne.get("IDMarque"),
            debut=ligne.get("Debut"),
            fin=ligne.get("Fin"),
            descriptif=ligne.get("Descriptif", ""),
            id_cartes=ligne.get("IDCartes")
        )