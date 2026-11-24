# running-logs

市民ランナーのランログ管理・週次まとめ記事生成プロジェクト。

## クラウド（スマホ・Web）で作業するとき：最初に記憶を読む

MasaのMacでは `~/.claude` に記憶（経緯・残タスク・合意済みルール）があるが、クラウドのセッションには無い。
`~/.claude/projects/-Users-yamamotomasaharu/memory/` が存在しない環境なら、**作業を始める前に**次を行う：

1. `git clone --depth 1 https://github.com/humpbacktail/claude-config.git ~/claude-config`（非公開リポジトリ）
2. `~/claude-config/CLAUDE.md` と `~/claude-config/projects/-Users-yamamotomasaharu/memory/MEMORY.md`（索引）を読み、このリポジトリに関係する `project_*.md` / `feedback_*.md` も読む
3. 作業中に決まったこと・わかったこと・残タスクは、同じ記憶ファイルに追記し、`git -C ~/claude-config pull --rebase` → commit → push する（Macは次回セッション開始時に自動で取り込む）
4. cloneやpushができなかったら、黙って進めずMasaに伝える（記憶なしで作業していることを明示する）

`~/Documents/ARCHITECTURE.md` などMac上のファイルはクラウドからは読めない。

## ファイル構成

- `logs/YYYY-MM-DD-NN.md` — 日別ランログ（telegram-running-botが書き込み）
- `drafts/YYYY-MM-DD.md` — 週次まとめ記事の下書き（週末日付でファイル名）
- `plans/YYYY-MM.md` — 月間トレーニングプラン（masa-coach-botが月初に自動生成）
- `weekly-summary-prompt.md` — まとめ記事の生成ルール・構成定義
- `images/` — ランの写真

## 週次まとめの生成方法

毎週**火曜 7:00 JST**に GitHub Actions（`.github/workflows/weekly-draft.yml`）が自動実行し、前週月〜日のランログをもとに `drafts/YYYY-MM-DD.md`（日曜日付）を生成・コミットする。（2026-06-15変更、旧：水曜9:00）

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

## 集計（scripts/update_monthly_summary.py）

- README の月間・週次サマリーと stats.json は、`collect_runs()` → `aggregate_runs()` の同じ集計結果から作る（2026-11-17、Codexレビュー指摘で統一）
- 距離が入っていないログ（例：2026-09-30-01＝睡眠画面だけ）は記録一覧には残すが、回数・距離の集計には入れない
- 距離の合計は Decimal、表示だけ小数第1位に四捨五入。平均ペースは丸める前の距離で計算。時間が空欄のログは距離・回数には入れるが、ペース計算（pace_km）からは外す
- テスト：`python3 -m unittest discover -s tests`（GitHub Actions でも集計前に実行。落ちたら README/stats は更新されない）
