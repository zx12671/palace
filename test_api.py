#!/usr/bin/env python3
"""最简 DashScope API 调用测试"""
import json
import os
from urllib import request

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
MODEL = "qwen3-max"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

url = f"{BASE_URL}/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}
body = json.dumps({
    "model": MODEL,
    "messages": [{"role": "user", "content": "1+1=?只回答数字"}],
}).encode()

req = request.Request(url, data=body, headers=headers, method="POST")
with request.urlopen(req, timeout=30) as resp:
    data = json.load(resp)

text = data["choices"][0]["message"]["content"]
print(f"回答: {text.strip()}")
