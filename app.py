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

st.set_page_config(page_title="Aura AI", page_icon="✦", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:wght@300;400;500&family=Cormorant:ital,wght@0,300;0,400;1,300;1,400&display=swap');

* { box-sizing: border-box; }
.stApp { background: #05050d; color: #ece8f8; font-family: 'Syne', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 2rem 2rem 2rem !important; max-width: 1200px !important; }

.stApp::before {
    content: '';
    position: fixed; inset: 0;
    background:
        radial-gradient(ellipse at 20% 20%, rgba(139,124,248,0.07) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, rgba(200,160,74,0.05) 0%, transparent 50%);
    pointer-events: none; z-index: 0;
    animation: bgPulse 8s ease-in-out infinite;
}
@keyframes bgPulse { 0%,100%{opacity:1} 50%{opacity:0.7} }

.aura-header { text-align:center; padding:48px 0 32px; animation:fadeDown .8s ease forwards; }
@keyframes fadeDown { from{opacity:0;transform:translateY(-20px)} to{opacity:1;transform:translateY(0)} }
.aura-logo { font-family:'Cormorant',serif; font-size:clamp(3rem,6vw,5rem); font-weight:300; font-style:italic; letter-spacing:.05em; color:#ece8f8; line-height:1; margin-bottom:8px; }
.aura-logo span { color:#c8a04a; font-weight:400; }
.aura-tagline { font-family:'DM Mono',monospace; font-size:.68rem; letter-spacing:.3em; text-transform:uppercase; color:rgba(200,160,74,0.6); margin-bottom:24px; }
.aura-divider { width:60px; height:1px; background:linear-gradient(90deg,transparent,#c8a04a,transparent); margin:0 auto 32px; animation:expandLine 1s ease .5s both; }
@keyframes expandLine { from{width:0;opacity:0} to{width:60px;opacity:1} }

.sec-title { font-family:'Cormorant',serif; font-size:clamp(1.8rem,3vw,2.8rem); font-weight:300; font-style:italic; color:#ece8f8; margin-bottom:6px; animation:fadeUp .6s ease forwards; }
.sec-sub { font-family:'DM Mono',monospace; font-size:.65rem; letter-spacing:.2em; text-transform:uppercase; color:rgba(200,160,74,0.5); margin-bottom:28px; animation:fadeUp .6s ease .1s both; }
@keyframes fadeUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }

/* Voice button */
.voice-btn-wrap { display:flex; gap:10px; align-items:center; margin-bottom:12px; }
.voice-status { font-family:'DM Mono',monospace; font-size:.65rem; color:rgba(200,160,74,0.6); letter-spacing:.1em; }
.recording-pulse { display:inline-block; width:8px; height:8px; background:#f05050; border-radius:50%; animation:recPulse 1s ease infinite; margin-right:6px; }
@keyframes recPulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(1.4)} }

/* TTS audio player */
.tts-wrap { background:rgba(200,160,74,0.06); border:1px solid rgba(200,160,74,0.15); border-radius:10px; padding:12px 16px; margin-top:8px; display:flex; align-items:center; gap:10px; }
.tts-label { font-family:'DM Mono',monospace; font-size:.62rem; color:rgba(200,160,74,0.5); letter-spacing:.1em; text-transform:uppercase; white-space:nowrap; }
audio { flex:1; height:32px; }
audio::-webkit-media-controls-panel { background:rgba(200,160,74,0.1); }

.stChatMessage { background:rgba(255,255,255,0.03) !important; border:1px solid rgba(255,255,255,0.06) !important; border-radius:12px !important; margin-bottom:12px !important; animation:msgSlide .4s ease forwards; backdrop-filter:blur(10px); }
@keyframes msgSlide { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
.stChatMessage [data-testid="chatAvatarIcon-user"] { background:#c8a04a !important; }
.stChatMessage [data-testid="chatAvatarIcon-assistant"] { background:#8b7cf8 !important; }

.stChatInput { background:rgba(255,255,255,0.04) !important; border:1px solid rgba(255,255,255,0.1) !important; border-radius:12px !important; color:#ece8f8 !important; transition:border-color .3s !important; }
.stChatInput:focus-within { border-color:rgba(200,160,74,0.5) !important; box-shadow:0 0 0 3px rgba(200,160,74,0.08) !important; }

.stButton > button { background:linear-gradient(135deg,#c8a04a,#a07830) !important; color:#05050d !important; border:none !important; border-radius:8px !important; font-family:'Syne',sans-serif !important; font-weight:700 !important; font-size:.78rem !important; letter-spacing:.12em !important; text-transform:uppercase !important; padding:12px 28px !important; transition:all .3s !important; }
.stButton > button:hover { transform:translateY(-2px) !important; box-shadow:0 8px 32px rgba(200,160,74,0.3) !important; }
.stButton > button:active { transform:translateY(0) !important; }

.stTextInput > div > div > input, .stTextArea > div > div > textarea { background:rgba(255,255,255,0.04) !important; border:1px solid rgba(255,255,255,0.1) !important; border-radius:8px !important; color:#ece8f8 !important; transition:border-color .3s !important; }
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus { border-color:rgba(200,160,74,0.5) !important; box-shadow:0 0 0 3px rgba(200,160,74,0.08) !important; }

.stSelectbox > div > div { background:rgba(255,255,255,0.04) !important; border:1px solid rgba(255,255,255,0.1) !important; border-radius:8px !important; color:#ece8f8 !important; }
.stSelectbox > div > div:hover { border-color:rgba(200,160,74,0.4) !important; }

.stSlider > div > div > div { background:rgba(200,160,74,0.3) !important; }
.stSlider > div > div > div > div { background:#c8a04a !important; }

.stFileUploader { background:rgba(255,255,255,0.03) !important; border:2px dashed rgba(200,160,74,0.2) !important; border-radius:12px !important; }
.stFileUploader:hover { border-color:rgba(200,160,74,0.5) !important; }

[data-testid="metric-container"] { background:rgba(255,255,255,0.04) !important; border:1px solid rgba(255,255,255,0.08) !important; border-radius:12px !important; padding:20px !important; transition:all .3s !important; }
[data-testid="metric-container"]:hover { border-color:rgba(200,160,74,0.3) !important; transform:translateY(-2px) !important; }
[data-testid="stMetricValue"] { color:#c8a04a !important; font-family:'Cormorant',serif !important; font-size:2rem !important; }
[data-testid="stMetricLabel"] { color:rgba(236,232,248,0.5) !important; font-size:.75rem !important; }

div[data-testid="stSidebar"] { background:rgba(8,8,18,0.95) !important; border-right:1px solid rgba(255,255,255,0.05) !important; backdrop-filter:blur(20px) !important; }
div[data-testid="stSidebar"] .stMarkdown h2 { font-family:'Cormorant',serif !important; font-style:italic !important; color:#c8a04a !important; font-size:1.4rem !important; font-weight:300 !important; }

.stSuccess { background:rgba(200,160,74,0.08) !important; border:1px solid rgba(200,160,74,0.2) !important; border-radius:10px !important; }
.stInfo { background:rgba(139,124,248,0.08) !important; border:1px solid rgba(139,124,248,0.2) !important; border-radius:10px !important; }
.stError { background:rgba(248,100,100,0.08) !important; border:1px solid rgba(248,100,100,0.2) !important; border-radius:10px !important; }
.stWarning { background:rgba(248,180,100,0.08) !important; border:1px solid rgba(248,180,100,0.2) !important; border-radius:10px !important; }
.stSpinner > div { border-top-color:#c8a04a !important; }

.aura-card { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07); border-radius:16px; padding:28px; margin-bottom:16px; transition:all .3s; position:relative; overflow:hidden; }
.aura-card::before { content:''; position:absolute; top:0;left:0;right:0; height:2px; background:linear-gradient(90deg,#c8a04a,#8b7cf8); transform:scaleX(0); transition:transform .4s; transform-origin:left; }
.aura-card:hover::before { transform:scaleX(1); }
.aura-card:hover { border-color:rgba(200,160,74,0.2); transform:translateY(-2px); box-shadow:0 8px 32px rgba(0,0,0,0.3); }

.aura-footer { text-align:center; padding:32px 0 16px; font-family:'DM Mono',monospace; font-size:.62rem; letter-spacing:.15em; color:rgba(236,232,248,0.2); text-transform:uppercase; border-top:1px solid rgba(255,255,255,0.05); margin-top:48px; }
::-webkit-scrollbar { width:4px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:rgba(200,160,74,0.3); border-radius:2px; }
::-webkit-scrollbar-thumb:hover { background:rgba(200,160,74,0.6); }
.stDownloadButton > button { background:transparent !important; border:1px solid rgba(200,160,74,0.4) !important; color:#c8a04a !important; border-radius:8px !important; font-family:'DM Mono',monospace !important; font-size:.7rem !important; letter-spacing:.1em !important; transition:all .3s !important; }
.stDownloadButton > button:hover { background:rgba(200,160,74,0.1) !important; transform:translateY(-2px) !important; }
.stCaption { color:rgba(236,232,248,0.35) !important; font-family:'DM Mono',monospace !important; font-size:.65rem !important; }
hr { border-color:rgba(255,255,255,0.06) !important; }
</style>
""", unsafe_allow_html=True)

# ── VOICE TO TEXT JS COMPONENT ──
VOICE_INPUT_JS = """
<script>
let mediaRecorder = null;
let audioChunks   = [];
let isRecording   = false;

function startVoiceRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        mediaRecorder  = new MediaRecorder(stream);
        audioChunks    = [];
        isRecording    = true;
        document.getElementById('voiceStatus').innerHTML =
            '<span class="recording-pulse"></span> Recording...';
        document.getElementById('voiceBtn').textContent = '⏹ Stop';

        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
        mediaRecorder.onstop = () => {
            const blob   = new Blob(audioChunks, { type: 'audio/webm' });
            const reader = new FileReader();
            reader.onloadend = () => {
                const b64 = reader.result.split(',')[1];
                // Send to Streamlit via query param trick
                const input = window.parent.document.querySelector('input[aria-label="voice_data_input"]');
                if (input) {
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(input, b64);
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                }
                document.getElementById('voiceStatus').innerHTML = '✦ Click mic to speak';
                document.getElementById('voiceBtn').textContent  = '🎙 Speak';
                isRecording = false;
            };
            reader.readAsDataURL(blob);
            stream.getTracks().forEach(t => t.stop());
        };
        mediaRecorder.start();
    })
    .catch(err => {
        document.getElementById('voiceStatus').innerHTML = '❌ Mic access denied';
    });
}

function stopVoiceRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
    }
}

function toggleRecording() {
    if (!isRecording) startVoiceRecording();
    else               stopVoiceRecording();
}
</script>
<div class="voice-btn-wrap">
    <button id="voiceBtn" onclick="toggleRecording()"
        style="background:linear-gradient(135deg,#8b7cf8,#6b5cf0);color:#fff;border:none;
               border-radius:8px;padding:10px 20px;font-family:'Syne',sans-serif;
               font-weight:700;font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;
               cursor:pointer;transition:all .3s;display:flex;align-items:center;gap:8px;">
        🎙 Speak
    </button>
    <span id="voiceStatus" class="voice-status">✦ Click mic to speak</span>
</div>
"""

# ── TTS HELPER ──
def text_to_speech_html(text, lang="en"):
    """Generate HTML audio player with Web Speech API TTS."""
    # Clean text for JS
    clean = text.replace("'", "\\'").replace("\n", " ").replace('"', '\\"')[:500]
    lang_map = {"English": "en-US", "Hindi": "hi-IN", "Hinglish": "hi-IN", "Marathi": "mr-IN"}
    voice_lang = lang_map.get(lang, "en-US")
    html = f"""
    <div class="tts-wrap">
        <span class="tts-label">🔊 Listen</span>
        <button onclick="speakText()" id="ttsBtn"
            style="background:rgba(200,160,74,0.15);border:1px solid rgba(200,160,74,0.3);
                   color:#c8a04a;border-radius:6px;padding:6px 14px;cursor:pointer;
                   font-family:'DM Mono',monospace;font-size:.65rem;letter-spacing:.1em;
                   transition:all .3s;">
            ▶ Play
        </button>
        <button onclick="stopSpeak()"
            style="background:rgba(248,100,100,0.1);border:1px solid rgba(248,100,100,0.2);
                   color:#f06060;border-radius:6px;padding:6px 14px;cursor:pointer;
                   font-family:'DM Mono',monospace;font-size:.65rem;letter-spacing:.1em;
                   transition:all .3s;">
            ⏹ Stop
        </button>
    </div>
    <script>
    function speakText() {{
        window.speechSynthesis.cancel();
        const utt  = new SpeechSynthesisUtterance('{clean}');
        utt.lang   = '{voice_lang}';
        utt.rate   = 0.95;
        utt.pitch  = 1.0;
        const voices = window.speechSynthesis.getVoices();
        const match  = voices.find(v => v.lang.startsWith('{voice_lang[:2]}'));
        if (match) utt.voice = match;
        document.getElementById('ttsBtn').textContent = '🔊 Speaking...';
        utt.onend = () => document.getElementById('ttsBtn').textContent = '▶ Play';
        window.speechSynthesis.speak(utt);
    }}
    function stopSpeak() {{
        window.speechSynthesis.cancel();
        const btn = document.getElementById('ttsBtn');
        if (btn) btn.textContent = '▶ Play';
    }}
    </script>
    """
    return html

# ── MODELS ──
MODELS = {
    "⚡ Llama 3.1 8B (Fast)":        "llama-3.1-8b-instant",
    "🧠 Llama 3.3 70B (Smart)":      "llama-3.3-70b-versatile",
    "💎 Mixtral 8x7B (Balanced)":    "mixtral-8x7b-32768",
    "🔬 Gemma 2 9B (Google)":        "gemma2-9b-it",
    "🚀 DeepSeek R1 (Reasoning)":    "deepseek-r1-distill-llama-70b",
}

LANGUAGES = {
    "English":  "Respond in English only.",
    "Hindi":    "Hamesha Hindi mein jawab do.",
    "Hinglish": "Hinglish mein jawab do — Hindi aur English mix karke, jaise dost baat karte hain.",
    "Marathi":  "Marathi madhe uttar dya.",
}

# ── HEADER ──
st.markdown("""
<div class="aura-header">
    <div class="aura-logo">Aura <span>AI</span></div>
    <div class="aura-tagline">✦ &nbsp; Multi-Model Intelligence &nbsp; ✦</div>
    <div class="aura-divider"></div>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("## ✦ Aura Settings")
    st.markdown("---")

    feature = st.selectbox("Choose Feature", [
        "💬 AI Chat",
        "🎨 Image Generator",
        "🖼 Image Analyzer",
        "📄 PDF Chat",
        "🌤 Weather",
        "💻 Code Assistant",
    ])

    if "Chat" in feature or "Code" in feature or "PDF" in feature:
        st.markdown("**AI Model**")
        selected_model_name = st.selectbox("Model", list(MODELS.keys()))
        selected_model = MODELS[selected_model_name]

        st.markdown("**Language**")
        selected_lang = st.selectbox("Language", list(LANGUAGES.keys()))

        temperature = st.slider("Creativity", 0.1, 1.0, 0.7)
        max_tokens  = st.slider("Max Tokens", 100, 4000, 1000)

        if st.button("Clear Chat", use_container_width=True):
            for key in ["messages", "pdf_text", "voice_transcript"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        if "messages" in st.session_state and len(st.session_state.messages) > 0:
            chat_export = "\n\n".join([
                f"{'You' if m['role']=='user' else 'Aura'}: {m['content']}"
                for m in st.session_state.messages
            ])
            st.download_button(
                "Export Chat", chat_export,
                file_name=f"aura_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain", use_container_width=True
            )

    st.markdown("---")
    st.caption("Built by Rupal Darode ✦")


# ── HELPER: CALL GROQ ──
def call_groq(messages, model, temperature=0.7, max_tokens=1000):
    try:
        GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    except Exception:
        return "❌ GROQ_API_KEY not found in Streamlit secrets."
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type":  "application/json"
        }
        payload = {
            "model": model, "messages": messages,
            "temperature": temperature, "max_tokens": max_tokens,
        }
        res  = requests.post("https://api.groq.com/openai/v1/chat/completions",
                             headers=headers, json=payload, timeout=30)
        data = res.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        elif "error" in data:
            return f"❌ API Error: {data['error']['message']}"
        else:
            return f"❌ Unexpected: {data}"
    except requests.exceptions.Timeout:
        return "⏱ Request timed out."
    except Exception as e:
        return f"❌ Error: {str(e)}"


# ── HELPER: TRANSCRIBE AUDIO VIA GROQ WHISPER ──
def transcribe_audio(audio_b64: str) -> str:
    try:
        GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    except Exception:
        return ""
    try:
        audio_bytes = base64.b64decode(audio_b64)
        files   = {"file": ("audio.webm", audio_bytes, "audio/webm")}
        data    = {"model": "whisper-large-v3"}
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        res = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers=headers, files=files, data=data, timeout=30
        )
        result = res.json()
        return result.get("text", "")
    except Exception:
        return ""


# ── HELPER: RENDER CHAT WITH VOICE ──
def render_chat_with_voice(system_prompt, lang="English"):
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # TTS button on every assistant message
            if msg["role"] == "assistant":
                st.components.v1.html(text_to_speech_html(msg["content"], lang), height=60)

    # ── VOICE INPUT SECTION ──
    st.markdown("---")
    st.markdown('<div style="font-family:\'DM Mono\',monospace;font-size:.65rem;letter-spacing:.18em;color:rgba(200,160,74,0.5);text-transform:uppercase;margin-bottom:8px;">🎙 Voice Input</div>', unsafe_allow_html=True)

    # Browser-based speech recognition (Web Speech API)
    voice_html = """
    <script>
    let recognition = null;
    let isListening = false;

    function toggleVoice() {
        const btn    = document.getElementById('micBtn');
        const status = document.getElementById('micStatus');
        const output = document.getElementById('transcript');

        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            status.textContent = '❌ Browser not supported. Use Chrome.';
            return;
        }

        if (isListening) {
            recognition.stop();
            return;
        }

        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SR();
        recognition.continuous      = false;
        recognition.interimResults  = true;
        recognition.lang            = 'en-IN';

        recognition.onstart = () => {
            isListening = true;
            btn.innerHTML = '<span style="display:inline-block;width:10px;height:10px;background:#f05050;border-radius:50%;animation:recPulse 1s infinite;margin-right:6px;"></span>Listening...';
            btn.style.background = 'linear-gradient(135deg,#f05050,#c03030)';
            status.textContent   = '🔴 Speak now...';
        };
        recognition.onresult = (e) => {
            let interim = '', final = '';
            for (let i = e.resultIndex; i < e.results.length; i++) {
                if (e.results[i].isFinal) final   += e.results[i][0].transcript;
                else                       interim += e.results[i][0].transcript;
            }
            output.value = final || interim;
            status.textContent = interim ? '💬 ' + interim : '✅ Got it!';
        };
        recognition.onerror = (e) => {
            status.textContent = '❌ ' + e.error + '. Try again.';
            resetBtn();
        };
        recognition.onend = () => {
            isListening = false;
            resetBtn();
            // Auto-fill chat input if we got text
            const txt = output.value.trim();
            if (txt) {
                status.textContent = '✅ Transcript ready — paste below or click Send';
                // Try to fill streamlit chat input
                const chatInputs = window.parent.document.querySelectorAll('textarea');
                chatInputs.forEach(inp => {
                    if (inp.getAttribute('data-testid') === 'stChatInputTextArea') {
                        const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;
                        setter.call(inp, txt);
                        inp.dispatchEvent(new Event('input',{bubbles:true}));
                    }
                });
            }
        };
        recognition.start();
    }

    function resetBtn() {
        const btn  = document.getElementById('micBtn');
        const stat = document.getElementById('micStatus');
        if (btn)  { btn.innerHTML = '🎙 Speak'; btn.style.background = 'linear-gradient(135deg,#8b7cf8,#6b5cf0)'; }
        isListening = false;
    }

    function copyTranscript() {
        const txt = document.getElementById('transcript').value;
        if (!txt) return;
        navigator.clipboard.writeText(txt).then(() => {
            document.getElementById('micStatus').textContent = '📋 Copied! Paste in chat below.';
        });
    }
    </script>

    <style>
    @keyframes recPulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(1.4)} }
    #micBtn {
        background: linear-gradient(135deg,#8b7cf8,#6b5cf0);
        color: #fff; border: none; border-radius: 8px;
        padding: 10px 22px; font-weight: 700; font-size: .72rem;
        letter-spacing: .12em; text-transform: uppercase;
        cursor: pointer; transition: all .3s; margin-right:8px;
    }
    #micBtn:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(139,124,248,0.3); }
    #copyBtn {
        background: rgba(200,160,74,0.12); color: #c8a04a;
        border: 1px solid rgba(200,160,74,0.3); border-radius: 8px;
        padding: 10px 18px; font-size: .7rem; letter-spacing: .1em;
        text-transform: uppercase; cursor: pointer; transition: all .3s;
    }
    #copyBtn:hover { background: rgba(200,160,74,0.2); }
    #transcript {
        width: 100%; margin-top: 10px; padding: 10px 14px;
        background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px; color: #ece8f8; font-size: .85rem;
        font-family: 'Syne', sans-serif; resize: none; min-height: 44px;
        transition: border-color .3s;
    }
    #transcript:focus { outline: none; border-color: rgba(200,160,74,0.5); }
    #micStatus { font-family: 'DM Mono',monospace; font-size: .62rem; color: rgba(200,160,74,0.6); letter-spacing:.1em; margin-top:6px; display:block; }
    </style>

    <div>
        <button id="micBtn" onclick="toggleVoice()">🎙 Speak</button>
        <button id="copyBtn" onclick="copyTranscript()">📋 Copy</button>
        <textarea id="transcript" placeholder="Your speech will appear here..." rows="2"></textarea>
        <span id="micStatus">✦ Click mic → speak → copy → paste in chat</span>
    </div>
    """
    st.components.v1.html(voice_html, height=160)

    # Text chat input
    st.markdown('<div style="font-family:\'DM Mono\',monospace;font-size:.65rem;letter-spacing:.18em;color:rgba(200,160,74,0.5);text-transform:uppercase;margin:12px 0 6px;">💬 Type or paste message</div>', unsafe_allow_html=True)
    prompt = st.chat_input("Message Aura...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        all_messages = [{"role": "system", "content": system_prompt}] + [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        with st.chat_message("assistant"):
            with st.spinner(""):
                reply = call_groq(all_messages, selected_model, temperature, max_tokens)
                st.markdown(reply)
                # Auto TTS for latest reply
                st.components.v1.html(text_to_speech_html(reply, lang), height=60)
                st.session_state.messages.append({"role": "assistant", "content": reply})


# ══════════════════════════════════════════
# FEATURE 1: AI CHAT
# ══════════════════════════════════════════
if "AI Chat" in feature:
    st.markdown('<div class="sec-title">💬 AI Chat</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Multi-model conversational intelligence · Voice enabled</div>', unsafe_allow_html=True)
    st.caption(f"Model: {selected_model_name}  ·  Language: {selected_lang}")

    system_prompt = f"You are Aura, a helpful and friendly AI assistant. {LANGUAGES[selected_lang]}"
    render_chat_with_voice(system_prompt, selected_lang)


# ══════════════════════════════════════════
# FEATURE 2: IMAGE GENERATOR
# ══════════════════════════════════════════
elif "Image Generator" in feature:
    st.markdown('<div class="sec-title">🎨 Image Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Powered by Pollinations AI — Free & unlimited</div>', unsafe_allow_html=True)

    styles = {
        "None": "", "Realistic": ", ultra realistic, 8k, cinematic lighting",
        "Anime": ", anime style, vibrant colors, Studio Ghibli",
        "Oil Painting": ", oil painting, detailed brushwork, museum quality",
        "Cyberpunk": ", cyberpunk, neon lights, futuristic city, blade runner",
        "Watercolor": ", watercolor art, soft colors, artistic",
        "Sketch": ", pencil sketch, hand drawn, detailed",
    }

    st.markdown('<div class="aura-card">', unsafe_allow_html=True)
    image_prompt = st.text_area("Describe your image",
                                placeholder="A beautiful Indian woman in traditional saree, golden hour...", height=100)
    col1, col2, col3 = st.columns(3)
    with col1: style  = st.selectbox("Style",  list(styles.keys()))
    with col2: width  = st.slider("Width",  256, 1024, 512, step=64)
    with col3: height_val = st.slider("Height", 256, 1024, 512, step=64)
    negative = st.text_input("Negative prompt", placeholder="blurry, ugly, distorted...")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("✦ Generate Image", use_container_width=True):
        if image_prompt.strip():
            with st.spinner("Creating your image..."):
                try:
                    full_prompt = image_prompt + styles[style]
                    encoded     = urllib.parse.quote(full_prompt)
                    url         = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height_val}&nologo=true"
                    response    = requests.get(url, timeout=60)
                    response.raise_for_status()
                    image = Image.open(BytesIO(response.content))
                    st.image(image, use_container_width=True)
                    buf = BytesIO()
                    image.save(buf, format="PNG")
                    st.download_button("Download Image", buf.getvalue(),
                                       file_name="aura_image.png", mime="image/png",
                                       use_container_width=True)
                except Exception as e:
                    st.error(f"Failed: {e}")
        else:
            st.warning("Please enter a prompt!")


# ══════════════════════════════════════════
# FEATURE 3: IMAGE ANALYZER
# ══════════════════════════════════════════
elif "Image Analyzer" in feature:
    st.markdown('<div class="sec-title">🖼 Image Analyzer</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Upload any image and ask anything about it</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload an image", type=["png","jpg","jpeg","webp"])
    if uploaded:
        image = Image.open(uploaded)
        st.image(image, use_container_width=True)
        st.markdown("**Quick Actions**")
        col1, col2, col3, col4 = st.columns(4)
        quick_q = ""
        with col1:
            if st.button("Describe"):  quick_q = "Describe this image in detail."
        with col2:
            if st.button("Colors"):    quick_q = "What are the main colors?"
        with col3:
            if st.button("Mood"):      quick_q = "What is the mood or emotion?"
        with col4:
            if st.button("Objects"):   quick_q = "List all objects you can identify."

        user_q = st.text_input("Or ask your own question:", value=quick_q,
                               placeholder="What is happening in this image?")
        if st.button("Analyze", use_container_width=True):
            if user_q:
                with st.spinner("Analyzing..."):
                    reply = call_groq([
                        {"role": "system", "content": "You are an expert image analyst."},
                        {"role": "user",   "content": f"I have uploaded an image. {user_q}"}
                    ], "llama-3.3-70b-versatile", 0.3, 1000)
                    st.success(reply)
                    st.components.v1.html(text_to_speech_html(reply), height=60)
            else:
                st.warning("Please enter a question!")
    else:
        st.info("Upload an image to get started!")


# ══════════════════════════════════════════
# FEATURE 4: PDF CHAT
# ══════════════════════════════════════════
elif "PDF" in feature:
    st.markdown('<div class="sec-title">📄 PDF Chat</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Upload a PDF and have a conversation with it</div>', unsafe_allow_html=True)

    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])
    if uploaded_pdf:
        if "pdf_text" not in st.session_state:
            with st.spinner("Reading PDF..."):
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_pdf.read()))
                    text = "".join(page.extract_text() + "\n" for page in pdf_reader.pages)
                    st.session_state.pdf_text = text[:8000]
                    st.success(f"PDF loaded — {len(pdf_reader.pages)} pages")
                except Exception as e:
                    st.error(f"Could not read PDF: {e}")

        if "pdf_text" in st.session_state:
            st.caption(f"PDF loaded · {len(st.session_state.pdf_text)} characters")
            system_prompt = f"""You are a helpful assistant. Answer based on this document:\n\n---\n{st.session_state.pdf_text}\n---\n\nIf not in document, say so. {LANGUAGES[selected_lang]}"""
            render_chat_with_voice(system_prompt, selected_lang)
    else:
        st.info("Upload a PDF to start chatting with it!")
        for key in ["messages", "pdf_text"]:
            if key in st.session_state:
                del st.session_state[key]


# ══════════════════════════════════════════
# FEATURE 5: WEATHER
# ══════════════════════════════════════════
elif "Weather" in feature:
    st.markdown('<div class="sec-title">🌤 Weather</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Real-time weather for any city worldwide</div>', unsafe_allow_html=True)

    st.markdown('<div class="aura-card">', unsafe_allow_html=True)
    col1, col2 = st.columns([3,1])
    with col1: city = st.text_input("Enter city name", placeholder="Nagpur, Mumbai, Delhi...")
    with col2: unit = st.selectbox("Unit", ["Celsius","Fahrenheit"])
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Get Weather", use_container_width=True):
        if city.strip():
            with st.spinner("Fetching weather..."):
                try:
                    unit_sym = "°C" if unit == "Celsius" else "°F"
                    geo_res  = requests.get(
                        f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1",
                        timeout=10).json()
                    if "results" not in geo_res or not geo_res["results"]:
                        st.error("City not found.")
                    else:
                        loc  = geo_res["results"][0]
                        lat, lon = loc["latitude"], loc["longitude"]
                        name     = loc.get("name", city)
                        country  = loc.get("country", "")
                        w = requests.get(
                            f"https://api.open-meteo.com/v1/forecast?"
                            f"latitude={lat}&longitude={lon}"
                            f"&current=temperature_2m,relative_humidity_2m,"
                            f"wind_speed_10m,weather_code,apparent_temperature"
                            f"&temperature_unit={'celsius' if unit=='Celsius' else 'fahrenheit'}",
                            timeout=10).json()
                        curr     = w["current"]
                        temp     = curr["temperature_2m"]
                        feels    = curr["apparent_temperature"]
                        humidity = curr["relative_humidity_2m"]
                        wind     = curr["wind_speed_10m"]
                        code     = curr["weather_code"]
                        desc_map = {
                            0:"☀️ Clear",1:"🌤 Mainly Clear",2:"⛅ Partly Cloudy",
                            3:"☁️ Overcast",45:"🌫 Foggy",51:"🌦 Drizzle",
                            61:"🌧 Light Rain",63:"🌧 Rain",65:"🌧 Heavy Rain",
                            71:"🌨 Snow",80:"🌦 Showers",95:"⛈ Thunderstorm",
                        }
                        desc = desc_map.get(code, "🌡 Unknown")
                        st.success(f"**{name}, {country}**")
                        c1,c2,c3,c4 = st.columns(4)
                        c1.metric("Temperature", f"{temp}{unit_sym}", f"Feels {feels}{unit_sym}")
                        c2.metric("Humidity",    f"{humidity}%")
                        c3.metric("Wind Speed",  f"{wind} km/h")
                        c4.metric("Condition",   desc)
                        with st.spinner("Getting AI tip..."):
                            tip = call_groq([
                                {"role":"system","content":"Give a short 2-3 line practical weather tip."},
                                {"role":"user",  "content":f"Weather: {temp}{unit_sym}, {desc}, humidity {humidity}%."}
                            ], "llama-3.1-8b-instant", 0.7, 200)
                            st.info(f"💡 {tip}")
                            st.components.v1.html(text_to_speech_html(tip), height=60)
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter a city name!")


# ══════════════════════════════════════════
# FEATURE 6: CODE ASSISTANT
# ══════════════════════════════════════════
elif "Code" in feature:
    st.markdown('<div class="sec-title">💻 Code Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Write, debug, explain and convert code</div>', unsafe_allow_html=True)

    st.markdown('<div class="aura-card">', unsafe_allow_html=True)
    code_action = st.selectbox("What do you want?", [
        "✍️ Write code for me", "🐛 Debug my code", "📖 Explain this code",
        "🔄 Convert to another language", "⚡ Optimize my code", "🧪 Write tests for my code",
    ])
    lang_options = ["Python","JavaScript","Java","C++","SQL","HTML/CSS","React","Other"]
    col1, col2 = st.columns(2)
    with col1: code_lang   = st.selectbox("Language", lang_options)
    with col2: target_lang = st.selectbox("Convert TO", lang_options) if "Convert" in code_action else None
    user_input = st.text_area("Describe what you want / Paste your code", height=180,
                              placeholder="Write a function to sort a list in Python...")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("✦ Run", use_container_width=True):
        if user_input.strip():
            with st.spinner("Processing..."):
                prompts = {
                    "✍️ Write code for me":          f"Write clean {code_lang} code for: {user_input}.",
                    "🐛 Debug my code":              f"Debug this {code_lang} code:\n\n{user_input}",
                    "📖 Explain this code":          f"Explain this {code_lang} code:\n\n{user_input}",
                    "🔄 Convert to another language":f"Convert {code_lang} to {target_lang}:\n\n{user_input}",
                    "⚡ Optimize my code":           f"Optimize this {code_lang} code:\n\n{user_input}",
                    "🧪 Write tests for my code":    f"Write unit tests for:\n\n{user_input}",
                }
                reply = call_groq([
                    {"role":"system","content":"You are an expert programmer. Use markdown code blocks."},
                    {"role":"user",  "content":prompts[code_action]}
                ], selected_model, 0.3, max_tokens)
                st.markdown(reply)
                st.download_button("Download Response", reply,
                                   file_name="aura_code.txt", mime="text/plain")
        else:
            st.warning("Please enter your code or description!")


# ── FOOTER ──
st.markdown("""
<div class="aura-footer">
    Built with ✦ by Rupal Darode &nbsp;|&nbsp; Aura AI &nbsp;|&nbsp; Powered by Groq + Pollinations
</div>
""", unsafe_allow_html=True)
