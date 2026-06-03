"""
╔══════════════════════════════════════════════════════════════════╗
║                        AURA AI  ✦                               ║
║   100% Local · No API Keys · Hugging Face Models                ║
║   Features: Chat · Image Gen · Image Analyze · PDF · Weather    ║
║             Voice-to-Text · Text-to-Voice · Voice-to-Voice      ║
╚══════════════════════════════════════════════════════════════════╝

SETUP:
    pip install -r requirements.txt
    streamlit run app.py

Models auto-download on first use (~2–4 GB total, cached locally).
"""

import streamlit as st
import requests
import urllib.parse
import base64
import io
import os
import json
import tempfile
from datetime import datetime
from io import BytesIO
from PIL import Image

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="Aura AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLOBAL CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap');

:root {
    --bg:        #080c14;
    --bg2:       #0d1220;
    --bg3:       #111827;
    --border:    rgba(99,179,237,0.12);
    --border2:   rgba(99,179,237,0.25);
    --gold:      #f0b429;
    --gold2:     #d69e2e;
    --blue:      #63b3ed;
    --purple:    #9f7aea;
    --green:     #68d391;
    --red:       #fc8181;
    --text:      #e2e8f0;
    --text2:     #94a3b8;
    --text3:     #64748b;
    --radius:    12px;
    --shadow:    0 4px 24px rgba(0,0,0,0.4);
}

* { box-sizing: border-box; margin: 0; padding: 0; }
html, body, .stApp { background: var(--bg) !important; color: var(--text) !important; font-family: 'Outfit', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1rem 2rem 3rem !important; max-width: 1100px !important; }

/* ── Background mesh ── */
.stApp::before {
    content: '';
    position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background:
        radial-gradient(ellipse 80% 60% at 10% 5%,  rgba(99,179,237,0.04) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 90% 90%, rgba(159,122,234,0.04) 0%, transparent 60%),
        radial-gradient(ellipse 40% 40% at 50% 50%, rgba(240,180,41,0.02)  0%, transparent 70%);
}

/* ── HEADER ── */
.aura-header {
    text-align: center; padding: 40px 0 28px;
    animation: fadeDown 0.7s ease forwards;
}
@keyframes fadeDown { from{opacity:0;transform:translateY(-18px)} to{opacity:1;transform:translateY(0)} }

.aura-logo {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2.8rem,5vw,4.2rem);
    font-weight: 700; font-style: italic;
    background: linear-gradient(135deg, #f0b429 0%, #63b3ed 50%, #9f7aea 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; letter-spacing: -0.01em; line-height: 1;
}
.aura-tagline {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem; letter-spacing: 0.28em; text-transform: uppercase;
    color: var(--text3); margin: 10px 0 20px;
}
.aura-rule {
    width: 80px; height: 1px; margin: 0 auto;
    background: linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    animation: expandRule 1s ease 0.4s both;
}
@keyframes expandRule { from{width:0;opacity:0} to{width:80px;opacity:1} }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .stMarkdown h2 {
    font-family: 'Playfair Display', serif !important;
    font-style: italic !important; color: var(--gold) !important;
    font-size: 1.3rem !important; font-weight: 400 !important;
}

/* ── FEATURE NAV PILLS ── */
.nav-pill {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 8px 16px; border-radius: 999px; cursor: pointer;
    font-size: 0.78rem; font-weight: 500; letter-spacing: 0.03em;
    border: 1px solid var(--border); background: transparent;
    color: var(--text2); transition: all 0.25s; margin: 3px 0;
    width: 100%; text-align: left;
}
.nav-pill:hover  { border-color: var(--border2); color: var(--text); background: rgba(99,179,237,0.06); }
.nav-pill.active { border-color: var(--gold); color: var(--gold); background: rgba(240,180,41,0.08); }

/* ── CARDS ── */
.card {
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 24px; margin-bottom: 16px;
    transition: border-color 0.3s, box-shadow 0.3s;
    animation: fadeUp 0.5s ease forwards;
    position: relative; overflow: hidden;
}
.card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background: linear-gradient(90deg, var(--gold), var(--blue), var(--purple));
    transform: scaleX(0); transition: transform 0.4s; transform-origin: left;
}
.card:hover { border-color: var(--border2); box-shadow: var(--shadow); }
.card:hover::before { transform: scaleX(1); }
@keyframes fadeUp { from{opacity:0;transform:translateY(14px)} to{opacity:1;transform:translateY(0)} }

/* ── SECTION TITLES ── */
.sec-title {
    font-family: 'Playfair Display', serif; font-style: italic;
    font-size: clamp(1.6rem,3vw,2.4rem); color: var(--text);
    margin-bottom: 4px; animation: fadeUp 0.5s ease forwards;
}
.sec-sub {
    font-family: 'JetBrains Mono', monospace; font-size: 0.62rem;
    letter-spacing: 0.2em; text-transform: uppercase; color: var(--text3);
    margin-bottom: 24px; animation: fadeUp 0.5s ease 0.1s both;
}

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, var(--gold), var(--gold2)) !important;
    color: #080c14 !important; border: none !important;
    border-radius: var(--radius) !important;
    font-family: 'Outfit', sans-serif !important; font-weight: 700 !important;
    font-size: 0.78rem !important; letter-spacing: 0.1em !important;
    text-transform: uppercase !important; padding: 12px 28px !important;
    transition: all 0.3s !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 28px rgba(240,180,41,0.35) !important; }
.stButton > button:active { transform: translateY(0) !important; }

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stTextArea  > div > div > textarea {
    background: var(--bg3) !important; border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important; color: var(--text) !important;
    font-family: 'Outfit', sans-serif !important;
    transition: border-color 0.3s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea  > div > div > textarea:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 3px rgba(240,180,41,0.1) !important;
}

/* ── SELECT / SLIDER ── */
.stSelectbox > div > div { background: var(--bg3) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; color: var(--text) !important; }
.stSelectbox > div > div:hover { border-color: var(--border2) !important; }
.stSlider > div > div > div { background: rgba(240,180,41,0.25) !important; }
.stSlider > div > div > div > div { background: var(--gold) !important; }

/* ── CHAT ── */
.stChatMessage { background: var(--bg2) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; margin-bottom: 10px !important; animation: fadeUp 0.35s ease forwards; }
.stChatMessage [data-testid="chatAvatarIcon-user"]      { background: var(--gold)   !important; }
.stChatMessage [data-testid="chatAvatarIcon-assistant"] { background: var(--purple) !important; }
.stChatInput { background: var(--bg3) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; color: var(--text) !important; }
.stChatInput:focus-within { border-color: var(--gold) !important; }

/* ── ALERTS ── */
.stSuccess { background: rgba(104,211,145,0.08) !important; border: 1px solid rgba(104,211,145,0.25) !important; border-radius: var(--radius) !important; }
.stInfo    { background: rgba(99,179,237,0.08)  !important; border: 1px solid rgba(99,179,237,0.25)  !important; border-radius: var(--radius) !important; }
.stError   { background: rgba(252,129,129,0.08) !important; border: 1px solid rgba(252,129,129,0.25) !important; border-radius: var(--radius) !important; }
.stWarning { background: rgba(240,180,41,0.08)  !important; border: 1px solid rgba(240,180,41,0.25)  !important; border-radius: var(--radius) !important; }
.stSpinner > div { border-top-color: var(--gold) !important; }

/* ── FILE UPLOADER ── */
.stFileUploader { background: rgba(99,179,237,0.03) !important; border: 2px dashed var(--border) !important; border-radius: var(--radius) !important; }
.stFileUploader:hover { border-color: var(--border2) !important; }

/* ── METRICS ── */
[data-testid="metric-container"] { background: var(--bg2) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; padding: 16px !important; transition: all 0.3s !important; }
[data-testid="metric-container"]:hover { border-color: var(--border2) !important; transform: translateY(-2px) !important; }
[data-testid="stMetricValue"] { color: var(--gold) !important; font-family: 'Playfair Display', serif !important; font-size: 1.8rem !important; }
[data-testid="stMetricLabel"] { color: var(--text3) !important; font-size: 0.72rem !important; }

/* ── DOWNLOAD BUTTON ── */
.stDownloadButton > button { background: transparent !important; border: 1px solid var(--border2) !important; color: var(--blue) !important; border-radius: var(--radius) !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.7rem !important; transition: all 0.3s !important; }
.stDownloadButton > button:hover { background: rgba(99,179,237,0.1) !important; transform: translateY(-2px) !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(240,180,41,0.3); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: rgba(240,180,41,0.6); }

/* ── VOICE WIDGET ── */
.voice-card {
    background: var(--bg3); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 16px; margin: 12px 0;
}
.mono-label {
    font-family: 'JetBrains Mono', monospace; font-size: 0.6rem;
    letter-spacing: 0.2em; text-transform: uppercase; color: var(--text3);
    margin-bottom: 8px; display: block;
}

/* ── FOOTER ── */
.aura-footer {
    text-align: center; padding: 28px 0 12px;
    font-family: 'JetBrains Mono', monospace; font-size: 0.58rem;
    letter-spacing: 0.15em; color: var(--text3); text-transform: uppercase;
    border-top: 1px solid var(--border); margin-top: 48px;
}

/* ── TAB OVERRIDE ── */
.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid var(--border) !important; gap: 0 !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: var(--text3) !important; border: none !important; border-bottom: 2px solid transparent !important; font-family: 'Outfit',sans-serif !important; font-size: 0.8rem !important; padding: 10px 20px !important; }
.stTabs [aria-selected="true"] { color: var(--gold) !important; border-bottom-color: var(--gold) !important; }
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAZY MODEL LOADERS  (cached — download once, reuse forever)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@st.cache_resource(show_spinner="Loading chat model…")
def load_chat_model():
    from transformers import pipeline
    return pipeline(
        "text-generation",
        model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        device_map="auto",
        torch_dtype="auto",
    )

@st.cache_resource(show_spinner="Loading image-caption model…")
def load_caption_model():
    from transformers import pipeline
    return pipeline(
        "image-to-text",
        model="Salesforce/blip-image-captioning-base",
        device_map="auto",
    )

@st.cache_resource(show_spinner="Loading image-gen model…")
def load_image_gen():
    try:
        from diffusers import StableDiffusionPipeline
        import torch
        pipe = StableDiffusionPipeline.from_pretrained(
            "OFA-Sys/small-stable-diffusion-v0",
            torch_dtype=torch.float32,
            safety_checker=None,
            requires_safety_checker=False,
        )
        pipe.enable_attention_slicing()
        return pipe
    except Exception as e:
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def chat_with_model(messages: list, max_new_tokens: int = 512) -> str:
    """Run TinyLlama chat."""
    try:
        pipe = load_chat_model()
        # Build prompt in TinyLlama chat format
        prompt = ""
        for m in messages:
            role = m["role"]
            content = m["content"]
            if role == "system":
                prompt += f"<|system|>\n{content}</s>\n"
            elif role == "user":
                prompt += f"<|user|>\n{content}</s>\n"
            elif role == "assistant":
                prompt += f"<|assistant|>\n{content}</s>\n"
        prompt += "<|assistant|>\n"

        out = pipe(
            prompt,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=pipe.tokenizer.eos_token_id,
            eos_token_id=pipe.tokenizer.eos_token_id,
        )
        generated = out[0]["generated_text"]
        # Extract only the last assistant reply
        reply = generated.split("<|assistant|>")[-1].strip()
        reply = reply.replace("</s>", "").strip()
        return reply if reply else "I'm not sure how to respond to that."
    except Exception as e:
        return f"⚠️ Chat error: {e}"


def analyze_image(image: Image.Image, question: str = "") -> str:
    """Caption / analyze image with BLIP."""
    try:
        cap_pipe = load_caption_model()
        result   = cap_pipe(image)
        caption  = result[0]["generated_text"] if result else "Could not describe image."

        if question.strip():
            # Use chat model to answer the question using caption as context
            answer = chat_with_model([
                {"role": "system",  "content": "You are a helpful visual assistant. Use the image description to answer the user's question."},
                {"role": "user",    "content": f"Image description: {caption}\n\nQuestion: {question}"},
            ])
            return f"**Visual description:** {caption}\n\n**Answer:** {answer}"
        return caption
    except Exception as e:
        return f"⚠️ Image analysis error: {e}"


def generate_image_local(prompt: str, style_suffix: str) -> Image.Image | None:
    """Generate image with local SD pipeline."""
    pipe = load_image_gen()
    if pipe is None:
        return None
    full = prompt + style_suffix
    result = pipe(full, num_inference_steps=20, guidance_scale=7.5)
    return result.images[0]


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF."""
    import PyPDF2
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text   = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    return text.strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX."""
    try:
        from docx import Document
        doc  = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        return f"Could not read DOCX: {e}"


def get_weather(city: str, unit: str = "Celsius") -> dict | None:
    """Fetch weather from open-meteo (no key needed)."""
    try:
        geo = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1",
            timeout=10
        ).json()
        if "results" not in geo or not geo["results"]:
            return None
        loc = geo["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        unit_param = "celsius" if unit == "Celsius" else "fahrenheit"
        w = requests.get(
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,"
            f"weather_code,apparent_temperature,precipitation"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
            f"&temperature_unit={unit_param}&forecast_days=5&timezone=auto",
            timeout=10
        ).json()
        return {"loc": loc, "weather": w, "unit": unit}
    except Exception:
        return None


WEATHER_CODES = {
    0:"☀️ Clear sky", 1:"🌤 Mainly clear", 2:"⛅ Partly cloudy",
    3:"☁️ Overcast", 45:"🌫 Foggy", 48:"🌫 Icy fog",
    51:"🌦 Light drizzle", 61:"🌧 Light rain", 63:"🌧 Moderate rain",
    65:"🌧 Heavy rain", 71:"🌨 Light snow", 75:"❄️ Heavy snow",
    80:"🌦 Rain showers", 95:"⛈ Thunderstorm",
}


def tts_html(text: str, lang: str = "en") -> str:
    """Browser Web Speech API TTS widget."""
    clean = text.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")[:600]
    lang_map = {"en": "en-US", "hi": "hi-IN", "mr": "mr-IN"}
    voice_lang = lang_map.get(lang, "en-US")
    return f"""
    <div style="display:flex;align-items:center;gap:10px;padding:10px 14px;
                background:rgba(240,180,41,0.06);border:1px solid rgba(240,180,41,0.15);
                border-radius:10px;margin-top:8px;">
        <span style="font-family:'JetBrains Mono',monospace;font-size:.58rem;
                     letter-spacing:.12em;color:rgba(240,180,41,0.5);text-transform:uppercase;">
            🔊 Listen
        </span>
        <button onclick="ttsPlay_{id(text) % 99999}()" id="ttsBtn_{id(text) % 99999}"
            style="background:rgba(240,180,41,0.12);border:1px solid rgba(240,180,41,0.3);
                   color:#f0b429;border-radius:6px;padding:5px 14px;cursor:pointer;
                   font-size:.65rem;letter-spacing:.08em;transition:all .3s;">
            ▶ Play
        </button>
        <button onclick="window.speechSynthesis.cancel();document.getElementById('ttsBtn_{id(text) % 99999}').textContent='▶ Play';"
            style="background:rgba(252,129,129,0.1);border:1px solid rgba(252,129,129,0.2);
                   color:#fc8181;border-radius:6px;padding:5px 14px;cursor:pointer;
                   font-size:.65rem;letter-spacing:.08em;transition:all .3s;">
            ⏹ Stop
        </button>
    </div>
    <script>
    function ttsPlay_{id(text) % 99999}() {{
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance('{clean}');
        u.lang = '{voice_lang}'; u.rate = 0.95; u.pitch = 1.0;
        const vs = window.speechSynthesis.getVoices();
        const v  = vs.find(x => x.lang.startsWith('{voice_lang[:2]}'));
        if (v) u.voice = v;
        const btn = document.getElementById('ttsBtn_{id(text) % 99999}');
        btn.textContent = '🔊 Speaking…';
        u.onend = () => btn.textContent = '▶ Play';
        window.speechSynthesis.speak(u);
    }}
    </script>
    """


VOICE_INPUT_HTML = """
<script>
let recog = null, isListening = false;

function toggleMic() {
    const btn  = document.getElementById('micBtn');
    const stat = document.getElementById('micStat');
    const out  = document.getElementById('micOut');

    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        stat.textContent = '❌ Use Chrome — Firefox does not support Web Speech API';
        return;
    }
    if (isListening) { recog.stop(); return; }

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    recog = new SR();
    recog.lang = 'en-IN'; recog.continuous = false; recog.interimResults = true;

    recog.onstart = () => {
        isListening = true;
        btn.textContent = '⏹ Stop';
        btn.style.background = 'linear-gradient(135deg,#fc8181,#e53e3e)';
        stat.textContent = '🔴 Listening… speak now';
    };
    recog.onresult = e => {
        let txt = '';
        for (let i = e.resultIndex; i < e.results.length; i++)
            txt += e.results[i][0].transcript;
        out.value = txt;
        stat.textContent = '💬 ' + txt.slice(0, 60) + (txt.length > 60 ? '…' : '');
    };
    recog.onerror = e => {
        if (e.error === 'not-allowed')
            stat.textContent = '❌ Mic blocked — click the 🔒 icon in address bar → Allow microphone';
        else
            stat.textContent = '❌ Error: ' + e.error;
        resetMic();
    };
    recog.onend = () => { isListening = false; resetMic(); };
    recog.start();
}

function resetMic() {
    const btn = document.getElementById('micBtn');
    if (btn) { btn.textContent = '🎙 Speak'; btn.style.background = 'linear-gradient(135deg,#9f7aea,#6b46c1)'; }
    isListening = false;
}

function copyMic() {
    const txt = document.getElementById('micOut').value;
    if (!txt) return;
    navigator.clipboard.writeText(txt).then(() => {
        document.getElementById('micStat').textContent = '✅ Copied! Paste in the chat below.';
    });
}
</script>

<style>
.vm-wrap  { background:rgba(13,18,32,0.9);border:1px solid rgba(99,179,237,0.12);border-radius:12px;padding:14px 16px;margin:10px 0; }
.vm-btns  { display:flex;gap:8px;margin-bottom:10px; }
.vm-btn   { border:none;border-radius:8px;padding:9px 18px;font-weight:600;font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;cursor:pointer;transition:all .25s; }
#micBtn   { background:linear-gradient(135deg,#9f7aea,#6b46c1);color:#fff; }
#micBtn:hover { transform:translateY(-1px);box-shadow:0 6px 20px rgba(159,122,234,.35); }
#copyBtn  { background:rgba(240,180,41,.12);color:#f0b429;border:1px solid rgba(240,180,41,.3); }
#copyBtn:hover { background:rgba(240,180,41,.2); }
#micOut   { width:100%;padding:9px 12px;background:rgba(255,255,255,.04);border:1px solid rgba(99,179,237,.12);border-radius:8px;color:#e2e8f0;font-size:.85rem;resize:none;min-height:42px;outline:none;transition:border-color .3s; }
#micOut:focus { border-color:rgba(240,180,41,.5); }
#micStat  { font-family:'JetBrains Mono',monospace;font-size:.58rem;color:rgba(240,180,41,.55);letter-spacing:.1em;margin-top:6px;display:block; }
</style>

<div class="vm-wrap">
    <div class="vm-btns">
        <button class="vm-btn" id="micBtn" onclick="toggleMic()">🎙 Speak</button>
        <button class="vm-btn" id="copyBtn" onclick="copyMic()">📋 Copy</button>
    </div>
    <textarea id="micOut" rows="2" placeholder="Your speech will appear here — then Copy & Paste below…"></textarea>
    <span id="micStat">✦ Click Speak → talk → Copy → paste in chat</span>
</div>
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<div class="aura-header">
    <div class="aura-logo">Aura AI</div>
    <div class="aura-tagline">✦ &nbsp; 100 % local · no api keys · hugging face · offline-ready &nbsp; ✦</div>
    <div class="aura-rule"></div>
</div>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FEATURES = [
    ("💬", "AI Chat"),
    ("🎨", "Image Generator"),
    ("🖼", "Image Analyzer"),
    ("📄", "Document Chat"),
    ("🌤", "Weather"),
    ("🔊", "Voice Studio"),
]

with st.sidebar:
    st.markdown("## ✦ Aura")
    st.markdown("---")

    if "feature" not in st.session_state:
        st.session_state.feature = "AI Chat"

    for icon, name in FEATURES:
        active = "active" if st.session_state.feature == name else ""
        if st.button(f"{icon}  {name}", key=f"nav_{name}", use_container_width=True):
            st.session_state.feature = name
            st.rerun()

    st.markdown("---")

    # Per-feature settings
    feat = st.session_state.feature
    if feat in ("AI Chat", "Document Chat"):
        st.markdown("**Settings**")
        st.session_state.temperature = st.slider("Creativity", 0.1, 1.0, 0.7, key="temp_slider")
        st.session_state.max_tokens  = st.slider("Max tokens", 64, 1024, 400, key="tok_slider")
        st.session_state.chat_lang   = st.selectbox("TTS language", ["en", "hi", "mr"], key="lang_sel")
        if st.button("🗑 Clear Chat", use_container_width=True):
            for k in ["messages", "doc_text", "doc_name"]:
                st.session_state.pop(k, None)
            st.rerun()

    st.markdown("---")
    st.caption("Built by Rupal Darode ✦")
    st.caption("All models run locally 🏠")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SHARED CHAT RENDERER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_chat(system_prompt: str, show_voice_input: bool = True):
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                lang = st.session_state.get("chat_lang", "en")
                st.components.v1.html(tts_html(msg["content"], lang), height=62, scrolling=False)

    if show_voice_input:
        with st.expander("🎙 Voice Input — speak then copy/paste"):
            st.components.v1.html(VOICE_INPUT_HTML, height=155, scrolling=False)

    prompt = st.chat_input("Message Aura…")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        all_msgs = [{"role": "system", "content": system_prompt}] + [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                reply = chat_with_model(
                    all_msgs,
                    max_new_tokens=st.session_state.get("max_tokens", 400),
                )
            st.markdown(reply)
            lang = st.session_state.get("chat_lang", "en")
            st.components.v1.html(tts_html(reply, lang), height=62, scrolling=False)
        st.session_state.messages.append({"role": "assistant", "content": reply})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ══  FEATURE 1: AI CHAT  ══
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if st.session_state.feature == "AI Chat":
    st.markdown('<div class="sec-title">💬 AI Chat</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Local TinyLlama · Voice input · TTS output</div>', unsafe_allow_html=True)

    system_prompt = (
        "You are Aura, a helpful, concise, and friendly AI assistant. "
        "Give clear, accurate answers. Keep responses focused."
    )
    render_chat(system_prompt)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ══  FEATURE 2: IMAGE GENERATOR  ══
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif st.session_state.feature == "Image Generator":
    st.markdown('<div class="sec-title">🎨 Image Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Local Stable Diffusion · No internet needed · ~2 GB download once</div>', unsafe_allow_html=True)

    STYLES = {
        "None":         "",
        "Realistic":    ", ultra realistic, 8k, cinematic lighting",
        "Anime":        ", anime style, vibrant, Studio Ghibli",
        "Oil Painting": ", oil painting, detailed brushwork",
        "Cyberpunk":    ", cyberpunk, neon lights, futuristic",
        "Watercolor":   ", watercolor art, soft colors, artistic",
        "Sketch":       ", pencil sketch, hand drawn, detailed",
    }

    st.markdown('<div class="card">', unsafe_allow_html=True)
    prompt_img = st.text_area("Describe your image",
                              placeholder="A red apple on a white table, studio lighting…",
                              height=90, key="img_prompt")
    c1, c2 = st.columns(2)
    with c1: style_key = st.selectbox("Style", list(STYLES.keys()))
    with c2: neg_img   = st.text_input("Negative prompt", placeholder="blurry, ugly, low quality…")
    st.markdown('</div>', unsafe_allow_html=True)

    st.info("⚡ First run downloads ~2 GB model. Subsequent runs are instant from cache.", icon="📦")

    if st.button("✦ Generate Image", use_container_width=True):
        if prompt_img.strip():
            with st.spinner("🎨 Generating… (30–90 sec on CPU, ~5 sec on GPU)"):
                img = generate_image_local(prompt_img.strip(), STYLES[style_key])
            if img:
                st.image(img, use_container_width=True)
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.download_button("⬇ Download PNG", buf.getvalue(),
                                   file_name="aura_image.png", mime="image/png",
                                   use_container_width=True)
            else:
                st.error("Image generation failed. Make sure `diffusers` and `torch` are installed.")
                st.code("pip install diffusers torch accelerate", language="bash")
        else:
            st.warning("Please enter a prompt!")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ══  FEATURE 3: IMAGE ANALYZER  ══
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif st.session_state.feature == "Image Analyzer":
    st.markdown('<div class="sec-title">🖼 Image Analyzer</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">BLIP captioning · Ask anything about the image</div>', unsafe_allow_html=True)

    uploaded_img = st.file_uploader("Upload image (PNG / JPG / WEBP)", type=["png","jpg","jpeg","webp"])

    if uploaded_img:
        image = Image.open(uploaded_img).convert("RGB")
        st.image(image, use_container_width=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Quick Actions**")
        c1, c2, c3, c4 = st.columns(4)
        quick = ""
        with c1:
            if st.button("📝 Describe"):  quick = "Describe this image in detail."
        with c2:
            if st.button("🎨 Colors"):    quick = "What are the dominant colors and their mood?"
        with c3:
            if st.button("😊 Mood"):      quick = "What is the overall mood or emotion of this image?"
        with c4:
            if st.button("📦 Objects"):   quick = "List all visible objects in this image."

        question = st.text_input("Or ask your own question:", value=quick,
                                 placeholder="What is happening in this image?")
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🔍 Analyze", use_container_width=True):
            with st.spinner("Analyzing image…"):
                result = analyze_image(image, question)
            st.success(result)
            st.components.v1.html(tts_html(result), height=62, scrolling=False)
    else:
        st.info("📤 Upload an image to get started.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ══  FEATURE 4: DOCUMENT CHAT  ══
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif st.session_state.feature == "Document Chat":
    st.markdown('<div class="sec-title">📄 Document Chat</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">PDF · DOCX · TXT — chat with any document</div>', unsafe_allow_html=True)

    uploaded_doc = st.file_uploader("Upload document", type=["pdf","docx","txt"])

    if uploaded_doc:
        if "doc_text" not in st.session_state or st.session_state.get("doc_name") != uploaded_doc.name:
            with st.spinner("Reading document…"):
                raw = uploaded_doc.read()
                ext = uploaded_doc.name.split(".")[-1].lower()
                if ext == "pdf":
                    text = extract_text_from_pdf(raw)
                elif ext == "docx":
                    text = extract_text_from_docx(raw)
                else:
                    text = raw.decode("utf-8", errors="ignore")
                st.session_state.doc_text = text[:6000]   # keep first 6k chars
                st.session_state.doc_name = uploaded_doc.name
                st.session_state.messages = []            # reset chat
            st.success(f"✅ Loaded **{uploaded_doc.name}** — {len(text):,} characters")

        if "doc_text" in st.session_state:
            st.caption(f"📄 {st.session_state.doc_name} · {len(st.session_state.doc_text):,} chars loaded")
            system = (
                f"You are a helpful assistant. Answer questions based ONLY on the document below.\n"
                f"If the answer is not in the document, say 'I couldn't find that in the document.'\n\n"
                f"--- DOCUMENT ---\n{st.session_state.doc_text}\n--- END ---"
            )
            render_chat(system)
    else:
        st.info("📤 Upload a PDF, DOCX, or TXT file to start chatting with it.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ══  FEATURE 5: WEATHER  ══
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif st.session_state.feature == "Weather":
    st.markdown('<div class="sec-title">🌤 Weather</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Open-Meteo API · No key needed · 5-day forecast</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1: city = st.text_input("City name", placeholder="Nagpur, Mumbai, Delhi, New York…")
    with c2: unit = st.selectbox("Unit", ["Celsius", "Fahrenheit"])
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🔍 Get Weather", use_container_width=True):
        if city.strip():
            with st.spinner("Fetching weather…"):
                data = get_weather(city.strip(), unit)
            if not data:
                st.error("City not found. Please check the spelling.")
            else:
                loc = data["loc"]
                w   = data["weather"]["current"]
                d   = data["weather"]["daily"]
                sym = "°C" if unit == "Celsius" else "°F"
                code = w.get("weather_code", 0)
                desc = WEATHER_CODES.get(code, "🌡 Unknown")

                st.success(f"**{loc.get('name')}, {loc.get('country')}**  ·  {loc.get('admin1','')}")

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("🌡 Temperature",  f"{w['temperature_2m']}{sym}",       f"Feels {w['apparent_temperature']}{sym}")
                c2.metric("💧 Humidity",     f"{w['relative_humidity_2m']}%")
                c3.metric("💨 Wind",         f"{w['wind_speed_10m']} km/h")
                c4.metric("🌦 Condition",    desc)

                # 5-day forecast
                st.markdown("**5-Day Forecast**")
                cols = st.columns(5)
                for i, col in enumerate(cols):
                    try:
                        day   = datetime.fromisoformat(d["time"][i]).strftime("%a %d")
                        hi    = d["temperature_2m_max"][i]
                        lo    = d["temperature_2m_min"][i]
                        rain  = d["precipitation_sum"][i]
                        col.markdown(f"""
<div style="background:var(--bg3);border:1px solid var(--border);border-radius:10px;
            padding:12px 8px;text-align:center;">
    <div style="font-size:.72rem;color:var(--text3);font-family:'JetBrains Mono',monospace;">{day}</div>
    <div style="font-size:1.4rem;margin:6px 0;">
        {WEATHER_CODES.get(0,'🌡').split()[0]}
    </div>
    <div style="color:var(--gold);font-weight:600;font-size:.85rem;">{hi:.0f}{sym}</div>
    <div style="color:var(--text3);font-size:.78rem;">{lo:.0f}{sym}</div>
    <div style="color:var(--blue);font-size:.68rem;margin-top:4px;">💧 {rain:.1f}mm</div>
</div>""", unsafe_allow_html=True)
                    except Exception:
                        pass

                # AI weather tip
                with st.spinner("Getting AI tip…"):
                    tip = chat_with_model([
                        {"role": "system", "content": "Give a short 2-line practical tip for the weather."},
                        {"role": "user",   "content": f"Weather: {w['temperature_2m']}{sym}, {desc}, humidity {w['relative_humidity_2m']}%."},
                    ], max_new_tokens=80)
                st.info(f"💡 {tip}")
                st.components.v1.html(tts_html(tip), height=62, scrolling=False)
        else:
            st.warning("Please enter a city name.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ══  FEATURE 6: VOICE STUDIO  ══
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif st.session_state.feature == "Voice Studio":
    st.markdown('<div class="sec-title">🔊 Voice Studio</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Voice-to-Text · Text-to-Voice · Voice-to-Voice</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🎙 Voice → Text", "📢 Text → Voice", "🔄 Voice → Voice"])

    # ── TAB 1: Voice to Text ──
    with tab1:
        st.markdown("**Speak and convert to text using your browser microphone.**")
        st.markdown("*Works best in Chrome. The browser handles all speech recognition — no model needed.*")
        st.components.v1.html(VOICE_INPUT_HTML, height=160, scrolling=False)
        st.info("After copying the text, you can paste it anywhere — the chat, a document, etc.")

    # ── TAB 2: Text to Voice ──
    with tab2:
        st.markdown("**Type text and hear it spoken aloud using your browser's TTS engine.**")
        tts_text = st.text_area("Enter text to speak", height=140,
                                placeholder="Type anything here and press Play…")
        tts_lang = st.selectbox("Language / accent", ["en", "hi", "mr"],
                                format_func=lambda x: {"en":"English","hi":"Hindi","mr":"Marathi"}[x])
        if tts_text.strip():
            st.components.v1.html(tts_html(tts_text, tts_lang), height=62, scrolling=False)
        else:
            st.caption("Start typing above to see the player.")

    # ── TAB 3: Voice to Voice (speak → AI reply → hear it) ──
    with tab3:
        st.markdown("**Speak a question → AI thinks → hear the answer.**")
        st.markdown("**How to use:**")
        st.markdown("1. Click **Speak** → say your question → Click **Copy**")
        st.markdown("2. Paste in the **Ask box** below → Click **Ask**")
        st.markdown("3. Listen to the AI's spoken reply 🔊")

        st.components.v1.html(VOICE_INPUT_HTML, height=160, scrolling=False)

        st.markdown("---")
        v2v_input = st.text_area("Ask box — paste your voice transcript here:", height=80,
                                 placeholder="Paste the copied transcript here…")
        v2v_lang  = st.selectbox("Reply language", ["en", "hi", "mr"],
                                 format_func=lambda x: {"en":"English","hi":"Hindi","mr":"Marathi"}[x],
                                 key="v2v_lang")

        if st.button("🎯 Ask Aura", use_container_width=True):
            if v2v_input.strip():
                with st.spinner("Thinking…"):
                    reply = chat_with_model([
                        {"role": "system",  "content": "You are Aura. Answer helpfully in 2-3 sentences."},
                        {"role": "user",    "content": v2v_input.strip()},
                    ], max_new_tokens=150)
                st.success(f"**Aura:** {reply}")
                st.components.v1.html(tts_html(reply, v2v_lang), height=62, scrolling=False)
            else:
                st.warning("Paste your voice transcript in the Ask box first.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FOOTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<div class="aura-footer">
    Built with ✦ by Rupal Darode &nbsp;·&nbsp; Aura AI &nbsp;·&nbsp;
    TinyLlama · BLIP · Stable Diffusion · Open-Meteo &nbsp;·&nbsp; 100% Local
</div>
""", unsafe_allow_html=True)
