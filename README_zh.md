# Examples — 官方示例 Agent 集合

> 10 个可运行的示例 Agent，覆盖从 QuickStart 到高级多 Agent 模式的完整学习路径。
> 隶属于 [Airymax ecosystem](https://atomgit.com/openairymax/ecosystem) 的叶子仓。

**语言:** [English](README.md) | 简体中文

[![Version](https://img.shields.io/badge/version-0.1.1-5a6b7e)](https://atomgit.com/openairymax/examples)
[![License](https://img.shields.io/badge/license-AGPL--3.0+Apache--2.0-4a90d9)](LICENSE)
[![Branch](https://img.shields.io/badge/branch-feature%2Fofficial--hubs--01-6f7b8e)](https://atomgit.com/openairymax/examples)

**仓库:** `git@atomgit.com:openairymax/examples.git` · **分支:** `feature/official-hubs-01`

---

## 概述

`ecosystem/examples/` 是 Airymax AI Agent 运行时平台的**官方示例 Agent 集合**。每个示例都是自包含、可运行的项目，含独立的 `README.md`、`config.yaml` 与 `*.agent.yaml` 定义，演示 Airymax SDK 与 AgentRT 运行时的一项具体能力。10 个示例共同构成一条分级学习路径，从 5 分钟 QuickStart 一路进阶到高级多 Agent 编排与 A2A 通信。

集合覆盖完整能力面：最小 Agent 搭建、自定义工具、MCP 协议集成、Plugin SDK（四型插件）、代码审查技能、提示词调优框架、自定义 MCP 工具服务器、带记忆持久化的多 Agent 协作、带 Hook 的完整客服流水线、4 种多 Agent 协作模式（Sequential / Parallel / Debate / Hierarchical），以及 Agent-to-Agent 协议通信。

在生态层中，`examples/` 是**最顶层的下游消费方**：运行时导入 Airymax SDK 与运行时（不内嵌代码），引用 `ecosystem/prompts` 的提示词模板、`ecosystem/skills` 的技能定义，并假设运行时配置遵循 `ecosystem/manager/configs/agentrt.yaml`。下游被 Agent 开发者（作为参考实现与起步模板）、培训/入门引导（作为分级实验材料）、CI/文档生成消费。

## 目录结构

```
examples/
├── hello-agent/                       # 入门 — 5 分钟 QuickStart
│   ├── README.md
│   ├── config.yaml
│   └── agents/main.agent.yaml
├── weather-agent/                     # 入门 — 自定义工具 + MCP
│   ├── README.md
│   ├── config.yaml
│   ├── agents/weather.agent.yaml
│   └── tools/weather_tool.py
├── plugin-demo/                       # 入门 — Plugin SDK
│   ├── README.md
│   ├── config.yaml
│   └── plugins/
│       ├── my_agent_plugin.py
│       ├── my_tool_plugin.py
│       ├── my_hook_plugin.py
│       └── my_skill_plugin.py
├── code-review-agent/                 # 中级 — 代码审查技能
│   ├── README.md
│   ├── config.yaml
│   ├── agents/code_review.agent.yaml
│   └── skills/code_review_skill.py
├── prompt-tuner-demo/                 # 中级 — 提示词调优
│   ├── README.md
│   ├── config.yaml
│   ├── eval/sample_dataset.jsonl
│   └── scripts/run_eval.py
├── mcp-tool-server/                   # 中级 — MCP 工具服务器
│   ├── README.md
│   ├── config.yaml
│   ├── server/tool_server.py
│   └── tools/
│       ├── calculator.py
│       └── file_reader.py
├── research-agent/                    # 中级 — 多 Agent + 记忆
│   ├── README.md
│   ├── config.yaml
│   └── agents/
│       ├── research.agent.yaml
│       └── research_coordinator.agent.yaml
├── customer-support-agent/            # 高级 — 完整流水线 + Hook
│   ├── README.md
│   ├── config.yaml
│   ├── agents/support.agent.yaml
│   └── hooks/support_hooks.py
├── multi-agent-debate/                # 高级 — 4 种协作模式
│   ├── README.md
│   ├── config.yaml
│   └── agents/
│       ├── proponent.agent.yaml
│       ├── opponent.agent.yaml
│       ├── judge.agent.yaml
│       └── moderator.agent.yaml
├── a2a-chat/                          # 高级 — A2A 协议
│   ├── README.md
│   ├── config.yaml
│   └── agents/
│       ├── chat_agent_a.agent.yaml
│       └── chat_agent_b.agent.yaml
├── .github/workflows/ci.yml           # CI 流水线
├── .gitignore
└── README.md                          # 本文件
```

## 核心组件 — 示例目录

| # | 示例 | 难度 | 展示能力 |
|---|------|:----:|----------|
| 1 | [`hello-agent`](hello-agent/) | 入门 | 5 分钟 QuickStart：最少代码运行 Agent |
| 2 | [`weather-agent`](weather-agent/) | 入门 | 自定义工具 + MCP 协议集成 |
| 3 | [`plugin-demo`](plugin-demo/) | 入门 | Plugin SDK 四型插件（Agent / Tool / Hook / Skill） |
| 4 | [`code-review-agent`](code-review-agent/) | 中级 | 代码审查 Skill + 安全扫描 |
| 5 | [`prompt-tuner-demo`](prompt-tuner-demo/) | 中级 | 提示词调优框架使用 + 评估数据集 |
| 6 | [`mcp-tool-server`](mcp-tool-server/) | 中级 | 自定义 MCP 工具服务器（calculator + file_reader） |
| 7 | [`research-agent`](research-agent/) | 中级 | 多 Agent 协作 + 记忆持久化 |
| 8 | [`customer-support-agent`](customer-support-agent/) | 高级 | 完整 Pipeline + Hook 系统 |
| 9 | [`multi-agent-debate`](multi-agent-debate/) | 高级 | 4 种多 Agent 协作模式（Sequential / Parallel / Debate / Hierarchical） |
| 10 | [`a2a-chat`](a2a-chat/) | 高级 | A2A（Agent-to-Agent）协议 Agent 间通信 |

### 学习路径

```
入门     hello-agent → weather-agent → plugin-demo
            ↓
中级     code-review-agent → prompt-tuner-demo → mcp-tool-server → research-agent
            ↓
高级     customer-support-agent → multi-agent-debate → a2a-chat
```

每个示例目录都有独立的 `README.md`，说明所演示的概念、目录结构与扩展建议。从 [`hello-agent/README.md`](hello-agent/README.md) 开始可了解最小可运行配置。

## 上游依赖

`examples/` 以 Airymax SDK 与运行时作为构建 / 运行依赖。所有示例均不在本地内嵌 SDK 代码，而是在运行时导入：

| 依赖 | 用途 |
|------|------|
| `sdk-python`（`agentrt` / `agentos` 包） | 每个示例 Python 代码（工具、Hook、技能、插件）所使用的主 SDK |
| `sdk-go` / `sdk-rust` / `sdk-typescript` | 等价 SDK，覆盖同一能力面；示例在概念上与语言无关 |
| AgentRT 运行时 | 托管网关，执行 CoreLoopThree（认知 → 规划 → 执行 → 反思）并提供 Agent 服务 |
| `ecosystem/prompts` | 部分示例引用官方提示词注册表中的模板 |
| `ecosystem/skills` | `code-review-agent` 等示例消费官方技能定义 |
| `ecosystem/manager` | 示例假设运行时配置遵循 `manager/configs/agentrt.yaml` |

## 下游消费方

| 消费方 | 使用方式 |
|--------|----------|
| **Agent 开发者（学习者）** | 将示例作为参考实现与起步模板 |
| **培训 / 入门引导** | 作为上述学习路径中的分级实验材料 |
| **CI / 文档生成** | 文档引用示例，并可能在 CI 中进行冒烟测试 |

## 使用说明 / 快速开始

每个示例自包含，可用 AgentRT CLI 直接运行。

### 前置条件

```bash
# 安装 Airymax SDK + AgentRT 运行时
pip install agentrt
export OPENAI_API_KEY=sk-...
```

### 运行示例

```bash
# hello-agent — 5 分钟 QuickStart
cd hello-agent
agentrt run --config config.yaml

# 通过网关与 Agent 对话（默认端口 8080）
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好，请介绍一下你自己"}'
```

### 多 Agent 示例

```bash
# multi-agent-debate — 选择协作模式
cd multi-agent-debate
agentrt run --config config.yaml --mode debate
agentrt run --config config.yaml --mode sequential
agentrt run --config config.yaml --topic "AI 是否会取代人类创造力"
```

### A2A 通信

```bash
# 启动两个 Agent 服务端，让它们通过 A2A 对话
cd a2a-chat
agentrt serve --agent agents/chat_agent_a.agent.yaml --port 8001 &
agentrt serve --agent agents/chat_agent_b.agent.yaml --port 8002 &
agentrt run --config config.yaml
```

## 构建

`examples/` 仅提供配置与 Python 源码——无编译产物。示例由 AgentRT 运行时执行，运行时需单独安装：

```bash
# 安装运行时 + SDK（提供 `agentrt` CLI）
pip install agentrt

# 运行任意示例（无需构建步骤）
cd hello-agent && agentrt run --config config.yaml
```

CI 定义在 `.github/workflows/ci.yml`，每次推送时对示例配置进行冒烟测试。

## 分支策略

本叶子仓位于 **`feature/official-hubs-01`** 分支（活跃开发）。聚合它的管理仓保持在 `main`。

## 许可证

采用 **AGPL v3 + Apache 2.0** 双许可证（SPDX: `AGPL-3.0-or-later OR Apache-2.0`）。详见 [LICENSE](LICENSE)。

Copyright (c) 2025-2026 SPHARX Ltd. All Rights Reserved.
