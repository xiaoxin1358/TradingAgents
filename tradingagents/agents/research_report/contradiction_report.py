"""Contradiction Report — markdown report rendered from the store + deep-LLM insights.

FR-5: renders the daily contradiction_report.md (新增 / 持续 / 解决 / 统计)
directly from SQLite in code. No LLM in rendering: the data is already
structured, so rendering is deterministic, free, and cannot fail the run.

FR-7: ``create_contradiction_insight`` is a deep-LLM node that explains WHY each
open contradiction exists (成因 / 双方逻辑点评 / 验证信号 / 倾向) and persists the
insight back into the ``contradictions.insight`` column. Fault-tolerant: a failed
LLM call yields no insights and never blocks the main report.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import date

from langchain_core.messages import HumanMessage, SystemMessage

from .claim_extractor import extract_json
from .contradiction_store import ContradictionStore

logger = logging.getLogger(__name__)

_DIRECTION = {-1: "看空", 0: "中性", 1: "看多"}
_KIND_CN = {"factual": "事实", "opinion": "观点"}
_SCOPE_CN = {"direct": "直接", "indirect": "间接"}
_SCALE_CN = {"same": "同尺度", "cross": "跨尺度"}

CONTRADICTION_INSIGHT_SYSTEM = """你是资深的券商研报矛盾分析专家。给定若干条已检出的
研报矛盾（同一对象上两家机构观点相反），逐条分析其成因并给出研究见解。
只输出一个 JSON 数组，不要任何解释或 markdown。每项格式：
{"id": "矛盾id(原样返回)", "cause_type": "口径差异|时间尺度|框架假设|信息时效|立场差异|其他",
 "cause": "成因分析(1-3句,说明矛盾从何而来)",
 "analysis": "双方逻辑点评(各1句,指出各自关键假设与弱点)",
 "watch": "验证信号(具体看什么数据/指标能裁决,1-2句)",
 "tilt": "倾向(哪方更可能对,或'不确定',1句,必须谨慎表述)"}
规则：
- id 必须与输入一致，用于回写数据库
- cause_type 优先归因到最可能的单一类别；factual 矛盾多因"口径差异/信息时效"，cross 矛盾多因"时间尺度"
- tilt 是基于逻辑与数据可检验性的审慎判断，不预测市场点位
- 不要编造输入中不存在的证据；信息不足时 watch/tilt 如实说明"""


def _type_cn(row: dict) -> str:
    kind = _KIND_CN.get(row.get("kind", "?"), row.get("kind", "?"))
    scope = _SCOPE_CN.get(row.get("scope", "?"), row.get("scope", "?"))
    scale = _SCALE_CN.get(row.get("scale", "?"), row.get("scale", "?"))
    return f"{kind}/{scope}/{scale}"


def _days_open(row: dict, day: str) -> int | None:
    """Days since first_seen; None if dates are unparseable."""
    try:
        return (date.fromisoformat(day) - date.fromisoformat(row["first_seen"])).days
    except ValueError:
        return None


def _claim_line(claim: dict) -> str:
    broker = claim.get("broker", "?")
    subject = claim.get("subject", "?")
    direction = _DIRECTION.get(claim.get("direction"), "?")
    quote = claim.get("quote") or ""
    return f"{broker}[{direction} {subject}] {quote}"


def _insight_block(row: dict) -> str:
    """v3.3: one-line summary (cause_type + tilt) with the rest inside <details>.

    The full cause/analysis/watch text stays in the markdown (so searches and
    assertions still see it), but only one line is shown by default.
    """
    raw = row.get("insight")
    if not raw:
        return ""
    try:
        d = json.loads(raw)
    except (TypeError, ValueError):
        return ""
    cause_type = d.get("cause_type", "其他")
    tilt = d.get("tilt") or "不确定"
    lines = [f"    📝 **洞察**：{cause_type} · 倾向：{tilt}"]
    detail = []
    if d.get("cause"):
        detail.append(f"成因：{d['cause']}")
    if d.get("analysis"):
        detail.append(f"点评：{d['analysis']}")
    if d.get("watch"):
        detail.append(f"验证：{d['watch']}")
    if detail:
        lines.append(
            f"      <details><summary>详情</summary>{'<br>'.join(detail)}</details>"
        )
    return "\n".join(lines)


def _rows_markdown(rows: list[dict], day: str) -> str:
    """v3.3: group rows by subject; each row keeps broker pair + timeline."""
    if not rows:
        return "- （无）"
    by_subject: dict[str, list[dict]] = {}
    for r in rows:
        by_subject.setdefault(r["subject"], []).append(r)
    lines = []
    for subject, group in by_subject.items():
        lines.append(
            f"### {subject}（{len(group)} 条）" if len(group) > 1 else f"### {subject}"
        )
        for r in group:
            a, b = r["claim_a"], r["claim_b"]
            days = _days_open(r, day)
            timeline = f"首次 {r['first_seen']} · 最近 {r['last_seen']}"
            if days:
                timeline += f" · 持续 {days} 天"
            lines.append(f"- **{_type_cn(r)}** · {timeline}")
            lines.append(f"  - {_claim_line(a)}")
            lines.append(f"  - {_claim_line(b)}")
            block = _insight_block(r)
            if block:
                lines.append(block)
    return "\n".join(lines)


def _overview_markdown(rows: list[dict], day: str) -> str:
    """v3.3: one-screen overview table of today's active contradictions."""
    if not rows:
        return "- （无）"
    lines = [
        "| 对象 | 类型 | 甲方 | 乙方 | 持续天数 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        a, b = r["claim_a"], r["claim_b"]
        dir_a = _DIRECTION.get(a.get("direction"), "?")
        dir_b = _DIRECTION.get(b.get("direction"), "?")
        days = _days_open(r, day)
        days_s = "今日新增" if days == 0 else (f"{days} 天" if days is not None else "?")
        lines.append(
            f"| {r['subject']} | {_type_cn(r)} | "
            f"{a.get('broker', '?')}[{dir_a}] | {b.get('broker', '?')}[{dir_b}] | {days_s} |"
        )
    return "\n".join(lines)


def _stats_markdown(stats: dict, active: list[dict], day: str) -> str:
    """v3.3: totals + kind/cause_type distributions + longest open span."""
    total = stats["total"]
    rate = stats["resolved"] / total * 100 if total else 0.0
    lines = [
        f"- 累计矛盾：{stats['total']} 条 | 未决：{stats['open']} | "
        f"已解决：{stats['resolved']} | 解决率：{rate:.0f}%"
    ]
    if not active:
        return "\n".join(lines)
    kinds = Counter(r.get("kind", "?") for r in active)
    lines.append(
        "- 活跃矛盾类型："
        + " | ".join(f"{_KIND_CN.get(k, k)} {v}" for k, v in kinds.most_common())
    )
    causes: Counter[str] = Counter()
    for r in active:
        try:
            causes[json.loads(r["insight"]).get("cause_type", "其他")] += 1
        except (TypeError, ValueError):
            causes["未生成"] += 1
    lines.append(
        "- 洞察归因分布："
        + " | ".join(f"{k} {v}" for k, v in causes.most_common())
    )
    longest = max(_days_open(r, day) or 0 for r in active)
    lines.append(f"- 最长未决：{longest} 天")
    return "\n".join(lines)


def render_contradiction_report(store: ContradictionStore, day: str) -> str:
    """v3.3 (docs 7.3): overview + 新增/持续/解决 three mutually exclusive
    sections (empty sections are not rendered), subject-grouped rows,
    collapsed insights, and richer stats."""
    new_rows = [r for r in store.new_since(day) if r["status"] == "open"]
    open_rows = [r for r in store.list_open() if r["first_seen"] != day]
    resolved_rows = store.resolved_since(day)
    active = new_rows + open_rows
    stats = store.stats()

    parts = [
        "# 矛盾信号分析报告",
        f"**日期**: {day}",
        "",
        "## 📋 今日矛盾速览",
        _overview_markdown(active, day),
        "",
    ]
    if new_rows:
        parts += ["## 🔴 今日新增矛盾", _rows_markdown(new_rows, day), ""]
    if open_rows:
        parts += ["## 🟡 仍在持续（历史未决）", _rows_markdown(open_rows, day), ""]
    if resolved_rows:
        parts += ["## 🟢 今日解决（市场裁决）", _rows_markdown(resolved_rows, day), ""]
    parts += ["## 📊 矛盾统计", _stats_markdown(stats, active, day), ""]
    return "\n".join(parts)


def create_contradiction_insight(llm, store: ContradictionStore):
    """FR-7: deep-LLM node that analyses open contradictions and persists
    one insight per contradiction into the store."""

    def contradiction_insight_node(state: dict) -> dict:
        open_rows = store.list_open()
        if not open_rows:
            return {"contradiction_insights": "[]"}

        payload_lines = []
        for r in open_rows:
            a, b = r["claim_a"], r["claim_b"]
            payload_lines.append(
                f"- id: {r['id']}\n"
                f"  对象: {r['subject']} | 类型: {r['kind']}/{r['scope']}/{r['scale']} | "
                f"首次: {r['first_seen']} 最近: {r['last_seen']}\n"
                f"  甲方: {a.get('broker')}[{_DIRECTION.get(a.get('direction'), '?')}] {a.get('quote', '')}\n"
                f"  乙方: {b.get('broker')}[{_DIRECTION.get(b.get('direction'), '?')}] {b.get('quote', '')}"
            )
        payload = "\n".join(payload_lines)

        try:
            result = llm.invoke(
                [
                    SystemMessage(content=CONTRADICTION_INSIGHT_SYSTEM),
                    HumanMessage(content=f"待分析矛盾：\n\n{payload}\n\n请逐条输出洞察 JSON 数组。"),
                ]
            )
            items = extract_json(result.content)
            if not isinstance(items, list):
                items = [items] if isinstance(items, dict) else []
        except Exception as exc:  # LLM 调用/解析失败不阻塞主链路
            logger.warning("Contradiction Insight: failed (%s); no insights", exc)
            return {"contradiction_insights": "[]"}

        valid_ids = {r["id"] for r in open_rows}
        keep = []
        for item in items:
            cid = item.get("id")
            if cid in valid_ids:
                store.save_insight(cid, item)
                keep.append(item)
        logger.info("Contradiction Insight: %d insight(s) persisted", len(keep))
        return {"contradiction_insights": json.dumps(keep, ensure_ascii=False)}

    return contradiction_insight_node


def create_contradiction_report(store: ContradictionStore):
    """Return a LangGraph node that writes contradiction_report into state."""

    def contradiction_report_node(state: dict) -> dict:
        day = state.get("analysis_date", date.today().isoformat())
        return {"contradiction_report": render_contradiction_report(store, day)}

    return contradiction_report_node
