# Markets — 官方分发包市场

> Airymax AI Agent 运行时平台的官方分发市场。
> 隶属于 [Airymax ecosystem](https://atomgit.com/openairymax/ecosystem) 的叶子仓。

**语言:** [English](README.md) | 简体中文

[![Version](https://img.shields.io/badge/version-0.2.0-5a6b7e)](https://atomgit.com/openairymax/markets)
[![License](https://img.shields.io/badge/license-AGPL--3.0+Apache--2.0-4a90d9)](LICENSE)
[![Branch](https://img.shields.io/badge/branch-develop%2Fhubs--01-6f7b8e)](https://atomgit.com/openairymax/markets)

**仓库:** `git@atomgit.com:openairymax/markets.git` · **分支:** `develop/hubs-01`

---

## 概述

`ecosystem/markets/` 是 Airymax 平台的**官方分发包市场**。它分发带版本号、可安装的
包——工具、技能与示例 Agent——可插入 AgentRT 运行时而无需触碰核心。它体现平台
"除了核心，一切都是服务"的理念：每个包自带 `package.yaml` 元数据与自包含安装器，
可在运行时启用或卸载。

在生态层中，`markets/` 是**分发层**：`ecosystem/agents` 承载内置 Agent 执行器，
`ecosystem/skills` 承载技能定义，`markets/` 将两者（及第三方式扩展）打包为可安装
制品。运行时的 `market_d` 守护进程从本仓库解析分发包。

## 目录结构

```
markets/
├── tools/                        # 工具包（可安装的计算后端）
│   └── maths-toolkit/            # 数学计算后端（SymPy + MCP-Mathematics）
│       ├── package.yaml          # 包元数据（安装与注册的唯一权威源）
│       ├── install.sh            # 自包含安装器（共享虚拟环境）
│       ├── backend/              # Python stdio JSON-RPC worker
│       │   └── maths_backend.py
│       └── skills/maths.yaml     # 可选的运行时使用指南
├── examples/                     # 参考示例 Agent（用 AgentRT CLI 运行）
│   ├── hello-agent/
│   ├── code-review-agent/
│   └── research-agent/
├── .gitignore
└── README.md                     # 本文件
```

## 包规范

每个可分发包位于独立目录，且必须声明 `package.yaml`：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 唯一包名（命名空间：`category/name`） |
| `category` | enum | `tool` / `skill` / `agent` |
| `version` | semver | 包版本，须与发布标签一致 |
| `default_installed` | bool | 运行时是否出厂默认启用 |
| `install.script` | string | 安装器入口路径 |
| `install.shared_venv` | bool | 复用 `$AIRY_HOME/venv` 而非独立环境 |
| `components` | list | 运行时组件（python_worker / pip_dependencies / ...） |
| `capabilities` | list | 对运行时暴露的能力标识 |
| `downgrade` | string | 包环境不可用时的降级行为 |

## 使用

### 安装包

```bash
# 在本仓库检出中
cd tools/maths-toolkit
./install.sh --airy-home "$HOME/.airy"

# 运行时的 market_d 在启动时解析并启用已注册的包
```

### 运行示例 Agent

```bash
cd examples/hello-agent
agentrt run --config config.yaml
```

## 与生态的关系

| 仓库 | 角色 |
|------|------|
| `ecosystem/markets` | **本仓库** — 可分发包的分发 |
| `ecosystem/agents` | 内置 Agent 执行器（核心 Agent 不作为市场包） |
| `ecosystem/skills` | 官方技能定义 |
| `ecosystem/manager` | 配置与生命周期管理 |
| `ecosystem/prompts` | 提示词模板库 |

## 分支策略

本叶子仓以 `develop/hubs-01` 为活跃开发分支。聚合它的管理仓保持在 `main`。

## 许可证

采用 **AGPL v3 + Apache 2.0** 双许可证（SPDX: `AGPL-3.0-or-later OR Apache-2.0`）。
完整文本见 [LICENSE](LICENSE)。

Copyright (c) 2025-2026 SPHARX Ltd. 保留所有权利。
