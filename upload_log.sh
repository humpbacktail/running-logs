#!/bin/bash

# エラーが起きたら中断する
set -e

echo "🌀 1. GitHubの最新状態を取得（pull）..."

# ローカルに未コミットの変更があると pull が失敗するので確認
if ! git diff-index --quiet HEAD --; then
  echo "⚠️ ローカルに未コミットの変更があります。先に commit か stash してください。"
  exit 1
fi

# pull で GitHub 上の変更をローカルに取り込む
git pull origin main

echo "✅ pull 完了"

# Step 1: 日付を受け取る（なければ今日の日付）
DATE=${1:-$(date "+%Y-%m-%d")}

# Step 2: 必要なフォルダを作る
mkdir -p "images/$DATE"
mkdir -p "logs"

# Step 3: upload/DATE にあるファイルを images/DATE に移動
if [ -d "upload/$DATE" ]; then
  shopt -s nullglob  # 空ディレクトリでもエラーにならないようにする
  mv upload/$DATE/* images/$DATE/
  rmdir upload/$DATE 2>/dev/null || echo "（info）空でないため upload/$DATE は削除されませんでした"
else
  echo "⚠️ upload/$DATE フォルダが見つかりません。処理を中止します。"
  exit 1
fi

# Step 4: logs/DATE.md を作成
# テンプレート読み込みによる .md 作成
TEMPLATE_FILE="logs/template.md.tpl"
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "❌ テンプレートファイルが見つかりません: $TEMPLATE_FILE"
  exit 1
fi

# 画像タグ生成
IMAGES_MD=""
for img in images/$DATE/*; do
  BASENAME=$(basename "$img")
  IMAGES_MD+="<img src=\"/images/$DATE/$BASENAME\" width=\"400\" />"$'\n'
done

# テンプレートを使ってログファイルを作成
sed -e "s/{{DATE}}/$DATE/g" -e "s|{{IMAGES}}|$IMAGES_MD|g" "$TEMPLATE_FILE" > logs/$DATE.md



# Step 5: Git操作（add → commit → push）
git add images/$DATE logs/$DATE.md
git commit -m "Add log and images for $DATE"
git push origin main

echo "✅ $DATE のログをGitHubにアップしました！"
echo "🚀 upload_log.sh 完了！"


