# ============================================================
#  Aura AI  —  Complete Fixed Version
#  Built by Rupal Darode
# ============================================================
#
#  SETUP — Add these in Streamlit Cloud → Settings → Secrets:
#
#     GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxx"
#
#  Get free Groq key: https://console.groq.com/keys
#
#  NOTE: No HF_TOKEN needed anymore!
#   • Image Generator → uses Pollinations.ai (100% free, no key)
#   • Image Analyzer  → uses Groq LLaMA vision (uses GROQ_API_KEY)
#   • Weather         → uses Open-Meteo (free, no key)
# ============================================================

import io
import base64
import urllib.parse
from datetime import datetime

import PyPDF2
import requests
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from io import BytesIO

# ── PAGE CONFIG ────────────────────────────────────────────
st.set_page_config(page_title="Aura AI", page_icon="✨", layout="wide")

# ── STYLING ────────────────────────────────────────────────
st.markdown("""
<style>
  .stApp { background-color: #f9fafb; }
  section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
  }
  .stChatMessage {
    background-color: #ffffff !important;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
  }
  /* Hide default label for voice text input */
  .voice-hidden { display: none; }
</style>
""", unsafe_allow_html=True)


# ── CONSTANTS ──────────────────────────────────────────────

GROQ_MODELS = {
    "⚡ Llama 3.1 8B  — Fast":      "llama-3.1-8b-instant",
    "🧠 Llama 3.3 70B — Smart":     "llama-3.3-70b-versatile",
    "💎 Mixtral 8x7B  — Balanced":  "mixtral-8x7b-32768",
    "🔬 Gemma 2 9B    — Google":    "gemma2-9b-it",
}

# Pollinations.ai image models — FREE, no API key, no blocks
POLLINATIONS_MODELS = {
    "Flux (Best Quality)":    "flux",
    "Flux Realism":           "flux-realism",
    "Flux Anime":             "flux-anime",
    "Flux 3D":                "flux-3d",
    "Turbo (Fastest)":        "turbo",
}

IMAGE_STYLES = {
    "None":         "",
    "Realistic":    ", ultra realistic, photographic, 8k",
    "Anime":        ", anime style, vibrant, Studio Ghibli",
    "Oil Painting": ", oil painting, detailed brushwork",
    "Cyberpunk":    ", cyberpunk, neon lights, futuristic",
    "Watercolor":   ", watercolor, soft colors, artistic",
    "Sketch":       ", pencil sketch, hand drawn",
}

LANGUAGES = {
    "English":  "Always respond in English.",
    "Hindi":    "Hamesha Hindi mein jawab do.",
    "Hinglish": "Hinglish mein jawab do — Hindi aur English mix karke.",
    "Marathi":  "Marathi madhe uttar dya.",
}


# ── HELPER FUNCTIONS ───────────────────────────────────────

def call_groq(messages, model, temperature=0.7, max_tokens=1000):
    """Call Groq API and return reply text."""
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        return "❌ GROQ_API_KEY missing. Add it in Streamlit Settings → Secrets."

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens},
            timeout=30,
        )
        data = res.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        elif "error" in data:
            return f"❌ Groq Error: {data['error']['message']}"
        return f"❌ Unexpected: {data}"
    except requests.exceptions.Timeout:
        return "⏱ Timed out. Try again."
    except Exception as e:
        return f"❌ Error: {e}"


def generate_image_pollinations(prompt, model="flux"):
    """
    Generate image using Pollinations.ai — completely FREE, no API key needed.
    Returns a PIL Image on success, or None on failure.
    """
    try:
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?model={model}&width=768&height=768&nologo=true"
        res = requests.get(url, timeout=60)
        if res.status_code == 200:
            return Image.open(BytesIO(res.content))
        st.error(f"❌ Image generation failed. Status: {res.status_code}")
        return None
    except Exception as e:
        st.error(f"❌ Image generation error: {e}")
        return None


def analyze_image_groq(image: Image.Image, question: str) -> str:
    """
    Analyze an image using Groq's LLaMA vision model.
    Converts image to base64 and sends to Groq — no HF token needed.
    """
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        return "❌ GROQ_API_KEY missing."

    # Convert image to base64
    buf = BytesIO()
    image.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.2-11b-vision-preview",  # Groq's free vision model
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                            {"type": "text", "text": question},
                        ],
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.3,
            },
            timeout=30,
        )
        data = res.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        elif "error" in data:
            return f"❌ Groq Error: {data['error']['message']}"
        return f"❌ Unexpected response: {data}"
    except Exception as e:
        return f"❌ Vision error: {e}"


def extract_pdf_text(pdf_file) -> str:
    """Extract text from PDF (max 8000 chars)."""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        text = "".join(page.extract_text() or "" for page in reader.pages)
        return text[:8000]
    except Exception as e:
        return f"ERROR: {e}"


def transcribe_audio_groq(audio_bytes: bytes) -> str:
    """
    Transcribe audio using Groq Whisper API.
    This is how voice → text works reliably in Streamlit Cloud.
    """
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        return ""

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": ("audio.wav", audio_bytes, "audio/wav")},
            data={"model": "whisper-large-v3"},
            timeout=30,
        )
        data = res.json()
        return data.get("text", "")
    except Exception as e:
        return ""


# ── SIDEBAR ────────────────────────────────────────────────

with st.sidebar:
    st.title("✨ Aura AI")
    st.caption("Built by Rupal Darode")
    st.divider()

    feature = st.selectbox("Choose a feature", [
        "💬 AI Chat",
        "🎨 Image Generator",
        "🖼 Image Analyzer",
        "🌤 Weather",
        "💻 Code Assistant",
    ])

    st.divider()

    is_chat_feature = any(x in feature for x in ["Chat", "Code"])

    if is_chat_feature:
        model_name  = st.selectbox("Model", list(GROQ_MODELS.keys()))
        model_id    = GROQ_MODELS[model_name]
        language    = st.selectbox("Language", list(LANGUAGES.keys()))
        lang_rule   = LANGUAGES[language]
        temperature = st.slider("Creativity", 0.1, 1.0, 0.7)
        max_tokens  = st.slider("Max Tokens", 100, 4000, 1000)

        if st.button("🗑 Clear Chat"):
            for key in ["messages", "pdf_context", "pdf_name"]:
                st.session_state.pop(key, None)
            st.rerun()

        if st.session_state.get("messages"):
            lines = [
                f"{'You' if m['role'] == 'user' else 'Aura'}: {m['content']}"
                for m in st.session_state.messages
                if isinstance(m["content"], str)
            ]
            st.download_button(
                "📥 Export Chat", "\n\n".join(lines),
                file_name=f"aura_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
            )
    else:
        model_id    = GROQ_MODELS["⚡ Llama 3.1 8B  — Fast"]
        lang_rule   = LANGUAGES["English"]
        temperature = 0.7
        max_tokens  = 1000


# ══════════════════════════════════════════════════════════
#  FEATURE 1 — AI CHAT
# ══════════════════════════════════════════════════════════

if "AI Chat" in feature:
    st.header("💬 AI Chat")
    st.caption(f"Model: {model_name}  |  Language: {language}")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if isinstance(msg["content"], str):
                st.markdown(msg["content"])

    # PDF badge
    if st.session_state.get("pdf_context"):
        st.info(f"📄 PDF loaded: {st.session_state.get('pdf_name', 'document.pdf')}")

    # ── INPUT ROW: Mic | Attach | Text Input | Send ──────────────
    # All controls in ONE row using columns
    col_mic, col_attach, col_input, col_send = st.columns([1, 1, 8, 1.2])

    with col_mic:
        # Native Streamlit audio recorder — works in Cloud, no JS tricks
        audio = st.audio_input("🎤", label_visibility="collapsed", key="mic_recorder")

    with col_attach:
        # PDF attach button — toggles the PDF uploader below
        if st.button("📎", help="Attach a PDF"):
            st.session_state.show_pdf = not st.session_state.get("show_pdf", False)

    with col_input:
        typed_input = st.chat_input("Type a message or record with 🎤 …")

    # ── Voice transcription ────────────────────────────────────────
    # When user records audio, transcribe it with Groq Whisper
    voice_input = ""
    if audio is not None:
        # Only process if this is a NEW recording
        audio_bytes = audio.read()
        audio_hash  = hash(audio_bytes)
        if st.session_state.get("last_audio_hash") != audio_hash:
            st.session_state.last_audio_hash = audio_hash
            with st.spinner("🎙 Transcribing your voice..."):
                voice_input = transcribe_audio_groq(audio_bytes)
            if voice_input:
                st.session_state.pending_voice = voice_input
                st.rerun()

    # Retrieve pending voice input after rerun
    if st.session_state.get("pending_voice"):
        voice_input = st.session_state.pop("pending_voice")

    # ── PDF Uploader (shown only when 📎 clicked) ──────────────────
    if st.session_state.get("show_pdf", False):
        with st.container():
            st.caption("📎 Attach a PDF to chat with it")
            pdf_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed", key="pdf_up")
            if pdf_file and st.session_state.get("pdf_name") != pdf_file.name:
                with st.spinner("Reading PDF..."):
                    text = extract_pdf_text(pdf_file)
                if not text.startswith("ERROR"):
                    st.session_state.pdf_context = text
                    st.session_state.pdf_name    = pdf_file.name
                    st.session_state.show_pdf    = False
                    st.success(f"✅ PDF loaded: {pdf_file.name}")
                    st.rerun()
                else:
                    st.error(text)

    # ── Process whichever input arrived ──────────────────────────
    # Priority: typed > voice
    final_input = typed_input or voice_input or None

    if final_input:
        st.session_state.messages.append({"role": "user", "content": final_input})
        with st.chat_message("user"):
            st.markdown(final_input)

        # Build system prompt
        system = f"You are Aura, a helpful and friendly AI assistant. {lang_rule}"
        if st.session_state.get("pdf_context"):
            system += (
                f"\n\nThe user has attached a PDF. Answer from it:\n"
                f"---\n{st.session_state.pdf_context}\n---\n"
                "If the answer isn't in the PDF, say so."
            )

        all_messages = [{"role": "system", "content": system}] + [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
            if isinstance(m["content"], str)
        ]

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = call_groq(all_messages, model_id, temperature, max_tokens)
                st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

        # Text-to-speech — speak the reply
        tts_safe = reply[:500].replace("`", "").replace('"', "'").replace("\n", " ")
        components.html(f"""
<script>
(function() {{
  const u = new SpeechSynthesisUtterance({repr(tts_safe)});
  u.lang = 'en-US'; u.rate = 1.0;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}})();
</script>
""", height=0)


# ══════════════════════════════════════════════════════════
#  FEATURE 2 — IMAGE GENERATOR (Pollinations.ai — FREE)
# ══════════════════════════════════════════════════════════

elif "Image Generator" in feature:
    st.header("🎨 Image Generator")
    st.caption("Powered by Pollinations.ai — completely free, no API key needed!")

    prompt   = st.text_area("Describe your image", placeholder="A sunset over Mumbai skyline, golden hour...")
    col1, col2 = st.columns(2)
    style    = col1.selectbox("Style", list(IMAGE_STYLES.keys()))
    p_model  = col2.selectbox("Model", list(POLLINATIONS_MODELS.keys()))

    if st.button("✨ Generate Image", use_container_width=True):
        if not prompt.strip():
            st.warning("Please describe your image first.")
        else:
            full_prompt = prompt.strip() + IMAGE_STYLES[style]
            with st.spinner("Generating image... (5–15 seconds)"):
                image = generate_image_pollinations(full_prompt, POLLINATIONS_MODELS[p_model])
                if image:
                    st.image(image, use_container_width=True)
                    buf = BytesIO()
                    image.save(buf, format="PNG")
                    st.download_button(
                        "⬇ Download Image", buf.getvalue(),
                        file_name="aura_image.png", mime="image/png",
                        use_container_width=True,
                    )


# ══════════════════════════════════════════════════════════
#  FEATURE 3 — IMAGE ANALYZER (Groq LLaMA Vision — FREE)
# ══════════════════════════════════════════════════════════

elif "Image Analyzer" in feature:
    st.header("🖼 Image Analyzer")
    st.caption("Powered by Groq LLaMA Vision — uses your GROQ_API_KEY, no HF token needed")

    uploaded = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"])

    if not uploaded:
        st.info("📤 Upload an image to get started.")
    else:
        image = Image.open(uploaded)
        st.image(image, use_container_width=True)

        st.markdown("**Quick actions:**")
        c1, c2, c3, c4 = st.columns(4)
        question = ""
        if c1.button("📝 Describe"): question = "Describe this image in detail."
        if c2.button("🎨 Colors"):   question = "What are the main colors in this image?"
        if c3.button("😊 Mood"):     question = "What is the mood or emotion shown?"
        if c4.button("📦 Objects"):  question = "List all objects visible in this image."

        question = st.text_input("Or type your own question:", value=question,
                                 placeholder="What is happening in this image?")

        if st.button("🔍 Analyze", use_container_width=True):
            if not question.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("Analyzing image with AI vision..."):
                    reply = analyze_image_groq(image, question)
                st.success(reply)


# ══════════════════════════════════════════════════════════
#  FEATURE 4 — WEATHER (Open-Meteo, no API key)
# ══════════════════════════════════════════════════════════

elif "Weather" in feature:
    st.header("🌤 Weather")
    st.caption("Real-time weather — no API key needed")

    col1, col2 = st.columns([3, 1])
    city = col1.text_input("Enter a city name", placeholder="Nagpur, Mumbai, Delhi, London...")
    unit = col2.selectbox("Unit", ["Celsius", "Fahrenheit"])

    if st.button("Get Weather", use_container_width=True):
        if not city.strip():
            st.warning("Please enter a city name.")
        else:
            with st.spinner(f"Fetching weather for {city}..."):
                try:
                    # Step 1: Get coordinates
                    geo = requests.get(
                        f"https://geocoding-api.open-meteo.com/v1/search"
                        f"?name={urllib.parse.quote(city.strip())}&count=1",
                        timeout=10,
                    ).json()

                    if not geo.get("results"):
                        st.error(f"❌ '{city}' not found. Try 'Nagpur, India' or 'Delhi, India'.")
                    else:
                        loc       = geo["results"][0]
                        lat, lon  = loc["latitude"], loc["longitude"]
                        city_name = loc.get("name", city)
                        country   = loc.get("country", "")
                        unit_p    = "celsius" if unit == "Celsius" else "fahrenheit"
                        unit_sym  = "°C" if unit == "Celsius" else "°F"

                        # Step 2: Get weather
                        # NOTE: newer Open-Meteo uses 'relative_humidity_2m' (no 'ity' prefix)
                        w = requests.get(
                            f"https://api.open-meteo.com/v1/forecast"
                            f"?latitude={lat}&longitude={lon}"
                            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
                            f"weather_code,wind_speed_10m"
                            f"&temperature_unit={unit_p}"
                            f"&forecast_days=1",
                            timeout=10,
                        ).json()

                        cur      = w.get("current", {})
                        temp     = cur.get("temperature_2m", "N/A")
                        humidity = cur.get("relative_humidity_2m", "N/A")
                        feels    = cur.get("apparent_temperature", "N/A")
                        wind     = cur.get("wind_speed_10m", "N/A")
                        wmo_code = cur.get("weather_code", 0)

                        code_map = {
                            0: "☀️ Clear sky", 1: "🌤 Mainly clear", 2: "⛅ Partly cloudy",
                            3: "☁️ Overcast",  45: "🌫 Foggy",       48: "🌫 Icy fog",
                            51: "🌦 Light drizzle", 61: "🌧 Light rain", 63: "🌧 Moderate rain",
                            65: "🌧 Heavy rain", 71: "🌨 Light snow", 80: "🌦 Rain showers",
                            95: "⛈ Thunderstorm",
                        }
                        condition = code_map.get(wmo_code, f"🌡 Code {wmo_code}")

                        st.subheader(f"📍 {city_name}, {country}")
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("🌡 Temperature", f"{temp}{unit_sym}", f"Feels {feels}{unit_sym}")
                        m2.metric("💧 Humidity",    f"{humidity}%")
                        m3.metric("💨 Wind Speed",  f"{wind} km/h")
                        m4.metric("☁️ Condition",   condition)

                        with st.spinner("Getting AI tip..."):
                            tip = call_groq([
                                {"role": "system", "content": "You are a helpful weather assistant. Give a practical 2-line tip."},
                                {"role": "user", "content": f"Weather in {city_name}: {temp}{unit_sym}, {condition}, humidity {humidity}%. What to wear?"},
                            ], "llama-3.1-8b-instant", 0.7, 200)
                            st.info(f"💡 AI Tip: {tip}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ No internet connection.")
                except requests.exceptions.Timeout:
                    st.error("⏱ Request timed out. Try again.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")


# ══════════════════════════════════════════════════════════
#  FEATURE 5 — CODE ASSISTANT
# ══════════════════════════════════════════════════════════

elif "Code" in feature:
    st.header("💻 Code Assistant")
    st.caption("Write, debug, explain, and convert code")

    action = st.selectbox("What do you need?", [
        "✍️ Write code for me",
        "🐛 Debug my code",
        "📖 Explain this code",
        "🔄 Convert to another language",
        "⚡ Optimize my code",
        "🧪 Write tests for my code",
    ])

    col1, col2 = st.columns(2)
    lang        = col1.selectbox("Language", ["Python", "JavaScript", "Java", "C++", "SQL", "HTML/CSS", "React", "Other"])
    target_lang = col2.selectbox("Convert TO", ["Python", "JavaScript", "Java", "C++", "SQL"]) if "Convert" in action else None

    user_code = st.text_area("Paste your code or describe what you want", height=200,
                             placeholder="e.g. Write a function to check if a number is prime")

    if st.button("🚀 Run", use_container_width=True):
        if not user_code.strip():
            st.warning("Please enter code or a description.")
        else:
            with st.spinner("Processing..."):
                prompts = {
                    "✍️ Write code for me":           f"Write clean, well-commented {lang} code for: {user_code}. Include example usage.",
                    "🐛 Debug my code":               f"Debug this {lang} code and explain all issues:\n\n{user_code}",
                    "📖 Explain this code":           f"Explain this {lang} code step by step in simple terms:\n\n{user_code}",
                    "🔄 Convert to another language":  f"Convert this {lang} code to {target_lang}:\n\n{user_code}",
                    "⚡ Optimize my code":            f"Optimize this {lang} code for better performance:\n\n{user_code}",
                    "🧪 Write tests for my code":     f"Write comprehensive unit tests for this {lang} code:\n\n{user_code}",
                }
                reply = call_groq(
                    [
                        {"role": "system", "content": "You are an expert programmer. Provide clean, working code with clear explanations. Use markdown code blocks."},
                        {"role": "user",   "content": prompts[action]},
                    ],
                    model_id, temperature=0.3, max_tokens=max_tokens,
                )
                st.markdown(reply)
                st.download_button("📥 Download", reply, file_name="aura_code.txt", mime="text/plain")
