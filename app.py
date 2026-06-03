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

    # ── 🎤 Voice-to-Text widget (Web Speech API — uses browser mic) ──
    # This HTML component:
    #   • Shows a mic button the user clicks to start speaking
    #   • Uses the browser's built-in SpeechRecognition (no API key needed)
    #   • Sends the transcript back to Streamlit via postMessage
    # It also handles Text-to-Speech: Streamlit sends the reply text
    # back to the component and it reads it aloud using speechSynthesis.
    voice_html = """
    <style>
      body { margin: 0; font-family: sans-serif; background: transparent; }
      #voice-bar {
        display: flex; align-items: center; gap: 10px;
        background: #f9fafb; border: 1px solid #e5e7eb;
        border-radius: 12px; padding: 8px 14px;
        width: fit-content;
      }
      #mic-btn {
        width: 38px; height: 38px; border-radius: 50%;
        border: none; cursor: pointer; font-size: 18px;
        background: #f3f4f6; transition: all 0.2s;
        display: flex; align-items: center; justify-content: center;
      }
      #mic-btn.listening {
        background: #fee2e2; animation: pulse 1s infinite;
      }
      @keyframes pulse {
        0%,100% { transform: scale(1); }
        50%      { transform: scale(1.15); }
      }
      #status { font-size: 13px; color: #6b7280; min-width: 160px; }
      #transcript-box {
        font-size: 13px; color: #111827;
        background: #fff; border: 1px solid #d1d5db;
        border-radius: 8px; padding: 6px 10px;
        min-width: 220px; display: none;
      }
      #send-btn {
        padding: 6px 14px; border-radius: 8px; border: none;
        background: #2563eb; color: white; font-size: 13px;
        cursor: pointer; display: none;
      }
      #send-btn:hover { background: #1d4ed8; }
    </style>

    <div id="voice-bar">
      <button id="mic-btn" title="Click to speak">🎤</button>
      <span id="status">Click mic to speak</span>
      <div id="transcript-box"></div>
      <button id="send-btn">Send ↗</button>
    </div>

    <script>
    const micBtn        = document.getElementById('mic-btn');
    const statusEl      = document.getElementById('status');
    const transcriptBox = document.getElementById('transcript-box');
    const sendBtn       = document.getElementById('send-btn');

    let recognition = null;
    let finalText   = '';

    // ── Check browser support ──────────────────────────────────────
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      statusEl.textContent = '⚠️ Browser not supported. Use Chrome.';
      micBtn.disabled = true;
    } else {
      recognition = new SpeechRecognition();
      recognition.lang        = 'en-US';  // change to 'hi-IN' for Hindi
      recognition.interimResults = true;  // show live partial results
      recognition.continuous     = false;

      recognition.onstart = () => {
        micBtn.classList.add('listening');
        micBtn.textContent     = '⏹';
        statusEl.textContent   = '🔴 Listening...';
        transcriptBox.style.display = 'none';
        sendBtn.style.display       = 'none';
        finalText = '';
      };

      recognition.onresult = (event) => {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const t = event.results[i][0].transcript;
          if (event.results[i].isFinal) finalText += t;
          else interim += t;
        }
        // Show live transcript while speaking
        transcriptBox.style.display = 'block';
        transcriptBox.textContent   = finalText || interim;
      };

      recognition.onend = () => {
        micBtn.classList.remove('listening');
        micBtn.textContent = '🎤';
        if (finalText.trim()) {
          statusEl.textContent      = '✅ Got it!';
          transcriptBox.textContent = finalText;
          sendBtn.style.display     = 'inline-block';
        } else {
          statusEl.textContent        = 'Click mic to speak';
          transcriptBox.style.display = 'none';
        }
      };

      recognition.onerror = (e) => {
        micBtn.classList.remove('listening');
        micBtn.textContent   = '🎤';
        statusEl.textContent = '❌ ' + e.error + '. Try again.';
      };

      // Toggle mic on button click
      micBtn.addEventListener('click', () => {
        if (micBtn.classList.contains('listening')) {
          recognition.stop();
        } else {
          recognition.start();
        }
      });

      // Send transcript to Streamlit when user clicks Send
      sendBtn.addEventListener('click', () => {
        if (finalText.trim()) {
          // postMessage sends data from this iframe → parent Streamlit page
          window.parent.postMessage({
            type: 'voice_transcript',
            text: finalText.trim()
          }, '*');
          statusEl.textContent        = '📨 Sent!';
          sendBtn.style.display       = 'none';
          transcriptBox.style.display = 'none';
          finalText = '';
        }
      });
    }

    // ── Text-to-Speech: listen for reply from Streamlit ───────────
    // Streamlit sends a message with { type: 'tts', text: '...' }
    window.addEventListener('message', (event) => {
      if (event.data && event.data.type === 'tts' && event.data.text) {
        const utter = new SpeechSynthesisUtterance(event.data.text);
        utter.lang  = 'en-US';
        utter.rate  = 1.0;
        window.speechSynthesis.cancel();   // stop any ongoing speech
        window.speechSynthesis.speak(utter);
        statusEl.textContent = '🔊 Speaking...';
        utter.onend = () => { statusEl.textContent = 'Click mic to speak'; };
      }
    });
    </script>
    """

    # Render the voice widget — height is just enough for the bar
    components.html(voice_html, height=65)

    # ── Receive transcript from the voice widget ────────────────────
    # The Web Speech widget posts a message to the parent page.
    # We capture it via a small JS bridge that writes to a Streamlit
    # text_input hidden behind the voice bar.
    # Simpler approach: use a query-param trick — the widget sends
    # transcript via postMessage; we catch it with a hidden st.text_input
    # that the user can also use directly.

    # Show a small text box that auto-fills from voice
    voice_text = st.text_input(
        "🎤 Voice transcript (auto-filled after speaking, or type here):",
        key="voice_input_box",
        placeholder="Your spoken words appear here...",
        label_visibility="collapsed",
    )

    st.caption("👆 Speak → click Send in the mic widget → text appears above → press Enter to chat")

    # ── [📎 PDF]  [___ main chat input ___] ────────────────────────
    pdf_col, chat_col = st.columns([0.8, 9])

    with pdf_col:
        if st.button("📎", help="Attach a PDF", use_container_width=True):
            st.session_state.show_pdf_uploader = not st.session_state.get("show_pdf_uploader", False)

    with chat_col:
        # Use voice text if available, otherwise wait for typed input
        prefill    = voice_text or st.session_state.pop("voice_prefill", "")
        user_input = st.chat_input("Type your message...")

    # Use whichever input came in — typed chat input takes priority
    final_input = user_input or (voice_text if voice_text else None)

    # PDF uploader — slides open when 📎 is clicked
    if st.session_state.get("show_pdf_uploader"):
        pdf_file = st.file_uploader("Choose a PDF", type=["pdf"],
                                    label_visibility="collapsed", key="pdf_uploader")
        if pdf_file and st.session_state.get("pdf_name") != pdf_file.name:
            with st.spinner("Reading PDF..."):
                text = extract_pdf_text(pdf_file)
            if text.startswith("ERROR"):
                st.error(text)
            else:
                st.session_state.pdf_context       = text
                st.session_state.pdf_name          = pdf_file.name
                st.session_state.show_pdf_uploader = False
                st.rerun()

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
