# Pre-Analyst：行业板块预分析模块

在完整的多 Agent 交易分析管线启动之前，Pre-Analyst 模块通过 **三方辩论** 先判断当前哪些行业/板块最具投资潜力，为后续的个股分析提供方向性指导。

## 架构概述

```
┌─────────────────────────────────────────────────┐
│                 Pre-Analyst 模块                  │
│                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐  │
│  │ Cycle    │──→│ Growth   │──→│ Defensive    │  │
│  │ 周期派    │   │ 成长派    │   │ 防御派        │  │
│  └──────────┘   └──────────┘   └──────────────┘  │
│       ↑              ↑              ↑    │       │
│       └──────────────┴──────────────┘    │       │
│              循环辩论 (N 轮)              │       │
│                                          ↓       │
│                              ┌─────────────────┐ │
│                              │ Sector Manager   │ │
│                              │ 行业裁判 (最终决策)│ │
│                              └─────────────────┘ │
└─────────────────────────────────────────────────┘
                         ↓
             sector_recommendation 注入 AgentState
                         ↓
         下游分析师（Market / News / Fundamentals）读取
```

### 三个辩论 Agent

| Agent                  | 投资哲学                         | 关注的行业                 |
| ---------------------- | -------------------------------- | -------------------------- |
| **周期派 (Cyclical)**  | 宏观经济周期驱动行业轮动         | 金融、能源、工业、材料     |
| **成长派 (Growth)**    | 结构性趋势和技术创新创造长期价值 | 科技、AI、新能源、生物医药 |
| **防御派 (Defensive)** | 资本保值和下行保护优先           | 消费、公用事业、医疗       |

### 裁判 (Sector Manager)

使用 **深度思考 LLM**（与 Research Manager 同级），阅读完整辩论记录后输出结构化推荐：

- 推荐行业（按优先级排列）
- 应低配/回避的行业
- 信心等级
- 关键假设与风险

---

## 使用方式

### 方式一：独立运行（推荐先验证流程）

Pre-Analyst 模块可以 **完全脱离** 12 Agent 完整管线独立运行，不依赖 `TradingAgentsGraph`：

```bash
# 使用已激活的 TradingAgent conda 环境
conda activate TradingAgent
python -m tradingagents.agents.pre_analyst.standalone
```

指定参数：

```bash
python -m tradingagents.agents.pre_analyst.standalone \
    --provider deepseek \
    --model deepseek-chat \
    --rounds 2
```

程序化调用：

```python
from tradingagents.agents.pre_analyst.standalone import run_sector_analysis

result = run_sector_analysis(
    provider="openai",
    model="gpt-4o",
    max_debate_rounds=2,          # 辩论轮数（每轮 3 人各发言 1 次）
)

print(result["sector_recommendation"])   # Sector Manager 的最终推荐
print(result["debate_history"])          # 完整辩论记录
print(result["judge_decision"])          # 同 sector_recommendation
```

### 方式二：嵌入完整管线

在 `TradingAgentsGraph` 中启用：

```python
# main.py 或 cli/main.py 中
from tradingagents.graph.trading_graph import TradingAgentsGraph

graph = TradingAgentsGraph(
    selected_analysts=["market", "social", "news", "fundamentals"],
    config=config,
)

# 构建图时传入 enable_pre_analyst=True
graph.graph_setup.setup_graph(
    selected_analysts=["market", "social", "news", "fundamentals"],
    enable_pre_analyst=True,   # ← 启用行业预分析
)

# 后续流程不变，下游 Agent 会自动从 state 读取 sector_recommendation
```

启用后，完整执行流程变为：

```
START → 周期派 → 成长派 → 防御派 → ...(循环)... → Sector Manager
      → Market Analyst → Sentiment Analyst → News Analyst → Fundamentals Analyst
      → Bull/Bear 辩论 → Research Manager → Trader
      → 风险三方辩论 → Portfolio Manager → END
```

### 方式三：不启用（默认行为）

```python
# enable_pre_analyst 默认为 False，行为与之前完全一致
graph.graph_setup.setup_graph(
    selected_analysts=["market", "social", "news", "fundamentals"],
    # enable_pre_analyst=False  ← 默认值
)
```

---

## 配置参数

| 参数                  | 说明                            | 默认值                   |
| --------------------- | ------------------------------- | ------------------------ |
| `max_debate_rounds`   | 辩论轮数（每轮 3 人各发言一次） | `1`（共 3 次发言）       |
| 辩论 Agent 的 LLM     | 使用 `quick_thinking_llm`       | 与分析师一致             |
| Sector Manager 的 LLM | 使用 `deep_thinking_llm`        | 与 Research Manager 一致 |

---

## 状态结构

Pre-Analyst 的输出注入 `AgentState`，下游 Agent 可直接读取：

```python
# 在任意下游 Agent 的 node 函数中：
sector_rec = state.get("sector_recommendation", "")

# debate 详细记录在：
debate = state.get("sector_debate_state", {})
debate["cyclical_history"]   # 周期派全部发言
debate["growth_history"]     # 成长派全部发言
debate["defensive_history"]  # 防御派全部发言
debate["history"]            # 完整辩论记录
debate["judge_decision"]     # Sector Manager 最终裁决
debate["count"]              # 总发言次数
```

---

## 运行测试

```bash
conda activate TradingAgent
pip install pytest  # 如未安装

# 单元测试（不调 LLM）
pytest tests/test_pre_analyst_state.py -v -m unit

# 节点测试（mock LLM）
pytest tests/test_pre_analyst_nodes.py -v -m unit

# 集成测试（mock LLM，验证完整图流程）
pytest tests/test_pre_analyst_pipeline.py -v -m integration

# 全量
pytest tests/test_pre_analyst_*.py -v

# 确保不影响现有测试
pytest tests/ -v  # enable_pre_analyst=False 时全量应通过
```

---

## 后续迭代计划

| 优先级 | 内容                                                     |
| ------ | -------------------------------------------------------- |
| 🔴 高  | 为辩论 Agent 添加数据工具（行业 ETF 表现、板块轮动指标） |
| 🟡 中  | CLI 交互式开关（`--enable-pre-analyst`）                 |
| 🟡 中  | 行业推荐注入到 Memory Log 供复盘                         |
| 🟢 低  | 环境变量配置 `TRADINGAGENTS_ENABLE_PRE_ANALYST`          |
| 🟢 低  | 报告目录增加 `0_pre_analyst/` 小节                       |

---

## 文件位置

```
tradingagents/agents/pre_analyst/
├── __init__.py                  # 模块导出
├── sector_debate_state.py       # SectorDebateState 类型定义
├── cyclical_analyst.py          # 周期派 agent
├── growth_analyst.py            # 成长派 agent
├── defensive_analyst.py         # 防御派 agent
├── sector_manager.py            # 裁判 agent
└── standalone.py                # 独立运行入口

tests/
├── test_pre_analyst_state.py    # 状态 schema 单元测试
├── test_pre_analyst_nodes.py    # Agent 节点测试 (mock LLM)
└── test_pre_analyst_pipeline.py # 独立管线集成测试
```
