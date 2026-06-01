import streamlit as st
from transformers import pipeline
from PIL import Image
import requests
from io import BytesIO
import torch
import urllib.parse

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="Aura AI",
    page_icon="🤖",
    layout="wide"
)

# ==========================================
# CUSTOM CSS
# ==========================================

st.markdown("""
<style>
.stApp {
    background-color: #0b1120;
    color: white;
}
.main-title {
    text-align: center;
    font-size: 55px;
    font-weight: bold;
    color: #00ffff;
}
.subtitle {
    text-align: center;
    color: #bbbbbb;
    margin-bottom: 30px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# TITLE
# ==========================================

st.markdown("<div class='main-title'>Aura AI Assistant</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Multimodal AI Chatbot — Chat · Image Generation · Image Analysis</div>", unsafe_allow_html=True)

# ==========================================
# DEVICE DETECTION
# ==========================================

DEVICE = 0 if torch.cuda.is_available() else -1
DEVICE_NAME = "GPU ✅" if torch.cuda.is_available() else "CPU ⚠️"

# ==========================================
# MODEL LOADERS (cached so they load once)
# ==========================================

@st.cache_resource
def load_chatbot():
    return pipeline(
        "text-generation",
        model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        device=DEVICE,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )

@st.cache_resource
def load_caption_model():
    """BLIP captioning — describes the image in detail."""
    from transformers import BlipProcessor, BlipForConditionalGeneration
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
    model = BlipForConditionalGeneration.from_pretrained(
        "Salesforce/blip-image-captioning-large",
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )
    if torch.cuda.is_available():
        model = model.to("cuda")
    return processor, model

@st.cache_resource
def load_vqa_model():
    """BLIP VQA — answers specific questions about the image."""
    from transformers import BlipProcessor, BlipForQuestionAnswering
    processor = BlipProcessor.from_pretrained("Salesforce/blip-vqa-base")
    model = BlipForQuestionAnswering.from_pretrained(
        "Salesforce/blip-vqa-base",
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )
    if torch.cuda.is_available():
        model = model.to("cuda")
    return processor, model

# ==========================================
# SESSION STATE
# ==========================================

if "messages" not in st.session_state:
    st.session_state.messages = []

# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.title("⚙ Aura Settings")
    st.caption(f"Running on: {DEVICE_NAME}")

    feature = st.selectbox(
        "Choose Feature",
        ["AI Chat", "Image Generator", "Image Analyzer", "About"]
    )

    temperature = st.slider("Creativity", 0.1, 1.0, 0.7)
    max_tokens = st.slider("Max Tokens", 50, 500, 200)

    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ==========================================
# AI CHAT
# ==========================================

if feature == "AI Chat":
    st.subheader("💬 AI Chat")

    # Load model
    chatbot = load_chatbot()

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    prompt = st.chat_input("Ask anything...")

    if prompt:
        # Save & show user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Build prompt with last 6 messages for context (memory)
        history_text = ""
        recent = st.session_state.messages[-7:-1]  # up to 6 prior turns
        for msg in recent:
            role_tag = "user" if msg["role"] == "user" else "assistant"
            history_text += f"<|{role_tag}|>\n{msg['content']}</s>\n"

        formatted_prompt = (
            "<|system|>\nYou are Aura, a helpful and friendly AI assistant. "
            "Give clear, concise answers.</s>\n"
            + history_text
            + f"<|user|>\n{prompt}</s>\n<|assistant|>\n"
        )

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = chatbot(
                    formatted_prompt,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    repetition_penalty=1.15,
                    return_full_text=False,
                )
                response = result[0]["generated_text"].strip()
                if not response:
                    response = "I'm not sure about that. Could you rephrase?"
                st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

# ==========================================
# IMAGE GENERATOR
# ==========================================

elif feature == "Image Generator":
    st.subheader("🎨 AI Image Generator")
    st.caption("Powered by Pollinations AI (free, no API key needed)")

    image_prompt = st.text_area(
        "Describe your image",
        placeholder="Ultra realistic futuristic city, cinematic lighting, 8k"
    )

    col1, col2 = st.columns(2)
    with col1:
        width = st.slider("Width", 256, 1024, 512, step=64)
    with col2:
        height = st.slider("Height", 256, 1024, 512, step=64)

    if st.button("✨ Generate Image"):
        if image_prompt.strip():
            with st.spinner("Generating image..."):
                try:
                    encoded_prompt = urllib.parse.quote(image_prompt)
                    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    image = Image.open(BytesIO(response.content))
                    st.image(image, use_container_width=True)

                    # Download button
                    buf = BytesIO()
                    image.save(buf, format="PNG")
                    st.download_button(
                        "⬇ Download Image",
                        data=buf.getvalue(),
                        file_name="aura_generated.png",
                        mime="image/png"
                    )
                except Exception as e:
                    st.error(f"Image generation failed: {e}")
        else:
            st.warning("Please enter a prompt first.")

# ==========================================
# IMAGE ANALYZER
# ==========================================

elif feature == "Image Analyzer":
    st.subheader("🖼 AI Image Analyzer")
    st.caption("Powered by BLIP-Large (captioning) + BLIP-VQA (questions)")

    uploaded_image = st.file_uploader(
        "Upload an image",
        type=["png", "jpg", "jpeg", "webp"]
    )

    if uploaded_image is not None:
        image = Image.open(uploaded_image).convert("RGB")
        st.image(image, caption="Uploaded Image", use_container_width=True)

        mode = st.radio(
            "What do you want to do?",
            ["📝 Describe the image", "❓ Ask a specific question"],
            horizontal=True
        )

        question = ""
        if "Ask" in mode:
            st.info("💡 Ask short, factual questions for best results. Examples below:")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("What is in the image?"):
                    question = "what is in the image"
            with col2:
                if st.button("What color is the main object?"):
                    question = "what color is the main object"
            with col3:
                if st.button("How many people are there?"):
                    question = "how many people are there"

            custom_q = st.text_input(
                "Or type your own question:",
                placeholder="Is it daytime or nighttime?  /  What animal is in the image?",
                value=question
            )
            if custom_q:
                question = custom_q

        if st.button("🔍 Analyze Image"):
            if "Ask" in mode and not question.strip():
                st.warning("Please enter a question or click one of the example buttons.")
            else:
                with st.spinner("Analyzing image..."):
                    try:
                        if "Describe" in mode:
                            # Use captioning model — gives a full sentence description
                            processor, blip_model = load_caption_model()
                            # Conditional captioning with a hint gives richer output
                            inputs = processor(image, "a photography of", return_tensors="pt")
                            if torch.cuda.is_available():
                                inputs = {k: v.to("cuda") for k, v in inputs.items()}
                            with torch.no_grad():
                                output = blip_model.generate(
                                    **inputs,
                                    max_new_tokens=100,
                                    num_beams=5,           # beam search = better quality
                                    min_length=20,         # force a full sentence
                                )
                            result = processor.decode(output[0], skip_special_tokens=True)
                            st.success(f"**Description:** {result}")

                        else:
                            # Use dedicated VQA model — built for Q&A, not captioning
                            processor, blip_model = load_vqa_model()
                            inputs = processor(image, question.strip(), return_tensors="pt")
                            if torch.cuda.is_available():
                                inputs = {k: v.to("cuda") for k, v in inputs.items()}
                            with torch.no_grad():
                                output = blip_model.generate(**inputs, max_new_tokens=50)
                            result = processor.decode(output[0], skip_special_tokens=True)
                            st.success(f"**Answer:** {result}")
                            st.caption(f"Question asked: _{question}_")

                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
                        st.info("Make sure transformers and torch are installed via requirements.txt")

# ==========================================
# ABOUT
# ==========================================

elif feature == "About":
    st.subheader("🤖 About Aura AI")
    st.markdown(f"""
    **Running on:** {DEVICE_NAME}

    ### Features
    - 💬 AI Chatbot with memory (last 6 messages)
    - 🎨 AI Image Generator (Pollinations AI)
    - 🖼 Real Image Analyzer (BLIP vision model)
    - 🚀 GPU accelerated (auto-detected)

    ### Models Used
    - **TinyLlama 1.1B** — fast chat model
    - **BLIP** (Salesforce) — image captioning & visual Q&A
    - **Pollinations AI** — free image generation

    ### Upgrade Path
    | Feature | Current | Better Option |
    |---|---|---|
    | Chat | TinyLlama 1.1B | Mistral 7B, Llama 3 8B |
    | Vision | BLIP base | LLaVA-1.5 7B (needs 8GB VRAM) |
    | Images | Pollinations | SDXL locally |
    """)

# ==========================================
# FOOTER
# ==========================================

st.markdown("---")
st.markdown(
    "<center>Built with ❤️ using Streamlit + Hugging Face | Running on: "
    f"{DEVICE_NAME}</center>",
    unsafe_allow_html=True
)
