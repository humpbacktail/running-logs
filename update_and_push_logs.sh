#!/bin/bash
set -e

echo "🚀 ログ更新とGitHubプッシュスクリプト開始（$(date)）"

# --- 1. 処理対象のMDファイルを特定 ---
# logs/ にある最新のMDファイルを対象とする (今回のコミット対象を特定するために使用)
LAST_MODIFIED_LOG=$(ls -t logs/*.md 2>/dev/null | grep -v "README.md" | head -1)

if [ -z "$LAST_MODIFIED_LOG" ]; then
    echo "❌ logs/ ディレクトリ内に処理対象のログファイルが見つかりませんでした。処理を中止します。"
    exit 1
fi

DATE=$(basename "${LAST_MODIFIED_LOG%.md}") # 例: 2025-07-15

LOG_FILE="logs/${DATE}.md"
IMAGE_DIR="images/${DATE}" # 画像ディレクトリは既に存在し、画像も移動済み
README_FILE="README.md"

# --- 2. GitHubの最新状態を確認・同期 ---
echo "🌀 GitHubの最新状態を確認中..."
# ここで、未ステージングの変更がないかのみをチェックする
# （新しいログファイルはまだステージングされていないので、このチェックには引っかからない）
if ! git diff --quiet; then
  echo "⚠️ ローカルに未ステージングの変更があります。先に commit か stash してください。"
  exit 1
fi

# Git pull --rebase は、ステージングエリアがクリーンな状態で実行する必要がある
git pull --rebase origin main
echo "✅ GitHub同期完了"

# --- 2.5 新規ファイルをステージング (Git同期後) ---
# create_log_entry.sh で作成された新しいファイルやディレクトリをステージングする
echo "🌀 新規ログファイルと画像ディレクトリをステージング中..."
git add "$LOG_FILE" "$IMAGE_DIR" || true # 新規ファイルが存在しない場合もエラーにならないように || true を追加
echo "✅ 新規ファイルのステージング完了"


# --- 3. README.md の記録一覧と月間サマリーを更新 (Pythonスクリプトを呼び出し) ---
/usr/bin/env python3 scripts/update_monthly_summary.py

# ---

# --- 4. Git 操作（add → commit → push） ---
echo "🚀 GitHubにアップロード中..."

# 新しいログファイル、画像ディレクトリ、そして更新された README.md を最終的に追加/ステージング
# ここで再度 add するのは、Pythonスクリプトが README.md を変更する可能性があるため
git add "$LOG_FILE" "$IMAGE_DIR" "$README_FILE"

if git diff-index --quiet HEAD --; then
  echo "ℹ️ コミット対象の変更がありません。Git操作をスキップします。"
else
  git commit -m "Add log and images for ${DATE} and update README.md"
  git push
  echo "✅ ${DATE} のログと画像をGitHubにプッシュ完了！"
fi

echo "🎉 スクリプト完了！"