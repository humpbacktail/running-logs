import os
import re
import json
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
README_PATH = os.path.join(SCRIPT_DIR, "../README.md")
LOGS_DIR = os.path.join(SCRIPT_DIR, "../logs")
INDEX_PATH = os.path.join(SCRIPT_DIR, "../index.html")
STATS_JSON_PATH = os.path.join(SCRIPT_DIR, "../stats.json")
PROFILE_JSON_PATH = os.path.join(SCRIPT_DIR, "../profile.json")

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


    distance = float(distance_match.group(1)) if distance_match else 0.0
    shoe = shoe_match.group(1).strip() if shoe_match else "不明"

    if time_hms_match:
        h, m, s = map(int, time_hms_match.groups())
        duration = timedelta(hours=h, minutes=m, seconds=s)
    else:
        duration = timedelta()

    return distance, duration, shoe

def format_pace(total_sec, total_km):
    """平均ペース（秒/km を四捨五入）。README・stats.json 共通で使う。km は丸める前の値を渡すこと。"""
    total_km = float(total_km)
    if total_km <= 0 or total_sec <= 0:
        return "-"
    m, s = divmod(int(round(total_sec / total_km)), 60)
    return f"{m}'{s:02d}\"/km"


def round_km(km):
    """表示用に小数第1位へ四捨五入（内部の合計は Decimal のまま持つ）"""
    return float(Decimal(km).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def collect_runs(logs_dir=None):
    """集計に使う「走った記録」を日付順に返す。
    距離が入っていないログ（例：2026-09-30-01＝睡眠画面だけ）は表示一覧には残すが、走行実績には含めない。"""
    logs_dir = logs_dir or LOGS_DIR
    runs = []
    for fname in sorted(os.listdir(logs_dir)):
        if not fname.endswith(".md") or fname == "index.md":
            continue
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", fname)
        if not m:
            continue
        km, duration, shoe = parse_log_file(os.path.join(logs_dir, fname))
        if km <= 0:
            continue
        runs.append({
            "fname": fname,
            "date": date(*map(int, m.groups())),
            "km": Decimal(str(km)),  # 加算順で丸めがぶれないよう Decimal で合計する
            "sec": int(duration.total_seconds()),
            "shoe": shoe,
        })
    return runs


def aggregate_runs(runs):
    """月・週・シューズ・日別の合計。README と stats.json は必ずこの結果から作る（数値の食い違い防止）。"""
    monthly = defaultdict(lambda: {"km": Decimal(0), "sec": 0, "count": 0})
    weekly = defaultdict(lambda: {"km": Decimal(0), "sec": 0, "count": 0,
                                  "monday": None, "sunday": None,
                                  "longest_km": Decimal(0), "longest_file": None})
    shoes = defaultdict(lambda: {"km": Decimal(0), "count": 0})
    daily = defaultdict(lambda: defaultdict(Decimal))  # "YYYY-MM" -> {日(int): km}

    for r in runs:
        d = r["date"]
        mkey = f"{d.year}-{d.month:02d}"
        mo = monthly[mkey]
        mo["km"] += r["km"]; mo["sec"] += r["sec"]; mo["count"] += 1
        daily[mkey][d.day] += r["km"]

        iy, iw, wd = d.isocalendar()
        w = weekly[f"{iy}-W{iw:02d}"]
        w["km"] += r["km"]; w["sec"] += r["sec"]; w["count"] += 1
        if w["monday"] is None:
            w["monday"] = d - timedelta(days=wd - 1)
            w["sunday"] = w["monday"] + timedelta(days=6)
        if r["km"] > w["longest_km"]:
            w["longest_km"], w["longest_file"] = r["km"], r["fname"]

        shoes[r["shoe"]]["km"] += r["km"]
        shoes[r["shoe"]]["count"] += 1

    return {"monthly": monthly, "weekly": weekly, "shoes": shoes, "daily": daily}


def generate_summary_markdown(agg=None):
    agg = agg or aggregate_runs(collect_runs())
    lines = []
    for mkey in sorted(agg["monthly"].keys(), reverse=True):
        v = agg["monthly"][mkey]
        y, mo = mkey.split("-")
        hours, minutes = v["sec"] // 3600, (v["sec"] % 3600) // 60
        lines.append(f"- **{y}年{mo}月**: 距離 **{round_km(v['km'])} km**, 時間 **{hours}時間{minutes}分**, 平均ペース **{format_pace(v['sec'], v['km'])}**")
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

def generate_weekly_summary_markdown(agg=None) -> str:
    agg = agg or aggregate_runs(collect_runs())
    lines = []
    for wkey, w in sorted(agg["weekly"].items(), reverse=True):
        mon = w["monday"].strftime("%m/%d")
        sun = w["sunday"].strftime("%m/%d")
        lines.append("<details>")
        lines.append(
            f"<summary>📆 {wkey}（{mon}–{sun}） — {round_km(w['km'])} km / {w['count']}回 / 平均 {format_pace(w['sec'], w['km'])}</summary>\n"
        )
        if w["longest_file"]:
            label = w["longest_file"].replace(".md", "")
            lines.append(f"- 最長: {round_km(w['longest_km'])} km — [{label}](logs/{w['longest_file']})")
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

def generate_stats_json(agg=None):
    """月間・週間・シューズ別の集計データをJSONで出力"""
    agg = agg or aggregate_runs(collect_runs())
    monthly, weekly, shoes, daily = agg["monthly"], agg["weekly"], agg["shoes"], agg["daily"]

    # 月間リスト（新しい順）
    monthly_list = [
        {"month": k, "km": round_km(v["km"]), "count": v["count"], "pace": format_pace(v["sec"], v["km"])}
        for k, v in sorted(monthly.items(), reverse=True)
    ]

    # 週間リスト（新しい順、直近26週まで）
    weekly_list = [
        {"week": k, "monday": v["monday"].strftime("%Y-%m-%d"), "sunday": v["sunday"].strftime("%Y-%m-%d"),
         "km": round_km(v["km"]), "count": v["count"], "pace": format_pace(v["sec"], v["km"])}
        for k, v in sorted(weekly.items(), reverse=True)[:26]
    ]

    # シューズ別リスト（距離降順）
    # 通算距離 = ログ開始前（NIKEアプリ時代）の距離 profile.json shoe_pre_log_km + ログの距離。
    # 本数はログ分しか分からないので、km/count はログ分のまま触らない（total_km は別キー）。
    pre_log = {}
    try:
        with open(PROFILE_JSON_PATH, encoding="utf-8") as f:
            pre_log = json.load(f).get("shoe_pre_log_km", {}) or {}
    except (OSError, ValueError) as e:
        print(f"⚠️ profile.json の shoe_pre_log_km を読めませんでした: {e}")

    shoe_list = []
    for name, v in sorted(shoes.items(), key=lambda x: x[1]["km"], reverse=True):
        item = {
            "shoe": name,
            "km": round_km(v["km"]),
            "count": v["count"],
        }
        if name != "不明":  # 新しいシューズ（下駄なし）は通算＝ログ距離
            item["total_km"] = round_km(Decimal(str(pre_log.get(name, 0))) + v["km"])
        shoe_list.append(item)

    # 日別（月内グラフ用・直近3ヶ月分だけ。{"YYYY-MM": [{"day":1,"km":6.1}, ...]}）
    daily_by_month = {}
    for mk in sorted(monthly.keys(), reverse=True)[:3]:
        daily_by_month[mk] = [
            {"day": day, "km": round_km(v)}
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

def update_readme(agg=None):
    agg = agg or aggregate_runs(collect_runs())
    new_summary = generate_summary_markdown(agg)
    new_record_list = generate_record_list_markdown()
    weekly_md = generate_weekly_summary_markdown(agg)

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
    agg = aggregate_runs(collect_runs())  # README と stats.json は同じ集計結果を使う
    update_readme(agg)
    print("🏆 index.html のベスト記録と最近のログを更新中...")
    update_index()
    print("📊 stats.json を生成中...")
    generate_stats_json(agg)
    print("✅ 完了！")
