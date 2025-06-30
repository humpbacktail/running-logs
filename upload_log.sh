#!/bin/bash
set -e
set -x

# 引数チェック（YYYY-MM-DD形式の日付が必要）
if [ $# -ne 1 ]; then
  echo "Usage: $0 YYYY-MM-DD"
  exit 1
fi

DATE=$1
URL_PATH="/Users/yamamotomasaharu/documents/running-logs/upload/${DATE}/"

# すでに.mdファイルがある場合はエラーで止める（上書き防止）
if [ -e logs/${DATE}.md ]; then
  echo "Error: logs/${DATE}.md already exists. Please delete it or choose another date."
  exit 1
fi

# 画像を移動（画像が存在しない場合はスキップ）
if ls logs/images/* 1> /dev/null 2>&1; then
  mkdir -p upload/${DATE}
  mv logs/images/* upload/${DATE}/
else
  echo "No images to move. Skipping image move."
fi

# Markdownファイルを生成
sed "s|{{image_url}}|${URL_PATH}|g" logs/template.md.tpl > logs/${DATE}.md

# Git操作（必要ならコメントアウト可能）
git add upload/${DATE}/*
git add logs/${DATE}.md
git commit -m "Add running log and images for ${DATE}"
git push origin main
