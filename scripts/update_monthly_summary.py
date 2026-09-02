import os
import re
import json
from collections import defaultdict
from datetime import date, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
README_PATH = os.path.join(SCRIPT_DIR, "../README.md")
LOGS_DIR = os.path.join(SCRIPT_DIR, "../logs")
INDEX_PATH = os.path.join(SCRIPT_DIR, "../index.html")
STATS_JSON_PATH = os.path.join(SCRIPT_DIR, "../stats.json")

TIME_RE = re.compile(r"時間:\s*([0-9]{1,2}:[0-5][0-9](?::[0-5][0-9])?)")
DIST_RE = re.compile(r"距離:\s*([0-9]+(?:\.[0-9]+)?)\s*km", re.IGNORECASE)

# 距離カテゴリの定義
DISTANCE_CATEGORIES = [
    {"label": "フルマラソン 🏅", "min": 40.0, "max": 43.0},
    {"label": "ハーフマラソン 🥈", "min": 21.0, "max": 23.0},
    {"label": "10km 🥉",          "min": 9.0,  "max": 11.0},
    {"label": "5km ⭐",            "min": 4.0,  "max": 6.0},
]

def parse_log_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    distance_match = re.search(r"距離\s*[：:]\s*([0-9.]+)\s*km", content, re.IGNORECASE)
    time_hms_match = re.search(r"時間\s*[：:]\s*(\d{1,2}):(\d{2}):(\d{2})", content)
    shoe_match = re.search(r"使用シューズ\s*[：:]\s*(.+)", content)

    print(f"[DEBUG] {os.path.basename(filepath)} -> {time_hms_match.groups() if time_hms_match else '時間見つからず'}")

    distance = float(distance_match.group(1)) if distance_match else 0.0
    shoe = shoe_match.group(1).strip() if shoe_match else "不明"

    if time_hms_match:
        h, m, s = map(int, time_hms_match.groups())
        duration = timedelta(hours=h, minutes=m, seconds=s)
    else:
        duration = timedelta()

    return distance, duration, shoe

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
            distance, time, _ = parse_log_file(os.path.join(LOGS_DIR, filename))
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
    logs_by_month = defaultdict(list)

    for filename in os.listdir(LOGS_DIR):
        if filename.endswith(".md"):
            m = re.match(r"(\d{4})-(\d{2})-\d{2}", filename)
            if m:
                y, mo = m.groups()
                logs_by_month[f"{y}-{mo}"].append(filename)

    blocks = []
    for ym in sorted(logs_by_month.keys(), reverse=True):
        y, mo = ym.split("-")
        mo_i = int(mo)
        mo02 = f"{mo_i:02d}"

        blocks.append("<details>")
        blocks.append(f"<summary>📂 {y}年{mo_i}月</summary>\n")
        blocks.append(f"<!-- RECORD_LIST_{y}_{mo02}_START -->")

        for f in sorted(logs_by_month[ym], reverse=True):
            label = f.replace(".md", "")
            blocks.append(f"- [{label}](logs/{f})")

        blocks.append(f"<!-- RECORD_LIST_{y}_{mo02}_END -->")
        blocks.append("</details>\n")

    return "\n".join(blocks)

def _format_pace(total_sec, total_km):
    if total_km <= 0:
        return "-"
    spk = total_sec / total_km
    m, s = divmod(int(round(spk)), 60)
    return f"{m}'{s:02d}\"/km"

def generate_weekly_summary_markdown(LOGS_DIR: str) -> str:
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

        km, duration, _ = parse_log_file(os.path.join(LOGS_DIR, fname))
        sec = int(duration.total_seconds())

        iy, iw, _ = d.isocalendar()
        key = (iy, iw)
        w = weeks[key]
        w["km"]   += km
        w["sec"]  += sec
        w["count"] += 1
        if km > w["longest_km"]:
            w["longest_km"]   = km
            w["longest_file"] = fname

        wd = d.isoweekday()
        mon = d - timedelta(days=wd - 1)
        sun = mon + timedelta(days=6)
        w["monday"] = mon if w["monday"] is None or mon < w["monday"] else w["monday"]
        w["sunday"] = sun if w["sunday"] is None or sun > w["sunday"] else w["sunday"]

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


def generate_best_records_markdown():
    MEDAL_MAP = {
        "フルマラソン 🏅": ("🏅", "Full Marathon"),
        "ハーフマラソン 🥈": ("🥈", "Half Marathon"),
        "10km 🥉": ("🥉", "10km"),
        "5km ⭐": ("⭐", "5km"),
    }
    bests = {cat["label"]: None for cat in DISTANCE_CATEGORIES}

    for filename in os.listdir(LOGS_DIR):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(LOGS_DIR, filename)
        km, duration, _ = parse_log_file(filepath)
        if km == 0 or duration.total_seconds() == 0:
            continue
        for cat in DISTANCE_CATEGORIES:
            if cat["min"] <= km <= cat["max"]:
                label = cat["label"]
                if bests[label] is None or duration < bests[label]["duration"]:
                    bests[label] = {
                        "duration": duration,
                        "km": km,
                        "filename": filename,
                        "date": filename[:10],
                    }

    lines = []
    for cat in DISTANCE_CATEGORIES:
        label = cat["label"]
        best = bests[label]
        medal, en_label = MEDAL_MAP.get(label, ("", label))
        if best:
            total_sec = int(best["duration"].total_seconds())
            h = total_sec // 3600
            m = (total_sec % 3600) // 60
            s = total_sec % 60
            time_str = f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m}:{s:02d}"
            pace_sec = total_sec / best["km"]
            pm, ps = divmod(int(round(pace_sec)), 60)
            pace_str = f"{pm}\'{ps:02d}\"/km"
            log_name = best["filename"].replace(".md", "")
            log_url = f"/running-logs/logs/{log_name}.html"
            lines.append(
                f'''    <div class="record-card">\n'''
                f'''      <div class="record-cat">{medal} {en_label}</div>\n'''
                f'''      <div class="record-time">{time_str}</div>\n'''
                f'''      <div class="record-meta">{best["km"]:.1f} km · {pace_str}<br><a href="{log_url}">{best["date"]} →</a></div>\n'''
                f'''    </div>'''
            )
        else:
            lines.append(
                f'''    <div class="record-card">\n'''
                f'''      <div class="record-cat">{medal} {en_label}</div>\n'''
                f'''      <div class="record-time">-</div>\n'''
                f'''      <div class="record-meta">記録なし</div>\n'''
                f'''    </div>'''
            )

    return "\n".join(lines)


def generate_recent_logs_markdown(n=5):
    files = sorted(
        [f for f in os.listdir(LOGS_DIR)
         if f.endswith(".md") and f != "index.md"],
        reverse=True
    )[:n]

    lines = []
    for f in files:
        label = f.replace(".md", "")
        km, duration, _ = parse_log_file(os.path.join(LOGS_DIR, f))
        total_sec = int(duration.total_seconds())
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        s = total_sec % 60
        time_str = f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m}:{s:02d}"
        km_str = f"{km:.1f} km" if km > 0 else "-"
        date_str = label[:10]
        log_url = f"/running-logs/logs/{label}.html"
        lines.append(
            f'''    <a class="log-item" href="{log_url}">\n'''
            f'''      <span class="log-date">{date_str}</span>\n'''
            f'''      <span class="log-km">{km_str}</span>\n'''
            f'''      <span class="log-time-val">{time_str}</span>\n'''
            f'''      <span class="log-pace"></span>\n'''
            f'''    </a>'''
        )
    return "\n".join(lines)


# ============================================================
# ★ 新機能: stats.json の生成
# ============================================================

def generate_stats_json():
    """月間・週間・シューズ別の集計データをJSONで出力"""

    monthly = defaultdict(lambda: {"km": 0.0, "sec": 0, "count": 0})
    weekly  = defaultdict(lambda: {"km": 0.0, "sec": 0, "count": 0, "monday": None, "sunday": None})
    shoes   = defaultdict(lambda: {"km": 0.0, "count": 0})
    daily   = defaultdict(lambda: defaultdict(float))  # "YYYY-MM" -> {日(int): km}

    for fname in sorted(os.listdir(LOGS_DIR)):
        if not fname.endswith(".md") or fname == "index.md":
            continue
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", fname)
        if not m:
            continue

        y, mo, dd = map(int, m.groups())
        d = date(y, mo, dd)
        km, duration, shoe = parse_log_file(os.path.join(LOGS_DIR, fname))
        sec = int(duration.total_seconds())

        # 月間
        mkey = f"{y}-{mo:02d}"
        monthly[mkey]["km"]    += km
        monthly[mkey]["sec"]   += sec
        monthly[mkey]["count"] += 1

        # 日別（月内グラフ用）
        daily[mkey][dd] += km

        # 週間
        iy, iw, wd_iso = d.isocalendar()
        wkey = f"{iy}-W{iw:02d}"
        mon = d - timedelta(days=wd_iso - 1)
        sun = mon + timedelta(days=6)
        weekly[wkey]["km"]    += km
        weekly[wkey]["sec"]   += sec
        weekly[wkey]["count"] += 1
        if weekly[wkey]["monday"] is None:
            weekly[wkey]["monday"] = mon.strftime("%Y-%m-%d")
            weekly[wkey]["sunday"] = sun.strftime("%Y-%m-%d")

        # シューズ別
        shoes[shoe]["km"]    += km
        shoes[shoe]["count"] += 1

    def to_pace(sec, km):
        if km <= 0: return "-"
        spk = sec / km
        mn, s = divmod(int(round(spk)), 60)
        return f"{mn}'{s:02d}\"/km"

    # 月間リスト（新しい順）
    monthly_list = []
    for k in sorted(monthly.keys(), reverse=True):
        v = monthly[k]
        km_r = round(v["km"], 1)
        monthly_list.append({
            "month": k,
            "km": km_r,
            "count": v["count"],
            "pace": to_pace(v["sec"], v["km"]),
        })

    # 週間リスト（新しい順、直近26週まで）
    weekly_list = []
    for k in sorted(weekly.keys(), reverse=True)[:26]:
        v = weekly[k]
        km_r = round(v["km"], 1)
        weekly_list.append({
            "week": k,
            "monday": v["monday"],
            "sunday": v["sunday"],
            "km": km_r,
            "count": v["count"],
            "pace": to_pace(v["sec"], v["km"]),
        })

    # シューズ別リスト（距離降順）
    shoe_list = []
    for name, v in sorted(shoes.items(), key=lambda x: x[1]["km"], reverse=True):
        shoe_list.append({
            "shoe": name,
            "km": round(v["km"], 1),
            "count": v["count"],
        })

    # 日別（月内グラフ用・直近3ヶ月分だけ。{"YYYY-MM": [{"day":1,"km":6.1}, ...]}）
    daily_by_month = {}
    for mk in sorted(monthly.keys(), reverse=True)[:3]:
        daily_by_month[mk] = [
            {"day": day, "km": round(v, 1)}
            for day, v in sorted(daily[mk].items())
        ]

    stats = {
        "generated_at": date.today().strftime("%Y-%m-%d"),
        "monthly": monthly_list,
        "weekly": weekly_list,
        "shoes": shoe_list,
        "daily_by_month": daily_by_month,
    }

    with open(STATS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"📊 stats.json を生成しました（月: {len(monthly_list)}件, 週: {len(weekly_list)}件, シューズ: {len(shoe_list)}種）")


# ============================================================

def update_index():
    best_md = generate_best_records_markdown()
    recent_md = generate_recent_logs_markdown(5)

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index = f.read()

    if "<!-- BEST_RECORDS_START -->" in index and "<!-- BEST_RECORDS_END -->" in index:
        index = re.sub(
            r"(<!-- BEST_RECORDS_START -->)(.*?)(<!-- BEST_RECORDS_END -->)",
            f"\\1\n{best_md}\n\\3",
            index, flags=re.DOTALL
        )
    else:
        best_section = f"\n## 🏆 ベスト記録\n\n<!-- BEST_RECORDS_START -->\n{best_md}\n<!-- BEST_RECORDS_END -->\n"
        index += best_section

    if "<!-- RECENT_LOGS_START -->" in index and "<!-- RECENT_LOGS_END -->" in index:
        index = re.sub(
            r"(<!-- RECENT_LOGS_START -->)(.*?)(<!-- RECENT_LOGS_END -->)",
            f"\\1\n{recent_md}\n\\3",
            index, flags=re.DOTALL
        )
    else:
        recent_section = f"\n## 📋 最近のログ\n\n<!-- RECENT_LOGS_START -->\n{recent_md}\n<!-- RECENT_LOGS_END -->\n"
        index += recent_section

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(index)

def update_readme():
    new_summary = generate_summary_markdown()
    new_record_list = generate_record_list_markdown()
    weekly_md = generate_weekly_summary_markdown(LOGS_DIR)

    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    if "<!-- SUMMARY_START -->" in readme and "<!-- SUMMARY_END -->" in readme:
        readme = re.sub(
            r"(<!-- SUMMARY_START -->)(.*?)(<!-- SUMMARY_END -->)",
            f"\\1\n{new_summary}\n\\3",
            readme, flags=re.DOTALL
        )
    else:
        summary_section = f"## 📊 月間サマリー\n\n<!-- SUMMARY_START -->\n{new_summary}\n<!-- SUMMARY_END -->\n\n"
        readme = summary_section + readme

    if "<!-- WEEKLY_SUMMARY_START -->" in readme and "<!-- WEEKLY_SUMMARY_END -->" in readme:
        readme = re.sub(
            r"(<!-- WEEKLY_SUMMARY_START -->)(.*?)(<!-- WEEKLY_SUMMARY_END -->)",
            f"\\1\n{weekly_md}\n\\3",
            readme, flags=re.DOTALL
        )
    else:
        weekly_section = (
            "## 🗓️ 週次サマリー\n\n"
            f"<!-- WEEKLY_SUMMARY_START -->\n{weekly_md}\n<!-- WEEKLY_SUMMARY_END -->\n\n"
        )
        if "<!-- SUMMARY_END -->" in readme:
            readme = re.sub(r"(<!-- SUMMARY_END -->)", r"\1\n\n" + weekly_section, readme, count=1, flags=re.DOTALL)
        else:
            readme = weekly_section + readme

    readme = re.sub(
        r"(<!-- RECORD_LIST_START -->)(.*?)(<!-- RECORD_LIST_END -->)",
        f"\\1\n{new_record_list}\n\\3",
        readme, flags=re.DOTALL
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(readme)

if __name__ == "__main__":
    print("📝 README.md の月間サマリーと記録一覧を更新中...")
    update_readme()
    print("🏆 index.html のベスト記録と最近のログを更新中...")
    update_index()
    print("📊 stats.json を生成中...")
    generate_stats_json()
    print("✅ 完了！")
