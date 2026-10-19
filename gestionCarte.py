import threading
import os
import streamlit as st

# Dossier local où seront stockées les images des cartes
DOSSIER_LOCAL = "cartes_images"
TAILLE_MAX_MO = 5
TAILLE_MAX_OCTETS = TAILLE_MAX_MO * 1024 * 1024

def uploader_fichier_en_arriere_plan(sheet, carte_id, image_bytes, nom_fichier):
    """
    Enregistre l'image localement en arrière-plan et met à jour Google Sheets.
    """
    try:
        # S'assurer que le dossier local existe
        os.makedirs(DOSSIER_LOCAL, exist_ok=True)
        
        # Chemin complet du fichier
        chemin_fichier = os.path.join(DOSSIER_LOCAL, nom_fichier)
        
        # Écriture du fichier sur le disque
        with open(chemin_fichier, "wb") as f:
            f.write(image_bytes)
            
        print(f"✅ Image enregistrée localement : {chemin_fichier}")

        # Mise à jour de la table "Carte" dans Google Sheets (Colonne C / Index 3 = NomFichier)
        ws_carte = sheet.worksheet("Carte")
        cellule_id = ws_carte.find(str(carte_id))
        if cellule_id:
            ws_carte.update_cell(cellule_id.row, 3, nom_fichier)

    except Exception as e:
        print(f"❌ Erreur lors de l'enregistrement local en arrière-plan : {e}")


def creer_nouvelle_carte(sheet, nom_carte, image_file):
    try:
        # Vérification de la taille du fichier (Maximum 5 Mo)
        if image_file.size > TAILLE_MAX_OCTETS:
            return False, f"Le fichier est trop volumineux. La taille maximale autorisée est de {TAILLE_MAX_MO} Mo."

        ws_carte = sheet.worksheet("Carte")
        toutes_cartes = ws_carte.get_all_records()

        nouveau_id_carte = max([int(c.get("ID", 0)) for c in toutes_cartes], default=0) + 1

        # Insertion initiale dans la base de données
        ws_carte.append_row([nouveau_id_carte, nom_carte, ""])

        st.session_state["id_carte_active"] = str(nouveau_id_carte)
        st.session_state["carte_courante"] = nom_carte

        if image_file is not None:
            image_bytes = image_file.getvalue()
            nom_fichier = image_file.name

            # Lancement du thread pour l'écriture locale (zéro latence UI)
            thread_upload = threading.Thread(
                target=uploader_fichier_en_arriere_plan,
                args=(sheet, nouveau_id_carte, image_bytes, nom_fichier)
            )
            thread_upload.daemon = True
            thread_upload.start()

        return True, nouveau_id_carte

    except Exception as e:
        return False, str(e)