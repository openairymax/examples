# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""markets 叶仓测试引导。

导入根约定（与 skills 叶仓一致的包纪律）：
- 仓库根与 tests/ 均为正式包（__init__.py 齐备），
  pytest prepend 模式沿包链自动将仓库父级插入 sys.path，
  独立叶仓场景以 ``markets.*`` 解析；
- 伞仓组装场景同样以 ``markets.*`` 前缀解析（父级为 ecosystem/）。

本文件不夹带任何 sys.path 补丁，路径解析统一交由包链机制。
"""

import sys

# 禁止写入 .pyc 字节码缓存，根治源码区 __pycache__ 污染
sys.dont_write_bytecode = True
