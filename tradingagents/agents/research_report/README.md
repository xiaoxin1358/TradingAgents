# Research Report Agents

基于 LLM 的研报阅读与总结 Agent 系统，独立于主交易流水线，覆盖 5 类研报。

## 快速开始

```bash
# 最简用法：所有参数都有默认值
python run_report_reader.py

# 指定日期
python run_report_reader.py --date 2026-07-25
```

| 参数       | 必填 | 默认值                               | 说明                              |
| ---------- | ---- | ------------------------------------ | --------------------------------- |
| `--root`   | 否   | `D:\WORKS\all_data\data\report_data` | 研报数据根目录                    |
| `--date`   | 否   | 今天                                 | 分析日期 YYYY-MM-DD               |
| `--output` | 否   | `reports/{date}/`                    | 报告输出目录                      |
| `--db`     | 否   | `reports/contradictions.db`          | 矛盾信号 SQLite 库（跨天积累）    |

> 也可用 `launchers/research_report/launch.py`（薄封装，已含 Windows GBK 控制台 UTF-8 修复）。

## 架构

```
                          ┌─ 宏观 Reader   ─┐
                          ├─ 行业 Reader   ─┤
Data Loader (纯 I/O) ─────┼─ 个股 Reader   ─┼─→ Summary Manager ──→ final_summary.md
   5 类 *_raw 预取         ├─ 策略 Reader   ─┤    (deep, 交叉验证)
                          └─ 晨报 Reader   ─┘         │
                                                       │ 矛盾支线（串行）
                                                       ▼
                       Claim Extractor → Contradiction Judge → Contradiction Insight
                       (quick, 两次抽取)   (deep, 判定+落库)      (deep, 成因洞察)
                                                       │
                                                       ▼
                                       Contradiction Report (纯代码渲染)
                                                  → contradiction_report.md
```

5 个 Reader **并行**（无工具、纯 LLM），主链路与矛盾支线各自落盘；矛盾支线所有节点容错，失败不阻塞主链路。

## 模块

| 文件                       | 职责                                        |
| -------------------------- | ------------------------------------------- |
| `state.py`                 | `ResearchReportState`                       |
| `tools.py`                 | `load_all_reports` 数据预取                 |
| `macro_reader.py`          | 宏观研报                                    |
| `industry_reader.py`       | 行业研报                                    |
| `stock_reader.py`          | 个股研报                                    |
| `strategy_reader.py`       | 策略报告                                    |
| `morning_reader.py`        | 券商晨报                                    |
| `summary_manager.py`       | 交叉验证 & 综合建议                         |
| `claim_extractor.py`       | 观点结构化抽取（含 final_summary 矛盾信号） |
| `contradiction_judge.py`   | 矛盾判定 + 确定性 id 落库                   |
| `contradiction_report.py`  | 成因洞察 + 报告渲染                         |
| `contradiction_store.py`   | SQLite 持久化（跨天去重、生命周期）         |

## 扩展

详见 `docs/research-report-agents.md`（阅读器）、`docs/research-report-contradiction.md`（矛盾检测）、`docs/research-report-contradiction-insight.md`（成因洞察）。
