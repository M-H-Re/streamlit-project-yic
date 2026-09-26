import time
from openai import OpenAI
import streamlit as st

st.set_page_config(
    page_title="KLSP Interactive Educational Theater", layout="centered"
)


# Cache client initialization to prevent micro-delays across script re-runs
@st.cache_resource
# def get_client():
#   # Extract secrets
#   api_key = st.secrets["GEMINI_API_KEY"]
#   base_url = st.secrets.get("BASE_URL", None)

#   # Configure HttpOptions if custom base_url proxy is set
#   http_options = types.HttpOptions(base_url=base_url) if base_url else None

#   return genai.Client(api_key=api_key, http_options=http_options)

def get_client():
  return OpenAI(
    api_key=st.secrets["API_KEY"],
    base_url=st.secrets.get("BASE_URL", None)
  )

client = get_client()

# Valid Flash models for stable response
CANDIDATE_MODELS = ["assistant-advanced"]

SCENES = {
    "scene_1_genesis": {
        "type": "branching",
        "title": "Scene 1: Juliet's Proposal",
        "video_url": "videos/genesis.mp4",
        "question": (
            "Juliet proposes marriage to Romeo! How should Romeo respond?"
        ),
        "context_description": (
            "Juliet proposes marriage to Romeo on the balcony."
        ),
        "choices": {
            "Option A: Accept the marriage proposal": {
                "route": "scene_2_accept",
                "transition_text": (
                    "Romeo's heart fills with joy as he accepts Juliet's pledge"
                    " of love..."
                ),
            },
            "Option B: Refuse the proposal": {
                "route": "scene_3_refuse",
                "transition_text": (
                    "A sudden shadow falls over the balcony as Romeo hesitates"
                    " and refuses..."
                ),
            },
        },
    },
    "scene_2_accept": {
        "type": "branching",
        "title": "Scene 2A: The Betrothal",
        "video_url": "videos/accept.mp4",
        "question": "With vows exchanged, where should the lovers go next?",
        "context_description": "Romeo accepts the marriage proposal.",
        "choices": {
            "Option A: Seek Friar Laurence's help": {
                "route": "scene_4_question",
                "transition_text": (
                    "They decide to visit Friar Laurence to arrange a secret"
                    " ceremony..."
                ),
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
        "question": "Juliet is heartbroken. What happens next?",
        "context_description": "Juliet reacts to the refused marriage proposal.",
        "choices": {
            "Option A: Look around the room for comfort": {
                "route": "scene_4_question",
                "transition_text": (
                    "Juliet steps back into her chamber, looking around..."
                ),
            },
            "Option B: Search for a musical token": {
                "route": "scene_4_question",
                "transition_text": (
                    "Searching for solace, she turns toward the corner of the"
                    " room..."
                ),
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
        "context_description": (
            "A character points out a hidden musical object and asks the"
            " audience to identify it."
        ),
        "next_scene": "scene_5_answer",
    },
    "scene_5_answer": {
        "type": "branching",
        "title": "Scene 4: Object Revealed",
        "video_url": "videos/answer.mp4",
        "question": (
            "The mystery instrument is revealed! What would you like to do"
            " now?"
        ),
        "context_description": (
            "The character reveals the ukulele after the user's correct answer."
        ),
        "choices": {
            "Option A: Restart the play": {
                "route": "scene_1_genesis",
                "transition_text": (
                    "Returning to the balcony where it all began..."
                ),
            }
        },
    },
}

# --- State Management ---
if "current_scene_id" not in st.session_state:
  st.session_state.current_scene_id = "scene_1_genesis"
if "video_finished" not in st.session_state:
  st.session_state.video_finished = False
if "hint_count" not in st.session_state:
  st.session_state.hint_count = 0

current_scene = SCENES[st.session_state.current_scene_id]

st.title(current_scene["title"])

# Video Player
st.video(current_scene["video_url"], autoplay=True)

if st.button("proceed"):
  st.session_state.video_finished = True


# Fast AI call helper with token limits & error logging for debugging
def get_fast_ai_response(prompt):
  for model_name in CANDIDATE_MODELS:
    try:
      response = client.chat.completions.create(
          model=model_name, messages=[{"role": "user", "content": prompt}],
          temperature=0.7, max_tokens=60
      )
      if response.choices and response.choices[0].message:
        return response.choices[0].message
    except Exception as e:
      print(f"DEBUG: Failed model {model_name} with error: {e}")
      continue

  return (
      "That doesn't look quite right! Take another close look and try guessing"
      " again."
  )


# --- SCENE ROUTING & DISPLAY LOGIC ---
if st.session_state.video_finished:

  # MODE 1: BRANCHING DECISION (INSTANT - NO AI LATENCY)
  if current_scene["type"] == "branching":
    st.subheader("Make Your Decision")
    st.write(f"**Question:** {current_scene['question']}")

    choice_options = list(current_scene["choices"].keys())
    selected_choice_key = st.radio(
        "Select your path:",
        choice_options,
        key=st.session_state.current_scene_id,
    )

    if st.button("Confirm Choice"):
      selected = current_scene["choices"][selected_choice_key]

      # Instantly display hardcoded transition without waiting for an API call
      st.info(f"**Narrator:** {selected['transition_text']}")
      time.sleep(1.5)

      # Transition scenes
      st.session_state.current_scene_id = selected["route"]
      st.session_state.video_finished = False
      st.session_state.hint_count = 0
      st.rerun()

  # MODE 2: INTERACTIVE CHALLENGE (OBJECT FINDING / HINTING)
  elif current_scene["type"] == "interactive_challenge":
    st.subheader("Interactive Challenge")
    st.write(f"**{current_scene['character_name']} asks:**")
    st.info(f'"{current_scene["prompt_question"]}"')

    target = current_scene["target_answer"].upper()
    revealed_letters = st.session_state.hint_count

    masked_word = " ".join([
        char if idx < revealed_letters else "_"
        for idx, char in enumerate(target)
    ])
    st.markdown(f"### Hint Display: `{masked_word}`")

    if revealed_letters < len(target):
      if st.button("💡 Need a Hint? (Reveal a Letter)"):
        st.session_state.hint_count += 1
        st.rerun()

    user_guess = st.text_input("Type your answer here:").strip()

    if st.button("Submit Answer"):
      if user_guess.upper() == target:
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

        st.error(f"❌ **Incorrect Guess:** '{user_guess}'")
        st.warning(f"**{current_scene['character_name']}:** {correction}")

        if st.session_state.hint_count < len(target):
          st.session_state.hint_count += 1