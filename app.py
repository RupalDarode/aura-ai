import streamlit as st
import requests
from io import BytesIO
from PIL import Image
import urllib.parse

st.set_page_config(page_title="Aura AI", page_icon="🤖", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0b1120; color: white; }
.main-title { text-align: center; font-size: 55px; font-weight: bold; color: #00ffff; }
.subtitle { text-align: center; color: #bbbbbb; margin-bottom: 30px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>Aura AI Assistant</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Multi-Model AI Chatbot · Image Generator</div>", unsafe_allow_html=True)

MODELS = {
    "⚡ Llama 3.1 8B (Fast)":      "llama-3.1-8b-instant",
    "🧠 Llama 3.3 70B (Smart)":    "llama-3.3-70b-versatile",
    "💎 Mixtral 8x7B (Balanced)":  "mixtral-8x7b-32768",
    "🔬 Gemma 2 9B (Google)":      "gemma2-9b-it",
    "🚀 DeepSeek R1 (Reasoning)":  "deepseek-r1-distill-llama-70b",
}

with st.sidebar:
    st.title("⚙ Aura Settings")
    feature = st.selectbox("Choose Feature", ["💬 AI Chat", "🎨 Image Generator"])
    if "Chat" in feature:
        st.markdown("---")
        st.markdown("**Choose AI Model:**")
        selected_model_name = st.selectbox("Model", list(MODELS.keys()))
        selected_model = MODELS[selected_model_name]
        temperature = st.slider("Creativity", 0.1, 1.0, 0.7)
        max_tokens = st.slider("Max Tokens", 100, 4000, 1000)
        if st.button("🗑 Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    st.markdown("---")
    st.caption("Built by Rupal Darode 🚀")

if "Chat" in feature:
    st.subheader("💬 AI Chat")
    try:
        GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    except Exception:
        st.error("⚠️ GROQ_API_KEY not found in secrets. Please add it in Streamlit settings.")
        st.stop()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.caption(f"Using: {selected_model_name}")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask anything...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    headers = {
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": selected_model,
                        "messages": [
                            {"role": "system", "content": "You are Aura, a helpful and friendly AI assistant."},
                            *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }
                    res = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers, json=payload, timeout=30
                    )
                    data = res.json()
                    if "choices" in data:
                        reply = data["choices"][0]["message"]["content"]
                    elif "error" in data:
                        reply = f"❌ API Error: {data['error']['message']}"
                    else:
                        reply = f"❌ Unexpected response: {data}"
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

elif "Image" in feature:
    st.subheader("🎨 AI Image Generator")
    st.caption("Powered by Pollinations AI — Free!")
    image_prompt = st.text_area("Describe your image", placeholder="Futuristic city, cinematic lighting, 8k")
    col1, col2 = st.columns(2)
    with col1:
        width = st.slider("Width", 256, 1024, 512, step=64)
    with col2:
        height = st.slider("Height", 256, 1024, 512, step=64)
    if st.button("✨ Generate Image"):
        if image_prompt.strip():
            with st.spinner("Generating..."):
                try:
                    encoded = urllib.parse.quote(image_prompt)
                    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true"
                    response = requests.get(url, timeout=60)
                    image = Image.open(BytesIO(response.content))
                    st.image(image, use_container_width=True)
                    buf = BytesIO()
                    image.save(buf, format="PNG")
                    st.download_button("⬇ Download", buf.getvalue(), file_name="aura.png", mime="image/png")
                except Exception as e:
                    st.error(f"❌ Failed: {e}")
        else:
            st.warning("Enter a prompt first!")

st.markdown("---")
st.markdown("<center>Built with ❤️ by Rupal Darode | Aura AI 🤖</center>", unsafe_allow_html=True)
