#!/usr/bin/env python3
# migrate_logs.py
import argparse, datetime, os, pathlib, re, sys
from typing import List

# ---------- ユーティリティ ----------
DATE_IN_NAME = re.compile(r"(20\d{2})[-_/\.](\d{2})[-_/\.](\d{2})")
H1_TITLE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)

def infer_date_from_name(name: str) -> str:
    m = DATE_IN_NAME.search(name)
    if m:
        y, mo, d = m.groups()
        return f"{y}-{mo}-{d}"
    return datetime.date.today().isoformat()

def infer_title(content: str, fallback: str) -> str:
    m = H1_TITLE.search(content)
    if m:
        return m.group(1).strip()
    return re.sub(r"\.md$", "", fallback, flags=re.IGNORECASE)

def has_front_matter(text: str) -> bool:
    return text.lstrip().startswith("---")

def ensure_front_matter(text: str, title: str, date_iso: str) -> str:
    if has_front_matter(text):
        return text
    fm = f"---\ntitle: {title}\ndate: {date_iso}\n---\n\n"
    return fm + text

def safe_write(path: pathlib.Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(content)

def next_available(path: pathlib.Path) -> pathlib.Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    i = 1
    while True:
        cand = path.with_name(f"{stem}-{i}{suffix}")
        if not cand.exists():
            return cand
        i += 1

# ---------- メイン ----------
def migrate(sources: List[str], target: str, move: bool, dry_run: bool, excludes: List[str]):
    root = pathlib.Path(".").resolve()
    tdir = root / target
    tdir.mkdir(exist_ok=True)

    excludes_set = set(excludes) | {"README.md", "index.md"}
    migrated = 0
    skipped  = 0

    for src in sources:
        sdir = (root / src).resolve()
        if not sdir.exists():
            print(f"⚠️  Source not found: {src}")
            continue

        for p in sdir.rglob("*.md"):
            # 自分自身/ターゲット/隠し・テンプレの除外
            if target in p.parts:
                skipped += 1
                continue
            if p.name in excludes_set:
                skipped += 1
                continue

            try:
                content = p.read_text(encoding="utf-8")
            except Exception as e:
                print(f"❌ Read error: {p} ({e})")
                skipped += 1
                continue

            date_iso = infer_date_from_name(p.name)
            title = infer_title(content, p.name)
            new_content = ensure_front_matter(content, title, date_iso)

            # ファイル名：既に日付がなければ付与
            out_name = p.name
            if not DATE_IN_NAME.search(out_name):
                # スラッグ簡易化（空白→ハイフン）
                slug_base = re.sub(r"\s+", "-", re.sub(r"\.md$", "", p.name, flags=re.I))
                out_name = f"{date_iso}-{slug_base}.md"
            out_path = next_available(tdir / out_name)

            if dry_run:
                print(f"DRY-RUN: {'MOVE' if move else 'COPY'} {p.relative_to(root)} -> {out_path.relative_to(root)}  (title='{title}', date={date_iso})")
            else:
                if move:
                    # move: まず書き出し→元を削除（安全のためcopy→deleteの二段構え）
                    safe_write(out_path, new_content)
                    try:
                        p.unlink()
                    except Exception as e:
                        print(f"⚠️ Could not remove source {p}: {e}")
                else:
                    # copy: 新規を書き出し（元は残す）
                    safe_write(out_path, new_content)

                migrated += 1

    print(f"✅ Migrated: {migrated}  |  Skipped: {skipped}  |  Output dir: {target}")
    if dry_run:
        print("ℹ️  Dry run only. No files were written. Remove --dry-run to execute.")

def main():
    parser = argparse.ArgumentParser(description="Migrate Markdown logs into Jekyll collection '_logs/'.")
    parser.add_argument("--source", "-s", action="append", default=["logs"], help="Source directory (repeatable). Default: logs")
    parser.add_argument("--target", "-t", default="_logs", help="Target collection directory. Default: _logs")
    parser.add_argument("--move", action="store_true", help="Move instead of copy (default is copy).")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without writing files.")
    parser.add_argument("--exclude", "-x", action="append", default=[], help="File name to exclude (repeatable).")
    args = parser.parse_args()

    migrate(args.source, args.target, args.move, args.dry_run, args.exclude)

if __name__ == "__main__":
    main()
