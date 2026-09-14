# 研报分析 + 矛盾信号检测 — 使用指南

> 基于 TradingAgents v3.0 的研报阅读系统：每天爬取的券商研报 → LLM 多 Agent 总结 → 综合投资建议 + **矛盾信号分析报告**。

---

## 1. 快速开始

```powershell
# 用 TradingAgent conda 环境
& "D:\anaconda3\envs\TradingAgent\python.exe" launchers\research_report\launch.py
```

什么参数都不加，默认：

- 分析**今天**的研报
- 数据根目录：`D:\WORKS\all_data\data\report_data`
- 输出到：`reports/{今天}/`
- 矛盾库：`reports/contradictions.db`

## 2. 常用命令

```powershell
# 分析指定日期
& "D:\anaconda3\envs\TradingAgent\python.exe" launchers\research_report\launch.py --date 2026-08-06

# 指定数据根目录 + 输出目录 + 矛盾库路径
& "D:\anaconda3\envs\TradingAgent\python.exe" launchers\research_report\launch.py `
    --date 2026-08-06 --root D:\WORKS\all_data\data\report_data `
    --output reports\2026-08-06 --db reports\contradictions.db

# 只看参数说明（不触发 LLM）
& "D:\anaconda3\envs\TradingAgent\python.exe" launchers\research_report\launch.py --help
```

## 3. 参数一览

| 参数       | 默认值                               | 说明                                     |
| ---------- | ------------------------------------ | ---------------------------------------- |
| `--root`   | `D:\WORKS\all_data\data\report_data` | 研报数据根目录（内含按日期分的子文件夹） |
| `--date`   | 今天                                 | 分析日期，格式 `YYYY-MM-DD`              |
| `--output` | `reports/{date}/`                    | 报告输出目录                             |
| `--db`     | `reports/contradictions.db`          | 矛盾信号 SQLite 库路径（跨天积累）       |

## 4. 跑完看什么

输出目录下会有 **7 份报告**：

```
reports/2026-08-06/
├── macro_summary.md        # 宏观研报总结
├── industry_summary.md     # 行业研报总结
├── stock_summary.md        # 个股研报总结
├── strategy_summary.md     # 策略报告总结
├── morning_summary.md      # 券商晨报总结
├── final_summary.md        # 综合投资建议（主链路，含交叉验证）
└── contradiction_report.md # ⭐ 矛盾信号分析报告（新增）
```

## 5. 矛盾报告怎么读

`contradiction_report.md` 分四个区：

| 区                  | 含义                         | 价值                                               |
| ------------------- | ---------------------------- | -------------------------------------------------- |
| 🔴 **今日新增矛盾** | 当天检出的券商分歧           | 预期差 = 潜在机会/风险，这是研报里信息量最大的部分 |
| 🟡 **仍在持续**     | 历史未决矛盾（跨天追踪）     | 看分歧持续了几天、是否有新券商站队                 |
| 🟢 **今日解决**     | 市场已裁决的矛盾（谁对谁错） | M2 Verifier 上线后自动产出                         |
| 📊 **矛盾统计**     | 累计 / 未决 / 已解决条数     | 长期运行形成"分歧热度"指标                         |

每条矛盾包含：**对象**（如 AI算力）、**类型**（factual/opinion、direct/indirect、same/cross）、**双方券商 + 方向 + 原文引述**。

### 真实示例（2026-08-06）

```
## 🔴 今日新增矛盾
- **AI算力/泛热门科技赛道**（opinion/indirect/same）：
  - 国新证券[看多] 建议AI算力等投资机会。
  - 国元证券[看空] 阶段性减配泛热门科技赛道。
- **A股市场风格配置**（opinion/indirect/same）：
  - 中银证券[看多 高盈利高估值风格] 8月高盈利高估值风格有望占优。
  - 国元证券[看多 红利低波资产] 增配红利低波资产。
```

## 6. 核心价值：跨天积累

矛盾库是 SQLite 持久化的，**每天跑都会累积**：

- 同一对券商 + 同一对象的矛盾**复用同一 id**，`last_seen` 刷新，不重复记录
- 天天跑，"仍在持续"区会显示矛盾**持续了几天**，直到被新报告或市场结果解决
- 查历史矛盾：

```powershell
& "D:\anaconda3\envs\TradingAgent\python.exe" -c "import sqlite3; c=sqlite3.connect('reports/contradictions.db'); [print(r) for r in c.execute('SELECT id, status, first_seen, last_seen FROM contradictions')]"
```

## 7. 跑测试（不消耗 API）

```powershell
& "D:\anaconda3\envs\TradingAgent\python.exe" -m pytest tests/test_contradiction_store.py tests/test_report_reader_graph.py -v
```

## 8. 注意事项

- **耗时**：全流程调真实 LLM（默认 deepseek），约 5~10 分钟、消耗 API 额度。想快速验证逻辑就跑测试（FakeLLM，秒级）。
- **LLM 配置**：读取项目根 `.env` 的 `TRADAGINGAGENTS_*` 配置（provider/model/API key）。
- **编码**：启动脚本已内置 UTF-8 修复，Windows 默认 GBK 控制台也能正常打印 ✓/emoji。
- **数据前提**：`{root}/{date}/` 下需要有 `宏观研究/ 行业研报/ 个股研报/ 策略报告/ 券商晨报` 至少一个分类文件夹（.txt 文件）。

## 9. 后续路线

- [x] M1 矛盾检测闭环（抽取 → 判定 → 落库 → 报告）
- [ ] M2 市场验证（Verifier：价格/财报对账，裁决谁对）
- [ ] M3 反哺 Summary Manager（未决矛盾降置信度）+ 分析师信用分

详见 `docs/research-report-contradiction.md`。
