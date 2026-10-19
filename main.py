import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components

from RecupLogo import charger_image_depuis_drive, charger_liens_importants
from connexionCompte import afficher_module_connexion
from carte import Carte
from validationMarqueur import enregistrer_nouveau_marqueur
from composantCarte import afficher_carte_interactive
from gestionCarte import creer_nouvelle_carte

# Configuration de la page
st.set_page_config(
    page_title="Cartographie Interactive Kalipsa",
    layout="wide",
)

# --- Interception des coordonnées stockées par la carte HTML via localStorage ---
if "coords_selectionnees" not in st.session_state:
    st.session_state["coords_selectionnees"] = ""

# Initialisation sécurisée de l'état de session
if "utilisateur" not in st.session_state:
    st.session_state.utilisateur = None
    
if "coords_selectionnees" not in st.session_state:
    st.session_state["coords_selectionnees"] = ""

# Interception des coordonnées transmises par l'URL
if "coords" in st.query_params:
    val_coords = st.query_params["coords"]
    if isinstance(val_coords, list) and len(val_coords) > 0:
        st.session_state["coords_selectionnees"] = val_coords[0]
    elif isinstance(val_coords, str):
        st.session_state["coords_selectionnees"] = val_coords
    del st.query_params["coords"]

# Connexion Google Sheets
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
client = gspread.authorize(creds)
SPREADSHEET_ID = "1wLIA_HaiIOUEJ818Z1zN0aEIiWXj_2RuD3BkvKrOalQ"
sheet = client.open_by_key(SPREADSHEET_ID)

# Chargement du Logo et Titre
flux_logo = charger_image_depuis_drive("Logo.png")
if flux_logo:
    col_img, col_txt = st.columns([1, 5])
    with col_img:
        st.image(flux_logo, width=70)
    with col_txt:
        st.markdown("<h2 style='margin-top: 5px;'>Navigation</h2>", unsafe_allow_html=True)
else:
    st.markdown("## Navigation")

# --- Chargement de la base utilisateurs pour le module de connexion ---
@st.cache_data(ttl=60)
def charger_base_identification(_sheet) -> pd.DataFrame:
    """Charge la table Identification via l'objet gspread existant."""
    try:
        ws = _sheet.worksheet("Identification")
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        print(f"Erreur chargement base identification : {e}")
        return pd.DataFrame(columns=["ID", "Nom", "Mail", "Droit"])

if "bdd_utilisateurs" not in st.session_state:
    st.session_state.bdd_utilisateurs = charger_base_identification(sheet)

# Barre de navigation et espace membre
col_nav, col_auth = st.columns([3, 1.2])
with col_auth:
    afficher_module_connexion(st.session_state.bdd_utilisateurs)

st.divider()

# Structure principale (Carte / Panneau)
col_carte, col_panneau = st.columns([3, 1.2])
fluxCarte = charger_image_depuis_drive("Carte Monde.png")

with col_carte:
    try:
        ws_cartes = sheet.worksheet("Carte").get_all_records()
        ws_marques = sheet.worksheet("Marque").get_all_records()
        ws_dates = sheet.worksheet("DateMarque").get_all_records()
        
        cartes = [Carte.depuis_ligne(row) for row in ws_cartes]
        
        carte_courante = next((c for c in cartes if c.nom == st.session_state.get("carte_courante", "Carte du Monde")), None)
        if not carte_courante:
            carte_courante = next((c for c in cartes if c.id == "1"), None)
        
        st.subheader(f"📍 {st.session_state.get('carte_courante', 'Carte du Monde')}")
        
        # Ligne de temps
        st.markdown("### ⏳ Ligne de temps")
        annee_selectionnee = st.slider(
            "Année de référence pour la carte",
            min_value=10, max_value=900, value=11, step=1, format="Année %d"
        )
        st.session_state["annee_carte"] = annee_selectionnee
        
        # Chargement sécurisé du flux de la carte
        fluxCarte = charger_image_depuis_drive("Carte Monde.png")
        if fluxCarte:
            afficher_carte_interactive(fluxCarte)
        else:
            st.error("Impossible de charger l'image 'Carte Monde.png' depuis Google Drive.")
            
    except Exception as e:
        st.error(f"Erreur lors du chargement de la carte : {e}")

with col_panneau:
    st.subheader("📋 Informations & Actions")
    
    if st.session_state.get("utilisateur"):
        st.markdown(f"### ➕ Proposer un Marqueur ({st.session_state.utilisateur['Nom']})")
        
        with st.expander("Créer un marqueur temporaire", expanded=True):
            st.info(f"Droit actuel : **{st.session_state.utilisateur['Droit']}**")
            
            coords_actuelles = st.session_state.get("coords_selectionnees", "")
            if coords_actuelles:
                st.success(f"📍 Emplacement enregistré : **{coords_actuelles}**")
            else:
                st.warning("👆 Cliquez sur la carte pour définir l'emplacement du marqueur.")
        
            with st.form("form_ajout_marqueur"):
                nom_lieu = st.text_input("Nom du lieu")
                
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    debut_marque = st.number_input("Date de début", min_value=10, max_value=900, value=int(st.session_state.get("annee_carte", 10)), step=1)
                with col_d2:
                    fin_marque = st.number_input("Date de fin", min_value=10, max_value=900, value=900, step=1)
                    
                # Le fichier image récupéré depuis l'interface que tu viens de montrer :
                image_marqueur = st.file_uploader("Image du marqueur (facultatif, 5 Mo max)", type=["png", "jpg", "jpeg"])
                
                description = st.text_area("Description")
            
                submit_button = st.form_submit_button(label="Envoyer pour validation", type="primary")
                
                if submit_button:
                    coordonnees = st.session_state.get("coords_selectionnees", "").strip()
                    
                    if nom_lieu and coordonnees:
                        # 1. Si une image de carte est fournie, on lance l'initialisation de la carte en base + thread d'upload
                        id_carte_associee = ""
                        if image_marqueur is not None:
                            # On utilise le nom du lieu saisi comme nom de la carte, et on lance le thread d'upload
                            succes_carte, res_carte = creer_nouvelle_carte(
                                sheet=sheet,
                                nom_carte=nom_lieu,
                                image_file=image_marqueur
                            )
                            if succes_carte:
                                id_carte_associee = str(res_carte) # Récupération de l'ID généré pour le lier au marqueur
                            else:
                                st.error(f"Erreur lors de la création de la carte : {res_carte}")
                                st.stop()
                        
                        # 2. Ensuite, on enregistre le marqueur en lui passant l'ID de la carte associée (s'il y en a une)
                        succes, resultat = enregistrer_nouveau_marqueur(
                            sheet=sheet,
                            carte_courante=carte_courante,
                            nom_lieu=nom_lieu,
                            coordonnees=coordonnees,
                            debut_marque=debut_marque,
                            fin_marque=fin_marque,
                            description=description,
                            lien_id_carte=id_carte_associee  # ID récupéré automatiquement de la nouvelle carte créée
                        )
                        
                        if succes:
                            st.session_state["coords_selectionnees"] = ""
                            if "coords" in st.query_params:
                                del st.query_params["coords"]
                            st.success(f"Le marqueur et sa carte associée '{nom_lieu}' ont été pris en compte avec succès ! L'upload se fait en arrière-plan.")
                            st.rerun()
                        else:
                            st.error(f"Erreur lors de l'enregistrement du marqueur : {resultat}")
                    else:
                        st.warning("Veuillez renseigner le nom du lieu et cliquer sur la carte pour définir l'emplacement.")
    else:
        st.warning("🔒 Connectez-vous avec votre compte pour proposer des marqueurs.")