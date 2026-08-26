# Templates — 脚手架模板

> 属于 `ecosystem/markets`（官方包市场）仓库的 `templates` 子模块。

## 定位

`templates/` 提供新项目脚手架模板：开发者以模板为起点，快速生成
Agent 应用或 Skill 的目录骨架，保证结构与市场契约一致。

## 目录结构

```
templates/
├── python-agent/   # Python Agent 脚手架
└── rust-skill/     # Rust Skill 脚手架
```

## 各模板说明

| 模板 | 目标 | 内容 |
|------|------|------|
| `python-agent` | Python 语言 Agent | 标准 Agent 目录骨架（入口/配置/依赖） |
| `rust-skill` | Rust 语言 Skill | Skill 插件骨架（含契约/构建结构） |

## 使用方式

复制对应模板目录为新项目，按模板内 README 与占位符完成填充：

```bash
cp -r templates/python-agent my-agent
# 修改配置、实现逻辑后作为分发包提交
```

模板结构与 `contracts/schema.json` 对齐，确保生成的项目可直接通过
契约校验与安装器。
