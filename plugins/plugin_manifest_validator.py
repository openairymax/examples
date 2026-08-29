#!/usr/bin/env python3
# Copyright (c) 2026 SPHARX. All Rights Reserved.
# "From data intelligence emerges."

"""
Plugin Manifest Validator (0.1.6 P1-5 插件机制子集：组件声明即校验)
==================================================================

消费 manager/schema/plugin-manifest.schema.json 对插件 manifest.yaml
做离线校验（纯本地，无需网络/AgentRT 运行时），随 market 包分发。

与 plugin_d/plugin_discovery.c 的必填字段校验（name/library/type/
api_version/min_airy_version）对齐（S-4：schema 是权威，运行时约束一致）。

用法：
  python3 plugin_manifest_validator.py <manifest.yaml...>   # 逐个文件
  python3 plugin_manifest_validator.py --dir <插件目录>     # 目录批量
  python3 plugin_manifest_validator.py --strict             # 警告也计失败

返回码：0=全部通过；1=存在错误（或 strict 下有警告）。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

try:
    import jsonschema
    from jsonschema import Draft202012Validator, Draft7Validator
except ImportError:
    jsonschema = None

# 默认 schema：ecosystem/manager/schema/plugin-manifest.schema.json
DEFAULT_SCHEMA = (
    Path(__file__).resolve().parent.parent.parent
    / "manager"
    / "schema"
    / "plugin-manifest.schema.json"
)


def _load_schema(path: Path):
    import json

    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _validate_manifest(mf_path: Path, schema: dict, strict: bool,
                       check_lib: bool = False) -> list[str]:
    """校验单个 manifest.yaml，返回错误列表（strict 时警告并入）。"""
    errors: list[str] = []
    rel = str(mf_path)

    if yaml is None:
        errors.append(f"{rel}: 缺 PyYAML（pip install pyyaml）")
        return errors
    with mf_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        errors.append(f"{rel}: manifest 顶层必须是对象")
        return errors

    # 1) JSON Schema 校验（S-4 权威约束：必填 8 字段 + type 枚举 + 版本格式）
    if jsonschema is not None:
        try:
            cls = Draft202012Validator if "$schema" in schema or True else Draft7Validator
            cls(schema).validate(data)
        except jsonschema.exceptions.ValidationError as exc:
            path = "/".join(str(p) for p in exc.path) or "<root>"
            errors.append(f"{rel}: schema 校验失败 @ {path}: {exc.message}")
    else:
        errors.append(f"{rel}: 缺 jsonschema 库，跳过 schema 校验")

    # 2) 语义校验：name 与 library 前缀一致性（S-4 命名约束）
    name = data.get("name")
    lib = data.get("library")
    if name and lib:
        expected = f"libairy_skill_{name}.so"
        if lib != expected:
            errors.append(f"{rel}: library 命名不一致（期望 {expected}，实际 {lib}）")

    # 3) library 文件存在性（仅 --check-lib 启用：.so 是编译产物，源码树
    #    CI 不要求存在；发布/分发形态校验时启用，确保包内库文件齐备）。
    if check_lib and lib and not mf_path.parent.joinpath(lib).exists():
        errors.append(f"{rel}: library 文件缺失: {mf_path.parent / lib}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifests", nargs="*", help="manifest.yaml 文件路径")
    parser.add_argument("--dir", help="插件目录（批量校验其下 manifest.yaml）")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA), help="schema 路径")
    parser.add_argument("--strict", action="store_true", help="警告计为失败")
    parser.add_argument("--check-lib", action="store_true",
                        help="校验 library 文件存在性（发布/分发形态）")
    args = parser.parse_args()

    schema_path = Path(args.schema)
    if not schema_path.is_file():
        print(f"[FAIL] schema 不存在: {schema_path}", file=sys.stderr)
        return 1
    schema = _load_schema(schema_path)

    targets: list[Path] = []
    for m in args.manifests:
        targets.append(Path(m))
    if args.dir:
        d = Path(args.dir)
        if not d.is_dir():
            print(f"[FAIL] 目录不存在: {d}", file=sys.stderr)
            return 1
        targets.extend(sorted(d.rglob("manifest.y*ml")))
    if not targets:
        parser.print_usage()
        return 1

    all_errors: list[str] = []
    for t in targets:
        if not t.is_file():
            all_errors.append(f"{t}: 文件不存在")
            continue
        all_errors.extend(_validate_manifest(t, schema, args.strict, args.check_lib))

    if all_errors:
        for e in all_errors:
            print(f"  [FAIL] {e}", file=sys.stderr)
        print(f"[FAIL] 插件 manifest 校验未通过（{len(all_errors)} 项）", file=sys.stderr)
        return 1
    print(f"[ OK ] 插件 manifest 校验通过（{len(targets)} 个）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
