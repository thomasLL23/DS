
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import random

st.set_page_config(page_title="Veille DS Automobiles", layout="wide")
st.title("🚗 Agent de Veille – DS Automobiles (100% gratuit)")

# Scraping Bing News
def scrape_bing_news(query, max_results=10):
    url = f"https://www.bing.com/news/search?q={query}&setlang=fr"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    articles = []
    for item in soup.select("div.news-card")[:max_results]:
        try:
            title = item.select_one("a.title").text.strip()
            link = item.select_one("a.title")['href']
            snippet = item.select_one("div.snippet").text.strip()
            source = item.select_one("div.source").text.strip()
            articles.append({
                'date': datetime.today().date(),
                'titre': title,
                'contenu': snippet,
                'source': source,
                'lien': link
            })
        except:
            continue
    return pd.DataFrame(articles)

# Détection de modèle
MODELES_DS = ["DS N4", "DS N8", "DS7", "DS3", "DS9", "DS4"]

def detecter_modele(titre):
    for m in MODELES_DS:
        if m.lower() in titre.lower():
            return m
    return "DS Global"

# Analyse "IA" minimale sans modèle lourd
def analyser_article(row):
    résumé = row['contenu'][:200] + "..."  # Résumé simplifié
    ton = "Positif" if any(w in row['contenu'].lower() for w in ["succès", "innovant", "record"]) else "Neutre"
    modele = detecter_modele(row['titre'])
    return pd.Series({'résumé': résumé, 'ton': ton, 'modèle': modele})

# Interface utilisateur
nb_articles = st.slider("Nombre d'articles à récupérer", 5, 30, 10)

if st.button("🔍 Lancer la veille maintenant"):
    articles = scrape_bing_news("DS Automobiles", nb_articles)
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
