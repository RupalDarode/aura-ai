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

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def get_hf_token() -> str:
    token = ""
    try:
        token = st.secrets.get("HF_TOKEN", "")
    except Exception:
        token = ""
    return token or os.getenv("HF_TOKEN", "")


def hf_headers() -> Dict[str, str]:
    token = get_hf_token()
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def get_hf_api_bases() -> List[str]:
    custom_base = ""
    try:
        custom_base = st.secrets.get("HF_API_BASE", "")
    except Exception:
        custom_base = ""
    custom_base = custom_base or os.getenv("HF_API_BASE", "")

    bases = []
    if custom_base:
        bases.append(custom_base.rstrip("/"))

    # New Hugging Face serverless inference route, then legacy route as fallback.
    bases.extend(
        [
            "https://router.huggingface.co/hf-inference/models",
            "https://api-inference.huggingface.co/models",
        ]
    )
    return list(dict.fromkeys(bases))


def call_hf_api(
    model: str,
    payload: Any,
    *,
    task: str,
    timeout: int = 60,
    binary: bool = False,
    content_type: Optional[str] = None,
) -> Any:
    headers = hf_headers()
    if content_type:
        headers["Content-Type"] = content_type
    last_error = None

    for base in get_hf_api_bases():
        url = f"{base}/{model}"
        try:
            response = requests.post(
                url,
                headers=headers,
                json=None if binary else payload,
                data=payload if binary else None,
                timeout=timeout,
            )

            if response.status_code == 503:
                try:
                    message = response.json().get("error", "Model is loading. Try again in a minute.")
                except Exception:
                    message = "Model is loading. Try again in a minute."
                raise RuntimeError(message)

            if not response.ok:
                try:
                    error_text = response.json().get("error", response.text)
                except Exception:
                    error_text = response.text
                raise RuntimeError(f"{task} failed from {base}: {error_text}")

            content_type_header = response.headers.get("content-type", "")
            if content_type_header.startswith("image/"):
                return response.content
            if content_type_header.startswith("audio/"):
                return response.content
            return response.json()
        except (requests.exceptions.RequestException, RuntimeError) as exc:
            last_error = exc
            continue

    raise RuntimeError(
        "Could not reach Hugging Face from this Streamlit server. "
        "Check internet access, DNS, and Streamlit Cloud outbound network settings. "
        f"Last error: {last_error}"
    )


def build_chat_prompt(messages: List[Dict[str, str]], system_prompt: str) -> str:
    prompt = f"<|system|>\n{system_prompt}</s>\n"
    for message in messages[-12:]:
        role = message["role"]
        content = message["content"]
        if role == "user":
            prompt += f"<|user|>\n{content}</s>\n"
        else:
            prompt += f"<|assistant|>\n{content}</s>\n"
    prompt += "<|assistant|>\n"
    return prompt


def clean_generated_reply(text: str) -> str:
    markers = ["<|assistant|>", "Assistant:", "</s>"]
    reply = text
    for marker in markers:
        if marker in reply:
            reply = reply.split(marker)[-1]
    return reply.strip()


def chat_with_hugging_face(
    messages: List[Dict[str, str]],
    model: str,
    system_prompt: str,
    temperature: float,
    max_new_tokens: int,
) -> str:
    prompt = build_chat_prompt(messages, system_prompt)
    data = call_hf_api(
        model,
        {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "return_full_text": False,
            },
            "options": {"wait_for_model": True},
        },
        task="Chat",
        timeout=120,
    )

    if isinstance(data, list) and data:
        text = data[0].get("generated_text", "")
        return clean_generated_reply(text) or "I could not generate a response."
    if isinstance(data, dict):
        return clean_generated_reply(data.get("generated_text", str(data)))
    return str(data)


def transcribe_audio(audio_bytes: bytes, model: str) -> str:
    data = call_hf_api(
        model,
        audio_bytes,
        task="Speech to text",
        timeout=120,
        binary=True,
        content_type="audio/wav",
    )
    if isinstance(data, dict):
        return data.get("text", "").strip()
    return str(data).strip()


def speak_text_browser(text: str, language: str) -> None:
    lang_codes = {
        "English": "en-US",
        "Hindi": "hi-IN",
        "Hinglish": "hi-IN",
        "Marathi": "mr-IN",
    }
    safe_text = text[:1200].replace("`", "").replace("\n", " ")
    lang = lang_codes.get(language, "en-US")
    components.html(
        f"""
        <script>
        (function() {{
          const utterance = new SpeechSynthesisUtterance({safe_text!r});
          utterance.lang = {lang!r};
          utterance.rate = 1.0;
          window.speechSynthesis.cancel();
          window.speechSynthesis.speak(utterance);
        }})();
        </script>
        """,
        height=0,
    )


def extract_pdf_text(uploaded_file) -> str:
    if PyPDF2 is None:
        return "PyPDF2 is not installed. Run: pip install PyPDF2"
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text.strip()
    except Exception as exc:
        return f"Could not read PDF: {exc}"


def extract_docx_text(uploaded_file) -> str:
    if docx is None:
        return "python-docx is not installed. Run: pip install python-docx"
    try:
        document = docx.Document(io.BytesIO(uploaded_file.getvalue()))
        return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
    except Exception as exc:
        return f"Could not read DOCX: {exc}"


def extract_document_text(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return extract_pdf_text(uploaded_file)
    if name.endswith(".docx"):
        return extract_docx_text(uploaded_file)
    if name.endswith((".txt", ".md", ".csv")):
        return uploaded_file.getvalue().decode("utf-8", errors="ignore").strip()
    return "Unsupported document type."


def analyze_image_caption(image: Image.Image, model: str) -> str:
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG")
    data = call_hf_api(
        model,
        buffer.getvalue(),
        task="Image analysis",
        timeout=120,
        binary=True,
        content_type="image/jpeg",
    )
    if isinstance(data, list) and data:
        return data[0].get("generated_text", str(data[0]))
    if isinstance(data, dict):
        return data.get("generated_text", data.get("caption", str(data)))
    return str(data)


def generate_image(prompt: str, model: str) -> bytes:
    return call_hf_api(
        model,
        {"inputs": prompt, "options": {"wait_for_model": True}},
        task="Image generation",
        timeout=180,
    )


def pollinations_image_url(prompt: str) -> str:
    import random
    import urllib.parse

    encoded_prompt = urllib.parse.quote(prompt)
    seed = random.randint(1, 999999)
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=768&nologo=true&seed={seed}"


def get_weather(city: str, unit: str) -> Dict[str, Any]:
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo = requests.get(
        geo_url,
        params={"name": city.strip(), "count": 1, "language": "en", "format": "json"},
        timeout=20,
    ).json()

    if not geo.get("results"):
        raise ValueError(f"City '{city}' was not found. Try adding the country name.")

    location = geo["results"][0]
    temperature_unit = "fahrenheit" if unit == "Fahrenheit" else "celsius"
    weather = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
            "current_weather": "true",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "temperature_unit": temperature_unit,
            "wind_speed_unit": "kmh",
            "forecast_days": 5,
            "timezone": "auto",
        },
        timeout=20,
    ).json()

    current = weather.get("current") or {}
    current_weather = weather.get("current_weather") or {}

    if current_weather:
        current.setdefault("temperature_2m", current_weather.get("temperature"))
        current.setdefault("apparent_temperature", current_weather.get("temperature"))
        current.setdefault("weather_code", current_weather.get("weathercode"))
        current.setdefault("wind_speed_10m", current_weather.get("windspeed"))

    daily = weather.get("daily", {})
    return {
        "place": f"{location.get('name', city)}, {location.get('country', '')}",
        "current": current,
        "daily": daily,
        "condition": WEATHER_CODES.get(current.get("weather_code"), "Unknown"),
        "unit": "F" if unit == "Fahrenheit" else "C",
    }


def init_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("document_context", "")
    st.session_state.setdefault("document_name", "")


init_state()


with st.sidebar:
    st.title("Aura AI")
    st.caption("Streamlit app powered by Hugging Face models")
    st.divider()

    feature = st.radio(
        "Features",
        [
            "Conversational Chatbot",
            "Document Upload",
            "PDF Analyzer",
            "Image Analyzer",
            "Image Generation",
            "Weather Forecasting",
        ],
    )

    st.divider()
    chat_model_name = st.selectbox("Chat model", list(HF_CHAT_MODELS.keys()))
    chat_model = HF_CHAT_MODELS[chat_model_name]
    language = st.selectbox("Response language", list(LANGUAGE_RULES.keys()))
    temperature = st.slider("Creativity", 0.1, 1.0, 0.7, 0.1)
    max_tokens = st.slider("Max answer length", 100, 1200, 500, 50)

    st.divider()
    if get_hf_token():
        st.success("HF_TOKEN loaded")
    else:
        st.warning("Add HF_TOKEN in Streamlit secrets for best results.")

    if st.button("Clear chat and document", use_container_width=True):
        st.session_state.messages = []
        st.session_state.document_context = ""
        st.session_state.document_name = ""
        st.rerun()


def document_context_note() -> str:
    if not st.session_state.document_context:
        return ""
    clipped = st.session_state.document_context[:7000]
    return (
        f"\n\nThe user uploaded this document named {st.session_state.document_name}. "
        f"Use it when relevant:\n---\n{clipped}\n---"
    )


if feature == "Conversational Chatbot":
    st.header("Conversational Chatbot")
    st.caption("Type, upload a document for context, or speak into the microphone.")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.session_state.document_context:
        st.info(f"Document context loaded: {st.session_state.document_name}")

    upload_col, voice_col = st.columns([2, 1])
    with upload_col:
        chat_doc = st.file_uploader(
            "Attach document context",
            type=["pdf", "docx", "txt", "md", "csv"],
            key="chat_document",
        )
    with voice_col:
        stt_model_name = st.selectbox("Voice model", list(HF_STT_MODELS.keys()))
        if hasattr(st, "audio_input"):
            voice_file = st.audio_input("Voice to text")
        else:
            voice_file = st.file_uploader("Upload voice audio", type=["wav", "mp3", "m4a"], key="voice_upload")

    if chat_doc is not None and st.session_state.document_name != chat_doc.name:
        text = extract_document_text(chat_doc)
        if text:
            st.session_state.document_context = text
            st.session_state.document_name = chat_doc.name
            st.success(f"Loaded {chat_doc.name}")

    voice_text = ""
    if voice_file is not None:
        audio_bytes = voice_file.read()
        audio_hash = hash(audio_bytes)
        if st.session_state.get("last_audio_hash") != audio_hash:
            st.session_state.last_audio_hash = audio_hash
            with st.spinner("Converting voice to text..."):
                try:
                    voice_text = transcribe_audio(audio_bytes, HF_STT_MODELS[stt_model_name])
                    if voice_text:
                        st.success(f"Voice text: {voice_text}")
                except Exception as exc:
                    st.error("Voice-to-text could not reach Hugging Face from this Streamlit server.")
                    with st.expander("Technical Hugging Face error"):
                        st.code(str(exc))

    typed_text = st.chat_input("Type your message here...")
    user_text = typed_text or voice_text

    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        system_prompt = (
            "You are Aura AI, a helpful conversational assistant. "
            "Answer clearly and practically. "
            f"{LANGUAGE_RULES[language]}"
            f"{document_context_note()}"
        )

        with st.chat_message("assistant"):
            with st.spinner("Thinking with Hugging Face..."):
                try:
                    reply = chat_with_hugging_face(
                        st.session_state.messages,
                        chat_model,
                        system_prompt,
                        temperature,
                        max_tokens,
                    )
                except Exception as exc:
                    reply = (
                        "Sorry, I could not reach Hugging Face from this Streamlit server. "
                        "Please check your HF_TOKEN secret and Streamlit Cloud network/DNS access."
                    )
                    with st.expander("Technical Hugging Face error"):
                        st.code(str(exc))
                st.markdown(reply)
                speak_text_browser(reply, language)

        st.session_state.messages.append({"role": "assistant", "content": reply})

    if st.session_state.messages:
        export_text = "\n\n".join(f"{m['role'].title()}: {m['content']}" for m in st.session_state.messages)
        st.download_button(
            "Download chat",
            export_text,
            file_name=f"aura_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
        )


elif feature == "Document Upload":
    st.header("Document Upload")
    st.caption("Upload PDF, DOCX, TXT, MD, or CSV files and ask questions about them.")

    uploaded = st.file_uploader("Upload a document", type=["pdf", "docx", "txt", "md", "csv"])
    if uploaded:
        text = extract_document_text(uploaded)
        st.session_state.document_context = text
        st.session_state.document_name = uploaded.name
        st.success(f"Loaded {uploaded.name}")
        st.text_area("Extracted text", value=text[:10000], height=280)

        question = st.text_input("Ask about this document", placeholder="Summarize this document in 5 points")
        if st.button("Analyze document", use_container_width=True) and question.strip():
            prompt = (
                "You are a document analysis assistant. Use the document text to answer. "
                f"{LANGUAGE_RULES[language]}\n\nDocument:\n{text[:9000]}"
            )
            with st.spinner("Analyzing document..."):
                try:
                    answer = chat_with_hugging_face(
                        [{"role": "user", "content": question}],
                        chat_model,
                        prompt,
                        temperature,
                        max_tokens,
                    )
                    st.markdown(answer)
                except Exception as exc:
                    st.error(str(exc))


elif feature == "PDF Analyzer":
    st.header("PDF Analyzer")
    st.caption("Extract, summarize, and question-answer over a PDF.")

    pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
    if pdf_file:
        pdf_text = extract_pdf_text(pdf_file)
        st.session_state.document_context = pdf_text
        st.session_state.document_name = pdf_file.name
        st.success(f"Loaded {pdf_file.name}")
        st.text_area("PDF text preview", pdf_text[:10000], height=260)

        action = st.selectbox("PDF task", ["Summarize", "Key points", "Find risks/issues", "Custom question"])
        custom_question = ""
        if action == "Custom question":
            custom_question = st.text_input("Your question")

        if st.button("Run PDF analysis", use_container_width=True):
            question = custom_question or f"{action} this PDF."
            system_prompt = (
                "You are a precise PDF analyzer. Base your answer on the PDF text. "
                f"{LANGUAGE_RULES[language]}\n\nPDF text:\n{pdf_text[:10000]}"
            )
            with st.spinner("Analyzing PDF..."):
                try:
                    answer = chat_with_hugging_face(
                        [{"role": "user", "content": question}],
                        chat_model,
                        system_prompt,
                        temperature,
                        max_tokens,
                    )
                    st.markdown(answer)
                except Exception as exc:
                    st.error(str(exc))


elif feature == "Image Analyzer":
    st.header("Image Analyzer")
    st.caption("Upload an image and analyze it with a Hugging Face vision model.")

    image_model_name = st.selectbox("Image analyzer model", list(HF_IMAGE_ANALYZER_MODELS.keys()))
    uploaded_image = st.file_uploader("Upload image", type=["png", "jpg", "jpeg", "webp"])
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, use_container_width=True)
        question = st.text_input("Ask about the image", value="Describe this image in detail.")

        if st.button("Analyze image", use_container_width=True):
            with st.spinner("Analyzing image..."):
                try:
                    caption = analyze_image_caption(image, HF_IMAGE_ANALYZER_MODELS[image_model_name])
                    st.subheader("Vision model result")
                    st.markdown(caption)

                    if question.strip() and question.lower() != "describe this image in detail.":
                        system_prompt = (
                            "You answer questions about images using the provided visual caption. "
                            f"{LANGUAGE_RULES[language]}"
                        )
                        answer = chat_with_hugging_face(
                            [{"role": "user", "content": f"Image caption: {caption}\nQuestion: {question}"}],
                            chat_model,
                            system_prompt,
                            temperature,
                            max_tokens,
                        )
                        st.subheader("Answer")
                        st.markdown(answer)
                except Exception as exc:
                    st.error(str(exc))


elif feature == "Image Generation":
    st.header("Image Generation")
    st.caption("Generate images from text using Hugging Face diffusion models.")

    image_gen_model_name = st.selectbox("Image generation model", list(HF_IMAGE_GENERATION_MODELS.keys()))
    prompt = st.text_area("Image prompt", placeholder="A peaceful mountain village at sunrise")
    style = st.selectbox("Style", list(IMAGE_STYLES.keys()))

    if st.button("Generate image", use_container_width=True):
        if not prompt.strip():
            st.warning("Please enter an image prompt.")
        else:
            full_prompt = prompt.strip() + IMAGE_STYLES[style]
            with st.spinner("Generating image with Hugging Face..."):
                try:
                    image_bytes = generate_image(full_prompt, HF_IMAGE_GENERATION_MODELS[image_gen_model_name])
                    st.image(image_bytes, caption=full_prompt, use_container_width=True)
                    st.download_button(
                        "Download image",
                        image_bytes,
                        file_name="aura_generated_image.png",
                        mime="image/png",
                    )
                except Exception as exc:
                    st.warning(
                        "Hugging Face image generation could not be reached from the Streamlit server. "
                        "Showing a browser-loaded fallback image instead."
                    )
                    st.markdown(
                        f"""
                        <div style="text-align:center">
                          <img src="{pollinations_image_url(full_prompt)}"
                               style="max-width:100%; border-radius:8px; border:1px solid #e5e7eb;" />
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    with st.expander("Technical Hugging Face error"):
                        st.code(str(exc))


elif feature == "Weather Forecasting":
    st.header("Weather Forecasting")
    st.caption("Current weather and 5-day forecast using Open-Meteo.")

    col_city, col_unit = st.columns([3, 1])
    city = col_city.text_input("City", placeholder="Nagpur, Mumbai, Delhi, London")
    unit = col_unit.selectbox("Unit", ["Celsius", "Fahrenheit"])

    if st.button("Get forecast", use_container_width=True):
        if not city.strip():
            st.warning("Please enter a city.")
        else:
            with st.spinner("Fetching weather..."):
                try:
                    weather = get_weather(city, unit)
                    current = weather["current"]
                    unit_symbol = weather["unit"]

                    st.subheader(weather["place"])
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Temperature", f"{current.get('temperature_2m', 'N/A')} deg {unit_symbol}")
                    c2.metric("Feels like", f"{current.get('apparent_temperature', 'N/A')} deg {unit_symbol}")
                    c3.metric("Humidity", f"{current.get('relative_humidity_2m', 'N/A')}%")
                    c4.metric("Wind", f"{current.get('wind_speed_10m', 'N/A')} km/h")
                    st.info(f"Condition: {weather['condition']}")

                    daily = weather["daily"]
                    if daily:
                        st.subheader("5-day forecast")
                        rows = []
                        for index, day in enumerate(daily.get("time", [])):
                            rows.append(
                                {
                                    "Date": day,
                                    f"Max ({unit_symbol})": daily.get("temperature_2m_max", [])[index],
                                    f"Min ({unit_symbol})": daily.get("temperature_2m_min", [])[index],
                                    "Rain chance (%)": daily.get("precipitation_probability_max", [])[index],
                                }
                            )
                        st.table(rows)

                    with st.spinner("Creating AI weather tip..."):
                        prompt = (
                            f"Weather for {weather['place']}: {current}. "
                            "Give a short practical clothing and travel tip."
                        )
                        try:
                            tip = chat_with_hugging_face(
                                [{"role": "user", "content": prompt}],
                                chat_model,
                                f"You are a weather assistant. {LANGUAGE_RULES[language]}",
                                0.4,
                                180,
                            )
                            st.markdown(f"**AI tip:** {tip}")
                        except Exception:
                            pass
                except Exception as exc:
                    st.error(str(exc))
