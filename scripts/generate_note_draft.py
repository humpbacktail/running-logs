import os
import re
import glob
from datetime import datetime, timedelta
from google import genai

# --- 設定 ---
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"
client = genai.Client(api_key=API_KEY)

LOGS_DIR = "logs"
README_PATH = "README.md"
OUTPUT_DIR = "outputs"

# --- MASAさんの特徴 (ブラウザ版Geminiの知見) ---
MASA_PROFILE = """
- 目標: 3/15 板橋シティマラソンでサブ4達成
- 傾向: 睡眠が6時間を切ると心拍数が上がりやすく、粘りが弱まる傾向がある
- ペット: ジャックラッセルテリアを大切にしている
- 趣味: 映画鑑賞、読書、数学
"""

def generate_weekly_note():
    today = datetime.now()
    # 1. 前週の月曜日と日曜日を計算
    current_weekday = today.weekday() # 月=0, 日=6
    last_monday = today - timedelta(days=current_weekday + 7)
    last_sunday = last_monday + timedelta(days=6)
    
    # ファイル名用の日付文字列 (MMDD形式)
    start_md = last_monday.strftime("%m%d")
    end_md = last_sunday.strftime("%m%d")
    file_name = f"weekly_note_draft_{start_md}_{end_md}.txt"
    output_path = os.path.join(OUTPUT_DIR, file_name)

    print(f"📅 集計期間: {last_monday.strftime('%Y-%m-%d')} 〜 {last_sunday.strftime('%Y-%m-%d')}")

    # 2. ログファイルの収集
    recent_logs = ""
    for i in range(7):
        date_str = (last_monday + timedelta(days=i)).strftime("%Y-%m-%d")
        pattern = os.path.join(LOGS_DIR, f"{date_str}-*.md")
        for file_path in sorted(glob.glob(pattern)):
            with open(file_path, "r", encoding="utf-8") as f:
                recent_logs += f"\n--- FILE: {os.path.basename(file_path)} ---\n"
                recent_logs += f.read()

    if not recent_logs:
        print("⚠️ 対象期間（先週）のログが見つかりませんでした。")
        return

    # 3. READMEから累計データを取得
    readme_data = ""
    try:
        with open(README_PATH, "r", encoding="utf-8") as f:
            content = f.read()
            m = re.search(r"(.*?)", content, re.DOTALL)
            if m: readme_data = m.group(1).strip()
    except: pass

    # 4. AIへのプロンプト
    prompt = f"""
    あなたはMASA専用のランニング・エージェントです。
    先週1週間（{last_monday.strftime('%Y-%m-%d')}〜{last_sunday.strftime('%Y-%m-%d')}）のログを元に、
    note.com 投稿用の振り返り記事を執筆してください。

    【MASAのプロフィール】
    {MASA_PROFILE}

    【全体実績サマリー】
    {readme_data}

    【今週の個別ログ】
    {recent_logs}

    【執筆ルール】
    1. タイトルは「週のハイライト」が伝わる魅力的なものに。
    2. 構成：導入、各ランの要約、写真への言及、3/15サブ4に向けた週間総評。
    3. 各日のAIコーチのコメントも踏まえつつ、週全体の成長や課題を抽出してください。
    """

    # 5. 生成と保存
    try:
        print("🤖 AIが週報を執筆中...")
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"✅ 完成しました！: {output_path}")
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    generate_weekly_note()