#!/bin/bash
set -e

echo "🚀 ログ更新とGitHubプッシュスクリプト開始（$(date)）"

# --- 1. 処理対象のMDファイルを特定 ---
LAST_MODIFIED_LOG=$(ls -t logs/*.md 2>/dev/null | grep -v "README.md" | head -1)

if [ -z "$LAST_MODIFIED_LOG" ]; then
    echo "❌ logs/ ディレクトリ内に処理対象のログファイルが見つかりませんでした。処理を中止します。"
    exit 1
fi

FULL_IDENTIFIER=$(basename "${LAST_MODIFIED_LOG%.md}")
BASE_DATE=$(echo "$FULL_IDENTIFIER" | cut -d'-' -f1-3)

LOG_FILE="logs/${FULL_IDENTIFIER}.md"
IMAGE_DIR="images/${FULL_IDENTIFIER}"
README_FILE="README.md"

if [[ "$OSTYPE" == "darwin"* ]]; then # macOSの場合
  DISPLAY_DATE=$(date -j -f "%Y-%m-%d" "$BASE_DATE" "+%Y年%m月%d日")
else # Linuxの場合
  DISPLAY_DATE=$(date -d "$BASE_DATE" "+%Y年%m月%d日")
fi

# --- 1.5 新規ファイルをステージング ---
echo "🌀 新規ログファイルと画像ディレクトリをステージング中..."
git add "$LOG_FILE" "$IMAGE_DIR" || true
echo "✅ 新規ファイルのステージング完了"

# --- 2. GitHubの最新状態を確認・同期 ---
echo "🌀 GitHub同期準備中..."

# ローカルに未コミットの変更（ステージング済み含む）があるかを確認
# git stash save -u はUntrackedファイルも一時的に退避させる
if ! git diff-index --quiet HEAD -- || ! git diff --quiet; then # ステージング済みまたは未ステージングの変更があるか
    echo "⚠️ ローカルにコミットされていない変更があります。一時的に退避します (git stash)。"
    git stash save --include-untracked "Stash before pull by update_and_push_logs.sh"
    STASH_APPLIED=true # stashが適用されたことを記録
else
    STASH_APPLIED=false
fi

git pull --rebase origin main
echo "✅ GitHub同期完了"

# もしstashしていたら元に戻す
if [ "$STASH_APPLIED" = true ]; then
    echo "🌀 退避した変更を戻しています (git stash pop)..."
    git stash pop
    # popで競合が発生した場合のエラーハンドリングも必要だが、ここではシンプルに続行
fi

# --- 3. README.md の記録一覧と月間サマリーを更新 (Pythonスクリプトを呼び出し) ---
/usr/bin/env python3 scripts/update_monthly_summary.py

# --- 4. Git 操作（add → commit → push） ---
echo "🚀 GitHubにアップロード中..."

# 更新された README.md をステージング
git add "$README_FILE"

# コミット対象の変更があるか最終確認
if git diff-index --quiet HEAD --; then
  echo "ℹ️ コミット対象の変更がありません。Git操作をスキップします。"
else
  git commit -m "Add log and images for ${DISPLAY_DATE} (${FULL_IDENTIFIER}) and update README.md"
  git push
  echo "✅ ${DISPLAY_DATE} (${FULL_IDENTIFIER}) のログと画像をGitHubにプッシュ完了！"
fi

echo "🎉 スクリプト完了！"