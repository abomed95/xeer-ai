# =========================================================
# Xeer AI Premium - Streamlit Frontend (Improved Blue-Gold UI)
# =========================================================

import uuid
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/ask"

st.set_page_config(
    page_title="Xeer AI Premium",
    page_icon="⚖️",
    layout="wide",
)

# =========================================================
# STYLE GLOBAL
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top right, rgba(212,175,55,0.10), transparent 24%),
        radial-gradient(circle at top left, rgba(59,130,246,0.08), transparent 24%),
        linear-gradient(180deg, #06111f 0%, #0b1525 100%);
    color: #f8fafc;
}

/* zone principale */
.block-container {
    max-width: 1320px;
    padding-top: 1rem;
    padding-bottom: 1rem;
}

/* sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #091320 0%, #0f1d31 100%);
    border-right: 1px solid rgba(212,175,55,0.14);
}

/* textes sidebar */
.sidebar-logo {
    font-size: 1.7rem;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 0.35rem;
}

.sidebar-logo span {
    color: #d4af37;
}

.sidebar-muted {
    color: #a7b5c8;
    font-size: 0.96rem;
    line-height: 1.75;
    margin-bottom: 1rem;
}

.section-title {
    color: #f8fafc;
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 0.55rem;
}

/* cartes sidebar */
.nav-card, .recent-card, .hero-card, .feature-card, .chat-shell {
    background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.025));
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 22px;
    box-shadow: 0 14px 40px rgba(0,0,0,0.18);
}

.nav-card, .recent-card {
    padding: 14px;
}

.nav-item {
    padding: 12px 14px;
    border-radius: 14px;
    margin-bottom: 8px;
    background: rgba(255,255,255,0.03);
    border: 1px solid transparent;
    color: #e5e7eb;
    font-weight: 600;
}

.nav-item.active {
    background: rgba(212,175,55,0.10);
    border: 1px solid rgba(212,175,55,0.25);
    color: #f4d27a;
}

.recent-item {
    padding: 10px 0;
    color: #c7d2e0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    font-size: 0.94rem;
}

.recent-item:last-child {
    border-bottom: none;
}

.session-box {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(212,175,55,0.14);
    border-radius: 14px;
    padding: 10px 12px;
    color: #e2e8f0;
    font-size: 0.82rem;
    word-break: break-all;
}

/* hero */
.hero-card {
    padding: 26px 28px;
    margin-bottom: 18px;
}

.hero-badge {
    display: inline-block;
    background: linear-gradient(90deg, #caa74a, #f4d27a);
    color: #111827;
    padding: 7px 14px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 800;
    margin-bottom: 14px;
}

.hero-title {
    font-size: 2.2rem;
    font-weight: 800;
    line-height: 1.1;
    color: #ffffff;
    margin-bottom: 10px;
}

.hero-title span {
    background: linear-gradient(90deg, #d4af37, #f8e7a1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-sub {
    color: #a7b5c8;
    font-size: 1rem;
    line-height: 1.8;
    max-width: 850px;
    margin-bottom: 18px;
}

.kpi-row {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
    margin-top: 8px;
}

.kpi-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 14px;
}

.kpi-label {
    color: #9fb0c6;
    font-size: 0.82rem;
    margin-bottom: 6px;
}

.kpi-value {
    color: #f8fafc;
    font-size: 1rem;
    font-weight: 800;
}

/* cartes d'accueil */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
    margin-bottom: 20px;
}

.feature-card {
    padding: 20px;
}

.feature-icon {
    width: 52px;
    height: 52px;
    display: grid;
    place-items: center;
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(212,175,55,0.18), rgba(255,255,255,0.04));
    border: 1px solid rgba(212,175,55,0.18);
    margin-bottom: 14px;
    font-size: 1.4rem;
}

.feature-title {
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 8px;
    color: #ffffff;
}

.feature-desc {
    color: #a7b5c8;
    line-height: 1.7;
    font-size: 0.95rem;
}

/* zone chat */
.chat-shell {
    padding: 18px;
    margin-top: 4px;
}

.msg-user {
    background: linear-gradient(135deg, #10213b, #162847);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 18px;
    padding: 14px 16px;
    margin-bottom: 14px;
    color: #f8fafc;
}

.msg-ai {
    background: linear-gradient(135deg, rgba(11,19,32,0.98), rgba(15,23,42,0.96));
    border: 1px solid rgba(212,175,55,0.18);
    border-radius: 18px;
    padding: 16px 18px;
    margin-bottom: 14px;
    color: #f8fafc;
    box-shadow: 0 10px 28px rgba(0,0,0,0.20);
}

.msg-ai-title {
    font-size: 1rem;
    font-weight: 800;
    color: #f4d27a;
    margin-bottom: 10px;
}

.source-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-left: 4px solid #d4af37;
    border-radius: 14px;
    padding: 12px;
    margin-bottom: 12px;
}

.muted {
    color: #9fb0c6;
    font-size: 0.88rem;
}

.copy-box textarea {
    background: rgba(255,255,255,0.03) !important;
    color: #f8fafc !important;
}

div[data-testid="stExpander"] {
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.02);
}

/* input chat */
.chat-input-wrap {
    margin-top: 12px;
}

div[data-testid="stChatInput"] {
    position: sticky;
    bottom: 0;
    background: transparent;
}

div[data-testid="stChatInput"] > div {
    background: linear-gradient(135deg, rgba(11,19,32,0.98), rgba(15,23,42,0.98));
    border: 1px solid rgba(212,175,55,0.16);
    border-radius: 18px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.28);
}

/* boutons */
.stButton > button {
    border-radius: 14px !important;
    font-weight: 700 !important;
    border: 1px solid rgba(212,175,55,0.18) !important;
    background: linear-gradient(135deg, #0f1f38, #132744) !important;
    color: white !important;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    border-color: rgba(212,175,55,0.45) !important;
    color: #f4d27a !important;
    transform: translateY(-1px);
}

/* footer */
.footer-note {
    text-align: center;
    color: #8ea2bb;
    font-size: 0.88rem;
    margin-top: 20px;
}

/* responsive */
@media (max-width: 1150px) {
    .feature-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .kpi-row {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 700px) {
    .feature-grid,
    .kpi-row {
        grid-template-columns: 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# ÉTAT DE SESSION
# =========================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "top_k" not in st.session_state:
    st.session_state.top_k = 5

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown('<div class="sidebar-logo">⚖️ Xeer <span>AI</span></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-muted">Assistant juridique-culturel premium propulsé par Xeer Ciise, RAG et OpenAI.</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="section-title">Navigation</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    st.markdown('<div class="nav-item active">🏠 Accueil</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">🔎 Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">🧠 Mémoire</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">📚 Sources</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Réglages</div>', unsafe_allow_html=True)
    st.session_state.top_k = st.slider(
        "Nombre de sources",
        min_value=3,
        max_value=8,
        value=st.session_state.top_k
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Récents chats</div>', unsafe_allow_html=True)
    st.markdown('<div class="recent-card">', unsafe_allow_html=True)
    for recent in [
        "Waa maxay Xeer Ciise ?",
        "Maxaa loo isticmaalaa ?",
        "Explique le Xeer Ciise",
        "Qu’est-ce que Xeer Ciise ?"
    ]:
        st.markdown(f'<div class="recent-item">{recent}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Session</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="session-box">{st.session_state.session_id}</div>', unsafe_allow_html=True)

    st.markdown("")
    if st.button("🆕 Nouvelle conversation", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

# =========================================================
# HERO
# =========================================================
st.markdown("""
<div class="hero-card">
    <div class="hero-badge">ÉDITION PREMIUM+ BLUE GOLD</div>
    <div class="hero-title">Xeer AI <span>Premium</span></div>
    <div class="hero-sub">
        Votre assistant IA premium pour le droit coutumier somalien, les connaissances juridiques et culturelles,
        les sources vérifiées et les réponses multilingues structurées.
    </div>
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-label">Mode</div>
            <div class="kpi-value">Premium Chat</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Mémoire</div>
            <div class="kpi-value">Activée</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Sources</div>
            <div class="kpi-value">Vérifiables</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Langues</div>
            <div class="kpi-value">SO / FR / EN</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# CARTES D’ACCUEIL SI PAS DE MESSAGES
# =========================================================
if not st.session_state.messages:
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon">🎓</div>
            <div class="feature-title">Soutien académique</div>
            <div class="feature-desc">
                Explorez Xeer Ciise pour la recherche, l’apprentissage et l’étude structurée du droit et de la culture.
            </div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <div class="feature-title">Mémoire de conversation</div>
            <div class="feature-desc">
                Posez naturellement des questions de suivi et gardez le même contexte tout au long de la séance.
            </div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">⚖️</div>
            <div class="feature-title">Réponses juridiques et culturelles</div>
            <div class="feature-desc">
                Obtenez des réponses structurées fondées sur le corpus Xeer Ciise et le droit coutumier somalien.
            </div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">💡</div>
            <div class="feature-title">Génération d’insights</div>
            <div class="feature-desc">
                Comprenez les significations, les rôles, les traditions et les sources avec des réponses claires et premium.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# ZONE CHAT
# =========================================================
st.markdown('<div class="chat-shell">', unsafe_allow_html=True)

for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(
            f"""
            <div class="msg-user">
                <b>👤 Vous</b><br><br>
                {msg["content"]}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="msg-ai">
                <div class="msg-ai-title">🤖 Xeer AI Premium</div>
                {msg["content"]}
            </div>
            """,
            unsafe_allow_html=True
        )

        # bloc stable pour copier / récupérer la réponse
        with st.expander("📋 Copier / récupérer la réponse"):
            st.text_area(
                "Réponse sélectionnable",
                value=msg["content"],
                height=180,
                key=f"copy_area_{idx}",
            )

            st.download_button(
                label="⬇️ Télécharger la réponse (.txt)",
                data=msg["content"],
                file_name=f"xeer_ai_reponse_{idx}.txt",
                mime="text/plain",
                key=f"download_{idx}",
            )

        # affichage des sources
        if msg.get("sources"):
            with st.expander("📚 Sources et extraits"):
                for i, src in enumerate(msg["sources"], start=1):
                    st.markdown(f"""
<div class="source-card">
    <b>Source {i}</b><br>
    <span class="muted">
        Page: {src.get('page', 'N/A')} |
        Chunk: {src.get('chunk_index', 'N/A')} |
        Score: {src.get('score', 'N/A')} |
        Distance: {src.get('distance', 'N/A')}
    </span>
    <hr>
    <div>{src.get('excerpt', '')}</div>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# INPUT CHAT
# =========================================================
st.markdown('<div class="chat-input-wrap">', unsafe_allow_html=True)
prompt = st.chat_input("Pose ta question sur Xeer Ciise...")
st.markdown('</div>', unsafe_allow_html=True)

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    st.rerun()

# =========================================================
# ENVOI À L’API
# =========================================================
if st.session_state.messages:
    last_msg = st.session_state.messages[-1]

    if last_msg["role"] == "user" and (
        len(st.session_state.messages) == 1 or
        st.session_state.messages[-2]["role"] != "assistant"
    ):
        with st.spinner("Xeer AI Premium réfléchit..."):
            try:
                response = requests.post(
                    API_URL,
                    json={
                        "question": last_msg["content"],
                        "top_k": st.session_state.top_k,
                        "session_id": st.session_state.session_id,
                    },
                    timeout=90,
                )
                response.raise_for_status()
                data = response.json()

                answer = data.get("answer", "Aucune réponse.")
                sources = data.get("sources", [])

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })
                st.rerun()

            except requests.exceptions.ConnectionError:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "❌ Impossible de joindre l’API FastAPI. Lance d’abord le backend.",
                    "sources": []
                })
                st.rerun()

            except requests.exceptions.Timeout:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "❌ La requête a pris trop de temps.",
                    "sources": []
                })
                st.rerun()

            except requests.exceptions.HTTPError as e:
                try:
                    detail = response.json()
                except Exception:
                    detail = str(e)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ Erreur HTTP : {detail}",
                    "sources": []
                })
                st.rerun()

            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ Erreur : {e}",
                    "sources": []
                })
                st.rerun()

# =========================================================
# FOOTER
# =========================================================
st.markdown(
    '<div class="footer-note">Xeer AI Premium · Expérience de chat premium construite avec FastAPI, Streamlit, ChromaDB et OpenAI</div>',
    unsafe_allow_html=True
)