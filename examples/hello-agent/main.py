"""hello-agent — 5 分钟快速上手示例

创建 orchestration AgentContext，实例化 airymax_agents 的 CodingAgent，
分配一个简单编码任务并打印执行结果。

运行方式::

    cd airymaxhub/ecosystem/examples/hello-agent
    python3 main.py

无需任何配置即可跑通（无 API key 时自动启用 MockLLMClient）。
设置 OPENAI_API_KEY（及可选 OPENAI_BASE_URL）即切换真实 LLM。

agentrt 接入（可选）：
- 默认不注入 SyscallProxy（纯 Python LLM 模式，向后兼容）
- 设置环境变量 AIRY_USE_IPC=1 时注入 SyscallProxy(backend='ipc')，
  Agent execute() 会在 LLM 推理前后将上下文/结果持久化到 mem_d，
  并把 tool_d 内置工具（fs_read/fs_write/web_search/web_fetch/...）
  注册为 function-calling 工具（需先启动 agentrt daemons）
"""

import asyncio
import os
import sys
from pathlib import Path

# 开发模式下把相关包根目录加入 sys.path（安装版可省略）：
#   ../../agents/   使 `import airymax_agents` / `import orchestration` 可用
#   ../../../sdk/sdk-python/  使 `import agentrt` 可用
HERE = Path(__file__).resolve().parent
ECOSYSTEM_ROOT = HERE.parent.parent
SDK_PYTHON_ROOT = ECOSYSTEM_ROOT.parent / "sdk" / "sdk-python"
for _root in (ECOSYSTEM_ROOT / "agents", SDK_PYTHON_ROOT):
    sys.path.insert(0, str(_root))

from airymax_agents import get_agent, list_agents  # noqa: E402
from orchestration.core.agent import AgentContext  # noqa: E402


def _maybe_build_syscall_proxy():
    """根据环境变量决定是否注入 agentrt SyscallProxy。

    - AIRY_USE_IPC=1：注入 IPC 后端（直连 mem_d / agent_d / tool_d）
    - 默认：返回 None（纯 Python LLM 模式，离线可跑）
    """
    if os.environ.get("AIRY_USE_IPC", "").lower() not in ("1", "true", "yes"):
        return None
    from agentrt.syscall import SyscallProxy  # noqa: WPS433 (动态导入避免硬依赖)

    proxy = SyscallProxy(backend="ipc")
    print(f"[syscall] backend={proxy._backend}")
    return proxy


async def main() -> None:
    print("=" * 60)
    print("Airymax hello-agent — 快速上手")
    print("available roles:", list_agents())
    print("=" * 60)

    # 1. 实例化 CodingAgent（可按需注入 syscall_proxy）
    syscall_proxy = _maybe_build_syscall_proxy()
    agent = get_agent("coding", syscall_proxy=syscall_proxy)
    await agent.initialize()
    print(f"\n[agent] id={agent.agent_id} role={agent.contract.get('role')}")
    print(f"[agent] syscall_proxy={'on' if syscall_proxy is not None else 'off'}")

    # 2. 创建 AgentContext 并分配任务
    task = "用 Python 编写一个 hello_world 函数，并给出调用示例。"
    ctx = AgentContext(agent_id=agent.agent_id, task_id="hello-001")
    print(f"\n[task] {task}")

    # 3. 执行并打印结果
    result = await agent.execute(task, ctx)

    print("\n--- TaskResult ---")
    print("success:", result.success)
    if result.error:
        print("error:", result.error)
    print("\n[output]")
    print(result.output)
    print("\n[metrics]")
    for key, value in (result.metrics or {}).items():
        print(f"  {key}: {value}")

    await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
