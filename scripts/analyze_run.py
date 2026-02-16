import os
import sys
import re
import PIL.Image
import requests
from google import genai
from datetime import datetime

# --- 【重要】パスの基準をスクショの親ディレクトリに固定 ---
# 実行場所がどこであれ、常に scripts/ の一つ上（ルート）を基準にします
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- 基本設定 ---
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
        return f"{target_hour}時頃: 気温: {temp}℃, 風速: {wind}m/s"
    except:
        return "データ取得失敗"

def analyze_run(image_paths, target_id):
    valid_images = [p for p in image_paths if p.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not valid_images:
        print("❌ 解析対象の画像が見つかりません。")
        return

    base_date = target_id[:10]
    print(f"📸 ID: {target_id} として解析を開始...")
    images = [PIL.Image.open(p) for p in valid_images]

    main_prompt = f"""
    あなたは、ランニングを生涯の楽しみとするMASAさんの良き伴侶であり、精密なデータ入力担当者です。
    出力にバッククォート(```)は絶対に使わず、Markdownの生テキストのみを出力してください。

    ### 抽出の掟:
    - 時間帯は、画像内の「開始時刻」を最優先で探し、その「時」を抽出せよ。
    - 「使用シューズ」は、プログラムから渡された値【 {run_memo} 】をそのまま使うこと。

    【絶対厳守フォーマット】
    ---
    title: "🏃‍♂️ {target_id} のランログ"
    date: {base_date}
    ---
    - 距離：
    - 時間：
    - 平均心拍数：
    - 使用シューズ：{run_memo}
    - 時間帯：
    - 天候：(解析中)
    - コース：
    - 補給：
    - 睡眠：
    - 今日の目的：
    - コメント：

    ## 📝 コーチコメント
    (歳を重ねても楽しく健康に走り続けることを全肯定し、ハーフ完走を応援する300文字以上のメッセージ)
    """

    response = client.models.generate_content(model=MODEL_NAME, contents=[main_prompt, *images])
    md_content = response.text

    # 天気情報の挿入
    time_match = re.search(r"時間帯：.*?(\d{1,2})時", md_content)
    if time_match:
        actual_weather = get_weather_data(base_date, f"{time_match.group(1)}:00")
        md_content = re.sub(r"- 天候：.*", f"- 天候：{actual_weather}", md_content)

    final_md = md_content.replace("```markdown", "").replace("```", "").strip()

    # 画像パスの生成 (BASE_DIR を基準にする)
    photo_section = "\n\n## 📸 写真一覧\n"
    for img_path in valid_images:
        filename = os.path.basename(img_path)
        # Markdown内での相対パスは images/ から始める
        photo_section += f'<img src="../images/{target_id}/{filename}" width="400" loading="lazy" decoding="async">\n'
    
    final_md = final_md + photo_section

    # 保存先を BASE_DIR/logs/ に固定
    output_path = os.path.join(BASE_DIR, "logs", f"{target_id}.md")
    
    # logsフォルダがない場合は作成
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_md)

    print(f"✅ ログを生成しました: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    # 第一引数がID、残りが画像パス
    analyze_run(sys.argv[2:], sys.argv[1])