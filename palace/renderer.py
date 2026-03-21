"""Render decision data into Markdown report."""
from .llm import deep_get


def _format_value(val, indent=0):
    """Recursively format any JSON value into readable Markdown."""
    prefix = "  " * indent
    if isinstance(val, str):
        return f"{prefix}{val}"
    if isinstance(val, list):
        lines = []
        for item in val:
            if isinstance(item, dict):
                parts = []
                for k, v in item.items():
                    if isinstance(v, (list, dict)):
                        parts.append(f"**{k}**:\n{_format_value(v, indent + 1)}")
                    else:
                        parts.append(f"**{k}**: {v}")
                lines.append(f"{prefix}- " + " | ".join(parts[:2]))
                for p in parts[2:]:
                    lines.append(f"{prefix}  {p}")
            else:
                lines.append(f"{prefix}- {item}")
        return "\n".join(lines)
    if isinstance(val, dict):
        lines = []
        for k, v in val.items():
            if isinstance(v, (list, dict)):
                lines.append(f"{prefix}- **{k}**:")
                lines.append(_format_value(v, indent + 1))
            else:
                lines.append(f"{prefix}- **{k}**: {v}")
        return "\n".join(lines)
    return f"{prefix}{val}"


def build_markdown(issue, draft, review, final, exec_plan):
    lines = []
    lines.append(f"# {issue.get('title', 'Decision')}")
    lines.append("")

    lines.append("## 背景与问题")
    lines.append(issue.get("background", ""))
    lines.append("")

    # --- Draft ---
    lines.append("## 中书省·草案方案")
    drafts = deep_get(draft, "drafts", "options", "plans", default=[])
    if drafts:
        for i, opt in enumerate(drafts, 1):
            name = deep_get(opt, "name", "title", default=f"方案{i}")
            summary = deep_get(opt, "summary", "description", default="")
            lines.append(f"### 方案{i}: {name}")
            lines.append(f"{summary}")
            for label, keys in [("优势", ("pros", "advantages")),
                                ("劣势", ("cons", "disadvantages")),
                                ("粗步骤", ("rough_steps", "steps"))]:
                items = deep_get(opt, *keys, default=[])
                if items:
                    lines.append(f"**{label}**:")
                    for item in items:
                        lines.append(f"- {item}")
            lines.append("")
    else:
        lines.append(_format_value(draft))
        lines.append("")

    # --- Review ---
    lines.append("## 门下省·审议意见")
    risks = deep_get(review, "risks", "risk_list", "concerns", default=[])
    if risks:
        lines.append("**风险与漏洞**:")
        for r in risks:
            if isinstance(r, dict):
                lines.append(f"- {deep_get(r, 'description', 'risk', default=str(r))}")
            else:
                lines.append(f"- {r}")
    suggestions = deep_get(
        review, "revision_suggestions", "suggestions",
        "revisions", default=[],
    )
    if suggestions:
        lines.append("")
        lines.append("**修订建议**:")
        for s in suggestions:
            lines.append(f"- {s}")
    lines.append("")

    # --- Final ---
    lines.append("## 尚书省·圣裁定稿")
    ic = deep_get(final, "imperial_choice", "choice", "selected", default={})
    if ic:
        ic_name = deep_get(ic, "name", "title", "summary", default="")
        ic_reason = deep_get(ic, "reasoning", "reason", default="")
        lines.append("### 圣裁优先方案")
        lines.append(f"{ic_name}")
        if ic_reason:
            lines.append("")
            lines.append(f"**理由**: {ic_reason}")
    alt = deep_get(final, "alternative", "alternatives", "backup", default=None)
    if alt:
        lines.append("")
        lines.append("### 备选方案")
        if isinstance(alt, list):
            for a in alt:
                a_name = deep_get(a, "name", "summary", default="")
                a_reason = deep_get(a, "reasoning", "reason", default="")
                lines.append(f"- {a_name}")
                if a_reason:
                    lines.append(f"  理由: {a_reason}")
        elif isinstance(alt, dict):
            a_name = deep_get(alt, "name", "summary", default="")
            a_reason = deep_get(alt, "reasoning", "reason", default="")
            lines.append(f"{a_name}")
            if a_reason:
                lines.append("")
                lines.append(f"**理由**: {a_reason}")
    lines.append("")

    # --- Six Ministries ---
    liubu = exec_plan.get("liubu", {})
    dept_names = {
        "libu": "吏部·分工",
        "hubu": "户部·资源",
        "libu_ritual": "礼部·流程",
        "bingbu": "兵部·执行",
        "xingbu": "刑部·风险",
        "gongbu": "工部·工具",
    }
    for key, title in dept_names.items():
        dept = liubu.get(key, {})
        if not dept:
            continue
        lines.append(f"## {title}")
        lines.append(_format_value(dept))
        lines.append("")

    return "\n".join(lines)
