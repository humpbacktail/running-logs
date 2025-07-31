#!/bin/bash
set -e

echo "🔧 ログエントリー作成スクリプト開始（$(date)）"

# --- 1. 日付と連番の決定 ---
BASE_DATE=$(find upload -mindepth 1 -maxdepth 1 -type d -print0 | xargs -0 stat -f "%m %N" | sort -n | tail -1 | cut -d' ' -f2- | cut -d'/' -f2 | cut -d'-' -f1-3)

if [ -z "$BASE_DATE" ]; then
  echo "❌ upload/ 以下に日付フォルダが見つかりません。処理を中止します。"
  exit 1
fi

LAST_NUMBER=0
for f in logs/${BASE_DATE}-*.md; do
    if [ -f "$f" ]; then
        num_part=$(echo "$f" | sed -E "s|logs/${BASE_DATE}-([0-9]+)\.md|\1|")
        if [[ "$num_part" =~ ^[0-9]+$ ]] && (( 10#$num_part > LAST_NUMBER )); then
            LAST_NUMBER=$num_part
        fi
    fi
done
NEXT_NUMBER=$((LAST_NUMBER + 1))
FORMATTED_NUMBER=$(printf "%02d" "$NEXT_NUMBER")

LOG_IDENTIFIER="${BASE_DATE}-${FORMATTED_NUMBER}"
UPLOAD_DIR="upload/${BASE_DATE}"
IMAGE_DIR="images/${LOG_IDENTIFIER}"
LOG_FILE="logs/${LOG_IDENTIFIER}.md"
TEMPLATE_FILE="logs/template.md.tpl"

if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "❌ テンプレートファイルが見つかりません: ${TEMPLATE_FILE}"
  exit 1
fi

mkdir -p "${IMAGE_DIR}"

echo "📂 画像を ${UPLOAD_DIR} から ${IMAGE_DIR} へ移動中..."
if [ -d "${UPLOAD_DIR}" ] && [ "$(ls -A "${UPLOAD_DIR}")" ]; then
  mv "${UPLOAD_DIR}"/* "${IMAGE_DIR}/"
  echo "✅ 画像の移動が完了しました。"
  rm -rf "${UPLOAD_DIR}"
  echo "🗑️ ${UPLOAD_DIR} を削除しました。"
else
  echo "⚠️ ${UPLOAD_DIR} が存在しないか空のため、画像移動をスキップします。"
  if [ -d "${UPLOAD_DIR}" ]; then
    rmdir "${UPLOAD_DIR}" 2>/dev/null || true
  fi
  echo "ℹ️ ${UPLOAD_DIR} に画像が見つからなかったため、ログファイルの生成をスキップし、処理を終了します。"
  exit 0
fi

TEMP_IMG_BLOCK=$(mktemp)
if compgen -G "${IMAGE_DIR}/*" > /dev/null; then
  for img in "${IMAGE_DIR}"/*; do
    filename=$(basename "$img")
    echo '<img src="/images/'"${LOG_IDENTIFIER}"'/'"${filename}"'" width="400" />' >> "${TEMP_IMG_BLOCK}"
  done
else
  echo "（写真なし）" >> "${TEMP_IMG_BLOCK}"
  echo "ℹ️ ${IMAGE_DIR} に画像が見つかりませんでした。"
fi

echo "📝 Markdownファイルを生成中: ${LOG_FILE}"

IMAGE_BLOCK=$(cat "${TEMP_IMG_BLOCK}")

awk -v date_var="${BASE_DATE}" -v image_block="${IMAGE_BLOCK}" '
{
  line = $0
  gsub(/\$\{DATE\}/, date_var, line)
  gsub(/\$\{IMAGES\}/, image_block, line)
  print line
}' "${TEMPLATE_FILE}" > "${LOG_FILE}"

rm "${TEMP_IMG_BLOCK}" || true

echo "✅ Markdownログ生成完了: ${LOG_FILE}"
echo "👉 logs/${LOG_IDENTIFIER}.md を開いて、距離・時間などの情報を手動で入力してください。"
echo "🔧 手入力完了後、'bash update_and_push_logs.sh' を実行してください。"
echo "🎉 ログエントリー作成完了！"
