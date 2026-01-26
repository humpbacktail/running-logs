import os
import sys
import glob
from string import Template
import PIL.Image
import requests

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

# --- ライブラリのインポート ---
from google import genai
from google.genai import types

# --- 設定 ---
API_KEY = os.getenv("GEMINI_API_KEY") 
MODEL_NAME = "gemini-2.5-flash" 
client = genai.Client(api_key=API_KEY)
TEMPLATE_PATH = "logs/template.md.tpl" 

def analyze_images_and_create_md(image_dir, output_md_path, date_str, seq_num):
    image_paths = glob.glob(os.path.join(image_dir, "*"))
    valid_exts = ['.jpg', '.jpeg', '.png', '.webp', '.heic']
    
    image_objects = []
    identifier = f"{date_str}-{seq_num}"
    img_tags_list = []

    print(f"🤖 {len(image_paths)}枚の画像を読み込み中...")

    image_paths.sort()
    for p in image_paths:
        if os.path.splitext(p)[1].lower() in valid_exts:
            fname = os.path.basename(p)
            tag = f'<img src="../images/{identifier}/{fname}" width="400" loading="lazy" decoding="async" />'
            img_tags_list.append(tag)
            try:
                img = PIL.Image.open(p)
                image_objects.append(img)
            except Exception:
                print(f"⚠️ スキップ: {p}")

    img_tags_str = "\n".join(img_tags_list)

    # --- ステップ1: AIに開始時間を教えてもらう ---
    print("🕒 開始時刻を抽出中...")
    time_prompt = "これらの画像から、ランニングの開始時間をHH形式（2桁の数字のみ）で回答してください。例: 07, 10, 15。数字以外は不要です。"
    try:
        time_res = client.models.generate_content(model=MODEL_NAME, contents=[time_prompt, *image_objects])
        start_hour = time_res.text.strip().zfill(2)[:2] # 最初の2文字を数字として取得
        if not start_hour.isdigit(): start_hour = "07" # 失敗時はデフォルト07
    except:
        start_hour = "07"

    # --- ステップ2: その時間の天気を取得 ---
    weather_info = get_weather_data(date_str, f"{start_hour}:00")
    print(f"🌡️ {start_hour}時の気象データを取得しました: {weather_info}")

    # --- ステップ3: テンプレートとメモを準備 ---
    try:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            tpl_content = f.read()
        src = Template(tpl_content)
        draft_content = src.safe_substitute({'DATE': date_str, 'IDENTIFIER': identifier, 'IMAGES': img_tags_str})
    except Exception:
        draft_content = f"Date: {date_str}\n\n{img_tags_str}"

    USER_MEMO = os.getenv("RUN_MEMO", "（なし）")

    # --- ステップ4: 全データを合体させて最終解析 ---
    final_prompt = f"""
    あなたはMASA専用のランニング・エージェントです。目標は3/15板橋シティでのサブ4。

    【入力情報】
    - ユーザーメモ: {USER_MEMO}
    - 抽出された開始時刻: {start_hour}時
    - 当時の正確な気象データ: {weather_info}

    【記入ルール】
    1. 時間は HH:MM:SS、距離は小文字 km。
    2. メモのシューズ名を反映。
    3. 天候欄には必ず「{start_hour}時頃の気象データ: {weather_info}」を反映。
    4. コーチコメントは、この気象条件とサブ4目標（3/15）を照らし合わせて熱く記述。

    【対象テキスト】
    {draft_content}
    """

    try:
        print("🤖 最終レポートを作成中...")
        response = client.models.generate_content(model=MODEL_NAME, contents=[final_prompt, *image_objects])
        ai_text = response.text.replace("```markdown", "").replace("```", "").strip()
        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write(ai_text)
        print(f"✅ ログ完成！: {output_md_path}")
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    analyze_images_and_create_md(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])