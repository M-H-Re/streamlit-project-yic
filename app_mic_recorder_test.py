import json
from openai import OpenAI
import streamlit as st

# -----------------------------------------------------------------------------
# 1. PAGE SETUP
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Voice AI Workshop",
    page_icon="🎭",
    layout="centered",
)

st.title("🎭 AI Actor Voice Workshop Test")

# -----------------------------------------------------------------------------
# 2. OPENAI CLIENT & SETUP
# -----------------------------------------------------------------------------
@st.cache_resource
def get_client():
    return OpenAI(
        api_key=st.secrets["API_KEY"],
        base_url=st.secrets.get("BASE_URL", None)
    )

client = get_client()

# Set model to assistant-base
EVAL_MODEL = "assistant-base"

ACTOR_NAME = "Romeo"
PREDICAMENT = "Juliet has offered her love, but our families are bitter enemies! What should I do now?"

CORE_BRANCHES = {
    "scene_2_accept": {
        "title": "Branch A: Romeo Accepts & Pledges Love",
        "intent": "Accept love, marry secretly, stay together, trust love, or try to make peace.",
    },
    "scene_3_refuse": {
        "title": "Branch B: Romeo Refuses / Steps Back",
        "intent": "Refuse, wait, run away, stay safe, or avoid danger with the families.",
    },
}

# State management initialization
if "show_dialog" not in st.session_state:
    st.session_state.show_dialog = False
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
# 3. AI EVALUATION FUNCTIONS
# -----------------------------------------------------------------------------
def evaluate_initial_suggestion(actor_name, predicament, initial_answer):
    system_prompt = f"""
    You are an interactive AI actor playing {actor_name} in a live theater play for children.
    Predicament: "{predicament}"
    
    TASK:
    1. Read the child's suggestion: "{initial_answer}"
    2. Determine if the suggestion is RELEVANT/REALISTIC to the story or UNREALISTIC/OFF-TOPIC.
    3. Generate 'actor_response':
       - If RELEVANT: React warmly in 1 short sentence, then ask WHY they think that is the best path.
       - If UNREALISTIC/OFF-TOPIC: Make a lighthearted, in-character reaction showing why that isn't possible, then ask what else {actor_name} should do.
    
    Keep 'actor_response' under 25 words. Do not use emojis, stage directions, or parentheticals.

    Return ONLY a JSON object:
    {{"is_relevant": boolean, "actor_response": string}}
    """
    try:
        response = client.chat.completions.create(
            model=EVAL_MODEL,
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.5,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {
            "is_relevant": True,
            "actor_response": f"That is an interesting thought! Why do you feel that is the best path for {actor_name}?",
        }

def evaluate_child_reasoning(actor_name, predicament, initial_answer, explanation, branches):
    branches_formatted = json.dumps(branches, indent=2)
    system_prompt = f"""
    You are an interactive AI actor playing {actor_name} in a play with ONLY 2 fixed video paths:
    1. 'scene_2_accept' (Romeo stays and accepts love / marriage / peace)
    2. 'scene_3_refuse' (Romeo steps back, refuses, flees, or hesitates due to danger)

    YOUR TASK:
    1. Read the child's suggestion and explanation.
    2. Determine which of the 2 paths ('scene_2_accept' OR 'scene_3_refuse') their idea leans closer toward.
    3. Set 'matched_scene' to that key.
    4. Write a UNIQUE 1-2 sentence response as 'actor_comment' that FIRST validates their specific reason, and SECOND seamlessly bridges their idea into that video path (max 30 words).

    Keep 'actor_comment' free of emojis or stage directions.

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
            model=EVAL_MODEL,
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
            "actor_comment": "Your wisdom gives me courage! I shall trust in love and pledge my heart to Juliet!",
        }

# Fixed JS Injector for Voice Recognition
def render_voice_button(status_id="speech-status"):
    st.components.v1.html(
        f"""
        <script>
        function startDictation() {{
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {{
                var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                var recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = "en-US";
                
                var status = document.getElementById('{status_id}');
                status.innerText = "🎙️ Listening... Speak now!";
                
                recognition.start();

                recognition.onresult = function(e) {{
                    var transcript = e.results[0][0].transcript;
                    recognition.stop();
                    status.innerText = "✅ Captured!";
                    
                    var inputs = window.parent.document.querySelectorAll('input[type="text"]');
                    if (inputs.length > 0) {{
                        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                        nativeInputValueSetter.call(inputs[0], transcript);
                        
                        // Dispatch events so React/Streamlit locks the text value permanently
                        inputs[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                        inputs[0].dispatchEvent(new Event('change', {{ bubbles: true }}));
                        inputs[0].dispatchEvent(new Event('blur', {{ bubbles: true }}));
                    }}
                }};

                recognition.onerror = function(e) {{
                    recognition.stop();
                    status.innerText = "⚠️ Voice error. Click again.";
                }};
            }} else {{
                alert("Voice Recognition is not supported in this browser. Try Google Chrome or Edge.");
            }}
        }}
        </script>
        <div style="display: flex; align-items: center; gap: 10px; font-family: sans-serif; margin-bottom: 5px;">
            <button type="button" onclick="startDictation()" style="
                background-color: #FF4B4B;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: bold;
                cursor: pointer;
            ">🎙️ Click & Speak</button>
            <span id="{status_id}" style="color: #666; font-size: 0.85rem;">Click button to talk</span>
        </div>
        """,
        height=45,
    )

# -----------------------------------------------------------------------------
# 4. OVERLAY DIALOG (STABLE OVERLAY)
# -----------------------------------------------------------------------------
@st.dialog("🎭 AI Actor Socratic Workshop", width="small")
def render_ai_dialogue_overlay():
    st.caption(f'Predicament: "{PREDICAMENT}"')

    # STEP 1: SUGGESTION
    if st.session_state.ai_step == 1:
        st.subheader("Step 1: What should Romeo do?")

        if st.session_state.redirect_message:
            st.warning(f'🎭 **{ACTOR_NAME}:** "{st.session_state.redirect_message}"')

        render_voice_button("status_step_1")

        with st.form("suggestion_form", clear_on_submit=False):
            user_sugg = st.text_input(
                "Your suggestion:",
                placeholder="Click mic above or type here..."
            )
            submitted_sugg = st.form_submit_button("Send Suggestion", type="primary")

            if submitted_sugg:
                if not user_sugg.strip():
                    st.error("Please provide a suggestion before submitting.")
                else:
                    with st.spinner(f"{ACTOR_NAME} is evaluating..."):
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

    # STEP 2: REASONING
    elif st.session_state.ai_step == 2:
        st.subheader("Step 2: Explain Your Reasoning")

        st.success(f'**Your Suggestion:** "{st.session_state.initial_suggestion}"')
        st.info(f'🎭 **{ACTOR_NAME} asks:** "{st.session_state.followup_question}"')

        if st.session_state.ai_review_result is None:
            render_voice_button("status_step_2")

            with st.form("reason_form", clear_on_submit=False):
                user_reason = st.text_input(
                    "Your reason:",
                    placeholder="Click mic above or type here..."
                )
                submitted_reason = st.form_submit_button("Submit Reason", type="primary")

                if submitted_reason:
                    if not user_reason.strip():
                        st.error("Please explain your reason before submitting.")
                    else:
                        with st.spinner(f"{ACTOR_NAME} is processing..."):
                            result = evaluate_child_reasoning(
                                ACTOR_NAME,
                                PREDICAMENT,
                                st.session_state.initial_suggestion,
                                user_reason.strip(),
                                CORE_BRANCHES,
                            )
                            st.session_state.ai_review_result = result
                            st.rerun()

        else:
            result = st.session_state.ai_review_result
            actor_comment = result.get("actor_comment", "")
            matched_scene = result.get("matched_scene", "scene_2_accept")

            st.success(f'🎭 **{ACTOR_NAME}:** "{actor_comment}"')
            st.info(f"🎬 **Routed Scene Branch:** `{matched_scene}`")

            if st.button("Close & Done ✅", type="primary", use_container_width=True):
                st.session_state.show_dialog = False
                reset_ai_state()
                st.rerun()

# -----------------------------------------------------------------------------
# 5. MAIN SCREEN & DIALOG PERSISTENCE
# -----------------------------------------------------------------------------
if st.button("💬 Launch Workshop Modal", type="primary", use_container_width=True):
    st.session_state.show_dialog = True

if st.session_state.show_dialog:
    render_ai_dialogue_overlay()