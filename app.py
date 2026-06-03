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
    .attach-badge {
        display: inline-flex; align-items: center; gap: 6px;
        background: #eff6ff; border: 1px solid #bfdbfe;
        border-radius: 999px; padding: 3px 10px;
        font-size: 12px; color: #1d4ed8; margin-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────

GROQ_MODELS = {
    "⚡ Llama 3.1 8B  — Fast":      "llama-3.1-8b-instant",
    "🧠 Llama 3.3 70B — Smart":     "llama-3.3-70b-versatile",
    "💎 Mixtral 8x7B  — Balanced":  "mixtral-8x7b-32768",
    "🔬 Gemma 2 9B    — Google":    "gemma2-9b-it",
    "🚀 DeepSeek R1   — Reasoning": "deepseek-r1-distill-llama-70b",
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


# ─────────────────────────────────────────
# HELPER: GROQ TEXT AI
# ─────────────────────────────────────────

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
            json={"model": model, "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens},
            timeout=30,
        )
        data = res.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        elif "error" in data:
            return f"❌ Groq Error: {data['error']['message']}"
        return f"❌ Unexpected: {data}"
    except requests.exceptions.Timeout:
        return "⏱ Request timed out. Please try again."
    except Exception as e:
        return f"❌ Error: {str(e)}"


# ─────────────────────────────────────────
# HELPER: IMAGE GENERATION — Pollinations
# (No API key needed, no blocked domains)
# ─────────────────────────────────────────

def generate_image(prompt: str) -> Image.Image | None:
    """
    Generate image via Pollinations.ai — completely free, no key needed.
    Uses a different subdomain (image.pollinations.ai) which is NOT blocked.
    The old free tier still works when nologo=true is NOT used.
    """
    try:
        encoded = urllib.parse.quote(prompt)
        # Use the simple GET endpoint — no auth, no payment required
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=768&seed=42&model=flux"
        res = requests.get(url, timeout=90)
        if res.status_code == 200 and res.headers.get("content-type", "").startswith("image"):
            return Image.open(BytesIO(res.content))
        else:
            st.error(f"❌ Image service error {res.status_code}. Try a different prompt or style.")
            return None
    except Exception as e:
        st.error(f"❌ Failed to generate image: {e}")
        return None


# ─────────────────────────────────────────
# HELPER: IMAGE ANALYSIS — Groq vision
# Convert image → base64 → send to Groq
# (Works on Streamlit Cloud, no HF needed)
# ─────────────────────────────────────────

def analyze_image_groq(image: Image.Image, question: str) -> str:
    """
    Send image + question to Groq's vision-capable model.
    Groq supports base64 images via the OpenAI-compatible messages format.
    """
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        return "❌ GROQ_API_KEY missing."

    # Resize large images to save tokens (max 1024px on longest side)
    max_px = 1024
    if max(image.size) > max_px:
        ratio = max_px / max(image.size)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image = image.resize(new_size, Image.LANCZOS)

    # Convert to base64 JPEG
    buf = BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                },
                {"type": "text", "text": question},
            ],
        }
    ]

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            # Use the vision model — meta-llama/llama-4-scout-17b-16e-instruct supports images
            json={"model": "meta-llama/llama-4-scout-17b-16e-instruct",
                  "messages": messages, "max_tokens": 1000},
            timeout=30,
        )
        data = res.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        elif "error" in data:
            return f"❌ Groq Vision Error: {data['error']['message']}"
        return f"❌ Unexpected: {data}"
    except Exception as e:
        return f"❌ Error: {e}"


# ─────────────────────────────────────────
# HELPER: PDF TEXT EXTRACTION
# ─────────────────────────────────────────

def extract_pdf_text(pdf_file) -> str:
    """Extract text from a PDF file object (max 8000 chars)."""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        text = "".join(page.extract_text() or "" for page in reader.pages)
        return text[:8000]
    except Exception as e:
        return f"ERROR: {e}"


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────

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
        model_id    = GROQ_MODELS["⚡ Llama 3.1 8B  — Fast"]
        lang_rule   = LANGUAGES["English"]
        temperature = 0.7
        max_tokens  = 1000


# ─────────────────────────────────────────
# FEATURE 1 — AI CHAT
# ─────────────────────────────────────────

if "AI Chat" in feature:
    st.header("💬 AI Chat")
    if is_chat:
        st.caption(f"Model: {model_name}  |  Language: {language}")

    # Message history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if isinstance(msg["content"], str):
                st.markdown(msg["content"])

    # PDF badge
    if st.session_state.get("pdf_context"):
        pdf_name = st.session_state.get("pdf_name", "document.pdf")
        st.markdown(f'<div class="attach-badge">📄 {pdf_name} — PDF loaded</div>',
                    unsafe_allow_html=True)

    # ── Input row: [📎 🎤 icons]  [chat input] ──────────────────────
    left_col, right_col = st.columns([2.2, 8])

    with left_col:
        components.html("""
<style>
  body { margin:0; padding:0; background:transparent; }
  .bar { display:flex; align-items:center; gap:6px; padding:4px 0; }
  .icon-btn {
    width:36px; height:36px; border-radius:50%;
    border:1px solid #e5e7eb; background:#f9fafb;
    font-size:16px; cursor:pointer;
    display:flex; align-items:center; justify-content:center;
    transition:background 0.15s;
  }
  .icon-btn:hover { background:#f3f4f6; }
  .icon-btn.listening { background:#fee2e2; animation:pulse 1s infinite; }
  @keyframes pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.13)} }
  #tip { font-size:11px; color:#9ca3af; white-space:nowrap; display:none; }
</style>
<div class="bar">
  <label for="pdf-input" class="icon-btn" title="Attach PDF">📎</label>
  <input id="pdf-input" type="file" accept=".pdf" style="display:none" onchange="sendPdf(this)">
  <button id="mic-btn" class="icon-btn" title="Speak a message">🎤</button>
  <span id="tip"></span>
</div>
<script>
function sendPdf(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    window.parent.postMessage({ type:'pdf_upload', name:file.name, data:reader.result }, '*');
  };
  reader.readAsDataURL(file);
}
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
const micBtn = document.getElementById('mic-btn');
const tip = document.getElementById('tip');
if (!SR) {
  micBtn.title = 'Use Chrome for voice';
  micBtn.style.opacity = '0.4';
} else {
  const rec = new SR();
  rec.lang = 'en-US';
  rec.interimResults = true;
  rec.continuous = false;
  let finalText = '';
  rec.onstart  = () => { micBtn.classList.add('listening'); micBtn.textContent='⏹'; finalText=''; tip.style.display='none'; };
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
      window.parent.postMessage({ type:'voice_transcript', text:finalText.trim() }, '*');
      tip.textContent = '✅ Sent!';
      setTimeout(() => { tip.style.display='none'; }, 1500);
    } else { tip.style.display='none'; }
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

    # Voice text box — auto-filled after mic sends transcript
    voice_text = st.text_input("voice", key="voice_input_box",
                               label_visibility="collapsed",
                               placeholder="Voice text appears here — press Enter to send")

    # PDF uploader (shown when 📎 icon is clicked in HTML)
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

    final_input = user_input or (voice_text.strip() if voice_text else None)

    if final_input:
        st.session_state.messages.append({"role": "user", "content": final_input})
        with st.chat_message("user"):
            st.markdown(final_input)

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

        # TTS — send reply text to the mic iframe to read aloud
        tts_js = f"""
        <script>
        document.querySelectorAll('iframe').forEach(f => {{
            try {{ f.contentWindow.postMessage({{type:'tts',text:{repr(reply[:400])}}}, '*'); }} catch(e) {{}}
        }});
        </script>"""
        components.html(tts_js, height=0)


# ─────────────────────────────────────────
# FEATURE 2 — IMAGE GENERATOR
# Uses Pollinations.ai — free, no key, not blocked
# ─────────────────────────────────────────

elif "Image Generator" in feature:
    st.header("🎨 Image Generator")
    st.caption("AI generates detailed SVG artwork — no external API, works 100% on Streamlit Cloud")

    prompt = st.text_area("Describe your image",
                          placeholder="A sunset over Mumbai skyline with orange sky and boats...")

    col1, col2 = st.columns(2)
    style = col1.selectbox("Art Style", [
        "Flat Illustration", "Realistic Scene", "Watercolor",
        "Minimalist", "Cyberpunk", "Fantasy Art"
    ])
    color_mood = col2.selectbox("Color Mood", [
        "Vibrant & Colorful", "Warm & Sunset", "Cool & Night",
        "Pastel & Soft", "Dark & Moody", "Black & White"
    ])

    if st.button("✨ Generate Image", use_container_width=True):
        if not prompt.strip():
            st.warning("Please enter a prompt first.")
        else:
            with st.spinner("Generating your artwork with AI..."):

                svg_system = """You are a world-class SVG illustrator. You create stunning, 
photorealistic-looking SVG artwork using advanced SVG techniques.

STRICT RULES:
- Output ONLY raw SVG code. No markdown, no backticks, no explanation whatsoever.
- Start your response with <svg and end with </svg>. Nothing before or after.
- Canvas size: viewBox="0 0 800 600" width="800" height="600"

QUALITY REQUIREMENTS — you MUST use ALL of these techniques:
1. GRADIENTS: Use <linearGradient> and <radialGradient> for skies, water, skin, buildings — never flat colors
2. DEPTH & LAYERS: Draw background → midground → foreground elements in order
3. REALISTIC LIGHTING: Add highlights (lighter stroke/fill) and shadows (darker shapes with opacity)
4. TEXTURES: Use <pattern> or many small shapes to simulate texture (water ripples, grass blades, brick)
5. FINE DETAILS: Windows on buildings, leaves on trees, waves on water, stars in sky — use groups <g>
6. ATMOSPHERIC EFFECTS: Use <filter> with feGaussianBlur for glow, fog, soft shadows
7. REFLECTIONS: Mirror shapes with opacity for water/glass reflections
8. CURVES: Use <path> with bezier curves (C, Q commands) for organic shapes — NOT just rectangles
9. MINIMUM 40 SVG elements for a rich, detailed scene
10. COLORS: Rich, harmonious palette — use specific hex codes, not generic color names"""

                svg_prompt = f"""Create a STUNNING, HIGHLY DETAILED SVG illustration of:
"{prompt}"

Art style: {style}
Color mood: {color_mood}

Scene requirements:
- Draw a complete, layered scene with background, midground, and foreground
- Use realistic gradients for sky/atmosphere
- Add fine details: textures, lighting, shadows, small elements
- Make it look like professional digital art
- Every major element must have gradient fills, not flat colors
- Add atmospheric depth (things further away are lighter/hazier)

Return ONLY the SVG code. Start with <svg viewBox="0 0 800 600" width="800" height="600"..."""

                svg_code = call_groq(
                    [{"role": "system", "content": svg_system},
                     {"role": "user", "content": svg_prompt}],
                    model="llama-3.3-70b-versatile",
                    temperature=0.4,
                    max_tokens=4000
                )

                # Clean up — extract just the SVG part
                if "<svg" in svg_code and "</svg>" in svg_code:
                    start = svg_code.index("<svg")
                    end   = svg_code.index("</svg>") + 6
                    svg_code = svg_code[start:end]

                    # Show the SVG as an image
                    st.markdown("### 🖼 Generated Artwork")
                    components.html(f"""
<html><body style="margin:0;padding:0;background:transparent">
<div style="display:flex;flex-direction:column;align-items:center;gap:10px;padding:4px">
  <div style="border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.15);width:100%">
    {svg_code}
  </div>
  <button onclick="downloadSVG()" style="
    padding:8px 28px;background:#2563eb;color:white;
    border:none;border-radius:8px;font-size:14px;cursor:pointer;
    font-family:sans-serif">
    ⬇ Download SVG
  </button>
</div>
<script>
function downloadSVG() {{
  const svgData = {repr(svg_code)};
  const blob = new Blob([svgData], {{type:'image/svg+xml'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'aura_artwork.svg';
  a.click();
}}
</script>
</body></html>
""", height=680)
                    st.caption("💡 Tip: For a different version of the same prompt, click Generate again — each run creates a unique image.")
                else:
                    st.error("Could not generate image. Please try again with a different prompt.")
                    st.code(svg_code[:300])


# ─────────────────────────────────────────
# FEATURE 3 — IMAGE ANALYZER
# Uses Groq vision (base64) — no HF needed
# ─────────────────────────────────────────

elif "Image Analyzer" in feature:
    st.header("🖼 Image Analyzer")
    st.caption("Upload an image — Groq vision AI will analyze it directly")

    uploaded = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"])

    if not uploaded:
        st.info("Upload an image to get started.")
    else:
        image = Image.open(uploaded)
        st.image(image, use_container_width=True)

        st.markdown("**Quick actions:**")
        c1, c2, c3, c4 = st.columns(4)
        question = ""
        if c1.button("📝 Describe"): question = "Describe this image in detail."
        if c2.button("🎨 Colors"):   question = "What are the main colors in this image?"
        if c3.button("😊 Mood"):     question = "What is the mood or emotion of this image?"
        if c4.button("📦 Objects"):  question = "List all objects you can see in this image."

        question = st.text_input("Or type your own question:", value=question,
                                 placeholder="What is happening in this image?")

        if st.button("🔍 Analyze", use_container_width=True):
            if not question:
                st.warning("Please enter a question.")
            else:
                with st.spinner("Analyzing your image with Groq vision..."):
                    reply = analyze_image_groq(image, question)
                    st.success(reply)


# ─────────────────────────────────────────
# FEATURE 4 — WEATHER
# Fixed: use correct Open-Meteo field names
# ─────────────────────────────────────────

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
                    # wttr.in — simple, reliable, no API key, works on Streamlit Cloud
                    # Returns JSON with current weather for any city name
                    unit_sym = "°C" if unit == "Celsius" else "°F"
                    wttr_url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
                    res = requests.get(wttr_url, timeout=15)

                    if res.status_code != 200:
                        st.error(f"City not found or service unavailable. Try a different spelling.")
                    else:
                        data = res.json()
                        cc   = data["current_condition"][0]   # current conditions block
                        area = data["nearest_area"][0]

                        # Extract city and country name
                        city_name = area["areaName"][0]["value"]
                        country   = area["country"][0]["value"]

                        # Temperature: C or F
                        temp     = cc["temp_C"] if unit == "Celsius" else cc["temp_F"]
                        feels    = cc["FeelsLikeC"] if unit == "Celsius" else cc["FeelsLikeF"]
                        humidity = cc["humidity"]
                        wind     = cc["windspeedKmph"]
                        desc     = cc["weatherDesc"][0]["value"]  # e.g. "Sunny", "Partly cloudy"

                        # Pick an emoji based on description keywords
                        desc_lower = desc.lower()
                        if "thunder" in desc_lower:                  emoji = "⛈"
                        elif "snow" in desc_lower:                   emoji = "🌨"
                        elif "rain" in desc_lower or "drizzle" in desc_lower: emoji = "🌧"
                        elif "fog" in desc_lower or "mist" in desc_lower:     emoji = "🌫"
                        elif "overcast" in desc_lower or "cloudy" in desc_lower: emoji = "☁️"
                        elif "partly" in desc_lower:                 emoji = "⛅"
                        elif "sunny" in desc_lower or "clear" in desc_lower:  emoji = "☀️"
                        else:                                        emoji = "🌤"
                        condition = f"{emoji} {desc}"

                        st.subheader(f"{city_name}, {country}")
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("🌡 Temperature", f"{temp}{unit_sym}", f"Feels {feels}{unit_sym}")
                        m2.metric("💧 Humidity",    f"{humidity}%")
                        m3.metric("💨 Wind Speed",  f"{wind} km/h")
                        m4.metric("🌤 Condition",   condition)

                        with st.spinner("Getting AI tip..."):
                            tip = call_groq([
                                {"role": "system", "content": "Helpful weather assistant. Give a practical 2-line tip."},
                                {"role": "user",   "content": f"Weather in {city_name}: {temp}{unit_sym}, {condition}, humidity {humidity}%. What to wear?"},
                            ], "llama-3.1-8b-instant", 0.7, 200)
                            st.info(f"💡 AI Tip: {tip}")

                except Exception as e:
                    st.error(f"Something went wrong: {e}")


# ─────────────────────────────────────────
# FEATURE 5 — CODE ASSISTANT
# ─────────────────────────────────────────

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
                    "✍️ Write code for me":          f"Write clean, well-commented {lang} code for: {user_code}. Include example usage.",
                    "🐛 Debug my code":              f"Debug this {lang} code and explain all issues:\n\n{user_code}",
                    "📖 Explain this code":          f"Explain this {lang} code step by step in simple terms:\n\n{user_code}",
                    "🔄 Convert to another language": f"Convert this {lang} code to {target_lang}:\n\n{user_code}",
                    "⚡ Optimize my code":           f"Optimize this {lang} code for better performance:\n\n{user_code}",
                    "🧪 Write tests for my code":    f"Write comprehensive unit tests for this {lang} code:\n\n{user_code}",
                }
                messages = [
                    {"role": "system", "content": "You are an expert programmer. Provide clean, working code with clear explanations. Use markdown code blocks."},
                    {"role": "user",   "content": prompts[action]},
                ]
                reply = call_groq(messages, model_id, temperature=0.3, max_tokens=max_tokens)
                st.markdown(reply)
                st.download_button("📥 Download", reply, file_name="aura_code.txt", mime="text/plain")
