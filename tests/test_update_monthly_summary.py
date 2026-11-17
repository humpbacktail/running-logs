"""scripts/update_monthly_summary.py の回帰テスト（python3 -m unittest discover -s tests）。
本物の logs/ や README.md には触らず、一時フォルダに小さなログを作って確かめる。"""
import json
import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import update_monthly_summary as ums  # noqa: E402


def log(km, time, shoe="テストシューズ"):
    return f"---\ntitle: x\n---\n- 距離：{km}\n- 時間：{time}\n- 使用シューズ：{shoe}\n"


README = """# running-logs

## 📊 月間サマリー

<!-- SUMMARY_START -->
old
<!-- SUMMARY_END -->

## 🗓️ 週次サマリー

<!-- WEEKLY_SUMMARY_START -->
old
<!-- WEEKLY_SUMMARY_END -->

## 記録一覧

<!-- RECORD_LIST_START -->
old
<!-- RECORD_LIST_END -->

フッター（マーカーの外は書き換えない）
"""

INDEX = "<html><!-- BEST_RECORDS_START --><!-- BEST_RECORDS_END --><!-- RECENT_LOGS_START --><!-- RECENT_LOGS_END --></html>"


class StatsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.logs = os.path.join(d, "logs")
        os.mkdir(self.logs)
        files = {
            # 浮動小数点で足し順により 0.1 ずれやすい値を混ぜる
            "2026-08-01-01.md": log("10.05km", "1:00:30"),
            "2026-08-02-01.md": log("10.1km", "0:59:59"),
            "2026-08-03-01.md": log("0.15km", "0:01:00", "別シューズ"),
            "2026-08-04-01.md": log("7.25km", "0:45:01"),
            # 距離・時間が空欄（睡眠画面だけ等）→ 一覧には残るが回数に入れない
            "2026-08-05-01.md": "---\ntitle: x\n---\n- 距離：\n- 時間：\n- 使用シューズ：テストシューズ\n",
            "index.md": "index",
        }
        for name, body in files.items():
            with open(os.path.join(self.logs, name), "w", encoding="utf-8") as f:
                f.write(body)
        self.paths = {
            "LOGS_DIR": self.logs,
            "README_PATH": os.path.join(d, "README.md"),
            "INDEX_PATH": os.path.join(d, "index.html"),
            "STATS_JSON_PATH": os.path.join(d, "stats.json"),
            "PROFILE_JSON_PATH": os.path.join(d, "profile.json"),
        }
        with open(self.paths["README_PATH"], "w", encoding="utf-8") as f:
            f.write(README)
        with open(self.paths["INDEX_PATH"], "w", encoding="utf-8") as f:
            f.write(INDEX)
        with open(self.paths["PROFILE_JSON_PATH"], "w", encoding="utf-8") as f:
            json.dump({"shoe_pre_log_km": {"テストシューズ": 353.5}}, f, ensure_ascii=False)
        self.saved = {k: getattr(ums, k) for k in self.paths}
        for k, v in self.paths.items():
            setattr(ums, k, v)

    def tearDown(self):
        for k, v in self.saved.items():
            setattr(ums, k, v)
        self.tmp.cleanup()

    def run_all(self):
        agg = ums.aggregate_runs(ums.collect_runs())
        ums.update_readme(agg)
        ums.update_index()
        ums.generate_stats_json(agg)
        with open(self.paths["README_PATH"], encoding="utf-8") as f:
            readme = f.read()
        with open(self.paths["STATS_JSON_PATH"], encoding="utf-8") as f:
            stats = json.load(f)
        return readme, stats

    def test_empty_log_not_counted_but_valid_logs_are(self):
        _, stats = self.run_all()
        self.assertEqual(stats["monthly"][0]["count"], 4)
        self.assertEqual(stats["weekly"][0]["count"] + stats["weekly"][1]["count"], 4)
        shoes = {s["shoe"]: s for s in stats["shoes"]}
        self.assertEqual(shoes["テストシューズ"]["count"], 3)
        self.assertEqual(shoes["別シューズ"]["count"], 1)
        self.assertNotIn("不明", shoes)

    def test_empty_log_still_listed_in_readme(self):
        readme, _ = self.run_all()
        self.assertIn("[2026-08-05-01](logs/2026-08-05-01.md)", readme)

    def test_readme_and_stats_month_agree(self):
        readme, stats = self.run_all()
        m = stats["monthly"][0]
        line = re.search(r"2026年08月\*\*: 距離 \*\*([0-9.]+) km.*平均ペース \*\*([^*]+)\*\*", readme)
        self.assertEqual(float(line.group(1)), m["km"])
        self.assertEqual(line.group(2), m["pace"])
        self.assertEqual(m["km"], 27.6)  # 10.05+10.1+0.15+7.25 = 27.55 → 27.6（四捨五入）

    def test_pace_uses_unrounded_distance(self):
        # 27.55km / 2:46:30(9990秒) = 362.6秒/km → 6'03"。丸めた27.6kmで割ると 6'02" になってしまう
        _, stats = self.run_all()
        self.assertEqual(stats["monthly"][0]["pace"], "6'03\"/km")

    def test_shoe_total_km_keeps_pre_log(self):
        _, stats = self.run_all()
        shoes = {s["shoe"]: s for s in stats["shoes"]}
        self.assertEqual(shoes["テストシューズ"]["km"], 27.4)
        self.assertEqual(shoes["テストシューズ"]["total_km"], 380.9)

    def test_idempotent(self):
        first = self.run_all()
        second = self.run_all()
        self.assertEqual(first, second)

    def test_readme_markers_and_no_control_chars(self):
        readme, _ = self.run_all()
        for mk in ["SUMMARY", "WEEKLY_SUMMARY", "RECORD_LIST"]:
            self.assertEqual(readme.count(f"<!-- {mk}_START -->"), 1)
            self.assertEqual(readme.count(f"<!-- {mk}_END -->"), 1)
        self.assertNotIn("old", readme)
        self.assertIn("フッター（マーカーの外は書き換えない）", readme)
        self.assertIsNone(re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", readme))


if __name__ == "__main__":
    unittest.main()
