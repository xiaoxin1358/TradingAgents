"""Summary Manager — reads all 5 Reader summaries and produces final investment advice."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, RemoveMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


SUMMARY_MANAGER_SYSTEM = """You are the **Chief Investment Strategist**.  Your team of 5 analysts
has each produced a summary of today's brokerage research reports.  Your job is
to **cross-validate their findings** and produce a coherent, actionable
investment recommendation.

---

**Instructions**

1. Read all 5 summaries carefully.
2. **Cross-validate**: does the macro backdrop support the industry calls?
   Do strategy allocations align with individual stock ratings?  Flag contradictions.
3. Synthesise into:
   - **Asset-class implications** (equities, bonds, commodities, FX).
   - **Sector tilts** (overweight / underweight) with multi-analyst support.
   - **High-conviction stock ideas** (where multiple analysts converge).
   - **Key indicators** to monitor.
   - **Risk level** (low / medium / high) and top risks.
4. Be explicit about **confidence**: high when multiple analysts agree,
   low when there are contradictions.

**Output Format**

---

## 投资建议综合报告

### 宏观背景
...

### 大类资产配置
| 资产类别 | 方向 | 逻辑 | 置信度 |
|---------|------|------|--------|
| ...     | ...  | ...  | 高/中/低 |

### 行业配置建议
| 行业 | 建议 | 宏观支撑 | 策略支撑 | 置信度 |
|------|------|---------|---------|--------|
| ...  | ...  | ✓/✗     | ✓/✗     | ...    |

### 重点关注标的
| 股票 | 评级共识 | 核心逻辑 | 来源 |
|------|---------|---------|------|
| ...  | ...     | ...     | ...  |

### 交叉验证发现
- **一致信号**: ...
- **矛盾信号**: ...

### 关键跟踪指标
...

### 风险等级
- **当前**: 低 / 中 / 高
- **核心风险点**: ...

### 一句话总结
...
"""


def create_summary_manager(llm):
    """Return a LangGraph node that synthesises all 5 summaries into investment advice."""

    def summary_manager_node(state: dict) -> dict:
        all_summaries = (
            f"## 宏观研究总结\n\n{state.get('macro_summary', '')}\n\n---\n\n"
            f"## 行业研报总结\n\n{state.get('industry_summary', '')}\n\n---\n\n"
            f"## 个股研报总结\n\n{state.get('stock_summary', '')}\n\n---\n\n"
            f"## 策略报告总结\n\n{state.get('strategy_summary', '')}\n\n---\n\n"
            f"## 券商晨报总结\n\n{state.get('morning_summary', '')}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant collaborating with other assistants. "
                    "\n{system_message}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        ).partial(system_message=SUMMARY_MANAGER_SYSTEM)

        context_msg = HumanMessage(
            content=f"Here are the 5 analyst summaries:\n\n{all_summaries}\n\n"
            "Please produce your cross-validated investment recommendation "
            "following the output format above."
        )

        messages = list(state["messages"]) + [context_msg]
        result = (prompt | llm).invoke(messages)

        return {
            "messages": [result],
            "final_summary": result.content,
        }

    return summary_manager_node


def create_summary_msg_delete():
    """Clear message history after the Summary Manager finishes."""

    def delete_messages(state: dict) -> dict:
        messages = state["messages"]
        removal = [RemoveMessage(id=m.id) for m in messages]
        analysis_date = state.get("analysis_date", "")
        placeholder = HumanMessage(
            content=f"Research report analysis complete. Date: {analysis_date}."
        )
        return {"messages": removal + [placeholder]}

    return delete_messages
