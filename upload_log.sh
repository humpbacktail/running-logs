#!/bin/bash
set -e

# 日付抽出
export DATE=$(basename "$(find upload -mindepth 1 -maxdepth 1 -type d | head -n 1)")

UPLOAD_DIR="upload/${DATE}"
IMAGE_DIR="images/${DATE}"
LOG_FILE="logs/${DATE}.md"
TEMPLATE_FILE="logs/template.md.tpl"

mkdir -p "${IMAGE_DIR}"

# 画像移動
if [ -d "${UPLOAD_DIR}" ] && [ "$(ls -A "${UPLOAD_DIR}")" ]; then
  mv "${UPLOAD_DIR}"/* "${IMAGE_DIR}/"
else
  echo "⚠️ ${UPLOAD_DIR} が存在しないか空のため、画像移動をスキップします"
fi

# 画像リンク生成
IMG_BLOCK=""
for img in "${IMAGE_DIR}"/*; do
  filename=$(basename "$img")
  IMG_BLOCK+=$'\n'"![${filename}](images/${DATE}/${filename})"$'\n'
done

# テンプレートを読み込み、変数を置換
sed -e "s|\${DATE}|${DATE}|g" \
    -e "s|\${IMAGES}|${IMG_BLOCK}|g" \
    "$TEMPLATE_FILE" > "$LOG_FILE"

echo "✅ 完了！生成されたファイル: $LOG_FILE"
