"""Claim Extractor — structured claim extraction from raw report texts (quick LLM).

FR-1: reads the 5 ``*_raw`` state fields and emits a JSON array of Claim tuples:
    {"broker", "author", "report_type", "subject", "direction",
     "strength", "horizon", "target", "quote"}
Follows the reader factory pattern from ``stock_reader.py``, but requires strict
JSON so downstream nodes can parse it deterministically.

v3.2: TWO quick-LLM passes —
  1. extract ordinary claims from the raw report texts;
  2. extract paired claims from the final_summary's "矛盾信号" section (as a
     separate, high-priority input so Summary Manager's findings are never
     drowned out by the ~120KB raw text).
Both are fault-tolerant: a failed pass yields nothing and never blocks.
"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

CLAIM_EXTRACTOR_SYSTEM = """你是研报观点抽取器。从研报原文中抽取结构化 Claim。
只输出一个 JSON 数组，不要任何解释或 markdown。每项格式：
{"broker": "券商名", "author": "分析师(无则null)", "report_type": "宏观/行业/个股/策略/晨报",
 "subject": "对象(股票名/行业/资产/宏观变量)", "direction": -1或0或1,
 "strength": 0到1的小数, "horizon": "短期/中期/长期",
 "target": 目标价数字(没有则null), "quote": "原文片段"}
规则：
- direction: 看多=1, 中性=0, 看空=-1
- horizon: 从原文推断时间尺度，必须填
- quote 必须是原文逐字片段
- 只抽取明确表达观点的句子，跳过无观点的背景描述
- **中性的明确表述也要抽（direction=0），它可能是矛盾的一方（如'谨慎/中性/观望'）**
- subject 尽量统一命名（如 光模块/CPO/光通信 归为 光模块）
"""

CONFLICT_SIGNAL_EXTRACTOR_SYSTEM = """你是研报矛盾信号解析器。给定综合投资建议中的
"矛盾信号"段落，把每条矛盾信号解析成一对对立的 Claim。
只输出一个 JSON 数组，不要任何解释或 markdown。每条矛盾信号对应 2 个元素（对立双方）：
{"broker": "立场方名称(原文提到的券商/机构名，无则'SummaryManager')",
 "author": null, "report_type": "综合",
 "subject": "矛盾主题(统一命名，如 黄金/债市/光模块/军工/估值/美联储)",
 "direction": -1或0或1, "strength": 0到1的小数,
 "horizon": "短期/中期/长期", "target": null,
 "quote": "该方观点的原文描述摘要"}
规则：
- 每条矛盾信号必须解析为 2 个 claim（双方立场），方向相反或一强一弱（如 乐观=1 vs 中性=0）
- subject 用统一主题名，同义词归一化（光模块/CPO/光通信→光模块）
- broker 用原文提到的机构名；若该方不是具体机构（如市场事件/宏观数据），标"SummaryManager"
- quote 用原文中的描述，保持原意"""

_RAW_FIELDS = ["macro_raw", "industry_raw", "stock_raw", "strategy_raw", "morning_raw"]


def extract_json(text: str):
    """Robustly parse a JSON array/object from an LLM reply (handles code fences)."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        for opener, closer in (("[", "]"), ("{", "}")):
            start = text.find(opener)
            if start == -1:
                continue
            depth = 0
            for i in range(start, len(text)):
                if text[i] == opener:
                    depth += 1
                elif text[i] == closer:
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start : i + 1])
                        except json.JSONDecodeError:
                            break
    raise ValueError(f"no JSON found in LLM output: {text[:200]!r}")


def _extract_or_empty(llm, system: str, human: str, label: str) -> list:
    """One fault-tolerant extraction pass; returns a list of claims (may be empty)."""
    try:
        result = llm.invoke(
            [SystemMessage(content=system), HumanMessage(content=human)]
        )
        parsed = extract_json(result.content)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return [parsed]
        return []
    except Exception as exc:  # 任何失败都不阻塞主链路
        logger.warning("Claim Extractor [%s]: failed (%s); using empty claims", label, exc)
        return []


def create_claim_extractor(llm):
    """Return a LangGraph node that extracts Claim tuples (raw pass + conflict-signal pass)."""

    def claim_extractor_node(state: dict) -> dict:
        raw = "\n\n".join(state.get(f, "") for f in _RAW_FIELDS)
        final_summary = state.get("final_summary", "")

        claims = _extract_or_empty(
            llm, CLAIM_EXTRACTOR_SYSTEM, f"研报原文：\n\n{raw}", "raw"
        )
        # 第二次：final_summary 的"矛盾信号"作为独立高优先级输入，保证 Summary Manager
        # 已发现的矛盾不被 ~120KB 原文淹没
        if final_summary:
            claims += _extract_or_empty(
                llm,
                CONFLICT_SIGNAL_EXTRACTOR_SYSTEM,
                f"矛盾信号段落：\n\n{final_summary}",
                "conflict-signal",
            )
        return {"claims": json.dumps(claims, ensure_ascii=False)}

    return claim_extractor_node
