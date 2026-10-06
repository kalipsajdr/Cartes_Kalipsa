from google_auth_oauthlib.flow import Flow

st.set_page_config(layout="wide")

# --- CONFIGURATION ---
REDIRECT_URI = "http://localhost:8501"
URL_BDD = "https://docs.google.com/spreadsheets/d/15CnBOGKNwe_ir_WkzSjO-4dnsDmgoCBUkNx6913J21o/edit"

client_config = {
    "web": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

# --- INITIALISATION DU VIGILE ---
# On utilise le décorateur @st.cache_resource pour que le flow 
# soit créé UNE SEULE FOIS et ne change JAMAIS.
@st.cache_resource
def get_flow():
    return Flow.from_client_config(
        client_config,
        scopes=["https://www.googleapis.com/auth/userinfo.email", "openid"],
        redirect_uri=REDIRECT_URI
    )

@st.cache_data(ttl=3600)
def charger_df_classe(_conn, url, nom_classe):
    return _conn.read(spreadsheet=url, worksheet=nom_classe, ttl=3600)

def bouton_connexion(url):
    # CSS pour recréer le style Streamlit avec effet de survol
    st.markdown("""
        <style>
        /* Style de base du bouton (lien) */
        .stGoogleButton {
            display: flex !important; /* Changé de inline-flex à flex */
            align-items: center !important;
            justify-content: center !important;
            width: 50% !important;
            margin-left: auto !important; /* Ajout de !important pour être sûr */
            margin-right: auto !important;
            padding: 10px 20px !important;
            background-color: #f0f2f6 !important; /* Couleur de fond par défaut */
            color: #31333F !important; /* Couleur du texte */
            border-radius: 8px !important;
            border: 1px solid rgba(49, 51, 63, 0.2) !important;
            font-weight: 500 !important;
            text-decoration: none !important;
            transition: background-color 0.1s ease-in-out, border-color 0.1s ease-in-out !important;
            cursor: pointer !important;
            margin-bottom: 10px !important;
        }

        /* Effet de survol (HOVER) */
        .stGoogleButton:hover {
            background-color: #e0e4eb !important; /* Couleur plus sombre au survol */
            border-color: rgba(49, 51, 63, 0.4) !important;
        }

        /* Effet de clic (ACTIVE) */
        .stGoogleButton:active {
            background-color: #d0d4db !important;
            border-color: rgba(49, 51, 63, 0.6) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Affichage du bouton avec la classe personnalisée
    st.markdown(f'<a href="{url}" target="_self" class="stGoogleButton">Se connecter avec Google</a>', unsafe_allow_html=True)