"""code-review-agent — 代码审查 Agent 示例

对指定代码文件/目录执行结构化审查（安全 / 性能 / 可维护性 / 正确性 / 风格），
并打印审查报告。

运行方式::

    cd airymaxhub/ecosystem/examples/code-review-agent
    python3 main.py                  # 默认审查本示例 main.py
    python3 main.py path/to/target.py
    python3 main.py path/to/dir      # 递归审查目录下所有源码文件

执行链路（两级降级）：
1. agentrt SDK 链路：当前 SDK 尚无 plugin 客户端（插件执行域已并入 tool_d），
   此处尝试经 ``SyscallProxy.skill_execute`` 调用 code_review 技能
   （FFI 后端需 libagentrt.so；IPC 后端暂未实现 skill_execute），
   不可用时自动降级到本地执行。
2. 本地执行链路（默认，离线可跑）：直接加载
   ``ecosystem/skills/src/code_review.py`` 的 :class:`CodeReviewSkill`
   做多维度静态分析，无需 LLM / 网络。
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

#: 代码审查技能实现文件（ecosystem/skills/src/code_review.py）
CODE_REVIEW_PY = ECOSYSTEM_ROOT / "skills" / "src" / "code_review.py"

#: 扩展名 → 技能支持的编程语言名
_LANG_BY_EXT = {
    ".py": "python",
    ".rs": "rust",
    ".js": "javascript",
    ".ts": "typescript",
    ".go": "go",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".java": "java",
}


def _load_code_review_skill():
    """按文件路径加载 CodeReviewSkill 类。

    使用 importlib 从 ``ecosystem/skills/src/code_review.py`` 加载，
    避免依赖 skills 包的整体导入（该模块内部会自行把 sdk-python
    加入 sys.path 再导入 agentrt.plugin_types）。
    """
    if not CODE_REVIEW_PY.is_file():
        raise FileNotFoundError(
            f"CodeReviewSkill 未找到: {CODE_REVIEW_PY}（需在 airymaxhub 仓库内运行）"
        )
    spec = importlib.util.spec_from_file_location("code_review_skill", CODE_REVIEW_PY)
    module = importlib.util.module_from_spec(spec)
    sys.modules["code_review_skill"] = module
    spec.loader.exec_module(module)
    return module.CodeReviewSkill


def _guess_language(path: Path) -> Optional[str]:
    """按扩展名推断语言。"""
    return _LANG_BY_EXT.get(path.suffix.lower())


def _collect_targets(path: Path) -> List[Path]:
    """收集待审查文件：单文件直接返回；目录则递归收集受支持的源码文件。"""
    if path.is_file():
        if _guess_language(path) is None:
            raise ValueError(f"不支持的文件类型: {path}（支持: {sorted(_LANG_BY_EXT)}）")
        return [path]
    if path.is_dir():
        files = [
            p for p in path.rglob("*")
            if p.is_file() and _guess_language(p) is not None
            and "__pycache__" not in p.parts and ".git" not in p.parts
        ]
        return sorted(files)
    raise FileNotFoundError(f"路径不存在: {path}")


def _try_sdk_chain(code: str, language: str) -> Optional[Dict[str, Any]]:
    """优先走真实链路：经 agentrt SDK 调用 code_review 技能。

    当前 SDK 无 plugin 客户端，此处尝试 :meth:`SyscallProxy.skill_execute`
    （FFI 后端需 libagentrt.so）。任何不可用（库缺失 / IPC 后端未实现 /
    daemon 未启动）都抛异常，由调用方降级到本地执行。
    """
    from agentrt.syscall import SyscallProxy  # noqa: WPS433 (动态导入避免硬依赖)

    proxy = SyscallProxy(backend="ipc")
    payload = json.dumps({"code": code, "language": language}, ensure_ascii=False)
    output = proxy.skill_execute("code_review", payload)
    if isinstance(output, str) and output.strip():
        return json.loads(output)
    if isinstance(output, dict):
        return output
    return None


async def _review_locally(skill_cls: type, code: str, language: str) -> Dict[str, Any]:
    """本地执行链路：运行 CodeReviewSkill 的完整生命周期。"""
    skill = skill_cls()
    context: Dict[str, Any] = {
        "code": code,
        "language": language,
        "focus": "all",
        "severity_threshold": "low",
    }
    if not skill.validate_input(context):
        raise ValueError(f"输入校验失败（language={language!r}）")
    context = await skill.pre_execute(context)
    result = await skill.execute(context)
    return await skill.post_execute(context, result)


def _print_report(path: Path, result: Dict[str, Any]) -> None:
    """格式化打印单文件审查报告。"""
    findings: List[Dict[str, Any]] = result.get("findings", [])
    print("=" * 60)
    print(f"[审查文件] {path}")
    print(f"[语言] {result.get('language')} | "
          f"[审查行数] {result.get('lines_reviewed')} | "
          f"[评分] {result.get('overall_score')}/100")
    print(f"[摘要] {result.get('summary')}")
    if not findings:
        print("[结果] 未发现问题，代码质量良好。")
        return
    print(f"[发现] 共 {len(findings)} 条：")
    for idx, finding in enumerate(findings, 1):
        print(f"  {idx}. [{finding.get('severity')}] "
              f"{finding.get('category')} — {finding.get('title')}")
        if finding.get("location"):
            print(f"       位置: {finding.get('location')}")
        if finding.get("description"):
            print(f"       说明: {finding.get('description')}")
        if finding.get("suggestion"):
            print(f"       建议: {finding.get('suggestion')}")


async def main() -> None:
    # 1. 解析目标路径（默认审查本示例自身，便于离线演示）
    raw_target = sys.argv[1] if len(sys.argv) > 1 else str(HERE / "main.py")
    target = Path(raw_target).resolve()
    print(f"[目标] {target}")

    targets = _collect_targets(target)
    if not targets:
        print(f"[提示] 目录 {target} 下未找到受支持的源码文件。")
        return
    print(f"[待审查] 共 {len(targets)} 个文件")

    # 2. 加载 CodeReviewSkill（本地执行链路，离线可跑）
    skill_cls = _load_code_review_skill()

    for file_path in targets:
        code = file_path.read_text(encoding="utf-8", errors="replace")
        language = _guess_language(file_path)

        # 3. 优先尝试 agentrt SDK 真实链路（不可用则降级）
        result: Optional[Dict[str, Any]] = None
        try:
            result = _try_sdk_chain(code, language)
            if result is not None:
                print(f"[链路] {file_path} 经 agentrt SDK 执行")
        except Exception as exc:  # noqa: WPS440 降级属预期行为
            print(f"[链路] agentrt SDK 不可用（{exc}），降级为本地 CodeReviewSkill")

        # 4. 本地执行（默认路径）
        if result is None:
            result = await _review_locally(skill_cls, code, language)

        # 5. 打印报告
        _print_report(file_path, result)


if __name__ == "__main__":
    asyncio.run(main())
