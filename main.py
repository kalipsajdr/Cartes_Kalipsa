import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import base64

import gspread
from google.oauth2.service_account import Credentials
from RecupLogo import charger_image_depuis_drive, charger_liens_importants

from connexionCompte import afficher_module_connexion

# Connexion automatique via st.secrets
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], 
    scopes=scopes
)

# Client Google Sheets
client = gspread.authorize(creds)
sheet = client.open_by_key("1wLIA_HaiIOUEJ818Z1zN0aEIiWXj_2RuD3BkvKrOalQ")

# --- 1. RÉCUPÉRATION DU LOGO DEPUIS GOOGLE SHEETS ---
SPREADSHEET_ID = "1wLIA_HaiIOUEJ818Z1zN0aEIiWXj_2RuD3BkvKrOalQ"

# --- 1. Chargement des liens importants ---
liens = charger_liens_importants(SPREADSHEET_ID)

# --- 2. Affichage propre du Logo et du Titre ---
flux_logo = charger_image_depuis_drive("Logo.png")

if flux_logo:
    # On crée deux colonnes : une étroite pour l'image, une plus large pour le texte
    col_img, col_txt = st.columns([1, 5])
    
    with col_img:
        st.image(flux_logo, width=70)
        
    with col_txt:
        # On ajuste l'alignement vertical avec un peu de CSS ou directement un titre Markdown stylisé
        st.markdown("<h2 style='margin-top: 5px;'>Navigation</h2>", unsafe_allow_html=True)
else:
    st.markdown("## Navigation")

# --- 2. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Cartographie Interactive JDR",
    page_icon=flux_logo, 
    layout="wide",
#    initial_sidebar_state="collapsed"  # <-- Masque la sidebar par défaut
)

# --- Affichage du logo dans la barre latérale si besoin ---
# if logo_url:
#     try:
#         st.sidebar.image(logo_url, width=100)
#     except Exception:
#         st.sidebar.image("🗺️") # Fallback si le lien Drive bloque

# --- 3. INITIALISATION DU SESSION STATE & DE LA BDD ---
@st.cache_data(ttl=60)
def charger_base_identification(sheet_id: str) -> pd.DataFrame:
    """Chargement de la table Identification au démarrage."""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Identification"
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        return df
    except Exception:
        return pd.DataFrame(columns=["ID", "Nom", "Mail", "Droit"])

if "bdd_utilisateurs" not in st.session_state:
    st.session_state.bdd_utilisateurs = charger_base_identification(SPREADSHEET_ID)

if "utilisateur" not in st.session_state:
    st.session_state.utilisateur = None  # Est maintenant bien initialisé !

if "carte_courante" not in st.session_state:
    st.session_state.carte_courante = "Carte du Monde"

# --- 4. BARRE DE NAVIGATION ET ESPACE MEMBRE ---
col_nav, col_auth = st.columns([3, 1.2])

with col_auth:
    # L'utilisateur et la session sont bien définis avant cet appel
    afficher_module_connexion()

st.divider()

# --- 5. RESTE DE L'INTERFACE (Carte, Panneau) ---
col_carte, col_panneau = st.columns([3, 1.2])

fluxCarte = charger_image_depuis_drive("Carte Monde.png")

with col_carte:
    st.subheader(f"📍 {st.session_state.carte_courante}")
    
    # --- Ligne de temps (Chronologie de la carte) ---
    st.markdown("### ⏳ Ligne de temps")
    
    # Création du curseur de l'an 10 à l'an 900
    annee_selectionnee = st.slider(
        "Année de référence pour la carte",
        min_value=10,
        max_value=900,
        value=10,  # Année par défaut au chargement
        step=1,    # Pas d'1 an (tu peux passer à 5 ou 10 si tu préfères des sauts plus grands)
        format="Année %d"
    )
    
    # Sauvegarde dans la session pour y accéder facilement depuis tes futurs modules de marqueurs/événements
    st.session_state["annee_carte"] = annee_selectionnee
    
    # Petit retour visuel (optionnel)
    # st.caption(affichage := f"Affichage de la carte et des événements pour l'**Année {annee_selectionnee}**")
    
    #Zoom de la carte
    # Initialisation de l'état du zoom s'il n'existe pas
    if "zoom_niveau" not in st.session_state:
        st.session_state["zoom_niveau"] = 100  # En pourcentage (ex: 100%)

    # # Slider pour contrôler le zoom de la carte
    # # --- Initialisation et affichage de ton Slider de Zoom ---
    # if "zoom_niveau" not in st.session_state:
    #     st.session_state["zoom_niveau"] = 100
    
    zoom_val = 100
    # zoom_val = st.slider(
    #     "Zoom de la carte",
    #     min_value=50,
    #     max_value=300,
    #     value=st.session_state["zoom_niveau"],
    #     step=10,
    #     format="%d%%",
    #     key="slider_zoom"
    # )
    
    st.session_state["zoom_niveau"] = zoom_val

    #Carte affichée

    if fluxCarte:
        if "zoom_niveau" not in st.session_state:
            st.session_state["zoom_niveau"] = 100
        
        zoom_pct = st.session_state["zoom_niveau"]
        largeur_base = 1000
        largeur_actuelle = int(largeur_base * (zoom_pct / 100))
        
        # Conversion de l'image en Base64
        fluxCarte.seek(0)
        encoded_img = base64.b64encode(fluxCarte.read()).decode("utf-8")
        img_data_url = f"data:image/png;base64,{encoded_img}"
        
        # Phrase d'indication au-dessus de la carte
        st.markdown("<p style='text-align: center; color: #666; font-style: italic;'>💡 Pour le zoom, utilisez la molette de votre souris (ou Ctrl + Molette). Maintenez le clic gauche pour vous déplacer.</p>", unsafe_allow_html=True)
    
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{
                margin: 0;
                background-color: #f8f9fa;
                overflow: hidden;
                font-family: sans-serif;
            }}
            /* Conteneur global qui englobe la carte et l'infobulle fixe */
            #map-wrapper-outer {{
                position: relative;
                width: 100%;
                height: 600px;
            }}
            #map-container {{
                width: 100%;
                height: 580px;
                overflow: auto;
                border: 2px solid #ccc;
                border-radius: 8px;
                background-color: #f8f9fa;
                position: relative;
                cursor: grab;
                user-select: none;
            }}
            #map-container:active {{
                cursor: grabbing;
            }}
            #map-image-wrapper {{
                width: {largeur_actuelle}px;
                height: auto;
                pointer-events: none;
                transform-origin: 0 0;
            }}
            img {{
                width: 100%;
                height: auto;
                display: block;
            }}
            /* Infobulle positionnée de manière fixe sur le composant (ne bouge plus avec la carte) */
            #zoom-badge {{
                position: absolute;
                bottom: 25px;
                right: 20px;
                background-color: rgba(0, 0, 0, 0.75);
                color: white;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
                pointer-events: none;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                z-index: 100;
            }}
        </style>
        </head>
        <body>
            <div id="map-wrapper-outer">
                <div id="map-container">
                    <div id="map-image-wrapper">
                        <img src="{img_data_url}" />
                    </div>
                </div>
                <!-- L'infobulle est ici, indépendante du scroll de la carte -->
                <div id="zoom-badge">{zoom_pct}%</div>
            </div>
    
            <script>
            const container = document.getElementById('map-container');
            const wrapper = document.getElementById('map-image-wrapper');
            const badge = document.getElementById('zoom-badge');
            
            let isDown = false;
            let startX, startY, scrollLeft, scrollTop;
    
            // Glisser-déposer (Pan)
            container.addEventListener('mousedown', (e) => {{
                isDown = true;
                startX = e.pageX - container.offsetLeft;
                startY = e.pageY - container.offsetTop;
                scrollLeft = container.scrollLeft;
                scrollTop = container.scrollTop;
            }});
    
            container.addEventListener('mouseleave', () => {{ isDown = false; }});
            container.addEventListener('mouseup', () => {{ isDown = false; }});
    
            container.addEventListener('mousemove', (e) => {{
                if (!isDown) return;
                e.preventDefault();
                const x = e.pageX - container.offsetLeft;
                const y = e.pageY - container.offsetTop;
                const walkX = x - startX;
                const walkY = y - startY;
                container.scrollLeft = scrollLeft - walkX;
                container.scrollTop = scrollTop - walkY;
            }});
    
            // Zoom à la molette avec mise à jour de l'infobulle fixe
            container.addEventListener('wheel', (e) => {{
                e.preventDefault();
                let currentWidth = wrapper.offsetWidth;
                
                let zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
                let newWidth = Math.round(currentWidth * zoomFactor);
                
                if (newWidth < 500) newWidth = 500;
                if (newWidth > 3000) newWidth = 3000;
    
                wrapper.style.width = newWidth + 'px';
    
                let currentPct = Math.round((newWidth / 1000) * 100);
                badge.innerText = currentPct + '%';
            }}, {{ passive: false }});
            </script>
        </body>
        </html>
        """
        
        components.html(html_content, height=600)

with col_panneau:
    st.subheader("📋 Informations & Actions")
    
    with st.expander("📍 Marqueur Sélectionné", expanded=True):
        st.write("**Nom du lieu :** Donjon d'Aethelgard")
        st.write("**Description :** Forteresse nichée dans les montagnes.")
        st.image("https://picsum.photos/300/200", width="stretch")

    st.divider()

    # Formulaire disponible si connecté
    if st.session_state.utilisateur:
        st.markdown(f"### ➕ Proposer un Marqueur ({st.session_state.utilisateur['Nom']})")
        with st.expander("Créer un marqueur temporaire"):
            st.info(f"Droit actuel : **{st.session_state.utilisateur['Droit']}**")
            nom_m = st.text_input("Nom du lieu")
            desc_m = st.text_area("Description")
            if st.button("Envoyer pour validation", type="primary", width="stretch"):
                st.success("Marqueur soumis !")
    else:
        st.warning("🔒 Connectez-vous avec votre compte Google pour proposer des marqueurs.")