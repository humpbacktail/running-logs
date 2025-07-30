#!/bin/bash

# Step 1: 日付を受け取る（なければ今日の日付）
DATE=${1:-$(date "+%Y-%m-%d")}

# Step 2: 必要なフォルダを作る
mkdir -p "images/$DATE"
mkdir -p "logs"

# Step 3: upload/DATE にあるファイルを images/DATE に移動
if [ -d "upload/$DATE" ]; then
  mv upload/$DATE/* images/$DATE/
  rmdir upload/$DATE
else
  echo "⚠️ upload/$DATE フォルダが見つかりません。処理を中止します。"
  exit 1
fi

# Step 4: logs/DATE.md を作成
cat <<EOF > logs/$DATE.md
# 🏃‍♂️ $DATE のランログ

- 距離：
- 時間：
- 平均心拍数：
- 時間帯：
- 天候：
- コース：
- 補給：
- 睡眠：
- 今日の目的：
- コメント：

## 📝 コーチコメント：

## 📸 写真一覧
EOF

# Step 5: Markdownに画像を追記
for img in images/$DATE/*; do
  BASENAME=$(basename "$img")
  echo "<img src=\"/images/$DATE/$BASENAME\" width=\"400\" />" >> logs/$DATE.md
done

# Step 6: Git操作（add → commit → push）
git add images/$DATE logs/$DATE.md
git commit -m "Add log and images for $DATE"
git push origin main

echo "✅ $DATE のログをGitHubにアップしました！"
