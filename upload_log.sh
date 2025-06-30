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

# アップロード画像を images/ に移動
mv "${UPLOAD_DIR}"/* "${IMAGE_DIR}/"

# 画像のMarkdownリンク生成を一時ファイルに書き出す（改行対応のため）
TEMP_IMG_BLOCK=$(mktemp)
for img in "${IMAGE_DIR}"/*; do
  filename=$(basename "${img}")
  echo "![${filename}](images/${DATE}/${filename})" >> "${TEMP_IMG_BLOCK}"
  echo "" >> "${TEMP_IMG_BLOCK}"
done

# テンプレートを一時ファイルに変換（変数はプレースホルダで置換）
TEMP_TEMPLATE=$(mktemp)
sed -e "s|\${DATE}|${DATE}|g" -e "s|${IMAGES}|${IMAGES_BLOCK}|g" "${TEMPLATE_FILE}" > "${LOG_FILE}"

# 画像ブロックを挿入（${IMAGES} を置換）
awk -v img_block="$(cat "${TEMP_IMG_BLOCK}")" '
  {
    if ($0 ~ /\${IMAGES}/) {
      print img_block
    } else {
      print
    }
  }
' "${TEMP_TEMPLATE}" > "${LOG_FILE}"

# 後片付け
rm "${TEMP_IMG_BLOCK}" "${TEMP_TEMPLATE}"

echo "✅ 完成！→ ${LOG_FILE}"
