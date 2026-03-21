# Palace Plugin for Claude Code

A multi-agent decision system for Claude Code. Claude acts as all 9 agents from the Tang Dynasty's Three Departments & Six Ministries, while you serve as the Emperor with final approval authority.

三省六部多智能体决策系统 Claude Code 插件。Claude 扮演唐朝三省六部 9 个智能体，用户作为皇上审批裁决，产出结构化决策报告。

## Install | 安装

**From GitHub | 从 GitHub 安装**

```
/plugin marketplace add zx12671/palace
/plugin install palace@palace
```

**Local testing | 本地测试**

```bash
claude --plugin-dir ./palace-plugin
```

**Project-level (no install needed) | 项目级（无需安装）**

Copy `skills/palace/` to your project's `.claude/skills/palace/`.

将 `skills/palace/` 复制到项目的 `.claude/skills/palace/` 即可。

## Usage | 使用

```
/palace Should I quit my job to start a business?
/palace 帮我决定要不要辞职去创业
/palace I need to choose between React and Vue
/palace 我应该选 React 还是 Vue 做前端
```

## How It Works | 工作流程

1. **Build Issue** — Structure your decision as JSON, confirm with the Emperor
2. **Three Departments** — Draft options → Review risks → Finalize recommendation
3. **Emperor's Ruling** — Approve, reject, or revise
4. **Six Ministries** — Roles, budget, process, execution, risks, tools
5. **Report** — Full `decision.md` output

---

1. **构建议题** — 将决策结构化为 JSON，皇上确认
2. **三省流程** — 起草方案 → 审议风险（可打回）→ 定稿推荐
3. **皇上裁决** — 批准 / 打回 / 修改
4. **六部执行** — 分工 / 资源 / 流程 / 执行 / 风险 / 工具
5. **报告** — 生成完整 decision.md 决策报告

## MCP Integration | MCP 集成

During the Six Ministries phase, the plugin can use available MCP tools:

六部执行阶段可调用 MCP 工具实际落地：

- **Notion** — Create project pages, execution dashboards
- **GitHub** — Create issues for milestone tracking
- Other MCP tools as available

All MCP actions require Emperor's approval before execution.

所有 MCP 操作执行前需皇上批准。

## License

MIT
