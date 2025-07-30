#!/bin/bash
set -e

echo "🔧 ログエントリー作成スクリプト開始（$(date)）"

# --- 1. 日付と連番の決定 ---
# upload/ ディレクトリ内のサブディレクトリからベースの日付（例: 2025-07-30）を抽出
# ※ ここでの assumption: upload/ の中には、処理待ちの YYYY-MM-DD 形式のディレクトリが一つだけある
BASE_DATE=$(find upload -mindepth 1 -maxdepth 1 -type d -print0 | xargs -0 stat -f "%m %N" | sort -n | tail -1 | cut -d' ' -f2- | cut -d'/' -f2 | cut -d'-' -f1-3)

if [ -z "$BASE_DATE" ]; then
  echo "❌ upload/ 以下に日付フォルダが見つかりません。処理を中止します。"
  exit 1
fi

# 当日の最大連番を検索し、次の連番を決定
# logs/YYY-MM-DD-NN.md 形式のファイルを探し、NN の最大値を見つける
LAST_NUMBER=0
for f in logs/${BASE_DATE}-*.md; do
    if [ -f "$f" ]; then # ファイルが存在することを確認
        # ファイル名から連番部分のみを抽出（例: logs/2025-07-30-01.md -> 01）
        num_part=$(echo "$f" | sed -E "s|logs/${BASE_DATE}-([0-9]+)\.md|\1|")
        # 抽出した部分が数値であり、かつ現在のLAST_NUMBERより大きい場合、更新
        if [[ "$num_part" =~ ^[0-9]+$ ]] && (( 10#$num_part > LAST_NUMBER )); then # 10# で10進数として比較
            LAST_NUMBER=$num_part
        fi
    fi
done
NEXT_NUMBER=$((LAST_NUMBER + 1))
FORMATTED_NUMBER=$(printf "%02d" "$NEXT_NUMBER") # 2桁ゼロ埋め

# 最終的なログの識別子 (YYYY-MM-DD-NN)
LOG_IDENTIFIER="${BASE_DATE}-${FORMATTED_NUMBER}"

UPLOAD_DIR="upload/${BASE_DATE}" # upload フォルダは日付部分のみ (例: 2025-07-30)
IMAGE_DIR="images/${LOG_IDENTIFIER}" # 画像フォルダは連番付き
LOG_FILE="logs/${LOG_IDENTIFIER}.md" # MDファイルも連番付き
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
  # ディレクトリが空でなければrmdirは失敗するので、エラーは無視
  if [ -d "${UPLOAD_DIR}" ]; then
    rmdir "${UPLOAD_DIR}" 2>/dev/null || true # エラーを無視
  fi
  # 画像がない場合は、ログファイルの生成もスキップし、スクリプトを終了
  echo "ℹ️ ${UPLOAD_DIR} に画像が見つからなかったため、ログファイルの生成をスキップし、処理を終了します。"
  exit 0
fi

# --- 4. 画像リンク生成 ---
TEMP_IMG_BLOCK=$(mktemp)
# glob でファイルが存在するかチェック
if compgen -G "${IMAGE_DIR}/*" > /dev/null; then
    for img in "${IMAGE_DIR}"/*; do
      filename=$(basename "$img")
      # ここも LOG_IDENTIFIER に修正
      echo '<img src="/images/'"${LOG_IDENTIFIER}"'/'"${filename}"'" width="400" />' >> "${TEMP_IMG_BLOCK}"
    done
else
    # 画像がなくても空ブロックではなく、「（写真なし）」と表示
    echo "（写真なし）" >> "${TEMP_IMG_BLOCK}"
    echo "ℹ️ ${IMAGE_DIR} に画像が見つかりませんでした。"
fi

# --- 5. テンプレートからMarkdown生成 ---
echo "📝 Markdownファイルを生成中: ${LOG_FILE}"

# BASE_DATE を ${DATE} に、images_block_content_param を ${IMAGES} に置き換える
awk -v date_var="${BASE_DATE}" -v images_block_content_param="$(cat "${TEMP_IMG_BLOCK}")" '
  BEGIN {
    images_block_content = images_block_content_param;
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
echo "👉 logs/${LOG_IDENTIFIER}.md を開いて、距離・時間などの情報を手動で入力してください。"
echo "🔧 手入力完了後、'bash update_and_push_logs.sh' を実行してください。"
echo "🎉 ログエントリー作成完了！"