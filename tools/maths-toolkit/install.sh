#!/bin/sh
# SPDX-FileCopyrightText: 2025-2026 SPHARX Ltd.
# SPDX-License-Identifier: AGPL-3.0-or-later OR Apache-2.0
# ============================================================================
# maths-toolkit 数学计算工具包安装器（market Tool 类包）
#
# 定位：agentrt 出厂自带的数学计算后端。安装 MCP-Mathematics + sympy-mcp
#       组合方案的能力（SymPy 符号计算 + MCP-Mathematics 数值/单位转换）。
#
# 设计决策：
#   - 共享 Python 虚拟环境：$AIRY_HOME/venv（与 agentrt 其他 Python 组件共用，
#     不重复创建多环境，避免空间浪费）。
#   - 默认不安装 einsteinpy（相对论计算需求可加 --with-einsteinpy）。
#   - maths_d 是调用本工具包的用户态服务；本包负责 Python 依赖与后端脚本部署。
#   - 依赖安装三级策略（2026-08-29 社区反馈 0.1.5a 数学库联网安装失败）：
#       1) 离线优先：包内 wheels/ 自带纯 Python wheel（sympy+mpmath），
#          --no-index 免网络，断网/弱网环境符号计算仍可用；
#       2) 在线回退：清华 PyPI 镜像（AIRY_PIP_INDEX 可覆盖）；
#       3) mcp-mathematics/einsteinpy 仅增强，在线失败不阻断
#          （maths_backend.py 内置单位换算兜底表降级）。
#
# 用法：
#   sh install.sh [--airy-home <path>] [--with-einsteinpy] [--uninstall]
#
# 产物：
#   $AIRY_HOME/venv/                   共享 Python 虚拟环境（sympy + mcp-mathematics）
#   $AIRY_HOME/backend/maths_backend.py 数学计算后端 worker（maths_d 经 stdio 调用）
#   $AIRY_HOME/config/maths-toolkit.yaml 工具包注册信息
# ============================================================================

# 失败即退：venv 创建/pip 依赖/后端部署任一失败必须向主安装器返回非零
# （2026-08-29 生产验证教训：此前仅 set -u，pip install 失败后脚本继续
# 执行并打印 [OK] 返回 0，主安装器误报"maths-toolkit 安装完成"，实际
# venv/依赖缺失导致 maths_d 无法启动）。
set -eu

AIRY_HOME="${AIRY_HOME:-$HOME/.airymaxrt}"
WITH_EINSTEINPY=0
UNINSTALL=0

while [ $# -gt 0 ]; do
    case "$1" in
        --airy-home) AIRY_HOME="$2"; shift 2 ;;
        --with-einsteinpy) WITH_EINSTEINPY=1; shift ;;
        --uninstall) UNINSTALL=1; shift ;;
        --help|-h)
            sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
            exit 0 ;;
        *) echo "[FAIL] 未知参数: $1（--help 查看用法）"; exit 1 ;;
    esac
done

VENV_DIR="${AIRY_HOME}/venv"
BACKEND_SRC="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/backend/maths_backend.py"
BACKEND_DST="${AIRY_HOME}/backend/maths_backend.py"
REG_FILE="${AIRY_HOME}/config/maths-toolkit.yaml"

if [ "$UNINSTALL" = "1" ]; then
    echo "[INFO] 卸载 maths-toolkit..."
    rm -f "$BACKEND_DST" "$REG_FILE"
    # 保留共享 venv（其他组件可能共用），仅提示
    echo "[ OK ] maths-toolkit 已卸载（共享 venv 保留：$VENV_DIR）"
    exit 0
fi

# ─── 环境检测 ────────────────────────────────────────────────────────────
if ! command -v python3 >/dev/null 2>&1; then
    echo "[WARN] 未找到 python3，跳过数学工具包安装（agentrt 仍可用纯 C 快速路径）"
    exit 0
fi

mkdir -p "$AIRY_HOME/backend" "$AIRY_HOME/config"

# ─── 共享虚拟环境（幂等） ────────────────────────────────────────────────
if [ ! -x "$VENV_DIR/bin/python3" ]; then
    echo "[INFO] 创建共享 Python 虚拟环境: $VENV_DIR"
    if ! python3 -m venv "$VENV_DIR"; then
        echo "[FAIL] venv 创建失败"
        exit 1
    fi
else
    echo "[INFO] 复用现有共享虚拟环境: $VENV_DIR"
fi

PYTHON_BIN="$VENV_DIR/bin/python3"
PIP_BIN="$VENV_DIR/bin/pip"

# ─── 安装 Python 依赖（离线 wheel 优先 → 在线镜像回退） ────────────────
# 2026-08-29 生产教训：社区 0.1.5a 安装时 pip 联网失败导致 sympy 缺失，
# maths_d 符号层不可用。三级策略见文件头设计决策。
PIP_INDEX="${AIRY_PIP_INDEX:-https://pypi.tuna.tsinghua.edu.cn/simple}"
WHEELS_DIR="${AIRY_WHEELS_DIR:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/wheels}"

# ── 1) sympy（符号计算核心）：离线 wheel 优先，免网络保底 ──
SYMPY_INSTALLED=0
if [ -d "$WHEELS_DIR" ] && ls "$WHEELS_DIR"/*.whl >/dev/null 2>&1; then
    echo "[INFO] 离线安装 sympy（包内 wheel，免网络）..."
    if "$PIP_BIN" install --quiet --no-index --find-links "$WHEELS_DIR" sympy mpmath; then
        SYMPY_INSTALLED=1
        echo "[ OK ] 离线安装成功（sympy + mpmath）"
    else
        echo "[WARN] 离线 wheel 安装失败，回退在线安装"
    fi
fi
if [ "$SYMPY_INSTALLED" = "0" ]; then
    echo "[INFO] 在线安装 sympy（镜像: $PIP_INDEX）..."
    if ! "$PIP_BIN" install --quiet --upgrade -i "$PIP_INDEX" sympy; then
        echo "[FAIL] sympy 安装失败（离线与在线均不可用），数学符号计算不可用"
        exit 1
    fi
fi

# ── 2) 自动检索更新 + 在线增强（mcp-mathematics / einsteinpy） ─────────
# 2026-08-29 社区诉求"安装后自动检索更新，更新失败功能不缺失"：
# 数值/单位/金融增强（mcp-mathematics）与 sympy 版本更新在此统一完成；
# 在线失败仅降级警告（maths_backend.py 内置单位兜底表），保留离线已装
# 版本，功能不缺失。
echo "[INFO] 自动检索在线更新（mcp-mathematics + 组件最新版，失败不影响已装版本）..."
if ! "$PIP_BIN" install --quiet --upgrade --timeout 10 --retries 1 -i "$PIP_INDEX" mcp-mathematics \
        ${SYMPY_INSTALLED:+sympy}; then
    echo "[WARN] 在线更新不可用（断网/镜像超时），保留已装版本，功能不受影响"
fi
if [ "$WITH_EINSTEINPY" = "1" ]; then
    echo "[INFO] 安装 einsteinpy（广义相对论计算）..."
    if ! "$PIP_BIN" install --quiet --upgrade --timeout 10 --retries 1 -i "$PIP_INDEX" einsteinpy; then
        echo "[WARN] einsteinpy 安装失败（可选功能，跳过）"
    fi
fi

# ─── 部署后端 worker ─────────────────────────────────────────────────────
if [ -f "$BACKEND_SRC" ]; then
    cp -f "$BACKEND_SRC" "$BACKEND_DST"
    chmod 644 "$BACKEND_DST"
    echo "[ OK ] 数学后端已部署: $BACKEND_DST"
else
    echo "[WARN] 未找到后端脚本: $BACKEND_SRC"
fi

# ─── 注册信息 ────────────────────────────────────────────────────────────
cat > "$REG_FILE" <<EOF
# maths-toolkit 注册信息（由 install.sh 生成）
name: maths-toolkit
category: tool
version: 0.1.4
backend: $BACKEND_DST
venv: $VENV_DIR
python: $PYTHON_BIN
sympy: $("$PYTHON_BIN" -c "import sympy; print(sympy.__version__)" 2>/dev/null || echo unknown)
mcp_mathematics: $("$PYTHON_BIN" -c "import importlib.util; print('yes' if importlib.util.find_spec('mcp_mathematics') else 'no')" 2>/dev/null || echo no)
installed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

echo "[ OK ] maths-toolkit 安装完成（agentrt 出厂数学计算后端）"
echo "       后端: $BACKEND_DST"
echo "       venv: $VENV_DIR"
