import os
import sys
import glob
from string import Template
import PIL.Image

# --- ライブラリのインポート ---
from google import genai
from google.genai import types

# --- 設定 ---
API_KEY = os.getenv("GEMINI_API_KEY") 
# モデル名を最新版に固定、または環境変数から取得
MODEL_NAME = "gemini-2.5-flash" 

# クライアント初期化（オプションなしのシンプル版でOK）
client = genai.Client(api_key=API_KEY)


TEMPLATE_PATH = "logs/template.md.tpl" 

if not API_KEY:
    print("❌ APIキーが設定されていません。export GEMINI_API_KEY='...' してください。")
    sys.exit(1)

# クライアントの初期化
#　client = genai.Client(api_key=API_KEY, http_options={'api_version': 'v1'})

def analyze_images_and_create_md(image_dir, output_md_path, date_str, seq_num):
    # 1. 画像ファイルを集める
    image_paths = glob.glob(os.path.join(image_dir, "*"))
    valid_exts = ['.jpg', '.jpeg', '.png', '.webp', '.heic']
    
    image_objects = []
    identifier = f"{date_str}-{seq_num}"

    if not image_paths:
        print("⚠️ 画像が見つかりません。")
        return

    image_paths.sort()
    img_tags_list = []

    print(f"🤖 {len(image_paths)}枚の画像をAIで解析中...")

    for p in image_paths:
        if os.path.splitext(p)[1].lower() in valid_exts:
            fname = os.path.basename(p)
            tag = f'<img src="../images/{identifier}/{fname}" width="400" loading="lazy" decoding="async" />'
            img_tags_list.append(tag)
            
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

    # --- ★追加ロジック：シューズ名やメモを環境変数から取得 ---
    # LINEボット化を見据え、一言メッセージを反映できるようにします
    USER_MEMO = os.getenv("RUN_MEMO", "（特になし）")

    # 4. プロンプト作成（外界情報・コーチング・シューズ対応版）
    prompt = f"""
    あなたはMASA専用のランニング・エージェント「Gemini」です。
    外界情報（天候・大会情報）と画像解析に強みを持ちます。

    【ミッション】
    提示されたテンプレートの空欄を埋めて、完成されたMarkdownのみを出力してください。

    【入力情報】
    - ユーザーからのメモ: {USER_MEMO}
    - 目標: 3/15 板橋シティマラソンでサブ4達成
    - 次のレース: 2/15 青梅マラソン(30km)

    【解析・記入ルール】
    1. **データ抽出**: 画像内の距離、時間、心拍数、ピッチ、睡眠データを正確に抜いてください。
    2. **使用シューズ**: メモ「{USER_MEMO}」にシューズ名があれば、必ず「- 使用シューズ：」の右側にその名前を記入してください。
    3. **天候・外界情報**: 写真の明るさや影、時刻から「天候」を推測し、当時の気温や風の状況もプロランニングコーチの視点で推測して補足してください。
    4. **コメント**: 走行データ（心拍数や負荷）から、身体へのダメージやVO2Maxの傾向を分析してください。
    5. **コーチコメント**: 外界コンディション（寒さ、風など）とサブ4目標を照らし合わせ、具体的にアドバイスしてください。「論理的な分析」は別エージェント(ChatGPT)が担当するため、あなたは「客観的状況と最新データに基づくフィードバック」に集中してください。

    【対象のテキスト】
    {draft_content}
    """

    # 5. AI生成実行
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt, *image_objects]
        )
        
        ai_text = response.text
        ai_text = ai_text.replace("```markdown", "").replace("```", "").strip()

        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write(ai_text)
            
        print(f"✅ AI作成完了！ {output_md_path}")
        
    except Exception as e:
        print(f"❌ AI生成エラー: {e}")
        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write(draft_content)
        sys.exit(1)

if __name__ == "__main__":
    analyze_images_and_create_md(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])