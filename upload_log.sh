#!/bin/bash
set -e

# 日付指定（upload/ のサブディレクトリ名を自動抽出）
export DATE=$(basename "$(find upload -mindepth 1 -maxdepth 1 -type d | head -n 1)")

# パス定義
UPLOAD_DIR="upload/${DATE}"
IMAGE_DIR="images/${DATE}"
LOG_FILE="logs/${DATE}.md"
TEMPLATE_FILE="logs/template.md.tpl"

# フォルダ作成
mkdir -p "${IMAGE_DIR}"

# アップロード画像を images/ に移動（存在チェック付き）
if [ -d "${UPLOAD_DIR}" ] && [ "$(ls -A "${UPLOAD_DIR}")" ]; then
  mv "${UPLOAD_DIR}"/* "${IMAGE_DIR}/"
else
  echo "⚠️ ${UPLOAD_DIR} が存在しないか空のため、画像移動をスキップします"
fi

# Markdown画像リンク作成
IMAGES_BLOCK=""
for img in "${IMAGE_DIR}"/*; do
  filename=$(basename "${img}")
  IMAGES_BLOCK+="![${filename}](images/${DATE}/${filename})"$'\n\n'
done

# テンプレートの ${DATE} を置換して仮ファイルを作成
TEMP_FILE=$(mktemp)
sed "s|\${DATE}|${DATE}|g" "${TEMPLATE_FILE}" > "${TEMP_FILE}"

# ${IMAGES} を改行ありで挿入（Macのsedはエスケープが必要）
sed "s|\${IMAGES}|$(printf '%s\n' "${IMAGES_BLOCK}" | sed 's/[&/\]/\\&/g')|" "${TEMP_FILE}" > "${LOG_FILE}"

rm "${TEMP_FILE}"

echo "✅ 完成！→ ${LOG_FILE}"
