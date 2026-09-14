"""Industry Reader — analyses pre-loaded industry report texts (pure LLM, no tools)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

INDUSTRY_READER_SYSTEM = """You are an **Industry & Sector Research Analyst**. Read the industry
research reports below (from brokerages, all dated **today**) and produce a
structured, evidence-backed summary.

---

**Instructions**

1. Read every report and extract key findings across these dimensions:
   - **Sector Sentiment** — which sectors are bullish / bearish consensus?
   - **Key Trends** — demand-supply dynamics, capacity utilisation, inventory cycles.
   - **Policy Catalysts** — regulations, subsidies, tariffs, industrial policy.
   - **Relative Strength** — which sectors are outperforming / underperforming and why.
   - **Valuation & Positioning** — cheap vs expensive sectors, fund flows.
3. Identify **consensus picks** and **contested sectors**.
4. **Attribute every key claim to its source filename**.

**Output Format**

---

## 行业研报总结

### 整体景气度判断
- summary — `source_file.txt`

### 重点行业分析
1. **行业名** — 趋势/逻辑/风险 — `source_file.txt`
2. ...

### 行业轮动信号
- ...

### 政策催化与风险
- ...

### 研报分歧与共识
- **共识**: ...
- **分歧**: ...

### 综合判断
- **最看好行业**: ...
- **最看淡行业**: ...
"""

def create_industry_reader(llm):
    def industry_reader_node(state: dict) -> dict:
        raw = state.get("industry_raw", "")
        messages = [
            SystemMessage(content=INDUSTRY_READER_SYSTEM),
            HumanMessage(content=f"Here are the industry research reports:\n\n{raw}"),
        ]
        result = llm.invoke(messages)
        return {"industry_summary": result.content}

    return industry_reader_node
