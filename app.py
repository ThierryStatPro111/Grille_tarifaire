# ============================================================
# APPLICATION STREAMLIT — CALCULATEUR DE PRIME AUTOMOBILE
# Projet Master 2 Actuariat — Tarification Automobile
# Auteur : Thierry NIYOKWIZIGIRWA
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# ============================================================
# CONFIGURATION DE LA PAGE
# ============================================================
st.set_page_config(
    page_title="Calculateur de Prime Automobile",
    page_icon="🚗",
    layout="wide"
)

# ============================================================
# PARAMETRES DU MODELE (issus de notre GLM Poisson x Log-Normal)
# ============================================================

# Prime pure de référence (calculée dans R)
PRIME_PURE_REF = 80.59

# Chargements
CHARGEMENT_FRAIS    = 0.25
CHARGEMENT_SECURITE = 0.10
CHARGEMENT_REASSURANCE = 0.05
CHARGEMENT_TOTAL    = CHARGEMENT_FRAIS + CHARGEMENT_SECURITE + CHARGEMENT_REASSURANCE

# Relativités Area (issues du GLM Poisson x LogNormal)
RELATIVITES_AREA = {
    "A (Très rural)"   : 1.000,
    "B (Rural)"        : 1.122,
    "C (Semi-urbain)"  : 1.190,
    "D (Urbain)"       : 1.410,
    "E (Très urbain)"  : 1.503,
    "F (Métropole)"    : 1.337
}

# Relativités DrivAge
RELATIVITES_DRIVAGE = {
    "18-25 ans" : 1.000,
    "26-35 ans" : 0.884,
    "36-45 ans" : 1.304,
    "46-55 ans" : 1.525,
    "56-65 ans" : 1.327,
    "65+ ans"   : 1.551
}

# Relativités VehAge
RELATIVITES_VEHAGE = {
    "0-1 an (neuf)"  : 1.000,
    "2-5 ans"        : 0.986,
    "6-10 ans"       : 0.968,
    "11-15 ans"      : 0.815,
    "16-25 ans"      : 0.697,
    "Plus de 25 ans" : 0.363
}

# Relativités VehGas
RELATIVITES_VEHGAS = {
    "Diesel"  : 1.000,
    "Essence" : 0.835
}

# Relativités VehBrand
RELATIVITES_BRAND = {
    "Autres" : 1.000,
    "B1"     : 0.970,
    "B2"     : 0.974,
    "B3"     : 1.021,
    "B4"     : 0.930,
    "B5"     : 0.938,
    "B6"     : 0.963,
    "B10"    : 0.984,
    "B12"    : 0.880
}

# Fonction de calcul BonusMalus (relativité par point)
def relativite_bonusmalus(bm):
    # exp(0.0265 * (BM - 50)) — centré sur la référence BM=50
    return np.exp(0.0265 * (bm - 50))

# ============================================================
# FONCTION PRINCIPALE DE CALCUL
# ============================================================
def calculer_prime(area, driv_age, veh_age, veh_gas, veh_brand, bm):
    """
    Calcule la prime commerciale pour un profil donné.
    Méthode : Prime de référence × Relativités tarifaires
    Modèle   : GLM Poisson (fréquence) × Log-Normal (sévérité)
    """
    # Calcul du multiplicateur global
    multiplicateur = (
        RELATIVITES_AREA[area]      *
        RELATIVITES_DRIVAGE[driv_age] *
        RELATIVITES_VEHAGE[veh_age]  *
        RELATIVITES_VEHGAS[veh_gas]  *
        RELATIVITES_BRAND[veh_brand] *
        relativite_bonusmalus(bm)
    )

    # Prime pure individuelle
    prime_pure = PRIME_PURE_REF * multiplicateur

    # Prime commerciale avec chargements
    prime_commerciale = prime_pure / (1 - CHARGEMENT_TOTAL)

    return prime_pure, prime_commerciale, multiplicateur

# ============================================================
# INTERFACE UTILISATEUR
# ============================================================

# --- TITRE ---
st.title("🚗 Calculateur de Prime Automobile RC")
st.markdown("""
**Projet Master 2 Actuariat — Université du Burundi**  
Grille tarifaire construite sur le dataset *freMTPL2* 
(677 991 polices, marché français RC automobile)  
Modèle : GLM Poisson × Log-Normal | Chargements : 40%
""")
st.markdown("---")

# --- MISE EN PAGE EN COLONNES ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 Caractéristiques de l'assuré")

    area = st.selectbox(
        "Zone géographique",
        options=list(RELATIVITES_AREA.keys()),
        help="Zone A = très rural, Zone F = métropole"
    )

    driv_age = st.selectbox(
        "Classe d'âge du conducteur",
        options=list(RELATIVITES_DRIVAGE.keys())
    )

    bm = st.slider(
        "Coefficient Bonus-Malus",
        min_value=50,
        max_value=230,
        value=50,
        step=1,
        help="50 = bonus maximum légal | > 100 = malus"
    )

    st.subheader("🚘 Caractéristiques du véhicule")

    veh_age = st.selectbox(
        "Âge du véhicule",
        options=list(RELATIVITES_VEHAGE.keys())
    )

    veh_gas = st.selectbox(
        "Type de carburant",
        options=list(RELATIVITES_VEHGAS.keys())
    )

    veh_brand = st.selectbox(
        "Marque du véhicule",
        options=list(RELATIVITES_BRAND.keys()),
        help="Codes anonymisés — B12 est la marque la moins sinistrée"
    )

with col2:
    st.subheader("💰 Résultat tarifaire")

    # Calcul
    prime_pure, prime_commerciale, multiplicateur = calculer_prime(
        area, driv_age, veh_age, veh_gas, veh_brand, bm
    )

    # Affichage des résultats
    col_r1, col_r2 = st.columns(2)

    with col_r1:
        st.metric(
            label="Prime pure",
            value=f"{prime_pure:.2f} €",
            help="Prime couvrant exactement le risque technique"
        )

    with col_r2:
        st.metric(
            label="Prime commerciale",
            value=f"{prime_commerciale:.2f} €",
            delta=f"+{(prime_commerciale - PRIME_PURE_REF / (1 - CHARGEMENT_TOTAL)):.2f} € vs référence",
            help="Prime pure + 40% de chargements"
        )

    # Jauge de risque
    ratio_vs_ref = prime_commerciale / (PRIME_PURE_REF / (1 - CHARGEMENT_TOTAL))

    if ratio_vs_ref < 0.80:
        niveau_risque = "🟢 Risque faible"
        couleur = "green"
    elif ratio_vs_ref < 1.50:
        niveau_risque = "🟡 Risque modéré"
        couleur = "orange"
    elif ratio_vs_ref < 5.0:
        niveau_risque = "🟠 Risque élevé"
        couleur = "darkorange"
    else:
        niveau_risque = "🔴 Risque très élevé"
        couleur = "red"

    st.markdown(f"**Niveau de risque :** {niveau_risque}")
    st.markdown(f"**Multiplicateur global :** {multiplicateur:.4f}×")

    # Décomposition des relativités
    st.subheader("📊 Décomposition des relativités")

    rel_data = {
        "Facteur"      : ["Zone", "Âge conducteur", "BonusMalus",
                          "Âge véhicule", "Carburant", "Marque"],
        "Relativité"   : [
            RELATIVITES_AREA[area],
            RELATIVITES_DRIVAGE[driv_age],
            round(relativite_bonusmalus(bm), 4),
            RELATIVITES_VEHAGE[veh_age],
            RELATIVITES_VEHGAS[veh_gas],
            RELATIVITES_BRAND[veh_brand]
        ]
    }

    df_rel = pd.DataFrame(rel_data)
    df_rel["Effet"] = df_rel["Relativité"].apply(
        lambda x: "↑ Majoration" if x > 1.01
        else ("↓ Réduction" if x < 0.99 else "→ Neutre")
    )

    # Graphique en barres
    colors = [
        "green" if r < 0.99 else ("red" if r > 1.01 else "gray")
        for r in df_rel["Relativité"]
    ]

    fig = go.Figure(go.Bar(
        x=df_rel["Facteur"],
        y=df_rel["Relativité"],
        marker_color=colors,
        text=[f"{r:.4f}" for r in df_rel["Relativité"]],
        textposition="outside"
    ))

    fig.add_hline(y=1.0, line_dash="dash",
                  line_color="black",
                  annotation_text="Référence (1.000)")

    fig.update_layout(
        title="Relativités tarifaires par facteur",
        xaxis_title="Facteur de risque",
        yaxis_title="Relativité",
        height=350,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# SECTION 2 : COMPARAISON DE PROFILS
# ============================================================
st.markdown("---")
st.subheader("🔍 Comparaison de profils")
st.markdown("Comparez votre profil avec des profils types du portefeuille.")

profils_types = {
    "Profil référence\n(base)": {
        "area": "A (Très rural)", "driv_age": "18-25 ans",
        "veh_age": "0-1 an (neuf)", "veh_gas": "Diesel",
        "veh_brand": "Autres", "bm": 50
    },
    "Bon profil\n(économique)": {
        "area": "B (Rural)", "driv_age": "36-45 ans",
        "veh_age": "2-5 ans", "veh_gas": "Essence",
        "veh_brand": "B12", "bm": 50
    },
    "Profil moyen\n(cœur portefeuille)": {
        "area": "C (Semi-urbain)", "driv_age": "46-55 ans",
        "veh_age": "6-10 ans", "veh_gas": "Diesel",
        "veh_brand": "B2", "bm": 60
    },
    "Profil risqué\n(jeune + malus)": {
        "area": "E (Très urbain)", "driv_age": "18-25 ans",
        "veh_age": "0-1 an (neuf)", "veh_gas": "Essence",
        "veh_brand": "B3", "bm": 100
    },
    "Profil très risqué\n(fort malus urbain)": {
        "area": "F (Métropole)", "driv_age": "26-35 ans",
        "veh_age": "0-1 an (neuf)", "veh_gas": "Essence",
        "veh_brand": "B3", "bm": 150
    }
}

noms    = []
primes  = []
for nom, p in profils_types.items():
    _, pc, _ = calculer_prime(
        p["area"], p["driv_age"], p["veh_age"],
        p["veh_gas"], p["veh_brand"], p["bm"]
    )
    noms.append(nom)
    primes.append(round(pc, 2))

# Ajouter le profil courant
_, prime_courant, _ = calculer_prime(
    area, driv_age, veh_age, veh_gas, veh_brand, bm
)
noms.append("Votre profil")
primes.append(round(prime_courant, 2))

couleurs = ["steelblue"] * (len(noms) - 1) + ["orange"]

fig2 = go.Figure(go.Bar(
    x=noms,
    y=primes,
    marker_color=couleurs,
    text=[f"{p:.0f} €" for p in primes],
    textposition="outside"
))

fig2.update_layout(
    title="Comparaison des primes commerciales par profil",
    xaxis_title="Profil",
    yaxis_title="Prime commerciale (€)",
    height=400,
    showlegend=False
)

st.plotly_chart(fig2, use_container_width=True)

# ============================================================
# SECTION 3 : SENSIBILITE AU BONUS-MALUS
# ============================================================
st.markdown("---")
st.subheader("📈 Sensibilité au coefficient Bonus-Malus")
st.markdown("""
Cette courbe montre l'évolution de votre prime commerciale 
en fonction du coefficient Bonus-Malus, toutes choses égales par ailleurs.
""")

bm_range = list(range(50, 231, 5))
primes_bm = []
for bm_val in bm_range:
    _, pc_bm, _ = calculer_prime(
        area, driv_age, veh_age, veh_gas, veh_brand, bm_val
    )
    primes_bm.append(round(pc_bm, 2))

fig3 = go.Figure()

fig3.add_trace(go.Scatter(
    x=bm_range,
    y=primes_bm,
    mode="lines",
    name="Prime commerciale",
    line=dict(color="steelblue", width=2)
))

fig3.add_vline(
    x=bm,
    line_dash="dash",
    line_color="orange",
    annotation_text=f"Votre BM : {bm}"
)

fig3.update_layout(
    title="Évolution de la prime selon le Bonus-Malus",
    xaxis_title="Coefficient Bonus-Malus",
    yaxis_title="Prime commerciale (€)",
    height=350
)

st.plotly_chart(fig3, use_container_width=True)

# ============================================================
# SECTION 4 : STRUCTURE DE LA PRIME
# ============================================================
st.markdown("---")
st.subheader("🥧 Décomposition de la prime commerciale")

col_p1, col_p2 = st.columns([1, 1])

with col_p1:
    # Graphique camembert
    labels = ["Prime pure (risque technique)",
              "Frais de gestion (25%)",
              "Marge de sécurité (10%)",
              "Coût réassurance (5%)"]
    values = [
        prime_pure,
        prime_commerciale * CHARGEMENT_FRAIS,
        prime_commerciale * CHARGEMENT_SECURITE,
        prime_commerciale * CHARGEMENT_REASSURANCE
    ]

    fig4 = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker_colors=["steelblue", "orange",
                        "lightcoral", "lightgreen"]
    ))

    fig4.update_layout(
        title=f"Structure de la prime : {prime_commerciale:.2f} €",
        height=350
    )

    st.plotly_chart(fig4, use_container_width=True)

with col_p2:
    st.markdown("### Détail des composantes")
    st.markdown(f"""
    | Composante | Montant |
    |---|---|
    | Prime pure (risque technique) | **{prime_pure:.2f} €** |
    | Frais de gestion (25%) | {prime_commerciale * CHARGEMENT_FRAIS:.2f} € |
    | Marge de sécurité (10%) | {prime_commerciale * CHARGEMENT_SECURITE:.2f} € |
    | Coût réassurance (5%) | {prime_commerciale * CHARGEMENT_REASSURANCE:.2f} € |
    | **Prime commerciale totale** | **{prime_commerciale:.2f} €** |
    """)

    st.info(f"""
    💡 **Interprétation actuarielle**
    
    Votre prime pure de **{prime_pure:.2f} €** correspond au coût 
    technique attendu de votre sinistralité sur un an.
    
    Le multiplicateur global de **{multiplicateur:.3f}×** résulte de 
    la combinaison de tous vos facteurs de risque.
    
    Sans chargements, la prime de référence serait de 
    **{PRIME_PURE_REF:.2f} €**.
    """)

# ============================================================
# PIED DE PAGE
# ============================================================
st.markdown("---")
st.markdown("""
<small>
**Source des données :** freMTPL2freq/freMTPL2sev (CASdatasets, 677 991 polices)  
**Modèle :** GLM Poisson (fréquence) × Log-Normal (sévérité)  
**Auteur :** Thierry NIYOKWIZIGIRWA — Master 2 Actuariat, Université du Burundi — 2026  
*Ce calculateur est un outil académique basé sur un modèle statistique.*
</small>
""", unsafe_allow_html=True)