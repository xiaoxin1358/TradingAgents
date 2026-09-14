"""矛盾信号分析启动脚本 — 一键运行研报分析 + 矛盾检测。

薄封装：复用项目根 ``run_report_reader.py`` 的全部逻辑（v3.0 图：
5 Reader + Summary Manager 主链路 + 矛盾分析并行分支），这里只负责
把项目根加入 sys.path 并修复 Windows GBK 控制台编码。

用法:
    python launch.py
    python launch.py --date 2026-08-06
    python launch.py --date 2026-08-06 --db reports/contradictions.db
"""

from __future__ import annotations

import sys
from pathlib import Path

# 项目根（launchers/research_report/ 上两级），让 tradingagents 可导入
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Windows GBK 控制台无法打印 ✓/emoji，强制 UTF-8，避免中途崩溃
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from run_report_reader import main  # noqa: E402

if __name__ == "__main__":
    main()
