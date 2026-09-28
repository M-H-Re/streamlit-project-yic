import time
from openai import OpenAI
import streamlit as st

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & THEME (CREME, WARM TONED, DARK PURPLE)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="The Bard's Play",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    /* Base Page Styling */
    .stApp {
        background-color: #FAF6EE !important; /* Creme */
        color: #2D122D !important; /* Dark Purple */
        font-family: 'Georgia', serif;
    }
    
    /* Hero Title & Subtitle */
    .hero-title {
        color: #2D122D;
        font-size: 4rem;
        font-weight: bold;
        text-align: center;
        margin-top: 1.5rem;
    }
    .hero-subtitle {
        color: #6B4E71;
        font-size: 1.3rem;
        text-align: center;
        margin-bottom: 2.5rem;
        font-style: italic;
    }
    
    /* Centered Main Landing Play Button */
    div.stButton > button[key="btn_start_play"] {
        background-color: #2D122D !important;
        color: #FAF6EE !important;
        font-size: 1.8rem !important;
        padding: 1rem 3.5rem !important;
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
    
    /* Play Gallery Block Cards */
    .play-card {
        background-color: #FFFDF9;
        border: 2px solid #E8DCC4;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.04);
        margin-bottom: 10px;
    }
    .play-card h3 {
        color: #2D122D;
        margin-bottom: 8px;
    }
    .play-card p {
        color: #7A6263;
        font-size: 0.95rem;
    }

    /* Larger Interactive & Branching Text Elements */
    .stage-question-text {
        font-size: 1.5rem !important;
        font-weight: 600;
        color: #2D122D;
        margin-bottom: 15px;
    }
    .stage-challenge-prompt {
        font-size: 1.6rem !important;
        font-weight: 500;
        color: #2D122D;
        line-height: 1.4;
    }
    div[data-testid="stMarkdownContainer"] p {
        font-size: 1.15rem;
    }
    /* Larger Radio Label Text */
    div[data-widget="stRadio"] label p {
        font-size: 1.3rem !important;
        font-weight: bold;
        color: #2D122D;
    }
    </style>
""",
    unsafe_allow_html=True,
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
      api_key=st.secrets["API_KEY"], base_url=st.secrets.get("BASE_URL", None)
  )


client = get_client()

# Valid Flash models for stable response
CANDIDATE_MODELS = ["assistant-base"]

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
if "page" not in st.session_state:
  st.session_state.page = "main"
if "selected_play" not in st.session_state:
  st.session_state.selected_play = None
if "current_scene_id" not in st.session_state:
  st.session_state.current_scene_id = "scene_1_genesis"
if "video_finished" not in st.session_state:
  st.session_state.video_finished = False
if "hint_count" not in st.session_state:
  st.session_state.hint_count = 0


# Fast AI call helper with token limits & error logging for debugging
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
    except Exception as e:
      print(f"DEBUG: Failed model {model_name} with error: {e}")
      continue

  return (
      "That doesn't look quite right! Take another close look and try guessing"
      " again."
  )


# -----------------------------------------------------------------------------
# PAGE ROUTING & VIEWS
# -----------------------------------------------------------------------------

# --- VIEW 1: MAIN HERO PAGE ---
if st.session_state.page == "main":
  st.markdown("<div style='height: 12vh;'></div>", unsafe_allow_html=True)
  st.markdown(
      "<h1 class='hero-title'>The Bard's Play</h1>", unsafe_allow_html=True
  )
  st.markdown(
      "<p class='hero-subtitle'>Step into the world of interactive drama and classic storytelling.</p>",
      unsafe_allow_html=True,
  )

  # Centered column layout for the play button
  _, col_center, _ = st.columns([1, 2, 1])
  with col_center:
    if st.button("Play 🎭", key="btn_start_play", use_container_width=True):
      st.session_state.page = "gallery"
      st.rerun()

# --- VIEW 2: PLAY GALLERY ---
elif st.session_state.page == "gallery":
  top_col1, top_col2 = st.columns([4, 1])
  with top_col1:
    st.title("🎭 The Bard's Play Gallery")
  with top_col2:
    if st.button("← Back to Home"):
      st.session_state.page = "main"
      st.rerun()

  st.write("Select a play block below to launch the interactive stage.")
  st.markdown("---")

  cols = st.columns(3)
  plays = [
      {
          "id": "romeo_juliet",
          "title": "Romeo & Juliet",
          "desc": "A classic Shakespearean tale of star-crossed lovers.",
      },
      {
          "id": "macbeth",
          "title": "Macbeth",
          "desc": "A terrifying journey into ambition and tragedy.",
      },
      {
          "id": "hamlet",
          "title": "Hamlet",
          "desc": "Revenge, conspiracy, and destiny in Denmark.",
      },
      {
          "id": "julius_caesar",
          "title": "Julius Caesar",
          "desc": "Political intrigue and betrayal in ancient Rome.",
      },
      {
          "id": "sang_kancil",
          "title": "Sang Kancil dan Buaya",
          "desc": "A clever mouse-deer outsmarts the crocodiles.",
      },
  ]

  for idx, p in enumerate(plays):
    with cols[idx % 3]:
      st.markdown(
          f"""
            <div class="play-card">
                <h3>{p['title']}</h3>
                <p>{p['desc']}</p>
            </div>
            """,
          unsafe_allow_html=True,
      )
      if st.button(
          f"🎬 Launch {p['title']}", key=p["id"], use_container_width=True
      ):
        st.session_state.selected_play = p["id"]
        st.session_state.page = "stage"
        st.rerun()

# --- VIEW 3: INTERACTIVE STAGE ---
elif st.session_state.page == "stage":
  if st.button("← Back to Gallery"):
    st.session_state.page = "gallery"
    st.session_state.current_scene_id = "scene_1_genesis"
    st.session_state.video_finished = False
    st.rerun()

  if st.session_state.selected_play == "romeo_juliet":
    current_scene = SCENES[st.session_state.current_scene_id]

    st.title(current_scene["title"])

    # Video Player
    st.video(current_scene["video_url"], autoplay=True)

    if not st.session_state.video_finished:
      if st.button("proceed"):
        st.session_state.video_finished = True
        st.rerun()

    # --- SCENE ROUTING & DISPLAY LOGIC ---
    if st.session_state.video_finished:
      st.write("---")

      # MODE 1: BRANCHING DECISION (INSTANT - NO AI LATENCY)
      if current_scene["type"] == "branching":
        st.subheader("Make Your Decision")
        st.markdown(
            f'<p class="stage-question-text"><strong>Question:</strong>'
            f' {current_scene["question"]}</p>',
            unsafe_allow_html=True,
        )

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
        st.markdown(
            f"### **{current_scene['character_name']} asks:**"
        )
        st.markdown(
            f'<div class="stage-challenge-prompt">"{current_scene["prompt_question"]}"</div>',
            unsafe_allow_html=True,
        )

        st.write("")  # Spacing
        target = current_scene["target_answer"].upper()
        revealed_letters = st.session_state.hint_count

        masked_word = " ".join([
            char if idx < revealed_letters else "_"
            for idx, char in enumerate(target)
        ])
        st.markdown(f"## Hint Display: `{masked_word}`")

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
  else:
    st.info("Interactive videos for this play will be added soon!")