import streamlit as st
import gspread

def enregistrer_nouveau_marqueur(sheet, carte_courante, nom_lieu, coordonnees, debut_marque, fin_marque, description, lien_id_carte=""):
    """
    Enregistre le marqueur temporaire dans 'Marque' (6 colonnes) 
    et ses informations temporelles dans 'DateMarque' (5 colonnes).
    """
    try:
        # --- 1. Ajout dans la table "Marque" ---
        ws_marques_obj = sheet.worksheet("Marque")
        toutes_marques = ws_marques_obj.get_all_records()
        prochain_id = max([int(m.get("ID", 0)) for m in toutes_marques], default=0) + 1
        
        # Récupération sécurisée de l'ID ou du nom de l'utilisateur depuis st.session_state
        user_info = st.session_state.get("utilisateur", "Anonyme")
        
        if isinstance(user_info, dict):
            # Si c'est un dictionnaire, on extrait l'ID (ou le Nom)
            id_utilisateur = user_info.get("ID", user_info.get("Nom", "Anonyme"))
        else:
            id_utilisateur = user_info
        
        # Inscription des 6 colonnes exactes de la table Marque :
        # A: ID | B: Nom | C: Coordonee | D: Temporaire | E: LienIdCarte | F: IdUtilisateur
        ws_marques_obj.append_row([
            prochain_id,
            nom_lieu,
            coordonnees,
            "Oui",  # Toujours "Oui" car il s'agit d'un nouveau marqueur temporaire
            str(lien_id_carte) if lien_id_carte else "",
            str(id_utilisateur)
        ])
        
        # --- 2. Ajout dans la table "DateMarque" ---
        ws_dates_obj = sheet.worksheet("DateMarque")
        
        # Récupération sécurisée de l'ID de la carte active
        id_carte_active = "1"
        if carte_courante and hasattr(carte_courante, 'id'):
            id_carte_active = str(carte_courante.id)
        else:
            ws_cartes = sheet.worksheet("Carte").get_all_records()
            nom_carte_actuelle = st.session_state.get("carte_courante", "Carte du Monde")
            for c in ws_cartes:
                if str(c.get("Nom")) == str(nom_carte_actuelle):
                    id_carte_active = str(c.get("ID", "1"))
                    break
        
        # Inscription dans DateMarque :
        # A: IDMarque | B: Debut | C: Fin | D: Descriptif | E: IDCartes
        ws_dates_obj.append_row([
            prochain_id,
            str(debut_marque),
            str(fin_marque),
            description,
            id_carte_active
        ])
        
        return True, prochain_id
        
    except Exception as e:
        return False, str(e)