"""Unit tests for the contradiction store + report rendering (no LLM).

Covers the M1 self-check: deterministic id, cross-day dedup (id reuse),
and the four report sections.
"""

import pytest

from tradingagents.agents.research_report.contradiction_report import (
    render_contradiction_report,
)
from tradingagents.agents.research_report.contradiction_store import (
    ContradictionStore,
    contradiction_id,
)


def _claim(broker: str, subject: str, direction: int) -> dict:
    return {
        "broker": broker,
        "author": None,
        "report_type": "个股研报",
        "subject": subject,
        "direction": direction,
        "strength": 0.8,
        "horizon": "中期",
        "target": None,
        "quote": f"{broker} 观点原文",
    }


def _item(subject: str, kind: str, a: dict, b: dict) -> dict:
    return {
        "id": contradiction_id(a, b, subject, kind),
        "subject": subject,
        "kind": kind,
        "scope": "direct",
        "scale": "same",
        "claim_a": a,
        "claim_b": b,
        "horizon_a": a["horizon"],
        "horizon_b": b["horizon"],
    }


@pytest.fixture()
def store(tmp_path):
    return ContradictionStore(str(tmp_path / "test.db"))


class TestContradictionId:
    def test_broker_order_irrelevant(self):
        a, b = _claim("国元", "AI算力", 1), _claim("中邮", "AI算力", -1)
        assert contradiction_id(a, b, "AI算力", "opinion") == contradiction_id(
            b, a, "AI算力", "opinion"
        )

    def test_kind_is_part_of_id(self):
        a, b = _claim("国元", "AI算力", 1), _claim("中邮", "AI算力", -1)
        assert contradiction_id(a, b, "AI算力", "opinion") != contradiction_id(
            a, b, "AI算力", "factual"
        )


class TestUpsertDedup:
    def test_same_id_reuses_row_across_days(self, store):
        item = _item("AI算力", "opinion", _claim("国元", "AI算力", 1), _claim("中邮", "AI算力", -1))
        assert store.upsert(item, "2026-08-10") is True
        assert store.upsert(item, "2026-08-11") is False  # updated, not re-inserted

        rows = store.list_open()
        assert len(rows) == 1
        assert rows[0]["first_seen"] == "2026-08-10"
        assert rows[0]["last_seen"] == "2026-08-11"

    def test_different_brokers_are_separate_rows(self, store):
        a = _claim("国元", "AI算力", 1)
        b1, b2 = _claim("中邮", "AI算力", -1), _claim("东吴", "AI算力", -1)
        store.upsert(_item("AI算力", "opinion", a, b1), "2026-08-10")
        store.upsert(_item("AI算力", "opinion", a, b2), "2026-08-10")
        assert len(store.list_open()) == 2


class TestReport:
    def test_contains_all_four_sections_when_data_present(self, store):
        store.upsert(
            _item("AI算力", "opinion", _claim("国元", "AI算力", 1), _claim("中邮", "AI算力", -1)),
            "2026-08-10",
        )
        old = _item("光伏", "opinion", _claim("国元", "光伏", 1), _claim("东吴", "光伏", -1))
        store.upsert(old, "2026-08-01")
        store.upsert(old, "2026-08-09")
        done = _item("乘用车", "factual", _claim("中汽", "乘用车", 1), _claim("华泰", "乘用车", -1))
        store.upsert(done, "2026-08-05")
        store.resolve(done["id"], "a", "market", "2026-08-10")
        report = render_contradiction_report(store, "2026-08-10")
        for section in ["今日新增矛盾", "仍在持续", "今日解决", "矛盾统计"]:
            assert section in report
        assert "AI算力" in report
        assert "累计矛盾：3 条" in report


class TestReportV33:
    """docs 7.3.3: 三区互斥、顶部概览、洞察折叠、quote 不截断、空区块不渲染。"""

    def _seed(self, store):
        new = _item("AI算力", "opinion", _claim("国元", "AI算力", 1), _claim("中邮", "AI算力", -1))
        store.upsert(new, "2026-08-10")
        old = _item("光伏", "opinion", _claim("国元", "光伏", 1), _claim("东吴", "光伏", -1))
        store.upsert(old, "2026-08-01")
        store.upsert(old, "2026-08-09")
        return new, old

    def test_sections_mutually_exclusive(self, store):
        self._seed(store)
        report = render_contradiction_report(store, "2026-08-10")
        new_start = report.index("## 🔴")
        cont_start = report.index("## 🟡")
        stats_start = report.index("## 📊")
        assert "AI算力" in report[new_start:cont_start]        # 新增区有
        assert "AI算力" not in report[cont_start:stats_start]  # 持续区没有
        assert "光伏" in report[cont_start:stats_start]        # 持续区有
        assert "光伏" not in report[new_start:cont_start]      # 新增区没有

    def test_empty_section_not_rendered(self, store):
        store.upsert(
            _item("AI算力", "opinion", _claim("国元", "AI算力", 1), _claim("中邮", "AI算力", -1)),
            "2026-08-10",
        )
        report = render_contradiction_report(store, "2026-08-10")
        assert "今日解决" not in report    # 无 resolved 数据
        assert "仍在持续" not in report    # 无历史矛盾（全是今日新增）

    def test_overview_table_present(self, store):
        self._seed(store)
        report = render_contradiction_report(store, "2026-08-10")
        assert "## 📋 今日矛盾速览" in report
        assert "| 对象 | 类型 | 甲方 | 乙方 | 持续天数 |" in report
        assert "今日新增" in report  # 概览的持续天数列（AI算力）
        assert "9 天" in report      # 光伏 08-01 → 08-10

    def test_long_quote_not_truncated(self, store):
        a = _claim("国元", "AI算力", 1)
        a["quote"] = "看多逻辑" * 30  # 120 字，远超旧版 60 字截断
        store.upsert(_item("AI算力", "opinion", a, _claim("中邮", "AI算力", -1)), "2026-08-10")
        report = render_contradiction_report(store, "2026-08-10")
        assert a["quote"] in report

    def test_insight_collapses_to_summary_line(self, store):
        item = _item("AI算力", "opinion", _claim("国元", "AI算力", 1), _claim("中邮", "AI算力", -1))
        store.upsert(item, "2026-08-10")
        store.save_insight(item["id"], {
            "id": item["id"], "cause_type": "框架假设", "cause": "关键假设不同",
            "analysis": "双方点评", "watch": "跟踪云厂商资本开支", "tilt": "不确定",
        })
        report = render_contradiction_report(store, "2026-08-10")
        assert "📝 **洞察**：框架假设 · 倾向：不确定" in report
        assert "<details><summary>详情</summary>" in report
        assert "跟踪云厂商资本开支" in report  # 折叠内容仍在文本中，仅视觉折叠


class TestInsight:
    def test_save_insight_persists_and_renders(self, store):
        item = _item("AI算力", "opinion", _claim("国元", "AI算力", 1), _claim("中邮", "AI算力", -1))
        store.upsert(item, "2026-08-10")
        store.save_insight(item["id"], {
            "id": item["id"], "cause_type": "框架假设", "cause": "关键假设不同",
            "analysis": "双方点评", "watch": "跟踪云厂商资本开支", "tilt": "不确定",
        })
        rows = store.list_open()
        assert rows[0]["insight"]
        report = render_contradiction_report(store, "2026-08-10")
        assert "📝 **洞察**" in report
        assert "框架假设" in report
        assert "跟踪云厂商资本开支" in report

    def test_legacy_db_without_insight_column_migrates(self, tmp_path):
        import sqlite3

        db = tmp_path / "legacy.db"
        conn = sqlite3.connect(str(db))
        conn.execute(
            "CREATE TABLE contradictions ("
            " id TEXT PRIMARY KEY, subject TEXT NOT NULL, kind TEXT NOT NULL,"
            " scope TEXT NOT NULL, scale TEXT NOT NULL, claim_a TEXT NOT NULL,"
            " claim_b TEXT NOT NULL, horizon_a TEXT, horizon_b TEXT,"
            " status TEXT NOT NULL DEFAULT 'open', winner TEXT, resolved_by TEXT,"
            " resolved_date TEXT, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL)"
        )
        conn.commit()
        conn.close()

        store = ContradictionStore(str(db))  # 打开时自动 ALTER 迁移
        item = _item("AI算力", "opinion", _claim("国元", "AI算力", 1), _claim("中邮", "AI算力", -1))
        store.upsert(item, "2026-08-10")
        store.save_insight(item["id"], {"id": item["id"], "cause_type": "口径差异"})
        assert store.list_open()[0]["insight"]
