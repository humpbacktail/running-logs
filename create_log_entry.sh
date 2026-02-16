#!/bin/bash
# ---------------------------------------------------------
# create_log_entry.sh (連番フォルダ作成・移動・解析の司令塔)
# ---------------------------------------------------------

UPLOAD_DIR="upload"
IMAGES_DIR="images"
LOGS_DIR="logs"

# 1. uploadフォルダ内の日付フォルダを探す
SRC_DIR=$(ls -1 "$UPLOAD_DIR" | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -n 1)

if [ -z "$SRC_DIR" ]; then
    echo "❌ upload/ 内に日付フォルダが見つかりません。"
    exit 1
fi

# 2. ベースとなる日付を取得 (例: 2026-02-16)
BASE_DATE=$(echo "$SRC_DIR" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')

# 3. logs/ を見て、次の連番を決定する (01, 02...)
LAST_NUM=$(ls "$LOGS_DIR"/${BASE_DATE}-*.md 2>/dev/null | grep -oE '[0-9]{2}\.md$' | cut -d. -f1 | sort -n | tail -1)
if [ -z "$LAST_NUM" ]; then
    NEXT_NUM="01"
else
    NEXT_NUM=$(printf "%02d" $((10#$LAST_NUM + 1)))
fi

TARGET_ID="${BASE_DATE}-${NEXT_NUM}"
echo "📂 次のIDを確定しました: $TARGET_ID"

# 4. 【ここが重要】新しいフォルダを先に作り、そこに画像を移動
# これにより、既存のフォルダの中に混ざる事故を防ぎます
mkdir -p "$IMAGES_DIR/$TARGET_ID"
mv "$UPLOAD_DIR/$SRC_DIR"/* "$IMAGES_DIR/$TARGET_ID/"

# 空になったupload側の日付フォルダを削除
rmdir "$UPLOAD_DIR/$SRC_DIR"

# 5. Pythonによる解析実行
python3 analyze_run.py "$TARGET_ID" "$IMAGES_DIR/$TARGET_ID"/*