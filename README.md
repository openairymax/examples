# Examples — Official Example Agent Collection

> 10 runnable example agents covering the full learning path from QuickStart to advanced multi-agent patterns.
> A leaf repository under the [Airymax ecosystem](https://atomgit.com/openairymax/ecosystem).

**Language:** English | [简体中文](README_zh.md)

[![Version](https://img.shields.io/badge/version-0.1.1-5a6b7e)](https://atomgit.com/openairymax/examples)
[![License](https://img.shields.io/badge/license-AGPL--3.0+Apache--2.0-4a90d9)](LICENSE)
[![Branch](https://img.shields.io/badge/branch-feature%2Fofficial--hubs--01-6f7b8e)](https://atomgit.com/openairymax/examples)

**Repository:** `git@atomgit.com:openairymax/examples.git` · **Branch:** `feature/official-hubs-01`

---

## Overview

`ecosystem/examples/` is the **official example Agent collection** of the Airymax AI Agent Runtime Platform. Every example is a self-contained, runnable project with its own `README.md`, `config.yaml` and `*.agent.yaml` definitions, demonstrating one concrete capability of the Airymax SDK and AgentRT runtime. Together the 10 examples form a graded learning path from a 5-minute QuickStart to advanced multi-agent orchestration and A2A communication.

The collection covers the full capability surface: minimal agent setup, custom tools, MCP protocol integration, the Plugin SDK (all four plugin types), the code-review skill, the prompt tuning framework, a custom MCP tool server, multi-agent collaboration with memory persistence, a full customer-support pipeline with hooks, four multi-agent collaboration modes (Sequential / Parallel / Debate / Hierarchical), and Agent-to-Agent protocol communication.

Within the ecosystem layer, `examples/` is the **topmost downstream consumer**: it imports the Airymax SDK and runtime at runtime (no vendored code), references prompt templates from `ecosystem/prompts`, skill definitions from `ecosystem/skills`, and assumes runtime configuration conforms to `ecosystem/manager/configs/agentrt.yaml`. It is consumed downstream by agent developers (as reference implementations and starting templates), workshops/onboarding (as graded lab material), and CI/docs generation.

## Directory Structure

```
examples/
├── hello-agent/                       # Beginner — 5-minute QuickStart
│   ├── README.md
│   ├── config.yaml
│   └── agents/main.agent.yaml
├── weather-agent/                     # Beginner — custom tool + MCP
│   ├── README.md
│   ├── config.yaml
│   ├── agents/weather.agent.yaml
│   └── tools/weather_tool.py
├── plugin-demo/                       # Beginner — Plugin SDK
│   ├── README.md
│   ├── config.yaml
│   └── plugins/
│       ├── my_agent_plugin.py
│       ├── my_tool_plugin.py
│       ├── my_hook_plugin.py
│       └── my_skill_plugin.py
├── code-review-agent/                 # Intermediate — code review skill
│   ├── README.md
│   ├── config.yaml
│   ├── agents/code_review.agent.yaml
│   └── skills/code_review_skill.py
├── prompt-tuner-demo/                 # Intermediate — prompt tuning
│   ├── README.md
│   ├── config.yaml
│   ├── eval/sample_dataset.jsonl
│   └── scripts/run_eval.py
├── mcp-tool-server/                   # Intermediate — MCP tool server
│   ├── README.md
│   ├── config.yaml
│   ├── server/tool_server.py
│   └── tools/
│       ├── calculator.py
│       └── file_reader.py
├── research-agent/                    # Intermediate — multi-agent + memory
│   ├── README.md
│   ├── config.yaml
│   └── agents/
│       ├── research.agent.yaml
│       └── research_coordinator.agent.yaml
├── customer-support-agent/            # Advanced — full pipeline + hooks
│   ├── README.md
│   ├── config.yaml
│   ├── agents/support.agent.yaml
│   └── hooks/support_hooks.py
├── multi-agent-debate/                # Advanced — 4 collaboration modes
│   ├── README.md
│   ├── config.yaml
│   └── agents/
│       ├── proponent.agent.yaml
│       ├── opponent.agent.yaml
│       ├── judge.agent.yaml
│       └── moderator.agent.yaml
├── a2a-chat/                          # Advanced — A2A protocol
│   ├── README.md
│   ├── config.yaml
│   └── agents/
│       ├── chat_agent_a.agent.yaml
│       └── chat_agent_b.agent.yaml
├── .github/workflows/ci.yml           # CI pipeline
├── .gitignore
└── README.md                          # This file
```

## Core Components — Example Catalog

| # | Example | Difficulty | Capability showcased |
|---|---------|:----------:|----------------------|
| 1 | [`hello-agent`](hello-agent/) | Beginner | 5-minute QuickStart: minimal runnable Agent |
| 2 | [`weather-agent`](weather-agent/) | Beginner | Custom tools + MCP protocol integration |
| 3 | [`plugin-demo`](plugin-demo/) | Beginner | Plugin SDK — all four plugin types (Agent / Tool / Hook / Skill) |
| 4 | [`code-review-agent`](code-review-agent/) | Intermediate | Code review Skill + security scanning |
| 5 | [`prompt-tuner-demo`](prompt-tuner-demo/) | Intermediate | Prompt tuning framework usage with evaluation datasets |
| 6 | [`mcp-tool-server`](mcp-tool-server/) | Intermediate | Custom MCP tool server (calculator + file_reader) |
| 7 | [`research-agent`](research-agent/) | Intermediate | Multi-agent collaboration + memory persistence |
| 8 | [`customer-support-agent`](customer-support-agent/) | Advanced | Full pipeline + Hook system |
| 9 | [`multi-agent-debate`](multi-agent-debate/) | Advanced | 4 multi-agent collaboration modes (Sequential / Parallel / Debate / Hierarchical) |
| 10 | [`a2a-chat`](a2a-chat/) | Advanced | A2A (Agent-to-Agent) protocol inter-agent communication |

### Learning Path

```
Beginner     hello-agent → weather-agent → plugin-demo
                ↓
Intermediate code-review-agent → prompt-tuner-demo → mcp-tool-server → research-agent
                ↓
Advanced     customer-support-agent → multi-agent-debate → a2a-chat
```

Each example directory has its own `README.md` explaining the demonstrated concept, the directory layout and extension suggestions. Start from [`hello-agent/README.md`](hello-agent/README.md) for the absolute minimum.

## Upstream Dependencies

`examples/` consumes the Airymax SDK and runtime as its build/run dependency. None of the examples vendor SDK code — they import it at runtime:

| Dependency | Purpose |
|------------|---------|
| `sdk-python` (`agentrt` / `agentos` package) | Primary SDK used by every example's Python code (tools, hooks, skills, plugins) |
| `sdk-go` / `sdk-rust` / `sdk-typescript` | Equivalent SDKs for the same surface area; examples are language-agnostic in concept |
| AgentRT runtime | Hosts the gateway, executes the CoreLoopThree (Cognition → Planning → Execution → Reflection) and serves the agents |
| `ecosystem/prompts` | Some examples reference prompt templates from the official prompt registry |
| `ecosystem/skills` | `code-review-agent` and similar examples consume official skill definitions |
| `ecosystem/manager` | Examples assume runtime configuration conforms to `manager/configs/agentrt.yaml` |

## Downstream Consumers

| Consumer | How it uses `examples/` |
|----------|--------------------------|
| **Agent developers (learners)** | Use the examples as reference implementations and starting templates |
| **Workshops / onboarding** | Used as graded lab material in the learning path above |
| **CI / docs generation** | Examples are referenced by documentation and may be smoke-tested in CI |

## Usage / Quick Start

Each example is self-contained and runnable with the AgentRT CLI.

### Prerequisites

```bash
# Install the Airymax SDK + AgentRT runtime
pip install agentrt
export OPENAI_API_KEY=sk-...
```

### Run an example

```bash
# hello-agent — 5-minute QuickStart
cd hello-agent
agentrt run --config config.yaml

# Talk to the agent via the gateway (default port 8080)
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, please introduce yourself"}'
```

### Multi-agent example

```bash
# multi-agent-debate — pick a collaboration mode
cd multi-agent-debate
agentrt run --config config.yaml --mode debate
agentrt run --config config.yaml --mode sequential
agentrt run --config config.yaml --topic "Will AI replace human creativity?"
```

### A2A communication

```bash
# Start two agent servers and let them talk over A2A
cd a2a-chat
agentrt serve --agent agents/chat_agent_a.agent.yaml --port 8001 &
agentrt serve --agent agents/chat_agent_b.agent.yaml --port 8002 &
agentrt run --config config.yaml
```

## Build

`examples/` ships configuration and Python source only — there is no compiled artifact. The examples are executed by the AgentRT runtime, which is installed separately:

```bash
# Install the runtime + SDK (provides the `agentrt` CLI)
pip install agentrt

# Run any example (no build step required)
cd hello-agent && agentrt run --config config.yaml
```

CI is defined in `.github/workflows/ci.yml` and smoke-tests the example configurations on every push.

## Branch Strategy

This leaf repository is on the **`feature/official-hubs-01`** branch (active development). The management repository that aggregates it stays on `main`.

## License

Dual-licensed under **AGPL v3 + Apache 2.0** (SPDX: `AGPL-3.0-or-later OR Apache-2.0`). See [LICENSE](LICENSE) for the full text.

Copyright (c) 2025-2026 SPHARX Ltd. All Rights Reserved.
