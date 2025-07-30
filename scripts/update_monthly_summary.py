#!/usr/bin/env python3

import os
import re
import datetime

# 設定
LOGS_DIR = 'logs'
README_FILE = 'README.md'

# README.md 内のセクションマーカーをユニークなものに変更
RECORD_LIST_SECTION_START = ''
RECORD_LIST_SECTION_END = ''

SUMMARY_SECTION_START = ''
SUMMARY_SECTION_END = ''

# (parse_log_file, format_time_from_seconds, calculate_pace は変更なし)
# (generate_record_list_html, generate_monthly_summary は変更なし)

def update_readme_sections(record_list_content, summary_content):
    """
    README.mdの記録一覧と月間サマリーセクションを新しい内容で更新する。
    """
    readme_content_lines = [] # 最終的にファイルに書き込む行のリスト
    in_record_list_replace_block = False
    in_summary_replace_block = False

    with open(README_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            stripped_line = line.strip()

            # 記録一覧セクションの処理
            if stripped_line == RECORD_LIST_SECTION_START:
                readme_content_lines.append(line.rstrip('\n')) # 元の行（改行あり）を追加
                readme_content_lines.append(record_list_content) # 新しい記録一覧を挿入
                in_record_list_replace_block = True # ここから置換ブロックに入る
                continue # 次の行へ
            elif stripped_line == RECORD_LIST_SECTION_END:
                readme_content_lines.append(line.rstrip('\n')) # 元の行（改行あり）を追加
                in_record_list_replace_block = False # 置換ブロックから出る
                continue # 次の行へ

            # 月間サマリーセクションの処理
            if stripped_line == SUMMARY_SECTION_START:
                readme_content_lines.append(line.rstrip('\n')) # 元の行（改行あり）を追加
                readme_content_lines.append(summary_content) # 新しいサマリーを挿入
                in_summary_replace_block = True # ここから置換ブロックに入る
                continue
            elif stripped_line == SUMMARY_SECTION_END:
                readme_content_lines.append(line.rstrip('\n')) # 元の行（改行あり）を追加
                in_summary_replace_block = False # 置換ブロックから出る
                continue

            # 置換ブロック内でなければ、元の行をそのまま追加
            if not in_record_list_replace_block and not in_summary_replace_block:
                readme_content_lines.append(line.rstrip('\n')) # 元の行（改行あり）を追加

    # ファイルに書き込み
    with open(README_FILE, 'w', encoding='utf-8', newline='\n') as f:
        for line_to_write in readme_content_lines:
            f.write(line_to_write + '\n') # 各要素の末尾に改行を追加して書き込む

if __name__ == "__main__":
    print("📝 README.md の記録一覧と月間サマリーを更新中 (Pythonスクリプト)...")
    try:
        record_list_html = generate_record_list_html()
        monthly_summary_content = generate_monthly_summary()
        update_readme_sections(record_list_html, monthly_summary_content)
        print("✅ README.md の更新が完了しました。")
    except FileNotFoundError:
        print(f"エラー: {LOGS_DIR} ディレクトリまたは {README_FILE} が見つかりません。")
        exit(1)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        # 詳細なエラーメッセージを表示
        import traceback
        traceback.print_exc()
        exit(1)