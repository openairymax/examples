# hello-agent — 5 分钟快速上手

最小可运行示例：创建 Airymax `AgentContext`，实例化 `airymax_agents` 的
`CodingAgent`，分配一个简单编码任务并打印执行结果。

## 运行

```bash
cd airymaxhub/ecosystem/examples/hello-agent
python3 main.py
```

无需任何配置即可跑通：未检测到 API key 时自动启用 `MockLLMClient`（离线模式），
设置 `OPENAI_API_KEY`（及可选 `OPENAI_BASE_URL`）即切换真实 LLM。

## 可选：接入 agentrt 系统调用

```bash
AIRY_USE_IPC=1 python3 main.py
```

注入 `SyscallProxy(backend='ipc')` 后，Agent 执行前后会把上下文/结果持久化到
`mem_d`，并把 `tool_d` 内置工具（`fs_read` / `fs_write` / `web_search` /
`web_fetch` / ...）注册为 function-calling 工具。需要先启动 agentrt 守护进程
（`mem_d` / `agent_d` / `tool_d`）。

## 示例输出（离线 Mock 模式）

```
====================================================================
Airymax hello-agent — 快速上手
available roles: ['product_manager', 'architect', 'backend', 'frontend', 'devops', 'security', 'tester', 'coding']
====================================================================

[agent] id=coding_v1 role=coding
[agent] syscall_proxy=off

[task] 用 Python 编写一个 hello_world 函数，并给出调用示例。

--- TaskResult ---
success: True
...
```

## 代码说明

- `AgentContext(agent_id=..., task_id=...)` — Airymax 执行上下文
- `get_agent("coding")` — 从 `airymax_agents.AGENT_REGISTRY` 实例化
  `CodingAgent`（等价于 `CodingAgent()`）
- `await agent.execute(task, ctx)` — 执行任务，返回 `TaskResult`

## 下一步

- 换用其他角色：`product_manager` / `architect` / `backend` / `frontend` /
  `devops` / `security` / `tester` / `coding`
- 参考 `ecosystem/agents/examples/run_pm.py` 查看带记忆持久化的完整用法
