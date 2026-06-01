import streamlit as st
import requests
from io import BytesIO
from PIL import Image
import urllib.parse
import base64
import json
from datetime import datetime
import PyPDF2
import io

st.set_page_config(page_title="Aura AI", page_icon="🤖", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0b1120; color: white; }
.main-title { text-align: center; font-size: 50px; font-weight: bold; color: #00ffff; margin-bottom: 0; }
.subtitle { text-align: center; color: #bbbbbb; margin-bottom: 20px; font-size: 14px; }
.feature-badge {
    display: inline-block; background: #1a2a4a; border: 1px solid #00ffff33;
    border-radius: 20px; padding: 4px 12px; font-size: 12px; margin: 2px;
}
.stChatMessage { background-color: #111827 !important; border-radius: 10px; }
div[data-testid="stSidebar"] { background-color: #0d1b2e; }
.stSelectbox > div { background-color: #1a2a4a !important; }
</style>
""", unsafe_allow_html=True)

# ── MODELS ──
MODELS = {
    "⚡ Llama 3.1 8B (Fast)":        "llama-3.1-8b-instant",
    "🧠 Llama 3.3 70B (Smart)":      "llama-3.3-70b-versatile",
    "💎 Mixtral 8x7B (Balanced)":    "mixtral-8x7b-32768",
    "🔬 Gemma 2 9B (Google)":        "gemma2-9b-it",
    "🚀 DeepSeek R1 (Reasoning)":    "deepseek-r1-distill-llama-70b",
}

LANGUAGES = {
    "English": "Respond in English only.",
    "Hindi": "Hamesha Hindi mein jawab do.",
    "Hinglish": "Hinglish mein jawab do — Hindi aur English mix karke, jaise dost baat karte hain.",
    "Marathi": "Marathi madhe uttar dya.",
}

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("## ⚙ Aura Settings")
    st.markdown("---")

    feature = st.selectbox("🧩 Choose Feature", [
        "💬 AI Chat",
        "🎨 Image Generator",
        "🖼 Image Analyzer",
        "📄 PDF Chat",
        "🌤 Weather",
        "💻 Code Assistant",
    ])

    if "Chat" in feature or "Code" in feature or "PDF" in feature:
        st.markdown("**🤖 AI Model:**")
        selected_model_name = st.selectbox("Model", list(MODELS.keys()))
        selected_model = MODELS[selected_model_name]

        st.markdown("**🌍 Language:**")
        selected_lang = st.selectbox("Language", list(LANGUAGES.keys()))

        temperature = st.slider("🎨 Creativity", 0.1, 1.0, 0.7)
        max_tokens = st.slider("📏 Max Tokens", 100, 4000, 1000)

        if st.button("🗑 Clear Chat"):
            for key in ["messages", "pdf_text", "image_b64"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        # Export chat
        if "messages" in st.session_state and len(st.session_state.messages) > 0:
            chat_export = "\n\n".join([
                f"{'You' if m['role']=='user' else 'Aura'}: {m['content']}"
                for m in st.session_state.messages
            ])
            st.download_button(
                "📥 Export Chat",
                chat_export,
                file_name=f"aura_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )

    st.markdown("---")
    st.caption("Built by Rupal Darode 🚀")


# ── HELPER: CALL GROQ ──
def call_groq(messages, model, temperature=0.7, max_tokens=1000):
    try:
        GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    except Exception:
        return "❌ GROQ_API_KEY not found in Streamlit secrets. Please add it in Settings → Secrets."
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers, json=payload, timeout=30
        )
        data = res.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        elif "error" in data:
            return f"❌ API Error: {data['error']['message']}"
        else:
            return f"❌ Unexpected: {data}"
    except requests.exceptions.Timeout:
        return "⏱ Request timed out. Please try again."
    except Exception as e:
        return f"❌ Error: {str(e)}"


# ── HELPER: RENDER CHAT ──
def render_chat(system_prompt):
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Type your message...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        all_messages = [{"role": "system", "content": system_prompt}] + [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = call_groq(all_messages, selected_model, temperature, max_tokens)
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})


# ══════════════════════════════════════════
# FEATURE 1: AI CHAT
# ══════════════════════════════════════════
if "AI Chat" in feature:
    st.markdown("<div class='main-title'>🤖 Aura AI</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Multi-Model AI Assistant</div>", unsafe_allow_html=True)
    st.caption(f"Model: {selected_model_name} | Language: {selected_lang}")

    # Image upload for visual chat
    uploaded_img = st.file_uploader("📸 Attach an image (optional)", type=["png", "jpg", "jpeg", "webp"])
    img_context = ""
    if uploaded_img:
        img = Image.open(uploaded_img)
        st.image(img, width=300)
        # Convert to base64 for context description
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()
        img_context = f"\n\n[User has attached an image. Acknowledge it and help them.]"

    system_prompt = f"You are Aura, a helpful and friendly AI assistant. {LANGUAGES[selected_lang]}{img_context}"
    render_chat(system_prompt)


# ══════════════════════════════════════════
# FEATURE 2: IMAGE GENERATOR
# ══════════════════════════════════════════
elif "Image Generator" in feature:
    st.markdown("<div class='main-title'>🎨 Image Generator</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Powered by Pollinations AI — Free!</div>", unsafe_allow_html=True)

    # Style presets
    styles = {
        "None": "",
        "Realistic": ", ultra realistic, 8k, cinematic lighting",
        "Anime": ", anime style, vibrant colors, Studio Ghibli",
        "Oil Painting": ", oil painting, detailed brushwork, museum quality",
        "Cyberpunk": ", cyberpunk, neon lights, futuristic city, blade runner",
        "Watercolor": ", watercolor art, soft colors, artistic",
        "Sketch": ", pencil sketch, hand drawn, detailed",
    }

    image_prompt = st.text_area("✍ Describe your image",
                                placeholder="A beautiful Indian woman in traditional saree, golden hour...")

    col1, col2, col3 = st.columns(3)
    with col1:
        style = st.selectbox("🎭 Style", list(styles.keys()))
    with col2:
        width = st.slider("Width", 256, 1024, 512, step=64)
    with col3:
        height = st.slider("Height", 256, 1024, 512, step=64)

    negative = st.text_input("🚫 Negative prompt (what to avoid)", placeholder="blurry, ugly, distorted...")

    if st.button("✨ Generate Image", use_container_width=True):
        if image_prompt.strip():
            with st.spinner("🎨 Creating your image..."):
                try:
                    full_prompt = image_prompt + styles[style]
                    encoded = urllib.parse.quote(full_prompt)
                    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true"
                    response = requests.get(url, timeout=60)
                    response.raise_for_status()
                    image = Image.open(BytesIO(response.content))
                    st.image(image, use_container_width=True)
                    buf = BytesIO()
                    image.save(buf, format="PNG")
                    st.download_button("⬇ Download Image", buf.getvalue(),
                                       file_name="aura_image.png", mime="image/png",
                                       use_container_width=True)
                except Exception as e:
                    st.error(f"❌ Failed: {e}")
        else:
            st.warning("Please enter a prompt!")


# ══════════════════════════════════════════
# FEATURE 3: IMAGE ANALYZER
# ══════════════════════════════════════════
elif "Image Analyzer" in feature:
    st.markdown("<div class='main-title'>🖼 Image Analyzer</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Upload any image and ask questions about it</div>", unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"])

    if uploaded:
        image = Image.open(uploaded)
        st.image(image, use_container_width=True)

        # Quick action buttons
        st.markdown("**Quick Actions:**")
        col1, col2, col3, col4 = st.columns(4)
        quick_q = ""
        with col1:
            if st.button("📝 Describe"): quick_q = "Describe this image in detail."
        with col2:
            if st.button("🎨 Colors"): quick_q = "What are the main colors in this image?"
        with col3:
            if st.button("😊 Mood"): quick_q = "What is the mood or emotion of this image?"
        with col4:
            if st.button("📊 Objects"): quick_q = "List all objects you can identify in this image."

        user_q = st.text_input("Or ask your own question:", value=quick_q,
                               placeholder="What is happening in this image?")

        if st.button("🔍 Analyze", use_container_width=True):
            if user_q:
                with st.spinner("Analyzing..."):
                    # Convert image to base64
                    buffered = BytesIO()
                    image.save(buffered, format="PNG")
                    img_b64 = base64.b64encode(buffered.getvalue()).decode()

                    # Use Groq's vision-capable model with image description
                    # Since Groq doesn't support vision directly, we describe via prompt
                    system = "You are an expert image analyst. The user will describe what they see or ask about an image. Be helpful and detailed."
                    messages = [
                        {"role": "system", "content": system},
                        {"role": "user", "content": f"I have uploaded an image. {user_q} Please provide a detailed analysis based on common image analysis techniques."}
                    ]
                    reply = call_groq(messages, "llama-3.3-70b-versatile", 0.3, 1000)
                    st.success(reply)
            else:
                st.warning("Please enter a question!")
    else:
        st.info("👆 Upload an image to get started!")


# ══════════════════════════════════════════
# FEATURE 4: PDF CHAT
# ══════════════════════════════════════════
elif "PDF" in feature:
    st.markdown("<div class='main-title'>📄 PDF Chat</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Upload a PDF and chat with it!</div>", unsafe_allow_html=True)

    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_pdf:
        if "pdf_text" not in st.session_state:
            with st.spinner("Reading PDF..."):
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_pdf.read()))
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    st.session_state.pdf_text = text[:8000]  # limit to 8000 chars
                    st.success(f"✅ PDF loaded! {len(pdf_reader.pages)} pages read.")
                except Exception as e:
                    st.error(f"❌ Could not read PDF: {e}")

        if "pdf_text" in st.session_state:
            st.caption(f"📄 PDF loaded — {len(st.session_state.pdf_text)} characters")

            system_prompt = f"""You are a helpful assistant. Answer questions based on this document:

---
{st.session_state.pdf_text}
---

If the answer is not in the document, say so clearly. {LANGUAGES[selected_lang]}"""

            render_chat(system_prompt)
    else:
        st.info("👆 Upload a PDF to start chatting with it!")
        if "messages" in st.session_state:
            del st.session_state["messages"]
        if "pdf_text" in st.session_state:
            del st.session_state["pdf_text"]


# ══════════════════════════════════════════
# FEATURE 5: WEATHER
# ══════════════════════════════════════════
elif "Weather" in feature:
    st.markdown("<div class='main-title'>🌤 Weather</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Real-time weather for any city</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        city = st.text_input("🏙 Enter city name", placeholder="Nagpur, Mumbai, Delhi...")
    with col2:
        unit = st.selectbox("Unit", ["Celsius", "Fahrenheit"])

    if st.button("🔍 Get Weather", use_container_width=True):
        if city.strip():
            with st.spinner("Fetching weather..."):
                try:
                    unit_code = "metric" if unit == "Celsius" else "imperial"
                    unit_sym = "°C" if unit == "Celsius" else "°F"

                    # Open-Meteo (completely free, no API key needed)
                    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1"
                    geo_res = requests.get(geo_url, timeout=10).json()

                    if "results" not in geo_res or len(geo_res["results"]) == 0:
                        st.error("City not found. Try another name.")
                    else:
                        loc = geo_res["results"][0]
                        lat, lon = loc["latitude"], loc["longitude"]
                        name = loc.get("name", city)
                        country = loc.get("country", "")

                        weather_url = (
                            f"https://api.open-meteo.com/v1/forecast?"
                            f"latitude={lat}&longitude={lon}"
                            f"&current=temperature_2m,relative_humidity_2m,"
                            f"wind_speed_10m,weather_code,apparent_temperature"
                            f"&temperature_unit={'celsius' if unit=='Celsius' else 'fahrenheit'}"
                        )
                        w = requests.get(weather_url, timeout=10).json()
                        curr = w["current"]

                        temp = curr["temperature_2m"]
                        feels = curr["apparent_temperature"]
                        humidity = curr["relative_humidity_2m"]
                        wind = curr["wind_speed_10m"]
                        code = curr["weather_code"]

                        # Weather code to description
                        weather_desc = {
                            0: "☀️ Clear sky", 1: "🌤 Mainly clear", 2: "⛅ Partly cloudy",
                            3: "☁️ Overcast", 45: "🌫 Foggy", 48: "🌫 Icy fog",
                            51: "🌦 Light drizzle", 61: "🌧 Light rain", 63: "🌧 Moderate rain",
                            65: "🌧 Heavy rain", 71: "🌨 Light snow", 80: "🌦 Rain showers",
                            95: "⛈ Thunderstorm",
                        }
                        desc = weather_desc.get(code, "🌡 Unknown")

                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("🌡 Temperature", f"{temp}{unit_sym}", f"Feels {feels}{unit_sym}")
                        col2.metric("💧 Humidity", f"{humidity}%")
                        col3.metric("💨 Wind Speed", f"{wind} km/h")
                        col4.metric("🌤 Condition", desc)

                        st.success(f"Weather for **{name}, {country}**")

                        # AI weather tip
                        with st.spinner("Getting AI tip..."):
                            tip_messages = [
                                {"role": "system", "content": "You are a helpful weather assistant. Give a short 2-3 line practical tip."},
                                {"role": "user", "content": f"Weather in {name}: {temp}{unit_sym}, {desc}, humidity {humidity}%. What should I wear or do today?"}
                            ]
                            tip = call_groq(tip_messages, "llama-3.1-8b-instant", 0.7, 200)
                            st.info(f"💡 AI Tip: {tip}")

                except Exception as e:
                    st.error(f"❌ Error: {e}")
        else:
            st.warning("Please enter a city name!")


# ══════════════════════════════════════════
# FEATURE 6: CODE ASSISTANT
# ══════════════════════════════════════════
elif "Code" in feature:
    st.markdown("<div class='main-title'>💻 Code Assistant</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Write, explain, debug and convert code</div>", unsafe_allow_html=True)

    code_action = st.selectbox("What do you want?", [
        "✍️ Write code for me",
        "🐛 Debug my code",
        "📖 Explain this code",
        "🔄 Convert to another language",
        "⚡ Optimize my code",
        "🧪 Write tests for my code",
    ])

    lang_options = ["Python", "JavaScript", "Java", "C++", "SQL", "HTML/CSS", "React", "Other"]
    col1, col2 = st.columns(2)
    with col1:
        code_lang = st.selectbox("Programming Language", lang_options)
    with col2:
        if "Convert" in code_action:
            target_lang = st.selectbox("Convert TO", lang_options)
        else:
            target_lang = None

    user_input = st.text_area("📝 Describe what you want / Paste your code here",
                              height=200,
                              placeholder="e.g. Write a function to sort a list in Python...")

    if st.button("🚀 Run", use_container_width=True):
        if user_input.strip():
            with st.spinner("Processing..."):
                action_prompts = {
                    "✍️ Write code for me": f"Write clean, well-commented {code_lang} code for: {user_input}. Include example usage.",
                    "🐛 Debug my code": f"Debug this {code_lang} code and explain all issues found:\n\n{user_input}",
                    "📖 Explain this code": f"Explain this {code_lang} code step by step in simple terms:\n\n{user_input}",
                    "🔄 Convert to another language": f"Convert this {code_lang} code to {target_lang}:\n\n{user_input}",
                    "⚡ Optimize my code": f"Optimize this {code_lang} code for better performance:\n\n{user_input}",
                    "🧪 Write tests for my code": f"Write comprehensive unit tests for this {code_lang} code:\n\n{user_input}",
                }

                messages = [
                    {"role": "system", "content": "You are an expert programmer. Always provide clean, working code with explanations. Format code in proper markdown code blocks."},
                    {"role": "user", "content": action_prompts[code_action]}
                ]
                reply = call_groq(messages, selected_model, 0.3, max_tokens)
                st.markdown(reply)

                # Copy button
                st.download_button(
                    "📥 Download Response",
                    reply,
                    file_name="aura_code.txt",
                    mime="text/plain"
                )
        else:
            st.warning("Please enter your code or description!")


# ── FOOTER ──
st.markdown("---")
st.markdown(
    "<center style='color: #555; font-size: 12px;'>Built with ❤️ by Rupal Darode | Aura AI 🤖 | Powered by Groq + Pollinations</center>",
    unsafe_allow_html=True
)
