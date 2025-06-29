#!/bin/bash

set -e

echo "🔧 スクリプト開始（$(date)）"
echo "PATH=$PATH"
echo "引数：$1"
echo "カレントディレクトリ：$(pwd)"
echo "upload/$1 の中身："
ls -la "upload/$1" || echo "⚠️ upload/$1 フォルダなし"

echo "🌀 GitHubの最新状態を確認中..."
if ! git diff-index --quiet HEAD --; then
  echo "⚠️ ローカルに未コミットの変更があります。先に commit か stash してください。"
  exit 1
fi

git pull --rebase origin main
echo "✅ GitHub同期完了"

DATE=${1:-$(date "+%Y-%m-%d")}

mkdir -p "images/$DATE"
mkdir -p "logs"

if [ -d "upload/$DATE" ]; then
  shopt -s nullglob
  mv upload/$DATE/* images/$DATE/
  rmdir upload/$DATE 2>/dev/null || echo "（info）空でないため upload/$DATE は削除されませんでした"
else
  echo "⚠️ upload/$DATE フォルダが見つかりません。処理を中止します。"
  exit 1
fi

TEMPLATE_FILE="logs/template.md.tpl"
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "❌ テンプレートファイルが見つかりません: $TEMPLATE_FILE"
  echo "👉 logs/template.md.tpl を確認してください"
  exit 1
fi

IMAGES_MD=""
for img in images/$DATE/*; do
  BASENAME=$(basename "$img")
  IMAGES_MD+=$(printf '<img src="/images/%s/%s" width="400" />\n' "$DATE" "$BASENAME")
done

# 環境変数に登録してテンプレートに差し込み
export DATE
export IMAGES="$IMAGES_MD"

# すでにログファイルが存在していたら上書きせず終了
if [ -f "logs/$DATE.md" ]; then
  echo "⚠️ logs/$DATE.md は既に存在しています。上書きを避けるため中止します。"
  exit 1
fi

/opt/anaconda3/bin/envsubst < "$TEMPLATE_FILE" > logs/$DATE.md


git add images/$DATE logs/$DATE.md
git commit -m "Add log and images for $DATE"
git push origin main

echo "✅ $DATE のログをGitHubにアップしました！"
echo "🚀 upload_log.sh 完了！"
