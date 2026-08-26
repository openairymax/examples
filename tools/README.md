# Tools — 工具市场包目录

> 本目录存放 Airymax 生态的 **Tool 类目市场包**（遵循 `market Tool` 契约），
> 由 `market_d` 管理注册/安装/发布，安装后以 daemon 或 worker 形式提供服务。

## 包列表

| 包 | 版本 | 说明 | 安装器 |
|----|------|------|--------|
| [maths-toolkit](maths-toolkit/) | 0.1.4 | agentrt 出厂自带的数学计算后端：MCP-Mathematics（数值/单位/金融/数论）+ sympy-mcp（符号计算），共享 `$AIRY_HOME/venv`，默认不装 einsteinpy | `install.sh` |

## 包结构约定

```
tools/<package>/
├── package.yaml        # market Tool 类目元数据（name/category/version/components/capabilities）
├── install.sh          # 安装器（创建共享 venv、部署 worker、生成注册信息）
├── backend/            # Python/脚本 worker（stdio JSON-RPC 协议）
└── skills/             # 可选技能指南（指导模型何时使用本工具）
```

## 通用约定

- **共享虚拟环境**：所有 Python 组件共用 `$AIRY_HOME/venv`，不重复创建独立环境，
  避免空间浪费；
- **安装镜像**：默认使用清华 PyPI 镜像（`https://pypi.tuna.tsinghua.edu.cn/simple`），
  可用 `AIRY_PIP_INDEX` 覆盖；
- **降级策略**：Python 后端不可用时，宿主 daemon（如 maths_d）自动降级到纯 C
  快速路径，不阻塞 agentrt 核心；
- **出厂预装**：agentrt 主 `install.sh` 默认预装（`--without-maths` 跳过）。
