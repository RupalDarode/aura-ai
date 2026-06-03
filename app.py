    "Flan-T5 XL": "google/flan-t5-xl",
}

HF_STT_MODELS = {
    "Whisper Small": "openai/whisper-small",
    "Whisper Base": "openai/whisper-base",
}

HF_IMAGE_MODELS = {
    "BLIP Caption": "Salesforce/blip-image-captioning-large",
    "ViT Image Classification": "google/vit-base-patch16-224",
}

HF_IMAGE_GEN_MODELS = {
    "Stable Diffusion XL": "stabilityai/stable-diffusion-xl-base-1.0",
    "Stable Diffusion 2": "stabilityai/stable-diffusion-2-1",
}

LANGUAGES = {
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
    token = st.secrets.get("HF_TOKEN", "") if hasattr(st, "secrets") else ""
    return token or os.environ.get("HF_TOKEN", "")


def hf_headers(content_type: str | None = "application/json") -> dict:
    token = get_hf_token()
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def hf_api_url(model_id: str) -> str:
    return f"https://api-inference.huggingface.co/models/{model_id}"


def parse_hf_error(response: requests.Response) -> str:
    try:
        data = response.json()
    except Exception:
        return response.text[:500] or "Unknown Hugging Face error."

    if isinstance(data, dict):
        message = data.get("error") or data.get("message") or str(data)
        estimated = data.get("estimated_time")
        if estimated:
            return f"{message} Try again in about {round(float(estimated))} seconds."
        return str(message)
    return str(data)


def call_hf_json(model_id: str, payload: dict, timeout: int = 90):
    response = requests.post(
        hf_api_url(model_id),
        headers=hf_headers(),
        json=payload,
        timeout=timeout,
    )
    if response.status_code >= 400:
        raise RuntimeError(parse_hf_error(response))
    return response.json()


def call_hf_binary(model_id: str, payload: dict, timeout: int = 120) -> bytes:
    response = requests.post(
        hf_api_url(model_id),
        headers=hf_headers(),
        json=payload,
        timeout=timeout,
    )
    if response.status_code >= 400:
        raise RuntimeError(parse_hf_error(response))
    return response.content

