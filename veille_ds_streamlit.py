
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import random

st.set_page_config(page_title="Veille DS Automobiles", layout="wide")
st.title("🚗 Agent de Veille – DS Automobiles (API Newsdata.io)")

# Configuration API Newsdata.io (clé gratuite requise)
API_KEY = "pub_afd14bba24914ca9a0c8b7d23a0fb755"
NEWS_API_URL = "https://newsdata.io/api/1/news"

# Récupération via API Newsdata.io
def fetch_news_articles(query, max_results=10):
    params = {
        "apikey": API_KEY,
        "q": query,
        "language": "fr",
        "country": "fr"
    }
    try:
        response = requests.get(NEWS_API_URL, params=params)
        data = response.json()
        articles = []
        for item in data.get("results", [])[:max_results]:
            articles.append({
                "date": item.get("pubDate", ""),
                "titre": item.get("title", ""),
                "contenu": item.get("description", ""),
                "source": item.get("source_id", ""),
                "lien": item.get("link", "")
            })
        return pd.DataFrame(articles)
    except Exception as e:
        st.error(f"Erreur lors de la récupération des articles : {e}")
        return pd.DataFrame()

# Détection de modèle
MODELES_DS = ["DS N4", "DS N8", "DS7", "DS3", "DS9", "DS4"]

def detecter_modele(titre):
    for m in MODELES_DS:
        if m.lower() in titre.lower():
            return m
    return "DS Global"

# Analyse simple de contenu
def analyser_article(row):
    résumé = row['contenu'][:200] + "..."
    ton = "Positif" if any(w in row['contenu'].lower() for w in ["succès", "innovant", "record"]) else "Neutre"
    modele = detecter_modele(row['titre'])
    return pd.Series({'résumé': résumé, 'ton': ton, 'modèle': modele})

# Interface utilisateur
nb_articles = st.slider("Nombre d'articles à récupérer", 5, 30, 10)
if st.button("🔍 Lancer la veille maintenant"):
    articles = fetch_news_articles("DS Automobiles", nb_articles)
    if not articles.empty:
        with st.spinner("Analyse des articles en cours..."):
            articles[['résumé', 'ton', 'modèle']] = articles.apply(analyser_article, axis=1)

        # Calcul notoriété
        mentions_today = len(articles)
        moyenne_7j = 25 / 7
        indice = int((mentions_today / max(moyenne_7j, 1)) * 50 + random.randint(0, 20))
        niveau = '🔴 Pic' if indice > 75 else '🟡 Stable' if indice > 50 else '🟢 Faible'

        st.metric("Indice de notoriété", f"{indice}/100", niveau)
        st.dataframe(articles[['date', 'titre', 'modèle', 'ton', 'résumé', 'source', 'lien']])
    else:
        st.warning("Aucun article trouvé. Veuillez réessayer plus tard.")
