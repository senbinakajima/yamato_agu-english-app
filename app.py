import streamlit as st
import requests
import json
import random
import textwrap

# Page Configuration
st.set_page_config(
    page_title="AGU English Vocab - Notion API",
    page_icon="🎓",
    layout="centered"
)

# --- Custom CSS for Styling ---
st.markdown(
"""<style>
/* Styling for Streamlit layout */
.stApp {
background-color: #f4f6f3;
}
.main-header {
font-family: 'sans serif';
color: #004a23;
font-weight: 800;
text-align: center;
margin-top: 1rem;
margin-bottom: 0.5rem;
}
.sub-header {
font-size: 0.9rem;
color: #64748b;
text-align: center;
margin-bottom: 2rem;
}
.flashcard-box {
background-color: white;
border: 1px solid rgba(0, 74, 35, 0.1);
border-radius: 1.5rem;
padding: 2.5rem 1.5rem;
box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03);
margin-bottom: 2rem;
text-align: center;
min-height: 280px;
display: flex;
flex-direction: column;
justify-content: center;
align-items: center;
}
.word-text {
font-size: 2.8rem;
font-weight: 800;
color: #1a202c;
margin-bottom: 0.5rem;
word-break: break-all;
}
.pos-badge {
background-color: rgba(0, 74, 35, 0.1);
color: #004a23;
padding: 0.3rem 0.9rem;
border-radius: 0.5rem;
font-size: 0.85rem;
font-weight: 700;
margin-bottom: 1.5rem;
display: inline-block;
}
.theme-badge {
background-color: #f1f5f9;
color: #475569;
padding: 0.2rem 0.6rem;
border-radius: 0.35rem;
font-size: 0.75rem;
font-weight: 600;
margin-bottom: 1.5rem;
display: inline-block;
margin-left: 0.5rem;
}
.meaning-text {
font-size: 1.6rem;
font-weight: 700;
color: #004a23;
margin-top: 1rem;
margin-bottom: 1rem;
}
.example-box {
background-color: #fdfefe;
border-left: 4px solid #004a23;
padding: 1rem;
border-radius: 0.5rem;
text-align: left;
margin-top: 1.5rem;
width: 100%;
border-top: 1px solid #f1f5f9;
border-right: 1px solid #f1f5f9;
border-bottom: 1px solid #f1f5f9;
}
.example-label {
font-size: 0.75rem;
color: #94a3b8;
font-weight: 700;
text-transform: uppercase;
margin-bottom: 0.25rem;
}
.example-sentence {
font-size: 0.95rem;
font-weight: 600;
color: #334155;
line-height: 1.4;
}
.example-translation {
font-size: 0.85rem;
color: #64748b;
margin-top: 0.25rem;
}
.score-circle {
background-color: #e6f0ea;
color: #004a23;
border-radius: 50%;
width: 120px;
height: 120px;
display: flex;
flex-direction: column;
justify-content: center;
align-items: center;
margin: 1.5rem auto;
box-shadow: 0 4px 10px rgba(0, 74, 35, 0.05);
}
.score-value {
font-size: 2.2rem;
font-weight: 900;
line-height: 1;
}
.score-label {
font-size: 0.7rem;
font-weight: 700;
text-transform: uppercase;
letter-spacing: 1px;
}
.failed-item {
background-color: white;
border: 1px solid #fee2e2;
border-radius: 1rem;
padding: 1rem;
margin-bottom: 0.5rem;
box-shadow: 0 2px 5px rgba(0, 0, 0, 0.01);
}
</style>""",
    unsafe_allow_html=True
)

# --- Helper function for Rerun ---
def trigger_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

# --- Notion API integration functions ---
def fetch_words_from_notion(api_key, database_id):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    words = []
    for result in data.get("results", []):
        properties = result.get("properties", {})
        page_id = result.get("id")
        
        # Safe extraction helpers for various Notion property configurations
        def get_rich_text(prop_names):
            if isinstance(prop_names, str):
                prop_names = [prop_names]
            for name in prop_names:
                prop = properties.get(name, {})
                p_type = prop.get("type")
                if p_type == "rich_text":
                    text_list = prop.get("rich_text", [])
                    return "".join([t.get("text", {}).get("content", "") for t in text_list])
                elif p_type == "title":
                    title_list = prop.get("title", [])
                    return "".join([t.get("text", {}).get("content", "") for t in title_list])
                elif p_type == "select":
                    return prop.get("select", {}).get("name", "")
            return ""
            
        def get_number(prop_names):
            if isinstance(prop_names, str):
                prop_names = [prop_names]
            for name in prop_names:
                prop = properties.get(name, {})
                if prop.get("type") == "number":
                    val = prop.get("number")
                    return val if val is not None else 0
            return 0
            
        word_text = get_rich_text(["Word", "Name", "単語"])
        
        word = {
            "id": page_id,
            "word": word_text,
            "part_of_speech": get_rich_text(["PartOfSpeech", "品詞", "part_of_speech"]),
            "meaning": get_rich_text(["Meaning", "意味", "meaning"]),
            "example_sentence": get_rich_text(["Example", "例文", "example_sentence"]),
            "japanese_translation": get_rich_text(["ExampleTranslation", "例文の和訳", "japanese_translation"]),
            "correct_prop": "Correct" if "Correct" in properties else ("正解数" if "正解数" in properties else "Correct"),
            "incorrect_prop": "Incorrect" if "Incorrect" in properties else ("不正解数" if "不正解数" in properties else "Incorrect"),
            "correct_val": get_number(["Correct", "正解数"]),
            "incorrect_val": get_number(["Incorrect", "不正解数"])
        }
        if word["word"]: # Skip empty pages
            words.append(word)
            
    return words

def update_notion_stat(api_key, page_id, prop_name, current_val):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    url = f"https://api.notion.com/v1/pages/{page_id}"
    body = {
        "properties": {
            prop_name: {
                "number": int(current_val) + 1
            }
        }
    }
    response = requests.patch(url, headers=headers, json=body)
    response.raise_for_status()

# --- Fallback data if Notion API is unavailable ---
def fetch_fallback_words():
    try:
        with open("words.json", "r", encoding="utf-8") as f:
            words = json.load(f)
            # Standardize object attributes
            for w in words:
                w["correct_prop"] = "Correct"
                w["incorrect_prop"] = "Incorrect"
                w["correct_val"] = w.get("correct_val", 0)
                w["incorrect_val"] = w.get("incorrect_val", 0)
            return words
    except Exception as e:
        # Mini backup list if words.json is missing
        return [
            {
                "id": "fallback_1",
                "word": "achieve",
                "part_of_speech": "動",
                "meaning": "〜を達成する、成し遂げる",
                "example_sentence": "Scientists use AI to achieve a breakthrough in material discovery.",
                "japanese_translation": "科学者たちは材料発見における画期的な進歩を達成するためにAIを使用する。",
                "correct_prop": "Correct",
                "incorrect_prop": "Incorrect",
                "correct_val": 0,
                "incorrect_val": 0
            }
        ]

# --- Session State Initialization ---
if "screen" not in st.session_state:
    st.session_state.screen = "start"
if "session_words" not in st.session_state:
    st.session_state.session_words = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False
if "incorrect_words" not in st.session_state:
    st.session_state.incorrect_words = []
if "correct_count" not in st.session_state:
    st.session_state.correct_count = 0
if "api_mode" not in st.session_state:
    st.session_state.api_mode = False

# --- Notion Keys check ---
api_key = st.secrets.get("NOTION_API_KEY")
database_id = st.secrets.get("NOTION_DATABASE_ID")
has_secrets = bool(api_key and database_id)

# --- Screen Rendering Router ---

# 1. START SCREEN
if st.session_state.screen == "start":
    st.markdown('<h1 class="main-header">AGU English Vocab</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">青山学院大学スクールカラーテーマ Notion API同期版</p>', unsafe_allow_html=True)
    
    # Render Status Panel
    if has_secrets:
        st.success("Notion API 認証情報が検出されました。データベース同期モードで起動可能です。 🌐")
        st.session_state.api_mode = True
    else:
        st.warning("Notion API 認証情報が st.secrets に見つかりません。オフライン（words.json）モードで起動します。 📁")
        st.session_state.api_mode = False
        
    st.write("")
    
    # Start button (Centered layout)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("学習スタート (10問)", use_container_width=True, type="primary"):
            # Load words
            words_pool = []
            if st.session_state.api_mode:
                with st.spinner("Notionから単語を取得中..."):
                    try:
                        words_pool = fetch_words_from_notion(api_key, database_id)
                        if not words_pool:
                            st.error("Notionデータベースが空であるか、正しく読み込めませんでした。ローカルデータを使用します。")
                            words_pool = fetch_fallback_words()
                            st.session_state.api_mode = False
                    except Exception as e:
                        st.error(f"Notion接続エラー: {e}。ローカルデータにフォールバックします。")
                        words_pool = fetch_fallback_words()
                        st.session_state.api_mode = False
            else:
                words_pool = fetch_fallback_words()
            
            # Shuffle and select 10 words
            random.shuffle(words_pool)
            st.session_state.session_words = words_pool[:10]
            st.session_state.current_index = 0
            st.session_state.correct_count = 0
            st.session_state.incorrect_words = []
            st.session_state.show_answer = False
            st.session_state.screen = "learn"
            trigger_rerun()

# 2. LEARN SCREEN
elif st.session_state.screen == "learn":
    st.markdown('<h2 class="main-header">AGU Vocab Study</h2>', unsafe_allow_html=True)
    
    # Current progress
    total_words = len(st.session_state.session_words)
    curr_idx = st.session_state.current_index
    
    # Safe bounds check
    if curr_idx >= total_words:
        st.session_state.screen = "result"
        trigger_rerun()
        
    current_word = st.session_state.session_words[curr_idx]
    
    # Progress UI
    st.progress(curr_idx / total_words)
    st.markdown(f"<p style='text-align: right; font-size: 0.8rem; font-weight: bold; color: #64748b;'>{curr_idx + 1} / {total_words}</p>", unsafe_allow_html=True)
    
    # Render Flashcard
    if not st.session_state.show_answer:
        # Card Front
        part_of_speech_html = f'<span class="pos-badge">{current_word.get("part_of_speech", "動")}</span>' if current_word.get("part_of_speech") else ''
        theme_html = f'<span class="theme-badge">{current_word.get("theme", "General")}</span>' if current_word.get("theme") else ''
        
        st.markdown(
f"""<div class="flashcard-box">
<div>
{part_of_speech_html}
{theme_html}
</div>
<div class="word-text">{current_word["word"]}</div>
<div style="height: 40px;"></div>
</div>""",
            unsafe_allow_html=True
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("答えを見る", use_container_width=True, type="primary"):
                st.session_state.show_answer = True
                trigger_rerun()
                
    else:
        # Card Back
        part_of_speech_html = f'<span class="pos-badge">{current_word.get("part_of_speech", "動")}</span>' if current_word.get("part_of_speech") else ''
        theme_html = f'<span class="theme-badge">{current_word.get("theme", "General")}</span>' if current_word.get("theme") else ''
        
        # Check if collocation exists
        collocation_html = ''
        if current_word.get("collocation"):
            collocation_html = f'<div style="margin-top: 5px;"><span style="font-size: 0.8rem; background-color: #e6f0ea; color: #004a23; border: 1px solid rgba(0, 74, 35, 0.1); border-radius: 1rem; padding: 0.2rem 0.6rem; font-weight: bold;">{current_word["collocation"]}</span></div>'
            
        example_html = ''
        if current_word.get("example_sentence"):
            example_html = f"""
            <div class="example-box">
                <div class="example-label">Example Sentence</div>
                <div class="example-sentence">{current_word["example_sentence"]}</div>
                <div class="example-translation">{current_word.get("japanese_translation", "")}</div>
            </div>
            """
            
        st.markdown(
f"""<div class="flashcard-box">
<div>
{part_of_speech_html}
{theme_html}
</div>
<div style="font-size: 1.1rem; font-weight: bold; color: #64748b; margin-bottom: 0.2rem;">{current_word["word"]}</div>
<div class="meaning-text">{current_word["meaning"]}</div>
{collocation_html}
{example_html}
</div>""",
            unsafe_allow_html=True
        )
        
        # Self-Evaluation Buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("❌ 忘れていた", use_container_width=True):
                st.session_state.incorrect_words.append(current_word)
                
                # Send API update if online database mode
                if st.session_state.api_mode and current_word.get("id") and not current_word["id"].startswith("fallback"):
                    with st.spinner("Notionを更新中..."):
                        try:
                            update_notion_stat(api_key, current_word["id"], current_word["incorrect_prop"], current_word["incorrect_val"])
                        except Exception as e:
                            st.toast(f"Notion書き込みエラー: {e}")
                
                st.session_state.current_index += 1
                st.session_state.show_answer = False
                trigger_rerun()
                
        with col2:
            if st.button("⭕️ 覚えていた", use_container_width=True, type="primary"):
                st.session_state.correct_count += 1
                
                # Send API update if online database mode
                if st.session_state.api_mode and current_word.get("id") and not current_word["id"].startswith("fallback"):
                    with st.spinner("Notionを更新中..."):
                        try:
                            update_notion_stat(api_key, current_word["id"], current_word["correct_prop"], current_word["correct_val"])
                        except Exception as e:
                            st.toast(f"Notion書き込みエラー: {e}")
                            
                st.session_state.current_index += 1
                st.session_state.show_answer = False
                trigger_rerun()
                
    st.write("")
    st.write("")
    # Quit Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("学習を中断して戻る", use_container_width=True, key="btn-cancel"):
            st.session_state.screen = "start"
            trigger_rerun()

# 3. RESULT SCREEN
elif st.session_state.screen == "result":
    st.markdown('<h1 class="main-header">Result</h1>', unsafe_allow_html=True)
    
    total = len(st.session_state.session_words)
    correct = st.session_state.correct_count
    accuracy = round((correct / total) * 100) if total > 0 else 0
    
    # Animated score representation
    st.markdown(
f"""<div class="score-circle">
<div class="score-value">{accuracy}%</div>
<div class="score-label">Accuracy</div>
</div>
<p style="text-align: center; font-weight: bold; font-size: 1.1rem; color: #1a202c; margin-bottom: 2rem;">
{total}問中 {correct}問 正解
</p>""",
        unsafe_allow_html=True
    )
    
    # Renders different encouragement messages
    if accuracy == 100:
        st.balloons()
        st.success("完璧です！素晴らしい学習成果です！🎓")
    elif accuracy >= 80:
        st.success("優秀な成績です！この調子で続けましょう！🌟")
    elif accuracy >= 50:
        st.info("順調です。間違えた単語を復習して知識を定着させましょう！📖")
    else:
        st.warning("一歩ずつ！繰り返し復習することが記憶定着の近道です！🚀")
        
    # Failed words display
    st.write("")
    st.subheader("❌ 忘れていた単語リスト")
    
    if st.session_state.incorrect_words:
        for w in st.session_state.incorrect_words:
            part_of_speech_badge = f'<span style="background-color: #fee2e2; color: #991b1b; padding: 0.15rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: bold; margin-left: 0.5rem;">{w.get("part_of_speech", "")}</span>' if w.get("part_of_speech") else ''
            
            st.markdown(
f"""<div class="failed-item">
<div style="display: flex; align-items: center; justify-content: space-between;">
<span style="font-weight: 800; font-size: 1.1rem; color: #1e293b;">{w["word"]}</span>
<span>{part_of_speech_badge}</span>
</div>
<div style="font-size: 0.9rem; color: #004a23; font-weight: 700; margin-top: 0.25rem;">{w["meaning"]}</div>
{f'<div style="font-size: 0.8rem; color: #64748b; font-style: italic; margin-top: 0.4rem;">{w["example_sentence"]}</div>' if w.get("example_sentence") else ''}
</div>""",
                unsafe_allow_html=True
            )
    else:
        st.write("素晴らしい！間違えた単語はありません。")
        
    st.write("")
    st.write("")
    
    # Navigation Action Buttons
    col1, col2 = st.columns(2)
    with col1:
        # Enable retry failed button only if failed list is not empty
        retry_disabled = len(st.session_state.incorrect_words) == 0
        if st.button("間違えた単語だけもう一度", use_container_width=True, disabled=retry_disabled, type="primary"):
            st.session_state.session_words = st.session_state.incorrect_words.copy()
            random.shuffle(st.session_state.session_words)
            st.session_state.current_index = 0
            st.session_state.correct_count = 0
            st.session_state.incorrect_words = []
            st.session_state.show_answer = False
            st.session_state.screen = "learn"
            trigger_rerun()
            
    with col2:
        if st.button("ホームに戻る", use_container_width=True):
            st.session_state.screen = "start"
            trigger_rerun()
