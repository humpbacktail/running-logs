#!/bin/bash
set -e

# 日付抽出（upload配下の最初のディレクトリ名を取得）
DATE=$(basename "$(find upload -mindepth 1 -maxdepth 1 -type d | sort | head -n 1)")

# 空チェック
if [ -z "$DATE" ]; then
  echo "❌ upload/ 以下に日付フォルダが見つかりません"
  exit 1
fi

UPLOAD_DIR="upload/${DATE}"
IMAGE_DIR="images/${DATE}"
LOG_FILE="logs/${DATE}.md"
TEMPLATE_FILE="logs/template.md.tpl"

mkdir -p "${IMAGE_DIR}"

# 画像移動とuploadディレクトリの削除
if [ -d "${UPLOAD_DIR}" ] && [ "$(ls -A "${UPLOAD_DIR}")" ]; then
  mv "${UPLOAD_DIR}"/* "${IMAGE_DIR}/"
  echo "✅ 画像の移動が完了しました。"

  # 元のuploadディレクトリを削除
  rm -rf "${UPLOAD_DIR}"
  echo "🗑️ ${UPLOAD_DIR} を削除しました。"
else
  echo "⚠️ ${UPLOAD_DIR} が存在しないか空のため、画像移動をスキップします。"
  if [ -d "${UPLOAD_DIR}" ]; then
    rmdir "${UPLOAD_DIR}" 2>/dev/null || echo "（情報）${UPLOAD_DIR} は空でないため削除されませんでした。"
  fi
fi

# 画像リンク生成
IMG_BLOCK=""
for img in "${IMAGE_DIR}"/*; do
  filename=$(basename "$img")
  IMG_BLOCK+="![${filename}](images/${DATE}/${filename})"$'\n'
done

# テンプレートを読み込み、置換してMarkdown生成
sed -e "s|\${DATE}|${DATE}|g" \
    -e "s|\${IMAGES}|${IMG_BLOCK}|g" \
    "$TEMPLATE_FILE" > "$LOG_FILE"

echo "✅ Markdownログ生成完了: $LOG_FILE"

# Git 操作（add → commit → push）
git add "$LOG_FILE" "$IMAGE_DIR"
git commit -m "Add log for ${DATE}"
git push

echo "🚀 GitHubにプッシュ完了！"
