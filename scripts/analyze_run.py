import os
import sys
import glob
from string import Template
import PIL.Image

# --- 新しいライブラリのインポート ---
from google import genai
from google.genai import types

# --- 設定 ---
API_KEY = os.getenv("GEMINI_API_KEY") 
# モデル名も環境変数から取る（設定なければ gemini-1.5-flash を使う）
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

TEMPLATE_PATH = "logs/template.md.tpl" 

if not API_KEY:
    print("❌ APIキーが設定されていません。export GEMINI_API_KEY='...' してください。")
    sys.exit(1)

# 新しいクライアントの初期化
client = genai.Client(api_key=API_KEY)

def analyze_images_and_create_md(image_dir, output_md_path, date_str, seq_num):
    # 1. 画像ファイルを集める
    image_paths = glob.glob(os.path.join(image_dir, "*"))
    valid_exts = ['.jpg', '.jpeg', '.png', '.webp', '.heic']
    
    # 画像パスリストと、AIに渡す画像オブジェクトリスト
    image_files_path = []
    image_objects = []

    identifier = f"{date_str}-{seq_num}"

    if not image_paths:
        print("⚠️ 画像が見つかりません。")
        return

    # 画像ファイル名順にソート
    image_paths.sort()
    
    # 画像タグ生成用リスト
    img_tags_list = []

    print(f"🤖 {len(image_paths)}枚の画像をAIで解析中...")

    for p in image_paths:
        if os.path.splitext(p)[1].lower() in valid_exts:
            image_files_path.append(p)
            fname = os.path.basename(p)
            
            # 1. MD用のタグを作る
            tag = f'<img src="../images/{identifier}/{fname}" width="400" loading="lazy" decoding="async" />'
            img_tags_list.append(tag)
            
            # 2. AI用の画像オブジェクトを作る (Pillowを使用)
            try:
                img = PIL.Image.open(p)
                image_objects.append(img)
            except Exception as e:
                print(f"⚠️ 画像読み込みスキップ: {p} ({e})")

    img_tags_str = "\n".join(img_tags_list)

    # 3. テンプレート読み込み
    try:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            tpl_content = f.read()
        
        src = Template(tpl_content)
        draft_content = src.safe_substitute({
            'DATE': date_str,
            'IDENTIFIER': identifier,
            'IMAGES': img_tags_str
        })
    except Exception as e:
        print(f"⚠️ テンプレート読み込みエラー: {e}")
        draft_content = f"Date: {date_str}\n\n{img_tags_str}"

    # 4. プロンプト作成
    prompt = f"""
    あなたはランニングデータの記録係です。
    以下に示すMarkdownテキストは、私のランニング日誌のテンプレート（下書き）です。
    添付した複数の画像を解析し、このテキストの空欄部分（「- 距離：」や「- 睡眠：」の右側など）を埋めて、
    **完成されたMarkdownテキストのみ**を出力してください。

    【ルール】
    1. **フォーマット厳守**: 提示されたテキストの構造、見出し、画像タグの位置などは絶対に変えないでください。空欄を埋めるだけです。
    2. **データ抽出**:
       - 画像内にある数値（距離、時間、心拍数、ペースなど）を正確に記入してください。
       - **「睡眠」**: 睡眠アプリのスクショがあれば、その時間やスコアを記入してください（なければ空欄）。
       - **「今日の目的」**: 画像内に「#ゆるラン」「ツキイチ」などの文字があればそれを採用してください。
       - **「天候」「時間帯」**: 写真の風景や開始時刻から推測してください。
       - **「コメント」**: ランニングの内容（負荷、VO2Maxの変化など）を要約して書いてください。
       - **「コーチコメント」**: データに基づいたフィードバック（「リカバリーが必要です」「良い傾向です」など）を書いてください。
    3. **出力**: Markdownコードブロックなどは不要です。中身のテキストだけを返してください。

    【対象のテキスト（下書き）】
    {draft_content}
    """

    # 5. AI生成実行 (新しい呼び出し方)
    try:
        # 画像とプロンプトをリストにして渡す
        response = client.models.generate_content(
            model=MODEL_NAME,  # ここを変数にする
            contents=[prompt, *image_objects]
        )
        
        ai_text = response.text
        
        # 整形
        ai_text = ai_text.replace("```markdown", "").replace("```", "").strip()

        # 書き出し
        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write(ai_text)
            
        print(f"✅ AI作成完了！ {output_md_path} にデータを埋め込みました。")
        
    except Exception as e:
        print(f"❌ AI生成エラー: {e}")
        # ファイルが空だと困るので、最低限テンプレート内容で保存
        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write(draft_content)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python analyze_run.py <img_dir> <md_path> <date> <seq>")
        sys.exit(1)
        
    analyze_images_and_create_md(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])