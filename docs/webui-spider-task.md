# 爬虫任务集成设计（任务中心扩展）

> **状态**: 设计文档 | **版本**: v0.1 | **日期**: 2026-08-15
>
> 关联: [`vue-frontend.md`](vue-frontend.md)（前端总设计,M2 任务中心 §12）

---

## 1. 背景与数据流闭环

东方财富研报爬虫（`D:\WORKS\all_data\src\industry_report_spider\`）是目前**唯一的数据入口**:

```mermaid
graph LR
    A[爬虫抓取] --> B[report_data/{date}/{分类}/*.txt]
    B --> C[研报阅读器 5 Reader]
    C --> D[总结 + 矛盾分析]
    D --> E[前端面板展示]
```

前端目前覆盖 C→E,缺 A。把爬虫加进任务中心后,整条链路都能在浏览器里驱动。

## 2. 爬虫现状盘点

| 项 | 值 |
| --- | --- |
| 入口 | `python -m src.industry_report_spider.industry_report_spider`（**cwd 必须在 `D:\WORKS\all_data`**） |
| 参数 | `--type`(industry/stock/macro/strategy/broker/all)、`--start/--end`(YYYY-MM-DD)、`--test`、`--limit`、`--pages`、`--industry`(行业代码,一般用默认) |
| 输出 | `D:\WORKS\all_data\data\report_data`（**正好是研报阅读器的默认数据源**,无缝衔接） |
| 幂等性 | ✅ 断点续抓:progress 文件记录已抓 infoCode,重复运行跳过已抓 |
| 反爬 | 随机请求延时 + 页面延时 + 3 次重试,全量抓取可能耗时 10~40 分钟 |
| 依赖 | requests / lxml(TradingAgent conda 环境已具备,无需新环境) |
| 日志 | stdout 逐行中文输出,UTF-8;与现有 SSE 管道完全兼容 |

## 3. 集成方案评估

| 方案 | 做法 | 评价 |
| --- | --- | --- |
| **A. 第 4 种任务类型**(推荐) | 复用 M2 JobManager:spider 成为白名单命令之一 | 零新组件;单任务锁、SSE、历史、恢复全部复用;改动最小 |
| B. 复合流水线"抓取+阅读一键" | spider 完成后自动触发 daily | 体验好,但引入任务链状态机;爬虫时长不确定,失败传播复杂。**列为 v2 可选** |
| C. 独立微服务 | 爬虫单独起一个常驻服务 | 过度设计:爬虫是批处理,不是服务;YAGNI 排除 |

**结论:方案 A。** 复用 M2 的整套任务框架,只是把"命令 + 参数 + 校验 + 表单"各加一行。

## 4. 实现设计

### 4.1 后端(`webapi/jobs.py` + `webapi/main.py`)

**命令映射**(白名单扩展):

| type | 命令(cwd) |
| --- | --- |
| `spider` | `[SPIDER_PYTHON, "-m", "src.industry_report_spider.industry_report_spider", "--type", t, "--start", s, "--end", e, (+ "--test"), (+ "--limit" n)]`,**cwd = `D:\WORKS\all_data`** |

**配置**(env,后端启动时读取):

| env | 默认 | 说明 |
| --- | --- | --- |
| `SPIDER_DIR` | `D:\WORKS\all_data` | 爬虫 cwd,白名单:命令只允许在该目录下执行 |
| `SPIDER_PYTHON` | `sys.executable` | 爬虫解释器(当前 conda 环境已够,预留切换) |

**JobManager 扩展点**(3 处小改):

1. `_command(job_type, params)` 增加 `spider` 分支;新增 `_cwd(job_type)`(daily/pre/trading 用项目根,spider 用 SPIDER_DIR)
2. `validate_params` 增加 spider 校验:
   - `type ∈ {industry, stock, macro, strategy, broker, all}`
   - `start/end`:`YYYY-MM-DD` 合法日期,`start ≤ end`;两者都可空(爬虫默认今天)
   - `test` 布尔、`limit` 整数 1~100
3. **不暴露 `--industry`/`--pages`**:用爬虫默认值,减少注入面(需要时再加)

**安全性**:`SPIDER_DIR` 只允许后端配置的固定值,前端不传路径;参数仍然全部 `shell=False` 列表传参。

### 4.2 前端(`JobsView.vue` + `api/types.ts`)

1. **radio 卡片加第 4 张**:🕷 **数据抓取** · "东方财富研报爬虫,抓取券商研报数据"(不置灰)
2. **表单联动**(type=spider 时):
   - 研报类型下拉:行业/个股/宏观/策略/券商晨报/全部
   - 日期范围:start + end(可空,默认今天)
   - 测试模式 checkbox(提示:仅抓 limit 篇,用于验证链路)
3. **任务完成后提示**:spider `done` → 提示条"数据抓取完成 → 发起研报阅读"(跳 `/jobs` 并预选 daily;v1 手动引导,v2 见 §5)
4. `typeLabel` 增加 `spider: "数据抓取"`

### 4.3 与现有页面零冲突

- 爬虫输出目录 = reader 默认 root,抓完后 `/reports/daily` 对应日期自然出现数据,无需任何联动代码
- M1/M2 全部既有 API 与页面不动

## 5. 分期

| 期 | 内容 | 自检 |
| --- | --- | --- |
| **v1**(本轮) | spider 单任务:抓取 → 日志流 → 完成提示 | 页面发起 `--test --limit 2` 抓行业研报 → 日志滚动 → `report_data/{今天}/行业研报/` 出现 2 个 txt |
| **v2**(可选) | 复合任务 `spider_chain`:spider done 后自动 start daily(后端在 _pump 结束回调里串起第二个子进程,单任务锁内完成) | 一键后最终产出矛盾报告;中途失败自动标记 failed 且保留日志 |

## 6. 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-1 | 任务创建 | 任务中心选"数据抓取"→ 测试模式 → 提交成功,历史表出现记录 |
| AC-2 | 参数校验 | `start > end`、`type=xxx` 一律 422,不产生子进程 |
| AC-3 | 日志流 | SSE 逐行显示爬虫输出(页码/篇数/✅),无重复行 |
| AC-4 | 数据落地 | 测试模式结束后 `report_data/{date}/` 出现对应分类 txt |
| AC-5 | 幂等重跑 | 同一日期再抓,progress 跳过已抓,日志显示"已抓 N 篇" |
| AC-6 | 回归 | M1+M2 全部 22 个测试保持绿;reader/pre/daily 任务行为不变 |
