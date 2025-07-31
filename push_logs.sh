#!/bin/bash
echo "🚀 GitHub にログをプッシュ中..."

# 残っていたらロックファイル削除
[ -f .git/index.lock ] && rm -f .git/index.lock && echo "🧹 index.lock を削除しました"

git add .
git commit -m "ランログ＆README更新"
git push

echo "✅ GitHubへのプッシュ完了！"
