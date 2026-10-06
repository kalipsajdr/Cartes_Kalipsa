import streamlit as st
import HashMail
import pandas as pd
from google_auth_oauthlib.flow import Flow
from marqueurMap import Marqueur
from imageJDR import ImageJDR

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

#Début du main
# Instanciation simple et propre
m1 = Marqueur(250, 180, description="Entrée du Donjon", lien="map_donjon_1")
carte = ImageJDR("https://drive.google.com/file/d/TON_FILE_ID/view", marqueurs=[m1])

if "email_utilisateur" not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>🧙‍♂️ Maverick JDR</h1>", unsafe_allow_html=True)
        
    if 'bdd' not in st.session_state:
        st.session_state.bdd= AccesBdd()
    bdd = st.session_state.bdd
    
    flow = get_flow()
    
    # On génère l'URL de connexion
    # code_challenge_method=None est important ici pour la simplicité
    auth_url, _ = flow.authorization_url(prompt='consent')
    
    empty_l, center_col, empty_r = st.columns([1, 2, 1])

    with center_col:
        st.info("Bienvenue aventurier. Connecte-toi pour continuer.")
        
    bouton_connexion(auth_url)

    # Vérification du retour de Google
    if "code" in st.query_params:
        try:
            code_google = st.query_params["code"]
            # On échange le code contre les infos de l'utilisateur
            flow.fetch_token(code=code_google)
            session = flow.authorized_session()
            user_info = session.get("https://www.googleapis.com/oauth2/v1/userinfo").json()
            
            st.session_state.email_utilisateur = HashMail.hasher_email(user_info["email"])
            st.query_params.clear() # On nettoie l'URL
            st.rerun()
        except Exception as e:
            st.error(f"Détail de l'erreur : {e}")
            st.warning("🔄 Rafraîchis la page (F5) et réessaie une seule fois.")
else:
    # --- INITIALISATION DES ACCÈS (Une seule fois) ---
    if 'bdd' not in st.session_state:
        st.session_state.bdd = AccesBdd()
    
    if 'bdd_manager_perso' not in st.session_state:
        st.session_state.bdd_manager_perso = bddPerso.BddManagerPerso(URL_BDD)

    bdd = st.session_state.bdd
    bddManager = st.session_state.bdd_manager_perso
    
    # --- TA LOGIQUE DE JEU ---
    if "email_utilisateur" in st.session_state:
        hashEmail = st.session_state.email_utilisateur
        
        # Utilisation de notre nouveau module
        user_data, est_nouveau = bdd.verifier_ou_creer_utilisateur(hashEmail)
        
        if est_nouveau:
            st.subheader("🧙‍♂️ Bienvenue, nouvel aventurier !")
            st.write("Ton email n'est pas encore enregistré dans Maverick. Au moment de l'enregistrement, ton email sera crypté pour des raison de confidentialité.")
            
            with st.form("inscription"):
                nouveau_pseudo = st.text_input("Choisis ton nom de héros (Pseudo) :")
                valider = st.form_submit_button("Entrer dans l'aventure")
                
                if valider and nouveau_pseudo:
                    with st.spinner("Création de ton compte..."):
                        bdd.enregistrer_nouveau_joueur(hashEmail, nouveau_pseudo)
                        st.success("Compte créé ! Bienvenue.")
                        st.rerun()
                elif valider:
                    st.warning("Il nous faut un pseudo pour l'histoire !")
                    
        else:
            # L'utilisateur existe déjà
            if int(user_data['Actif']) == 1:
                st.title(f"Heureux de te revoir, {user_data['Pseudo']} !")
                st.write(f"Rang : {user_data['NiveauDroit']}")
                
                if st.sidebar.button("Se déconnecter"):
                    st.session_state.clear()
                    st.rerun()
                
                # Nouvel Utilisateur ?
                user_data, est_nouveau = bdd.verifier_ou_creer_utilisateur(st.session_state.email_utilisateur)
                if 'urls_references' not in st.session_state:
                    st.session_state.urls_references = bdd.recup_urls_sources()
                
                if 'dict_global_ech_niv' not in st.session_state:
                    df_ech = bdd.lire_onglet_local("EchelleNiveau")
                    st.session_state.dict_global_ech_niv = df_ech.to_dict('records')
                    
                dicoEchNiv = st.session_state.dict_global_ech_niv
                moteur_niveau = EchelleNiveau(dicoEchNiv)
                
                if 'dict_global_couleur_magie' not in st.session_state:
                    df_coul_magies = bdd.lire_onglet_local("CouleursMagies")
                    st.session_state.dict_global_couleur_magie = df_coul_magies.to_dict('records')
                    
                dicoCoulMagies = st.session_state.dict_global_couleur_magie
                couleur_magie = CouleurMagies(dicoCoulMagies)
                
                if 'dict_global_materiaux_arme' not in st.session_state:
                    df_mat_arme = bdd.lire_onglet_local("MatériauArmes")
                    st.session_state.dict_global_materiaux_arme = df_mat_arme.to_dict('records')
                    
                dicoMatArme = st.session_state.dict_global_materiaux_arme
                
                urls = st.session_state.urls_references
                # On accède directement à la valeur via la clé entre crochets
                url_classes = urls.get('Classes')
                url_races = urls.get('Races')
                url_magies = urls.get('Magies')
                url_invocations = urls.get('Invocations')
                url_ressourcesEtCraft = urls.get('Ressources et craft')
                
                # Petite vérification de sécurité
                if not url_classes:
                    st.error("L'URL 'Classes' n'a pas été trouvée dans le dictionnaire des sources.")
                    
                if not url_magies:
                    st.error("L'URL 'Magie' n'a pas été trouvée dans le dictionnaire des sources.")

                if not est_nouveau and int(user_data['Actif']) == 1:
                    id_joueur = user_data['IdUtilisateur']
                    
                    # --- LOGIQUE D'AFFICHAGE ---
                    df_persos = bddManager.recupLstPersosUti(id_joueur)
                    
                    if 'toutes_les_stats' not in st.session_state:
                        st.session_state.toutes_les_stats = bddManager.charger_onglet_complet("Caracteristiques")
                    
                    # --- GESTION DE L'AFFICHAGE ---
                    if st.session_state.get('page_creation', False):
                        if st.button("⬅️ Retour à la liste"):
                            st.session_state.page_creation = False
                            st.rerun()
                        
                        # Appel du formulaire
                        CreerPerso.afficher_formulaire_creation(id_joueur)
                    
                    else:
                        st.title(f"Personnages de {user_data['Pseudo']}")
                        
                        if st.button("➕ Créer un nouveau personnage", use_container_width=True):
                            st.session_state.page_creation = True
                            st.rerun()
                        
                        st.divider()
                        
                        if df_persos.empty:
                            st.info("Tu n'as pas encore de personnage.")
                        else:
                            # --- CHARGEMENT des informations globales (Une seule fois) ---
                            if 'dict_global_carac' not in st.session_state:
                                st.session_state.dict_global_carac = bddManager.charger_onglet_complet("Caracteristiques")
                            
                            if 'dict_global_comp' not in st.session_state:
                                st.session_state.dict_global_comp = bddManager.charger_onglet_groupe("Competence")
                                
                            if 'dict_global_comp_spe' not in st.session_state:
                                st.session_state.dict_global_comp_spe = bddManager.charger_onglet_complet("CompSpe")
                            
                            if 'dict_global_sorts' not in st.session_state:
                                donnees_recuperees = bddManager.charger_onglet_sort("LstSorts")
                                if donnees_recuperees:
                                    st.session_state.dict_global_sorts = donnees_recuperees
                                else:
                                    st.session_state.dict_global_sorts = []
                            
                            if 'dict_global_maitrise' not in st.session_state:
                                st.session_state.dict_global_maitrise = bddManager.charger_onglet_complet("Maitrise")
                                
                            if 'dict_global_equipement' not in st.session_state:
                                st.session_state.dict_global_equipement = bddManager.charger_onglet_complet("Equipement")
                            
                            if 'ref_armes' not in st.session_state:
                                df_armes = bdd.lire_onglet_local("Armes")
                                # Supprime les lignes ayant le même nom avant de convertir en dictionnaire
                                df_armes = df_armes.drop_duplicates(subset=['Nom'])
                                dict_brut_armes = df_armes.set_index('Nom').to_dict(orient='index')
                                st.session_state.ref_armes = {nom: Arme(data) for nom, data in dict_brut_armes.items()}
                             
                            if 'ref_armures' not in st.session_state:
                                df_armures = bdd.lire_onglet_local("Armures")
                                # On crée le dictionnaire brut
                                dict_temp = df_armures.set_index('Nom').to_dict(orient='index')
                                # On le stocke pour éviter l'erreur AttributeError
                                st.session_state.dict_brut_armures = dict_temp
                                st.session_state.ref_armures = {nom: Armure(data) for nom, data in dict_temp.items()}
                                
                            if 'ref_armures_elem' not in st.session_state:
                                # 1. Lecture de l'onglet élémentaire
                                df_armures_elem = bdd.lire_onglet_local("ArmuresElem")
                                
                                # 2. Création du dictionnaire brut indexé par le 'Nom' (colonne C de ton image)
                                dict_temp_elem = df_armures_elem.set_index('Nom').to_dict(orient='index')
                                st.session_state.dict_brut_armures_elem = dict_temp_elem
                                
                                # 3. Dictionnaire temporaire pour stocker les objets Armure élémentaires convertis
                                armures_elem_objets = {}
                                
                                for nom_item, data in dict_temp_elem.items():
                                    # On extrait la valeur d'armure globale fournie par la table (AP ou AM)
                                    val_ap = data.get('AP', 0)
                                    val_am = data.get('AM', 0)
                                    
                                    # Si la colonne donne une valeur globale (ex: 2), on la répartit sur chaque zone,
                                    # ou on la laisse à 1 si c'est juste un indicateur (adapte selon tes règles).
                                    v_zone_ap = 1 if val_ap else 0
                                    v_zone_am = 1 if val_am else 0
                                    
                                    # On reconstruit un dictionnaire au format EXACT attendu par ta classe Armure
                                    data_formatee = {
                                        "nom": str(nom_item),
                                        "descriptif": f"Armure élémentaire de type {data.get('Magie', 'Inconnu')}",
                                        "type": str(data.get('Type', 'Vêtement')),
                                        "stats": f"+{val_ap}AP" if val_ap else f"+{val_am}AM",
                                        "solidite_max": 1,
                                        "resistance": str(data.get('Effet', '')),
                                        "faiblesse": "",
                                        # Attribution des points convertis aux membres en minuscules
                                        "t": v_zone_ap if val_ap else v_zone_am,
                                        "c": v_zone_ap if val_ap else v_zone_am,
                                        "bg": v_zone_ap if val_ap else v_zone_am,
                                        "bd": v_zone_ap if val_ap else v_zone_am,
                                        "jg": v_zone_ap if val_ap else v_zone_am,
                                        "jd": v_zone_ap if val_ap else v_zone_am
                                    }
                                    
                                    # Instanciation de l'objet Armure propre
                                    armures_elem_objets[nom_item] = Armure(data_formatee)
                                
                                # 4. Sauvegarde dans son state dédié (au cas où tu en as besoin ailleurs)
                                st.session_state.ref_armures_elem = armures_elem_objets
                                
                                # 5. L'ASTUCE : On fusionne directement dans le catalogue général des armures !
                                # Comme ça, ton fichier "Equipement" trouvera la robe élémentaire sans aucun changement de code !
                                if 'ref_armures' in st.session_state:
                                    st.session_state.ref_armures.update(armures_elem_objets)
                            
                            if 'ref_boucliers' not in st.session_state:
                                df_boucliers = bdd.lire_onglet_local("Boucliers")
                                # ÉTAPE 1 : Créer la colonne d'index en fusionnant les colonnes C et E
                                # On prend la valeur de 'Type de bouclier' si elle existe, sinon celle de 'Materiaux'
                                df_boucliers['Nom_Technique'] = df_boucliers['Type de bouclier'].fillna(df_boucliers['Materiaux'])
                                # ÉTAPE 2 : Nettoyage des lignes vides (si il y en a dans l'Excel)
                                df_boucliers = df_boucliers.dropna(subset=['Nom_Technique'])
                                # ÉTAPE 3 : Vérification des doublons (pour éviter l'erreur précédente)
                                df_boucliers = df_boucliers.drop_duplicates(subset=['Nom_Technique'])
                                # ÉTAPE 4 : Création du dictionnaire
                                dict_brut_boucliers = df_boucliers.set_index('Nom_Technique').to_dict(orient='index')
                                # ÉTAPE 5 : Création des objets
                                st.session_state.ref_boucliers = {nom: Bouclier(data) for nom, data in dict_brut_boucliers.items()}


                            # Récupération du dictionnaire pour la boucle
                            dicoCarac = st.session_state.dict_global_carac
                            dicoComp = st.session_state.dict_global_comp
                            dicoCompSpe = st.session_state.dict_global_comp_spe
                            manager_spe = CompSpeManager(dicoCompSpe)
                            dicoSorts = st.session_state.dict_global_sorts
                            dicoMaitrise = st.session_state.dict_global_maitrise
                            dicoEquipement = st.session_state.dict_global_equipement
                            dicoArme = st.session_state.ref_armes
                            dicoArmure = st.session_state.ref_armures                            
                            dicoBouclier = st.session_state.ref_boucliers
                            
                            # --- DÉBUT DE LA BOUCLE SUR LES PERSONNAGES ---
                            for _, p in df_persos.iterrows():
                                # Variables d'identification
                                id_p = p['IdPersonnage']
                                
                                maitrise_data = dicoMaitrise.get(id_p, {})
                                equip_data = dicoEquipement.get(id_p, {})
                                
                                total_xp = p['TotalXP']
                                niveau_global = moteur_niveau.convertir_xp_en_niveau(total_xp)
                                # On ajoute (ou met à jour) la clé 'NivGlobal' dans l'objet p
                                p['NivGlobal'] = niveau_global
                                
                                # On extrait les stats du personnage précis
                                caracPerso = dicoCarac.get(id_p, {}) 
                                
                                # On vérifie si on a bien trouvé des stats, sinon on met un dico vide
                                if not caracPerso:
                                    st.warning(f"Aucune caractéristique trouvée pour {p['Nom']}")

                                # Récupération sécurisée des compétences du perso spécifique
                                data_comp = dicoComp.get(id_p, [])
                                if not isinstance(data_comp, list):
                                    data_comp = []
                                
                                # Formatage des textes d'affichage
                                m_acq = p.get('MagieAcq', "")
                                magie_Aff = p['MagieInn'] if (pd.isna(m_acq) or m_acq == "") else f"{p['MagieInn']} / {m_acq}"
                                
                                c1_nom = p['Classe1']
                                c2_brute = p.get('Classe2', "")
                                c2_nom = "" if pd.isna(c2_brute) else str(c2_brute)
                                classe_Aff = c1_nom if c2_nom == "" else f"{c1_nom} / {c2_nom}"
                        
                                choix_spe = manager_spe.get_tous_choix_spe(p['IdPersonnage'])
                                
                                listeSorts = LstSorts(dicoSorts, bdd, url_magies, couleur_magie)
                                
                                df_coul = pd.DataFrame(st.session_state.dict_global_couleur_magie)
                                dieu_inn_info = df_coul[df_coul['NomMagie'] == p['MagieInn']]['Dieux'].values
                                dieu_inn_final = dieu_inn_info[0] if len(dieu_inn_info) > 0 else "Aucun"
                                
                                # Affichage de l'Expander
                                with st.expander(f"🎭 {p['Nom']} ({p.get('Surnom', '')}) - {p['Race']} - Magie : {magie_Aff} - Classe : {classe_Aff}"):
                                    # Récupération des données de classe
                                    df_c1 = charger_df_classe(bddManager.conn, url_classes, c1_nom)
                                    #st.dataframe(df_c1)
                                    obj_classe1 = ClassePerso(c1_nom, df_c1)
                                    
                                    obj_classe2 = None
                                    if c2_nom != "":
                                        df_c2 = charger_df_classe(bddManager.conn, url_classes, c2_nom)
                                        obj_classe2 = ClassePerso(c2_nom, df_c2)
                                    
                                    sorts_affichage = listeSorts.preparer_affichage(
                                        p['IdPersonnage'], 
                                        p['MagieInn'], 
                                        p['MagieAcq']
                                    )
                                    
                                    # Appel de la fiche avec les données du personnage actuel (data_comp)
                                    fiche_detaillee.afficher_fiche_complete(p, caracPerso, data_comp, obj_classe1, obj_classe2,choix_spe,sorts_affichage,dieu_inn_final,maitrise_data,equip_data,dicoArme,dicoArmure,dicoBouclier,dicoMatArme)
                                    
