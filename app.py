import streamlit as st
import requests
from io import BytesIO
from PIL import Image
import urllib.parse

st.set_page_config(
    page_title="Aura AI",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
<style>
.stApp { background-color: #0b1120; color: white; }
.main-title { text-align: center; font-size: 55px; font-weight: bold; color: #00ffff; }
.subtitle { text-align: center; color: #bbbbbb; margin-bottom: 30px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>Aura AI Assistant</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>AI Chatbot · Image Generator</div>", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙ Aura Settings")
    feature = st.selectbox("Choose Feature", ["AI Chat", "Image Generator"])
    st.markdown("---")
    st.caption("Built by Rupal Darode 🚀")

# ── AI CHAT ──
if feature == "AI Chat":
    st.subheader("💬 AI Chat")

    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

    if "messages" not in st.session_state:
        st.session_state.messages = []

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
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama3-8b-8192",
                    "messages": [
                        {"role": "system", "content": "You are Aura, a helpful and friendly AI assistant."},
                        *st.session_state.messages
                    ]
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions",
                                    headers=headers, json=payload)
                reply = res.json()["choices"][0]["message"]["content"]
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

# ── IMAGE GENERATOR ──
elif feature == "Image Generator":
    st.subheader("🎨 AI Image Generator")
    st.caption("Powered by Pollinations AI — Free & No API Key!")

    image_prompt = st.text_area("Describe your image",
                                 placeholder="Futuristic city, cinematic lighting, 8k")
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
                    response = requests.get(url, timeout=30)
                    image = Image.open(BytesIO(response.content))
                    st.image(image, use_container_width=True)
                    buf = BytesIO()
                    image.save(buf, format="PNG")
                    st.download_button("⬇ Download", buf.getvalue(),
                                       file_name="aura_generated.png", mime="image/png")
                except Exception as e:
                    st.error(f"Failed: {e}")
        else:
            st.warning("Please enter a prompt!")

st.markdown("---")
st.markdown("<center>Built with ❤️ by Rupal Darode | Aura AI</center>", unsafe_allow_html=True)
