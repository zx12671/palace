"""LLM client for DashScope (OpenAI-compatible API)."""
import json
import re
from urllib import request

DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen3-max"


def http_json(method, url, headers=None, data=None):
    payload = None
    if data is not None:
        payload = json.dumps(data).encode("utf-8")
    req = request.Request(url, data=payload, headers=headers or {}, method=method)
    with request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


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


def generate(prompt, model, api_key):
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
