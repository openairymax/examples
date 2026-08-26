# code-review-agent — 代码审查

对指定代码文件/目录执行结构化审查（安全 / 性能 / 可维护性 / 正确性 / 风格），
并打印审查报告。审查逻辑复用官方技能
[`ecosystem/skills/src/code_review.py`](../../skills/src/code_review.py)。

## 运行

```bash
cd airymaxhub/ecosystem/examples/code-review-agent
python3 main.py                  # 默认审查本示例 main.py
python3 main.py path/to/target.py
python3 main.py path/to/dir      # 递归审查目录下所有源码文件
```

无需任何配置即可跑通：默认走**本地执行链路**（多维度静态分析 + 正则快速扫描），
不依赖 LLM 与网络。

## 执行链路（两级降级）

1. **agentrt SDK 链路（真实链路）**：优先尝试经 `SyscallProxy.skill_execute`
   调用 `code_review` 技能。当前 SDK 尚无 plugin 客户端（plugin_d 未开放），
   该调用需要 FFI 库 `libagentrt.so`（IPC 后端暂未实现 `skill_execute`），
   不可用时自动降级。
2. **本地执行链路（默认，离线可跑）**：直接加载
   `CodeReviewSkill` 执行完整生命周期
   （`validate_input → pre_execute → execute → post_execute`），
   覆盖安全（SQL 注入 / XSS / 硬编码密钥）、性能、可维护性、正确性与风格五维。

## 审查维度

| 维度 | 示例 |
|------|------|
| security | 硬编码密钥、`eval()` / `exec()`、`shell=True`、SQL 字符串拼接 |
| correctness | 裸 `except:`、越界边界 |
| maintainability | TODO / FIXME 残留 |
| style | 超长行、`import *` |

## 示例输出

```
[目标] .../examples/code-review-agent/main.py
[待审查] 共 1 个文件
[链路] agentrt SDK 不可用（...），降级为本地 CodeReviewSkill
============================================================
[审查文件] .../code-review-agent/main.py
[语言] python | [审查行数] 191 | [评分] 100/100
[摘要] Code review (python): score 100/100
[结果] 未发现问题，代码质量良好。
```

## 换一个带问题的文件看效果

```bash
# 临时生成一个含硬编码密钥 / eval 的样本并审查
python3 main.py /path/to/any/buggy.py
```

审查结果按严重级别（critical → high → medium → low → info）排序，
`post_execute` 阶段按 `severity_threshold`（默认 low）过滤展示。
