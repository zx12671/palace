"""Agent runner and configuration for the Three Departments & Six Ministries."""
import json
import os

from .llm import generate, extract_json, unwrap

PROMPTS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "templates", "agent_prompts",
)

SANSHENG = [
    {"key": "zhongshu", "file": "zhongshu.md", "label": "中书省·草案", "seq": 1},
    {"key": "menxia",   "file": "menxia.md",   "label": "门下省·审议", "seq": 2},
    {"key": "shangshu", "file": "shangshu.md", "label": "尚书省·定稿", "seq": 3},
]

LIUBU = [
    {"key": "libu",        "file": "libu.md",        "label": "吏部·分工", "seq": 4},
    {"key": "hubu",        "file": "hubu.md",        "label": "户部·资源", "seq": 5},
    {"key": "libu_ritual", "file": "libu_ritual.md", "label": "礼部·流程", "seq": 6},
    {"key": "bingbu",      "file": "bingbu.md",      "label": "兵部·执行", "seq": 7},
    {"key": "xingbu",      "file": "xingbu.md",      "label": "刑部·风险", "seq": 8},
    {"key": "gongbu",      "file": "gongbu.md",      "label": "工部·工具", "seq": 9},
]

DEPT_LABELS = {d["key"]: d["label"] for d in LIUBU}


def _read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def run_agent(prompt_file, input_obj, model, api_key):
    """Run one agent and return parsed JSON output (no IO side-effects)."""
    prompt_path = os.path.join(PROMPTS_DIR, prompt_file)
    prompt = _read_text(prompt_path).strip()
    input_json = json.dumps(input_obj, ensure_ascii=False, indent=2)
    full_prompt = (
        f"{prompt}\n\n"
        f"输入 JSON:\n{input_json}\n\n"
        "只输出 JSON，不要包含多余文字。"
    )
    text = generate(full_prompt, model, api_key)
    result = extract_json(text)
    return unwrap(result)
