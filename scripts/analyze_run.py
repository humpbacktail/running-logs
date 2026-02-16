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
    """
    画像を解析し、Markdownファイルを生成する
    target_id: シェルから渡されるID (例: 2026-02-16-01)
    """
    valid_images = [p for p in image_paths if p.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not valid_images:
        print("❌ 解析対象の画像が見つかりません。")
        return

    # IDから日付(YYYY-MM-DD)を抽出
    base_date = target_id[:10]

    print(f"📸 ID: {target_id} として解析を開始...")
    images = [PIL.Image.open(p) for p in valid_images]

    # --- 1. AIへの指示（プロンプト） ---
    # 装飾禁止、目標を「楽しくハーフ完走」に合わせた最新版です
    main_prompt = f"""
    あなたは、ランニングを生涯の楽しみとするMASAさんの良き伴侶であり、精密なデータ入力担当者です。
    
    【出力に関する厳命】
    - 出力に ```markdown や ``` といったバッククォート（コードブロック）を絶対に使用しないでください。
    - Markdownの「生のテキスト」のみを直接出力してください。
    - 余計な挨拶、前置き、解説は一切不要です。

    ### 抽出の掟:
    - 時間帯は、画像内の「開始時刻（例：12:31:36）」や「XX:XX–YY:YY」という表記を最優先で探し、その「時」を抽出せよ。
    - 「使用シューズ」は、プログラムから渡された値【 {run_memo} 】をそのまま使うこと。
    - 画像内の「今日の目的」「コメント」「睡眠」などは、要約せず正確に書き写すこと。

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
    (歳を重ねても楽しく、健康に走り続けることを全肯定するメッセージにしてください)
    (目標は「ハーフマラソンを心地よく完走すること」として、300文字以上で労ってください)
    """

    response = client.models.generate_content(model=MODEL_NAME, contents=[main_prompt, *images])
    md_content = response.text

    # --- 2. 天気情報の挿入 ---
    time_match = re.search(r"時間帯：.*?(\d{1,2})時", md_content)
    if time_match:
        actual_weather = get_weather_data(base_date, f"{time_match.group(1)}:00")
        md_content = re.sub(r"- 天候：.*", f"- 天候：{actual_weather}", md_content)

    # --- 3. 装飾の最終クリーニング ---
    final_md = md_content.replace("```markdown", "").replace("```", "").strip()

    # --- 4. 写真一覧の生成 ---
    photo_section = "\n\n## 📸 写真一覧\n"
    for img_path in valid_images:
        filename = os.path.basename(img_path)
        photo_section += f'<img src="../images/{target_id}/{filename}" width="400" loading="lazy" decoding="async">\n'
    
    final_md = final_md + photo_section

    # --- 5. 保存 ---
    output_path = f"logs/{target_id}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_md)

    print(f"✅ ログを正常に生成しました: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用法: python3 analyze_run.py <TARGET_ID> <IMAGE_PATHS...>")
        sys.exit(1)
    # 第一引数がID、第二引数以降が画像パスのリスト
    analyze_run(sys.argv[2:], sys.argv[1])