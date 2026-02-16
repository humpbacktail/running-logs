import os
import sys
import re
import PIL.Image
import requests
from google import genai
from datetime import datetime
import glob

# --- 基本設定 ---
API_KEY = os.getenv("GEMINI_API_KEY") 
MODEL_NAME = "gemini-2.0-flash"
client = genai.Client(api_key=API_KEY)
run_memo = os.getenv("RUN_MEMO", "特になし")

def get_next_target_id(base_date):
    """
    指定された日付(YYYY-MM-DD)に対して、次の連番付きIDを生成する
    例: 2026-02-15-01.md があれば 2026-02-15-02 を返す
    """
    existing_files = glob.glob(f"logs/{base_date}-*.md")
    if not existing_files:
        return f"{base_date}-01"
    
    nums = []
    for f in existing_files:
        match = re.search(r"-(\d{2})\.md$", f)
        if match:
            nums.append(int(match.group(1)))
    
    next_num = max(nums) + 1 if nums else 1
    return f"{base_date}-{next_num:02d}"

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

def analyze_run(image_paths, base_date):
    valid_images = [p for p in image_paths if p.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not valid_images: return

    # 新しい仕様：連番付きのIDを決定
    target_id = get_next_target_id(base_date)
    print(f"📂 生成されるID: {target_id}")

    print(f"📸 {len(valid_images)}枚の画像を解析中...")
    images = [PIL.Image.open(p) for p in valid_images]

    # --- AIへの指示（プロンプト） ---
    main_prompt = f"""
    あなたは、ランニングを生涯の楽しみとするMASAさんの良き伴侶であり、精密なデータ入力担当者です。
    
    【出力に関する厳命】
    - 出力に ```markdown や ``` といったバッククォート（コードブロック）を絶対に使用しないでください。
    - Markdownの「生のテキスト」のみを直接出力してください。
    - 余計な解説は不要です。

    ### 抽出の掟:
    - 時間帯は、画像内の「開始時刻（例：12:31:36）」や「XX:XX–YY:YY」という表記を最優先で探し、その「時」を抽出せよ。
    - 「使用シューズ」は、プログラムから渡された値【 {run_memo} 】をそのまま使うこと。

    【絶対厳守フォーマット】
    ---
    title: "🏃‍♂️ {target_id} のランログ"
    date: {base_date}
    ---
    (以下項目続く...)
    """

    response = client.models.generate_content(model=MODEL_NAME, contents=[main_prompt, *images])
    md_content = response.text

    # 天気挿入と装飾削除（中略 - ロジックは維持）
    date_match = re.search(r"date:\s*(\d{4}-\d{2}-\d{2})", md_content)
    time_match = re.search(r"時間帯：.*?(\d{1,2})時", md_content)
    if date_match and time_match:
        actual_weather = get_weather_data(date_match.group(1), f"{time_match.group(1)}:00")
        md_content = re.sub(r"- 天候：.*", f"- 天候：{actual_weather}", md_content)

    final_md = md_content.replace("```markdown", "").replace("```", "").strip()

    # 画像パスの生成（連番付きのtarget_idを使用）
    photo_section = "\n\n## 📸 写真一覧\n"
    for img_path in valid_images:
        filename = os.path.basename(img_path)
        photo_section += f'<img src="../images/{target_id}/{filename}" width="400" loading="lazy" decoding="async">\n'
    
    final_md = final_md + photo_section

    # 保存
    output_path = f"logs/{target_id}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_md)

    print(f"✅ 連番仕様を復旧しました: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(1)
    analyze_run(sys.argv[2:], sys.argv[1])