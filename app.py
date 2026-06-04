"""
app.py — AI Assistant
======================
Features:
  1. 💬 Conversational Chat   (text + voice via Web Speech API)
  2. 🎨 Image Generator       (LOCAL — Stable Diffusion v1.5 via diffusers)
  3. 🖼  Image Analyzer        (LOCAL — BLIP captioning via transformers)
  4. 🌤  Weather Forecast      (Open-Meteo API — no key needed)
  5. 📄  Document Chat         (PDF / TXT upload + Groq Q&A)
  6. 🌐  Language Translator   (Groq LLM — 15+ languages)

API Keys required (only ONE, FREE):
  - GROQ_API_KEY  →  https://console.groq.com/keys

No HF_TOKEN needed — image models run locally on your machine.
First run downloads models (~2 GB). After that: fully offline.

Add to .streamlit/secrets.toml:
  GROQ_API_KEY = "gsk_..."
"""

# ── Standard library ──────────────────────────────────────────────
import io
import urllib.parse
import urllib3
import warnings
from datetime import datetime

# ── Third-party ───────────────────────────────────────────────────
import requests
import streamlit as st
from PIL import Image
from io import BytesIO

# Suppress SSL warnings (needed for some corporate/ISP networks)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore")


# ══════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ══════════════════════════════════════════════════════════════════
# STYLES — clean, minimal, professional dark theme
# ══════════════════════════════════════════════════════════════════

st.markdown("""
<style>
body, .stApp {
    background: #0f1117;
    color: #e8eaf0;
    font-family: 'Segoe UI', system-ui, sans-serif;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem !important; max-width: 1100px !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #161b27 !important;
    border-right: 1px solid #2a2f3e !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea  > div > div > textarea {
    background: #1a1f2e !important;
    border: 1px solid #2a2f3e !important;
    border-radius: 8px !important;
    color: #e8eaf0 !important;
}
.stTextInput > div > div > input:focus,
.stTextArea  > div > div > textarea:focus {
    border-color: #7c9ef5 !important;
    box-shadow: 0 0 0 2px rgba(124,158,245,.15) !important;
}

/* Buttons */
.stButton > button {
    background: #2e4bbd !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 10px 24px !important;
    transition: all .2s !important;
}
.stButton > button:hover {
    background: #3d5cd4 !important;
    transform: translateY(-1px) !important;
}

/* Selectbox / Slider */
.stSelectbox > div > div {
    background: #1a1f2e !important;
    border: 1px solid #2a2f3e !important;
    border-radius: 8px !important;
    color: #e8eaf0 !important;
}
.stSlider > div > div > div       { background: rgba(124,158,245,.3) !important; }
.stSlider > div > div > div > div { background: #7c9ef5 !important; }

/* File uploader */
.stFileUploader {
    background: #1a1f2e !important;
    border: 2px dashed #2a2f3e !important;
    border-radius: 12px !important;
}

/* Chat messages */
.stChatMessage {
    background: #1a1f2e !important;
    border: 1px solid #2a2f3e !important;
    border-radius: 10px !important;
    margin-bottom: 10px !important;
}
[data-testid="chatAvatarIcon-user"]      { background: #2e4bbd !important; }
[data-testid="chatAvatarIcon-assistant"] { background: #3a7d44 !important; }

/* Metrics */
[data-testid="metric-container"] {
    background: #1a1f2e !important;
    border: 1px solid #2a2f3e !important;
    border-radius: 10px !important;
    padding: 16px !important;
}
[data-testid="stMetricValue"] { color: #7c9ef5 !important; font-size: 1.8rem !important; }

/* Alerts */
.stSuccess { background: rgba(58,125,68,.15)  !important; border: 1px solid rgba(58,125,68,.4)  !important; border-radius: 8px !important; }
.stInfo    { background: rgba(124,158,245,.1) !important; border: 1px solid rgba(124,158,245,.3) !important; border-radius: 8px !important; }
.stError   { background: rgba(220,80,80,.1)   !important; border: 1px solid rgba(220,80,80,.3)   !important; border-radius: 8px !important; }
.stWarning { background: rgba(220,160,60,.1)  !important; border: 1px solid rgba(220,160,60,.3)  !important; border-radius: 8px !important; }

/* Download button */
.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid #2a2f3e !important;
    color: #7c9ef5 !important;
    border-radius: 8px !important;
}
.stDownloadButton > button:hover { background: #1a1f2e !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a2f3e; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════

GROQ_MODELS = {
    "⚡ Llama 3.1 8B  (Fast)":     "llama-3.1-8b-instant",
    "🧠 Llama 3.3 70B (Smart)":    "llama-3.3-70b-versatile",
    "💎 Mixtral 8×7B  (Balanced)": "mixtral-8x7b-32768",
    "🔬 Gemma 2 9B    (Google)":   "gemma2-9b-it",
}

TRANSLATE_LANGS = [
    "Hindi", "Marathi", "French", "Spanish", "German",
    "Japanese", "Chinese", "Arabic", "Russian", "Portuguese",
    "Bengali", "Tamil", "Telugu", "Kannada", "Gujarati",
]

IMAGE_STYLES = {
    "None":          "",
    "Realistic":     ", ultra realistic, 8k, DSLR, cinematic lighting",
    "Anime":         ", anime style, vibrant colors, Studio Ghibli",
    "Oil Painting":  ", oil painting, detailed brushwork, museum quality",
    "Cyberpunk":     ", cyberpunk, neon lights, futuristic, blade runner",
    "Watercolor":    ", watercolor art, soft colors, artistic",
    "Pencil Sketch": ", pencil sketch, hand-drawn, detailed linework",
    "3D Render":     ", 3D render, octane render, studio lighting",
}


# ══════════════════════════════════════════════════════════════════
# LOCAL MODEL LOADERS  (cached — loaded once, reused every time)
# ══════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner=False)
def load_image_pipeline():
    """
    Load Stable Diffusion v1.5 locally.
    First call downloads ~2 GB model weights (one-time only).
    Uses GPU if available, otherwise CPU.
    """
    from diffusers import StableDiffusionPipeline
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype  = torch.float16 if device == "cuda" else torch.float32

    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=dtype,
        safety_checker=None,          # removes NSFW filter overhead
        requires_safety_checker=False,
    )
    pipe = pipe.to(device)
    pipe.enable_attention_slicing()   # reduces RAM usage
    return pipe, device


@st.cache_resource(show_spinner=False)
def load_blip():
    """
    Load BLIP image-captioning model locally.
    First call downloads ~900 MB (one-time only).
    """
    from transformers import BlipProcessor, BlipForConditionalGeneration
    import torch

    model_id  = "Salesforce/blip-image-captioning-base"
    processor = BlipProcessor.from_pretrained(model_id)
    model     = BlipForConditionalGeneration.from_pretrained(
        model_id, torch_dtype=torch.float32
    )
    return processor, model


# ══════════════════════════════════════════════════════════════════
# API HELPERS
# ══════════════════════════════════════════════════════════════════

def get_groq_key() -> str:
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return ""


def call_groq(messages: list, model: str,
              temperature: float = 0.7, max_tokens: int = 1000) -> str:
    """Call Groq chat completion. Returns reply text or error string."""
    key = get_groq_key()
    if not key:
        return "❌ GROQ_API_KEY not found. Add it to .streamlit/secrets.toml"
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json={"model": model, "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens},
            timeout=30,
            verify=True,
        )
        data = resp.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        return f"❌ API Error: {data.get('error', {}).get('message', 'Unknown error')}"
    except requests.Timeout:
        return "⏱ Request timed out. Please try again."
    except Exception as e:
        return f"❌ Error: {e}"


def safe_get(url: str, **kwargs):
    """
    HTTP GET with automatic SSL fallback.
    Tries with SSL verification first; if SSL fails, retries with verify=False.
    """
    try:
        return requests.get(url, timeout=15, verify=True, **kwargs)
    except requests.exceptions.SSLError:
        return requests.get(url, timeout=15, verify=False, **kwargs)


# ══════════════════════════════════════════════════════════════════
# VOICE INPUT COMPONENT  (Web Speech API — Chrome/Edge only)
# ══════════════════════════════════════════════════════════════════

VOICE_HTML = """
<style>
#micBtn {
    background: #2e4bbd; color: #fff; border: none; border-radius: 8px;
    padding: 10px 22px; font-weight: 700; font-size: .78rem;
    letter-spacing: .06em; cursor: pointer; transition: all .25s;
    margin-right: 8px; text-transform: uppercase;
}
#micBtn:hover  { background: #3d5cd4; transform: translateY(-1px); }
#copyBtn {
    background: transparent; color: #7c9ef5;
    border: 1px solid #2a2f3e; border-radius: 8px;
    padding: 10px 18px; font-size: .75rem; cursor: pointer;
}
#copyBtn:hover { background: #1a1f2e; }
#transcript {
    width: 100%; margin-top: 10px; padding: 10px 14px;
    background: #1a1f2e; border: 1px solid #2a2f3e;
    border-radius: 8px; color: #e8eaf0; font-size: .88rem;
    resize: none; min-height: 44px; box-sizing: border-box;
}
#micStatus { font-size: .72rem; color: #7c9ef5; margin-top: 6px; display: block; }
</style>

<script>
let recognition = null, listening = false;

function toggleVoice() {
    const btn = document.getElementById('micBtn');
    const status = document.getElementById('micStatus');

    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        status.textContent = '❌ Not supported — use Google Chrome or Edge';
        return;
    }
    if (listening) { recognition.stop(); return; }

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SR();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-IN';

    recognition.onstart = () => {
        listening = true;
        btn.innerHTML = '⏹ Stop';
        btn.style.background = '#c04040';
        status.textContent = '🔴 Listening…';
    };
    recognition.onresult = (e) => {
        let final = '', interim = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
            e.results[i].isFinal
                ? (final   += e.results[i][0].transcript)
                : (interim += e.results[i][0].transcript);
        }
        document.getElementById('transcript').value = final || interim;
        status.textContent = interim ? '💬 ' + interim : '✅ Done — copy and paste below';
    };
    recognition.onerror = (e) => {
        status.textContent = e.error === 'not-allowed'
            ? '❌ Mic blocked — allow microphone in browser settings'
            : '❌ Error: ' + e.error;
        resetBtn();
    };
    recognition.onend = () => { listening = false; resetBtn(); };
    recognition.start();
}

function resetBtn() {
    const btn = document.getElementById('micBtn');
    if (btn) { btn.innerHTML = '🎙 Speak'; btn.style.background = '#2e4bbd'; }
}

function copyTranscript() {
    const txt = document.getElementById('transcript').value;
    if (!txt) return;
    navigator.clipboard.writeText(txt).then(() => {
        document.getElementById('micStatus').textContent =
            '📋 Copied! Paste it in the chat box below.';
    });
}
</script>

<div>
    <button id="micBtn"  onclick="toggleVoice()">🎙 Speak</button>
    <button id="copyBtn" onclick="copyTranscript()">📋 Copy Text</button>
    <textarea id="transcript" rows="2"
        placeholder="Your speech will appear here…"></textarea>
    <span id="micStatus">Click Speak → talk → Copy Text → paste in chat</span>
</div>
"""


def tts_html(text: str) -> str:
    """Play/Stop buttons using browser Web Speech API TTS."""
    safe = text.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")[:600]
    return f"""
    <div style="display:flex;align-items:center;gap:8px;margin-top:6px;">
        <span style="font-size:.7rem;color:#7c9ef5;">🔊</span>
        <button onclick="(function(){{
            window.speechSynthesis.cancel();
            var u = new SpeechSynthesisUtterance('{safe}');
            u.rate = 0.95;
            window.speechSynthesis.speak(u);
        }})()"
        style="background:rgba(124,158,245,.12);color:#7c9ef5;
               border:1px solid rgba(124,158,245,.3);border-radius:6px;
               padding:4px 12px;font-size:.72rem;cursor:pointer;">▶ Play</button>
        <button onclick="window.speechSynthesis.cancel()"
        style="background:rgba(200,80,80,.1);color:#e06060;
               border:1px solid rgba(200,80,80,.25);border-radius:6px;
               padding:4px 12px;font-size:.72rem;cursor:pointer;">⏹ Stop</button>
    </div>"""


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🤖 AI Assistant")
    st.markdown("---")

    feature = st.selectbox("Select Feature", [
        "💬 Chat",
        "🎨 Image Generator",
        "🖼  Image Analyzer",
        "🌤  Weather Forecast",
        "📄  Document Chat",
        "🌐  Translator",
    ])

    st.markdown("---")

    # Model settings (only for text features)
    if feature in ("💬 Chat", "📄  Document Chat"):
        st.markdown("**Model**")
        model_name     = st.selectbox("AI Model", list(GROQ_MODELS.keys()),
                                      label_visibility="collapsed")
        selected_model = GROQ_MODELS[model_name]
        temperature    = st.slider("Creativity",  0.1, 1.0,  0.7)
        max_tokens     = st.slider("Max Tokens",  200, 4000, 1000, step=100)

        if st.button("🗑 Clear Chat", use_container_width=True):
            for k in ["messages", "doc_text", "doc_name"]:
                st.session_state.pop(k, None)
            st.rerun()

        if st.session_state.get("messages"):
            export_txt = "\n\n".join(
                f"{'You' if m['role']=='user' else 'AI'}: {m['content']}"
                for m in st.session_state.messages
            )
            st.download_button(
                "⬇ Export Chat", export_txt,
                file_name=f"chat_{datetime.now():%Y%m%d_%H%M}.txt",
                use_container_width=True,
            )

    st.markdown("---")
    st.caption("Groq · Stable Diffusion · BLIP · Open-Meteo")


# ══════════════════════════════════════════════════════════════════
# SHARED CHAT RENDERER
# ══════════════════════════════════════════════════════════════════

def render_chat(system_prompt: str):
    """Show message history and handle new user input (text + voice)."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                st.components.v1.html(tts_html(msg["content"]), height=40)

    # Voice input (collapsible)
    with st.expander("🎙 Voice Input  (Chrome / Edge only)", expanded=False):
        st.caption("Click Speak → talk → Copy Text → paste in the chat box below.")
        st.components.v1.html(VOICE_HTML, height=135)

    # Text input
    prompt = st.chat_input("Type your message…")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        full_msgs = [{"role": "system", "content": system_prompt}] + \
                    st.session_state.messages

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                reply = call_groq(full_msgs, selected_model, temperature, max_tokens)
            st.markdown(reply)
            st.components.v1.html(tts_html(reply), height=40)

        st.session_state.messages.append({"role": "assistant", "content": reply})


# ══════════════════════════════════════════════════════════════════
# FEATURE 1 — CHAT
# ══════════════════════════════════════════════════════════════════

if feature == "💬 Chat":
    st.title("💬 AI Chat")
    st.caption("Conversational assistant — text + voice supported")
    render_chat("You are a helpful, friendly AI assistant. Be concise and clear.")


# ══════════════════════════════════════════════════════════════════
# FEATURE 2 — IMAGE GENERATOR  (runs locally — no API needed)
# ══════════════════════════════════════════════════════════════════

elif feature == "🎨 Image Generator":
    st.title("🎨 Image Generator")
    st.caption("Runs locally using Stable Diffusion v1.5 — no internet needed after first load")

    st.info(
        "⚠️ **First run only:** Downloads ~2 GB model weights automatically.  \n"
        "Subsequent runs are instant (model is cached on your machine).  \n"
        "GPU detected = fast (~10s). CPU only = slower (~2–5 min)."
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        prompt = st.text_area(
            "Describe your image ✏️",
            placeholder="A golden sunset over the Sahara desert, camels in silhouette…",
            height=110,
        )
    with col2:
        style      = st.selectbox("Style", list(IMAGE_STYLES.keys()))
        size       = st.selectbox("Size", ["512×512", "768×512", "512×768"])
        neg_prompt = st.text_input("Negative prompt",
                                   placeholder="blurry, ugly, low quality…",
                                   value="blurry, ugly, distorted, low quality, watermark")
        steps      = st.slider("Quality steps", 10, 50, 25,
                               help="More steps = better quality but slower")

    if st.button("✨ Generate Image", use_container_width=True):
        if not prompt.strip():
            st.warning("Please enter a description for the image.")
        else:
            full_prompt = prompt.strip() + IMAGE_STYLES[style]
            w_str, h_str = size.replace("×", "x").split("x")
            width, height = int(w_str), int(h_str)

            with st.spinner("Loading model (first time takes a minute)…"):
                try:
                    pipe, device = load_image_pipeline()
                except Exception as e:
                    st.error(
                        f"Model load failed: {e}\n\n"
                        "Run:  pip install torch diffusers transformers accelerate safetensors"
                    )
                    st.stop()

            gpu_note = "🚀 GPU" if device == "cuda" else "🖥 CPU (be patient…)"
            with st.spinner(f"Generating image on {gpu_note}  ·  {steps} steps"):
                try:
                    import torch
                    result = pipe(
                        prompt=full_prompt,
                        negative_prompt=neg_prompt,
                        width=width,
                        height=height,
                        num_inference_steps=steps,
                        guidance_scale=7.5,
                    )
                    image = result.images[0]

                    st.image(image, use_container_width=True, caption=full_prompt)

                    buf = BytesIO()
                    image.save(buf, format="PNG")
                    st.download_button(
                        "⬇ Download Image", buf.getvalue(),
                        file_name="generated_image.png",
                        mime="image/png",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"Generation error: {e}")


# ══════════════════════════════════════════════════════════════════
# FEATURE 3 — IMAGE ANALYZER  (runs locally — no API needed)
# ══════════════════════════════════════════════════════════════════

elif feature == "🖼  Image Analyzer":
    st.title("🖼 Image Analyzer")
    st.caption("Runs locally using BLIP captioning — no internet needed after first load")

    uploaded = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"])

    if uploaded:
        image = Image.open(uploaded).convert("RGB")

        col_img, col_ctrl = st.columns([1, 1])
        with col_img:
            st.image(image, use_container_width=True)

        with col_ctrl:
            st.markdown("**Quick Questions**")
            QUICK = {
                "📝 Describe":  "Describe this image in detail.",
                "🎨 Colors":    "What are the dominant colors and their mood?",
                "😊 Mood":      "What is the overall mood or emotion?",
                "📦 Objects":   "List all the objects visible.",
                "📖 Read Text": "Is there any text in the image? If yes, read it.",
            }
            quick_q = ""
            cols_q  = st.columns(2)
            for i, (label, question) in enumerate(QUICK.items()):
                if cols_q[i % 2].button(label, use_container_width=True):
                    quick_q = question

            user_q = st.text_input(
                "Or ask a custom question:",
                value=quick_q,
                placeholder="What is happening in this image?",
            )

            if st.button("🔍 Analyze", use_container_width=True):
                if not user_q:
                    st.warning("Please select or type a question.")
                else:
                    # Step 1 — Get image caption using local BLIP
                    with st.spinner("Loading BLIP model (first time ~1 min)…"):
                        try:
                            processor, blip_model = load_blip()
                        except Exception as e:
                            st.error(
                                f"BLIP load failed: {e}\n\n"
                                "Run:  pip install transformers torch"
                            )
                            st.stop()

                    with st.spinner("Analyzing image…"):
                        import torch
                        inputs  = processor(image, return_tensors="pt")
                        out     = blip_model.generate(**inputs, max_new_tokens=100)
                        caption = processor.decode(out[0], skip_special_tokens=True)

                    # Step 2 — Answer the user's question via Groq
                    with st.spinner("Generating answer…"):
                        groq_msgs = [
                            {"role": "system",
                             "content": (
                                 "You are an expert image analyst. "
                                 "Use the image caption to answer the user's question accurately."
                             )},
                            {"role": "user",
                             "content": (
                                 f"Image caption: {caption}\n\n"
                                 f"User question: {user_q}"
                             )},
                        ]
                        reply = call_groq(groq_msgs, "llama-3.3-70b-versatile", 0.3, 800)

                    st.markdown("---")
                    st.caption(f"📌 BLIP Caption: *{caption}*")
                    st.success(reply)
                    st.components.v1.html(tts_html(reply), height=40)
    else:
        st.info("Upload a PNG, JPG, or WEBP image to get started.")


# ══════════════════════════════════════════════════════════════════
# FEATURE 4 — WEATHER FORECAST
# ══════════════════════════════════════════════════════════════════

elif feature == "🌤  Weather Forecast":
    st.title("🌤 Weather Forecast")
    st.caption("Real-time weather — Open-Meteo API (free, no key needed)")

    col1, col2 = st.columns([3, 1])
    with col1:
        city = st.text_input("City name", placeholder="Nagpur, Mumbai, Delhi, London…")
    with col2:
        unit = st.selectbox("Unit", ["Celsius", "Fahrenheit"])

    if st.button("Get Weather", use_container_width=True):
        if not city.strip():
            st.warning("Please enter a city name.")
        else:
            with st.spinner("Fetching weather…"):
                try:
                    # ── Geocoding (with SSL fallback) ──────────────────────
                    geo_resp = safe_get(
                        f"https://geocoding-api.open-meteo.com/v1/search"
                        f"?name={urllib.parse.quote(city)}&count=1"
                    )
                    geo = geo_resp.json()

                    if not geo.get("results"):
                        st.error(f"City '{city}' not found. Check the spelling.")
                    else:
                        loc     = geo["results"][0]
                        lat     = loc["latitude"]
                        lon     = loc["longitude"]
                        name    = loc.get("name", city)
                        country = loc.get("country", "")

                        temp_unit = "celsius" if unit == "Celsius" else "fahrenheit"
                        sym       = "°C" if unit == "Celsius" else "°F"

                        # ── Weather data (with SSL fallback) ──────────────
                        weather_resp = safe_get(
                            f"https://api.open-meteo.com/v1/forecast"
                            f"?latitude={lat}&longitude={lon}"
                            f"&current=temperature_2m,apparent_temperature,"
                            f"relative_humidity_2m,wind_speed_10m,weather_code"
                            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
                            f"&temperature_unit={temp_unit}&forecast_days=5"
                        )
                        weather = weather_resp.json()

                        curr     = weather["current"]
                        temp     = curr["temperature_2m"]
                        feels    = curr["apparent_temperature"]
                        humidity = curr["relative_humidity_2m"]
                        wind     = curr["wind_speed_10m"]
                        code     = curr["weather_code"]

                        WEATHER_CODES = {
                            0:"☀️ Clear", 1:"🌤 Mainly Clear", 2:"⛅ Partly Cloudy",
                            3:"☁️ Overcast", 45:"🌫 Foggy", 51:"🌦 Light Drizzle",
                            61:"🌧 Light Rain", 63:"🌧 Rain", 65:"🌧 Heavy Rain",
                            71:"🌨 Light Snow", 73:"❄️ Snow", 80:"🌦 Showers",
                            95:"⛈ Thunderstorm",
                        }
                        condition = WEATHER_CODES.get(code, f"Code {code}")

                        st.markdown(f"### {name}, {country}")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Temperature", f"{temp}{sym}",  f"Feels {feels}{sym}")
                        c2.metric("Humidity",    f"{humidity}%")
                        c3.metric("Wind Speed",  f"{wind} km/h")
                        c4.metric("Condition",   condition)

                        # ── 5-day forecast ────────────────────────────────
                        st.markdown("#### 5-Day Forecast")
                        daily  = weather["daily"]
                        cols_f = st.columns(5)
                        for i in range(5):
                            day = datetime.strptime(daily["time"][i], "%Y-%m-%d").strftime("%a %d")
                            with cols_f[i]:
                                st.markdown(f"**{day}**")
                                st.markdown(f"↑ {daily['temperature_2m_max'][i]}{sym}")
                                st.markdown(f"↓ {daily['temperature_2m_min'][i]}{sym}")
                                st.markdown(f"🌧 {daily['precipitation_sum'][i]} mm")

                        # ── AI weather tip ────────────────────────────────
                        with st.spinner("Generating weather tip…"):
                            tip = call_groq([
                                {"role": "system",
                                 "content": "Give a practical 2-line weather tip."},
                                {"role": "user",
                                 "content": f"{name}: {temp}{sym}, {condition}, {humidity}% humidity."},
                            ], "llama-3.1-8b-instant", 0.6, 120)
                        st.info(f"💡 {tip}")
                        st.components.v1.html(tts_html(tip), height=40)

                except Exception as e:
                    st.error(
                        f"Weather fetch failed: {e}\n\n"
                        "Check your internet connection and try again."
                    )


# ══════════════════════════════════════════════════════════════════
# FEATURE 5 — DOCUMENT CHAT
# ══════════════════════════════════════════════════════════════════

elif feature == "📄  Document Chat":
    st.title("📄 Document Chat")
    st.caption("Upload a PDF or TXT file and ask questions about it")

    uploaded_doc = st.file_uploader("Upload document", type=["pdf", "txt"])

    if uploaded_doc:
        if ("doc_text" not in st.session_state or
                st.session_state.get("doc_name") != uploaded_doc.name):
            with st.spinner("Reading document…"):
                try:
                    if uploaded_doc.name.lower().endswith(".pdf"):
                        import PyPDF2
                        reader = PyPDF2.PdfReader(io.BytesIO(uploaded_doc.read()))
                        text   = "\n".join(p.extract_text() or "" for p in reader.pages)
                        info   = f"{len(reader.pages)} pages"
                    else:
                        text = uploaded_doc.read().decode("utf-8", errors="ignore")
                        info = f"{len(text.split())} words"

                    st.session_state.doc_text = text[:10_000]
                    st.session_state.doc_name = uploaded_doc.name
                    st.session_state.messages = []
                    st.success(f"✅ Loaded **{uploaded_doc.name}** — {info}")

                except Exception as e:
                    st.error(f"Could not read document: {e}")

        if "doc_text" in st.session_state:
            st.caption(
                f"📎 {st.session_state.doc_name} · "
                f"{len(st.session_state.doc_text):,} characters"
            )
            system_prompt = (
                "You are a helpful assistant. Answer ONLY based on the document below. "
                "If the answer is not in the document, say so clearly.\n\n"
                f"DOCUMENT:\n---\n{st.session_state.doc_text}\n---"
            )
            render_chat(system_prompt)
    else:
        st.info("Upload a **PDF** or **TXT** file to start chatting with it.")
        for k in ["messages", "doc_text", "doc_name"]:
            st.session_state.pop(k, None)


# ══════════════════════════════════════════════════════════════════
# FEATURE 6 — TRANSLATOR
# ══════════════════════════════════════════════════════════════════

elif feature == "🌐  Translator":
    st.title("🌐 Language Translator")
    st.caption("Translate to 15+ languages powered by Groq AI")

    col1, col2 = st.columns([2, 1])
    with col1:
        source_text = st.text_area(
            "Text to translate",
            placeholder="Enter text here in any language…",
            height=160,
        )
    with col2:
        target_lang   = st.selectbox("Translate to", TRANSLATE_LANGS)
        tone          = st.selectbox("Tone",
                                     ["Formal", "Informal / Casual", "Simple"])
        show_romanize = st.checkbox("Show Romanization", value=True)

    if st.button("🌐 Translate", use_container_width=True):
        if not source_text.strip():
            st.warning("Please enter some text to translate.")
        else:
            tone_map = {
                "Formal":           "formal and professional",
                "Informal / Casual":"informal and conversational",
                "Simple":           "simple and easy to understand",
            }
            roman_note = (
                "After translating, add 'Romanization: ...' on a new line "
                "if the target script is non-Latin."
                if show_romanize else ""
            )
            with st.spinner(f"Translating to {target_lang}…"):
                result = call_groq([
                    {"role": "system",
                     "content": (
                         f"You are a professional translator. Translate accurately into {target_lang}. "
                         f"Use a {tone_map[tone]} tone. "
                         f"Output ONLY the translation — no commentary. {roman_note}"
                     )},
                    {"role": "user", "content": source_text.strip()},
                ], "llama-3.3-70b-versatile", 0.3, 1000)

            st.markdown(f"**Translation → {target_lang}**")
            st.success(result)
            st.components.v1.html(tts_html(result), height=40)

            col_a, col_b = st.columns(2)
            col_a.download_button(
                "⬇ Download", result,
                file_name=f"translation_{target_lang.lower()}.txt",
                mime="text/plain", use_container_width=True,
            )
            if col_b.button("🔄 Back-translate to English", use_container_width=True):
                with st.spinner("Back-translating…"):
                    back = call_groq([
                        {"role": "system",
                         "content": "Translate to English. Output only the translation."},
                        {"role": "user", "content": result},
                    ], "llama-3.3-70b-versatile", 0.3, 500)
                st.info(f"**Back-translation (EN):** {back}")
