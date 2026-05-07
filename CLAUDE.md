# running-logs

市民ランナーのランログ管理・週次まとめ記事生成プロジェクト。

## ファイル構成

- `logs/YYYY-MM-DD-NN.md` — 日別ランログ（telegram-running-botが書き込み）
- `drafts/YYYY-MM-DD.md` — 週次まとめ記事の下書き（週末日付でファイル名）
- `plans/YYYY-MM.md` — 月間トレーニングプラン（masa-coach-botが月初に自動生成）
- `weekly-summary-prompt.md` — まとめ記事の生成ルール・構成定義
- `images/` — ランの写真

## 週次まとめの生成方法

毎週水曜 9:00 JST に GitHub Actions（`.github/workflows/weekly-draft.yml`）が自動実行し、前週月〜日のランログをもとに `drafts/YYYY-MM-DD.md`（日曜日付）を生成・コミットする。

- モデル：claude-sonnet-4-6
- 生成ルール：`weekly-summary-prompt.md` を参照
- 手動実行：GitHub Actions → 週次まとめ下書き生成 → Run workflow

手動で生成したい場合：
```
claude "先週月曜から日曜のランログをもとに、weekly-summary-prompt.mdのルールに従ってnote記事の下書きを生成して。出力はdrafts/YYYY-MM-DD.mdに保存して"
```

## 距離フォーマットについて

- ログの距離フィールドは `6.14km`（小文字）で記録される
- Geminiが `KM`（大文字）で出力するケースがあったが、2026-05-07 に両側を修正済み
  - `telegram-running-bot`：JSON.parse後に `p.kyori.toLowerCase()` で正規化
  - `scripts/update_monthly_summary.py`：`re.IGNORECASE` で集計側も大文字対応済み
