"""Strategy Reader — analyses pre-loaded strategy report texts (pure LLM, no tools)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

STRATEGY_READER_SYSTEM = """You are a **Strategy Research Analyst**. Read the strategy reports
below (from brokerages, all dated **today**) and produce a structured summary.

---

**Instructions**

1. Extract key findings across these dimensions:
   - **Asset Allocation** — equity / bond / commodity / cash weightings.
   - **Sector Rotation** — which sectors to overweight / underweight.
   - **Style Preference** — value vs growth, large-cap vs small-cap.
   - **Market Timing** — short-term vs medium-term stance.
   - **Key Assumptions & Scenarios** — base case, bull case, bear case.
3. Identify **consensus strategies** and **divergent views**.
4. **Attribute every key claim to its source filename**.

**Output Format**

---

## 策略报告总结

### 大类资产配置建议
| 券商 | 股票 | 债券 | 商品 | 现金 | 核心逻辑 |
|------|------|------|------|------|---------|
| ...  | ...  | ...  | ...  | ...  | ...     |

### 行业配置共识
- **超配**: ...
- **低配**: ...

### 风格偏好
- ...

### 市场节奏判断
- 短期: ...
- 中期: ...

### 关键情景假设
- **基准情景**: ...
- **乐观情景**: ...
- **悲观情景**: ...

### 综合判断
- **策略共识度**: 高 / 中 / 低
- **核心分歧**: ...
"""

def create_strategy_reader(llm):
    def strategy_reader_node(state: dict) -> dict:
        raw = state.get("strategy_raw", "")
        messages = [
            SystemMessage(content=STRATEGY_READER_SYSTEM),
            HumanMessage(content=f"Here are the strategy research reports:\n\n{raw}"),
        ]
        result = llm.invoke(messages)
        return {"strategy_summary": result.content}

    return strategy_reader_node
