import os
import sys
import glob
from string import Template
import PIL.Image
import requests
from google import genai
from google.genai import types

# --- 設定 ---
API_KEY = os.getenv("GEMINI_API_KEY") 
MODEL_NAME = "gemini-2.0-flash" 
client = genai.Client(api_key=API_KEY)
run_memo = os.getenv("RUN_MEMO", "特になし")
TEMPLATE_PATH = "logs/template.md.tpl"

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
    except:
        return "気象データ取得失敗"

def analyze_run(image_paths, target_id):
    # 画像のみをフィルタリング（念のため）
    valid_images = [p for p in image_paths if p.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not valid_images:
        print("解析対象の画像が見つかりません。")
        return

    images = [PIL.Image.open(p) for p in valid_images]

    # --- ステップ1: スクショからデータを抽出 ---
    initial_prompt = """
    ランニングアプリのスクリーンショットから以下の項目を抽出してください。
    1. 日付 (YYYY/MM/DD)
    2. 開始時刻 (HH:MM)
    3. 距離 (km)
    4. タイム (HH:MM:SS)
    5. 平均ペース (MM:SS /km)
    """
    
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[initial_prompt, *images]
    )
    raw_data = response.text
    print(f"--- 抽出データ ---\n{raw_data}")

    # --- ステップ2: 日時を特定して天気を取得 ---
    # (正規表現で抽出。失敗時は今日の日付)
    date_match = re.search(r"(\d{4}/\d{2}/\d{2})", raw_data)
    time_match = re.search(r"(\d{2}:\d{2})", raw_data)
    
    date_str = date_match.group(1).replace("/", "-") if date_match else target_id[:10]
    time_str = time_match.group(1) if time_match else "08:00"
    start_hour = time_str.split(':')[0]
    
    weather_info = get_weather_data(date_str, time_str)

    # --- ステップ3: 最終解析プロンプト ---
    final_prompt = f"""
    あなたはMASA専用のランニング・エージェントです。目標は3/15板橋シティでのサブ4。
    
    【入力情報】
    - ユーザーメモ: {run_memo}
    - 抽出データ: {raw_data}
    - 天気: {weather_info}
    
    【記入ルール】
    1. 形式はMarkdown。
    2. シューズ欄には「{run_memo}」を反映。
    3. コーチコメントは、サブ4目標を踏まえて熱く。
    """

    response_final = client.models.generate_content(
        model=MODEL_NAME,
        contents=[final_prompt, *images]
    )
    
    # 書き込み先ファイルパス
    output_path = f"logs/{target_id}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response_final.text)
    
    print(f"✅ 解析完了: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    
    target_id = sys.argv[1]
    image_paths = sys.argv[2:]
    analyze_run(image_paths, target_id)