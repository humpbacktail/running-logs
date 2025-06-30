#!/bin/bash

# スクリプト内でエラーが発生したら即座に終了
set -e

echo "🔧 スクリプト開始（$(date)）"

# --- 1. GitHubリポジトリの最新状態を確認・同期 ---
echo "🌀 GitHubの最新状態を確認中..."
if ! git diff-index --quiet HEAD --; then
  echo "⚠️ ローカルに未コミットの変更があります。先に commit か stash してください。"
  exit 1
fi

# 最新の状態に同期 (rebase オプションで履歴をきれいに保つ)
git pull --rebase origin main
echo "✅ GitHub同期完了"

# --- 2. 処理対象の日付フォルダを特定 ---
# upload/ ディレクトリ内のサブディレクトリを検索し、最初に見つかったものを対象とする。
# 通常は日付形式 (YYYY-MM-DD) のフォルダを想定。
# もし複数のフォルダがある場合、一番古いものが選択される可能性があるので注意。
# 厳密に最新のフォルダを処理したい場合は、find の代わりに他のロジックが必要になる場合があります。
TARGET_DIR=$(find upload -mindepth 1 -maxdepth 1 -type d | head -n 1)

if [ -z "$TARGET_DIR" ]; then
  echo "❌ upload/ ディレクトリ内に処理対象のフォルダが見つかりませんでした。処理を中止します。"
  exit 1
fi

export DATE=$(basename "$TARGET_DIR") # 例: 2023-10-27

# --- 3. パス定義 ---
UPLOAD_DIR="upload/${DATE}"
IMAGE_DIR="images/${DATE}"
LOG_FILE="logs/${DATE}.md"
TEMPLATE_FILE="logs/template.md.tpl"

# 必須ファイルの存在チェック
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "❌ テンプレートファイルが見つかりません: ${TEMPLATE_FILE}"
  echo "👉 logs/template.md.tpl が存在するか確認してください。"
  exit 1
fi

# --- 4. フォルダ作成と画像移動 ---
mkdir -p "${IMAGE_DIR}"

echo "📂 画像を ${UPLOAD_DIR} から ${IMAGE_DIR} へ移動中..."
if [ -d "${UPLOAD_DIR}" ] && [ "$(ls -A "${UPLOAD_DIR}")" ]; then
  mv "${UPLOAD_DIR}"/* "${IMAGE_DIR}/"
  echo "✅ 画像の移動が完了しました。"
else
  echo "⚠️ ${UPLOAD_DIR} が存在しないか空のため、画像の移動をスキップします。"
  # 画像がなければ、それ以降の処理は不要な場合も考慮
  echo "ℹ️ 画像がなければ、ログファイルは生成されません。"
  # clean up the upload directory even if empty or non-existent
  # rmdir "$UPLOAD_DIR" 2>/dev/null || true # If you want to delete only if empty
  exit 0 # 画像がない場合は成功として終了
fi

# 移動後、upload ディレクトリをクリーンアップ
# ディレクトリが空でなくても強制削除します。必要に応じて rmdir を使用してください。
if [ -d "${UPLOAD_DIR}" ]; then
  rm -rf "${UPLOAD_DIR}"
  echo "🗑️ ${UPLOAD_DIR} を削除しました。"
fi

# --- 5. Markdownファイルの生成 ---
echo "📝 Markdownファイルを生成中: ${LOG_FILE}"

# 画像のMarkdownリンクを一時ファイルに生成
TEMP_IMG_BLOCK=$(mktemp)
for img in "${IMAGE_DIR}"/*; do
  filename=$(basename "${img}")
  # Markdown の画像リンクは1行で十分で、不要な改行は含めない
  echo "![${filename}](images/${DATE}/${filename})" >> "${TEMP_IMG_BLOCK}"
done

# テンプレートに変数を埋め込み、画像ブロックを挿入
# awk を1回で処理することで効率化
awk -v date_var="${DATE}" -v images_block_var="$(cat "${TEMP_IMG_BLOCK}")" '
  {
    # 現在の行を変数にコピーして操作
    line = $0;
    gsub(/\$\{DATE\}/, date_var, line); # ${DATE} を置換
    # ${IMAGES} が行に含まれる場合、画像ブロックを挿入
    if (line ~ /\$\{IMAGES\}/) {
      sub(/\$\{IMAGES\}/, images_block_var, line); # 最初の ${IMAGES} を置換
    }
    print line; # 変更された行を出力
  }
' "${TEMPLATE_FILE}" > "${LOG_FILE}"

# 後片付け
rm "${TEMP_IMG_BLOCK}"
# TEMP_TEMPLATE はもう生成されていないため、削除不要

echo "✅ Markdownファイル生成完了！→ ${LOG_FILE}"

# --- 6. Gitにコミット・プッシュ ---
echo "🚀 GitHubにアップロード中..."

git add "${IMAGE_DIR}" "${LOG_FILE}"

# 未コミットの変更があるか最終確認
if git diff-index --quiet HEAD --; then
  echo "ℹ️ コミット対象の変更がありません。処理をスキップします。"
else
  git commit -m "Add log and images for ${DATE}"
  git push origin main
  echo "✅ ${DATE} のログと画像をGitHubにアップロードしました！"
fi

echo "🎉 スクリプト完了！"