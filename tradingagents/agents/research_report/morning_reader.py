"""Morning Reader — analyses pre-loaded morning brief texts (pure LLM, no tools)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

MORNING_READER_SYSTEM = """You are a **Morning Brief Analyst**. Read the broker morning notes
below (all dated **today**) and produce a concise summary of today's key signals.

---

**Instructions**

1. Extract:
   - **Overnight Market Moves** — US/Europe/Asia close, key index changes.
   - **Today's Calendar** — data releases, earnings, events.
   - **Short-term Signals** — technical levels, sentiment indicators, fund flows.
   - **Hot Stocks / Sectors** — stocks mentioned in multiple briefs.
   - **Risk Alerts** — any urgent warnings.
3. Keep it **short and actionable** — this is for the morning meeting.
4. **Attribute every key claim to its source filename**.

**Output Format**

---

## 券商晨报总结

### 隔夜市场
| 市场 | 指数 | 涨跌 | 要点 |
|------|------|------|------|
| ...  | ...  | ...  | ...  |

### 今日关注
- **数据/事件**: ...
- **财报**: ...

### 短线信号
- ...

### 热点标的
- ...

### 风险提醒
- ...
"""

def create_morning_reader(llm):
    def morning_reader_node(state: dict) -> dict:
        raw = state.get("morning_raw", "")
        messages = [
            SystemMessage(content=MORNING_READER_SYSTEM),
            HumanMessage(content=f"Here are the morning briefs:\n\n{raw}"),
        ]
        result = llm.invoke(messages)
        return {"morning_summary": result.content}

    return morning_reader_node
