# Palace Plugin for Claude Code

A multi-agent decision system for Claude Code. Claude acts as all 9 agents from the Tang Dynasty's Three Departments & Six Ministries, while you serve as the Emperor with final approval authority.

三省六部多智能体决策系统 Claude Code 插件。Claude 扮演唐朝三省六部 9 个智能体，用户作为皇上审批裁决，产出结构化决策报告。

## Install | 安装

**From GitHub | 从 GitHub 安装**

```
/plugin marketplace add zx12671/palace 【注册中】
/plugin install palace@palace
```

**Local testing | 本地测试**

```bash
claude --plugin-dir ./palace-plugin
```

**Project-level (no install needed) | 项目级（无需安装）**

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
