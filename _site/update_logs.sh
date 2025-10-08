#!/bin/bash
echo "📊 月間サマリーと記録一覧を更新中..."
python3 scripts/update_monthly_summary.py

echo "🪄 サイト用の _logs/ にコピー中..."
python3 migrate_logs.py --source logs

echo "✅ 集計＆サイト用コピー完了！README.md / _logs/ を確認してください。"
