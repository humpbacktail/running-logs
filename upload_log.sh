#!/bin/bash

set -e

# 日付を指定（例：2025-06-30）
export DATE=$(basename "$(find upload -mindepth 1 -maxdepth 1 -type d | head -n 1)")

# パス定義
UPLOAD_DIR="upload/${DATE}"
IMAGE_DIR="images/${DATE}"
LOG_FILE="logs/${DATE}.md"
TEMPLATE_FILE="logs/template.md.tpl"

# フォルダがなければ作成
mkdir -p "${IMAGE_DIR}"

# アップロード画像を images/ に移動
mv "${UPLOAD_DIR}"/* "${IMAGE_DIR}/"

# 画像のMarkdownリンク生成
IMAGES_BLOCK=""
for img in "${IMAGE_DIR}"/*; do
  filename=$(basename "${img}")
  IMAGES_BLOCK+="![${filename}](images/${DATE}/${filename})"$'\n\n'
done

# テンプレートから変数置換して .md 作成
sed -e "s|\${DATE}|${DATE}|g" -e "s|\${IMAGES}|${IMAGES_BLOCK}|g" "${TEMPLATE_FILE}" > "${LOG_FILE}"

echo "✅ ログファイル生成完了: ${LOG_FILE}"
