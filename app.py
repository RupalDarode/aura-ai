# ============================================================
#  Aura AI — Streamlit App
#  Built by Rupal Darode
#  Features: AI Chat (with voice), Image Generator,
#            Image Analyzer, Weather, Code Assistant
# ============================================================
#
#  HOW TO ADD YOUR TOKENS (Streamlit Secrets):
#  1. Open your app on Streamlit Cloud
#  2. Click "Settings" → "Secrets"
#  3. Paste the following (replace with your real keys):
#
#     GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxx"
#     HF_TOKEN     = "hf_xxxxxxxxxxxxxxxxxxxx"
#
#  Get GROQ key : https://console.groq.com/keys
#  Get HF token : https://huggingface.co/settings/tokens
# ============================================================

import io
from datetime import datetime

import PyPDF2
import requests
import streamlit as st
import streamlit.components.v1 as components
import urllib.parse
from io import BytesIO
from PIL import Image

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Aura AI", page_icon="✨", layout="wide")

# ── BASIC STYLING ──────────────────────────────────────────────────────────────

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
  .attach-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #eff6ff; border: 1px solid #bfdbfe;
    border-radius: 999px; padding: 3px 10px;
    font-size: 12px; color: #1d4ed8; margin-bottom: 6px;
  }
</style>
""", unsafe_allow_html=True)


# ── CONSTANTS ──────────────────────────────────────────────────────────────────

# Groq LLM models (free, fast, no sign-up needed beyond API key)
GROQ_MODELS = {
    "⚡ Llama 3.1 8B  — Fast":      "llama-3.1-8b-instant",
    "🧠 Llama 3.3 70B — Smart":     "llama-3.3-70b-versatile",
    "💎 Mixtral 8x7B  — Balanced":  "mixtral-8x7b-32768",
    "🔬 Gemma 2 9B    — Google":    "gemma2-9b-it",
    "🚀 DeepSeek R1   — Reasoning": "deepseek-r1-distill-llama-70b",
}

# Hugging Face image generation models (free tier)
HF_IMAGE_MODELS = {
    "Stable Diffusion XL":   "stabilityai/stable-diffusion-xl-base-1.0",
    "Stable Diffusion 2.1":  "stabilityai/stable-diffusion-2-1",
    "Dreamlike Photoreal 2": "dreamlike-art/dreamlike-photoreal-2.0",
}

# Language instructions for the chatbot
LANGUAGES = {
    "English":  "Always respond in English.",
    "Hindi":    "Hamesha Hindi mein jawab do.",
    "Hinglish": "Hinglish mein jawab do — Hindi aur English mix karke.",
    "Marathi":  "Marathi madhe uttar dya.",
}

# Image style modifiers appended to prompts
IMAGE_STYLES = {
    "None":         "",
    "Realistic":    ", ultra realistic, photographic, 8k",
    "Anime":        ", anime style, vibrant, Studio Ghibli",
    "Oil Painting": ", oil painting, detailed brushwork",
    "Cyberpunk":    ", cyberpunk, neon lights, futuristic",
    "Watercolor":   ", watercolor, soft colors, artistic",
    "Sketch":       ", pencil sketch, hand drawn",
}


# ── HELPER FUNCTIONS ───────────────────────────────────────────────────────────

def call_groq(messages, model, temperature=0.7, max_tokens=1000):
    """
    Send a list of messages to the Groq API and return the reply text.
    messages = [{"role": "user"/"assistant"/"system", "content": "..."}]
    """
    # Check for API key
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        return "❌ GROQ_API_KEY missing. Add it in Streamlit Settings → Secrets."

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=30,
        )
        data = response.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        elif "error" in data:
            return f"❌ Groq Error: {data['error']['message']}"
        return f"❌ Unexpected response: {data}"

    except requests.exceptions.Timeout:
        return "⏱ Request timed out. Please try again."
    except Exception as e:
        return f"❌ Error: {str(e)}"


def generate_image_hf(prompt, model_id):
    """
    Call Hugging Face Inference API to generate an image.
    Returns a PIL Image on success, or None on failure.
    """
    try:
        hf_token = st.secrets["HF_TOKEN"]
    except Exception:
        st.error("❌ HF_TOKEN missing. Add your Hugging Face token in Streamlit Secrets.")
        return None

    url = f"https://api-inference.huggingface.co/models/{model_id}"
    try:
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {hf_token}"},
            json={"inputs": prompt},
            timeout=120,
        )
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        elif response.status_code == 503:
            st.warning("⏳ Model is loading on Hugging Face — wait 20 seconds and try again.")
        else:
            st.error(f"❌ HF Error {response.status_code}: {response.text[:300]}")
        return None
    except Exception as e:
        st.error(f"❌ Image generation failed: {e}")
        return None


def analyze_image_hf(image: Image.Image) -> str:
    """
    Use Hugging Face BLIP model to generate a caption for the image.
    Returns a caption string, or an error message.
    """
    try:
        hf_token = st.secrets["HF_TOKEN"]
    except Exception:
        return "❌ HF_TOKEN missing. Add your Hugging Face token in Streamlit Secrets."

    # Convert image to bytes
    buf = BytesIO()
    image.save(buf, format="PNG")

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large",
            headers={"Authorization": f"Bearer {hf_token}"},
            data=buf.getvalue(),
            timeout=30,
        )
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and result:
                return result[0].get("generated_text", "No caption returned.")
            return str(result)
        elif response.status_code == 503:
            return "⏳ Vision model is loading. Try again in 20 seconds."
        return f"❌ HF Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return f"❌ Error: {e}"


def extract_pdf_text(pdf_file) -> str:
    """
    Read a PDF file and return its text content (max 8000 characters).
    Returns an error string if extraction fails.
    """
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        text = "".join(page.extract_text() or "" for page in reader.pages)
        return text[:8000]
    except Exception as e:
        return f"ERROR: {e}"


# ── SIDEBAR ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("✨ Aura AI")
    st.caption("Built by Rupal Darode")
    st.divider()

    # Main feature selector
    feature = st.selectbox("Choose a feature", [
        "💬 AI Chat",
        "🎨 Image Generator",
        "🖼 Image Analyzer",
        "🌤 Weather",
        "💻 Code Assistant",
    ])

    st.divider()

    # Show AI settings only for text-based features
    is_chat_feature = any(x in feature for x in ["Chat", "Code"])

    if is_chat_feature:
        model_name  = st.selectbox("Model", list(GROQ_MODELS.keys()))
        model_id    = GROQ_MODELS[model_name]
        language    = st.selectbox("Language", list(LANGUAGES.keys()))
        lang_rule   = LANGUAGES[language]
        temperature = st.slider("Creativity", 0.1, 1.0, 0.7)
        max_tokens  = st.slider("Max Tokens", 100, 4000, 1000)

        # Clear chat history
        if st.button("🗑 Clear Chat"):
            st.session_state.pop("messages", None)
            st.session_state.pop("pdf_context", None)
            st.session_state.pop("voice_input", None)
            st.rerun()

        # Export chat as text file
        if st.session_state.get("messages"):
            lines = [
                f"{'You' if m['role'] == 'user' else 'Aura'}: {m['content']}"
                for m in st.session_state.messages
                if isinstance(m["content"], str)
            ]
            st.download_button(
                "📥 Export Chat",
                "\n\n".join(lines),
                file_name=f"aura_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
            )
    else:
        # Safe defaults so these variables always exist
        model_id    = GROQ_MODELS["⚡ Llama 3.1 8B  — Fast"]
        lang_rule   = LANGUAGES["English"]
        temperature = 0.7
        max_tokens  = 1000


# ══════════════════════════════════════════════════════════════
#  FEATURE 1 — AI CHAT (with voice input + PDF attachment)
# ══════════════════════════════════════════════════════════════

if "AI Chat" in feature:
    st.header("💬 AI Chat")
    st.caption(f"Model: {model_name}  |  Language: {language}")

    # Initialize message history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show past messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if isinstance(msg["content"], str):
                st.markdown(msg["content"])

    # Show PDF badge if a PDF is loaded
    if st.session_state.get("pdf_context"):
        pdf_name = st.session_state.get("pdf_name", "document.pdf")
        st.markdown(
            f'<div class="attach-badge">📄 {pdf_name} — PDF loaded</div>',
            unsafe_allow_html=True,
        )

    # ── VOICE INPUT WIDGET ─────────────────────────────────────────────────
    # This HTML component records your voice using the browser's Web Speech API.
    # When you click ✅ Send, it writes the transcript into a Streamlit
    # query parameter (?voice=...) and reloads the page, which Streamlit reads.
    components.html("""
<style>
  body { margin:0; padding:0; font-family: sans-serif; }
  .voice-bar {
    display: flex; align-items: center; gap: 8px; padding: 4px 0;
  }
  button {
    padding: 6px 12px; border-radius: 8px; border: 1px solid #e5e7eb;
    background: #f9fafb; font-size: 14px; cursor: pointer;
  }
  button:hover { background: #f3f4f6; }
  #mic-btn.listening { background: #fee2e2; animation: pulse 1s infinite; }
  @keyframes pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.1)} }
  #transcript {
    flex: 1; font-size: 13px; color: #374151;
    padding: 4px 8px; border-radius: 6px;
    background: #f3f4f6; min-height: 24px;
  }
  #send-btn { background: #3b82f6; color: white; border-color: #2563eb; }
  #send-btn:hover { background: #2563eb; }
  #send-btn:disabled { background: #93c5fd; cursor: default; }
</style>

<div class="voice-bar">
  <button id="mic-btn" title="Click to start/stop recording">🎤 Speak</button>
  <span id="transcript">Press 🎤 Speak, say something, then click ✅ Send</span>
  <button id="send-btn" disabled onclick="sendVoice()">✅ Send</button>
</div>

<script>
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
const micBtn       = document.getElementById('mic-btn');
const transcriptEl = document.getElementById('transcript');
const sendBtn      = document.getElementById('send-btn');

let finalText = '';

if (!SR) {
  // Browser doesn't support Speech Recognition
  micBtn.textContent = '🎤 (Use Chrome)';
  micBtn.disabled = true;
  transcriptEl.textContent = '⚠️ Voice not supported. Use Google Chrome.';
} else {
  const rec = new SR();
  rec.lang           = 'en-US';
  rec.interimResults = true;   // show partial results while speaking
  rec.continuous     = false;

  rec.onstart = () => {
    micBtn.classList.add('listening');
    micBtn.textContent = '⏹ Stop';
    finalText = '';
    transcriptEl.textContent = 'Listening...';
    sendBtn.disabled = true;
  };

  rec.onresult = (event) => {
    let interim = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const text = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalText += text + ' ';
      } else {
        interim += text;
      }
    }
    // Show what was heard so far
    transcriptEl.textContent = (finalText + interim).trim() || 'Listening...';
  };

  rec.onend = () => {
    micBtn.classList.remove('listening');
    micBtn.textContent = '🎤 Speak';
    if (finalText.trim()) {
      transcriptEl.textContent = '✅ Heard: ' + finalText.trim();
      sendBtn.disabled = false;  // enable Send button
    } else {
      transcriptEl.textContent = 'Nothing heard. Try again.';
    }
  };

  rec.onerror = (event) => {
    micBtn.classList.remove('listening');
    micBtn.textContent = '🎤 Speak';
    transcriptEl.textContent = '❌ Error: ' + event.error;
  };

  micBtn.addEventListener('click', () => {
    if (micBtn.classList.contains('listening')) {
      rec.stop();
    } else {
      rec.start();
    }
  });
}

// When user clicks ✅ Send:
// We append the voice text as a URL query param and reload the page.
// Streamlit will then read it from st.query_params.
function sendVoice() {
  const text = finalText.trim();
  if (!text) return;

  // Put the voice text in the URL query string
  const url = new URL(window.parent.location.href);
  url.searchParams.set('voice_input', text);
  window.parent.location.href = url.toString();
}
</script>
""", height=60)

    # ── READ VOICE TEXT FROM URL QUERY PARAM ──────────────────────────────
    # When the voice widget reloads the page with ?voice_input=..., we read it here.
    voice_text = st.query_params.get("voice_input", "")

    # Clear the query param after reading so it doesn't repeat on next rerun
    if voice_text:
        st.query_params.clear()

    # ── PDF UPLOADER ───────────────────────────────────────────────────────
    with st.expander("📎 Attach a PDF (optional)", expanded=False):
        pdf_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
        if pdf_file and st.session_state.get("pdf_name") != pdf_file.name:
            with st.spinner("Reading PDF..."):
                text = extract_pdf_text(pdf_file)
            if not text.startswith("ERROR"):
                st.session_state.pdf_context = text
                st.session_state.pdf_name    = pdf_file.name
                st.success(f"✅ Loaded: {pdf_file.name}")
                st.rerun()
            else:
                st.error(text)

    # ── CHAT INPUT BOX ─────────────────────────────────────────────────────
    typed_input = st.chat_input("Type a message or use the 🎤 Speak button above…")

    # Use voice text if user didn't type anything
    final_input = typed_input or voice_text.strip() or None

    # ── PROCESS INPUT AND GET AI REPLY ────────────────────────────────────
    if final_input:
        # Save user message
        st.session_state.messages.append({"role": "user", "content": final_input})
        with st.chat_message("user"):
            st.markdown(final_input)

        # Build system prompt
        system_prompt = f"You are Aura, a helpful and friendly AI assistant. {lang_rule}"
        if st.session_state.get("pdf_context"):
            system_prompt += (
                f"\n\nThe user has attached a PDF. Use it to answer questions:\n\n"
                f"---\n{st.session_state.pdf_context}\n---\n"
                f"If the answer is not in the PDF, say so."
            )

        # Combine system prompt + full chat history
        all_messages = [{"role": "system", "content": system_prompt}] + [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
            if isinstance(m["content"], str)
        ]

        # Get AI reply
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = call_groq(all_messages, model_id, temperature, max_tokens)
                st.markdown(reply)

        # Save assistant reply
        st.session_state.messages.append({"role": "assistant", "content": reply})

        # ── TEXT-TO-SPEECH: read the reply aloud ──────────────────────────
        # We use a small inline script to speak the reply using the browser's
        # built-in SpeechSynthesis API (no extra packages needed).
        tts_text = reply[:600].replace("`", "").replace('"', "'")
        components.html(f"""
<script>
(function() {{
  const text = {repr(tts_text)};
  const u = new SpeechSynthesisUtterance(text);
  u.lang = 'en-US';
  u.rate = 1.0;
  window.speechSynthesis.cancel();  // stop any previous speech
  window.speechSynthesis.speak(u);
}})();
</script>
""", height=0)


# ══════════════════════════════════════════════════════════════
#  FEATURE 2 — IMAGE GENERATOR (Hugging Face)
# ══════════════════════════════════════════════════════════════

elif "Image Generator" in feature:
    st.header("🎨 Image Generator")
    st.caption("Powered by Hugging Face — needs HF_TOKEN in Streamlit Secrets")

    # Show setup instructions if token is missing
    try:
        st.secrets["HF_TOKEN"]
    except Exception:
        st.info("""
**How to add your Hugging Face token:**

1. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Click **"New token"** → set role to **Read** → copy the token
3. Open your Streamlit app → **Settings** → **Secrets**
4. Add this line:
```
HF_TOKEN = "hf_xxxxxxxxxxxxxxxx"
```
5. Save and rerun the app
""")

    prompt   = st.text_area("Describe your image", placeholder="A sunset over Mumbai skyline, golden hour...")
    col1, col2 = st.columns(2)
    style    = col1.selectbox("Style", list(IMAGE_STYLES.keys()))
    hf_model = col2.selectbox("Model", list(HF_IMAGE_MODELS.keys()))

    if st.button("✨ Generate Image", use_container_width=True):
        if not prompt.strip():
            st.warning("Please describe your image first.")
        else:
            full_prompt = prompt + IMAGE_STYLES[style]
            with st.spinner("Generating image... (may take 20–60 seconds on first run)"):
                image = generate_image_hf(full_prompt, HF_IMAGE_MODELS[hf_model])
                if image:
                    st.image(image, use_container_width=True)
                    # Save image and offer download
                    buf = BytesIO()
                    image.save(buf, format="PNG")
                    st.download_button(
                        "⬇ Download Image",
                        buf.getvalue(),
                        file_name="aura_image.png",
                        mime="image/png",
                        use_container_width=True,
                    )


# ══════════════════════════════════════════════════════════════
#  FEATURE 3 — IMAGE ANALYZER (HF BLIP + Groq)
# ══════════════════════════════════════════════════════════════

elif "Image Analyzer" in feature:
    st.header("🖼 Image Analyzer")
    st.caption("Step 1: Hugging Face BLIP reads the image. Step 2: Groq answers your question.")

    # Show HF token setup hint
    try:
        st.secrets["HF_TOKEN"]
    except Exception:
        st.info("⚠️ HF_TOKEN missing. See Image Generator tab for setup instructions.")

    uploaded = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"])

    if not uploaded:
        st.info("📤 Upload an image to get started.")
    else:
        image = Image.open(uploaded)
        st.image(image, use_container_width=True)

        # Quick action buttons
        st.markdown("**Quick actions:**")
        c1, c2, c3, c4 = st.columns(4)
        question = ""
        if c1.button("📝 Describe"): question = "Describe this image in detail."
        if c2.button("🎨 Colors"):   question = "What are the main colors in this image?"
        if c3.button("😊 Mood"):     question = "What is the mood or emotion in this image?"
        if c4.button("📦 Objects"):  question = "List all the objects visible in this image."

        question = st.text_input(
            "Or type your own question:",
            value=question,
            placeholder="What is happening in this image?",
        )

        if st.button("🔍 Analyze", use_container_width=True):
            if not question.strip():
                st.warning("Please enter a question.")
            else:
                # Step 1: Get image caption from BLIP
                with st.spinner("Step 1 — Reading image with AI vision model..."):
                    caption = analyze_image_hf(image)

                # Step 2: Let Groq answer based on the caption
                with st.spinner("Step 2 — Generating answer..."):
                    messages = [
                        {
                            "role": "system",
                            "content": (
                                "You are an expert image analyst. A vision model has described "
                                "the image. Use that description to answer the user's question thoroughly."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Vision model description: '{caption}'\n\nUser question: {question}",
                        },
                    ]
                    reply = call_groq(messages, "llama-3.3-70b-versatile", 0.3, 1000)

                st.success(reply)
                st.caption(f"🤖 Raw vision caption: {caption}")


# ══════════════════════════════════════════════════════════════
#  FEATURE 4 — WEATHER (Open-Meteo, no API key needed)
# ══════════════════════════════════════════════════════════════

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
                    # Step 1: Convert city name to coordinates
                    geo_url  = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city.strip())}&count=1"
                    geo_data = requests.get(geo_url, timeout=10).json()

                    if not geo_data.get("results"):
                        st.error(
                            f"❌ City '{city}' not found. "
                            "Try a different spelling or add the country (e.g. 'Delhi, India')."
                        )
                    else:
                        loc       = geo_data["results"][0]
                        lat       = loc["latitude"]
                        lon       = loc["longitude"]
                        city_name = loc.get("name", city)
                        country   = loc.get("country", "")
                        unit_param = "celsius" if unit == "Celsius" else "fahrenheit"
                        unit_sym   = "°C" if unit == "Celsius" else "°F"

                        # Step 2: Fetch weather data
                        weather_url = (
                            f"https://api.open-meteo.com/v1/forecast"
                            f"?latitude={lat}&longitude={lon}"
                            f"&current_weather=true"
                            f"&hourly=relativehumidity_2m,apparent_temperature"
                            f"&temperature_unit={unit_param}"
                            f"&forecast_days=1"
                        )
                        w_data = requests.get(weather_url, timeout=10).json()

                        # Parse current weather
                        cw       = w_data.get("current_weather", {})
                        temp     = cw.get("temperature", "N/A")
                        wind     = cw.get("windspeed", "N/A")
                        wmo_code = cw.get("weathercode", 0)

                        # Get humidity and feels-like from hourly (first hour of today)
                        hourly   = w_data.get("hourly", {})
                        humidity = hourly.get("relativehumidity_2m", ["N/A"])[0]
                        feels    = hourly.get("apparent_temperature",  ["N/A"])[0]

                        # Map WMO weather code to emoji + label
                        code_map = {
                            0:  "☀️ Clear sky",       1: "🌤 Mainly clear",
                            2:  "⛅ Partly cloudy",   3: "☁️ Overcast",
                            45: "🌫 Foggy",           48: "🌫 Icy fog",
                            51: "🌦 Light drizzle",   61: "🌧 Light rain",
                            63: "🌧 Moderate rain",   65: "🌧 Heavy rain",
                            71: "🌨 Light snow",      80: "🌦 Rain showers",
                            95: "⛈ Thunderstorm",
                        }
                        condition = code_map.get(wmo_code, f"🌡 Code {wmo_code}")

                        # Display weather metrics
                        st.subheader(f"📍 {city_name}, {country}")
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("🌡 Temperature", f"{temp}{unit_sym}", f"Feels {feels}{unit_sym}")
                        m2.metric("💧 Humidity",    f"{humidity}%")
                        m3.metric("💨 Wind Speed",  f"{wind} km/h")
                        m4.metric("☁️ Condition",   condition)

                        # AI tip
                        with st.spinner("Getting AI tip..."):
                            tip = call_groq(
                                [
                                    {"role": "system", "content": "You are a helpful weather assistant. Give a practical 2-line tip."},
                                    {"role": "user",   "content": f"Weather in {city_name}: {temp}{unit_sym}, {condition}, humidity {humidity}%. What should I wear or do?"},
                                ],
                                "llama-3.1-8b-instant", 0.7, 200,
                            )
                            st.info(f"💡 AI Tip: {tip}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ No internet connection. Please check your network.")
                except requests.exceptions.Timeout:
                    st.error("⏱ Request timed out. Please try again.")
                except Exception as e:
                    st.error(f"❌ Something went wrong: {e}")


# ══════════════════════════════════════════════════════════════
#  FEATURE 5 — CODE ASSISTANT
# ══════════════════════════════════════════════════════════════

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
    lang = col1.selectbox("Language", ["Python", "JavaScript", "Java", "C++", "SQL", "HTML/CSS", "React", "Other"])

    # Only show "Convert TO" if the Convert action is selected
    target_lang = None
    if "Convert" in action:
        target_lang = col2.selectbox("Convert TO", ["Python", "JavaScript", "Java", "C++", "SQL", "HTML/CSS", "React", "Other"])

    user_code = st.text_area(
        "Describe what you want, or paste your code here",
        height=200,
        placeholder="e.g. Write a function to check if a number is prime",
    )

    if st.button("🚀 Run", use_container_width=True):
        if not user_code.strip():
            st.warning("Please enter some code or a description.")
        else:
            with st.spinner("Processing..."):
                # Build the right prompt based on selected action
                prompts = {
                    "✍️ Write code for me":          f"Write clean, well-commented {lang} code for: {user_code}. Include example usage.",
                    "🐛 Debug my code":              f"Debug this {lang} code and explain all issues:\n\n{user_code}",
                    "📖 Explain this code":          f"Explain this {lang} code step by step in simple terms:\n\n{user_code}",
                    "🔄 Convert to another language": f"Convert this {lang} code to {target_lang}:\n\n{user_code}",
                    "⚡ Optimize my code":           f"Optimize this {lang} code for better performance:\n\n{user_code}",
                    "🧪 Write tests for my code":    f"Write comprehensive unit tests for this {lang} code:\n\n{user_code}",
                }

                messages = [
                    {
                        "role": "system",
                        "content": "You are an expert programmer. Provide clean, working code with clear explanations. Use markdown code blocks.",
                    },
                    {"role": "user", "content": prompts[action]},
                ]

                reply = call_groq(messages, model_id, temperature=0.3, max_tokens=max_tokens)
                st.markdown(reply)
                st.download_button(
                    "📥 Download",
                    reply,
                    file_name="aura_code.txt",
                    mime="text/plain",
                )
