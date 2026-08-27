# Client — 市场客户端

> 属于 `ecosystem/markets`（官方包市场）仓库的 `client` 子模块。

## 定位

`client/` 是市场（marketplace）的客户端库：向 AgentRT 运行时与开发者提供
与市场分发包交互所需的模型、错误类型与契约审计能力。

## 目录结构

```
client/
├── __init__.py          # 包入口
├── market_client.py     # 市场客户端（MarketClient）
├── contract_audit.py    # 契约审计（ContractAuditor）
├── models.py            # 数据模型（分发包/契约模型）
├── errors.py            # 错误类型（MarketError 等）
└── contract_audit.py    # 一致性审计（--report / --fix）
```

## 能力

- **MarketClient**（`market_client.py`）：面向市场服务的客户端封装，
  负责包解析、查询与分发交互；
- **ContractAuditor**（`contract_audit.py`）：契约一致性审计器，扫描
  仓库内分发包契约与权威 Schema 的偏差：

  ```bash
  python -m markets.client.contract_audit [--report]
  python -m markets.client.contract_audit --fix
  ```

  `--report` 输出偏差报告，`--fix` 自动修复可机械纠正的字段；
- **models.py**：`MarketPackage` 等数据模型，是包元数据（package.yaml）
  与运行时 `market_d` 之间的结构化载体；
- **errors.py**：`MarketError` 及子类，统一市场层错误语义（A-UEF 风格，
  错误可追溯、可分类）。

## 使用方式

运行时 `market_d` daemon 通过本客户端解析与启用已注册分发包；测试侧
`tests/test_contract_consistency.py` 基于 `models` / `contract_audit` 验证
仓库内全部契约与 Schema 的一致性。
