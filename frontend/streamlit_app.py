import uuid
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/ask"

st.set_page_config(
    page_title="Xeer AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS (Copilot-inspired) ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    /* GitHub dark palette */
    --bg:           #0d1117;
    --bg-elev-1:    #161b22;
    --bg-elev-2:    #1c2128;
    --bg-hover:     #21262d;
    --bg-input:     #0d1117;

    --border:        #30363d;
    --border-muted:  #21262d;
    --border-strong: #444c56;

    --text:         #e6edf3;
    --text-muted:   #7d8590;
    --text-dim:     #6e7681;

    /* Copilot brand: purple → blue gradient */
    --copilot-1:    #a371f7;
    --copilot-2:    #8957e5;
    --copilot-3:    #58a6ff;
    --copilot-grad: linear-gradient(135deg, #a371f7 0%, #8957e5 50%, #58a6ff 100%);
    --copilot-soft: rgba(163,113,247,0.10);
    --copilot-dim:  rgba(163,113,247,0.18);

    --success: #3fb950;
    --error:   #f85149;

    --radius-lg: 12px;
    --radius-md: 8px;
    --radius-sm: 6px;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text);
    font-feature-settings: 'cv11', 'ss01';
    -webkit-font-smoothing: antialiased;
}

.stApp { background: var(--bg); min-height: 100vh; }
.block-container { max-width: 920px; padding: 1rem 2rem 8rem; }

/* Hide Streamlit chrome */
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; }

/* ═══════════════════════ SIDEBAR ═══════════════════════ */
section[data-testid="stSidebar"] {
    background: var(--bg-elev-1);
    border-right: 1px solid var(--border-muted);
}
section[data-testid="stSidebar"] > div { padding: 1rem 0.75rem; }

.sb-brand {
    display: flex; align-items: center; gap: 10px;
    padding: 6px 8px 14px;
}
.sb-brand-mark {
    width: 28px; height: 28px; border-radius: 8px;
    display: grid; place-items: center;
    background: var(--copilot-grad);
    color: white; font-weight: 700; font-size: 1rem;
    box-shadow: 0 0 0 1px rgba(255,255,255,0.06) inset,
                0 4px 12px rgba(163,113,247,0.25);
}
.sb-brand-text {
    font-size: 0.95rem; font-weight: 600; color: var(--text);
    letter-spacing: -0.01em; line-height: 1.1;
}
.sb-brand-sub {
    font-size: 0.7rem; color: var(--text-dim); margin-top: 2px;
}

.sb-newchat {
    margin: 0 0 12px;
}

.sb-divider {
    height: 1px; background: var(--border-muted);
    margin: 10px 0;
}

.sb-label {
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.05em;
    text-transform: uppercase; color: var(--text-dim);
    margin: 4px 8px 6px; padding: 0;
}

/* Conversations list */
.sb-convos { display: flex; flex-direction: column; gap: 1px; }
.sb-convo-item {
    display: flex; align-items: center; gap: 8px;
    padding: 7px 10px; font-size: 0.84rem; font-weight: 400;
    color: var(--text-muted); border-radius: var(--radius-sm);
    cursor: pointer; transition: background 0.1s, color 0.1s;
    white-space: nowrap; overflow: hidden;
}
.sb-convo-item:hover { background: var(--bg-hover); color: var(--text); }
.sb-convo-item.active {
    background: var(--bg-hover); color: var(--text);
}
.sb-convo-icon {
    font-size: 0.85rem; opacity: 0.7; flex-shrink: 0;
    width: 14px; text-align: center;
}
.sb-convo-text {
    overflow: hidden; text-overflow: ellipsis;
}

/* Nav at bottom */
.sb-nav { display: flex; flex-direction: column; gap: 1px; }
.sb-nav-item {
    display: flex; align-items: center; gap: 10px;
    padding: 7px 10px; font-size: 0.84rem; font-weight: 500;
    color: var(--text-muted); border-radius: var(--radius-sm);
    cursor: pointer; transition: background 0.1s, color 0.1s;
}
.sb-nav-item:hover { background: var(--bg-hover); color: var(--text); }
.sb-nav-item.active { background: var(--bg-hover); color: var(--text); }
.sb-nav-icon {
    font-size: 0.9rem; width: 16px; text-align: center;
    opacity: 0.85;
}

/* Status footer in sidebar */
.sb-status {
    display: flex; align-items: center; gap: 8px;
    padding: 7px 10px; margin: 0 4px;
    font-size: 0.76rem; color: var(--text-muted);
    border-radius: var(--radius-sm);
}
.sb-status-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--success); flex-shrink: 0;
    box-shadow: 0 0 0 2px rgba(63,185,80,0.18);
}
.sb-status-dot.offline {
    background: var(--error);
    box-shadow: 0 0 0 2px rgba(248,81,73,0.18);
}

.sb-session {
    padding: 7px 10px; margin: 0 4px;
    font-size: 0.68rem; color: var(--text-dim);
    font-family: 'JetBrains Mono', monospace;
    word-break: break-all; line-height: 1.4;
    background: var(--bg); border: 1px solid var(--border-muted);
    border-radius: var(--radius-sm);
}

/* ═══════════════════════ TOP BAR ═══════════════════════ */
.topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 0 18px;
    border-bottom: 1px solid var(--border-muted);
    margin-bottom: 28px;
}
.topbar-title {
    font-size: 0.95rem; font-weight: 600; color: var(--text);
    letter-spacing: -0.01em;
    display: flex; align-items: center; gap: 10px;
}
.topbar-spark {
    background: var(--copilot-grad);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 1.15rem;
}
.topbar-meta {
    display: flex; gap: 6px;
}
.topbar-pill {
    padding: 4px 10px; border-radius: 999px;
    background: var(--bg-elev-1); border: 1px solid var(--border-muted);
    font-size: 0.72rem; color: var(--text-muted); font-weight: 500;
    font-family: 'JetBrains Mono', monospace;
}

/* ═══════════════════════ EMPTY HERO (Copilot style) ═══════════════════════ */
.hero {
    text-align: center; padding: 56px 0 40px;
}
.hero-icon {
    width: 56px; height: 56px; margin: 0 auto 24px;
    border-radius: 16px; display: grid; place-items: center;
    background: var(--copilot-grad);
    font-size: 1.7rem; color: white;
    box-shadow:
        0 0 0 1px rgba(255,255,255,0.06) inset,
        0 12px 40px rgba(163,113,247,0.25),
        0 4px 16px rgba(88,166,255,0.15);
}
.hero-title {
    font-size: 2rem; font-weight: 700; letter-spacing: -0.03em;
    color: var(--text); margin-bottom: 10px;
    line-height: 1.15;
}
.hero-title .grad {
    background: var(--copilot-grad);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-size: 0.95rem; color: var(--text-muted);
    max-width: 480px; margin: 0 auto; line-height: 1.55;
}

/* Suggestion cards (Copilot style) */
.suggest-grid {
    display: grid; grid-template-columns: repeat(2, 1fr);
    gap: 10px; margin-bottom: 40px;
    max-width: 760px; margin-left: auto; margin-right: auto;
}
.suggest-card {
    padding: 14px 16px; text-align: left;
    background: var(--bg-elev-1);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    cursor: pointer; transition: all 0.15s;
}
.suggest-card:hover {
    background: var(--bg-elev-2);
    border-color: var(--border-strong);
    transform: translateY(-1px);
}
.suggest-card-label {
    font-size: 0.7rem; font-weight: 600;
    background: var(--copilot-grad);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-transform: uppercase; letter-spacing: 0.05em;
    margin-bottom: 4px;
}
.suggest-card-text {
    font-size: 0.88rem; color: var(--text); line-height: 1.5;
    font-weight: 400;
}

/* ═══════════════════════ MESSAGES (Copilot thread style) ═══════════════════════ */
.thread { display: flex; flex-direction: column; gap: 28px; padding: 8px 0 16px; }

.msg {
    display: flex; gap: 14px; align-items: flex-start;
}

.msg-avatar {
    width: 28px; height: 28px; border-radius: 8px;
    display: grid; place-items: center; flex-shrink: 0;
    font-size: 0.78rem; font-weight: 600;
    margin-top: 2px;
}
.msg-avatar.user-av {
    background: var(--bg-elev-2);
    border: 1px solid var(--border);
    color: var(--text);
}
.msg-avatar.ai-av {
    background: var(--copilot-grad);
    color: white;
    box-shadow:
        0 0 0 1px rgba(255,255,255,0.06) inset,
        0 2px 8px rgba(163,113,247,0.3);
}

.msg-body { flex: 1; min-width: 0; }

.msg-name {
    font-size: 0.82rem; font-weight: 600;
    color: var(--text); margin-bottom: 6px;
    line-height: 1.3;
}
.msg-name.ai {
    background: var(--copilot-grad);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.msg-content {
    font-size: 0.93rem; line-height: 1.7; color: var(--text);
    word-wrap: break-word;
}
.msg-content p { margin: 0 0 10px; }
.msg-content code {
    background: var(--bg-elev-2); padding: 1px 6px;
    border-radius: 4px; font-family: 'JetBrains Mono', monospace;
    font-size: 0.85em; color: var(--copilot-1);
}

/* Source chips under AI reply */
.src-strip {
    display: flex; flex-wrap: wrap; gap: 6px;
    margin-top: 14px; padding-top: 12px;
    border-top: 1px solid var(--border-muted);
}
.src-strip-label {
    font-size: 0.7rem; color: var(--text-dim);
    width: 100%; margin-bottom: 4px;
    text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;
}
.src-chip {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 10px; background: var(--bg-elev-1);
    border: 1px solid var(--border); border-radius: 999px;
    font-size: 0.75rem; color: var(--text-muted); cursor: pointer;
    transition: border-color 0.1s, color 0.1s;
}
.src-chip:hover {
    border-color: var(--copilot-1); color: var(--text);
}
.src-chip-num {
    color: var(--copilot-1); font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}

/* Source details */
.source-list { display: flex; flex-direction: column; gap: 6px; margin-top: 10px; }
.source-item {
    padding: 10px 12px;
    background: var(--bg-elev-1);
    border: 1px solid var(--border); border-radius: var(--radius-md);
    font-size: 0.83rem;
}
.source-meta {
    color: var(--text-dim); font-size: 0.7rem; margin-bottom: 6px;
    font-family: 'JetBrains Mono', monospace;
    display: flex; gap: 10px; flex-wrap: wrap;
}
.source-meta span:first-child {
    background: var(--copilot-grad);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 600;
}
.source-excerpt { color: var(--text-muted); line-height: 1.55; }

details > summary { list-style: none; cursor: pointer; user-select: none; }
details > summary::-webkit-details-marker { display: none; }

/* Thinking */
.thinking {
    display: flex; align-items: center; gap: 12px;
    padding: 12px 14px; margin: 12px 0 16px;
    background: var(--bg-elev-1); border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    font-size: 0.85rem; color: var(--text-muted);
}
.thinking-spark {
    width: 18px; height: 18px; border-radius: 5px;
    background: var(--copilot-grad);
    display: grid; place-items: center;
    color: white; font-size: 0.7rem;
    animation: spark-pulse 1.6s ease-in-out infinite;
}
@keyframes spark-pulse {
    0%, 100% { opacity: 0.6; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.08); box-shadow: 0 0 12px rgba(163,113,247,0.5); }
}
.thinking-dots { display: inline-flex; gap: 3px; margin-left: 2px; }
.thinking-dots span {
    width: 4px; height: 4px; border-radius: 50%;
    background: var(--copilot-1);
    animation: blink 1.4s infinite ease-in-out both;
}
.thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
.thinking-dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes blink {
    0%, 80%, 100% { opacity: 0.2; }
    40% { opacity: 1; }
}

/* ═══════════════════════ CHAT INPUT (Copilot style) ═══════════════════════ */
div[data-testid="stChatInput"] {
    background: linear-gradient(180deg, transparent, var(--bg) 30%) !important;
    padding: 24px 0 16px !important;
}
div[data-testid="stChatInput"] > div {
    background: var(--bg-elev-1) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3) !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
div[data-testid="stChatInput"] > div:focus-within {
    border-color: var(--copilot-2) !important;
    box-shadow:
        0 0 0 3px rgba(137,87,229,0.15),
        0 8px 24px rgba(0,0,0,0.3) !important;
}
div[data-testid="stChatInput"] textarea {
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.92rem !important;
    line-height: 1.5 !important;
}
div[data-testid="stChatInput"] textarea::placeholder {
    color: var(--text-dim) !important;
}
div[data-testid="stChatInput"] button {
    background: var(--copilot-grad) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 8px rgba(163,113,247,0.3) !important;
    transition: transform 0.1s, box-shadow 0.15s !important;
}
div[data-testid="stChatInput"] button:hover {
    transform: scale(1.05) !important;
    box-shadow: 0 4px 14px rgba(163,113,247,0.45) !important;
}
div[data-testid="stChatInput"] button svg { fill: white !important; }

/* ═══════════════════════ BUTTONS ═══════════════════════ */
.stButton > button {
    background: var(--bg-elev-1) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text) !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.84rem !important;
    padding: 6px 12px !important;
    transition: background 0.1s, border-color 0.1s !important;
    box-shadow: none !important;
}
.stButton > button:hover {
    background: var(--bg-hover) !important;
    border-color: var(--border-strong) !important;
    transform: none !important;
}
.stButton > button:focus {
    box-shadow: 0 0 0 3px var(--copilot-soft) !important;
    border-color: var(--copilot-2) !important;
}

/* New chat button (primary Copilot style) */
.stButton.primary > button,
.stButton > button[kind="primary"] {
    background: var(--copilot-grad) !important;
    border: 1px solid transparent !important;
    color: white !important;
    box-shadow: 0 2px 8px rgba(163,113,247,0.2) !important;
}

/* ═══════════════════════ SLIDER ═══════════════════════ */
div[data-testid="stSlider"] label {
    font-size: 0.78rem !important;
    color: var(--text-muted) !important;
}
div[data-testid="stSlider"] div[role="slider"] {
    background: white !important;
    border: 2px solid var(--copilot-2) !important;
    box-shadow: 0 0 0 3px var(--copilot-soft) !important;
}
div[data-testid="stSlider"] > div > div > div > div {
    background: var(--copilot-grad) !important;
}

/* ═══════════════════════ EXPANDER ═══════════════════════ */
div[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    background: var(--bg-elev-1) !important;
    margin-top: 6px !important;
}
div[data-testid="stExpander"] summary {
    font-size: 0.82rem !important;
    color: var(--text-muted) !important;
}
div[data-testid="stExpander"] textarea {
    background: var(--bg) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
}

/* ═══════════════════════ SCROLLBAR ═══════════════════════ */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: var(--border); border-radius: 99px;
    border: 2px solid var(--bg);
}
::-webkit-scrollbar-thumb:hover { background: var(--border-strong); }

/* ═══════════════════════ RESPONSIVE ═══════════════════════ */
@media (max-width: 900px) {
    .suggest-grid { grid-template-columns: 1fr; }
    .topbar-meta { display: none; }
    .block-container { padding: 1rem 1rem 8rem; }
    .hero { padding: 32px 0 24px; }
    .hero-title { font-size: 1.6rem; }
}
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "top_k" not in st.session_state:
    st.session_state.top_k = 5
if "api_ok" not in st.session_state:
    st.session_state.api_ok = None

def check_api():
    try:
        r = requests.get("http://127.0.0.1:8000/", timeout=2)
        return r.status_code < 500
    except Exception:
        return False

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
        <div class="sb-brand-mark">✦</div>
        <div>
            <div class="sb-brand-text">Xeer AI</div>
            <div class="sb-brand-sub">Powered by RAG</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # New chat button (primary)
    st.markdown('<div class="sb-newchat">', unsafe_allow_html=True)
    if st.button("✦  Nouvelle conversation", use_container_width=True, type="primary"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Recent conversations
    st.markdown('<div class="sb-label">Récent</div>', unsafe_allow_html=True)
    recents = [
        ("💬", "Waa maxay Xeer Ciise?"),
        ("💬", "Rôle dans la société"),
        ("💬", "Règles de compensation"),
        ("💬", "Origines historiques"),
    ]
    st.markdown('<div class="sb-convos">', unsafe_allow_html=True)
    for icon, q in recents:
        st.markdown(
            f'<div class="sb-convo-item"><span class="sb-convo-icon">{icon}</span>'
            f'<span class="sb-convo-text">{q}</span></div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

    # Navigation
    st.markdown('<div class="sb-label">Espace</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="sb-nav">
        <div class="sb-nav-item active"><span class="sb-nav-icon">💬</span>Chat</div>
        <div class="sb-nav-item"><span class="sb-nav-icon">📚</span>Sources</div>
        <div class="sb-nav-item"><span class="sb-nav-icon">🧠</span>Mémoire</div>
        <div class="sb-nav-item"><span class="sb-nav-icon">⚙️</span>Paramètres</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-label">Sources par réponse</div>', unsafe_allow_html=True)
    st.session_state.top_k = st.slider(
        "", min_value=3, max_value=8, value=st.session_state.top_k,
        label_visibility="collapsed"
    )

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

    # Status
    if st.session_state.api_ok is None:
        st.session_state.api_ok = check_api()
    dot_class = "sb-status-dot" if st.session_state.api_ok else "sb-status-dot offline"
    status_text = "Backend en ligne" if st.session_state.api_ok else "Backend hors ligne"
    st.markdown(f"""
    <div class="sb-status">
        <div class="{dot_class}"></div>
        <span>{status_text}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)
    st.markdown(f'<div class="sb-session">{st.session_state.session_id[:20]}…</div>', unsafe_allow_html=True)

# ── TOPBAR ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="topbar">
    <div class="topbar-title">
        <span class="topbar-spark">✦</span>
        Xeer AI Chat
    </div>
    <div class="topbar-meta">
        <div class="topbar-pill">{len(st.session_state.messages)} msg</div>
        <div class="topbar-pill">top-k {st.session_state.top_k}</div>
        <div class="topbar-pill">SO · FR · EN</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── EMPTY STATE (Copilot-style hero) ──────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="hero">
        <div class="hero-icon">✦</div>
        <div class="hero-title">Bienvenue sur <span class="grad">Xeer AI</span></div>
        <div class="hero-sub">
            Posez n'importe quelle question sur le droit coutumier somalien.
            Réponses sourcées, multilingues et instantanées.
        </div>
    </div>
    <div class="suggest-grid">
        <div class="suggest-card">
            <div class="suggest-card-label">⚖️ Concept</div>
            <div class="suggest-card-text">Waa maxay Xeer Ciise iyo taariikhdiisa?</div>
        </div>
        <div class="suggest-card">
            <div class="suggest-card-label">📚 Doctrine</div>
            <div class="suggest-card-text">Explique le rôle du Xeer dans la résolution des conflits</div>
        </div>
        <div class="suggest-card">
            <div class="suggest-card-label">🔍 Analyse</div>
            <div class="suggest-card-text">Quelles sont les règles de compensation (diya) ?</div>
        </div>
        <div class="suggest-card">
            <div class="suggest-card-label">🌍 Culture</div>
            <div class="suggest-card-text">How does Xeer Ciise relate to Somali identity?</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── THREAD ────────────────────────────────────────────────────────────────────
if st.session_state.messages:
    st.markdown('<div class="thread">', unsafe_allow_html=True)

    for idx, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="msg">
                <div class="msg-avatar user-av">U</div>
                <div class="msg-body">
                    <div class="msg-name">Vous</div>
                    <div class="msg-content">{msg["content"]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            sources = msg.get("sources", [])
            chips_html = ""
            if sources:
                chips_html = '<div class="src-strip">'
                chips_html += '<div class="src-strip-label">Sources</div>'
                for i, src in enumerate(sources, 1):
                    page = src.get('page', '?')
                    chips_html += (
                        f'<div class="src-chip">'
                        f'<span class="src-chip-num">[{i}]</span> p.{page}'
                        f'</div>'
                    )
                chips_html += '</div>'

            st.markdown(f"""
            <div class="msg">
                <div class="msg-avatar ai-av">✦</div>
                <div class="msg-body">
                    <div class="msg-name ai">Xeer AI</div>
                    <div class="msg-content">{msg["content"]}</div>
                    {chips_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Expander pour détails sources + export
            if sources:
                with st.expander(f"📖 Voir les {len(sources)} extraits sourcés"):
                    src_html = '<div class="source-list">'
                    for i, src in enumerate(sources, 1):
                        src_html += f"""
                        <div class="source-item">
                            <div class="source-meta">
                                <span>[{i}]</span>
                                <span>page {src.get('page','N/A')}</span>
                                <span>chunk {src.get('chunk_index','N/A')}</span>
                                <span>score {src.get('score','N/A')}</span>
                            </div>
                            <div class="source-excerpt">{src.get('excerpt','')}</div>
                        </div>"""
                    src_html += '</div>'
                    st.markdown(src_html, unsafe_allow_html=True)

            with st.expander("⬇️ Exporter la réponse"):
                st.text_area("", value=msg["content"], height=120, key=f"copy_{idx}",
                             label_visibility="collapsed")
                st.download_button(
                    "Télécharger en .txt",
                    data=msg["content"],
                    file_name=f"xeer_ai_{idx}.txt",
                    mime="text/plain",
                    key=f"dl_{idx}",
                )

    st.markdown('</div>', unsafe_allow_html=True)

# ── CHAT INPUT ────────────────────────────────────────────────────────────────
prompt = st.chat_input("Posez votre question à Xeer AI…")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# ── API CALL ──────────────────────────────────────────────────────────────────
if st.session_state.messages:
    last = st.session_state.messages[-1]
    needs_reply = (
        last["role"] == "user" and
        (len(st.session_state.messages) == 1 or st.session_state.messages[-2]["role"] != "assistant")
    )

    if needs_reply:
        st.markdown("""
        <div class="thinking">
            <div class="thinking-spark">✦</div>
            <span>Xeer AI réfléchit</span>
            <div class="thinking-dots"><span></span><span></span><span></span></div>
        </div>
        """, unsafe_allow_html=True)
        try:
            resp = requests.post(
                API_URL,
                json={
                    "question": last["content"],
                    "top_k": st.session_state.top_k,
                    "session_id": st.session_state.session_id,
                },
                timeout=90,
            )
            resp.raise_for_status()
            data = resp.json()
            st.session_state.api_ok = True
            st.session_state.messages.append({
                "role": "assistant",
                "content": data.get("answer", "Aucune réponse."),
                "sources": data.get("sources", []),
            })
        except requests.exceptions.ConnectionError:
            st.session_state.api_ok = False
            st.session_state.messages.append({
                "role": "assistant",
                "content": "**Connexion impossible.** Veuillez démarrer le backend FastAPI (`uvicorn app.main:app`) et réessayer.",
                "sources": [],
            })
        except requests.exceptions.Timeout:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "**Délai dépassé.** La requête a pris trop de temps. Réessayez dans un instant.",
                "sources": [],
            })
        except Exception as e:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"**Erreur inattendue :** `{e}`",
                "sources": [],
            })
        st.rerun()
