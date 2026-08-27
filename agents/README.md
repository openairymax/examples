# Agents — Agent 安装器与契约校验

> 属于 `ecosystem/markets`（官方包市场）仓库的 `agents` 子模块。

## 定位

`agents/` 是 Agent 分发包的安装器与契约校验实现。它定义 Agent 包（agent
package）的安装、移除、列举与契约校验逻辑，使 Agent 可以作为可拔插的
分发包安装到 AgentRT 运行时，无需修改核心。

与 `ecosystem/markets` 顶层的关系：

- 顶层仓库 `markets/` 是「分发层」：`tools/`（工具包）、`examples/`（示例
  Agent）、`templates/`（脚手架模板）；
- `agents/` 提供 Agent 分发包自身的安装/校验工具链；
- `client/` 提供市场客户端的契约审计与错误模型。

## 目录结构

```
agents/
├── __init__.py              # 包入口
├── contracts/               # Agent 分发包元数据契约（JSON Schema + 校验器）
│   ├── schema.json          # 分发包元数据 Schema（仅约束分发/安装层）
│   ├── validator.py         # 契约校验器（AgentContractValidator）
│   └── example_contract.json # 示例分发包契约
└── installer/               # 安装器
    ├── cli.py               # CLI 入口（install/list/remove）
    └── core.py              # 安装核心逻辑
```

> **契约 SSoT 分工**：本目录的 `schema.json` 仅约束 Agent **分发包元数据**
> （entry_point / config_schema / dependencies / resources 等分发层字段）。
> Agent 的**运行时能力契约**（agent_id / role / capabilities 含 input/output
> schema / models / required_permissions / cost_profile / trust_metrics）
> 以 `ecosystem/agents/shared/contracts/agent.schema.json` 为唯一权威，
> 安装校验时两者并用：先验分发包元数据，再验运行时契约。

## 契约校验

`contracts/schema.json` 定义 Agent 分发包必须满足的元数据字段（agent_id、
agent_type、version、capabilities、description、config_schema、
entry_point 等）；`validator.py` 的 `AgentContractValidator` 在安装前校验
契约合规性，拒绝缺失必填字段或非法权限范围的包。

## 安装器

`installer/core.py` 实现安装核心逻辑；`installer/cli.py` 提供命令行入口：

```bash
python -m markets.agents.installer.cli install <agent_package>
python -m markets.agents.installer.cli list
python -m markets.agents.installer.cli remove <agent_name>
```

安装目标目录遵循 `$AIRY_RUNTIME_DIR` / `$AIRY_HOME` 优先，回退
`~/.agentrt`。

## 使用方式

- 开发者发布新 Agent：编写 `contracts/schema.json` 兼容的契约 → 用
  `installer/cli.py` 安装验证；
- 运行时：`agent_d` 驱动已安装 Agent 的执行器（见 ecosystem 顶层 README）。
