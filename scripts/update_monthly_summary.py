import os
import re
from collections import defaultdict

README_PATH = "../README.md"
LOGS_DIR = "../logs"

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
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    new_record_list = generate_record_list_markdown()

    readme = re.sub(
        r"(<!-- RECORD_LIST_START -->)(.*?)(<!-- RECORD_LIST_END -->)",
        f"\\1\n{new_record_list}\n\\3",
        readme,
        flags=re.DOTALL
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(readme)

if __name__ == "__main__":
    print("📝 README.md の記録一覧を月別に更新中...")
    update_readme()
    print("✅ 完了！")
