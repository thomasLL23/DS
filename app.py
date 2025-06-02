import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import random
from xml.etree import ElementTree as ET

st.set_page_config(page_title="Veille DS Automobiles", layout="wide")
st.title("🚗 Agent de Veille – DS Automobiles (APIs multiples)")

# Configuration API Newsdata.io
API_KEY_NEWSDATA = "pub_afd14bba24914ca9a0c8b7d23a0fb755"
NEWSDATA_URL = "https://newsdata.io/api/1/news"

# ContextualWeb
CONTEXTUAL_API_URL = "https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/Search/NewsSearchAPI"
HEADERS_CONTEXTUAL = {
    "X-RapidAPI-Key": "",
    "X-RapidAPI-Host": "contextualwebsearch-websearch-v1.p.rapidapi.com"
}

# Mediastack API
MEDIASTACK_API_KEY = "eaa929770f885d5e15b62d7d16a521d8"
MEDIASTACK_URL = "http://api.mediastack.com/v1/news"

# Flux RSS Google News et LeBlogAuto
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=DS+Automobiles&hl=fr&gl=FR&ceid=FR:fr",
    "https://www.leblogauto.com/feed"
]

def fetch_newsdata_articles(query, max_results=5):
    params = {
        "apikey": API_KEY_NEWSDATA,
        "q": query,
        "language": "fr"
    }
    try:
        response = requests.get(NEWSDATA_URL, params=params)
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
        return articles
    except:
        return []

def fetch_contextual_articles(query, max_results=5):
    params = {
        "q": query,
        "pageNumber": "1",
        "pageSize": str(max_results),
        "autoCorrect": "true"
    }
    try:
        response = requests.get(CONTEXTUAL_API_URL, headers=HEADERS_CONTEXTUAL, params=params)
        data = response.json()
        articles = []
        for item in data.get("value", []):
            articles.append({
                "date": item.get("datePublished", ""),
                "titre": item.get("title", ""),
                "contenu": item.get("body", ""),
                "source": item.get("provider", {}).get("name", ""),
                "lien": item.get("url", "")
            })
        return articles
    except:
        return []

def fetch_mediastack_articles(query, max_results=5):
    params = {
        "access_key": MEDIASTACK_API_KEY,
        "keywords": query,
        "languages": "fr"
    }
    try:
        response = requests.get(MEDIASTACK_URL, params=params)
        data = response.json()
        articles = []
        for item in data.get("data", [])[:max_results]:
            articles.append({
                "date": item.get("published_at", ""),
                "titre": item.get("title", ""),
                "contenu": item.get("description", ""),
                "source": item.get("source", ""),
                "lien": item.get("url", "")
            })
        return articles
    except:
        return []

def fetch_rss_articles(query, max_results=5):
    articles = []
    for feed_url in RSS_FEEDS:
        try:
            resp = requests.get(feed_url)
            tree = ET.fromstring(resp.content)
            items = tree.findall(".//item")
            count = 0
            for item in items:
                title = item.findtext("title") or ""
                desc = item.findtext("description") or ""
                if query.lower() in title.lower() or query.lower() in desc.lower():
                    articles.append({
                        "date": item.findtext("pubDate", ""),
                        "titre": title,
                        "contenu": desc,
                        "source": feed_url,
                        "lien": item.findtext("link", "")
                    })
                    count += 1
                    if count >= max_results:
                        break
        except:
            continue
    return articles

MODELES_DS = ["DS N4", "DS N8", "DS7", "DS3", "DS9", "DS4"]

def detecter_modele(titre):
    for m in MODELES_DS:
        if m.lower() in titre.lower():
            return m
    return "DS Global"

def analyser_article(row):
    résumé = row['contenu'][:200] + "..."
    ton = "Positif" if any(w in row['contenu'].lower() for w in ["succès", "innovant", "record"]) else "Neutre"
    modele = detecter_modele(row['titre'])
    return pd.Series({'résumé': résumé, 'ton': ton, 'modèle': modele})

nb_articles = st.slider("Nombre total d'articles à récupérer (par source)", 5, 30, 10)
if st.button("🔍 Lancer la veille maintenant"):
    newsdata_articles = fetch_newsdata_articles("DS Automobiles", nb_articles)
    contextual_articles = fetch_contextual_articles("DS Automobiles", nb_articles)
    mediastack_articles = fetch_mediastack_articles("DS Automobiles", nb_articles)
    rss_articles = fetch_rss_articles("DS Automobiles", nb_articles)

    articles = pd.DataFrame(newsdata_articles + contextual_articles + mediastack_articles + rss_articles)

    if not articles.empty:
        with st.spinner("Analyse des articles en cours..."):
            articles[['résumé', 'ton', 'modèle']] = articles.apply(analyser_article, axis=1)

        mentions_today = len(articles)
        moyenne_7j = 25 / 7
        indice = int((mentions_today / max(moyenne_7j, 1)) * 50 + random.randint(0, 20))
        niveau = '🔴 Pic' if indice > 75 else '🟡 Stable' if indice > 50 else '🟢 Faible'

        st.metric("Indice de notoriété", f"{indice}/100", niveau)
        st.dataframe(articles[['date', 'titre', 'modèle', 'ton', 'résumé', 'source', 'lien']])
    else:
        st.warning("Aucun article trouvé.")
