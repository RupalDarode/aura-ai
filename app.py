import base64
import io
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None


# ============================================================
# Aura AI - Streamlit + Hugging Face
# Features:
# 1. Conversational chatbot
# 2. Voice to text and text to voice in the same chatbot
# 3. Document upload
# 4. PDF analyzer
# 5. Image analyzer
# 6. Image generation
# 7. Weather forecasting
#
# Streamlit secrets:
# HF_TOKEN = "hf_xxxxxxxxxxxxxxxxx"
# ============================================================


st.set_page_config(page_title="Aura AI", page_icon="AI", layout="wide")

st.markdown(
    """
    <style>
      .stApp { background: #f8fafc; }
      section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5e7eb;
      }
      .stChatMessage {
        background: #ffffff !important;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
      }
      .small-note {
        color: #64748b;
        font-size: 0.9rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


HF_CHAT_MODELS = {
    "Zephyr 7B Beta - chat": "HuggingFaceH4/zephyr-7b-beta",
    "Mistral 7B Instruct - balanced": "mistralai/Mistral-7B-Instruct-v0.2",
    "Llama 3.1 8B Instruct - strong": "meta-llama/Llama-3.1-8B-Instruct",
}

HF_STT_MODELS = {
    "Whisper Small": "openai/whisper-small",
    "Whisper Base": "openai/whisper-base",
}

HF_IMAGE_ANALYZER_MODELS = {
    "BLIP Large Captioning": "Salesforce/blip-image-captioning-large",
    "BLIP Base Captioning": "Salesforce/blip-image-captioning-base",
}

HF_IMAGE_GENERATION_MODELS = {
    "Stable Diffusion XL": "stabilityai/stable-diffusion-xl-base-1.0",
    "Stable Diffusion 2.1": "stabilityai/stable-diffusion-2-1",
}

IMAGE_STYLES = {
    "Natural": "",
    "Realistic": ", realistic, highly detailed, natural lighting",
    "Anime": ", anime style, vibrant, expressive",
    "Oil Painting": ", oil painting, visible brush strokes",
    "Watercolor": ", watercolor, soft colors",
    "Cyberpunk": ", cyberpunk, neon, futuristic",
    "Sketch": ", pencil sketch, clean linework",
}

LANGUAGE_RULES = {
    "English": "Reply in English.",
    "Hindi": "Reply in Hindi.",
    "Hinglish": "Reply in Hinglish, mixing Hindi and English naturally.",
    "Marathi": "Reply in Marathi.",
}
