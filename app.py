import streamlit as st
import requests
from io import BytesIO
from PIL import Image
import urllib.parse
import base64
import PyPDF2
import io

st.set_page_config(page_title="Aura AI", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; }
html, body, .stApp { background: #07070f !important; }
.stApp { font-family: 'DM Sans', sans-serif; }
[data-testid="stSidebar"] { background: #0c0c18 !important; border-right: 1px solid rgba(255,255,255,0.05) !important; }
[data-testid="stSidebar"] > div { padding-top: 0 !important; }
div[data-testid="stToolbar"] { display: none; }
.stDeployButton { display: none; }
#MainMenu { display: none; }
footer { display: none; }
header { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
.stButton > button { background: #6d28d9 !important; color: #fff !important; border: none !important; border-radius: 10px !important; font-weight: 500 !important; padding: 10px 20px !important; }
.stButton > button:hover { background: #7c3aed !important; }
.stTextInput input, .stTextArea textarea { background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.08) !important; color: #fff !important; border-radius: 10px !important; }
.stSelectbox label, .stTextArea label, .stTextInput label, .stSlider label, .stFileUploader label { color: rgba(255,255,255,0.5) !important; font-size: 12px !important; }
.stSuccess { background: rgba(16,185,129,0.1) !important; border: 1px solid rgba(16,185,129,0.2) !important; border-radius: 10px !important; }
.stWarning { background: rgba(245,158,11,0.1) !important; border: 1px solid rgba(245,158,11,0.2) !important; border-radius: 10px !important; }
.stError { background: rgba(239,68,68,0.1) !important; border: 1px solid rgba(239,68,68,0.2) !important; border-radius: 10px !important; }
.stInfo { background: rgba(109,40,217,0.1) !important; border: 1px solid rgba(109,40,217,0.2) !important; border-radius: 10px !important; }
.stMarkdown p, .stMarkdown li { color: rgba(255,255,255,0.75) !important; font-size: 13px !important; }
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3 { color: #fff !important; font-family: 'Syne', sans-serif !important; }
.stMarkdown code { background: rgba(109,40,217,0.15) !important; color: #a78bfa !important; border-radius: 4px !important; }
.stMarkdown pre { background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 10px !important; }
.stChatInput textarea { background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.08) !important; color: #fff !important; border-radius: 12px !important; }
div[data-testid="metric-container"] { background: #0c0c18 !important; border: 1px solid rgba(255,255,255,0.06) !important; border-radius: 12px !important; padding: 14px !important; }
div[data-testid="metric-container"] label { color: rgba(255,255,255,0.35) !important; font-size: 11px !important; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #fff !important; }
hr { border-color: rgba(255,255,255,0.06) !important; }
</style>
""", unsafe_allow_html=True)

/* ── RESET & BASE ── */
* { box-sizing: border-box; }
html, body, .stApp { background: #07070f !important; }
.stApp { font-family: 'DM Sans', sans-serif; }
[data-testid="stSidebar"] {
    background: #0c0c18 !important;
    border-right: 1px solid rgba(255,255,255,0.05) !important;
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }
.stChatMessage { background: transparent !important; border: none !important; }
.stChatMessage [data-testid="stChatMessageContent"] { background: transparent !important; }
div[data-testid="stToolbar"] { display: none; }
.stDeployButton { display: none; }
#MainMenu { display: none; }
footer { display: none; }
header { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] .block-container { padding: 0 !important; }

/* ── SIDEBAR LOGO ── */
.logo-wrap {
    padding: 28px 20px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    margin-bottom: 8px;
}
.logo-mark {
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.5px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.logo-dot {
    width: 8px; height: 8px;
    background: #6d28d9;
    border-radius: 50%;
    display: inline-block;
}
.logo-sub {
    font-size: 11px;
    color: rgba(255,255,255,0.25);
    margin-top: 3px;
    letter-spacing: 0.5px;
}

/* ── NAV ── */
.nav-section {
    padding: 16px 20px 6px;
    font-size: 9px;
    font-weight: 600;
    color: rgba(255,255,255,0.2);
    text-transform: uppercase;
    letter-spacing: 1.5px;
}
.nav-link {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 12px;
    margin: 1px 8px;
    border-radius: 8px;
    font-size: 13px;
    color: rgba(255,255,255,0.35);
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
}
.nav-link:hover { background: rgba(255,255,255,0.04); color: rgba(255,255,255,0.7); }
.nav-link.active {
    background: rgba(109,40,217,0.15);
    color: #a78bfa;
    border: 1px solid rgba(109,40,217,0.2);
}
.nav-icon { font-size: 15px; width: 18px; text-align: center; }

/* ── MAIN HEADER ── */
.main-header {
    background: #0c0c18;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    padding: 16px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.header-icon {
    width: 36px; height: 36px;
    background: rgba(109,40,217,0.15);
    border: 1px solid rgba(109,40,217,0.2);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
}
.header-title {
    font-family: 'Syne', sans-serif;
    font-size: 16px;
    font-weight: 600;
    color: #fff;
}
.header-sub { font-size: 11px; color: rgba(255,255,255,0.3); margin-top: 1px; }
.header-pills { display: flex; gap: 6px; flex-wrap: wrap; }
.hpill {
    display: flex; align-items: center; gap: 5px;
    padding: 5px 11px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    font-size: 11px;
    color: rgba(255,255,255,0.35);
}

/* ── CONTENT ── */
.main-content { padding: 20px 28px; background: #07070f; min-height: calc(100vh - 70px); }

/* ── STAT CARDS ── */
.stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 16px;
}
.stat-card {
    background: #0c0c18;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 14px 16px;
}
.stat-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.stat-badge {
    width: 28px; height: 28px;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px;
}
.sb-p { background: rgba(109,40,217,0.15); }
.sb-b { background: rgba(59,130,246,0.15); }
.sb-g { background: rgba(16,185,129,0.15); }
.sb-a { background: rgba(245,158,11,0.15); }
.stat-num {
    font-family: 'Syne', sans-serif;
    font-size: 24px;
    font-weight: 700;
    color: #fff;
}
.stat-lbl { font-size: 11px; color: rgba(255,255,255,0.3); margin-top: 2px; }

/* ── MODEL SELECTOR ── */
.model-row { display: flex; gap: 6px; margin-bottom: 16px; flex-wrap: wrap; }
.model-chip {
    padding: 6px 12px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    font-size: 11px;
    color: rgba(255,255,255,0.3);
    cursor: pointer;
}
.model-chip.sel {
    background: rgba(109,40,217,0.15);
    border-color: rgba(109,40,217,0.3);
    color: #a78bfa;
}

/* ── CHAT CONTAINER ── */
.chat-container {
    background: #0c0c18;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    overflow: hidden;
}
.chat-top {
    padding: 12px 18px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.online-row { display: flex; align-items: center; gap: 8px; }
.online-dot {
    width: 7px; height: 7px;
    background: #10b981;
    border-radius: 50%;
    animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
.chat-title { font-size: 13px; font-weight: 500; color: #fff; }
.chat-sub { font-size: 10px; color: rgba(255,255,255,0.25); }

/* ── STREAMLIT OVERRIDES ── */
.stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: #fff !important;
    border-radius: 10px !important;
}
.stButton > button {
    background: #6d28d9 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 10px 20px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #7c3aed !important;
    transform: translateY(-1px) !important;
}
.stSelectbox label, .stTextArea label, .stTextInput label,
.stSlider label, .stFileUploader label {
    color: rgba(255,255,255,0.5) !important;
    font-size: 12px !important;
}
.stSlider [data-baseweb="slider"] div { background: #6d28d9 !important; }
.stSuccess { background: rgba(16,185,129,0.1) !important; border: 1px solid rgba(16,185,129,0.2) !important; border-radius: 10px !important; }
.stWarning { background: rgba(245,158,11,0.1) !important; border: 1px solid rgba(245,158,11,0.2) !important; border-radius: 10px !important; }
.stError { background: rgba(239,68,68,0.1) !important; border: 1px solid rgba(239,68,68,0.2) !important; border-radius: 10px !important; }
.stInfo { background: rgba(109,40,217,0.1) !important; border: 1px solid rgba(109,40,217,0.2) !important; border-radius: 10px !important; }
.stChatInput textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: #fff !important;
    border-radius: 12px !important;
}
.stChatInput > div {
    background: #0c0c18 !important;
    border-top: 1px solid rgba(255,255,255,0.05) !important;
    padding: 12px 18px !important;
}
[data-testid="stChatMessageAvatarAssistant"] { background: rgba(109,40,217,0.2) !important; }
[data-testid="stChatMessageAvatarUser"] { background: rgba(59,130,246,0.2) !important; }
.stMarkdown p, .stMarkdown li { color: rgba(255,255,255,0.75) !important; font-size: 13px !important; line-height: 1.7 !important; }
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3 { color: #fff !important; font-family: 'Syne', sans-serif !important; }
.stMarkdown code { background: rgba(109,40,217,0.15) !important; color: #a78bfa !important; border-radius: 4px !important; padding: 1px 6px !important; }
.stMarkdown pre { background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 10px !important; }
hr { border-color: rgba(255,255,255,0.06) !important; }
.stFileUploader {
    background: rgba(255,255,255,0.03) !important;
    border: 1px dashed rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    padding: 12px !important;
}
.stRadio label { color: rgba(255,255,255,0.6) !important; }
.stCheckbox label { color: rgba(255,255,255,0.6) !important; }
div[data-testid="column"] { gap: 10px; }
.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid rgba(255,255,255,0.06) !important; }
.stTabs [data-baseweb="tab"] { color: rgba(255,255,255,0.4) !important; background: transparent !important; }
.stTabs [aria-selected="true"] { color: #a78bfa !important; border-bottom: 2px solid #6d28d9 !important; }
.stProgress > div > div { background: #6d28d9 !important; border-radius: 10px !important; }
.stProgress > div { background: rgba(255,255,255,0.06) !important; border-radius: 10px !important; }
div[data-testid="metric-container"] {
    background: #0c0c18 !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 12px !important;
    padding: 14px !important;
}
div[data-testid="metric-container"] label { color: rgba(255,255,255,0.35) !important; font-size: 11px !important; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #fff !important; font-family: 'Syne', sans-serif !important; }
</style>
""", unsafe_allow_html=True)

MODELS = {
    "✦ Llama 3.3 70B": "llama-3.3-70b-versatile",
    "⚡ Llama 3.1 8B": "llama-3.1-8b-instant",
    "◈ Mixtral 8x7B": "mixtral-8x7b-32768",
    "◉ Gemma 2 9B": "gemma2-9b-it",
    "▲ DeepSeek R1": "deepseek-r1-distill-llama-70b",
}

LANGUAGES = {
    "English": "Respond in English.",
    "Hindi": "Hamesha Hindi mein jawab do.",
    "Hinglish": "Hinglish mein jawab do.",
    "Marathi": "Marathi madhe uttar dya.",
}

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("""
    <div class='logo-wrap'>
        <div class='logo-mark'><span class='logo-dot'></span> Aura AI</div>
        <div class='logo-sub'>Intelligent Assistant Suite</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='nav-section'>Features</div>", unsafe_allow_html=True)
    feature = st.selectbox("", [
        "✦ AI Chat",
        "◈ Image Generator",
        "◉ Image Analyzer",
        "▲ PDF Chat",
        "⬡ Weather",
        "⟨⟩ Code Assistant",
    ], label_visibility="collapsed")

    if any(x in feature for x in ["Chat", "Code", "PDF"]):
        st.markdown("<div class='nav-section' style='margin-top:16px;'>Model</div>", unsafe_allow_html=True)
        selected_model_name = st.selectbox("", list(MODELS.keys()), label_visibility="collapsed")
        selected_model = MODELS[selected_model_name]

        st.markdown("<div class='nav-section'>Language</div>", unsafe_allow_html=True)
        selected_lang = st.selectbox("", list(LANGUAGES.keys()), label_visibility="collapsed")

        temperature = st.slider("Creativity", 0.1, 1.0, 0.7)
        max_tokens = st.slider("Response Length", 100, 4000, 1000)

        if st.button("⟳ Clear Session"):
            for k in ["messages", "pdf_text"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

        if "messages" in st.session_state and len(st.session_state.messages) > 0:
            chat_text = "\n\n".join([
                f"{'You' if m['role']=='user' else 'Aura'}: {m['content']}"
                for m in st.session_state.messages
            ])
            st.download_button("↓ Export Chat", chat_text, file_name="aura_chat.txt", mime="text/plain")

    st.markdown("<div style='position:absolute;bottom:20px;left:0;right:0;padding:0 8px;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background:rgba(109,40,217,0.1);border:1px solid rgba(109,40,217,0.2);border-radius:10px;padding:12px 14px;margin:8px;'>
        <div style='font-size:11px;font-weight:600;color:#a78bfa;font-family:Syne,sans-serif;'>Aura Pro</div>
        <div style='font-size:10px;color:rgba(255,255,255,0.3);margin-top:2px;'>Unlimited AI · All features</div>
        <div style='margin-top:8px;font-size:11px;color:rgba(255,255,255,0.5);'>Built by Rupal Darode ✦</div>
    </div>
    """, unsafe_allow_html=True)


# ── GROQ HELPER ──
def call_groq(messages, model, temperature=0.7, max_tokens=1000):
    try:
        key = st.secrets["GROQ_API_KEY"]
    except:
        return "❌ GROQ_API_KEY not found in secrets."
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens},
            timeout=30
        )
        data = res.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"].strip()
        elif "error" in data:
            return f"❌ {data['error']['message']}"
        return "❌ Unexpected error."
    except Exception as e:
        return f"❌ {str(e)}"


# ── HEADER RENDERER ──
def render_header(icon, title, subtitle, pills=[]):
    pills_html = "".join([f"<div class='hpill'>{p}</div>" for p in pills])
    st.markdown(f"""
    <div class='main-header'>
        <div class='header-left'>
            <div class='header-icon'>{icon}</div>
            <div>
                <div class='header-title'>{title}</div>
                <div class='header-sub'>{subtitle}</div>
            </div>
        </div>
        <div class='header-pills'>{pills_html}</div>
    </div>
    <div class='main-content'>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════
# AI CHAT
# ══════════════════════════════════════════
if "Chat" in feature:
    render_header("✦", "AI Chat", "Multi-model intelligent assistant",
                  [selected_model_name, selected_lang, "◈ Attach Image"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Session Messages", len(st.session_state.get("messages", [])))
    col2.metric("Model", "70B" if "70B" in selected_model_name else "8B" if "8B" in selected_model_name else "MX")
    col3.metric("Language", selected_lang[:3].upper())
    col4.metric("Creativity", f"{int(temperature*100)}%")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    uploaded_img = st.file_uploader("Attach image (optional)", type=["png","jpg","jpeg","webp"])
    img_note = ""
    if uploaded_img:
        img = Image.open(uploaded_img)
        st.image(img, width=250)
        img_note = " [User has attached an image — acknowledge it.]"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.markdown("""
    <div style='background:#0c0c18;border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:12px 18px 4px;margin-bottom:8px;'>
    <div style='display:flex;align-items:center;gap:8px;padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,0.05);margin-bottom:10px;'>
    <div style='width:7px;height:7px;background:#10b981;border-radius:50%;'></div>
    <span style='font-size:12px;font-weight:500;color:#fff;'>Aura Assistant</span>
    <span style='font-size:10px;color:rgba(255,255,255,0.25);'>· Online · {}</span>
    </div>
    """.format(selected_model_name), unsafe_allow_html=True)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    st.markdown("</div>", unsafe_allow_html=True)

    prompt = st.chat_input("Message Aura...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        system = f"You are Aura, a helpful AI assistant. {LANGUAGES[selected_lang]}{img_note}"
        all_msgs = [{"role": "system", "content": system}] + [
            {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
        ]
        with st.chat_message("assistant"):
            with st.spinner(""):
                reply = call_groq(all_msgs, selected_model, temperature, max_tokens)
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})


# ══════════════════════════════════════════
# IMAGE GENERATOR
# ══════════════════════════════════════════
elif "Image" in feature and "Gen" in feature or "◈" in feature:
    render_header("◈", "Image Generator", "Text to image · Powered by Pollinations AI", ["Free · No API Key"])

    STYLES = {
        "None": "", "Photorealistic": ", ultra realistic, 8k, cinematic",
        "Anime": ", anime style, Studio Ghibli, vibrant",
        "Oil Painting": ", oil painting, museum quality, detailed",
        "Cyberpunk": ", cyberpunk, neon lights, blade runner aesthetic",
        "Watercolor": ", watercolor, soft artistic strokes",
        "Minimalist": ", minimalist, clean lines, white background",
        "Dark Fantasy": ", dark fantasy, dramatic lighting, cinematic",
    }

    prompt = st.text_area("Describe your image", height=100,
                           placeholder="A serene Japanese garden at sunset, cherry blossoms falling...")
    col1, col2, col3 = st.columns(3)
    with col1: style = st.selectbox("Style Preset", list(STYLES.keys()))
    with col2: width = st.slider("Width", 256, 1024, 768, step=64)
    with col3: height = st.slider("Height", 256, 1024, 512, step=64)

    if st.button("✦ Generate Image", use_container_width=True):
        if prompt.strip():
            with st.spinner("Creating your image..."):
                try:
                    full = prompt + STYLES[style]
                    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(full)}?width={width}&height={height}&nologo=true"
                    res = requests.get(url, timeout=60)
                    img = Image.open(BytesIO(res.content))
                    st.image(img, use_container_width=True)
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    st.download_button("↓ Download Image", buf.getvalue(),
                                       file_name="aura_image.png", mime="image/png", use_container_width=True)
                except Exception as e:
                    st.error(f"Generation failed: {e}")
        else:
            st.warning("Enter a prompt first.")


# ══════════════════════════════════════════
# IMAGE ANALYZER
# ══════════════════════════════════════════
elif "Analyzer" in feature or "◉" in feature:
    render_header("◉", "Image Analyzer", "Upload any image · Ask questions · Get AI insights", ["Gemini Vision"])

    uploaded = st.file_uploader("Upload image", type=["png","jpg","jpeg","webp"])
    if uploaded:
        image = Image.open(uploaded)
        st.image(image, use_container_width=True)

        st.markdown("<div style='display:flex;gap:8px;flex-wrap:wrap;margin:8px 0;'>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        q = ""
        with col1:
            if st.button("Describe", use_container_width=True): q = "Describe this image in detail."
        with col2:
            if st.button("Colors", use_container_width=True): q = "What are the main colors?"
        with col3:
            if st.button("Mood", use_container_width=True): q = "What is the mood of this image?"
        with col4:
            if st.button("Objects", use_container_width=True): q = "List all objects you can see."

        question = st.text_input("Or ask your own question", value=q, placeholder="What is happening in this image?")

        if st.button("◉ Analyze", use_container_width=True):
            if question.strip():
                try:
                    gemini_key = st.secrets["GEMINI_API_KEY"]
                    buf = BytesIO()
                    image.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode()

                    with st.spinner("Analyzing..."):
                        res = requests.post(
                            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}",
                            json={"contents": [{"parts": [
                                {"inline_data": {"mime_type": "image/png", "data": img_b64}},
                                {"text": question}
                            ]}]},
                            timeout=30
                        )
                        data = res.json()
                        if "candidates" in data:
                            reply = data["candidates"][0]["content"]["parts"][0]["text"]
                            st.success(reply)
                        else:
                            st.error(f"Error: {data}")
                except KeyError:
                    st.error("❌ GEMINI_API_KEY not found. Add it in Streamlit secrets.")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Enter a question.")
    else:
        st.info("Upload an image to get started.")


# ══════════════════════════════════════════
# PDF CHAT
# ══════════════════════════════════════════
elif "PDF" in feature or "▲" in feature:
    render_header("▲", "PDF Chat", "Upload a document · Chat with it instantly", [selected_model_name])

    pdf = st.file_uploader("Upload PDF", type=["pdf"])
    if pdf:
        if "pdf_text" not in st.session_state:
            with st.spinner("Reading PDF..."):
                try:
                    reader = PyPDF2.PdfReader(io.BytesIO(pdf.read()))
                    text = "".join([p.extract_text() + "\n" for p in reader.pages])
                    st.session_state.pdf_text = text[:8000]
                    st.success(f"✦ PDF loaded — {len(reader.pages)} pages")
                except Exception as e:
                    st.error(f"Could not read PDF: {e}")

        if "pdf_text" in st.session_state:
            if "messages" not in st.session_state:
                st.session_state.messages = []
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            prompt = st.chat_input("Ask about your document...")
            if prompt:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                system = f"Answer based on this document only:\n\n{st.session_state.pdf_text}\n\nIf not in document, say so. {LANGUAGES[selected_lang]}"
                all_msgs = [{"role": "system", "content": system}] + [
                    {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
                ]
                with st.chat_message("assistant"):
                    with st.spinner(""):
                        reply = call_groq(all_msgs, selected_model, temperature, max_tokens)
                        st.markdown(reply)
                        st.session_state.messages.append({"role": "assistant", "content": reply})
    else:
        st.info("Upload a PDF to start chatting with it.")
        for k in ["messages", "pdf_text"]:
            if k in st.session_state: del st.session_state[k]


# ══════════════════════════════════════════
# WEATHER
# ══════════════════════════════════════════
elif "Weather" in feature or "⬡" in feature:
    render_header("⬡", "Weather", "Real-time weather for any city · AI-powered tips", ["Open-Meteo · Free"])

    col1, col2 = st.columns([3,1])
    with col1: city = st.text_input("City", placeholder="Nagpur, Mumbai, Delhi, London...")
    with col2: unit = st.selectbox("Unit", ["Celsius", "Fahrenheit"])

    if st.button("⬡ Get Weather", use_container_width=True):
        if city.strip():
            with st.spinner("Fetching weather..."):
                try:
                    geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1", timeout=10).json()
                    if "results" not in geo:
                        st.error("City not found.")
                    else:
                        loc = geo["results"][0]
                        lat, lon = loc["latitude"], loc["longitude"]
                        name = loc.get("name", city)
                        country = loc.get("country", "")
                        unit_param = "celsius" if unit == "Celsius" else "fahrenheit"
                        sym = "°C" if unit == "Celsius" else "°F"
                        w = requests.get(
                            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                            f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code,apparent_temperature"
                            f"&temperature_unit={unit_param}", timeout=10
                        ).json()
                        curr = w["current"]
                        desc = {0:"☀ Clear",1:"🌤 Mainly clear",2:"⛅ Partly cloudy",3:"☁ Overcast",
                                45:"🌫 Foggy",61:"🌧 Rain",63:"🌧 Moderate rain",80:"🌦 Showers",95:"⛈ Thunderstorm"
                               }.get(curr["weather_code"], "🌡 Weather")

                        col1,col2,col3,col4 = st.columns(4)
                        col1.metric("Temperature", f"{curr['temperature_2m']}{sym}", f"Feels {curr['apparent_temperature']}{sym}")
                        col2.metric("Humidity", f"{curr['relative_humidity_2m']}%")
                        col3.metric("Wind", f"{curr['wind_speed_10m']} km/h")
                        col4.metric("Condition", desc)

                        st.success(f"Weather for **{name}, {country}**")
                        with st.spinner("Getting AI tip..."):
                            tip = call_groq([
                                {"role": "system", "content": "You are a helpful weather assistant. Give a 2-line practical tip."},
                                {"role": "user", "content": f"Weather: {curr['temperature_2m']}{sym}, {desc}, humidity {curr['relative_humidity_2m']}% in {name}. What to wear?"}
                            ], "llama-3.1-8b-instant", 0.7, 150)
                            st.info(f"✦ AI Tip: {tip}")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Enter a city name.")


# ══════════════════════════════════════════
# CODE ASSISTANT
# ══════════════════════════════════════════
elif "Code" in feature or "⟨⟩" in feature:
    render_header("⟨⟩", "Code Assistant", "Write · Debug · Explain · Convert · Optimize", [selected_model_name])

    col1, col2 = st.columns(2)
    with col1:
        action = st.selectbox("Action", [
            "✍ Write code", "🐛 Debug code", "📖 Explain code",
            "🔄 Convert language", "⚡ Optimize code", "🧪 Write tests"
        ])
    with col2:
        lang = st.selectbox("Language", ["Python","JavaScript","Java","C++","SQL","HTML/CSS","React","TypeScript","Other"])

    if "Convert" in action:
        target = st.selectbox("Convert to", ["JavaScript","Python","Java","TypeScript","Go","Rust"])
    else:
        target = None

    code_input = st.text_area("Your code or description", height=200,
                               placeholder="Paste your code or describe what you want...")

    if st.button("⟨⟩ Run", use_container_width=True):
        if code_input.strip():
            with st.spinner("Processing..."):
                prompts = {
                    "✍ Write code": f"Write clean, well-commented {lang} code for: {code_input}. Include example usage.",
                    "🐛 Debug code": f"Debug this {lang} code, explain all issues and provide fixed version:\n\n{code_input}",
                    "📖 Explain code": f"Explain this {lang} code step-by-step in simple terms:\n\n{code_input}",
                    "🔄 Convert language": f"Convert this {lang} code to {target}:\n\n{code_input}",
                    "⚡ Optimize code": f"Optimize this {lang} code for better performance:\n\n{code_input}",
                    "🧪 Write tests": f"Write comprehensive unit tests for this {lang} code:\n\n{code_input}",
                }
                reply = call_groq([
                    {"role": "system", "content": "You are an expert programmer. Provide clean, working code with explanations in markdown code blocks."},
                    {"role": "user", "content": prompts[action]}
                ], selected_model, 0.3, max_tokens)
                st.markdown(reply)
                st.download_button("↓ Download", reply, file_name="aura_code.txt", mime="text/plain")
        else:
            st.warning("Enter your code or description.")

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center;padding:20px 0 8px;font-size:11px;color:rgba(255,255,255,0.15);'>
Built with ✦ by Rupal Darode &nbsp;·&nbsp; Aura AI &nbsp;·&nbsp; Powered by Groq + Gemini
</div>
""", unsafe_allow_html=True)
