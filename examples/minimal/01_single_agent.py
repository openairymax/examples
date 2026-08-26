"""示例 1 — 单 Agent 端到端

演示最小可运行链路：创建 Agent → 注册工具 → 分配任务 → 调 LLM → 产出结果。

运行方式::

    cd airymaxhub/ecosystem/openlab
    python3 examples/minimal/01_single_agent.py

无需任何配置即可跑通 (Mock 模式自动启用)。
设置 OPENAI_API_KEY (及可选 OPENAI_BASE_URL) 即切真实 LLM。
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 确保 openlab 包可导入 (开发模式)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestration.core.agent import AgentContext
from orchestration.core.llm import make_llm_client
from orchestration.agents import LLMAgent


# ── 1. 定义一个工具 ──────────────────────────────────────

def get_current_time(params: dict) -> dict:
    """工具：返回当前时间。

    参数 schema 暴露给 LLM (OpenAI function-calling 格式)。
    """
    tz = params.get("timezone", "local")
    return {
        "timezone": tz,
        "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


async def main() -> None:
    # ── 2. 构造 Agent 契约 (遵循 01-agent-contract.md) ──────
    contract = {
        "schema_version": "1.0.0",
        "agent_id": "pm-001",
        "agent_name": "Product Manager Agent",
        "version": "1.0.0",
        "role": "product_manager",
        "description": "理解用户需求，撰写产品需求文档 (PRD)。",
        "models": {
            "system1": "gpt-4o-mini",   # t1-f 快思考
            "system2": "gpt-4o",        # t2 主思考
        },
        "required_permissions": ["read_project_context"],
    }

    # ── 3. 创建 Agent ───────────────────────────────────────
    llm = make_llm_client()
    agent = LLMAgent(contract, llm=llm)
    agent.register_tool(
        name="get_current_time",
        tool=get_current_time,
        schema={
            "description": "获取当前系统时间",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "时区，如 'Asia/Shanghai'",
                    },
                },
                "required": [],
            },
        },
    )
    await agent.initialize()

    # ── 4. 分配任务 ─────────────────────────────────────────
    task = "现在几点了？请用 get_current_time 工具确认，然后为待办事项应用写一份简短 PRD。"
    context = AgentContext(agent_id=agent.agent_id, task_id="task-001")

    print("=" * 60)
    print("Task:", task)
    print("=" * 60)

    result = await agent.execute(task, context)

    # ── 5. 打印结果 ─────────────────────────────────────────
    print("\n--- TaskResult ---")
    print("success:", result.success)
    if result.error:
        print("error:", result.error)
    print("\n[output]")
    print(result.output)
    print("\n[metrics]")
    for k, v in (result.metrics or {}).items():
        print(f"  {k}: {v}")

    await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
