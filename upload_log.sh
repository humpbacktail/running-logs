#!/bin/bash
set -e

export DATE=$(basename "$(find upload -mindepth 1 -maxdepth 1 -type d | head -n 1)")

UPLOAD_DIR="upload/${DATE}"
IMAGE_DIR="images/${DATE}"
LOG_FILE="logs/${DATE}.md"
TEMPLATE_FILE="logs/template.md.tpl"

mkdir -p "${IMAGE_DIR}"

if [ -d "${UPLOAD_DIR}" ] && [ "$(ls -A "${UPLOAD_DIR}")" ]; then
  mv "${UPLOAD_DIR}"/* "${IMAGE_DIR}/"
else
  echo "⚠️ ${UPLOAD_DIR} が存在しないか空のため、画像移動をスキップします"
fi

# 画像リンク作成
IMAGES_BLOCK=""
for img in "${IMAGE_DIR}"/*; do
  [ -f "$img" ] || continue
  filename=$(basename "$img")
  IMAGES_BLOCK+="![${filename}](images/${DATE}/${filename})"$'\n\n'
done

# 一時テンプレートにコピー
TEMP_TEMPLATE=$(mktemp)
cp "${TEMPLATE_FILE}" "${TEMP_TEMPLATE}"

# DATEだけsedで置換
sed -i '' "s|\${DATE}|${DATE}|g" "${TEMP_TEMPLATE}"

# ${IMAGES} だけawkでマルチライン置換
awk -v img_block="$IMAGES_BLOCK" '
  {
    if ($0 ~ /\${IMAGES}/) {
      printf "%s", img_block
    } else {
      print
    }
  }
' "${TEMP_TEMPLATE}" > "${LOG_FILE}"

rm "${TEMP_TEMPLATE}"
echo "✅ 完了！→ ${LOG_FILE}"
