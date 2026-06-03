# 🤖 Aura AI Assistant

> **A powerful multi-feature AI assistant built with Streamlit + Groq API**
> 
> Built by **Rupal Darode** 🚀

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red?style=flat-square&logo=streamlit)
![Groq](https://img.shields.io/badge/Groq-API-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| 💬 **AI Chat** | Multi-model chatbot with memory, image attach & language selector |
| 🎨 **Image Generator** | Generate images from text with style presets |
| 🖼 **Image Analyzer** | Upload any image and ask questions about it |
| 📄 **PDF Chat** | Upload a PDF and have a conversation with it |
| 🌤 **Weather** | Real-time weather for any city + AI tips |
| 💻 **Code Assistant** | Write, debug, explain, convert & optimize code |

---

## 🤖 AI Models Available

- ⚡ **Llama 3.1 8B** — Fast responses, everyday tasks
- 🧠 **Llama 3.3 70B** — Smart, complex reasoning
- 💎 **Mixtral 8x7B** — Balanced speed and quality
- 🔬 **Gemma 2 9B** — Google's efficient model
- 🚀 **DeepSeek R1** — Deep reasoning and analysis

---

## 🚀 Live Demo

👉 **[aura-ai-rupal.streamlit.app](https://aura-ai-rupal.streamlit.app)**

---

## 🛠 Tech Stack

- **Frontend:** Streamlit
- **AI Models:** Groq API (Llama, Mixtral, Gemma, DeepSeek)
- **Image Generation:** Pollinations AI (Free)
- **Weather:** Open-Meteo API (Free, no key needed)
- **PDF Reading:** PyPDF2
- **Language:** Python 3.10+

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/RupalDarode/aura-ai.git
cd aura-ai
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add your Groq API key

Create a file `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

Get your free API key at 👉 [console.groq.com](https://console.groq.com)

### 4. Run the app
```bash
streamlit run app.py
```

---

## 🌐 Deploy on Streamlit Cloud

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Add `GROQ_API_KEY` in **Settings → Secrets**
5. Click **Deploy** ✅

---

## 📁 Project Structure

```
aura-ai/
│
├── app.py              # Main application
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ Yes | Get free at console.groq.com |

---

## 💡 Usage Examples

**AI Chat:**
> Ask anything — general knowledge, creative writing, analysis

**Image Generator:**
> *"A beautiful Indian woman in traditional saree, golden hour, realistic"*

**PDF Chat:**
> Upload your resume, notes, or any PDF and ask questions

**Weather:**
> Type "Nagpur" → get live weather + AI clothing tip

**Code Assistant:**
> *"Write a Python function to scrape a website"*

---

## 🗺 Roadmap

- [ ] Voice input / output
- [ ] WhatsApp integration
- [ ] Save chat history
- [ ] User login system
- [ ] Mobile app version

---

## 👤 Author

**Rupal Darode**
- 📧 rupaldarode96@gmail.com
- 🐙 GitHub: [@RupalDarode](https://github.com/RupalDarode)

---

## 📄 License

MIT License — free to use and modify.

---

<div align="center">
Built with ❤️ using Streamlit + Groq | Aura AI 🤖
</div>
