# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Palace is a multi-agent personal decision-making system inspired by the Tang Dynasty's "Three Departments & Six Ministries" (三省六部) structure. Users input a decision issue (JSON), and 9 AI agents collaborate to produce a structured decision report with execution plan.

Default LLM: Alibaba Cloud DashScope API with `qwen3-max` (262K context window), using an OpenAI-compatible interface.

## Commands

### Environment
```bash
export DASHSCOPE_API_KEY="your-api-key"  # Required for API calls
```

### Running the System
```bash
# Batch mode (non-interactive)
python3 mvp.py --issue tests/fixtures/issue_tech_stack.json
python3 mvp.py --issue tests/fixtures/issue_tech_stack.json --outdir outputs --model qwen3-max
python3 mvp.py --list-models

# Interactive mode (with checkpoints and user approval at each phase)
python3 interactive.py --issue tests/fixtures/issue_tech_stack.json
python3 interactive.py --resume outputs/personal/decision_YYYYMMDD_HHMMSS/checkpoint.json
```

### Tests
```bash
# Offline unit tests (no API key needed)
python -m pytest tests/test_offline.py -v

# Single test class
python -m pytest tests/test_offline.py::TestExtractJson -v

# All tests (API tests auto-skip if DASHSCOPE_API_KEY not set)
python -m pytest tests/ -v
```

### Lint
```bash
ruff check --select E,F,W .
```

## Architecture

### Agent Pipeline (9 agents, sequential)

**Phase 1 — Three Departments (Decision):**
1. `zhongshu` (中书省) — drafts ≥2 decision options
2. `menxia` (门下省) — reviews draft, identifies ≥3 risks
3. `shangshu` (尚书省) — produces final decision with `imperial_choice`

**Phase 2 — Six Ministries (Execution):**
4. `libu` (吏部) — personnel/role assignments
5. `hubu` (户部) — budget/resources
6. `libu_ritual` (礼部) — process/communication
7. `bingbu` (兵部) — execution steps/milestones
8. `xingbu` (刑部) — risk mitigation
9. `gongbu` (工部) — tools/templates/deliverables

Agent prompts live in `templates/agent_prompts/*.md`. Output schemas are in `schemas/*.json`.

### Core Modules

- **`palace/llm.py`** — DashScope HTTP client (stdlib only, no external deps). Key functions: `generate()`, `extract_json()`, `http_json()`.
- **`palace/agents.py`** — `run_agent(template, context, model)` executes one agent call.
- **`palace/session.py`** — `DecisionSession` state machine (DRAFT → REVIEW → FINAL → DEPT → DONE). Handles checkpoints, user interaction points, and history.
- **`palace/renderer.py`** — `build_markdown()` converts structured JSON to the final `decision.md` report.

### Entry Points vs Core

`mvp.py` and `interactive.py` are thin CLIs that drive `DecisionSession`. The session is UI-agnostic — `interactive.py` registers prompt handlers; `mvp.py` calls `step()` directly.

### Output Structure
```
outputs/{domain}/decision_{timestamp}/
├── 01_zhongshu_draft.json ... 09_gongbu.json  # Per-agent JSON
├── exec_plan.json                               # Execution summary
├── decision.md                                  # Final report
└── checkpoint.json                              # Resume state
```

### No External Dependencies
Runtime uses stdlib only (`urllib`, `json`, `dataclasses`). Dev deps: `pytest`, `ruff`.
