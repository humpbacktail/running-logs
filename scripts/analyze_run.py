import os
import sys
import glob
from string import Template
import PIL.Image
import requests
from google import genai
from google.genai import types

# --- 気象データ取得関数 ---
def get_weather_data(date_str, time_str):
    lat, lon = 35.61, 139.60 # 多摩川周辺
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={date_str}&end_date={date_str}&hourly=temperature_2m,weather_code,wind_speed_10m&timezone=Asia%2FTokyo"
    try:
        response = requests.get(url)
        data = response.json()
        target_hour = int(time_str.split(':')[0])
        temp = data['hourly']['temperature_2m'][target_hour]
        wind = data['hourly']['wind_speed_10m'][target_hour]
        return f"気温: {temp}℃, 風速: {wind}m/s"
    except Exception:
        return "気象データ取得失敗"

# --- 設定 ---
API_KEY = os.getenv("GEMINI_API_KEY") 
MODEL_NAME = "gemini-2.5-flash" 
client = genai.Client(api_key=API_KEY)
TEMPLATE_PATH = "logs/template.md.tpl"

def analyze_run(image_paths, identifier):
    # --- ステップ1: 画像から基本情報を抽出 ---
    images = [PIL.Image.open(p) for p in image_paths]
    
    # 最初の解析：日付と時間を特定
    initial_prompt = "このランニングデータのスクリーンショットから、『走行日』と『開始時刻』を抽出してください。返信は 'YYYY-MM-DD, HH:MM' の形式のみで行ってください。"
    response = client.models.generate_content(model=MODEL_NAME, contents=[initial_prompt] + images)
    
    try:
        info = response.text.strip().split(', ')
        date_str = info[0]
        start_time = info[1]
        start_hour = start_time.split(':')[0]
    except Exception:
        date_str = "不明"
        start_time = "00:00"
        start_hour = "0"

    # --- ステップ2: 気象データを取得 ---
    weather_info = get_weather_data(date_str, start_time)
    print(f"🌤️ {start_hour}時の気象データを取得しました: {weather_info}")

    # --- ステップ3: テンプレート準備 ---
    img_tags = [f'  - <img src="../images/{identifier}/{os.path.basename(p)}" width="300">' for p in image_paths]
    img_tags_str = "\n".join(img_tags)
    
    try:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            tpl_content = f.read()
        src = Template(tpl_content)
        draft_content = src.safe_substitute({'DATE': date_str, 'IDENTIFIER': identifier, 'IMAGES': img_tags_str})
    except Exception:
        draft_content = f"Date: {date_str}\n\n{img_tags_str}"

    # 環境変数からメモを取得
    run_memo = os.getenv("RUN_MEMO", "特になし")

    # --- ステップ4: 全データを合体させて最終解析 ---
    final_prompt = f"""
    今回のランニングに関する追加メモ（シューズ情報など）: {run_memo}

    あなたはMASA専用のランニング・エージェントです。目標は3/15板橋シティでのサブ4。
    
    【状況】
    ユーザー（MASAさん）から、今日のランニングデータと「{run_memo}」というメモを受け取りました。
    
    【記入ルール】
    1. 形式はMarkdown。時間は HH:MM:SS、距離は km。
    2. シューズ欄には、メモにあるシューズ名を反映させてください。
    3. コーチコメント欄は、まず「{run_memo}」という報告に対して、親しみやすい一言（例：インフィニットプロでのリカバリーお疲れ様です！など）から始めてください。
    4. その上で、気象条件や目標タイムに向けた論理的な分析を「熱く」語ってください。

    提供された画像と、取得した天気・時間データを統合して、Markdown形式のログを出力してください。
    出力はMarkdownのコードブロックを含まない、純粋なテキストのみにしてください。
    """

    response = client.models.generate_content(model=MODEL_NAME, contents=[final_prompt] + images)
    
    output_path = f"logs/{identifier}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response.text)
    
    print(f"✅ ログを生成しました: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python analyze_run.py [identifier] [image_paths...]")
        sys.exit(1)
    
    target_id = sys.argv[1]
    paths = sys.argv[2:]
    analyze_run(paths, target_id)