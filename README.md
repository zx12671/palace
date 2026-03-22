# Palace

A multi-agent personal decision-making system inspired by the Tang Dynasty's "Three Departments and Six Ministries" (三省六部) structure.

唐朝三省六部制启发的多智能体个人决策系统。

---

## Overview | 概述

Palace decomposes complex decisions into a structured four-phase pipeline — **Draft → Review → Finalize → Execute** — powered by 9 AI agents collaborating as the Three Departments and Six Ministries.

Palace 将复杂决策分解为「起草 → 审议 → 定稿 → 执行」四阶段流程，由九个 AI 智能体（三省六部）协同完成，帮助个人做出更全面、更理性的决策。

### Three Departments (Decision) | 三省流程

| Phase | Agent | Role |
|-------|-------|------|
| Draft | Zhongshu (中书省) | Analyze the issue, generate multiple options |
| Review | Menxia (门下省) | Audit the draft, identify risks and gaps |
| Finalize | Shangshu (尚书省) | Synthesize draft + review into a final decision |

### Six Ministries (Execution) | 六部执行

| Ministry | Role |
|----------|------|
| Libu (吏部) | Personnel & role assignments |
| Hubu (户部) | Budget & resource planning |
| Libu Ritual (礼部) | Process & communication |
| Bingbu (兵部) | Execution steps & milestones |
| Xingbu (刑部) | Risk mitigation & compliance |
| Gongbu (工部) | Tools, templates & deliverables |

---

## Quick Start | 快速开始

### Two Ways to Use | 两种使用方式

**1. As a Claude Code Skill (Recommended) | 作为 Claude Code 技能（推荐）**

No API key needed. Claude itself acts as all 9 agents.

无需 API Key，Claude 自身扮演全部 9 个智能体角色。

```
/palace Should I quit my job to start a business?
/palace 帮我决定要不要辞职去创业
```

See [Claude Code Plugin](#claude-code-plugin) section below for installation.

**2. As a Standalone CLI | 作为独立命令行工具**

Requires a DashScope API key (Alibaba Cloud).

需要阿里云 DashScope API Key。

```bash
export DASHSCOPE_API_KEY="your-api-key"

# Batch mode | 批处理模式
python3 mvp.py --issue tests/fixtures/issue_tech_stack.json

# Interactive mode | 交互模式
python3 interactive.py --issue tests/fixtures/issue_tech_stack.json
```

Interactive mode pauses at each checkpoint for user input:

交互模式支持在每个关键节点暂停，让用户参与决策：

- Draft selection | 中书省草案选择
- Review feedback | 门下省审议意见注入
- Final approval | 尚书省定稿确认
- Ministry output review | 六部执行方案审批

---

## Claude Code Plugin | Claude Code 插件

### Install | 安装

**Option A: From GitHub | 从 GitHub 安装**

```
/plugin marketplace add zx12671/palace
/plugin install palace@palace
```


**Option B: Project-level (auto) | 项目级（自动生效）**

Clone this repo and work inside it. The skill at `.claude/skills/palace/` activates automatically.

克隆此仓库并在其中工作，`.claude/skills/palace/` 下的技能自动生效。

### Usage | 使用
合：想在自己的项目里直接用 `/palace` 命令。

```bash
# 1. 在你的项目根目录下创建 .claude/skills/ 目录
mkdir -p /path/to/your-project/.claude/skills/

# 2. 从 palace 仓库复制 skill
cp -r /path/to/palace/.claude/skills/palace /path/to/your-project/.claude/skills/palace

# 3. 进入你的项目，打开 Claude Code
cd /path/to/your-project
claude
```

进入 Claude Code 后直接输入：

```
/palace 帮我决定要不要辞职去创业
```

就这样，不需要 API Key，不需要安装任何依赖。Claude 自身扮演全部 9 个智能体。

```
/palace I need to decide between React and Vue for my frontend
/palace 我应该选 React 还是 Vue 做前端
```

### How It Works | 工作流程

1. **Build Issue** — Claude helps structure your decision as JSON, you confirm
2. **Three Departments** — Draft (options) → Review (risks) → Finalize (recommendation)
3. **Emperor's Ruling** — You approve, reject, or revise the final decision
4. **Six Ministries** — Execute with roles, budget, process, steps, risks, tools
5. **Report** — Full `decision.md` with all analysis

---

1. **构建议题** — Claude 帮助将决策结构化为 JSON，皇上确认
2. **三省流程** — 起草（方案）→ 审议（风险）→ 定稿（推荐）
3. **皇上裁决** — 批准、打回或修改定稿
4. **六部执行** — 分工、资源、流程、执行、风险、工具
5. **报告** — 生成完整的 `decision.md` 决策报告

---

## Project Structure | 项目结构

```
palace/
├── palace/                  # Core package | 核心包
│   ├── llm.py               # DashScope API client (stdlib only)
│   ├── agents.py            # Agent definitions & runner
│   ├── session.py           # Interactive session state machine
│   └── renderer.py          # Markdown report generator
├── templates/
│   └── agent_prompts/       # 9 agent prompt templates
├── schemas/                 # JSON schemas for input/output
├── tests/
│   └── fixtures/            # Sample issue JSON files
├── palace-plugin/           # Claude Code plugin (self-contained)
│   ├── .claude-plugin/
│   │   └── plugin.json
│   └── skills/palace/
│       ├── SKILL.md
│       └── references/
├── .claude/skills/palace/   # Project-level skill
├── mvp.py                   # Batch CLI entry point
├── interactive.py           # Interactive CLI entry point
└── scripts/
    └── package_skill.py     # Skill packaging tool
```

---

## Model | 模型

Default: `qwen3-max` (Alibaba Cloud Qwen, 262K context window) via OpenAI-compatible DashScope API.

默认使用 `qwen3-max`（阿里云千问系列旗舰模型），上下文窗口 262K tokens。

When used as a Claude Code skill, no external model is needed — Claude handles everything.

作为 Claude Code 技能使用时，无需外部模型，Claude 自身处理全部流程。

## Testing | 测试

```bash
# Offline tests (no API key needed)
python -m pytest tests/test_offline.py -v

# Lint
ruff check --select E,F,W .
```

## License

MIT
