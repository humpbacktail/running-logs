#!/bin/bash

# エラーが起きたら中断する
set -e

echo "🔧 スクリプト開始（$(date)）"
echo "PATH=$PATH"
echo "引数：$1"
echo "カレントディレクトリ：$(pwd)"
echo "upload/$1 の中身："
ls -la "upload/$1" || echo "⚠️ upload/$1 フォルダなし"

echo "🌀 1. GitHubの最新状態を取得（pull --rebase）..."

# ローカルに未コミットの変更があると pull が失敗するので確認
if ! git diff-index --quiet HEAD --; then
  echo "⚠️ ローカルに未コミットの変更があります。先に commit か stash してください。"
  exit 1
fi

# pull --rebase で GitHub 上の変更をローカルに取り込む
git pull --rebase origin main
echo "✅ pull --rebase 完了"

# Step 1: 日付を受け取る（なければ今日の日付）
DATE=${1:-$(date "+%Y-%m-%d")}

# Step 2: 必要なフォルダを作る
mkdir -p "images/$DATE"
mkdir -p "logs"

# Step 3: upload/DATE にあるファイルを images/DATE に移動
if [ -d "upload/$DATE" ]; then
  shopt -s nullglob
  mv upload/$DATE/* images/$DATE/
  rmdir upload/$DATE 2>/dev/null || echo "（info）空でないため upload/$DATE は削除されませんでした"
else
  echo "⚠️ upload/$DATE フォルダが見つかりません。処理を中止します。"
  exit 1
fi

# Step 4: logs/DATE.md を作成（テンプレート読み込み）
TEMPLATE_FILE="logs/template.md.tpl"
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "❌ テンプレートファイルが見つかりません: $TEMPLATE_FILE"
  exit 1
fi

# 画像タグ生成
IMAGES_MD=""
for img in images/$DATE/*; do
  BASENAME=$(basename "$img")
  IMAGES_MD+=$(printf '<img src="/images/%s/%s" width="400" />\n' "$DATE" "$BASENAME")
done

# 環境変数に登録してテンプレートに差し込み
export DATE
export IMAGES="$IMAGES_MD"

/opt/anaconda3/bin/envsubst < "$TEMPLATE_FILE" > logs/$DATE.md

# Step 5: Git操作
git add images/$DATE logs/$DATE.md
git commit -m "Add log and images for $DATE"
git push origin main

echo "✅ $DATE のログをGitHubにアップしました！"
echo "🚀 upload_log.sh 完了！"
