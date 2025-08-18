import os
import re
from collections import defaultdict
from datetime import date, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
README_PATH = os.path.join(SCRIPT_DIR, "../README.md")
LOGS_DIR = os.path.join(SCRIPT_DIR, "../logs")
TIME_RE = re.compile(r"時間:\s*([0-9]{1,2}:[0-5][0-9](?::[0-5][0-9])?)")
DIST_RE = re.compile(r"距離:\s*([0-9]+(?:\.[0-9]+)?)\s*km", re.IGNORECASE)

def parse_log_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    distance_match = re.search(r"距離\s*[：:]\s*([0-9.]+)\s*km", content)
    time_hms_match = re.search(r"時間\s*[：:]\s*(\d{1,2}):(\d{2}):(\d{2})", content)

    print(f"[DEBUG] {os.path.basename(filepath)} -> {time_hms_match.groups() if time_hms_match else '時間見つからず'}")

    distance = float(distance_match.group(1)) if distance_match else 0.0

    if time_hms_match:
        h, m, s = map(int, time_hms_match.groups())
        duration = timedelta(hours=h, minutes=m, seconds=s)
    else:
        duration = timedelta()

    return distance, duration

def format_pace(total_time, total_km):
    if total_km == 0 or total_time.total_seconds() == 0:
        return "--"
    seconds_per_km = total_time.total_seconds() / total_km
    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)
    return f"{minutes}'{seconds:02}/km"

def generate_summary_markdown():
    totals = defaultdict(lambda: {"distance": 0.0, "time": timedelta()})

    for filename in os.listdir(LOGS_DIR):
        if filename.endswith(".md"):
            match = re.match(r"(\d{4})-(\d{2})-\d{2}", filename)
            if not match:
                continue
            year, month = match.group(1), match.group(2)
            key = f"{year}年{month}月"
            distance, time = parse_log_file(os.path.join(LOGS_DIR, filename))
            totals[key]["distance"] += distance
            totals[key]["time"] += time

    lines = []
    for ym in sorted(totals.keys(), reverse=True):
        total_km = round(totals[ym]["distance"], 1)
        total_time = totals[ym]["time"]
        pace = format_pace(total_time, total_km)
        hours = int(total_time.total_seconds() // 3600)
        minutes = int((total_time.total_seconds() % 3600) // 60)
        lines.append(f"- **{ym}**: 距離 **{total_km} km**, 時間 **{hours}時間{minutes}分**, 平均ペース **{pace}**")

    return "\n".join(lines)


def generate_record_list_markdown():
    from collections import defaultdict
    import os, re

    logs_by_month = defaultdict(list)

    # 仕分け（既存のままでOK）
    for filename in os.listdir(LOGS_DIR):
        if filename.endswith(".md"):
            m = re.match(r"(\d{4})-(\d{2})-\d{2}", filename)
            if m:
                y, mo = m.groups()
                logs_by_month[f"{y}-{mo}"].append(filename)

    # 出力（新しい順）
    blocks = []
    for ym in sorted(logs_by_month.keys(), reverse=True):
        y, mo = ym.split("-")
        mo_i = int(mo)           # 表示用（8月の「8」）
        mo02 = f"{mo_i:02d}"     # マーカー用（08などゼロ埋め）

        blocks.append("<details>")
        blocks.append(f"<summary>📂 {y}年{mo_i}月</summary>\n")

        # ★ ここに月ごとの START マーカー
        blocks.append(f"<!-- RECORD_LIST_{y}_{mo02}_START -->")

        # 月内も新しい順で並べる
        for f in sorted(logs_by_month[ym], reverse=True):
            label = f.replace(".md", "")
            blocks.append(f"- [{label}](logs/{f})")

        # ★ ここに月ごとの END マーカー
        blocks.append(f"<!-- RECORD_LIST_{y}_{mo02}_END -->")
        blocks.append("</details>\n")

    return "\n".join(blocks)
    
def _parse_time_to_seconds(s):
    parts = [int(x) for x in s.split(":")]
    if   len(parts) == 3: h,m,sec = parts
    elif len(parts) == 2: h, m, sec = 0, parts[0], parts[1]
    else: return 0
    return h*3600 + m*60 + sec

def _format_pace(sec_per_km):
    if sec_per_km <= 0: return "-"
    m, s = divmod(int(round(sec_per_km)), 60)
    return f"{m}'{s:02d}\"/km"

def _monday_sunday_range(d: date):
    # ISO: Monday=1 ... Sunday=7
    wd = d.isoweekday()
    monday = d - timedelta(days=wd-1)
    sunday = monday + timedelta(days=6)
    return monday, sunday

def generate_weekly_summary_markdown(LOGS_DIR: str) -> str:
    # 週キー: (ISO年, 週番号)
    weeks = defaultdict(lambda: {
        "km": 0.0, "sec": 0, "count": 0,
        "longest_km": 0.0, "longest_file": None,
        "monday": None, "sunday": None
    })

    for fname in os.listdir(LOGS_DIR):
        if not fname.endswith(".md"):
            continue
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", fname)
        if not m:
            continue

        y, mo, dd = map(int, m.groups())
        d = date(y, mo, dd)

        # ★ 月次と同じパーサで距離・時間を取得（表記揺れを吸収）
        km, duration = parse_log_file(os.path.join(LOGS_DIR, fname))
        sec = int(duration.total_seconds())

        iy, iw, _ = d.isocalendar()   # (ISO年, 週番号, 曜日)
        key = (iy, iw)
        w = weeks[key]
        w["km"]   += km
        w["sec"]  += sec
        w["count"] += 1
        if km > w["longest_km"]:
            w["longest_km"]   = km
            w["longest_file"] = fname

        # 週の範囲（月〜日）
        wd = d.isoweekday()          # Mon=1..Sun=7
        mon = d - timedelta(days=wd - 1)
        sun = mon + timedelta(days=6)
        w["monday"] = mon if w["monday"] is None or mon < w["monday"] else w["monday"]
        w["sunday"] = sun if w["sunday"] is None or sun > w["sunday"] else w["sunday"]

    def _format_pace(total_sec, total_km):
        if total_km <= 0:
            return "-"
        spk = total_sec / total_km
        m, s = divmod(int(round(spk)), 60)
        return f"{m}'{s:02d}\"/km"

    lines = []
    for (iy, iw), w in sorted(weeks.items(), key=lambda kv: kv[0], reverse=True):
        km = round(w["km"], 1)
        pace = _format_pace(w["sec"], w["km"])
        mon = w["monday"].strftime("%m/%d") if w["monday"] else "??/??"
        sun = w["sunday"].strftime("%m/%d") if w["sunday"] else "??/??"

        lines.append("<details>")
        lines.append(
            f"<summary>📆 {iy}-W{iw:02d}（{mon}–{sun}） — {km} km / {w['count']}回 / 平均 {pace}</summary>\n"
        )
        if w["longest_file"]:
            label = w["longest_file"].replace(".md", "")
            lines.append(f"- 最長: {w['longest_km']:.1f} km — [{label}](logs/{w['longest_file']})")
        lines.append("</details>\n")

    return "\n".join(lines)


def update_readme():
    new_summary = generate_summary_markdown()
    new_record_list = generate_record_list_markdown()
    weekly_md = generate_weekly_summary_markdown(LOGS_DIR)  # ★週次を生成

    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    # 1) 月間サマリー（既存ロジック）
    if "<!-- SUMMARY_START -->" in readme and "<!-- SUMMARY_END -->" in readme:
        readme = re.sub(
            r"(<!-- SUMMARY_START -->)(.*?)(<!-- SUMMARY_END -->)",
            f"\\1\n{new_summary}\n\\3",
            readme,
            flags=re.DOTALL
        )
    else:
        summary_section = f"## 📊 月間サマリー\n\n<!-- SUMMARY_START -->\n{new_summary}\n<!-- SUMMARY_END -->\n\n"
        readme = summary_section + readme

    # 2) 週次サマリー（★ここを追加）
    if "<!-- WEEKLY_SUMMARY_START -->" in readme and "<!-- WEEKLY_SUMMARY_END -->" in readme:
        readme = re.sub(
            r"(<!-- WEEKLY_SUMMARY_START -->)(.*?)(<!-- WEEKLY_SUMMARY_END -->)",
            f"\\1\n{weekly_md}\n\\3",
            readme,
            flags=re.DOTALL
        )
    else:
        weekly_section = (
            "## 🗓️ 週次サマリー\n\n"
            f"<!-- WEEKLY_SUMMARY_START -->\n{weekly_md}\n<!-- WEEKLY_SUMMARY_END -->\n\n"
        )
        # 月間サマリーの直後に入れる（無ければ先頭に追加）
        if "<!-- SUMMARY_END -->" in readme:
            readme = re.sub(r"(<!-- SUMMARY_END -->)", r"\1\n\n" + weekly_section, readme, count=1, flags=re.DOTALL)
        else:
            readme = weekly_section + readme

    # 3) 記録一覧（既存ロジック）
    readme = re.sub(
        r"(<!-- RECORD_LIST_START -->)(.*?)(<!-- RECORD_LIST_END -->)",
        f"\\1\n{new_record_list}\n\\3",
        readme,
        flags=re.DOTALL
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(readme)

if __name__ == "__main__":
    print("📝 README.md の月間サマリーと記録一覧を更新中...")
    update_readme()
    print("✅ 完了！")
