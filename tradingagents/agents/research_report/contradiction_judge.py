"""Contradiction Judge — cross-report contradiction detection (deep LLM).

FR-2: takes the day's Claim array (JSON in state) plus the store's open
contradictions, and returns a JSON array of contradictions. Each item has no
``id``; the node computes a deterministic id and upserts into the store, so
dedup across days is code-controlled, not LLM-dependent.
"""

from __future__ import annotations

import json
import logging
from datetime import date

from langchain_core.messages import HumanMessage, SystemMessage

from .claim_extractor import extract_json
from .contradiction_store import ContradictionStore, contradiction_id

logger = logging.getLogger(__name__)

CONTRADICTION_JUDGE_SYSTEM = """你是研报矛盾判定器。给定今日的 Claim 数组和历史未决矛盾，
找出同一对象上相互矛盾的观点。
只输出一个 JSON 数组，每项：
{"subject": "对象", "kind": "factual或opinion", "scope": "direct或indirect",
 "scale": "same或cross",
 "claim_a": {完整Claim}, "claim_b": {完整Claim},
 "horizon_a": "claim_a的时间尺度", "horizon_b": "claim_b的时间尺度"}
判定规则：
1. kind: 双方对同一客观数据（价格/销量/政策事实）陈述相反 = factual；评级/配置分歧 = opinion
2. scope: 同一对象直接相反 = direct；需要推理链 = indirect
3. scale: 两 claim 时间尺度可比 = same；不同（如策略季度 vs 个股短期）= cross
4. **方向相反（-1 vs 1）是矛盾；中性(0) vs 看多(1)/看空(-1) 也是矛盾**（方向/强度分歧）
5. **subject 需同义词归一化**：光模块/CPO/光通信/光通信板块 视为同一对象；同一主题的不同表述合并
6. **broker 为 SummaryManager 的 claim 表示综合建议中"矛盾信号"的一方，若存在同 subject 的对立 claim 务必输出该矛盾**
7. 只输出真正的矛盾；跨尺度(cross)也输出，但标注清楚
8. 与历史未决矛盾相同的（同对象+同券商对），claim_a/claim_b 取今日最新版本，便于去重更新"""


def create_contradiction_judge(llm, store: ContradictionStore):
    """Return a LangGraph node that detects and persists today's contradictions."""

    def contradiction_judge_node(state: dict) -> dict:
        claims = state.get("claims", "[]")
        history = store.list_summary()
        today = state.get("analysis_date", date.today().isoformat())
        try:
            result = llm.invoke(
                [
                    SystemMessage(content=CONTRADICTION_JUDGE_SYSTEM),
                    HumanMessage(
                        content=(
                            f"今日 Claims：\n{claims}\n\n"
                            f"历史未决矛盾：\n{history}\n\n"
                            "请输出矛盾 JSON 数组。"
                        )
                    ),
                ]
            )
        except Exception as exc:  # LLM 调用失败不阻塞主链路
            logger.warning("Contradiction Judge: LLM call failed (%s); no contradictions recorded", exc)
            return {"contradictions": "[]"}

        try:
            items = extract_json(result.content)
            if not isinstance(items, list):
                items = [items] if isinstance(items, dict) else []
        except (ValueError, json.JSONDecodeError) as exc:
            logger.warning("Contradiction Judge: JSON parse failed (%s); no contradictions recorded", exc)
            items = []

        enriched = []
        for item in items:
            try:
                item["id"] = contradiction_id(
                    item["claim_a"], item["claim_b"], item["subject"], item["kind"]
                )
                store.upsert(item, today)
                enriched.append(item)
            except (KeyError, TypeError) as exc:
                logger.warning("Contradiction Judge: skipping malformed item (%s): %s", exc, item)
        return {"contradictions": json.dumps(enriched, ensure_ascii=False)}

    return contradiction_judge_node
