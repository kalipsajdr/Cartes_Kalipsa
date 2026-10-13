import re
import io
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import streamlit as st

@st.cache_data(ttl=300)
def charger_liens_importants(sheet_id: str) -> dict:
    """Charge l'onglet LiensImportants sous forme de dictionnaire {Nom: Lien}."""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=LiensImportants"
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        # Création du dictionnaire Nom -> Lien
        liens = dict(zip(df['Nom'].astype(str).str.strip(), df['Lien'].astype(str).str.strip()))
        return liens
    except Exception as e:
        return {}

def convertir_lien_drive_image(url: str) -> str:
    """Convertit un lien Google Drive (fichier ou dossier) en URL d'image directe."""
    if 'drive.google.com' in url:
        # Si c'est un lien de fichier /file/d/ID/
        match_file = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
        if match_file:
            file_id = match_file.group(1)
            return f"https://lh3.googleusercontent.com/d/{file_id}"
        
        # Si c'est un lien de dossier /folders/ID
        match_folder = re.search(r'/folders/([a-zA-Z0-9_-]+)', url)
        if match_folder:
            folder_id = match_folder.group(1)
            # Pour un dossier, on peut cibler le premier fichier ou utiliser le lien direct de thumbnail
            return f"https://drive.google.com/thumbnail?id={folder_id}&sz=w1000"
            
    return url

def charger_image_depuis_drive(nom_fichier: str):
    """Télécharge l'image depuis Google Drive en mémoire via le compte de service."""
    try:
        scopes = ["https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        service = build('drive', 'v3', credentials=creds)
        
        # Recherche du fichier par son nom
        query = f"name = '{nom_fichier}' and trashed = false"
        results = service.files().list(q=query, pageSize=1, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if not files:
            st.error(f"Fichier '{nom_fichier}' introuvable sur le Drive.")
            return None
            
        file_id = files[0]['id']
        
        # Téléchargement du contenu en mémoire
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        fh.seek(0)
        return fh
    except Exception as e:
        st.error(f"Erreur lors du chargement de {nom_fichier} : {e}")
        return None