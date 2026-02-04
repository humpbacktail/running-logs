import os
import sys
import re
import PIL.Image
import requests
from google import genai

# --- 設定 ---
API_KEY = os.getenv("GEMINI_API_KEY") 
MODEL_NAME = "gemini-2.0-flash" 
client = genai.Client(api_key=API_KEY)
run_memo = os.getenv("RUN_MEMO", "特になし")

def get_weather_data(date_str, time_str):
    lat, lon = 35.61, 139.60 
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
    valid_images = [p for p in image_paths if p.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not valid_images:
        print("❌ 解析対象の画像が見つかりません。")
        return

    print(f"📸 {len(valid_images)}枚の画像を解析中...")
    images = [PIL.Image.open(p) for p in valid_images]

    # ステップ1: データ抽出
    initial_prompt = "ランニングのスクショから日付(YYYY/MM/DD)、開始時刻(HH:MM)、距離(km)、タイム(HH:MM:SS)、平均ペースを抽出してください。"
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=[initial_prompt, *images])
        raw_data = response.text
    except Exception as e:
        print(f"❌ Gemini APIエラー: {e}")
        return

    # ステップ2: 天気
    date_match = re.search(r"(\d{4}/\d{2}/\d{2})", raw_data)
    time_match = re.search(r"(\d{2}:\d{2})", raw_data)
    date_str = date_match.group(1).replace("/", "-") if date_match else target_id[:10]
    time_str = time_match.group(1) if time_match else "08:00"
    weather_info = get_weather_data(date_str, time_str)

    # ステップ3: Markdown生成
    final_prompt = f"""
    あなたはMASA専用のコーチです。3/15板橋シティでのサブ4が目標です。
    以下の情報を元に、ブログ記事（Markdown）を完成させてください。
    
    【入力情報】
    - メモ: {run_memo}
    - データ: {raw_data}
    - 天気: {weather_info}

    【出力形式】
    ---
    title: "🏃‍♂️ {target_id} のランログ"
    date: {date_str}
    ---
    - 距離：(距離) km
    - 時間：(タイム)
    - 使用シューズ：{run_memo}
    - 天候：{weather_info}
    - コメント：(ランニングの内容を短く)

    ## 📝 コーチコメント
    (サブ4目標に向けた熱いコメントを300文字程度で)

    ## 📸 写真
    (画像をここへ表示)
    """

    response_final = client.models.generate_content(model=MODEL_NAME, contents=[final_prompt, *images])
    
    # 強制的に上書き保存
    output_path = f"logs/{target_id}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response_final.text)
    
    print(f"✅ 書き込み完了: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    analyze_run(sys.argv[2:], sys.argv[1])