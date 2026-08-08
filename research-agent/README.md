# research-agent — 资料搜集

演示 Agent 使用 `web_search` / `web_fetch` 工具做在线资料搜集；
工具不可达时自动降级为本地离线搜索（并明确打印提示）。

## 运行

```bash
cd airymaxhub/ecosystem/examples/research-agent
python3 main.py                          # 默认查询
python3 main.py "AgentRT 多智能体编排"    # 自定义查询
```

无需任何配置即可跑通：未启动 daemon 时自动降级为**离线模式**，
由本地 `WebSearchSkill` 输出离线搜索建议（含 DuckDuckGo / Google 搜索链接）。

## 执行链路（两级降级）

1. **在线链路**：`SyscallProxy(backend='ipc')` → `tool_d` 守护进程的
   `web_search`（DuckDuckGo HTML 搜索）与 `web_fetch`（页面正文抓取）工具。
   需要先启动 `tool_d`（sock 默认 `$AIRY_HOME/run/tool.sock`）。
2. **离线降级（默认，离线可跑）**：加载
   [`ecosystem/skills/src/web_search.py`](../../skills/src/web_search.py) 的
   `WebSearchSkill` 本地执行——内部先尝试 Gateway HTTP（`localhost:8080`），
   失败则生成搜索引擎链接，并打印「在线工具不可达」提示。

## 启动在线链路

```bash
# 先构建并启动 tool_d 守护进程（见 agentrt/daemons/tool_d）
python3 main.py "Rust 异步编程最佳实践"
```

输出示例（离线降级）：

```
====================================================================
Airymax research-agent — 资料搜集
[query] AgentRT 多智能体协作最佳实践
====================================================================
[提示] 在线工具不可达（...），降级为本地离线搜索
[提示] 如需在线链路，请先启动 tool_d 守护进程：
        agentrt/daemons/tool_d（sock 默认 $AIRY_HOME/run/tool.sock）

[链路] 离线（本地 WebSearchSkill），共 2 条结果

  1. Search: AgentRT 多智能体协作最佳实践 (relevance=1.000)
      https://duckduckgo.com/?q=AgentRT+%E5%A4%9A%E6%99%BA%E8%83%BD%E4%BD%93%E4%BD%9C%E6%9C%80%E4%BD%B3%E5%AE%9E%E8%B7%B5
  2. Search: AgentRT 多智能体协作最佳实践 (relevance=0.900)
      https://www.google.com/search?q=AgentRT+%E5%A4%9A%E6%99%BA%E8%83%BD%E4%BD%93%E4%BD%9C%E6%9C%80%E4%BD%B3%E5%AE%9E%E8%B7%B5

[摘要] Found 2 results for 'AgentRT 多智能体协作最佳实践'. Top results:
```

## 扩展建议

- 与 `airymax_agents` 组合：给 `get_agent("coding", syscall_proxy=proxy)`
  注入 `SyscallProxy`，Agent 即可在 LLM 回路中自动调用 `web_search` /
  `web_fetch`（工具 schema 见 `agents/airymax_agents/base.py` 的
  `BUILTIN_TOOL_SCHEMAS`）。
- 换用 `web_fetch` 对指定 URL 抓正文：`proxy.tool_execute("web_fetch", {"url": ...})`。
