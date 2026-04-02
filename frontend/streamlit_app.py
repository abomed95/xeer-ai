import uuid
import json
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/ask"

st.set_page_config(
    page_title="Xeer AI Premium",
    page_icon="⚖️",
    layout="wide",
)

# =========================
# PREMIUM+ CSS BLEU-OR
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top right, rgba(212,175,55,0.10), transparent 25%),
        radial-gradient(circle at top left, rgba(59,130,246,0.10), transparent 25%),
        linear-gradient(180deg, #06111f 0%, #0a1628 45%, #0b1420 100%);
    color: #f8fafc;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1320 0%, #0f1b2e 100%);
    border-right: 1px solid rgba(212,175,55,0.14);
}

.block-container {
    max-width: 1180px;
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}

.hero-wrap {
    background: linear-gradient(135deg, rgba(10,20,35,0.95), rgba(15,23,42,0.92));
    border: 1px solid rgba(212,175,55,0.16);
    border-radius: 24px;
    padding: 26px 28px 20px 28px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.35);
    margin-bottom: 1.2rem;
}

.premium-badge {
    display: inline-block;
    background: linear-gradient(90deg, #caa74a, #f4d27a);
    color: #111827;
    padding: 7px 14px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.4px;
    margin-bottom: 14px;
}

.main-title {
    font-size: 2.7rem;
    font-weight: 800;
    line-height: 1.05;
    margin-bottom: 0.4rem;
    color: #ffffff;
}

.main-title span {
    background: linear-gradient(90deg, #d4af37, #f8e7a1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.sub-title {
    color: #a9b7c9;
    font-size: 1.02rem;
    margin-bottom: 1.2rem;
    max-width: 850px;
}

.kpi-row {
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
    margin-top: 10px;
}

.kpi-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 12px 14px;
    min-width: 160px;
}

.kpi-label {
    color: #94a3b8;
    font-size: 0.82rem;
    margin-bottom: 4px;
}

.kpi-value {
    color: #f8fafc;
    font-size: 1rem;
    font-weight: 700;
}

.user-bubble {
    background: linear-gradient(135deg, #10213b, #162847);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 18px;
    padding: 15px 16px;
    margin-bottom: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.18);
}

.assistant-bubble {
    background: linear-gradient(135deg, rgba(11,19,32,0.98), rgba(15,23,42,0.96));
    border: 1px solid rgba(212,175,55,0.18);
    border-radius: 18px;
    padding: 18px 18px;
    margin-bottom: 14px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.24);
}

.answer-title {
    font-size: 1rem;
    font-weight: 800;
    color: #f4d27a;
    margin-bottom: 10px;
}

.copy-btn {
    display: inline-block;
    background: linear-gradient(90deg, #16233b, #0f1a2d);
    color: #f4d27a;
    border: 1px solid rgba(212,175,55,0.30);
    padding: 8px 14px;
    border-radius: 10px;
    cursor: pointer;
    margin-top: 10px;
    font-size: 0.92rem;
    font-weight: 600;
}

.source-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.02));
    border: 1px solid rgba(255,255,255,0.08);
    border-left: 4px solid #d4af37;
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 12px;
}

.source-meta {
    color: #9fb0c6;
    font-size: 0.85rem;
    margin-bottom: 8px;
}

.sidebar-logo {
    font-size: 1.45rem;
    font-weight: 800;
    color: white;
    margin-bottom: 0.35rem;
}

.sidebar-logo span {
    color: #f4d27a;
}

.sidebar-muted {
    color: #94a3b8;
    font-size: 0.92rem;
    margin-bottom: 1rem;
}

.section-title {
    color: #f8fafc;
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
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

.example-box {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 10px 12px;
    margin-bottom: 10px;
    color: #e5e7eb;
}

.footer-note {
    margin-top: 22px;
    color: #8ea2bb;
    font-size: 0.86rem;
    text-align: center;
    padding: 14px 0 6px 0;
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

hr {
    border-color: rgba(255,255,255,0.08);
}

[data-testid="stExpander"] {
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.02);
}
</style>
""", unsafe_allow_html=True)

# =========================
# SESSION STATE
# =========================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "top_k" not in st.session_state:
    st.session_state.top_k = 5

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown('<div class="sidebar-logo">⚖️ Xeer <span>AI</span></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-muted">Assistant juridique-culturel premium propulsé par Xeer Ciise, RAG et OpenAI.</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="section-title">Réglages</div>', unsafe_allow_html=True)
    st.session_state.top_k = st.slider(
        "Nombre de sources",
        min_value=3,
        max_value=8,
        value=st.session_state.top_k
    )

    st.markdown("---")
    st.markdown('<div class="section-title">Exemples</div>', unsafe_allow_html=True)
    for ex in [
        "Waa maxay Xeer Ciise ?",
        "Maxaa loo isticmaalaa ?",
        "Explique le Xeer Ciise",
        "Qu’est-ce que Xeer Ciise ?"
    ]:
        st.markdown(f'<div class="example-box">{ex}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-title">Session</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="session-box">{st.session_state.session_id}</div>', unsafe_allow_html=True)

    st.markdown("")
    if st.button("🆕 Nouvelle conversation", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

# =========================
# HERO HEADER
# =========================
st.markdown("""
<div class="hero-wrap">
    <div class="premium-badge">ÉDITION PREMIUM+ BLUE GOLD</div>
    <div class="main-title">Xeer AI <span>Premium</span></div>
    <div class="sub-title">
        Une interface haut de gamme pour interroger, comprendre et explorer le Xeer Ciise avec mémoire conversationnelle, sources traçables et réponses structurées.
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

# Message d’accueil
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center; padding:30px 10px 18px 10px; color:#9fb0c6;">
        <h3 style="color:#f8fafc;">👋 Bienvenue sur Xeer AI Premium</h3>
        <p>Pose une question sur le Xeer Ciise et obtiens une réponse structurée avec mémoire et sources.</p>
    </div>
    """, unsafe_allow_html=True)

# =========================
# DISPLAY MESSAGES
# =========================
for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(
            f"""
            <div class="user-bubble">
                <b>👤 Vous</b><br><br>
                {msg["content"]}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="assistant-bubble">
                <div class="answer-title">🤖 Xeer AI Premium</div>
                {msg["content"]}
            </div>
            """,
            unsafe_allow_html=True
        )

        safe_text = json.dumps(msg["content"])
        st.markdown(f"""
        <button onclick="navigator.clipboard.writeText({safe_text})" class="copy-btn">
            📋 Copier la réponse
        </button>
        """, unsafe_allow_html=True)

        if msg.get("sources"):
            with st.expander("📚 Sources et extraits"):
                for i, src in enumerate(msg["sources"], start=1):
                    st.markdown(f"""
<div class="source-card">
    <b>Source {i}</b>
    <div class="source-meta">
        Page: {src.get('page', 'N/A')} |
        Chunk: {src.get('chunk_index', 'N/A')} |
        Score: {src.get('score', 'N/A')} |
        Distance: {src.get('distance', 'N/A')}
    </div>
    <div>{src.get('excerpt', '')}</div>
</div>
""", unsafe_allow_html=True)

# =========================
# CHAT INPUT
# =========================
prompt = st.chat_input("Pose ta question sur Xeer Ciise...")

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    st.rerun()

# =========================
# PROCESS LAST USER MESSAGE
# =========================
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

# focus auto sur l’input
st.markdown("""
<script>
const input = window.parent.document.querySelector('textarea');
if (input) { input.focus(); }
</script>
""", unsafe_allow_html=True)

# =========================
# FOOTER
# =========================
st.markdown(
    '<div class="footer-note">Xeer AI Premium · Construit avec FastAPI, Streamlit, ChromaDB et OpenAI</div>',
    unsafe_allow_html=True
)