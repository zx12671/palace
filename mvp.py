#!/usr/bin/env python3
"""Palace MVP - Non-interactive batch mode (backward compatible)."""
import argparse
import json
import os
import sys
from datetime import datetime

from palace.llm import list_models, DEFAULT_MODEL
from palace.agents import run_agent, LIUBU
from palace.renderer import build_markdown


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    parser = argparse.ArgumentParser(description="Palace 批处理模式（非交互）")
    parser.add_argument("--issue", required=True, help="Path to Issue JSON")
    parser.add_argument("--outdir", default="outputs", help="Output directory")
    parser.add_argument(
        "--model", default="auto",
        help="Model name or 'auto' (default: qwen3-max)",
    )
    parser.add_argument(
        "--list-models", action="store_true",
        help="List available models",
    )
    args = parser.parse_args()

    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key:
        print(
            "DASHSCOPE_API_KEY is required. "
            "Set it in your environment.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.list_models:
        models = list_models(api_key)
        for m in models:
            print(m.get("id", ""))
        return

    issue = load_json(args.issue)

    os.makedirs(args.outdir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = issue.get("domain", "company")
    outdir = os.path.join(args.outdir, domain, f"decision_{timestamp}")
    os.makedirs(outdir, exist_ok=True)

    model = args.model
    if model == "auto":
        model = DEFAULT_MODEL

    print(f"\n{'=' * 50}")
    print(f"议题: {issue.get('title', '?')}")
    print(f"模型: {model}")
    print(f"{'=' * 50}")

    def _run(prompt_file, input_obj, label, seq):
        print(f"  ▶ {label} ...", flush=True)
        result = run_agent(prompt_file, input_obj, model, api_key)
        fname = f"{seq:02d}_{prompt_file.replace('.md', '')}.json"
        write_json(os.path.join(outdir, fname), result)
        print(f"  ✓ {label} 完成")
        return result

    print("\n[三省流程]")
    draft = _run("zhongshu.md", issue, "中书省·草案", 1)
    review = _run("menxia.md", draft, "门下省·审议", 2)
    final = _run("shangshu.md", {"Draft": draft, "Review": review}, "尚书省·定稿", 3)

    print("\n[六部执行]")
    liubu = {}
    for dept in LIUBU:
        result = _run(dept["file"], final, dept["label"], dept["seq"])
        liubu[dept["key"]] = result

    exec_plan = {
        "issue_id": final.get("issue_id", draft.get("issue_id", "")),
        "liubu": liubu,
    }
    write_json(os.path.join(outdir, "exec_plan.json"), exec_plan)

    md = build_markdown(issue, draft, review, final, exec_plan)
    write_text(os.path.join(outdir, "decision.md"), md)

    print(f"\nOutputs written to: {outdir}")


if __name__ == "__main__":
    main()
