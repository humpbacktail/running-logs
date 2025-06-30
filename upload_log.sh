#!/bin/bash
set -e
set -x

# 引数チェック
if [ $# -ne 1 ]; then
  echo "Usage: $0 YYYY-MM-DD"
  exit 1
fi

DATE=$1
SRC_DIR="upload/${DATE}"
DEST_DIR="images/${DATE}"
LOG_FILE="logs/${DATE}.md"
URL_PATH="images/${DATE}"

# 画像元フォルダが存在するかチェック
if [ ! -d "${SRC_DIR}" ]; then
  echo "Error: ${SRC_DIR} not found."
  exit 1
fi

# 画像移動
mkdir -p "${DEST_DIR}"
mv "${SRC_DIR}"/* "${DEST_DIR}/"

# Markdown生成
{
  echo "# Run Log: ${DATE}"
  echo ""
  for img in ${DEST_DIR}/*; do
    filename=$(basename "${img}")
    echo "![${filename}](${URL_PATH}/${filename})"
    echo ""
  done
} > "${LOG_FILE}"

echo "✅ Markdown created: ${LOG_FILE}"
