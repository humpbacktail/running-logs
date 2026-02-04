import os
import sys
import glob
import re  # これが必要でした！
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
    # 画像のみをフィルタリング
    valid_images = [p for p in image_paths if p.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not valid_images:
        print("解析対象の画像が見つかりません。")
        return

    print(f"📸 {len(valid_images)}枚の画像を解析中...")
    images = [PIL.Image.open(p) for p in valid_images]

    # --- ステップ1: データの抽出 ---
    initial_prompt = """
    ランニングアプリのスクリーンショットから以下の項目を必ず抽出してください。
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

    # --- ステップ2: 天気取得用の日時特定 ---
    date_match = re.search(r"(\d{4}/\d{2}/\d{2})", raw_data)
    time_match = re.search(r"(\d{2}:\d{2})", raw_data)
    
    date_str = date_match.group(1).replace("/", "-") if date_match else target_id[:10]
    time_str = time_match.group(1) if time_match else "08:00"
    weather_info = get_weather_data(date_str, time_str)

    # --- ステップ3: 最終的なMarkdown生成 ---
    # ここで直接、完成形のMarkdownを作らせます
    final_prompt = f"""
    あなたはMASA専用のランニング・エージェントです。3/15板橋シティでのサブ4を目指しています。
    以下の情報を元に、ブログ記事（Markdown形式）を作成してください。

    【入力情報】
    - ユーザーのメモ: {run_memo}
    - 抽出データ: {raw_data}
    - 取得した天気: {weather_info}

    【出力フォーマット】
    ---
    title: "🏃‍♂️ {target_id} のランログ"
    date: {date_str}
    ---
    - 距離：(距離) km
    - 時間：(タイム)
    - 使用シューズ：{run_memo}
    - 天候：{weather_info}
    - コメント：(一言)

    ## 📝 コーチコメント
    (サブ4達成に向けた、熱く前向きなアドバイスを300文字程度で)

    ## 📸 写真
    (画像が複数ある場合はここにまとめて表示)
    """

    response_final = client.models.generate_content(
        model=MODEL_NAME,
        contents=[final_prompt, *images]
    )
    
    output_path = f"logs/{target_id}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response_final.text)
    
    print(f"✅ 解析完了！ファイルに書き込みました: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    
    target_id = sys.argv[1]
    image_paths = sys.argv[2:]
    analyze_run(image_paths, target_id)