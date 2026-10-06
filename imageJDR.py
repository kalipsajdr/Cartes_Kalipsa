from PIL import Image
import requests
from io import BytesIO
from marqueurMap import Marqueur


class ImageJDR:
    def __init__(self, source_image, marqueurs: list[Marqueur] = None):
        """
        Gère l'image de la carte et sa liste de marqueurs associés.
        """
        self.monImage = self._charger_image(source_image)
        self.marqueurs = marqueurs if marqueurs is not None else []

    def _charger_image(self, source):
        """Charge l'image depuis une URL (Drive ou web) ou un fichier local."""
        if isinstance(source, Image.Image):
            return source
        elif isinstance(source, str) and (source.startswith("http://") or source.startswith("https://")):
            # Nettoyage de l'URL Google Drive
            if 'drive.google.com' in source:
                file_id = source.split('/d/')[1].split('/')[0]
                source = f"https://lh3.googleusercontent.com/d/{file_id}"
            
            response = requests.get(source)
            return Image.open(BytesIO(response.content))
        else:
            return Image.open(source)

    def ajouter_marqueur(self, marqueur: Marqueur):
        """Ajoute un marqueur à la carte."""
        self.marqueurs.append(marqueur)