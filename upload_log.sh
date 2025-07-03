#!/bin/bash
set -e

# 日付抽出（upload配下の最初のディレクトリ名を取得）
# find の結果を sort することで、日付形式であれば昇順（一番古い日付）が選択される
DATE=$(basename "$(find upload -mindepth 1 -maxdepth 1 -type d | sort | head -n 1)")

# 空チェック
if [ -z "$DATE" ]; then
  echo "❌ upload/ 以下に日付フォルダが見つかりません。処理を中止します。"
  exit 1
fi

UPLOAD_DIR="upload/${DATE}"
IMAGE_DIR="images/${DATE}"
LOG_FILE="logs/${DATE}.md"
TEMPLATE_FILE="logs/template.md.tpl"

# テンプレートファイルの存在チェック
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "❌ テンプレートファイルが見つかりません: ${TEMPLATE_FILE}"
  echo "👉 logs/template.md.tpl が存在するか確認してください。"
  exit 1
fi

mkdir -p "${IMAGE_DIR}"

# 画像移動とuploadディレクトリの削除
echo "📂 画像を ${UPLOAD_DIR} から ${IMAGE_DIR} へ移動中..."
if [ -d "${UPLOAD_DIR}" ] && [ "$(ls -A "${UPLOAD_DIR}")" ]; then
  mv "${UPLOAD_DIR}"/* "${IMAGE_DIR}/"
  echo "✅ 画像の移動が完了しました。"

  # 元のuploadディレクトリを削除
  rm -rf "${UPLOAD_DIR}"
  echo "🗑️ ${UPLOAD_DIR} を削除しました。"
else
  echo "⚠️ ${UPLOAD_DIR} が存在しないか空のため、画像移動をスキップします。"
  # uploadディレクトリが空だった場合も、処理済みとして削除を試みる
  if [ -d "${UPLOAD_DIR}" ]; then
    rmdir "${UPLOAD_DIR}" 2>/dev/null || echo "（情報）${UPLOAD_DIR} は空でないため削除されませんでした。"
  fi
  # 画像がない場合はログ生成処理もスキップして終了
  echo "ℹ️ 画像移動がスキップされたため、ログファイルの生成およびGit操作は行いません。"
  exit 0
fi

# 画像リンク生成
# TEMP_IMG_BLOCK を使ってファイルに書き出し、awk にはファイルの中身を渡す
TEMP_IMG_BLOCK=$(mktemp)
if compgen -G "${IMAGE_DIR}/*" > /dev/null; then
    for img in "${IMAGE_DIR}"/*; do
      filename=$(basename "$img")
      echo "![${filename}](images/${DATE}/${filename})" >> "${TEMP_IMG_BLOCK}"
    done
else
    echo "（写真なし）" >> "${TEMP_IMG_BLOCK}" # 画像がない場合の代替テキスト
    echo "ℹ️ ${IMAGE_DIR} に画像が見つかりませんでした。"
fi


# テンプレートを読み込み、置換してMarkdown生成
echo "📝 Markdownファイルを生成中: ${LOG_FILE}"
# awk を1回で処理することで効率化
awk -v date_var="${DATE}" -v images_block_var="$(cat "${TEMP_IMG_BLOCK}")" '
  {
    # 現在の行を変数にコピーして操作
    line = $0;
    gsub(/\$\{DATE\}/, date_var, line); # ${DATE} を置換
    # ${IMAGES} が行に含まれる場合、画像ブロックを挿入
    # sub() は最初の一致のみを置換
    if (line ~ /\$\{IMAGES\}/) {
      sub(/\$\{IMAGES\}/, images_block_var, line);
    }
    print line; # 変更された行を出力
  }
' "${TEMPLATE_FILE}" > "${LOG_FILE}"

# 後片付け
rm "${TEMP_IMG_BLOCK}"

echo "✅ Markdownログ生成完了: $LOG_FILE"

# Git 操作（add → commit → push）
echo "🚀 GitHubにアップロード中..."

git add "$LOG_FILE" "$IMAGE_DIR" # 新しいログファイルと画像ディレクトリを追加

# コミット対象の変更があるか確認
if git diff-index --quiet HEAD --; then
  echo "ℹ️ コミット対象の変更がありません。Git操作をスキップします。"
else
  git commit -m "Add log and images for ${DATE}"
  # git push origin main はリモートリポジトリが設定されていれば `git push` で十分
  git push
  echo "✅ ${DATE} のログと画像をGitHubにプッシュ完了！"
fi

echo "🎉 スクリプト完了！"