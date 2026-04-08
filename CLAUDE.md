# running-logs

市民ランナーのランログ管理・週次まとめ記事生成プロジェクト。

## ファイル構成

- `logs/YYYY-MM-DD.md` — 日別ランログ
- `drafts/YYYY-MM-DD.md` — 週次まとめ記事の下書き（週末日付でファイル名）
- `weekly-summary-prompt.md` — まとめ記事の生成ルール・構成定義
- `images/` — ランの写真

## 週次まとめの生成方法

```
claude "2026-03-23から2026-03-29のランログをもとに、weekly-summary-prompt.mdのルールに従ってnote記事の下書きを生成して。出力はdrafts/YYYY-MM-DD.mdに保存して"
```

`weekly-summary-prompt.md` を必ず参照してから生成すること。
