#!/bin/bash

# --- 対話パート ---
# LINEのやり取りをシミュレーションします
echo "🤖：お疲れ様です！今日のランニングのスクショは images/ に置きましたか？ (y/n)"
read confirm
if [ "$confirm" != "y" ]; then
    echo "先に画像を置いてから、もう一度実行してくださいね。"
    exit 1
fi

echo "🤖：今日のシューズやメモを教えてください（空欄でもOK）："
read user_input

# 入力された内容を環境変数にセット
export RUN_MEMO="$user_input"

# --- 実行パート ---
echo "🤖：了解です！解析を開始します..."
echo "-----------------------------------"

# 1. ログの生成（ここで RUN_MEMO が analyze_run.py に渡ります）
echo "🤖 1/3: ログを生成中..."
bash create_log_entry.sh

# 2. 集計 & サイト用コピー
echo "📊 2/3: READMEと月間サマリーを更新中..."
bash update_logs.sh

# 3. GitHubへプッシュ
echo "🚀 3/3: GitHubに保存中..."
bash push_logs.sh

echo "-----------------------------------"
echo "✨ すべての工程が完了しました！GitHubを確認してみてください。"