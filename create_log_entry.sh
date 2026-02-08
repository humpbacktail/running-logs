#!/bin/bash

UPLOAD_BASE="upload"
TARGET_DATE_DIR=$(ls -1 "$UPLOAD_BASE" | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' | head -n 1)

if [ -z "$TARGET_DATE_DIR" ]; then
    echo "❌ uploadフォルダ内に処理待ちの日付フォルダが見つかりません。"
    exit 1
fi

DATE="$TARGET_DATE_DIR"
IDENTIFIER="${DATE}-01"
TARGET_DIR="images/${IDENTIFIER}"
UPLOAD_DIR="${UPLOAD_BASE}/${DATE}"
LOG_FILE="logs/${IDENTIFIER}.md"

echo "🔧 ログエントリー作成スクリプト開始"

if [ -d "$UPLOAD_DIR" ]; then
    mkdir -p "$TARGET_DIR"
    echo "📂 画像を $UPLOAD_DIR から $TARGET_DIR へ移動中..."
    mv "$UPLOAD_DIR"/* "$TARGET_DIR/"
    rm -rf "$UPLOAD_DIR" # 移動後はフォルダごと消去してスッキリさせる
    echo "✅ 画像の移動が完了しました。"
fi

IMAGE_FILES=$(ls "$TARGET_DIR"/*.{png,jpg,jpeg,PNG,JPG,JPEG} 2>/dev/null)

if [ -n "$IMAGE_FILES" ]; then
    echo "📝 解析・生成中: $LOG_FILE"
    # Pythonが失敗した場合は、そこで中断メッセージを出して終了する
    if python3 scripts/analyze_run.py "$IDENTIFIER" $IMAGE_FILES; then
        echo "✨ 全工程が完了しました: $LOG_FILE"
    else
        echo "⚠️ 解析中にエラーが発生しました。時間を置いて再試行してください。"
        exit 1
    fi
else
    echo "❌ 画像が見つかりません"
    exit 1
fi