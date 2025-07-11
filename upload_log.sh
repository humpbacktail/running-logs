#!/bin/bash
set -e

# 日付抽出（upload配下の最初のディレクトリ名を取得）
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
README_FILE="README.md" # README.md のパスを追加

# テンプレートファイルの存在チェック
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "❌ テンプレートファイルが見つかりません: ${TEMPLATE_FILE}"
  echo "👉 logs/template.md.tpl が存在するか確認してください。"
  exit 1
fi
# README.md の存在チェック
if [ ! -f "$README_FILE" ]; then
  echo "❌ README.md ファイルが見つかりません: ${README_FILE}"
  echo "👉 README.md が存在するか確認してください。"
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

# 画像リンク生成 (awkに渡すため一時ファイルに書き出す)
TEMP_IMG_BLOCK=$(mktemp)
if compgen -G "${IMAGE_DIR}/*" > /dev/null; then
    for img in "${IMAGE_DIR}"/*; do
      filename=$(basename "$img")
      # ここをHTMLの<img>タグ形式に修正
      echo '<img src="/images/'"${DATE}"'/'"${filename}"'" width="400" />' >> "${TEMP_IMG_BLOCK}"
    done
else
    echo "（写真なし）" >> "${TEMP_IMG_BLOCK}" # 画像がない場合の代替テキスト
    echo "ℹ️ ${IMAGE_DIR} に画像が見つかりませんでした。"
fi


# テンプレートを読み込み、置換してMarkdown生成
echo "📝 Markdownファイルを生成中: ${LOG_FILE}"

# awk を1回で処理。画像ブロックはファイルから読み込む。
awk -v date_var="${DATE}" -v temp_img_file="${TEMP_IMG_BLOCK}" '
  BEGIN {
    # テンプレート処理の開始時に画像ブロックの内容を全て読み込む
    images_block_content = "";
    while ((getline line < temp_img_file) > 0) {
      images_block_content = images_block_content line "\n";
    }
    close(temp_img_file); # ファイルを閉じる
    # 最後の不要な改行を削除（もしあれば）
    if (length(images_block_content) > 0) {
      sub(/\n$/, "", images_block_content);
    }
  }
  {
    # 現在の行を変数にコピーして操作
    line = $0;
    gsub(/\$\{DATE\}/, date_var, line); # ${DATE} を置換
    # ${IMAGES} が行に含まれる場合、画像ブロックを挿入
    # sub() は最初の一致のみを置換
    if (line ~ /\$\{IMAGES\}/) {
      sub(/\$\{IMAGES\}/, images_block_content, line);
    }
    print line; # 変更された行を出力
  }
' "${TEMPLATE_FILE}" > "${LOG_FILE}"

# 後片付け
rm "${TEMP_IMG_BLOCK}"

echo "✅ Markdownログ生成完了: ${LOG_FILE}"

# ---

### 📝 README.md の記録一覧を更新

echo "📝 README.md の記録一覧を更新中..."

TEMP_README_LINKS=$(mktemp)
# logs/ ディレクトリ内の .md ファイルを日付順にソートして取得
# README.md 自体は除外
find logs -maxdepth 1 -name "*.md" ! -name "README.md" | sort | while read -r log_file; do
    log_filename=$(basename "$log_file") # 例: 2025-06-14.md
    log_date_raw="${log_filename%.md}" # 例: 2025-06-14

    # 日付を日本語形式に変換 (例: 2025年6月14日)
    # macOS/BSD と Linux で date コマンドのオプションが異なる場合があるので注意
    # ここではシンプルに年、月、日を抽出して結合
    year=$(echo "$log_date_raw" | cut -d'-' -f1)
    month=$(echo "$log_date_raw" | cut -d'-' -f2)
    day=$(echo "$log_date_raw" | cut -d'-' -f3)
    display_date="${year}年${month}月${day}日"

    echo "- [${display_date}](${log_file})" >> "${TEMP_README_LINKS}"
done

# README.md を更新する一時ファイル
TEMP_README_UPDATED=$(mktemp)

# awk を使って README.md の記録一覧セクションを更新
awk -v new_links_file="${TEMP_README_LINKS}" '
BEGIN {
    # 新しいリンクの内容を読み込む
    generated_log_links = "";
    while ((getline line < new_links_file) > 0) {
        generated_log_links = generated_log_links line "\n";
    }
    close(new_links_file);
    # 最後の不要な改行を削除
    if (length(generated_log_links) > 0) {
        sub(/\n$/, "", generated_log_links);
    }
    in_log_list_section = 0;
}

/^## 📅 記録一覧（リンク付き）/ {
    print; # ヘッダーをそのまま出力
    print ""; # ヘッダーの後に空行を挿入（見た目の調整）
    print generated_log_links; # 生成された新しいリンク一覧を挿入
    in_log_list_section = 1; # フラグを立て、このセクションの元の行をスキップする
    next; # 次の行へ
}

in_log_list_section && /^---$/ {
    print; # 区切り線をそのまま出力
    in_log_list_section = 0; # フラグをリセット
    next; # 次の行へ
}

!in_log_list_section {
    print; # 記録一覧セクション外の行はそのまま出力
}
' "${README_FILE}" > "${TEMP_README_UPDATED}"

# 更新された内容を README.md に書き戻す
mv "${TEMP_README_UPDATED}" "${README_FILE}"

# 後片付け
rm "${TEMP_README_LINKS}" "${TEMP_README_UPDATED}"

echo "✅ README.md の記録一覧を更新しました。"

# --- 📊 月間サマリーを更新 (Pythonスクリプトを呼び出し) ---
/usr/bin/env python3 scripts/update_monthly_summary.py

# ---

# 🚀 Git 操作（add → commit → push）

echo "🚀 GitHubにアップロード中..."

# 新しいログファイル、画像ディレクトリ、そして更新された README.md を追加
git add "$LOG_FILE" "$IMAGE_DIR" "$README_FILE"

# コミット対象の変更があるか確認
if git diff-index --quiet HEAD --; then
  echo "ℹ️ コミット対象の変更がありません。Git操作をスキップします。"
else
  git commit -m "Add log and images for ${DATE} and update README.md"
  git push
  echo "✅ ${DATE} のログと画像をGitHubにプッシュ完了！"
fi

echo "🎉 スクリプト完了！"