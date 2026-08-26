# Examples — 示例 Agent 集合

> 属于 `ecosystem/markets`（官方包市场）仓库的 `examples` 子模块。

## 定位

`examples/` 提供可直接运行/参考的示例 Agent 与示例应用，展示如何在
AgentRT 上开发、打包和运行 Agent。是开发者上手的最佳起点。

## 目录结构

```
examples/
├── hello-agent/            # 最小可运行 Agent（入门示例）
├── code-review-agent/      # 代码审查 Agent（消费 skills/CodeReviewSkill）
├── research-agent/         # 研究型 Agent（多步检索/分析）
└── apps/                   # 完整应用示例
    ├── ecommerce/          # 电商场景应用（含 manifest.json/config.yaml）
    ├── docgen/             # 文档生成应用（Jinja2 模板渲染）
    └── videoedit/          # 视频编辑应用
```

## 各示例说明

| 示例 | 说明 |
|------|------|
| `hello-agent` | 最小骨架：main.py + requirements.txt，演示 Agent 基本循环 |
| `code-review-agent` | 消费官方 `CodeReviewSkill` 的代码审查 Agent |
| `research-agent` | 演示检索 → 分析 → 输出的多步研究流程 |
| `apps/ecommerce` | 完整应用：manifest.json + config.yaml + run.sh + src/ |
| `apps/docgen` | 模板驱动文档生成：Jinja2 + src/generator.py |
| `apps/videoedit` | 视频编辑处理应用 |

## 使用方式

```bash
# 以 hello-agent 为例
cd examples/hello-agent
pip install -r requirements.txt
python main.py
```

完整应用（apps/*）均携带 `manifest.json`（市场契约）与 `config.yaml`
（运行配置），可作为自包含分发包提交到市场。
