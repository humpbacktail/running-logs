#!/usr/bin/env python3

import os
import re
import datetime

# 設定
LOGS_DIR = 'logs'
README_FILE = 'README.md'

# README.md 内のセクションマーカー
RECORD_LIST_SECTION_START = '## 📅 記録一覧（リンク付き）'
RECORD_LIST_SECTION_END = '---' # 記録一覧セクションの次の水平線

SUMMARY_SECTION_START = '## 📊 月間サマリー'
SUMMARY_SECTION_END = '---' # 月間サマリーセクションの次の水平線

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

def generate_record_list_html():
    """
    logsディレクトリからデータを読み込み、年/月ごとにグループ化されたHTML形式の記録一覧を生成する。
    """
    records_by_year_month = {} # キー: 'YYYY-MM', 値: リスト of (date_obj, display_date, log_file_path)

    for filename in sorted(os.listdir(LOGS_DIR)):
        if filename.endswith('.md') and filename != 'README.md':
            filepath = os.path.join(LOGS_DIR, filename)
            
            date_str = filename.replace('.md', '')
            try:
                log_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                year_month_key = log_date.strftime('%Y-%m') # 'YYYY-MM' 形式
                display_date = log_date.strftime('%Y年%m月%d日') # 例: 2025年07月12日
            except ValueError:
                continue # 不正なファイル名はスキップ

            if year_month_key not in records_by_year_month:
                records_by_year_month[year_month_key] = []
            
            records_by_year_month[year_month_key].append((log_date, display_date, filepath))

    # 年月順にソートし、HTML形式で出力
    html_output_lines = []
    
    # 年ごとにグループ化するための辞書
    records_by_year = {}
    for ym_key in sorted(records_by_year_month.keys()):
        year = ym_key.split('-')[0]
        if year not in records_by_year:
            records_by_year[year] = []
        records_by_year[year].append((ym_key, records_by_year_month[ym_key]))

    # 最新の年を上に表示
    for year_key in sorted(records_by_year.keys(), reverse=True):
        html_output_lines.append(f'<details open>') # デフォルトで年を展開
        html_output_lines.append(f'  <summary><h3>{year_key}年</h3></summary>')
        html_output_lines.append(f'  <ul>')
        
        # 月は古い順に表示 (年の中では昇順)
        for ym_key, records in sorted(records_by_year[year_key], key=lambda x: x[0]):
            month_name = datetime.datetime.strptime(ym_key, '%Y-%m').strftime('%m月')
            html_output_lines.append(f'    <li>')
            html_output_lines.append(f'      <details>')
            html_output_lines.append(f'        <summary><strong>{month_name}</strong></summary>')
            html_output_lines.append(f'        <ul>')
            
            # 日付の降順（新しい日付が上）でソート
            sorted_records = sorted(records, key=lambda x: x[0], reverse=True)
            for _, display_date, filepath in sorted_records:
                html_output_lines.append(f'          <li><a href="{filepath}">{display_date}</a></li>')
            
            html_output_lines.append(f'        </ul>')
            html_output_lines.append(f'      </details>')
            html_output_lines.append(f'    </li>')
        
        html_output_lines.append(f'  </ul>')
        html_output_lines.append(f'</details>')
    
    return "\n".join(html_output_lines)


def generate_monthly_summary():
    """
    logsディレクトリからデータを読み込み、月間集計を生成する。
    (この関数は変更なし)
    """
    monthly_data = {} # キー: 'YYYY-MM', 値: {'distance': float, 'time_sec': int}

    for filename in sorted(os.listdir(LOGS_DIR)):
        if filename.endswith('.md') and filename != 'README.md':
            filepath = os.path.join(LOGS_DIR, filename)
            
            date_str = filename.replace('.md', '')
            try:
                log_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
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
    """
    readme_content = []
    in_record_list_section = False
    in_summary_section = False

    with open(README_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            stripped_line = line.strip()

            if stripped_line == RECORD_LIST_SECTION_START:
                readme_content.append(RECORD_LIST_SECTION_START)
                readme_content.append('') # 空行
                readme_content.append(record_list_content) # 新しい記録一覧を挿入
                in_record_list_section = True
                continue
            
            if stripped_line == RECORD_LIST_SECTION_END and in_record_list_section:
                readme_content.append(RECORD_LIST_SECTION_END)
                in_record_list_section = False
                continue

            if stripped_line == SUMMARY_SECTION_START:
                readme_content.append(SUMMARY_SECTION_START)
                readme_content.append('') # 空行
                readme_content.append(summary_content) # 新しいサマリーを挿入
                in_summary_section = True
                continue
            
            if stripped_line == SUMMARY_SECTION_END and in_summary_section:
                readme_content.append(SUMMARY_SECTION_END)
                in_summary_section = False
                continue

            # 処理中のセクション外の行はそのまま追加
            if not in_record_list_section and not in_summary_section:
                readme_content.append(stripped_line) # strip() で余計な空白を削除してから追加

    # 書き込み (元のファイルが存在しない、またはセクションが見つからない場合のために、最後の調整が必要になることも)
    with open(README_FILE, 'w', encoding='utf-8') as f:
        for line in readme_content:
            f.write(line + '\n')

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