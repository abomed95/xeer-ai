import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/ask"

st.set_page_config(
    page_title="Xeer AI",
    page_icon="📘",
    layout="wide",
)

st.title("📘 Xeer AI")
st.caption("Assistant IA basé sur le livre Xeer Ciise")

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.header("Paramètres")
    top_k = st.slider("Nombre de résultats", min_value=3, max_value=10, value=5)

    st.markdown("---")
    st.subheader("Exemples")
    st.write("Waa maxay Xeer Ciise?")
    st.write("Xeerkan maxaa loogu baahday?")
    st.write("Explique le Xeer Ciise")

question = st.text_input("Pose ta question", placeholder="Ex: Waa maxay Xeer Ciise?")

if st.button("Envoyer"):
    if not question.strip():
        st.warning("Écris une question d'abord.")
    else:
        with st.spinner("Recherche en cours..."):
            try:
                response = requests.post(
                    API_URL,
                    json={
                        "question": question,
                        "top_k": top_k
                    },
                    timeout=60
                )

                response.raise_for_status()
                data = response.json()

                st.session_state.history.insert(0, data)

            except requests.exceptions.ConnectionError:
                st.error("Impossible de joindre l’API FastAPI. Lance d’abord le backend.")
            except requests.exceptions.Timeout:
                st.error("La requête a pris trop de temps.")
            except requests.exceptions.HTTPError as e:
                st.error(f"Erreur HTTP : {e}")
            except Exception as e:
                st.error(f"Erreur : {e}")

if st.session_state.history:
    latest = st.session_state.history[0]

    st.subheader("Réponse")
    st.write(latest.get("answer", ""))

    sources = latest.get("sources", [])
    if sources:
        st.subheader("Sources")
        for i, src in enumerate(sources, start=1):
            with st.expander(f"Source {i} — page {src.get('page', 'N/A')}"):
                st.write(f"**ID** : {src.get('id', '')}")
                st.write(f"**Page** : {src.get('page', '')}")
                st.write(f"**Chunk** : {src.get('chunk_index', '')}")
                st.write(f"**Fichier** : {src.get('source_file', '')}")
                st.write(f"**Distance** : {src.get('distance', '')}")
                st.write(f"**Score** : {src.get('score', '')}")
                st.write("**Extrait :**")
                st.write(src.get("excerpt", ""))

    if len(st.session_state.history) > 1:
        st.subheader("Historique")
        for idx, item in enumerate(st.session_state.history[1:], start=1):
            with st.expander(f"Question précédente {idx}: {item.get('question', '')}"):
                st.write(item.get("answer", ""))