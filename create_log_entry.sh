#!/bin/bash
set -e

echo "🔧 ログエントリー作成スクリプト開始（$(date)）"

# --- 1. 日付抽出 ---
DATE=$(basename "$(find upload -mindepth 1 -maxdepth 1 -type d | sort | head -n 1)")

if [ -z "$DATE" ]; then
  echo "❌ upload/ 以下に日付フォルダが見つかりません。処理を中止します。"
  exit 1
fi

UPLOAD_DIR="upload/${DATE}"
IMAGE_DIR="images/${DATE}"
LOG_FILE="logs/${DATE}.md"
TEMPLATE_FILE="logs/template.md.tpl"

# --- 2. 必須ファイルの存在チェック ---
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "❌ テンプレートファイルが見つかりません: ${TEMPLATE_FILE}"
  echo "👉 logs/template.md.tpl が存在するか確認してください。"
  exit 1
fi

mkdir -p "${IMAGE_DIR}"

# --- 3. 画像移動とuploadディレクトリの削除 ---
echo "📂 画像を ${UPLOAD_DIR} から ${IMAGE_DIR} へ移動中..."
if [ -d "${UPLOAD_DIR}" ] && [ "$(ls -A "${UPLOAD_DIR}")" ]; then
  mv "${UPLOAD_DIR}"/* "${IMAGE_DIR}/"
  echo "✅ 画像の移動が完了しました。"

  rm -rf "${UPLOAD_DIR}"
  echo "🗑️ ${UPLOAD_DIR} を削除しました。"
else
  echo "⚠️ ${UPLOAD_DIR} が存在しないか空のため、画像移動をスキップします。"
  if [ -d "${UPLOAD_DIR}" ]; then
    rmdir "${UPLOAD_DIR}" 2>/dev/null || echo "（情報）${UPLOAD_DIR} は空でないため削除されませんでした。"
  fi
  echo "ℹ️ 画像が見つからなかったため、ログファイルの生成をスキップします。"
  exit 0 # 画像がない場合はここで終了
fi

# --- 4. 画像リンク生成 ---
TEMP_IMG_BLOCK=$(mktemp)
if compgen -G "${IMAGE_DIR}/*" > /dev/null; then
    for img in "${IMAGE_DIR}"/*; do
      filename=$(basename "$img")
      echo '<img src="/images/'"${DATE}"'/'"${filename}"'" width="400" />' >> "${TEMP_IMG_BLOCK}"
    done
else
    echo "（写真なし）" >> "${TEMP_IMG_BLOCK}"
    echo "ℹ️ ${IMAGE_DIR} に画像が見つかりませんでした。"
fi

# --- 5. テンプレートからMarkdown生成 ---
echo "📝 Markdownファイルを生成中: ${LOG_FILE}"

awk -v date_var="${DATE}" -v temp_img_file="${TEMP_IMG_BLOCK}" '
  BEGIN {
    images_block_content = "";
    while ((getline line < temp_img_file) > 0) {
      images_block_content = images_block_content line "\n";
    }
    close(temp_img_file);
    if (length(images_block_content) > 0) {
      sub(/\n$/, "", images_block_content);
    }
  }
  {
    line = $0;
    gsub(/\$\{DATE\}/, date_var, line);
    if (line ~ /\$\{IMAGES\}/) {
      sub(/\$\{IMAGES\}/, images_block_content, line);
    }
    print line;
  }
' "${TEMPLATE_FILE}" > "${LOG_FILE}"

rm "${TEMP_IMG_BLOCK}" || true # 一時ファイルをクリーンアップ

echo "✅ Markdownログ生成完了: ${LOG_FILE}"
echo "👉 logs/${DATE}.md を開いて、距離・時間などの情報を手動で入力してください。"
echo "🔧 手入力完了後、'bash update_and_push_logs.sh' を実行してください。"
echo "🎉 ログエントリー作成完了！"