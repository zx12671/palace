"""LLM client supporting DashScope (qwen) and Google Gemini."""
import json
import re
from urllib import request

DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "qwen3-max"
GEMINI_DEFAULT_MODEL = "gemini-3.1-pro-preview"

GEMINI_PREFIXES = ("gemini-",)


def is_gemini_model(model):
    return any(model.lower().startswith(p) for p in GEMINI_PREFIXES)


def http_json(method, url, headers=None, data=None):
    payload = None
    if data is not None:
        payload = json.dumps(data).encode("utf-8")
    req = request.Request(url, data=payload, headers=headers or {}, method=method)
    with request.urlopen(req, timeout=180) as resp:
        return json.load(resp)


# --------------- DashScope (OpenAI-compatible) ---------------

def list_models(api_key):
    url = f"{DASHSCOPE_BASE_URL}/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    data = http_json("GET", url, headers=headers)
    return data.get("data", [])


def pick_strongest_model(models):
    def score(model):
        mid = model.get("id", "").lower()
        tier = 0
        if "max" in mid:
            tier += 4
        elif "plus" in mid:
            tier += 3
        elif "turbo" in mid:
            tier += 2
        elif "lite" in mid or "flash" in mid:
            tier += 1
        m = re.search(r"(\d+(?:\.\d+)?)", mid)
        ver = float(m.group(1)) if m else 0.0
        return ver * 10 + tier

    candidates = [m for m in models if "qwen" in m.get("id", "").lower()]
    if not candidates:
        return None
    candidates.sort(key=score, reverse=True)
    return candidates[0].get("id", "")


def _generate_dashscope(prompt, model, api_key):
    url = f"{DASHSCOPE_BASE_URL}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 32768,
    }
    data = http_json("POST", url, headers=headers, data=body)
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError(f"No choices in response: {data}")
    return choices[0].get("message", {}).get("content", "").strip()


# --------------- Google Gemini ---------------

def list_models_gemini(api_key):
    url = f"{GEMINI_BASE_URL}/models?key={api_key}"
    data = http_json("GET", url)
    return [
        {"id": m["name"].replace("models/", ""), "owned_by": "google"}
        for m in data.get("models", [])
        if "generateContent" in m.get("supportedGenerationMethods", [])
    ]


def _generate_gemini(prompt, model, api_key):
    url = f"{GEMINI_BASE_URL}/models/{model}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 32768,
        },
    }
    data = http_json("POST", url, headers=headers, data=body)
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"No candidates in Gemini response: {data}")
    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts = [p.get("text", "") for p in parts if not p.get("thought")]
    return "".join(text_parts).strip()


# --------------- Unified interface ---------------

def generate(prompt, model, api_key):
    if is_gemini_model(model):
        return _generate_gemini(prompt, model, api_key)
    return _generate_dashscope(prompt, model, api_key)


def extract_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    raise ValueError("Model output is not valid JSON")


def unwrap(obj):
    """Auto-unwrap single-key wrapper like {"Final": {...}}."""
    if isinstance(obj, dict) and len(obj) == 1:
        inner = next(iter(obj.values()))
        if isinstance(inner, dict):
            return inner
    return obj


def deep_get(obj, *keys, default=None):
    """Try multiple possible keys, return the first found."""
    for k in keys:
        if isinstance(obj, dict) and k in obj:
            return obj[k]
    return default
