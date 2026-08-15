"""Read-only settings + decision-memory access (docs 5.6 / 5.7).

Reads .env TRADINGAGENTS_* keys as plain text (no package import) and the
trading memory markdown file. The web UI shows values but never writes them.
"""

from __future__ import annotations

import os
from pathlib import Path

# Which TRADINGAGENTS_* keys are surfaced in the Settings page, grouped.
SETTING_GROUPS = [
    ("LLM 连接", [
        "TRADINGAGENTS_LLM_PROVIDER",
        "TRADINGAGENTS_DEEP_THINK_LLM",
        "TRADINGAGENTS_QUICK_THINK_LLM",
        "TRADINGAGENTS_BACKEND_URL",
    ]),
    ("运行选项", [
        "TRADINGAGENTS_CHECKPOINT_ENABLED",
        "TRADINGAGENTS_OUTPUT_LANG",
        "TRADINGAGENTS_RESEARCH_DEPTH",
    ]),
    ("数据与存储", [
        "TRADINGAGENTS_CACHE_DIR",
        "TRADINGAGENTS_MEMORY_LOG_PATH",
    ]),
]


def _load_dotenv(root: Path) -> dict[str, str]:
    env = {}
    dotenv = root / ".env"
    if dotenv.is_file():
        for line in dotenv.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip("'\"")
    return env


def get_settings(root: Path) -> dict:
    dotenv = _load_dotenv(root)
    groups = []
    for label, keys in SETTING_GROUPS:
        items = [
            {"key": k, "value": os.environ.get(k) or dotenv.get(k, "")}
            for k in keys
        ]
        groups.append({"label": label, "items": items})
    return {"groups": groups}


def memory_path(root: Path) -> Path:
    env_path = os.environ.get("TRADINGAGENTS_MEMORY_LOG_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return Path.home() / ".tradingagents" / "memory" / "trading_memory.md"


def get_memory(root: Path) -> dict:
    p = memory_path(root)
    if not p.is_file():
        return {"exists": False, "path": str(p), "content": "", "mtime": None}
    stat = p.stat()
    return {
        "exists": True,
        "path": str(p),
        "content": p.read_text(encoding="utf-8", errors="replace"),
        "mtime": stat.st_mtime,
    }
