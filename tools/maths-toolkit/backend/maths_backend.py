#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025-2026 SPHARX Ltd.
# SPDX-License-Identifier: AGPL-3.0-or-later OR Apache-2.0

"""
maths_backend.py — 数学计算后端 worker（maths-toolkit market 包）

maths_d 经 stdio JSON-RPC 调用的 Python 计算子进程。按"数学计算建议稿"
六级分类覆盖能力，组合 MCP-Mathematics（数值/单位/金融/数论）与
sympy-mcp（符号计算）两套引擎：

  数值层（MCP-Mathematics）：
    - numerical  数值表达式求值（52 内置函数：算术/三角/对数/统计/复数）
    - units      单位换算（158 种，覆盖 15 类量纲）
    - finance    金融计算（百分比/税率/利息/贷款/折扣/加价）
    - number_theory  数论（素数判定 / 质因数分解）

  符号层（SymPy，对应 sympy-mcp 能力）：
    - solve        方程/方程组求解（线性、二次、超越方程）
    - differentiate 求导 / 偏导
    - integrate    定积分 / 不定积分
    - limit        极限
    - simplify     化简
    - factor       因式分解
    - expand       展开
    - matrix       矩阵运算（det / inv / transpose / multiply / eigen）

协议：stdio 每行一个 JSON（请求 -> 响应）。
  请求  {"id":1,"method":"solve","params":{...}}
  响应  {"id":1,"result":{...}}  或  {"id":1,"error":{"message":"..."}}

安全边界：仅符号/数值计算，不执行任意代码。数值求值走 MCP-Mathematics
的 AST 安全求值（白名单操作符/函数、深度与长度限制、超时与内存上限）；
符号计算输入由 SymPy 受限解析（sympify）。
"""

import json
import sys

# ─── 引擎 1：MCP-Mathematics（数值/单位/金融/数论） ─────────────────────
try:
    from mcp_mathematics.calculator import (
        convert_with_history,
        execute_mathematical_computation,
        is_prime,
        prime_factors,
        calculate_percentage,
        calculate_percentage_change,
        calculate_tax,
        calculate_compound_interest,
        calculate_simple_interest,
        calculate_loan_payment,
        calculate_discount,
        calculate_markup,
    )

    HAS_MCP = True
except ImportError:  # pragma: no cover - 降级路径
    HAS_MCP = False


# ─── 引擎 2：SymPy（符号计算） ──────────────────────────────────────────
try:
    import sympy as sp

    HAS_SYMPY = True
except ImportError:  # pragma: no cover - 降级路径
    HAS_SYMPY = False

# 单位换算兜底表（MCP-Mathematics 不可用时的常用量纲子集）
_UNIT_TABLES = {
    "length": {"m": 1.0, "km": 1e3, "cm": 1e-2, "mm": 1e-3,
               "ft": 0.3048, "in": 0.0254, "mi": 1609.344, "yd": 0.9144},
    "mass": {"kg": 1.0, "g": 1e-3, "mg": 1e-6, "lb": 0.45359237,
             "oz": 0.028349523125, "t": 1e3},
    "time": {"s": 1.0, "ms": 1e-3, "min": 60.0, "h": 3600.0, "day": 86400.0},
    "speed": {"mps": 1.0, "kmh": 1.0 / 3.6, "mph": 0.44704, "kn": 0.514444444444},
    "temperature": {"c": "celsius", "f": "fahrenheit", "k": "kelvin"},
    "area": {"m2": 1.0, "km2": 1e6, "ha": 1e4, "acre": 4046.8564224, "ft2": 0.09290304},
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


# ═══ 数值层：MCP-Mathematics ═══════════════════════════════════════════

def handle_numerical(params):
    """数值表达式求值（MCP-Mathematics AST 安全求值，52 内置函数）。

    params: {"expr":"125*38/7.2+15"} 或 {"expr":"sin(pi/6)+sqrt(144)"}
    """
    expr = params.get("expr")
    if not expr:
        raise ValueError("missing expr")
    if not HAS_MCP:
        raise RuntimeError("mcp-mathematics not installed (run maths-toolkit install)")
    result = execute_mathematical_computation(expr)
    return {"result": result, "engine": "mcp-mathematics"}


def handle_units(params):
    """单位换算。优先 MCP-Mathematics（158 种，15 类量纲）。

    params: {"value":1.0,"from":"km","to":"m"} 或 {"value":100,"from":"celsius","to":"fahrenheit"}
    """
    value = _to_float(params.get("value", 1.0))
    frm = params.get("from")
    to = params.get("to")
    if frm is None or to is None or value is None:
        raise ValueError("missing value/from/to")
    if HAS_MCP:
        result = convert_with_history(value, frm, to)
        return {"result": result, "engine": "mcp-mathematics"}
    # 降级：内置兜底表
    category = params.get("category") or _fallback_unit_category(frm, to)
    table = _UNIT_TABLES.get(category)
    if not table:
        raise ValueError("unknown unit pair: %s -> %s" % (frm, to))
    if category == "temperature":
        return {"result": _convert_temperature(value, frm, to),
                "category": category, "engine": "fallback"}
    if frm not in table or to not in table:
        raise ValueError("unknown unit in %s: %s/%s" % (category, frm, to))
    return {"result": value * table[frm] / table[to],
            "category": category, "engine": "fallback"}


def _fallback_unit_category(frm, to):
    for cat, table in _UNIT_TABLES.items():
        if frm in table and to in table:
            return cat
    return None


def _convert_temperature(value, frm, to):
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


def handle_finance(params):
    """金融计算（MCP-Mathematics）。

    ops: percentage / percentage_change / tax / compound_interest /
         simple_interest / loan_payment / discount / markup
    """
    op = params.get("op")
    if not HAS_MCP:
        raise RuntimeError("mcp-mathematics not installed (run maths-toolkit install)")
    if op == "percentage":
        return {"result": calculate_percentage(
            _require_float(params, "value"), _require_float(params, "percentage"))}
    if op == "percentage_change":
        return {"result": calculate_percentage_change(
            _require_float(params, "old_value"), _require_float(params, "new_value"))}
    if op == "tax":
        return {"result": calculate_tax(
            _require_float(params, "amount"), _require_float(params, "tax_rate"),
            bool(params.get("is_inclusive", False)))}
    if op == "compound_interest":
        return {"result": calculate_compound_interest(
            _require_float(params, "principal"), _require_float(params, "rate"),
            _require_float(params, "time"),
            int(params.get("compounds_per_year", 12)))}
    if op == "simple_interest":
        return {"result": calculate_simple_interest(
            _require_float(params, "principal"), _require_float(params, "rate"),
            _require_float(params, "time"))}
    if op == "loan_payment":
        return {"result": calculate_loan_payment(
            _require_float(params, "principal"), _require_float(params, "rate"),
            int(params.get("months", 12)))}
    if op == "discount":
        return {"result": calculate_discount(
            _require_float(params, "original_price"),
            _require_float(params, "discount_percent"))}
    if op == "markup":
        return {"result": calculate_markup(
            _require_float(params, "cost"),
            _require_float(params, "markup_percent"))}
    raise ValueError("unsupported finance op: %s" % op)


def _require_float(params, key):
    value = _to_float(params.get(key))
    if value is None:
        raise ValueError("missing numeric param: %s" % key)
    return value


def handle_number_theory(params):
    """数论（MCP-Mathematics）：素数判定 / 质因数分解。"""
    op = params.get("op")
    if not HAS_MCP:
        raise RuntimeError("mcp-mathematics not installed (run maths-toolkit install)")
    n = int(params.get("n"))
    if op == "is_prime":
        return {"result": is_prime(n)}
    if op == "prime_factors":
        return {"result": prime_factors(n)}
    raise ValueError("unsupported number_theory op: %s" % op)


# ═══ 符号层：SymPy（sympy-mcp 能力） ═══════════════════════════════════

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
        free = set()
        for eq in eqs:
            free |= eq.free_symbols
        syms = sorted(free, key=str) or [sp.symbols("x")]
    if len(syms) == 1:
        return {"solutions": _result(sp.solve(eqs[0], syms[0]))}
    return {"solutions": _result(sp.solve(eqs, syms))}


def handle_differentiate(params):
    """求导。params: {"expr":"x**3+2*x","symbol":"x","order":1}"""
    expr = params.get("expr")
    if not expr:
        raise ValueError("missing expr")
    symbol = params.get("symbol", "x")
    order = int(params.get("order", 1))
    e = sp.diff(sp.sympify(expr), sp.symbols(symbol), order)
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
        return {"result": _result(r), "latex": sp.latex(r), "definite": True}
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
    """矩阵运算。params: {"op":"det|inv|transpose|multiply|eigen","a":[[...]],"b":[[...]]}"""
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
        return {"eigenvalues": _result(a.eigenvals()),
                "eigenvectors": _result(a.eigenvects())}


_HANDLERS = {
    # 数值层（MCP-Mathematics）
    "numerical": handle_numerical,
    "units": handle_units,
    "finance": handle_finance,
    "number_theory": handle_number_theory,
    # 符号层（SymPy / sympy-mcp）
    "solve": handle_solve,
    "differentiate": handle_differentiate,
    "integrate": handle_integrate,
    "limit": handle_limit,
    "simplify": handle_simplify,
    "factor": handle_factor,
    "expand": handle_expand,
    "matrix": handle_matrix,
}


def _dispatch(req):
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params") or {}

    if method == "health_check":
        return {"id": req_id,
                "result": {"status": "ok",
                           "sympy": HAS_SYMPY,
                           "mcp_mathematics": HAS_MCP}}

    if method in _HANDLERS:
        handler = _HANDLERS[method]
        if method not in ("numerical", "units", "finance", "number_theory") \
                and not HAS_SYMPY:
            raise RuntimeError("sympy not installed (run maths-toolkit install)")
        return {"id": req_id, "result": handler(params)}

    return {"id": req_id,
            "error": {"message": "unknown method: %s" % method}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = _dispatch(req)
        except json.JSONDecodeError:
            resp = {"id": None, "error": {"message": "bad JSON"}}
        except Exception as exc:  # noqa: BLE001 — 计算失败返回 JSON-RPC 错误
            resp = {"id": req.get("id") if isinstance(req, dict) else None,
                    "error": {"message": str(exc)[:512]}}
        print(json.dumps(resp))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
