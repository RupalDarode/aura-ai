# ============================================================
#  Aura AI  —  Final Fixed Version
#  Built by Rupal Darode
# ============================================================
#
#  SETUP: Streamlit Cloud → Settings → Secrets → paste:
#
#     GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxx"
#
#  Get FREE key: https://console.groq.com/keys
#  No other tokens needed.
# ============================================================

import base64
import io
import base64
import urllib.parse
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import PyPDF2
import requests
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from io import BytesIO

# ── PAGE CONFIG ─────────────────────────────────────────────
st.set_page_config(page_title="Aura AI", page_icon="✨", layout="wide")
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
</style>
""", unsafe_allow_html=True)
HF_CHAT_MODELS = {
    "Zephyr 7B Beta - chat": "HuggingFaceH4/zephyr-7b-beta",
    "Mistral 7B Instruct - balanced": "mistralai/Mistral-7B-Instruct-v0.2",
    "Llama 3.1 8B Instruct - strong": "meta-llama/Llama-3.1-8B-Instruct",
