#!/bin/bash
echo "📊 月間サマリーと記録一覧を更新中..."
python3 scripts/update_monthly_summary.py
echo "✅ 集計完了！README.md を確認してください。"
