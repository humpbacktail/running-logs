import os
import sys
import re
import PIL.Image
import requests
from google import genai
from datetime import datetime

# --- 基本設定 ---
API_KEY = os.getenv("GEMINI_API_KEY") 
MODEL_NAME = "gemini-2.0-flash"
client = genai.Client(api_key=API_KEY)
run_memo = os.getenv("RUN_MEMO", "特になし")

def get_weather_data(date_str, time_str):
    """気象情報を外部APIから取得"""
    lat, lon = 35.61, 139.60 
    url = f"[https://archive-api.open-meteo.com/v1/archive?latitude=](https://archive-api.open-meteo.com/v1/archive?latitude=){lat}&longitude={lon}&start_date={date_str}&end_date={date_str}&hourly=temperature_2m,weather_code,wind_speed_10m&timezone=Asia%2FTokyo"
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
    if not valid_images: return

    file_times = [datetime.fromtimestamp(os.path.getmtime(p)).strftime('%H:%M') for p in valid_images]
    hint_time = file_times[0] if file_times else "不明"

    print(f"📸 {len(valid_images)}枚の画像を解析中...")
    images = [PIL.Image.open(p) for p in valid_images]

    # --- 1. AIへの指示（プロンプト） ---
    # 装飾を禁止し、目標設定をMASAさんの現在のスタンスに合わせました
    main_prompt = f"""
    あなたは、ランニングを生涯の楽しみとするMASAさんの良き伴侶であり、精密なデータ入力担当者です。
    
    【出力に関する厳命】
    - 出力に ```markdown や ``` といったバッククォート（コードブロック）を絶対に使用しないでください。
    - Markdownの「生のテキスト」のみを直接出力してください。
    - 余計な挨拶、前置き、解説は一切不要です。

    ### 抽出と執筆の掟:
    - 画像内の「今日の目的」「コメント」「睡眠」などは、要約せず正確に書き写すこと。
    - 「使用シューズ」は、プログラムから渡された値【 {run_memo} 】をそのまま使うこと。
    - 項目を削ることは厳禁。不明な場合は「不明」と書け。

    【絶対厳守フォーマット】
    ---
    title: "🏃‍♂️ {target_id} のランログ"
    date: (YYYY-MM-DD形式)
    ---

    - 距離：
    - 時間：
    - 平均心拍数：
    - 使用シューズ：{run_memo}
    - 時間帯：(XX時)
    - 天候：(解析中)
    - コース：
    - 補給：
    - 睡眠：
    - 今日の目的：
    - コメント：

    ## 📝 コーチコメント
    (歳を重ねても楽しく、健康に走り続けることを全肯定するメッセージにしてください)
    (目標は「ハーフマラソンを心地よく完走すること」として、300文字以上で労ってください)
    """

    response = client.models.generate_content(model=MODEL_NAME, contents=[main_prompt, *images])
    md_content = response.text

    # --- 2. 天気情報の強制挿入（正規表現を強化） ---
    date_match = re.search(r"date:\s*(\d{4}-\d{2}-\d{2})", md_content)
    time_match = re.search(r"時間帯：.*?(\d{1,2})時", md_content)
    
    if date_match and time_match:
        actual_weather = get_weather_data(date_match.group(1), f"{time_match.group(1)}:00")
        md_content = re.sub(r"- 天候：.*", f"- 天候：{actual_weather}", md_content)

    # --- 3. 写真一覧の強制生成 ---
    photo_section = "\n\n## 📸 写真一覧\n"
    for img_path in valid_images:
        filename = os.path.basename(img_path)
        photo_section += f'<img src="../images/{target_id}/{filename}" width="400" loading="lazy" decoding="async">\n'

    # 重複削除
    final_md = md_content.replace("```markdown", "").replace("```", "").strip()
    if "## 📸 写真一覧" in final_md:
        final_md = final_md.split("## 📸 写真一覧")[0] + photo_section
    else:
        final_md = final_md + photo_section

    # --- 4. 保存 ---
    output_path = f"logs/{target_id}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_md)

    print(f"✅ 仕様遵守とフォーマット固定を完了しました: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(1)
    analyze_run(sys.argv[2:], sys.argv[1])