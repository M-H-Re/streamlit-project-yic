import json
import time
from openai import OpenAI
import streamlit as st

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & CLIENT INITIALIZATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Director Test Lab",
    page_icon="🎬",
    layout="centered",
)


@st.cache_resource
def get_client():
  return OpenAI(
      api_key=st.secrets["API_KEY"], base_url=st.secrets.get("BASE_URL", None)
  )


client = get_client()


# -----------------------------------------------------------------------------
# 2. AI SOCRATIC DIALOGUE FUNCTIONS
# -----------------------------------------------------------------------------
def evaluate_initial_suggestion(actor_name, predicament, initial_answer):
  """Evaluates Step 1 suggestion.

  If valid -> asks 'Why do you think so?'. If unrealistic/off-topic -> redirects
  gently in-character.
  """
  system_prompt = f"""
    You are an interactive AI actor playing {actor_name} in a live theater play for children.
    Predicament: "{predicament}"
    
    TASK:
    1. Read the child's suggestion: "{initial_answer}"
    2. Determine if the suggestion is RELEVANT/REALISTIC to the story or UNREALISTIC/OFF-TOPIC (e.g. modern tech, absurd objects, violence out of context, nonsensical text).
    3. Generate 'actor_response':
       - If RELEVANT: React warmly in 1 short sentence, then ask WHY they think that is the best path.
       - If UNREALISTIC/OFF-TOPIC: Make a lighthearted, in-character reaction showing why that isn't possible in Verona, then ask what else {actor_name} should do.
    
    Keep 'actor_response' under 25 words. Do not use emojis or stage directions.

    Return ONLY a JSON object:
    {{"is_relevant": boolean, "actor_response": string}}
    """

  try:
    response = client.chat.completions.create(
        model="assistant-base",
        messages=[{"role": "system", "content": system_prompt}],
        temperature=0.5,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)

  except Exception as e:
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
  """Evaluates full answer, validates unique reasoning, and subtly funnels toward 1 of 2 core scene branches."""
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
        model="assistant-base",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)

  except Exception as e:
    return {
        "matched_scene": "scene_2_accept",
        "actor_comment": (
            "Your wisdom gives me courage! I shall trust in love and pledge my"
            " heart to Juliet!"
        ),
    }


# -----------------------------------------------------------------------------
# 3. SCENE DATA & STATE MANAGEMENT
# -----------------------------------------------------------------------------
ACTOR_NAME = "Romeo"
PREDICAMENT = (
    "Juliet has offered her love, but our families are bitter enemies! What"
    " should I do now?"
)

CORE_BRANCHES = {
    "scene_2_accept": {
        "title": "Branch A: Romeo Accepts & Pledges Love",
        "intent": (
            "Accept love, marry secretly, stay together, trust love, or try to"
            " make peace."
        ),
    },
    "scene_3_refuse": {
        "title": "Branch B: Romeo Refuses / Steps Back",
        "intent": (
            "Refuse, wait, run away, stay safe, or avoid danger with the"
            " families."
        ),
    },
}

if "test_step" not in st.session_state:
  st.session_state.test_step = 1
if "initial_suggestion" not in st.session_state:
  st.session_state.initial_suggestion = ""
if "followup_question" not in st.session_state:
  st.session_state.followup_question = ""
if "redirect_message" not in st.session_state:
  st.session_state.redirect_message = ""
if "final_evaluation" not in st.session_state:
  st.session_state.final_evaluation = None

# -----------------------------------------------------------------------------
# 4. STREAMLIT INTERFACE
# -----------------------------------------------------------------------------
st.title("🎬 AI Director Test Lab")
st.caption("Interactive Dialogue with Redirection Loop & 2-Branch Funneling")
st.divider()

st.info(f"**{ACTOR_NAME}'s Predicament:** \"{PREDICAMENT}\"")

st.write("---")

# STEP 1: INITIAL SUGGESTION (WITH REDIRECTION LOOP)
if st.session_state.test_step == 1:
  st.markdown("### Step 1: Suggestion")

  # Show Romeo's redirect message if previous attempt was unrealistic
  if st.session_state.redirect_message:
    st.warning(f"🎭 **{ACTOR_NAME}:** \"{st.session_state.redirect_message}\"")

  with st.form("suggestion_form"):
    user_sugg = st.text_input(
        f"What should {ACTOR_NAME} do?",
        placeholder="e.g., Talk to her privately",
    )
    submitted_sugg = st.form_submit_button("Send Suggestion", type="primary")

    if submitted_sugg:
      if not user_sugg.strip():
        st.warning("Please type a suggestion first.")
      else:
        with st.spinner(f"{ACTOR_NAME} is listening to your idea..."):
          eval_res = evaluate_initial_suggestion(
              ACTOR_NAME, PREDICAMENT, user_sugg
          )

          if eval_res["is_relevant"]:
            # Valid suggestion -> Move to Step 2
            st.session_state.initial_suggestion = user_sugg
            st.session_state.followup_question = eval_res["actor_response"]
            st.session_state.redirect_message = ""
            st.session_state.test_step = 2
            st.rerun()
          else:
            # Unrealistic -> Stay on Step 1 with a redirect
            st.session_state.redirect_message = eval_res["actor_response"]
            st.rerun()

# STEP 2: REASONING (WHY DO YOU THINK SO?)
elif st.session_state.test_step == 2:
  st.success(f"**Your Suggestion:** \"{st.session_state.initial_suggestion}\"")
  st.info(
      f"🎭 **{ACTOR_NAME} asks:** \"{st.session_state.followup_question}\""
  )

  st.markdown("### Step 2: Reason")
  with st.form("explanation_form"):
    user_reason = st.text_input(
        "Explain your reasoning:",
        placeholder="e.g., Because showing love is the only way to stop the fighting.",
    )
    submitted_reason = st.form_submit_button("Send Reason", type="primary")

    if submitted_reason:
      if not user_reason.strip():
        st.warning("Please explain your reasoning first.")
      else:
        with st.spinner(
            f"{ACTOR_NAME} is evaluating and bridging your reason..."
        ):
          result = evaluate_child_reasoning(
              ACTOR_NAME,
              PREDICAMENT,
              st.session_state.initial_suggestion,
              user_reason,
              CORE_BRANCHES,
          )
          st.session_state.final_evaluation = result
          st.session_state.test_step = 3
          st.rerun()

# STEP 3: DYNAMIC BRIDGE & VIDEO SELECTION
elif st.session_state.test_step == 3:
  eval_data = st.session_state.final_evaluation
  matched_scene = eval_data.get("matched_scene")
  actor_comment = eval_data.get("actor_comment")

  st.markdown("### Step 3: AI Actor Transition & Video Selection")

  st.success(f"🎭 **{ACTOR_NAME}:** \"{actor_comment}\"")
  st.info(
      f"📹 **Next Video to Play:** `{matched_scene}` ("
      f" {CORE_BRANCHES[matched_scene]['title']})"
  )

  if st.button("Test Another Response", type="primary"):
    st.session_state.test_step = 1
    st.session_state.initial_suggestion = ""
    st.session_state.followup_question = ""
    st.session_state.redirect_message = ""
    st.session_state.final_evaluation = None
    st.rerun()

# Reset Button
st.write("---")
if st.button("Reset Test State"):
  st.session_state.test_step = 1
  st.session_state.initial_suggestion = ""
  st.session_state.followup_question = ""
  st.session_state.redirect_message = ""
  st.session_state.final_evaluation = None
  st.rerun()