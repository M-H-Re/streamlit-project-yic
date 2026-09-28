import base64
import json
import os
import time
from openai import OpenAI
import streamlit as st

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & STATIC WARM THEME
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="The Bard's Play",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    html, body, .stApp {
        background-color: #FAF6EE !important;
        color: #2D122D !important;
        font-family: 'Georgia', serif;
        overflow-x: hidden;
    }
    
    [data-testid="stHeader"], .main .block-container {
        background-color: #FAF6EE !important;
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
    }
    
    .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp span, .stApp label {
        color: #2D122D !important;
    }
    
    div[data-testid="stVideo"] {
        box-shadow: 0px 0px 20px rgba(45, 18, 45, 0.15) !important;
        border-radius: 12px;
    }

    .hero-title {
        color: #2D122D;
        font-size: 3.5rem;
        font-weight: bold;
        text-align: center;
        margin-top: 0.5rem;
    }
    .hero-subtitle {
        color: #6B4E71;
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 1.8rem;
        font-style: italic;
    }
    
    div.stButton > button[key="btn_start_play"] {
        background-color: #2D122D !important;
        color: #FAF6EE !important;
        font-size: 1.6rem !important;
        padding: 0.8rem 3rem !important;
        border-radius: 35px !important;
        border: 2px solid #D4A373 !important;
        display: block !important;
        margin: 0 auto !important;
        transition: all 0.3s ease;
        box-shadow: 0 6px 15px rgba(45, 18, 45, 0.2);
    }
    div.stButton > button[key="btn_start_play"]:hover {
        background-color: #4A234A !important;
        color: #FFECB3 !important;
        transform: scale(1.05);
    }
    
    .play-card {
        background-color: #FFFDF9;
        border: 2px solid #E8DCC4;
        border-radius: 10px;
        padding: 10px 12px;
        text-align: center;
        box-shadow: 0 3px 8px rgba(0,0,0,0.04);
        margin-bottom: 6px;
        height: 175px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .play-card h3 {
        color: #2D122D !important;
        font-size: 1.15rem !important;
        margin-top: 4px !important;
        margin-bottom: 4px !important;
    }
    .play-card p {
        color: #7A6263 !important;
        font-size: 0.85rem !important;
        margin-bottom: 0px !important;
        line-height: 1.2;
    }
    .play-card img {
        width: 55px;
        height: 55px;
        object-fit: contain;
        margin-bottom: 4px;
    }

    .stage-question-text {
        font-size: 1.15rem !important;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .stage-challenge-prompt {
        font-size: 1.15rem !important;
        font-weight: 500;
        line-height: 1.3;
    }
    div[data-testid="stMarkdownContainer"] p {
        font-size: 1.05rem;
    }
    div[data-widget="stRadio"] label p {
        font-size: 1.1rem !important;
        font-weight: bold;
    }

    div[data-testid="stModal"] > div:first-child {
        background-color: rgba(0, 0, 0, 0.55) !important;
        backdrop-filter: blur(2px);
    }
    div[data-testid="stModal"] [role="dialog"] {
        max-width: 550px !important;
        border: 2px solid #D4A373;
        border-radius: 16px;
        background-color: #2D122D;
        color: #FAF6EE;
        box-shadow: 0px 8px 25px rgba(0,0,0,0.5);
    }
    </style>
""",
    unsafe_allow_html=True,
)


def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            return f"data:image/jpeg;base64,{encoded}"
    return ""


@st.cache_resource
def get_client():
    return OpenAI(
        api_key=st.secrets["API_KEY"], base_url=st.secrets.get("BASE_URL", None)
    )


client = get_client()
CANDIDATE_MODELS = ["assistant-base"]

# -----------------------------------------------------------------------------
# ACHIEVEMENTS DEFINITION & UNLOCK ENGINE
# -----------------------------------------------------------------------------
ACHIEVEMENTS_LIST = {
    "sharp_eye": {
        "title": "🔍 Sharp Eye",
        "desc": "Solved the Ukulele challenge without taking any hints.",
    },
    "curious_mind": {
        "title": "💡 Curious Mind",
        "desc": "Used a hint to solve the mystery instrument challenge.",
    },
    "playwright": {
        "title": "🎭 Master Playwright",
        "desc": "Counseled Juliet and guided her decision with AI.",
    },
    "story_explorer": {
        "title": "🧭 Story Explorer",
        "desc": "Discovered all 3 main story branches (Accept, Refuse, Flee).",
    },
    "voice_actor": {
        "title": "🗣️ Vocal Virtuoso",
        "desc": "Used voice dictation to speak directly to the characters.",
    },
}


def unlock_achievement(achievement_id):
    """Triggers a Steam-style popup banner if the achievement hasn't been unlocked yet."""
    if "unlocked_achievements" not in st.session_state:
        st.session_state.unlocked_achievements = []

    if achievement_id not in st.session_state.unlocked_achievements:
        st.session_state.unlocked_achievements.append(achievement_id)
        ach = ACHIEVEMENTS_LIST[achievement_id]

        # 🏆 Steam-style Pop-up Toast
        st.toast(
            f"**Achievement Unlocked!**\n\n**{ach['title']}** - {ach['desc']}",
            icon="🏆",
        )


# -----------------------------------------------------------------------------
# CORE AI FUNCTIONS FOR SOCRATIC INTERACTION & ROUTING
# -----------------------------------------------------------------------------
def get_fast_ai_response(prompt):
    for model_name in CANDIDATE_MODELS:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content
        except Exception:
            continue
    return (
        "That doesn't look quite right! Take another close look and try guessing"
        " again."
    )


def evaluate_initial_suggestion(actor_name, predicament, initial_answer):
    system_prompt = f"""
    You are an interactive AI actor playing {actor_name} in a live theater play for children.
    Predicament: "{predicament}"
    
    TASK:
    1. Read the child's suggestion: "{initial_answer}"
    2. Determine if the suggestion is RELEVANT/REALISTIC to the story or UNREALISTIC/OFF-TOPIC.
    3. Generate 'actor_response':
       - If RELEVANT: React warmly in 1 short sentence, then ask WHY they think that is the best path.
       - If UNREALISTIC/OFF-TOPIC: Make a lighthearted, in-character reaction showing why that isn't possible in Verona, then ask what else {actor_name} should do.
    
    Keep 'actor_response' under 25 words. Do not use emojis, stage directions, or parentheticals.

    Return ONLY a JSON object:
    {{"is_relevant": boolean, "actor_response": string}}
    """
    try:
        response = client.chat.completions.create(
            model=CANDIDATE_MODELS[0],
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.5,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {
            "is_relevant": True,
            "actor_response": (
                f"That is an interesting thought! Why do you feel that is the best"
                f" path for {actor_name}?"
            ),
        }


def evaluate_child_reasoning(
    actor_name, predicament, initial_answer, explanation, branches
):
    branches_formatted = json.dumps(branches, indent=2)
    system_prompt = f"""
    You are an interactive AI actor playing {actor_name} in a play with ONLY 3 fixed video paths:
    1. 'scene_2_accept' (Juliet accepts Romeo's proposal / pledges love / agrees to marriage or peace)
    2. 'scene_3_refuse' (Juliet stays behind, refuses, or hesitates without fleeing)
    3. 'scene_7_run_away' (Romeo runs away, flees, leaves Verona, OR Juliet asks/tells Romeo to go away / flee for safety)

    YOUR TASK:
    1. Read the child's suggestion and explanation.
    2. Determine which of the 3 paths ('scene_2_accept', 'scene_3_refuse', OR 'scene_7_run_away') their idea leans closer toward.
       - IF the idea mentions Romeo leaving, escaping, running away, or Juliet urging Romeo to go away/leave: MATCH 'scene_7_run_away'.
    3. Set 'matched_scene' to that key.
    4. Write a UNIQUE 1-2 sentence response as 'actor_comment' that FIRST validates their specific reason, and SECOND seamlessly bridges their idea into that video path (max 30 words).

    Keep 'actor_comment' free of emojis or stage directions so it can be spoken clearly.

    Return ONLY a JSON object:
    {{"matched_scene": string, "actor_comment": string}}
    """

    user_prompt = f"""
    Predicament: "{predicament}"
    Child's Suggestion: "{initial_answer}"
    Child's Explanation: "{explanation}"

    Available Video Branches:
    {branches_formatted}
    """

    try:
        response = client.chat.completions.create(
            model=CANDIDATE_MODELS[0],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {
            "matched_scene": "scene_2_accept",
            "actor_comment": (
                "Your wisdom gives me courage! I shall trust in love and give my"
                " answer to Romeo!"
            ),
        }


def render_voice_button(status_id="speech-status", button_id="mic-toggle-btn"):
    # Render component and handle speech detection state toggle
    voice_captured = st.components.v1.html(
        f"""
        <script>
        var recognition = null;
        var isListening = false;
        var fullTranscript = "";

        function toggleDictation() {{
            var btn = document.getElementById('{button_id}');
            var status = document.getElementById('{status_id}');

            if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {{
                alert("Voice Recognition is not supported in this browser. Try Google Chrome or Edge.");
                return;
            }}

            var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

            if (!isListening) {{
                recognition = new SpeechRecognition();
                recognition.continuous = true;
                recognition.interimResults = true;
                recognition.lang = "en-US";
                fullTranscript = "";

                recognition.onstart = function() {{
                    isListening = true;
                    btn.innerText = "🛑 Stop Listening";
                    btn.style.backgroundColor = "#D32F2F";
                    status.innerText = "🎙️ Listening continuously... Speak now!";
                }};

                recognition.onresult = function(e) {{
                    var currentText = "";
                    for (var i = e.resultIndex; i < e.results.length; ++i) {{
                        currentText += e.results[i][0].transcript;
                    }}
                    fullTranscript = currentText;
                }};

                recognition.onerror = function(e) {{
                    status.innerText = "⚠️ Voice error. Try again.";
                    stopListening();
                }};

                recognition.onend = function() {{
                    if (isListening) {{
                        try {{ recognition.start(); }} catch(err) {{}}
                    }}
                }};

                recognition.start();

            }} else {{
                stopListening();
            }}

            function stopListening() {{
                isListening = false;
                if (recognition) {{
                    recognition.onend = null;
                    recognition.stop();
                }}
                
                btn.innerText = "🎙️ Start Voice Input";
                btn.style.backgroundColor = "#FF4B4B";
                status.innerText = fullTranscript ? "✅ Captured!" : "Click button to start talking";

                if (fullTranscript.trim().length > 0) {{
                    var inputs = window.parent.document.querySelectorAll('input[type="text"]');
                    if (inputs.length > 0) {{
                        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                        nativeInputValueSetter.call(inputs[0], fullTranscript);

                        inputs[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                        inputs[0].dispatchEvent(new Event('change', {{ bubbles: true }}));
                        inputs[0].dispatchEvent(new Event('blur', {{ bubbles: true }}));
                    }}
                }}
            }}
        }}
        </script>
        <div style="display: flex; align-items: center; gap: 10px; font-family: sans-serif; margin-bottom: 5px;">
            <button id="{button_id}" type="button" onclick="toggleDictation()" style="
                background-color: #FF4B4B;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: bold;
                cursor: pointer;
                transition: background-color 0.2s ease;
            ">🎙️ Start Voice Input</button>
            <span id="{status_id}" style="color: #FAF6EE; font-size: 0.85rem;">Click button to start talking</span>
        </div>
        """,
        height=45,
    )


# -----------------------------------------------------------------------------
# OVERLAY DIALOG MODAL (AI REVIEW WITH VOICE CONTROL)
# -----------------------------------------------------------------------------
@st.dialog("🎭 AI Actor Socratic Workshop", width="small")
def render_ai_dialogue_overlay():
    st.caption(f'Predicament: "{PREDICAMENT}"')

    if st.session_state.ai_step == 1:
        st.subheader(f"Step 1: What should {ACTOR_NAME} do?")
        if st.session_state.redirect_message:
            st.warning(f'🎭 **{ACTOR_NAME}:** "{st.session_state.redirect_message}"')

        render_voice_button("status_step_1", "mic_btn_step_1")

        # Track if voice mode toggle was clicked in step 1
        use_voice_toggle = st.checkbox("🎙️ Using Voice Input Mode", value=st.session_state.used_voice, key="cb_voice_step1")
        if use_voice_toggle:
            st.session_state.used_voice = True

        with st.form("suggestion_form", clear_on_submit=False):
            user_sugg = st.text_input(
                "Your suggestion:", placeholder="Click mic above or type here..."
            )
            submitted_sugg = st.form_submit_button("Send Suggestion", type="primary")

            if submitted_sugg:
                if not user_sugg.strip():
                    st.error("Please enter a suggestion before submitting.")
                else:
                    # 🏆 Check for Vocal Virtuoso trigger
                    if st.session_state.used_voice:
                        unlock_achievement("voice_actor")

                    with st.spinner(f"{ACTOR_NAME} is processing your suggestion..."):
                        eval_res = evaluate_initial_suggestion(
                            ACTOR_NAME, PREDICAMENT, user_sugg.strip()
                        )
                        if eval_res.get("is_relevant", True):
                            st.session_state.initial_suggestion = user_sugg.strip()
                            st.session_state.followup_question = eval_res["actor_response"]
                            st.session_state.redirect_message = ""
                            st.session_state.ai_step = 2
                            st.rerun()
                        else:
                            st.session_state.redirect_message = eval_res["actor_response"]
                            st.rerun()

    elif st.session_state.ai_step == 2:
        st.subheader("Step 2: Explain Your Reasoning")
        st.success(f'**Your Suggestion:** "{st.session_state.initial_suggestion}"')
        st.info(f'🎭 **{ACTOR_NAME} asks:** "{st.session_state.followup_question}"')

        if st.session_state.ai_review_result is None:
            render_voice_button("status_step_2", "mic_btn_step_2")

            # Track if voice mode toggle was clicked in step 2
            use_voice_toggle = st.checkbox("🎙️ Using Voice Input Mode", value=st.session_state.used_voice, key="cb_voice_step2")
            if use_voice_toggle:
                st.session_state.used_voice = True

            with st.form("reason_form", clear_on_submit=False):
                user_reason = st.text_input(
                    "Your reason:", placeholder="Click mic above or type here..."
                )
                submitted_reason = st.form_submit_button("Submit Reason", type="primary")

                if submitted_reason:
                    if not user_reason.strip():
                        st.error("Please explain your reasoning before submitting.")
                    else:
                        # 🏆 Check for Vocal Virtuoso trigger
                        if st.session_state.used_voice:
                            unlock_achievement("voice_actor")

                        with st.spinner(f"{ACTOR_NAME} is evaluating your path..."):
                            result = evaluate_child_reasoning(
                                ACTOR_NAME,
                                PREDICAMENT,
                                st.session_state.initial_suggestion,
                                user_reason.strip(),
                                CORE_BRANCHES,
                            )
                            st.session_state.ai_review_result = result
                            # 🏆 Unlock Playwright Achievement
                            unlock_achievement("playwright")
                            st.rerun()

        else:
            result = st.session_state.ai_review_result
            actor_comment = result.get("actor_comment", "")
            matched_scene = result.get("matched_scene", "scene_2_accept")

            st.success(f'🎭 **{ACTOR_NAME}:** "{actor_comment}"')
            st.write("")
            if st.button("Proceed to Scene 🎬", type="primary", use_container_width=True):
                st.session_state.current_scene_id = matched_scene
                st.session_state.video_finished = False
                st.session_state.show_overlay = False
                reset_ai_state()
                st.rerun()


# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION & ACHIEVEMENT GALLERY
# -----------------------------------------------------------------------------
def render_scene_sidebar():
    """Renders the scene map and unlocked Steam-style achievement badges."""
    if "unlocked_scenes" not in st.session_state:
        st.session_state.unlocked_scenes = ["scene_1_genesis"]
    if "unlocked_achievements" not in st.session_state:
        st.session_state.unlocked_achievements = []

    current_id = st.session_state.current_scene_id
    if current_id not in st.session_state.unlocked_scenes:
        st.session_state.unlocked_scenes.append(current_id)

    # Check if all 3 branches have been explored
    branches = ["scene_2_accept", "scene_3_refuse", "scene_7_run_away"]
    if all(b in st.session_state.unlocked_scenes for b in branches):
        unlock_achievement("story_explorer")

    with st.sidebar:
        st.header("🗺️ Scene Map")
        st.caption("Click any unlocked scene to revisit:")

        for scene_key in st.session_state.unlocked_scenes:
            if scene_key in SCENES:
                scene_info = SCENES[scene_key]
                scene_title = scene_info.get("title", scene_key)

                is_current = scene_key == current_id
                btn_label = f"📍 {scene_title}" if is_current else f"🎬 {scene_title}"

                if st.button(
                    btn_label,
                    key=f"sidebar_nav_{scene_key}",
                    use_container_width=True,
                    type="primary" if is_current else "secondary",
                ):
                    st.session_state.current_scene_id = scene_key
                    st.session_state.video_finished = False
                    st.session_state.show_overlay = False
                    reset_ai_state()
                    st.rerun()

        st.markdown("---")

        # 🏆 STAGE BADGES / ACHIEVEMENTS GALLERY
        st.header("🏆 Stage Badges")
        for ach_id, ach_info in ACHIEVEMENTS_LIST.items():
            if ach_id in st.session_state.unlocked_achievements:
                st.markdown(
                    f"✅ **{ach_info['title']}**  \n"
                    f"<span style='font-size:0.8rem; color:#4B6B38;'>{ach_info['desc']}</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"🔒 **<span style='color:#888;'>{ach_info['title']}</span>**  \n"
                    f"<span style='font-size:0.8rem; color:#999;'>Locked</span>",
                    unsafe_allow_html=True,
                )

        st.markdown("---")

        if st.button("🔄 Reset Story Progress", use_container_width=True):
            st.session_state.unlocked_scenes = ["scene_1_genesis"]
            st.session_state.unlocked_achievements = []
            st.session_state.used_voice = False
            st.session_state.current_scene_id = "scene_1_genesis"
            st.session_state.video_finished = False
            st.session_state.show_overlay = False
            st.session_state.hint_count = 0
            reset_ai_state()
            st.toast("Progress reset!", icon="🧹")
            st.rerun()


# -----------------------------------------------------------------------------
# SCENE DATA DEFINITIONS
# -----------------------------------------------------------------------------
ACTOR_NAME = "Juliet"
PREDICAMENT = (
    "Romeo has declared his love and proposed to me, but our families are bitter"
    " enemies! How should I respond?"
)

CORE_BRANCHES = {
    "scene_2_accept": {
        "title": "Branch A: Juliet Accepts & Pledges Love",
        "intent": "Accept Romeo's proposal, marry secretly, trust in love, or make peace.",
    },
    "scene_3_refuse": {
        "title": "Branch B: Juliet Refuses / Steps Back",
        "intent": "Refuse proposal, hesitate, stay safe, or avoid danger with the families.",
    },
    "scene_7_run_away": {
        "title": "Branch C: Flee / Ask Romeo to Go Away",
        "intent": "Romeo runs away, flees Verona, OR Juliet tells/asks Romeo to go away or escape to stay safe.",
    },
}

SCENES = {
    "scene_1_genesis": {
        "type": "ai_dialogue",
        "title": "Scene 1: Counsel Juliet",
        "video_url": "videos/genesis.mp4",
    },
    "scene_2_accept": {
        "type": "branching",
        "title": "Scene 2A: The Betrothal",
        "video_url": "videos/accept.mp4",
        "question": "With vows exchanged, where should the lovers go next?",
        "choices": {
            "Option A: Seek Friar Laurence's help": {
                "route": "scene_4_question",
                "transition_text": "They decide to visit Friar Laurence to arrange a secret ceremony...",
            },
            "Option B: Return to the courtyard": {
                "route": "scene_4_question",
                "transition_text": "They step down into the quiet courtyard...",
            },
        },
    },
    "scene_3_refuse": {
        "type": "branching",
        "title": "Scene 2B: Hearts Divided",
        "video_url": "videos/refuse.mp4",
        "question": "Romeo is heartbroken. What happens next?",
        "choices": {
            "Option A: Look around the room for comfort": {
                "route": "scene_4_question",
                "transition_text": "Juliet steps back into her chamber, looking around...",
            },
            "Option B: Search for a musical token": {
                "route": "scene_4_question",
                "transition_text": "Searching for solace, she turns toward the corner of the room...",
            },
        },
    },
    "scene_7_run_away": {
        "type": "branching",
        "title": "Scene 2C: Flight into the Shadows",
        "video_url": "videos/go_away.mp4",
        "question": "Romeo must flee the guards! Where should he seek refuge?",
        "choices": {
            "Option A: Escape through the city gates": {
                "route": "scene_4_question",
                "transition_text": "Romeo rushes into the night toward the gates of Verona...",
            },
            "Option B: Hide in the church courtyard": {
                "route": "scene_4_question",
                "transition_text": "Romeo slips quietly into the shadowy courtyard...",
            },
        },
    },
    "scene_4_question": {
        "type": "interactive_challenge",
        "title": "Scene 3: The Hidden Instrument",
        "video_url": "videos/question.mp4",
        "prompt_question": (
            "Halt! An unusual four-stringed instrument is resting in the room."
            " What is it called?"
        ),
        "target_answer": "UKULELE",
        "character_name": "Narrator",
        "next_scene": "scene_5_answer",
    },
    "scene_5_answer": {
        "type": "branching",
        "title": "Scene 4: Object Revealed",
        "video_url": "videos/answer.mp4",
        "question": "The mystery instrument is revealed! What would you like to do now?",
        "choices": {
            "Option A: Proceed to final decision": {
                "route": "scene_6_ai_dialogue",
                "transition_text": "Moving to the final choice of the story...",
            }
        },
    },
    "scene_6_ai_dialogue": {
        "type": "branching",
        "title": "Scene 5: Romeo's Proposal",
        "video_url": "videos/genesis.mp4",
        "question": "Romeo proposes marriage to Juliet! How should Juliet respond?",
        "choices": {
            "Option A: Accept Romeo's proposal": {
                "route": "scene_2_accept",
                "transition_text": "Juliet's heart fills with joy as she accepts Romeo's pledge of love...",
            },
            "Option B: Refuse the proposal": {
                "route": "scene_3_refuse",
                "transition_text": "A sudden shadow falls over the balcony as Juliet hesitates and refuses...",
            },
            "Option C: Urge Romeo to flee for safety": {
                "route": "scene_7_run_away",
                "transition_text": "Fearing for his life, Juliet asks Romeo to leave immediately...",
            },
        },
    },
}

# --- State Management ---
if "page" not in st.session_state:
    st.session_state.page = "main"
if "selected_play" not in st.session_state:
    st.session_state.selected_play = None
if "current_scene_id" not in st.session_state:
    st.session_state.current_scene_id = "scene_1_genesis"
if "unlocked_scenes" not in st.session_state:
    st.session_state.unlocked_scenes = ["scene_1_genesis"]
if "video_finished" not in st.session_state:
    st.session_state.video_finished = False
if "show_overlay" not in st.session_state:
    st.session_state.show_overlay = False
if "hint_count" not in st.session_state:
    st.session_state.hint_count = 0
if "used_voice" not in st.session_state:
    st.session_state.used_voice = False

if "ai_step" not in st.session_state:
    st.session_state.ai_step = 1
if "initial_suggestion" not in st.session_state:
    st.session_state.initial_suggestion = ""
if "followup_question" not in st.session_state:
    st.session_state.followup_question = ""
if "redirect_message" not in st.session_state:
    st.session_state.redirect_message = ""
if "ai_review_result" not in st.session_state:
    st.session_state.ai_review_result = None


def reset_ai_state():
    st.session_state.ai_step = 1
    st.session_state.initial_suggestion = ""
    st.session_state.followup_question = ""
    st.session_state.redirect_message = ""
    st.session_state.ai_review_result = None


# -----------------------------------------------------------------------------
# PAGE ROUTING & VIEWS
# -----------------------------------------------------------------------------

# --- VIEW 1: MAIN HERO PAGE ---
if st.session_state.page == "main":
    st.markdown("<div style='height: 8vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='hero-title'>The Bard's Play</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='hero-subtitle'>Step into the world of interactive drama and classic storytelling.</p>",
        unsafe_allow_html=True,
    )

    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        if st.button("Play 🎭", key="btn_start_play", use_container_width=True):
            st.session_state.page = "gallery"
            st.rerun()

# --- VIEW 2: PLAY GALLERY ---
elif st.session_state.page == "gallery":
    top_col1, top_col2 = st.columns([5, 1])
    with top_col1:
        st.markdown("<h2 style='margin:0;'>🎭 The Bard's Play Gallery</h2>", unsafe_allow_html=True)
    with top_col2:
        if st.button("← Back Home"):
            st.session_state.page = "main"
            st.rerun()

    st.caption("Select a play block below to launch the interactive stage.")

    plays = [
        {
            "id": "romeo_juliet",
            "title": "Romeo & Juliet",
            "desc": "A classic tale of star-crossed lovers.",
            "image": "images/romeo_juliet.jpg",
        },
        {
            "id": "macbeth",
            "title": "Macbeth",
            "desc": "A journey into ambition and tragedy.",
            "image": "images/macbeth.jpg",
        },
        {
            "id": "hamlet",
            "title": "Hamlet",
            "desc": "Revenge and destiny in Denmark.",
            "image": "images/hamlet.jpg",
        },
        {
            "id": "julius_caesar",
            "title": "Julius Caesar",
            "desc": "Political intrigue and betrayal in Rome.",
            "image": "images/julius_caesar.jpg",
        },
        {
            "id": "sang_kancil",
            "title": "Sang Kancil dan Buaya",
            "desc": "A clever mouse-deer outsmarts crocodiles.",
            "image": "images/sang_kancil.jpg",
        },
    ]

    cols = st.columns(5)
    for idx, p in enumerate(plays):
        img_src = get_image_base64(p["image"])
        img_html = f'<img src="{img_src}" alt="{p["title"]} Logo" />' if img_src else ''

        with cols[idx]:
            st.markdown(
                f"""
            <div class="play-card">
                {img_html}
                <h3>{p['title']}</h3>
                <p>{p['desc']}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
            if st.button("🎬 Launch", key=p["id"], use_container_width=True):
                st.session_state.selected_play = p["id"]
                st.session_state.page = "stage"
                st.rerun()

# --- VIEW 3: INTERACTIVE STAGE ---
elif st.session_state.page == "stage":

    render_scene_sidebar()

    if st.button("← Back to Gallery"):
        st.session_state.page = "gallery"
        st.session_state.current_scene_id = "scene_1_genesis"
        st.session_state.unlocked_scenes = ["scene_1_genesis"]
        st.session_state.video_finished = False
        st.session_state.show_overlay = False
        reset_ai_state()
        st.rerun()

    if st.session_state.selected_play == "romeo_juliet":
        current_scene = SCENES[st.session_state.current_scene_id]

        st.title(current_scene["title"])

        v_col1, v_col2 = st.columns([7, 3])

        with v_col1:
            st.video(current_scene["video_url"], autoplay=True)

        with v_col2:
            if not st.session_state.video_finished:
                st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
                if st.button("Proceed ➡️", key="btn_proceed_right", use_container_width=True, type="primary"):
                    st.session_state.video_finished = True
                    if current_scene["type"] == "ai_dialogue":
                        st.session_state.show_overlay = True
                    st.rerun()

            else:
                if current_scene["type"] == "branching":
                    st.subheader("Make Your Decision")
                    st.markdown(
                        f'<p class="stage-question-text"><strong>Question:</strong> {current_scene["question"]}</p>',
                        unsafe_allow_html=True,
                    )

                    choice_options = list(current_scene["choices"].keys())
                    selected_choice_key = st.radio(
                        "Select your path:",
                        choice_options,
                        key=st.session_state.current_scene_id,
                    )

                    if st.button("Confirm Choice", type="primary", use_container_width=True):
                        selected = current_scene["choices"][selected_choice_key]
                        st.info(f"**Narrator:** {selected['transition_text']}")
                        time.sleep(1.5)

                        st.session_state.current_scene_id = selected["route"]
                        st.session_state.video_finished = False
                        st.session_state.hint_count = 0
                        st.rerun()

                elif current_scene["type"] == "interactive_challenge":
                    st.subheader("Interactive Challenge")
                    st.markdown(f"**{current_scene['character_name']} asks:**")
                    st.markdown(
                        f'<div class="stage-challenge-prompt">"{current_scene["prompt_question"]}"</div>',
                        unsafe_allow_html=True,
                    )

                    target = current_scene["target_answer"].upper()
                    revealed_letters = st.session_state.hint_count

                    masked_word = " ".join([
                        char if idx < revealed_letters else "_"
                        for idx, char in enumerate(target)
                    ])
                    st.markdown(f"### Hint: `{masked_word}`")

                    if revealed_letters < len(target):
                        if st.button("💡 Need a Hint?"):
                            st.session_state.hint_count += 1
                            st.rerun()

                    user_guess = st.text_input("Type your answer:").strip()

                    if st.button("Submit Answer", type="primary", use_container_width=True):
                        if user_guess.upper() == target:
                            # 🏆 Check achievement criteria on correct answer
                            if st.session_state.hint_count == 0:
                                unlock_achievement("sharp_eye")
                            else:
                                unlock_achievement("curious_mind")

                            st.success(f"🎉 Correct! The answer is {target}.")
                            time.sleep(1.5)
                            st.session_state.current_scene_id = current_scene["next_scene"]
                            st.session_state.video_finished = False
                            st.session_state.hint_count = 0
                            st.rerun()
                        else:
                            with st.spinner("Preparing response..."):
                                correction_prompt = f"""
                                Character: {current_scene['character_name']}
                                Target Answer: {target}
                                Child's Wrong Guess: "{user_guess}"
                                Respond in 1 short sentence as the character gently telling the child "{user_guess}" is incorrect and encouraging them to try again. Max 12 words.
                                """
                                correction = get_fast_ai_response(correction_prompt)

                            st.error(f"❌ Incorrect: '{user_guess}'")
                            st.warning(f"**{current_scene['character_name']}:** {correction}")

                            if st.session_state.hint_count < len(target):
                                st.session_state.hint_count += 1

                elif current_scene["type"] == "ai_dialogue":
                    st.subheader("Interactive Dialogue")
                    if st.button(
                        f"💬 Direct {ACTOR_NAME} (Give Opinion)",
                        use_container_width=True,
                        type="primary",
                    ):
                        st.session_state.show_overlay = True

        if st.session_state.show_overlay and current_scene["type"] == "ai_dialogue":
            render_ai_dialogue_overlay()

    else:
        st.info("Interactive videos for this play will be added soon!")