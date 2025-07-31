#!/usr/bin/env python3

import os
import re
import datetime
import traceback

# 設定
LOGS_DIR = 'logs'
README_FILE = 'README.md'

# README.md 内のセクションマーカーを、Pythonスクリプトが認識する正確な文字列に定義
# これらは README.md ファイル内に手動で追加するコメント形式のマーカーと一致させる
RECORD_LIST_SECTION_START_MARKER = '<!-- RECORD_LIST_START -->'
RECORD_LIST_SECTION_END_MARKER = '<!-- RECORD_LIST_END -->'

SUMMARY_SECTION_START_MARKER = '<!-- SUMMARY_START -->'
SUMMARY_SECTION_END_MARKER = '<!-- SUMMARY_END -->'

# --- 関数定義 ---

def parse_log_file(filepath):
    """
    ログファイルから距離と時間を抽出する。
    例: - 距離：10.5km
        - 時間：45:13
    """
    distance_km = 0.0
    total_seconds = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

        # 距離の抽出 (kmの前にスペースがあってもなくても対応)
        dist_match = re.search(r'^- 距離：([0-9.]+)\s*km', content, re.MULTILINE)
        if dist_match:
            try:
                distance_km = float(dist_match.group(1))
            except ValueError:
                pass # 数値変換エラーはスキップ

        # 時間の抽出 (HH:MM:SS (時:分:秒) または MM:SS (分:秒) に対応)
        time_match_hms = re.search(r'^- 時間：([0-9]+):([0-9]+):([0-9]+)', content, re.MULTILINE)
        time_match_ms = re.search(r'^- 時間：([0-9]+):([0-9]+)', content, re.MULTILINE)

        if time_match_hms: # HH:MM:SS 形式の場合 (例: 01:05:52)
            hours = int(time_match_hms.group(1))
            minutes = int(time_match_hms.group(2))
            seconds = int(time_match_hms.group(3))
            total_seconds = hours * 3600 + minutes * 60 + seconds
        elif time_match_ms: # MM:SS 形式の場合 (例: 45:13)
            minutes = int(time_match_ms.group(1))
            seconds = int(time_match_ms.group(2))
            total_seconds = minutes * 60 + seconds
        else: # どちらの形式にもマッチしない場合
            total_seconds = 0
    
    return distance_km, total_seconds

def format_time_from_seconds(total_seconds):
    """秒数を 'HH時間MM分' 形式に変換"""
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours}時間{minutes:02d}分"

def calculate_pace(total_seconds, total_km):
    """平均ペースを '分'XX秒/km' 形式で計算"""
    if total_km == 0:
        return "N/A"
    
    pace_sec_per_km = total_seconds / total_km
    pace_minutes = int(pace_sec_per_km // 60)
    pace_seconds = int(pace_sec_per_km % 60)
    
    return f"{pace_minutes}'{pace_seconds:02d}/km"

def generate_record_list_markdown(): # 名前をhtmlからmarkdownに変更
    """
    logsディレクトリからデータを読み込み、全てのログをシンプルなMarkdownリスト形式で生成する。
    """
    all_records = [] 

    for filename in sorted(os.listdir(LOGS_DIR)):
        if filename.endswith('.md') and filename not in ['README.md', 'template.md.tpl']: # template.md.tplを除外
            filepath = os.path.join(LOGS_DIR, filename)
            
            # ファイル名から YYYY-MM-DD-NN を抽出 (例: 2025-07-30-01)
            full_identifier = filename.replace('.md', '')
            
            # YYYY-MM-DD 部分のみを抽出 (例: 2025-07-30)
            log_date_only_str = full_identifier.rsplit('-', 1)[0] if '-' in full_identifier and full_identifier.rsplit('-', 1)[1].isdigit() else full_identifier

            try:
                # ソートのために YYYY-MM-DD をパース
                log_date_obj = datetime.datetime.strptime(log_date_only_str, '%Y-%m-%d')
                
                # 表示用日付 (例: 2025年07月30日-01)
                num_part = full_identifier.rsplit('-', 1)[1] if '-' in full_identifier and full_identifier.rsplit('-', 1)[1].isdigit() else None
                if num_part:
                    display_date = f"{log_date_obj.strftime('%Y年%m月%d日')}-{num_part}"
                else: # 連番がない場合（YYYY-MM-DD.md 形式のファイル）
                    display_date = log_date_obj.strftime('%Y年%m月%d日')

                # ソートキー: 日付（降順）、連番（降順）
                sort_key = (log_date_obj, int(num_part) if num_part else 0)

            except ValueError:
                continue # 不正なファイル名はスキップ

            all_records.append((sort_key, full_identifier, display_date, filepath))

    # 全ての記録を日付（降順）かつ連番（降順）でソート
    sorted_records = sorted(all_records, key=lambda x: x[0], reverse=True)

    # Markdownリスト形式で出力
    markdown_output_lines = []
    for _, full_identifier_str, display_date, filepath in sorted_records:
        markdown_output_lines.append(f'- [{display_date}]({filepath})')
    
    return "\n".join(markdown_output_lines)


def generate_monthly_summary():
    """
    logsディレクトリからデータを読み込み、月間集計を生成する。
    ファイル名が YYYY-MM-DD-NN.md の形式に対応。
    """
    monthly_data = {} # キー: 'YYYY-MM', 値: {'distance': float, 'time_sec': int}

    for filename in sorted(os.listdir(LOGS_DIR)):
        if filename.endswith('.md') and filename not in ['README.md', 'template.md.tpl']: # template.md.tplを除外
            filepath = os.path.join(LOGS_DIR, filename)
            
            # ファイル名から YYYY-MM-DD-NN を抽出 (例: 2025-07-30-01)
            full_identifier = filename.replace('.md', '')
            
            # 月キー取得のために YYYY-MM-DD 部分のみを抽出 (例: 2025-07-30)
            log_date_only_str = full_identifier.rsplit('-', 1)[0] if '-' in full_identifier and full_identifier.rsplit('-', 1)[1].isdigit() else full_identifier

            try:
                log_date = datetime.datetime.strptime(log_date_only_str, '%Y-%m-%d')
                month_key = log_date.strftime('%Y-%m') # 'YYYY-MM' 形式
            except ValueError:
                continue # 不正なファイル名はスキップ

            distance, time_sec = parse_log_file(filepath)

            if month_key not in monthly_data:
                monthly_data[month_key] = {'distance': 0.0, 'time_sec': 0}
            
            monthly_data[month_key]['distance'] += distance
            monthly_data[month_key]['time_sec'] += time_sec

    # 集計結果を整形
    summary_lines = []
    # 月順にソートして出力
    for month_key in sorted(monthly_data.keys()):
        data = monthly_data[month_key]
        total_dist = data['distance']
        total_time_sec = data['time_sec']

        display_month = datetime.datetime.strptime(month_key, '%Y-%m').strftime('%Y年%m月')
        
        formatted_time = format_time_from_seconds(total_time_sec)
        avg_pace = calculate_pace(total_time_sec, total_dist)

        summary_lines.append(
            f"- **{display_month}**: 距離 **{total_dist:.1f} km**, 時間 **{formatted_time}**, 平均ペース **{avg_pace}**"
        )
    
    return "\n".join(summary_lines)

def update_readme_sections(record_list_content, summary_content):
    """
    README.mdの記録一覧と月間サマリーセクションを新しい内容で更新する。
    HTMLコメント形式のマーカーを使って内容を置換する。
    """
    try:
        with open(README_FILE, 'r', encoding='utf-8') as f:
            readme_full_content = f.read()

        # 記録一覧セクションの置換
        record_list_pattern = re.compile(
            re.escape(RECORD_LIST_SECTION_START_MARKER) + r'.*' + re.escape(RECORD_LIST_SECTION_END_MARKER),
            re.DOTALL # . が改行にもマッチするように
        )
        new_record_list_block = RECORD_LIST_SECTION_START_MARKER + '\n' + record_list_content + '\n' + RECORD_LIST_SECTION_END_MARKER
        readme_full_content = record_list_pattern.sub(new_record_list_block, readme_full_content, 1) # 1回だけ置換

        # 月間サマリーセクションの置換
        summary_pattern = re.compile(
            re.escape(SUMMARY_SECTION_START_MARKER) + r'.*' + re.escape(SUMMARY_SECTION_END_MARKER),
            re.DOTALL
        )
        new_summary_block = SUMMARY_SECTION_START_MARKER + '\n' + summary_content + '\n' + SUMMARY_SECTION_END_MARKER
        readme_full_content = summary_pattern.sub(new_summary_block, readme_full_content, 1) # 1回だけ置換

        with open(README_FILE, 'w', encoding='utf-8', newline='\n') as f:
            f.write(readme_full_content)

    except Exception as e:
        print(f"README.md の更新中にエラーが発生しました: {e}")
        raise # エラーを再スローして、トレースバックを表示させる

if __name__ == "__main__":
    print("📝 README.md の記録一覧と月間サマリーを更新中 (Pythonスクリプト)...")
    try:
        record_list_md = generate_record_list_markdown() # 関数名を変更
        monthly_summary_content = generate_monthly_summary()
        update_readme_sections(record_list_md, monthly_summary_content)
        print("✅ README.md の更新が完了しました。")
    except FileNotFoundError:
        print(f"エラー: {LOGS_DIR} ディレクトリまたは {README_FILE} が見つかりません。")
        exit(1)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        # 詳細なエラーメッセージを表示
        traceback.print_exc()
        exit(1)