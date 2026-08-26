"""research-agent — 资料搜集 Agent 示例

演示 Agent 使用 ``web_search`` / ``web_fetch`` 工具做在线资料搜集；
工具不可达时自动降级为本地离线搜索（明确打印提示）。

运行方式::

    cd airymaxhub/ecosystem/examples/research-agent
    python3 main.py                           # 默认查询
    python3 main.py "AgentRT 多智能体编排"    # 自定义查询

执行链路（两级降级）：
1. 在线链路：agentrt :class:`SyscallProxy`(backend='ipc') → tool_d 守护进程
   的 ``web_search`` / ``web_fetch`` 工具（需先启动 tool_d，见
   ``agentrt/daemons/tool_d``；sock 默认 ``$AIRY_HOME/run/tool.sock``）
2. 离线降级：加载 ``ecosystem/skills/src/web_search.py`` 的
   :class:`WebSearchSkill` 本地执行（内部先尝试 Gateway HTTP，失败则生成
   搜索引擎链接），并打印「在线工具不可达」提示。
"""

import asyncio
import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# agentrt SDK 在 import 时会注册 INFO 日志，这里压回 WARNING 保持输出整洁
logging.getLogger("agentrt.syscall").setLevel(logging.WARNING)

# 开发模式下把相关包根目录加入 sys.path（安装版可省略）：
#   ../../skills/   使 skills 包可导入
#   ../../../sdk/sdk-python/  使 `import agentrt` 可用
HERE = Path(__file__).resolve().parent
ECOSYSTEM_ROOT = HERE.parent.parent
SDK_PYTHON_ROOT = ECOSYSTEM_ROOT.parent / "sdk" / "sdk-python"
for _root in (ECOSYSTEM_ROOT / "skills", SDK_PYTHON_ROOT):
    sys.path.insert(0, str(_root))

#: 网络搜索技能实现文件（ecosystem/skills/src/web_search.py）
WEB_SEARCH_PY = ECOSYSTEM_ROOT / "skills" / "src" / "web_search.py"


def _load_web_search_skill():
    """按文件路径加载 WebSearchSkill 类（避免触发 skills 包整体导入）。"""
    if not WEB_SEARCH_PY.is_file():
        raise FileNotFoundError(
            f"WebSearchSkill 未找到: {WEB_SEARCH_PY}（需在 airymaxhub 仓库内运行）"
        )
    spec = importlib.util.spec_from_file_location("web_search_skill", WEB_SEARCH_PY)
    module = importlib.util.module_from_spec(spec)
    sys.modules["web_search_skill"] = module
    spec.loader.exec_module(module)
    return module.WebSearchSkill


def _try_online_search(query: str, max_results: int) -> Optional[List[Dict[str, Any]]]:
    """在线链路：经 agentrt SyscallProxy → tool_d 的 web_search 工具。

    返回解析后的结果列表；工具不可达（daemon 未启动 / 调用失败）时返回 None。
    """
    from agentrt.syscall import SyscallProxy  # noqa: WPS433 (动态导入避免硬依赖)

    proxy = SyscallProxy(backend="ipc")
    raw = proxy.tool_execute("web_search", {"query": query, "max_results": max_results})
    if not isinstance(raw, dict) or not raw.get("success"):
        raise RuntimeError(f"tool_d web_search 失败: {raw.get('error', raw)}")
    output = raw.get("output", "")
    if isinstance(output, str) and output.strip():
        parsed = json.loads(output)
    else:
        parsed = output
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict) and isinstance(parsed.get("results"), list):
        return parsed["results"]
    return [{"title": "raw output", "url": "", "snippet": str(output)}]


async def _fetch_page(proxy, url: str) -> str:
    """在线链路补充演示：经 tool_d 的 web_fetch 抓取页面正文（best-effort）。"""
    raw = proxy.tool_execute("web_fetch", {"url": url})
    if not isinstance(raw, dict) or not raw.get("success"):
        raise RuntimeError(f"tool_d web_fetch 失败: {raw.get('error', raw)}")
    text = raw.get("output", "")
    return text[:300] + "..." if len(text) > 300 else text


async def _search_offline(query: str, max_results: int) -> Dict[str, Any]:
    """离线降级：本地执行 WebSearchSkill（内部先试 Gateway，失败生成搜索链接）。"""
    skill_cls = _load_web_search_skill()
    skill = skill_cls()
    context: Dict[str, Any] = {
        "query": query,
        "max_results": max_results,
        "engine": "auto",
        "time_range": "all",
        "region": "us",
    }
    if not skill.validate_input(context):
        raise ValueError("搜索查询校验失败（query 为空或过长）")
    context = await skill.pre_execute(context)
    return await skill.execute(context)


def _print_results(results: List[Dict[str, Any]]) -> None:
    """格式化打印搜索结果。"""
    if not results:
        print("[结果] 未获取到任何结果。")
        return
    for idx, item in enumerate(results, 1):
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        snippet = item.get("snippet", "") or item.get("description", "")
        relevance = item.get("relevance")
        extra = f" (relevance={relevance:.3f})" if isinstance(relevance, (int, float)) else ""
        print(f"  {idx}. {title}{extra}")
        if url:
            print(f"      {url}")
        if snippet:
            print(f"      {snippet[:120]}")


async def main() -> None:
    # 1. 解析查询（默认演示用查询）
    query = " ".join(sys.argv[1:]) or "AgentRT 多智能体协作最佳实践"
    max_results = 5
    print("=" * 60)
    print("Airymax research-agent — 资料搜集")
    print(f"[query] {query}")
    print("=" * 60)

    # 2. 在线链路：SyscallProxy → tool_d web_search
    proxy = None
    try:
        from agentrt.syscall import SyscallProxy  # noqa: WPS433

        proxy = SyscallProxy(backend="ipc")
        results = _try_online_search(query, max_results)
        print(f"[链路] 在线（tool_d web_search），共 {len(results)} 条结果\n")
        _print_results(results)

        # 3. 补充演示 web_fetch：抓取第一条结果的页面正文（best-effort）
        if results and results[0].get("url"):
            print("\n[链路] 在线（tool_d web_fetch）抓取首条页面正文：")
            try:
                text = await _fetch_page(proxy, results[0]["url"])
                print(f"  {text}")
            except Exception as exc:
                print(f"  web_fetch 不可用（非致命）: {exc}")
    except Exception as exc:  # noqa: WPS440 降级属预期行为
        print(f"[提示] 在线工具不可达（{exc}），降级为本地离线搜索")
        print("[提示] 如需在线链路，请先启动 tool_d 守护进程：")
        print("        agentrt/daemons/tool_d（sock 默认 $AIRY_HOME/run/tool.sock）\n")

        # 4. 离线降级：本地 WebSearchSkill
        try:
            result = await _search_offline(query, max_results)
            results = result.get("results", [])
            print(f"[链路] 离线（本地 WebSearchSkill），共 {len(results)} 条结果\n")
            _print_results(results)
            if result.get("summary"):
                print(f"\n[摘要] {result['summary']}")
        except Exception as exc:
            print(f"[错误] 离线搜索也失败: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
