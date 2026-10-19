import hashlib
import streamlit as st
import pandas as pd

def hashar_email(email: str) -> str:
    """Hache l'adresse e-mail en SHA-256 de façon irréversible."""
    email_clean = email.strip().lower()
    return hashlib.sha256(email_clean.encode('utf-8')).hexdigest()

def verifier_utilisateur(email_hashe: str, bdd_df: pd.DataFrame) -> dict:
    """Recherche l'empreinte hachée dans la colonne 'Mail'."""
    if bdd_df is None or bdd_df.empty or 'Mail' not in bdd_df.columns:
        return None

    match = bdd_df[bdd_df['Mail'].astype(str).str.strip() == email_hashe]
    if not match.empty:
        row = match.iloc[0]
        return {
            "ID": row.get("ID", ""),
            "Nom": row.get("Nom", "Joueur"),
            "Mail_Hash": email_hashe,
            "Droit": row.get("Droit", "Joueur")
        }
    return None

def ajouter_utilisateur_bdd(pseudo: str, email_hashe: str, sheet_id: str):
    """
    Ajoute un utilisateur à la base de données via gspread et le compte de service.
    """
    bdd = st.session_state.get("bdd_utilisateurs", pd.DataFrame())
    nouveau_id = len(bdd) + 1 if not bdd.empty else 1
    
    nouvel_user_dict = {
        "ID": nouveau_id,
        "Nom": pseudo.strip(),
        "Mail": email_hashe,
        "Droit": "Joueur"
    }
    
    # 1. Mise à jour de la BDD locale dans la session Streamlit
    nouveau_df = pd.concat([bdd, pd.DataFrame([nouvel_user_dict])], ignore_index=True)
    st.session_state.bdd_utilisateurs = nouveau_df
    
    # 2. Écriture directe dans Google Sheets via gspread et le compte de service du secrets.toml
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # On charge les credentials directement depuis la section GCP de tes secrets
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], 
            scopes=scopes
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.worksheet("Identification")
        
        # Ajout de la ligne dans le Google Sheet
        ligne_a_ajouter = [int(nouveau_id), pseudo.strip(), email_hashe, "Joueur"]
        worksheet.append_row(ligne_a_ajouter)
        
        st.toast("✅ Compte enregistré dans Google Sheets avec succès !")
    except Exception as e:
        st.error(f"Erreur lors de l'écriture dans le Google Sheet : {e}")

    return {
        "ID": nouveau_id,
        "Nom": pseudo.strip(),
        "Mail_Hash": email_hashe,
        "Droit": "Joueur"
    }

def enregistrer_nouveau_compte(pseudo: str, email_hashe: str, bdd_df):
    """
    Génère les données du nouvel utilisateur et prépare l'enregistrement.
    """
    nouveau_id = len(bdd_df) + 1 if not bdd_df.empty else 1
    nouvel_user = {
        "ID": nouveau_id,
        "Nom": pseudo.strip(),
        "Mail_Hash": email_hashe,
        "Droit": "Joueur"
    }
    return nouvel_user

def afficher_module_connexion(bdd_df=None):
    # Si la base n'est pas passée en paramètre, tu peux la charger ici par sécurité
    if bdd_df is None:
       pass
    """Gère l'affichage de la connexion et de la création de compte."""
    st.markdown("### 🔑 Espace Membre")
    
    # 1. CAS : UTILISATEUR CONNECTÉ
    if st.session_state.utilisateur:
        user = st.session_state.utilisateur
        st.write(f"🟢 **{user['Nom']}** ({user['Droit']})")
        if st.button("Se déconnecter", width="stretch"):
            st.session_state.utilisateur = None
            if "email_hash_en_cours" in st.session_state:
                del st.session_state["email_hash_en_cours"]
            st.rerun()
            
    # 2. CAS : NON CONNECTÉ
    else:
        with st.popover("🔑 Connexion Google"):
            
            # Sub-case A : Email non trouvé -> Formulaire de création de compte
            if st.session_state.get("creation_compte_requise", False):
                st.subheader("🆕 Création de compte")
                st.info(
                    "🔒 **Respect de votre vie privée :**\n"
                    "Seul votre **pseudo** sera conservé en clair. Votre adresse e-mail est hachée "
                    "de manière irréversible (SHA-256) et aucun mot de passe n'est demandé ou stocké."
                )
                
                pseudo = st.text_input("Choisissez votre Pseudo / Nom de joueur", placeholder="Ex: Gandalf31")
                
                c_val, c_ann = st.columns(2)
                with c_val:
                    if st.button("Valider l'inscription", type="primary", width="stretch"):
                        if pseudo.strip():
                            email_hash = st.session_state.email_hash_en_cours
                            
                            # --- NOUVEAU CODE : ON APPELLE LA VRAIE FONCTION D'ÉCRITURE ---
                            # Remplace l'ID ci-dessous par ton ID de Google Sheet
                            SPREADSHEET_ID = "1wLIA_HaiIOUEJ818Z1zN0aEIiWXj_2RuD3BkvKrOalQ"
                            
                            nouvel_user = ajouter_utilisateur_bdd(pseudo, email_hash, SPREADSHEET_ID)
                            
                            st.session_state.utilisateur = nouvel_user
                            st.session_state.creation_compte_requise = False
                            st.success(f"Compte créé et enregistré dans le Sheet ! Bienvenue {pseudo}.")
                            st.rerun()
                        else:
                            st.warning("Veuillez saisir un pseudo valide.")
                
                with c_ann:
                    if st.button("Annuler", width="stretch"):
                        st.session_state.creation_compte_requise = False
                        st.rerun()

            # Sub-case B : Écran d'identification standard
            else:
                st.caption("Connexion sécurisée via Google.")
                email_saisi = st.text_input("Adresse Gmail", placeholder="exemple@gmail.com")
                
                if st.button("Se connecter avec Google", type="primary", width="stretch"):
                    if email_saisi:
                        # 1. Hachage immédiat de l'e-mail
                        email_hash = hashar_email(email_saisi)
                        st.session_state.email_hash_en_cours = email_hash
                        
                        # 2. Vérification dans la base
                        bdd = st.session_state.get("bdd_utilisateurs")
                        infos_user = verifier_utilisateur(email_hash, bdd)
                        
                        if infos_user:
                            st.session_state.utilisateur = infos_user
                            st.success(f"Bon retour, {infos_user['Nom']} !")
                            st.rerun()
                        else:
                            # Compte inexistant -> Bascule vers l'écran de création
                            st.session_state.creation_compte_requise = True
                            st.rerun()
                    else:
                        st.warning("Veuillez saisir votre e-mail.")