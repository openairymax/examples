# Markets — Official Package Marketplace

> Official distribution marketplace for the Airymax AI Agent Runtime Platform.
> A leaf repository under the [Airymax ecosystem](https://atomgit.com/openairymax/ecosystem).

**Language:** English | [简体中文](README_zh.md)

[![Version](https://img.shields.io/badge/version-0.2.0-5a6b7e)](https://atomgit.com/openairymax/markets)
[![License](https://img.shields.io/badge/license-AGPL--3.0+Apache--2.0-4a90d9)](LICENSE)
[![Branch](https://img.shields.io/badge/branch-develop%2Fhubs--01-6f7b8e)](https://atomgit.com/openairymax/markets)

**Repository:** `git@atomgit.com:openairymax/markets.git` · **Branch:** `develop/hubs-01`

---

## Overview

`ecosystem/markets/` is the **official package marketplace** of the Airymax platform. It
distributes versioned, installable packages — tools, skills and example agents — that can be
plugged into the AgentRT runtime without touching the core. It embodies the platform's
"everything except the core is a service" philosophy: every package carries its own
`package.yaml` metadata and a self-contained installer, and can be enabled or removed at
runtime.

Within the ecosystem layer, `markets/` is the **distribution layer**: `ecosystem/agents`
holds built-in agent executors, `ecosystem/skills` holds skill definitions, and `markets/`
packages them (plus third-party-style add-ons) into installable artifacts. The runtime's
`market_d` daemon resolves packages from this repository.

## Directory Structure

```
markets/
├── tools/                        # Tool packages (installable computation backends)
│   └── maths-toolkit/            # Maths computation backend (SymPy + MCP-Mathematics)
│       ├── package.yaml          # Package metadata (SSoT for install & registry)
│       ├── install.sh            # Self-contained installer (shared venv)
│       ├── backend/              # Python stdio JSON-RPC worker
│       │   └── maths_backend.py
│       └── skills/maths.yaml     # Optional usage guidance for the runtime
├── examples/                     # Reference example agents (run with AgentRT CLI)
│   ├── hello-agent/
│   ├── code-review-agent/
│   └── research-agent/
├── .gitignore
└── README.md                     # This file
```

## Package Specification

Every distributable package lives in its own directory and MUST declare a
`package.yaml`:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique package name (namespace: `category/name`) |
| `category` | enum | `tool` / `skill` / `agent` |
| `version` | semver | Package version, must match the release tag |
| `default_installed` | bool | Whether the runtime enables it out of the box |
| `install.script` | string | Path to the installer entry point |
| `install.shared_venv` | bool | Reuse `$AIRY_HOME/venv` instead of a dedicated one |
| `components` | list | Runtime components (python_worker / pip_dependencies / ...) |
| `capabilities` | list | Capability identifiers exposed to the runtime |
| `downgrade` | string | Behavior when the package's environment is unavailable |

## Usage

### Install a package

```bash
# From a checkout of this repository
cd tools/maths-toolkit
./install.sh --airy-home "$HOME/.airy"

# The runtime's market_d resolves and enables registered packages at startup
```

### Run an example agent

```bash
cd examples/hello-agent
agentrt run --config config.yaml
```

## Relationship to the Ecosystem

| Repository | Role |
|------------|------|
| `ecosystem/markets` | **This repo** — distribution of installable packages |
| `ecosystem/agents` | Built-in agent executors (core agents are not market packages) |
| `ecosystem/skills` | Official skill definitions |
| `ecosystem/manager` | Configuration & lifecycle management |
| `ecosystem/prompts` | Prompt template library |

## Branch Strategy

This leaf repository follows `develop/hubs-01` as its active development branch. The
management repository that aggregates it stays on `main`.

## License

Dual-licensed under **AGPL v3 + Apache 2.0** (SPDX: `AGPL-3.0-or-later OR Apache-2.0`).
See [LICENSE](LICENSE) for the full text.

Copyright (c) 2025-2026 SPHARX Ltd. All Rights Reserved.
