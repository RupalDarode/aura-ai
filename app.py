import streamlit as st
import streamlit.components.v1 as components
import requests
from io import BytesIO
from PIL import Image
import urllib.parse
import base64
import io
import PyPDF2
from datetime import datetime

st.set_page_config(page_title="Aura AI", page_icon="✨", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f9fafb; }
    section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e5e7eb; }
    .stChatMessage { background-color: #ffffff !important; border: 1px solid #e5e7eb; border-radius: 10px; }

    /* ── Inline attachment bar ── */
    /* Hide the default file-uploader UI; we only show the clickable label */
    .attachment-zone [data-testid="stFileUploader"] {
        display: flex; align-items: center; gap: 0;
    }
    .attachment-zone [data-testid="stFileUploaderDropzone"] {
        display: none !important;           /* hide the big drag-drop box */
    }
    .attachment-zone [data-testid="stFileUploaderDropzoneInstructions"] {
        display: none !important;
    }
    /* Make the browse button look like a small icon button */
    .attachment-zone [data-testid="stFileUploaderDropzone"] + div button,
    .attachment-zone button[kind="secondary"] {
        background: transparent !important;
        border: none !important;
        padding: 6px 10px !important;
        font-size: 20px !important;
        color: #6b7280 !important;
        cursor: pointer;
        border-radius: 8px;
        transition: background 0.15s;
    }
    .attachment-zone button[kind="secondary"]:hover {
        background: #f3f4f6 !important;
        color: #111827 !important;
    }
    /* Pill badge showing active attachment */
    .attach-badge {
        display: inline-flex; align-items: center; gap: 6px;
        background: #eff6ff; border: 1px solid #bfdbfe;
        border-radius: 999px; padding: 3px 10px;
        font-size: 12px; color: #1d4ed8; margin-bottom: 6px;
    }
    .attach-badge button {
        background: none; border: none; cursor: pointer;
        font-size: 13px; color: #6b7280; padding: 0 2px;
        line-height: 1;
    }
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ──────────────────────────────────────────────────────────────────

GROQ_MODELS = {
    "⚡ Llama 3.1 8B  — Fast":      "llama-3.1-8b-instant",
    "🧠 Llama 3.3 70B — Smart":     "llama-3.3-70b-versatile",
    "💎 Mixtral 8x7B  — Balanced":  "mixtral-8x7b-32768",
    "🔬 Gemma 2 9B    — Google":    "gemma2-9b-it",
    "🚀 DeepSeek R1   — Reasoning": "deepseek-r1-distill-llama-70b",
}

# Free Hugging Face image generation models
HF_IMAGE_MODELS = {
    "Stable Diffusion XL":   "stabilityai/stable-diffusion-xl-base-1.0",
    "Stable Diffusion 2.1":  "stabilityai/stable-diffusion-2-1",
    "Dreamlike Photoreal 2": "dreamlike-art/dreamlike-photoreal-2.0",
}

LANGUAGES = {
    "English":  "Always respond in English.",
    "Hindi":    "Hamesha Hindi mein jawab do.",
    "Hinglish": "Hinglish mein jawab do — Hindi aur English mix karke.",
    "Marathi":  "Marathi madhe uttar dya.",
}

IMAGE_STYLES = {
    "None":          "",
    "Realistic":     ", ultra realistic, photographic, 8k",
    "Anime":         ", anime style, vibrant, Studio Ghibli",
    "Oil Painting":  ", oil painting, detailed brushwork",
    "Cyberpunk":     ", cyberpunk, neon lights, futuristic",
    "Watercolor":    ", watercolor, soft colors, artistic",
    "Sketch":        ", pencil sketch, hand drawn",
}


# ── HELPER: GROQ (text AI) ─────────────────────────────────────────────────────

def call_groq(messages, model, temperature=0.7, max_tokens=1000):
    """Send messages to Groq and return reply string."""
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
        return f"❌ Unexpected response: {data}"
    except requests.exceptions.Timeout:
        return "⏱ Request timed out. Please try again."
    except Exception as e:
        return f"❌ Error: {str(e)}"


# ── HELPER: HF IMAGE GENERATION ───────────────────────────────────────────────

def generate_image_hf(prompt, model_id):
    """Call Hugging Face Inference API. Returns PIL Image or None."""
    try:
        hf_token = st.secrets["HF_TOKEN"]
    except Exception:
        st.error("❌ HF_TOKEN missing. Add your Hugging Face token in Streamlit Secrets.")
        return None

    url = f"https://api-inference.huggingface.co/models/{model_id}"
    try:
        res = requests.post(
            url,
            headers={"Authorization": f"Bearer {hf_token}"},
            json={"inputs": prompt},
            timeout=60,
        )
        if res.status_code == 200:
            return Image.open(BytesIO(res.content))
        elif res.status_code == 503:
            st.warning("⏳ Model is loading on Hugging Face — wait 20 seconds and try again.")
        else:
            st.error(f"❌ HF Error {res.status_code}: {res.text[:200]}")
        return None
    except Exception as e:
        st.error(f"❌ Image generation failed: {e}")
        return None


# ── HELPER: HF IMAGE CAPTIONING (BLIP) ────────────────────────────────────────

def analyze_image_hf(image: Image.Image) -> str:
    """Use HF BLIP to caption an image. Returns string."""
    try:
        hf_token = st.secrets["HF_TOKEN"]
    except Exception:
        return "❌ HF_TOKEN missing."

    buf = BytesIO()
    image.save(buf, format="PNG")

    try:
        res = requests.post(
            "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large",
            headers={"Authorization": f"Bearer {hf_token}"},
            data=buf.getvalue(),
            timeout=30,
        )
        if res.status_code == 200:
            result = res.json()
            if isinstance(result, list) and result:
                return result[0].get("generated_text", "No caption returned.")
            return str(result)
        elif res.status_code == 503:
            return "⏳ Vision model is loading. Try again in 20 seconds."
        return f"❌ HF Error {res.status_code}: {res.text[:200]}"
    except Exception as e:
        return f"❌ Error: {e}"


# ── HELPER: PDF TEXT EXTRACTION ────────────────────────────────────────────────

def extract_pdf_text(pdf_file) -> str:
    """Read PDF and return extracted text (max 8000 chars)."""
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

    feature = st.selectbox("Choose a feature", [
        "💬 AI Chat",
        "🎨 Image Generator",
        "🖼 Image Analyzer",
        "🌤 Weather",
        "💻 Code Assistant",
    ])

    st.divider()

    # Show model/language settings only for chat-based features
    is_chat = any(x in feature for x in ["Chat", "Code"])

    if is_chat:
        model_name  = st.selectbox("Model", list(GROQ_MODELS.keys()))
        model_id    = GROQ_MODELS[model_name]
        language    = st.selectbox("Language", list(LANGUAGES.keys()))
        lang_rule   = LANGUAGES[language]
        temperature = st.slider("Creativity", 0.1, 1.0, 0.7)
        max_tokens  = st.slider("Max Tokens", 100, 4000, 1000)

        if st.button("🗑 Clear Chat"):
            st.session_state.pop("messages", None)
            st.session_state.pop("pdf_context", None)
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
        # Safe defaults so variables exist throughout the script
        model_id    = GROQ_MODELS["⚡ Llama 3.1 8B  — Fast"]
        lang_rule   = LANGUAGES["English"]
        temperature = 0.7
        max_tokens  = 1000


# ── FEATURE 1: AI CHAT (with PDF attachment + voice) ──────────────────────────

if "AI Chat" in feature:
    st.header("💬 AI Chat")
    if is_chat:
        st.caption(f"Model: {model_name}  |  Language: {language}")

    # ── Message history ─────────────────────────────────────────────
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            content = msg["content"]
            if isinstance(content, str):
                st.markdown(content)

    # ── PDF badge (shown when a PDF is attached) ────────────────────
    if st.session_state.get("pdf_context"):
        pdf_name = st.session_state.get("pdf_name", "document.pdf")
        st.markdown(f'<div class="attach-badge">📄 {pdf_name} — PDF loaded</div>', unsafe_allow_html=True)

    # ── Compact input row: [📎] [🎤 mic widget] [──── chat input ────] ──
    # The mic widget is a tiny inline HTML component — just the icon button.
    # When clicked: it records → shows transcript inside the widget →
    # user clicks ✅ → text drops into the voice_text box below →
    # pressing Enter sends it. TTS reads replies aloud automatically.

    left_col, right_col = st.columns([2.2, 8])

    with left_col:
        # Single HTML component holds BOTH 📎 and 🎤 as small icon buttons
        # side by side — compact, no extra rows
        components.html("""
<style>
  body { margin:0; padding:0; background:transparent; }
  .bar {
    display: flex; align-items: center; gap: 6px;
    padding: 4px 0;
  }
  .icon-btn {
    width: 36px; height: 36px; border-radius: 50%;
    border: 1px solid #e5e7eb; background: #f9fafb;
    font-size: 16px; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.15s;
  }
  .icon-btn:hover { background: #f3f4f6; }
  .icon-btn.listening { background: #fee2e2; animation: pulse 1s infinite; }
  @keyframes pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.13)} }
  .tooltip {
    font-size: 11px; color: #9ca3af;
    white-space: nowrap; display: none;
  }
  .bar:has(#mic-btn.listening) .tooltip { display: inline; color: #ef4444; }
</style>

<div class="bar">

  <!-- 📎 PDF button — triggers file input -->
  <label for="pdf-input" class="icon-btn" title="Attach PDF">📎</label>
  <input id="pdf-input" type="file" accept=".pdf"
         style="display:none"
         onchange="sendPdf(this)">

  <!-- 🎤 Mic button -->
  <button id="mic-btn" class="icon-btn" title="Speak a message">🎤</button>

  <span class="tooltip" id="tip">Listening…</span>
</div>

<script>
// ── PDF: read file → send base64 to Streamlit via postMessage ───
function sendPdf(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    window.parent.postMessage({
      type: 'pdf_upload',
      name: file.name,
      data: reader.result   // data:application/pdf;base64,...
    }, '*');
  };
  reader.readAsDataURL(file);
}

// ── Mic: Web Speech API ─────────────────────────────────────────
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
const micBtn = document.getElementById('mic-btn');
const tip    = document.getElementById('tip');

if (!SR) {
  micBtn.title = 'Not supported — use Chrome';
  micBtn.style.opacity = '0.4';
} else {
  const rec = new SR();
  rec.lang           = 'en-US';
  rec.interimResults = true;
  rec.continuous     = false;

  let finalText = '';

  rec.onstart  = () => { micBtn.classList.add('listening'); micBtn.textContent='⏹'; finalText=''; };
  rec.onresult = (e) => {
    let interim = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const t = e.results[i][0].transcript;
      e.results[i].isFinal ? finalText += t : interim += t;
    }
    tip.textContent = finalText || interim;
    tip.style.display = 'inline';
  };
  rec.onend = () => {
    micBtn.classList.remove('listening');
    micBtn.textContent = '🎤';
    if (finalText.trim()) {
      window.parent.postMessage({ type: 'voice_transcript', text: finalText.trim() }, '*');
      tip.textContent = '✅ Sent!';
      setTimeout(() => { tip.style.display='none'; tip.textContent='Listening…'; }, 1500);
    } else {
      tip.style.display = 'none';
    }
  };
  rec.onerror = (e) => {
    micBtn.classList.remove('listening');
    micBtn.textContent = '🎤';
    tip.textContent = '❌ ' + e.error;
    tip.style.display = 'inline';
  };

  micBtn.addEventListener('click', () => {
    micBtn.classList.contains('listening') ? rec.stop() : rec.start();
  });
}

// ── TTS: speak Aura's reply when Streamlit sends it ────────────
window.addEventListener('message', (e) => {
  if (e.data?.type === 'tts' && e.data.text) {
    const u = new SpeechSynthesisUtterance(e.data.text);
    u.lang = 'en-US'; u.rate = 1.0;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  }
});
</script>
""", height=48)

    with right_col:
        user_input = st.chat_input("Type or use the mic…")

    # Voice transcript arrives as a query param written by postMessage.
    # We capture it with a hidden text_input that the JS widget fills.
    voice_text = st.text_input("voice", key="voice_input_box",
                               label_visibility="collapsed",
                               placeholder="Voice transcript appears here — press Enter to send")

    # PDF uploader triggered by 📎 click (postMessage can't directly trigger
    # Streamlit file dialogs, so we keep a fallback native uploader hidden
    # behind a toggle — the HTML label+input above handles it in-browser)
    if st.session_state.get("show_pdf_uploader"):
        pdf_file = st.file_uploader("PDF", type=["pdf"],
                                    label_visibility="collapsed", key="pdf_uploader")
        if pdf_file and st.session_state.get("pdf_name") != pdf_file.name:
            with st.spinner("Reading PDF..."):
                text = extract_pdf_text(pdf_file)
            if not text.startswith("ERROR"):
                st.session_state.pdf_context       = text
                st.session_state.pdf_name          = pdf_file.name
                st.session_state.show_pdf_uploader = False
                st.rerun()
            else:
                st.error(text)

    # Pick whichever input arrived — typed chat takes priority over voice box
    final_input = user_input or (voice_text.strip() if voice_text else None)

    if final_input:
        st.session_state.messages.append({"role": "user", "content": final_input})
        with st.chat_message("user"):
            st.markdown(final_input)

        # Build system prompt — include PDF if attached
        system = f"You are Aura, a helpful and friendly AI assistant. {lang_rule}"
        if st.session_state.get("pdf_context"):
            system += (
                f"\n\nThe user has attached a PDF. Answer questions based on it:\n\n"
                f"---\n{st.session_state.pdf_context}\n---\n"
                f"If the answer is not in the PDF, say so."
            )

        full_messages = [{"role": "system", "content": system}] + [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = call_groq(full_messages, model_id, temperature, max_tokens)
                st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

        # ── Text-to-Speech: send reply to the voice widget to read aloud ──
        # We inject a tiny script that posts the reply text to our iframe
        tts_script = f"""
        <script>
        // Find our voice component iframe and send it the reply text
        const iframes = window.parent.document.querySelectorAll('iframe');
        iframes.forEach(iframe => {{
            try {{
                iframe.contentWindow.postMessage({{
                    type: 'tts',
                    text: {repr(reply[:500])}
                }}, '*');
            }} catch(e) {{}}
        }});
        </script>
        """
        components.html(tts_script, height=0)


# ── FEATURE 2: IMAGE GENERATOR (Hugging Face) ─────────────────────────────────

elif "Image Generator" in feature:
    st.header("🎨 Image Generator")
    st.caption("Powered by Hugging Face — needs HF_TOKEN in secrets")

    prompt = st.text_area("Describe your image", placeholder="A sunset over Mumbai skyline, golden hour...")

    col1, col2 = st.columns(2)
    style     = col1.selectbox("Style", list(IMAGE_STYLES.keys()))
    hf_model  = col2.selectbox("Model", list(HF_IMAGE_MODELS.keys()))

    if st.button("✨ Generate Image", use_container_width=True):
        if not prompt.strip():
            st.warning("Please enter a prompt first.")
        else:
            with st.spinner("Generating... (may take 20–40 seconds on first run)"):
                image = generate_image_hf(prompt + IMAGE_STYLES[style], HF_IMAGE_MODELS[hf_model])
                if image:
                    st.image(image, use_container_width=True)
                    buf = BytesIO()
                    image.save(buf, format="PNG")
                    st.download_button("⬇ Download Image", buf.getvalue(),
                                       file_name="aura_image.png", mime="image/png",
                                       use_container_width=True)


# ── FEATURE 3: IMAGE ANALYZER (HF BLIP + Groq) ────────────────────────────────

elif "Image Analyzer" in feature:
    st.header("🖼 Image Analyzer")
    st.caption("Uses Hugging Face BLIP to read the image, then Groq to answer your question")

    uploaded = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"])

    if not uploaded:
        st.info("Upload an image to get started.")
    else:
        image = Image.open(uploaded)
        st.image(image, use_container_width=True)

        st.markdown("**Quick actions:**")
        c1, c2, c3, c4 = st.columns(4)
        question = ""
        if c1.button("📝 Describe"):  question = "Describe this image in detail."
        if c2.button("🎨 Colors"):    question = "What are the main colors?"
        if c3.button("😊 Mood"):      question = "What is the mood or emotion?"
        if c4.button("📦 Objects"):   question = "List all objects in the image."

        question = st.text_input("Or type your own question:", value=question,
                                 placeholder="What is happening in this image?")

        if st.button("🔍 Analyze", use_container_width=True):
            if not question:
                st.warning("Please enter a question.")
            else:
                with st.spinner("Step 1 — Reading image with BLIP vision model..."):
                    caption = analyze_image_hf(image)   # real image understanding

                with st.spinner("Step 2 — Generating detailed answer..."):
                    messages = [
                        {"role": "system", "content": "You are an expert image analyst. A vision model has described the image. Use that description to answer the user's question thoroughly."},
                        {"role": "user",   "content": f"Vision model description: '{caption}'\n\nUser question: {question}"},
                    ]
                    reply = call_groq(messages, "llama-3.3-70b-versatile", 0.3, 1000)
                    st.success(reply)
                    st.caption(f"🤖 Raw vision caption: {caption}")


# ── FEATURE 4: WEATHER ─────────────────────────────────────────────────────────

elif "Weather" in feature:
    st.header("🌤 Weather")
    st.caption("Real-time weather — no API key needed")

    col1, col2 = st.columns([3, 1])
    city = col1.text_input("Enter a city name", placeholder="Nagpur, Mumbai, Delhi...")
    unit = col2.selectbox("Unit", ["Celsius", "Fahrenheit"])

    if st.button("Get Weather", use_container_width=True):
        if not city.strip():
            st.warning("Please enter a city name.")
        else:
            with st.spinner("Fetching weather..."):
                try:
                    # Step 1: Get coordinates for the city
                    geo_data = requests.get(
                        f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1",
                        timeout=10,
                    ).json()

                    if not geo_data.get("results"):
                        st.error("City not found. Try a different spelling.")
                    else:
                        loc        = geo_data["results"][0]
                        lat, lon   = loc["latitude"], loc["longitude"]
                        city_name  = loc.get("name", city)
                        country    = loc.get("country", "")
                        unit_param = "celsius" if unit == "Celsius" else "fahrenheit"
                        unit_sym   = "°C" if unit == "Celsius" else "°F"

                        # Step 2: Fetch weather — use 'current_weather' (not 'current')
                        # Also fetch hourly humidity and feels-like for the current hour
                        w_data = requests.get(
                            f"https://api.open-meteo.com/v1/forecast?"
                            f"latitude={lat}&longitude={lon}"
                            f"&current_weather=true"
                            f"&hourly=relativehumidity_2m,apparent_temperature"
                            f"&temperature_unit={unit_param}&forecast_days=1",
                            timeout=10,
                        ).json()

                        # 'current_weather' is the top-level key returned by this API
                        cw       = w_data.get("current_weather", {})
                        temp     = cw.get("temperature", "N/A")
                        wind     = cw.get("windspeed", "N/A")
                        wmo_code = cw.get("weathercode", 0)

                        # Hourly arrays — index 0 is the first hour of today
                        hourly   = w_data.get("hourly", {})
                        humidity = hourly.get("relativehumidity_2m", ["N/A"])[0]
                        feels    = hourly.get("apparent_temperature",  ["N/A"])[0]

                        # WMO weather code → emoji label
                        code_map = {
                            0: "☀️ Clear sky",      1: "🌤 Mainly clear",   2: "⛅ Partly cloudy",
                            3: "☁️ Overcast",       45: "🌫 Foggy",         48: "🌫 Icy fog",
                            51: "🌦 Light drizzle", 61: "🌧 Light rain",    63: "🌧 Moderate rain",
                            65: "🌧 Heavy rain",    71: "🌨 Light snow",    80: "🌦 Rain showers",
                            95: "⛈ Thunderstorm",
                        }
                        condition = code_map.get(wmo_code, "🌡 Unknown")

                        st.subheader(f"{city_name}, {country}")
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Temperature", f"{temp}{unit_sym}", f"Feels {feels}{unit_sym}")
                        m2.metric("Humidity",    f"{humidity}%")
                        m3.metric("Wind Speed",  f"{wind} km/h")
                        m4.metric("Condition",   condition)

                        with st.spinner("Getting AI tip..."):
                            tip = call_groq([
                                {"role": "system", "content": "Helpful weather assistant. Give a practical 2-line tip."},
                                {"role": "user",   "content": f"Weather in {city_name}: {temp}{unit_sym}, {condition}, humidity {humidity}%. What should I wear or do?"},
                            ], "llama-3.1-8b-instant", 0.7, 200)
                            st.info(f"💡 AI Tip: {tip}")

                except Exception as e:
                    st.error(f"Something went wrong: {e}")


# ── FEATURE 5: CODE ASSISTANT ──────────────────────────────────────────────────

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
    target_lang = col2.selectbox("Convert TO", ["Python", "JavaScript", "Java", "C++", "SQL", "HTML/CSS", "React", "Other"]) if "Convert" in action else None

    user_code = st.text_area("Describe what you want or paste your code here", height=200,
                             placeholder="e.g. Write a function to check if a number is prime")

    if st.button("🚀 Run", use_container_width=True):
        if not user_code.strip():
            st.warning("Please enter some code or a description.")
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
                messages = [
                    {"role": "system", "content": "You are an expert programmer. Provide clean, working code with clear explanations. Use markdown code blocks."},
                    {"role": "user",   "content": prompts[action]},
                ]
                reply = call_groq(messages, model_id, temperature=0.3, max_tokens=max_tokens)
                st.markdown(reply)
                st.download_button("📥 Download", reply, file_name="aura_code.txt", mime="text/plain")
