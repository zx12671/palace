# Palace Plugin for Claude Code

三省六部多智能体决策系统。Claude 扮演唐朝三省六部 9 个智能体，用户作为皇上审批裁决。

## 安装

### 方式一：本地安装（测试用）

```bash
claude --plugin-dir ./palace-plugin
```

### 方式二：从 GitHub 安装

在 Claude Code 中运行：

```
/plugin marketplace add zx12671/palace
/plugin install palace@palace
```

### 方式三：项目级（无需安装）

将 `palace-plugin/skills/palace/` 目录复制到项目的 `.claude/skills/palace/` 即可。

## 使用

```
/palace 帮我决定要不要辞职去创业
/palace 我应该选 React 还是 Vue 做前端
```

## 流程

1. 构建 Issue JSON（皇上确认）
2. 中书省起草方案 → 门下省审议（可打回）→ 尚书省定稿
3. 皇上裁决（批准/打回/修改）
4. 六部执行（分工/资源/流程/执行/风险/工具）
5. 生成 decision.md 完整报告
