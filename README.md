# Palace 🏛️

唐朝三省六部制启发的多智能体个人决策系统。

## 概述

Palace 将复杂决策分解为「起草 → 审议 → 定稿 → 执行」四阶段流程，由九个 AI 智能体（三省六部）协同完成，帮助个人做出更全面、更理性的决策。

### 三省流程

| 阶段 | 智能体 | 职责 |
|------|--------|------|
| 起草 | 中书省 | 分析议题，生成多个备选方案 |
| 审议 | 门下省 | 审查草案，指出风险与不足 |
| 定稿 | 尚书省 | 综合草案与审议意见，产出最终决策 |

### 六部执行

| 部门 | 职责 |
|------|------|
| 吏部 | 人事与组织安排 |
| 户部 | 预算与资源规划 |
| 礼部 | 规范与流程制定 |
| 兵部 | 风险防控与应急预案 |
| 刑部 | 合规审查与约束条件 |
| 工部 | 技术实施与工程计划 |

## 快速开始

### 环境要求

- Python 3.9+
- 阿里云 DashScope API Key

### 设置

```bash
export DASHSCOPE_API_KEY="your-api-key"
```

### 批处理模式

```bash
python3 mvp.py --issue tests/fixtures/issue_tech_stack.json
```

### 交互模式

```bash
python3 interactive.py --issue tests/fixtures/issue_tech_stack.json
```

交互模式支持在每个关键节点暂停，让用户参与决策：
- 中书省草案选择
- 门下省审议意见注入
- 尚书省定稿确认
- 六部执行方案审批

## 项目结构

```
palace/
├── palace/              # 核心包
│   ├── __init__.py
│   ├── llm.py           # LLM 客户端（DashScope API）
│   ├── agents.py         # 智能体定义与执行
│   ├── renderer.py       # Markdown 报告生成
│   └── session.py        # 交互式会话状态机
├── templates/
│   └── agent_prompts/    # 各智能体 prompt 模板
├── tests/
│   └── fixtures/         # 测试用议题 JSON
├── interactive.py        # 交互式 CLI 入口
├── mvp.py                # 批处理 CLI 入口
└── docs/
    └── PRD.md            # 产品需求文档
```

## 模型

默认使用 `qwen3-max`（阿里云千问系列旗舰模型），上下文窗口 262K tokens。

## License

MIT
