import streamlit as st
import requests
from io import BytesIO
from PIL import Image
import urllib.parse
import base64
import io
import PyPDF2
from datetime import datetime

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Aura AI",
    page_icon="✨",
    layout="wide"
)

# Minimal CSS — just light background tweaks, no heavy overrides
st.markdown("""
<style>
    .stApp { background-color: #f9fafb; }
    section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e5e7eb; }
    .stChatMessage { background-color: #ffffff !important; border: 1px solid #e5e7eb; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────

MODELS = {
    "⚡ Llama 3.1 8B  — Fast":       "llama-3.1-8b-instant",
    "🧠 Llama 3.3 70B — Smart":      "llama-3.3-70b-versatile",
    "💎 Mixtral 8x7B  — Balanced":   "mixtral-8x7b-32768",
    "🔬 Gemma 2 9B    — Google":     "gemma2-9b-it",
    "🚀 DeepSeek R1   — Reasoning":  "deepseek-r1-distill-llama-70b",
}

LANGUAGES = {
    "English":  "Always respond in English.",
    "Hindi":    "Hamesha Hindi mein jawab do.",
    "Hinglish": "Hinglish mein jawab do — Hindi aur English mix karke.",
    "Marathi":  "Marathi madhe uttar dya.",
}

IMAGE_STYLES = {
    "None":        "",
    "Realistic":   ", ultra realistic, 8k, cinematic lighting",
    "Anime":       ", anime style, vibrant colors, Studio Ghibli",
    "Oil Painting":  ", oil painting, detailed brushwork, museum quality",
    "Cyberpunk":   ", cyberpunk, neon lights, futuristic city",
    "Watercolor":  ", watercolor art, soft colors, artistic",
    "Sketch":      ", pencil sketch, hand drawn, detailed",
}


# ─────────────────────────────────────────
# CORE HELPER: CALL GROQ API
# ─────────────────────────────────────────

def call_groq(messages, model, temperature=0.7, max_tokens=1000):
    """Send messages to Groq and return the reply text."""
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        return "❌ GROQ_API_KEY missing. Add it in Settings → Secrets."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers, json=body, timeout=30
        )
        data = res.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        elif "error" in data:
            return f"❌ API Error: {data['error']['message']}"
        else:
            return f"❌ Unexpected response: {data}"

    except requests.exceptions.Timeout:
        return "⏱ Request timed out. Please try again."
    except Exception as e:
        return f"❌ Error: {str(e)}"


# ─────────────────────────────────────────
# REUSABLE CHAT UI
# ─────────────────────────────────────────

def show_chat(system_prompt, model, temperature, max_tokens):
    """Display the full chat interface with message history."""

    # Start fresh message list if none exists
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show all previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input box at the bottom
    user_input = st.chat_input("Type your message...")

    if user_input:
        # Save and show the user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Build the full message list: system prompt + history
        full_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

        # Get and show the AI reply
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = call_groq(full_messages, model, temperature, max_tokens)
                st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})


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
        "📄 PDF Chat",
        "🌤 Weather",
        "💻 Code Assistant",
    ])

    st.divider()

    # These settings only matter for chat-based features
    is_chat_feature = any(x in feature for x in ["Chat", "Code", "PDF"])

    if is_chat_feature:
        model_name = st.selectbox("Model", list(MODELS.keys()))
        model_id   = MODELS[model_name]

        language   = st.selectbox("Language", list(LANGUAGES.keys()))
        lang_rule  = LANGUAGES[language]

        temperature = st.slider("Creativity", 0.1, 1.0, 0.7)
        max_tokens  = st.slider("Max Tokens",  100, 4000, 1000)

        if st.button("🗑 Clear Chat"):
            for key in ["messages", "pdf_text"]:
                st.session_state.pop(key, None)
            st.rerun()

        # Export chat as a text file
        if st.session_state.get("messages"):
            lines = [
                f"{'You' if m['role'] == 'user' else 'Aura'}: {m['content']}"
                for m in st.session_state.messages
            ]
            st.download_button(
                "📥 Export Chat",
                data="\n\n".join(lines),
                file_name=f"aura_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
            )


# ─────────────────────────────────────────
# FEATURE 1 — AI CHAT
# ─────────────────────────────────────────

if "AI Chat" in feature:
    st.header("💬 AI Chat")
    st.caption(f"Model: {model_name}  |  Language: {language}")

    system_prompt = f"You are Aura, a helpful and friendly AI assistant. {lang_rule}"
    show_chat(system_prompt, model_id, temperature, max_tokens)


# ─────────────────────────────────────────
# FEATURE 2 — IMAGE GENERATOR
# ─────────────────────────────────────────

elif "Image Generator" in feature:
    st.header("🎨 Image Generator")
    st.caption("Powered by Pollinations AI — completely free, no API key needed")

    prompt = st.text_area("Describe your image", placeholder="A sunset over Mumbai skyline, golden hour...")

    col1, col2, col3 = st.columns(3)
    style  = col1.selectbox("Style",  list(IMAGE_STYLES.keys()))
    width  = col2.slider("Width",  256, 1024, 512, step=64)
    height = col3.slider("Height", 256, 1024, 512, step=64)

    if st.button("✨ Generate Image", use_container_width=True):
        if not prompt.strip():
            st.warning("Please enter a prompt first.")
        else:
            with st.spinner("Generating your image..."):
                full_prompt = prompt + IMAGE_STYLES[style]
                encoded_prompt = urllib.parse.quote(full_prompt)
                url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"

                try:
                    response = requests.get(url, timeout=60)
                    response.raise_for_status()
                    image = Image.open(BytesIO(response.content))
                    st.image(image, use_container_width=True)

                    # Let user download the image
                    buf = BytesIO()
                    image.save(buf, format="PNG")
                    st.download_button("⬇ Download Image", buf.getvalue(),
                                       file_name="aura_image.png", mime="image/png",
                                       use_container_width=True)
                except Exception as e:
                    st.error(f"Failed to generate image: {e}")


# ─────────────────────────────────────────
# FEATURE 3 — IMAGE ANALYZER
# ─────────────────────────────────────────

elif "Image Analyzer" in feature:
    st.header("🖼 Image Analyzer")
    st.caption("Upload any image and ask questions about it")

    uploaded = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"])

    if not uploaded:
        st.info("Upload an image to get started.")
    else:
        image = Image.open(uploaded)
        st.image(image, use_container_width=True)

        # Quick-action buttons fill the question field automatically
        st.markdown("**Quick actions:**")
        c1, c2, c3, c4 = st.columns(4)
        question = ""
        if c1.button("📝 Describe"):  question = "Describe this image in detail."
        if c2.button("🎨 Colors"):    question = "What are the main colors in this image?"
        if c3.button("😊 Mood"):      question = "What is the mood or emotion of this image?"
        if c4.button("📦 Objects"):   question = "List all objects you can identify in this image."

        question = st.text_input("Or type your own question:", value=question,
                                 placeholder="What is happening in this image?")

        if st.button("🔍 Analyze", use_container_width=True):
            if not question:
                st.warning("Please enter a question.")
            else:
                with st.spinner("Analyzing..."):
                    messages = [
                        {"role": "system", "content": "You are an expert image analyst. Be detailed and helpful."},
                        {"role": "user",   "content": f"I have uploaded an image. {question}"},
                    ]
                    reply = call_groq(messages, "llama-3.3-70b-versatile", 0.3, 1000)
                    st.success(reply)


# ─────────────────────────────────────────
# FEATURE 4 — PDF CHAT
# ─────────────────────────────────────────

elif "PDF" in feature:
    st.header("📄 PDF Chat")
    st.caption("Upload a PDF and ask questions about its content")

    uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"])

    if not uploaded_pdf:
        # Clear old PDF data when no file is uploaded
        st.session_state.pop("pdf_text", None)
        st.session_state.pop("messages", None)
        st.info("Upload a PDF to start chatting with it.")
    else:
        # Read the PDF only once and store the text
        if "pdf_text" not in st.session_state:
            with st.spinner("Reading PDF..."):
                try:
                    reader = PyPDF2.PdfReader(io.BytesIO(uploaded_pdf.read()))
                    text = "".join(page.extract_text() for page in reader.pages)
                    st.session_state.pdf_text = text[:8000]   # limit to 8000 chars
                    st.success(f"✅ Loaded {len(reader.pages)} pages.")
                except Exception as e:
                    st.error(f"Could not read PDF: {e}")

        if "pdf_text" in st.session_state:
            st.caption(f"📄 {len(st.session_state.pdf_text)} characters loaded")

            system_prompt = f"""You are a helpful assistant. Answer questions based ONLY on this document:

---
{st.session_state.pdf_text}
---

If the answer is not in the document, say so. {lang_rule}"""

            show_chat(system_prompt, model_id, temperature, max_tokens)


# ─────────────────────────────────────────
# FEATURE 5 — WEATHER
# ─────────────────────────────────────────

elif "Weather" in feature:
    st.header("🌤 Weather")
    st.caption("Real-time weather for any city — no API key needed")

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
                    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1"
                    geo_data = requests.get(geo_url, timeout=10).json()

                    if "results" not in geo_data:
                        st.error("City not found. Try a different spelling.")
                    else:
                        loc = geo_data["results"][0]
                        lat, lon   = loc["latitude"], loc["longitude"]
                        city_name  = loc.get("name", city)
                        country    = loc.get("country", "")
                        unit_param = "celsius" if unit == "Celsius" else "fahrenheit"
                        unit_sym   = "°C" if unit == "Celsius" else "°F"

                        # Step 2: Get current weather using coordinates
                        weather_url = (
                            f"https://api.open-meteo.com/v1/forecast?"
                            f"latitude={lat}&longitude={lon}"
                            f"&current=temperature_2m,relative_humidity_2m,"
                            f"wind_speed_10m,weather_code,apparent_temperature"
                            f"&temperature_unit={unit_param}"
                        )
                        weather_data = requests.get(weather_url, timeout=10).json()
                        curr = weather_data["current"]

                        temp     = curr["temperature_2m"]
                        feels    = curr["apparent_temperature"]
                        humidity = curr["relative_humidity_2m"]
                        wind     = curr["wind_speed_10m"]
                        code     = curr["weather_code"]

                        # Map weather code to a human-readable description
                        code_map = {
                            0: "☀️ Clear sky",    1: "🌤 Mainly clear",  2: "⛅ Partly cloudy",
                            3: "☁️ Overcast",     45: "🌫 Foggy",        48: "🌫 Icy fog",
                            51: "🌦 Light drizzle", 61: "🌧 Light rain", 63: "🌧 Moderate rain",
                            65: "🌧 Heavy rain",  71: "🌨 Light snow",   80: "🌦 Rain showers",
                            95: "⛈ Thunderstorm",
                        }
                        condition = code_map.get(code, "🌡 Unknown")

                        # Show the weather metrics
                        st.subheader(f"{city_name}, {country}")
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Temperature",  f"{temp}{unit_sym}", f"Feels {feels}{unit_sym}")
                        m2.metric("Humidity",     f"{humidity}%")
                        m3.metric("Wind Speed",   f"{wind} km/h")
                        m4.metric("Condition",    condition)

                        # Step 3: Get a short AI tip based on the weather
                        with st.spinner("Getting AI tip..."):
                            tip_messages = [
                                {"role": "system", "content": "You are a helpful weather assistant. Give a practical 2-line tip."},
                                {"role": "user",   "content": f"Weather in {city_name}: {temp}{unit_sym}, {condition}, humidity {humidity}%. What should I wear or do?"},
                            ]
                            tip = call_groq(tip_messages, "llama-3.1-8b-instant", 0.7, 200)
                            st.info(f"💡 AI Tip: {tip}")

                except Exception as e:
                    st.error(f"Something went wrong: {e}")


# ─────────────────────────────────────────
# FEATURE 6 — CODE ASSISTANT
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
    lang = col1.selectbox("Language", ["Python", "JavaScript", "Java", "C++", "SQL", "HTML/CSS", "React", "Other"])
    target_lang = col2.selectbox("Convert TO", ["Python", "JavaScript", "Java", "C++", "SQL", "HTML/CSS", "React", "Other"]) if "Convert" in action else None

    user_code = st.text_area("Describe what you want or paste your code here", height=200,
                             placeholder="e.g. Write a function to check if a number is prime in Python")

    if st.button("🚀 Run", use_container_width=True):
        if not user_code.strip():
            st.warning("Please enter some code or a description.")
        else:
            with st.spinner("Processing..."):

                # Build the right prompt depending on what the user wants
                prompts = {
                    "✍️ Write code for me":          f"Write clean, well-commented {lang} code for: {user_code}. Include example usage.",
                    "🐛 Debug my code":              f"Debug this {lang} code and explain all issues found:\n\n{user_code}",
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

                st.download_button("📥 Download", reply,
                                   file_name="aura_code.txt", mime="text/plain")
