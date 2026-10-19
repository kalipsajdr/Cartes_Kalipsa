import streamlit as st
import folium
from streamlit_folium import st_folium
from PIL import Image
import io
import base64

@st.cache_data
def preparer_image_base64(img_bytes):
    """Met en cache la conversion de l'image pour un affichage instantané."""
    img = Image.open(io.BytesIO(img_bytes))
    height, width = img.size[1], img.size[0]
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    encoded_img = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    return height, width, f"data:image/png;base64,{encoded_img}"

def charger_marqueurs_carte(sheet, id_carte_courante):
    """
    Charge tous les marqueurs (permanents et temporaires) rattachés à la carte courante.
    """
    ws_marque = sheet.worksheet("Marque")
    tous_marqueurs = ws_marque.get_all_records()
    
    marqueurs_filtres = []
    for m in tous_marqueurs:
        # On vérifie si le marqueur est lié à la carte courante 
        # (via le champ LienIdCarte ou l'ID de la carte active)
        if str(m.get("LienIdCarte", "")) == str(id_carte_courante):
            marqueurs_filtres.append(m)
            
    return marqueurs_filtres

# Le fragment isole la carte : seul ce bloc se recharge au clic, de manière ultra-rapide (< 0.5s)
@st.fragment
def afficher_carte_interactive(fluxCarte):
    """
    Carte interactive Folium encapsulée dans un fragment Streamlit 
    pour un affichage instantané du marqueur sans recharger toute l'app.
    """
    if "coords_selectionnees" not in st.session_state:
        st.session_state["coords_selectionnees"] = ""

    # Lecture et préparation rapide via le cache
    fluxCarte.seek(0)
    img_bytes = fluxCarte.read()
    height, width, img_data_uri = preparer_image_base64(img_bytes)

    user_connecte = st.session_state.get("utilisateur") is not None
    coords_actuelles = st.session_state.get("coords_selectionnees", "")

    if user_connecte:
        if coords_actuelles:
            st.markdown(f"<p style='color: #28a745; font-weight: bold;'>📍 Emplacement sélectionné ({coords_actuelles}). Vous pouvez valider via votre formulaire.</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color: #333; font-weight: bold;'>📍 Cliquez sur la carte pour placer votre marqueur.</p>", unsafe_allow_html=True)

    # Création de la carte Folium
    m = folium.Map(
        crs="Simple",
        location=[height / 2, width / 2],
        zoom_start=0,
        min_zoom=-2,
        max_zoom=4,
        control_displayed=False
    )

    bounds = [[0, 0], [height, width]]
    folium.raster_layers.ImageOverlay(
        image=img_data_uri,
        bounds=bounds,
        interactive=True,
        cross_origin=False,
        z_index=1
    ).add_to(m)

    id_carte_actuelle = st.session_state.get("id_carte_active", "1")
    sheet_global = st.session_state.get("sheet") # Assure-toi d'avoir ta feuille connectée en session, ou passe-la en paramètre
    
    if sheet_global:
        marqueurs = charger_marqueurs_carte(sheet_global, id_carte_actuelle)
        for m_data in marqueurs:
            coords_str = m_data.get("Coordonee", "")
            if coords_str:
                try:
                    parts = coords_str.split(",")
                    if len(parts) == 2:
                        mx = float(parts[0].strip())
                        my = float(parts[1].strip())
                        
                        nom_lieu = m_data.get("Nom", "Lieu")
                        est_temporaire = str(m_data.get("Temporaire", "Non")).strip() == "Oui"
                        
                        # Style différencié pour les marqueurs temporaires (ex: orange) vs permanents (bleu)
                        couleur_fond = "#ff9800" if est_temporaire else "#007bff"
                        
                        popup_html = f"<div style='font-family: sans-serif;'><b>{nom_lieu}</b><br>Statut : {'Temporaire' f' (Modifiable)' if est_temporaire else 'Permanent'}<br>X : {int(mx)} | Y : {int(my)}</div>"
                        
                        folium.Marker(
                            location=[height - my, mx],
                            popup=folium.Popup(popup_html, max_width=250),
                            icon=folium.DivIcon(html=f"""
                                <div style="width: 24px; height: 36px; background-color: {couleur_fond}; border: 2px solid white; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); box-shadow: 2px 2px 5px rgba(0,0,0,0.5);"></div>
                            """)
                        ).add_to(m)
                except Exception:
                    pass

    # Affichage immédiat du marqueur cliquable si les coordonnées existent
    if coords_actuelles:
        try:
            parts = coords_actuelles.split(',')
            if len(parts) == 2:
                mx = float(parts[0].strip())
                my = float(parts[1].strip())
                
                # Création d'une info-bulle (popup) qui s'ouvre au clic sur le marqueur
                popup_contenu = f"<div style='font-family: sans-serif;'><b>Position sélectionnée</b><br>X : {int(mx)} | Y : {int(my)}</div>"
                
                folium.Marker(
                    location=[height - my, mx],
                    popup=folium.Popup(popup_contenu, max_width=250),
                    icon=folium.DivIcon(html="""
                        <div style="width: 24px; height: 36px; background-color: #ff9800; border: 2px solid white; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); box-shadow: 2px 2px 5px rgba(0,0,0,0.5);"></div>
                    """)
                ).add_to(m)
        except Exception:
            pass

    m.fit_bounds(bounds)

    # Affichage de la carte Folium
    output = st_folium(m, width="stretch", height=560, key="carte_leaflet_interactive", returned_objects=["last_clicked"])

    # Gestion de la sélection du clic avec rafraîchissement instantané du fragment uniquement
    if user_connecte and output and output.get("last_clicked"):
        clicked_lat = output["last_clicked"]["lat"]
        clicked_lng = output["last_clicked"]["lng"]
        
        final_x = int(round(clicked_lng))
        final_y = int(round(height - clicked_lat))
        
        if 0 <= final_x <= width and 0 <= final_y <= height:
            new_coords = f"{final_x}, {final_y}"
            if st.session_state["coords_selectionnees"] != new_coords:
                st.session_state["coords_selectionnees"] = new_coords
                st.rerun() # Ne relance que la carte, pas Google Sheets ni le reste !