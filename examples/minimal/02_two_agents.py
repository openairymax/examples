"""示例 2 — 两 Agent 协作

演示 Agent 间协作：ProductManager 写 PRD → Architect 基于 PRD 设计架构。

两种协作模式都展示：
  - 模式 A (顺序)：PM.execute → PRD，再 Architect.execute(PRD) → 架构
  - 模式 B (消息)：PM 用 Message 把结果发给 Architect，Architect 回信

运行方式::

    cd airymaxhub/ecosystem/agents
    python3 examples/minimal/02_two_agents.py

Mock 模式自动启用；设置 OPENAI_API_KEY 即切真实 LLM。
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestration.core.agent import AgentContext, Message
from orchestration.core.llm import make_llm_client
from orchestration.agents import LLMAgent


def make_pm_agent(llm) -> LLMAgent:
    contract = {
        "schema_version": "1.0.0",
        "agent_id": "pm-001",
        "agent_name": "Product Manager Agent",
        "version": "1.0.0",
        "role": "product_manager",
        "description": "理解用户需求，撰写产品需求文档 (PRD)。",
        "models": {"system1": "gpt-4o-mini", "system2": "gpt-4o"},
        "required_permissions": ["read_project_context"],
    }
    agent = LLMAgent(
        contract,
        llm=llm,
        system_prompt=(
            "你是产品经理。根据用户目标撰写清晰、结构化的 PRD。"
            "输出包含：用户目标、核心功能、非功能需求、验收标准。"
        ),
    )
    return agent


def make_architect_agent(llm) -> LLMAgent:
    contract = {
        "schema_version": "1.0.0",
        "agent_id": "arch-001",
        "agent_name": "Architect Agent",
        "version": "1.0.0",
        "role": "architect",
        "description": "根据 PRD 设计系统架构与模块划分。",
        "models": {"system1": "gpt-4o-mini", "system2": "gpt-4o"},
        "required_permissions": ["read_project_context"],
    }
    agent = LLMAgent(
        contract,
        llm=llm,
        system_prompt=(
            "你是系统架构师。基于给定的 PRD 输出架构设计。"
            "输出包含：技术选型、模块划分、关键决策、数据流。"
        ),
    )
    return agent


async def mode_a_sequential(pm: LLMAgent, architect: LLMAgent) -> None:
    """模式 A：顺序协作 — PM 产出 PRD，Architect 消费 PRD 产出架构。"""
    print("\n" + "=" * 60)
    print("模式 A：顺序协作 (PM.execute → Architect.execute)")
    print("=" * 60)

    # 1. PM 写 PRD
    user_goal = "我要做一个跨平台待办事项应用，支持团队协作和提醒"
    ctx = AgentContext(agent_id=pm.agent_id, task_id="prd-task")
    pm_result = await pm.execute(user_goal, ctx)

    print("\n[1] ProductManager 产出 PRD:")
    print("-" * 40)
    print(pm_result.output)

    # 2. Architect 基于 PRD 设计架构
    ctx2 = AgentContext(agent_id=architect.agent_id, task_id="arch-task")
    arch_result = await architect.execute(pm_result.output, ctx2)

    print("\n[2] Architect 产出架构设计:")
    print("-" * 40)
    print(arch_result.output)

    print("\n[metrics]")
    print("  PM       rounds:", pm_result.metrics.get("rounds") if pm_result.metrics else "?",
          "tokens:", pm_result.metrics.get("tokens") if pm_result.metrics else "?")
    print("  Architect rounds:", arch_result.metrics.get("rounds") if arch_result.metrics else "?",
          "tokens:", arch_result.metrics.get("tokens") if arch_result.metrics else "?")


async def mode_b_message(pm: LLMAgent, architect: LLMAgent) -> None:
    """模式 B：消息协作 — PM 发 Message 给 Architect，Architect 回信。"""
    print("\n" + "=" * 60)
    print("模式 B：消息协作 (PM → Message → Architect → 回信)")
    print("=" * 60)

    # PM 先产出 PRD 内容 (用 execute)
    ctx = AgentContext(agent_id=pm.agent_id, task_id="msg-prd-task")
    pm_result = await pm.execute("为 Markdown 笔记应用写一份简短 PRD", ctx)

    # PM 把结果作为任务消息发给 Architect
    delegation = Message(
        message_type="delegate",
        content=pm_result.output,
        sender=pm.agent_id,
        receiver=architect.agent_id,
    )
    print(f"\n[1] {pm.agent_id} → {architect.agent_id}: type={delegation.type}")
    print("    (附 PRD 内容，请求架构设计)")

    # Architect 处理消息并回信
    reply = await architect.handle_message(delegation)

    if reply and reply.content:
        print(f"\n[2] {reply.sender} → {reply.receiver}: type={reply.type}")
        print("-" * 40)
        # reply.content 是 TaskResult
        tr = reply.content
        if hasattr(tr, "output"):
            print(tr.output)
            print(f"\n  success={tr.success}")
        else:
            print(tr)
    else:
        print("\n[2] (Architect 未回信)")


async def main() -> None:
    llm = make_llm_client()

    pm = make_pm_agent(llm)
    architect = make_architect_agent(llm)
    await pm.initialize()
    await architect.initialize()

    print("LLM client:", type(llm).__name__)
    print("Agents:", [pm.agent_id, architect.agent_id])

    await mode_a_sequential(pm, architect)
    await mode_b_message(pm, architect)

    await pm.shutdown()
    await architect.shutdown()
    print("\n✓ 两种协作模式均完成。")


if __name__ == "__main__":
    asyncio.run(main())
