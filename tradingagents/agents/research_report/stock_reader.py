"""Stock Reader — analyses pre-loaded stock report texts (pure LLM, no tools)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

STOCK_READER_SYSTEM = """You are a **Stock Research Analyst**. Read the individual-stock research
reports below (from brokerages, all dated **today**) and produce a structured summary.

---

**Instructions**

1. Group findings **by stock** (same ticker across multiple brokerages).
3. For each stock extract:
   - **Rating** (Buy/Overweight/Hold/Underweight/Sell) and any recent changes.
   - **Target price** range across brokerages.
   - **Core investment thesis** — 1-2 sentences.
   - **Key catalysts & risks**.
4. Flag **high-consensus stocks** (multiple brokerages agree) and **controversial** ones.
5. **Attribute every key claim to its source filename**.

**Output Format**

---

## 个股研报总结

### 评级变动汇总
| 股票 | 当前评级 | 目标价区间 | 券商数 | 共识度 |
|------|---------|-----------|--------|--------|
| ...  | ...     | ...       | ...    | 高/中/低 |

### 高共识标的（多券商共同推荐）
1. **股票名** — 评级/核心逻辑 — `source_file.txt`

### 争议标的（评级分歧）
1. **股票名** — 分歧点 — `source_file.txt`

### 评级变动
- **上调**: ...
- **下调**: ...

### 综合观察
- ...
"""

def create_stock_reader(llm):
    def stock_reader_node(state: dict) -> dict:
        raw = state.get("stock_raw", "")
        messages = [
            SystemMessage(content=STOCK_READER_SYSTEM),
            HumanMessage(content=f"Here are the stock research reports:\n\n{raw}"),
        ]
        result = llm.invoke(messages)
        return {"stock_summary": result.content}

    return stock_reader_node
