#!/usr/bin/env python3

import os
import re
import datetime

# 設定
LOGS_DIR = 'logs'
README_FILE = 'README.md'
SUMMARY_SECTION_START = '## 📊 月間サマリー'
SUMMARY_SECTION_END = '---' # 次の水平線までを置換対象とする

def parse_log_file(filepath):
    """
    ログファイルから距離と時間を抽出する。
    例: - 距離：10.5 km
        - 時間：1時間30分
    """
    distance_km = 0.0
    total_seconds = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

        # 距離の抽出
        dist_match = re.search(r'^- 距離：([0-9.]+)\s*km', content, re.MULTILINE)
        if dist_match:
            try:
                distance_km = float(dist_match.group(1))
            except ValueError:
                pass # 数値変換エラーはスキップ

# 時間の抽出 (HH:MM または HH時間MM分 形式に対応)
        time_match_hm = re.search(r'^- 時間：([0-9]+):([0-9]+)', content, re.MULTILINE)
        time_match_jp = re.search(r'^- 時間：(?:([0-9]+)時間)?(?:([0-9]+)分)?', content, re.MULTILINE)

        if time_match_hm: # HH:MM 形式の場合
            minutes = int(time_match_hm.group(1)) if time_match_hm.group(1) else 0 # <- ここを修正
            seconds = int(time_match_hm.group(2)) if time_match_hm.group(2) else 0 # <- ここを修正
            total_seconds = minutes * 60 + seconds # <- ここを修正
        elif time_match_jp: # HH時間MM分 形式の場合
            hours = int(time_match_jp.group(1)) if time_match_jp.group(1) else 0
            minutes = int(time_match_jp.group(2)) if time_match_jp.group(2) else 0
            total_seconds = hours * 3600 + minutes * 60
        else:
            total_seconds = 0 # どちらの形式にもマッチしない場合

    
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

def generate_monthly_summary():
    """
    logsディレクトリからデータを読み込み、月間集計を生成する。
    """
    monthly_data = {} # キー: 'YYYY-MM', 値: {'distance': float, 'time_sec': int}

    for filename in sorted(os.listdir(LOGS_DIR)):
        if filename.endswith('.md') and filename != 'README.md':
            filepath = os.path.join(LOGS_DIR, filename)
            
            # ファイル名から日付（YYYY-MM-DD）を取得
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

def update_readme(new_summary_content):
    """
    README.mdの特定のセクションを新しい集計内容で更新する。
    """
    readme_content = []
    in_summary_section = False
    summary_section_written = False

    with open(README_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip() == SUMMARY_SECTION_START:
                readme_content.append(line.strip()) # ヘッダーをそのまま追加
                readme_content.append('') # 空行
                readme_content.append(new_summary_content) # 新しい集計内容を挿入
                in_summary_section = True
                summary_section_written = True
                continue # 次の行へ
            
            if in_summary_section and line.strip() == SUMMARY_SECTION_END:
                readme_content.append(line.strip()) # 区切り線をそのまま追加
                in_summary_section = False
                continue # 次の行へ

            if not in_summary_section:
                readme_content.append(line.strip()) # それ以外の行はそのまま追加

    # 書き込み (元のファイルが存在しない、またはセクションが見つからない場合のために、最後の調整が必要になることも)
    # ここでは既存セクションに上書きすることを前提としている
    with open(README_FILE, 'w', encoding='utf-8') as f:
        for line in readme_content:
            f.write(line + '\n')

if __name__ == "__main__":
    print("📝 月間サマリーを更新中 (Pythonスクリプト)...")
    try:
        summary_content = generate_monthly_summary()
        update_readme(summary_content)
        print("✅ 月間サマリーの更新が完了しました。")
    except FileNotFoundError:
        print(f"エラー: {LOGS_DIR} ディレクトリまたは {README_FILE} が見つかりません。")
        exit(1)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        exit(1)