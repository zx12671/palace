#!/usr/bin/env python3
"""Interactive CLI for Palace decision system."""
import argparse
import json
import os
import sys
from datetime import datetime

from palace.llm import deep_get, DEFAULT_MODEL
from palace.session import DecisionSession

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _print_header(issue, model):
    print(f"\n{'=' * 55}")
    print(f"  议题: {issue.get('title', '?')}")
    print(f"  模型: {model}")
    print(f"{'=' * 55}")


def _print_agent(label, status="running"):
    if status == "running":
        print(f"\n  ▶ {label} ...", end="", flush=True)
    else:
        print(f"\r  ✓ {label} 完成      ")


def _show_drafts(data):
    drafts = deep_get(data, "drafts", "options", "plans", default=[])
    if not drafts:
        print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
        return
    print()
    for i, opt in enumerate(drafts, 1):
        name = deep_get(opt, "name", "title", default=f"方案{i}")
        summary = deep_get(opt, "summary", "description", default="")
        print(f"  [{i}] {name}")
        if summary:
            print(f"      {summary[:80]}{'...' if len(summary) > 80 else ''}")


def _show_review(data):
    print()
    risks = deep_get(data, "risks", "risk_list", "concerns", default=[])
    if risks:
        print("  风险:")
        for i, r in enumerate(risks, 1):
            text = deep_get(r, "description", "risk", default=str(r)) if isinstance(r, dict) else str(r)
            print(f"    {i}. {text[:100]}")
    suggestions = deep_get(data, "revision_suggestions", "suggestions", "revisions", default=[])
    if suggestions:
        print("\n  修订建议:")
        for i, s in enumerate(suggestions, 1):
            print(f"    {i}. {s[:100]}")


def _show_final(data):
    print()
    ic = deep_get(data, "imperial_choice", "choice", "selected", default={})
    if ic:
        name = deep_get(ic, "name", "title", "summary", default="")
        print(f"  圣裁方案: {name[:100]}")
    alt = deep_get(data, "alternative", "alternatives", "backup", default=None)
    if alt:
        if isinstance(alt, dict):
            alt_name = deep_get(alt, "name", "summary", default="")
            print(f"  备选方案: {alt_name[:100]}")
        elif isinstance(alt, list) and alt:
            alt_name = deep_get(alt[0], "name", "summary", default="")
            print(f"  备选方案: {alt_name[:100]}")


def _show_dept(label, data):
    print()
    text = json.dumps(data, ensure_ascii=False, indent=2)
    lines = text.split("\n")
    preview = "\n".join(lines[:15])
    if len(lines) > 15:
        preview += f"\n    ... (共 {len(lines)} 行)"
    print(f"  {preview}")


def _input(prompt, default=""):
    try:
        val = input(prompt).strip()
        return val if val else default
    except (EOFError, KeyboardInterrupt):
        print("\n\n  [中断] 保存断点 ...")
        return "__interrupt__"


# ---------------------------------------------------------------------------
# Interaction handlers
# ---------------------------------------------------------------------------

def prompt_select_draft(result):
    _show_drafts(result.data)
    print()
    choice_str = _input("  请选择你倾向的方案编号（直接回车跳过）: ")
    if choice_str == "__interrupt__":
        return "__interrupt__"
    comment = ""
    if choice_str:
        comment_str = _input("  补充意见（可选，直接回车跳过）: ")
        if comment_str == "__interrupt__":
            return "__interrupt__"
        comment = comment_str
    choice = int(choice_str) if choice_str.isdigit() else None
    return {"choice": choice, "comment": comment}


def prompt_review_opinion(result):
    _show_review(result.data)
    print()
    print("  [1] 确认，进入定稿")
    print("  [2] 补充意见后进入定稿")
    print("  [3] 驳回，让中书省重新出草案")
    sel = _input("  请选择: ", "1")
    if sel == "__interrupt__":
        return "__interrupt__"
    if sel == "3":
        return {"action": "reject"}
    if sel == "2":
        comment = _input("  你的意见: ")
        if comment == "__interrupt__":
            return "__interrupt__"
        return {"action": "comment", "comment": comment}
    return {"action": "approve"}


def prompt_confirm_final(result):
    _show_final(result.data)
    print()
    print("  [1] 确认，进入六部执行")
    print("  [2] 驳回到审议阶段")
    print("  [3] 驳回到草案阶段")
    sel = _input("  请选择: ", "1")
    if sel == "__interrupt__":
        return "__interrupt__"
    if sel == "3":
        return {"action": "reject_to_draft"}
    if sel == "2":
        return {"action": "reject_to_review"}
    return {"action": "approve"}


def prompt_confirm_dept(result):
    _show_dept(result.agent_label, result.data)
    print()
    sel = _input(f"  [{result.agent_label}] [1] 确认  [2] 驳回重来: ", "1")
    if sel == "__interrupt__":
        return "__interrupt__"
    if sel == "2":
        comment = _input("  补充意见（可选）: ")
        if comment == "__interrupt__":
            return "__interrupt__"
        return {"action": "redo", "comment": comment}
    return {"action": "approve"}


PROMPT_HANDLERS = {
    "select_draft": prompt_select_draft,
    "review_opinion": prompt_review_opinion,
    "confirm_final": prompt_confirm_final,
    "confirm_dept": prompt_confirm_dept,
}


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_interactive(issue_path, model, outdir, resume_path=None):
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key:
        print("DASHSCOPE_API_KEY is required.", file=sys.stderr)
        sys.exit(1)

    issue = None
    if resume_path:
        session = DecisionSession.load_checkpoint(resume_path, api_key)
        issue = session.issue
        print("  从断点恢复...")
    else:
        with open(issue_path, "r", encoding="utf-8") as f:
            issue = json.load(f)
        if model == "auto":
            model = DEFAULT_MODEL
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = issue.get("domain", "company")
        full_outdir = os.path.join(outdir, domain, f"decision_{timestamp}")
        session = DecisionSession(issue, model, api_key, full_outdir)

    _print_header(session.issue, session.model)

    user_input = None
    while True:
        _print_agent(session.state, "running")
        result = session.step(user_input)
        _print_agent(result.agent_label, "done")

        if result.action == "done":
            report = result.data.get("report_path", "")
            print(f"\n  决策报告已生成: {report}")
            break

        handler = PROMPT_HANDLERS.get(result.action)
        if handler:
            user_input = handler(result)
            if user_input == "__interrupt__":
                session.save_checkpoint()
                cp = os.path.join(session.outdir, "checkpoint.json")
                print(f"  断点已保存: {cp}")
                print(f"  恢复命令: python3 interactive.py --resume {cp}")
                sys.exit(0)
        else:
            user_input = None

    session.save_checkpoint()


def main():
    parser = argparse.ArgumentParser(description="Palace 交互式决策系统")
    parser.add_argument("--issue", help="Issue JSON 文件路径")
    parser.add_argument("--outdir", default="outputs", help="输出目录")
    parser.add_argument("--model", default="auto", help="模型名称或 'auto'")
    parser.add_argument("--resume", help="从断点 checkpoint.json 恢复")
    args = parser.parse_args()

    if not args.issue and not args.resume:
        parser.error("需要 --issue 或 --resume 参数")

    run_interactive(args.issue, args.model, args.outdir, args.resume)


if __name__ == "__main__":
    main()
