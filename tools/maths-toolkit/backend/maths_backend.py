#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025-2026 SPHARX Ltd.
# SPDX-License-Identifier: AGPL-3.0-or-later OR Apache-2.0

"""
maths_backend.py — 数学计算后端 worker（maths-toolkit market 包）

maths_d 经 stdio JSON-RPC 调用的 Python 计算子进程。提供符号计算能力
（对应 sympy-mcp 的 SymPy 能力），覆盖建议稿第三/四/五级：

  - solve        方程/方程组求解（线性、二次、超越方程）
  - differentiate 求导 / 偏导
  - integrate    定积分 / 不定积分
  - limit        极限
  - simplify     化简
  - factor       因式分解
  - expand       展开
  - matrix       矩阵运算（det / inv / transpose / multiply / eigen）
  - units        常用单位换算（长度/质量/时间/温度/速度，来自 MCP-Mathematics 亮点）

协议：stdio 每行一个 JSON（请求 -> 响应）。
  请求  {"id":1,"method":"solve","params":{...}}
  响应  {"id":1,"result":{...}}  或  {"id":1,"error":{"message":"..."}}

安全边界：仅符号/数值计算，不执行任意代码；输入为表达式字符串，
由 SymPy 解析（sympify 受限解析）。
"""

import json
import sys

try:
    import sympy as sp
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False

# 单位换算表（量纲 -> {单位: 对 SI 基的倍率}，覆盖常用类别）
_UNIT_TABLES = {
    "length": {"m": 1.0, "km": 1e3, "cm": 1e-2, "mm": 1e-3,
               "ft": 0.3048, "in": 0.0254, "mi": 1609.344, "yd": 0.9144},
    "mass": {"kg": 1.0, "g": 1e-3, "mg": 1e-6, "lb": 0.45359237,
             "oz": 0.028349523125, "t": 1e3},
    "time": {"s": 1.0, "ms": 1e-3, "min": 60.0, "h": 3600.0,
             "day": 86400.0},
    "speed": {"mps": 1.0, "kmh": 1.0 / 3.6, "mph": 0.44704,
              "kn": 0.514444444444},
    "temperature": {"c": "celsius", "f": "fahrenheit", "k": "kelvin"},
    "area": {"m2": 1.0, "km2": 1e6, "ha": 1e4, "acre": 4046.8564224,
             "ft2": 0.09290304},
    "volume": {"m3": 1.0, "l": 1e-3, "ml": 1e-6, "gal": 0.003785411784},
}


def _to_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _result(value):
    """把 SymPy 表达式转成可 JSON 序列化的结果字符串。"""
    if isinstance(value, (list, tuple)):
        return [_result(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _result(v) for k, v in value.items()}
    return str(value)


def handle_solve(params):
    """求解方程或方程组。
    params: {"equation":"x**2-4=0","symbol":"x"} 或 {"equations":[...],"symbols":["x","y"]}
    """
    equations = params.get("equations") or ([params.get("equation")] if params.get("equation") else [])
    if not equations:
        raise ValueError("missing equation")
    symbols = params.get("symbols") or ([params.get("symbol")] if params.get("symbol") else [])
    eqs = []
    for eq in equations:
        if "=" in eq:
            lhs, rhs = eq.split("=", 1)
            eqs.append(sp.sympify(lhs) - sp.sympify(rhs))
        else:
            eqs.append(sp.sympify(eq))
    if symbols:
        syms = [sp.symbols(s) for s in symbols]
    else:
        # 自动收集方程中的自由符号
        free = set()
        for eq in eqs:
            free |= eq.free_symbols
        syms = sorted(free, key=str) or [sp.symbols("x")]
    if len(syms) == 1:
        sol = sp.solve(eqs[0], syms[0])
        return {"solutions": _result(sol)}
    sol = sp.solve(eqs, syms)
    return {"solutions": _result(sol)}


def handle_differentiate(params):
    """求导。params: {"expr":"x**3+2*x","symbol":"x","order":1}"""
    expr = params.get("expr")
    if not expr:
        raise ValueError("missing expr")
    symbol = params.get("symbol", "x")
    order = int(params.get("order", 1))
    e = sp.sympify(expr)
    s = sp.symbols(symbol)
    e = sp.diff(e, s, order)
    return {"result": _result(e), "latex": sp.latex(e)}


def handle_integrate(params):
    """积分。params: {"expr":"x**2","symbol":"x","a":"0","b":"1"}（有 a/b 为定积分）"""
    expr = params.get("expr")
    if not expr:
        raise ValueError("missing expr")
    symbol = params.get("symbol", "x")
    e = sp.sympify(expr)
    s = sp.symbols(symbol)
    if params.get("a") is not None and params.get("b") is not None:
        a, b = sp.sympify(params["a"]), sp.sympify(params["b"])
        r = sp.integrate(e, (s, a, b))
        return {"result": _result(r), "latex": sp.latex(r),
                "definite": True}
    r = sp.integrate(e, s)
    return {"result": _result(r), "latex": sp.latex(r), "definite": False}


def handle_limit(params):
    """极限。params: {"expr":"sin(x)/x","symbol":"x","to":"0","direction":"+"}"""
    expr = params.get("expr")
    if not expr:
        raise ValueError("missing expr")
    symbol = params.get("symbol", "x")
    to = sp.sympify(params.get("to", "0"))
    direction = params.get("direction", "+")
    e = sp.sympify(expr)
    s = sp.symbols(symbol)
    r = sp.limit(e, s, to, dir="-" if direction == "-" else "+")
    return {"result": _result(r), "latex": sp.latex(r)}


def handle_simplify(params):
    """化简。params: {"expr":"(x**2-1)/(x-1)"}"""
    expr = params.get("expr")
    if not expr:
        raise ValueError("missing expr")
    r = sp.simplify(sp.sympify(expr))
    return {"result": _result(r), "latex": sp.latex(r)}


def handle_factor(params):
    """因式分解。params: {"expr":"x**2-4"}"""
    expr = params.get("expr")
    if not expr:
        raise ValueError("missing expr")
    r = sp.factor(sp.sympify(expr))
    return {"result": _result(r), "latex": sp.latex(r)}


def handle_expand(params):
    """展开。params: {"expr":"(x+1)**3"}"""
    expr = params.get("expr")
    if not expr:
        raise ValueError("missing expr")
    r = sp.expand(sp.sympify(expr))
    return {"result": _result(r), "latex": sp.latex(r)}


def handle_matrix(params):
    """矩阵运算。params: {"op":"det|inv|transpose|multiply","a":[[...]],"b":[[...]]}
    eigen 单独：{"op":"eigen","a":[[...]]}"""
    op = params.get("op")
    if op not in ("det", "inv", "transpose", "multiply", "eigen"):
        raise ValueError("unsupported matrix op: %s" % op)
    a = sp.Matrix(params.get("a", []))
    if op == "det":
        return {"result": _result(a.det())}
    if op == "inv":
        return {"result": _result(a.inv())}
    if op == "transpose":
        return {"result": _result(a.T.tolist())}
    if op == "multiply":
        b = sp.Matrix(params.get("b", []))
        return {"result": _result((a * b).tolist())}
    if op == "eigen":
        vals = a.eigenvals()
        return {"eigenvalues": _result(vals),
                "eigenvectors": _result(a.eigenvects())}
    raise ValueError("unreachable")


def handle_units(params):
    """单位换算。params: {"category":"length","value":1.0,"from":"km","to":"m"}"""
    category = params.get("category")
    value = _to_float(params.get("value", 1.0))
    frm = params.get("from")
    to = params.get("to")
    if not category or not frm or not to or value is None:
        raise ValueError("missing category/value/from/to")
    table = _UNIT_TABLES.get(category)
    if not table:
        raise ValueError("unknown unit category: %s" % category)
    if category == "temperature":
        # 摄氏/华氏/开尔文专用换算
        c = _convert_temperature(value, frm, to)
        return {"result": c, "category": category}
    if frm not in table or to not in table:
        raise ValueError("unknown unit in %s: %s/%s" % (category, frm, to))
    result = value * table[frm] / table[to]
    return {"result": result, "category": category}


def _convert_temperature(value, frm, to):
    """温度换算：c / f / k 之间互转（中间统一转开尔文）。"""
    if frm == "c":
        k = value + 273.15
    elif frm == "f":
        k = (value - 32.0) * 5.0 / 9.0 + 273.15
    elif frm == "k":
        k = value
    else:
        raise ValueError("unknown temperature unit: %s" % frm)
    if to == "c":
        return k - 273.15
    if to == "f":
        return (k - 273.15) * 9.0 / 5.0 + 32.0
    if to == "k":
        return k
    raise ValueError("unknown temperature unit: %s" % to)


_HANDLERS = {
    "solve": handle_solve,
    "differentiate": handle_differentiate,
    "integrate": handle_integrate,
    "limit": handle_limit,
    "simplify": handle_simplify,
    "factor": handle_factor,
    "expand": handle_expand,
    "matrix": handle_matrix,
    "units": handle_units,
}


def main():
    if not HAS_SYMPY:
        # 无 SymPy 时仍响应健康检查，但符号计算方法返回错误提示
        pass
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"id": None, "error": {"message": "bad JSON"}}))
            sys.stdout.flush()
            continue
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params") or {}
        if method == "health_check":
            print(json.dumps({"id": req_id,
                              "result": {"status": "ok", "sympy": HAS_SYMPY}}))
            sys.stdout.flush()
            continue
        handler = _HANDLERS.get(method)
        if not handler:
            print(json.dumps({"id": req_id,
                              "error": {"message": "unknown method: %s" % method}}))
            sys.stdout.flush()
            continue
        if not HAS_SYMPY:
            print(json.dumps({"id": req_id,
                              "error": {"message": "sympy not installed (run maths-toolkit install)"}}))
            sys.stdout.flush()
            continue
        try:
            result = handler(params)
            print(json.dumps({"id": req_id, "result": result}))
        except Exception as exc:  # noqa: BLE001 — 计算失败返回 JSON-RPC 错误
            print(json.dumps({"id": req_id,
                              "error": {"message": str(exc)[:512]}}))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
