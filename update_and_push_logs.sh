#!/bin/bash
set -e

echo "🚀 ログ更新とGitHubプッシュスクリプト開始（$(date)）"

# --- 1. GitHubの最新状態を確認・同期 ---
echo "🌀 GitHubの最新状態を確認中..."
if ! git diff-index --quiet HEAD --; then
  echo "⚠️ ローカルに未コミットの変更があります。先に commit か stash してください。"
  exit 1
fi

git pull --rebase origin main
echo "✅ GitHub同期完了"

# --- 2. 処理対象の日付フォルダを特定 (logs/ にある最新のMDファイルを対象とする) ---
# ここでは、最新の変更があったログファイルを対象とすることを想定します。
# あるいは、手動入力したMDファイルが一つだけ新しいものとして検出される前提です。
# もし複数のMDファイルが同時に手入力された場合、全てを Git に追加することになります。
LAST_MODIFIED_LOG=$(ls -t logs/*.md 2>/dev/null | grep -v "README.md" | head -1)

if [ -z "$LAST_MODIFIED_LOG" ]; then
    echo "❌ logs/ ディレクトリ内に処理対象のログファイルが見つかりませんでした。処理を中止します。"
    exit 1
fi

DATE=$(basename "${LAST_MODIFIED_LOG%.md}") # logs/2025-07-12.md -> 2025-07-12

LOG_FILE="logs/${DATE}.md"
IMAGE_DIR="images/${DATE}" # 画像ディレクトリは既に存在し、画像も移動済み
README_FILE="README.md"

# --- 3. README.md の記録一覧を更新 ---
echo "📝 README.md の記録一覧を更新中..."

TEMP_README_LINKS=$(mktemp)
# logs/ ディレクトリ内の .md ファイルを日付順にソートして取得
# README.md 自体は除外
find logs -maxdepth 1 -name "*.md" ! -name "README.md" | sort | while read -r log_file_path; do
    log_filename=$(basename "$log_file_path")
    log_date_raw="${log_filename%.md}"

    year=$(echo "$log_date_raw" | cut -d'-' -f1)
    month=$(echo "$log_date_raw" | cut -d'-' -f2)
    day=$(echo "$log_date_raw" | cut -d'-' -f3)
    # macOS の date コマンドは -j オプションが必要
    display_date=$(date -j -f "%Y-%m-%d" "$log_date_raw" "+%Y年%m月%d日") || \
                   date -d "$log_date_raw" "+%Y年%m月%d日" # Linux互換性のため

    echo "- [${display_date}](${log_file_path})" >> "${TEMP_README_LINKS}"
done

TEMP_README_UPDATED=$(mktemp)

awk -v new_links_file="${TEMP_README_LINKS}" '
BEGIN {
    generated_log_links = "";
    while ((getline line < new_links_file) > 0) {
        generated_log_links = generated_log_links line "\n";
    }
    close(new_links_file);
    if (length(generated_log_links) > 0) {
        sub(/\n$/, "", generated_log_links);
    }
    in_log_list_section = 0;
}

/^## 📅 記録一覧（リンク付き）/ {
    print;
    print "";
    print generated_log_links;
    in_log_list_section = 1;
    next;
}

in_log_list_section && /^---$/ {
    print;
    in_log_list_section = 0;
    next;
}

!in_log_list_section {
    print;
}
' "${README_FILE}" > "${TEMP_README_UPDATED}"

mv "${TEMP_README_UPDATED}" "${README_FILE}"
rm "${TEMP_README_LINKS}" "${TEMP_README_UPDATED}" || true

echo "✅ README.md の記録一覧を更新しました。"

# --- 📊 月間サマリーを更新 (Pythonスクリプトを呼び出し) ---
/usr/bin/env python3 scripts/update_monthly_summary.py

# ---

# --- 4. Git 操作（add → commit → push） ---
echo "🚀 GitHubにアップロード中..."

# 新しいログファイル、画像ディレクトリ、そして更新された README.md を追加
git add "$LOG_FILE" "$IMAGE_DIR" "$README_FILE"

if git diff-index --quiet HEAD --; then
  echo "ℹ️ コミット対象の変更がありません。Git操作をスキップします。"
else
  git commit -m "Add log and images for ${DATE} and update README.md"
  git push
  echo "✅ ${DATE} のログと画像をGitHubにプッシュ完了！"
fi

echo "🎉 スクリプト完了！"