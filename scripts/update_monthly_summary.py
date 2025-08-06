import os
import re
from collections import defaultdict
from datetime import timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
README_PATH = os.path.join(SCRIPT_DIR, "../README.md")
LOGS_DIR = os.path.join(SCRIPT_DIR, "../logs")

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
    logs_by_month = defaultdict(list)

    for filename in sorted(os.listdir(LOGS_DIR), reverse=True):
        if filename.endswith(".md"):
            match = re.match(r"(\d{4})-(\d{2})-\d{2}", filename)
            if match:
                year, month = match.groups()
                logs_by_month[f"{year}-{month}"].append(filename)

    details_blocks = []
    for ym, filenames in logs_by_month.items():
        year, month = ym.split("-")
        block = [
            f"<details>",
            f"<summary>📂 {year}年{month}月</summary>\n",
            f"<!-- RECORD_LIST_{year}_{month}_START -->"
        ]
        for f in filenames:
            label = f.replace(".md", "")
            block.append(f"- [{label}](logs/{f})")
        block.append(f"<!-- RECORD_LIST_{year}_{month}_END -->")
        block.append("</details>\n")
        details_blocks.append("\n".join(block))

    return "\n\n".join(details_blocks)

def update_readme():
    new_summary = generate_summary_markdown()
    new_record_list = generate_record_list_markdown()

    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    # マーカーがあれば置換
    if "<!-- SUMMARY_START -->" in readme and "<!-- SUMMARY_END -->" in readme:
        readme = re.sub(
            r"(<!-- SUMMARY_START -->)(.*?)(<!-- SUMMARY_END -->)",
            f"\\1\n{new_summary}\n\\3",
            readme,
            flags=re.DOTALL
        )
    else:
        # マーカーがなければ自動挿入
        summary_section = f"## 📊 月間サマリー\n\n<!-- SUMMARY_START -->\n{new_summary}\n<!-- SUMMARY_END -->\n\n"
        readme = summary_section + readme

    # 記録一覧を差し替え（こちらは従来どおり）
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
