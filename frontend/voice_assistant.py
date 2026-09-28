"""
voice_assistant.py
-------------------
Conversational voice intake: asks the patient one question at a time,
listens via microphone, transcribes speech to text, extracts a
structured value for each PatientIntake field, and once complete,
returns a patient_data dict identical in shape to what
render_patient_form() produces in streamlit_app.py.
"""

from __future__ import annotations

import io
import tempfile
from typing import Any, Dict, List, Optional

import speech_recognition as sr
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment
from rapidfuzz import process, fuzz
from streamlit_mic_recorder import mic_recorder

from constants import COMMON_SYMPTOMS  # reuse the existing list


# ----------------------------------------------------------------------
# Conversation script: one entry per PatientIntake field
# ----------------------------------------------------------------------

QUESTIONS = [
    {"key": "age", "prompt": "What is your age?", "type": "number"},
    {"key": "sex", "prompt": "What is your sex assigned at birth? "
                             "Say Female, Male, Intersex, or Prefer not to say.", "type": "choice",
     "options": ["Female", "Male", "Intersex", "Prefer not to say"]},
    {"key": "symptoms", "prompt": "Please describe all the symptoms you are experiencing.", "type": "symptoms"},
    {"key": "duration_days", "prompt": "For how many days have you had these symptoms?", "type": "number"},
    {"key": "severity", "prompt": "How would you rate the severity? Say Mild, Moderate, or Severe.",
     "type": "choice", "options": ["Mild", "Moderate", "Severe"]},
    {"key": "progression", "prompt": "Are your symptoms Improving, Stable, or Worsening?",
     "type": "choice", "options": ["Improving", "Stable", "Worsening"]},
    {"key": "history", "prompt": "Please mention any relevant medical history, "
                                  "current medications, or allergies. Say 'none' if not applicable.",
     "type": "text"},
    {"key": "consent", "prompt": "This tool does not provide medical diagnoses and only helps "
                                  "organize information for a clinician. Do you consent to proceed? "
                                  "Say yes or no.", "type": "yesno"},
]


# ----------------------------------------------------------------------
# Text-to-speech: speak a question
# ----------------------------------------------------------------------

def speak(text: str) -> None:
    tts = gTTS(text=text, lang="en")
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    st.audio(buf.read(), format="audio/mp3", autoplay=True)


# ----------------------------------------------------------------------
# Speech-to-text: transcribe recorded audio bytes to text
# ----------------------------------------------------------------------

def transcribe(audio_bytes: bytes) -> str:
    recognizer = sr.Recognizer()

    # streamlit_mic_recorder returns browser-recorded audio, typically
    # WebM/Opus -- speech_recognition's AudioFile only understands WAV,
    # AIFF, or FLAC directly, so we convert via pydub/ffmpeg first.
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as raw_tmp:
        raw_tmp.write(audio_bytes)
        raw_path = raw_tmp.name

    wav_path = raw_path.replace(".webm", ".wav")

    try:
        audio_segment = AudioSegment.from_file(raw_path)
        audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)
        audio_segment.export(wav_path, format="wav")
    except Exception as exc:
        st.error(f"Could not decode recorded audio: {exc}")
        return ""

    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)

    try:
        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as exc:
        st.error(f"Speech recognition service error: {exc}")
        return ""


# ----------------------------------------------------------------------
# Extraction: map free-text answer -> structured value per field type
# ----------------------------------------------------------------------

def _extract_number(text: str) -> Optional[int]:
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None


def _extract_choice(text: str, options: List[str]) -> Optional[str]:
    match, score, _ = process.extractOne(text, options, scorer=fuzz.WRatio)
    return match if score >= 60 else None


def _extract_yesno(text: str) -> Optional[bool]:
    text = text.lower()
    if any(w in text for w in ["yes", "yeah", "agree", "sure", "okay"]):
        return True
    if any(w in text for w in ["no", "not", "disagree"]):
        return False
    return None


def _extract_symptoms(text: str) -> List[str]:
    """Fuzzy-match spoken phrase against COMMON_SYMPTOMS; splits on
    'and'/commas so multiple symptoms in one sentence are all caught."""
    found = []
    fragments = text.replace(" and ", ",").split(",")
    for fragment in fragments:
        fragment = fragment.strip()
        if not fragment:
            continue
        match, score, _ = process.extractOne(fragment, COMMON_SYMPTOMS, scorer=fuzz.WRatio)
        if score >= 55 and match not in found:
            found.append(match)
    return found


def extract_value(question: Dict[str, Any], text: str):
    qtype = question["type"]
    if qtype == "number":
        return _extract_number(text)
    if qtype == "choice":
        return _extract_choice(text, question["options"])
    if qtype == "yesno":
        return _extract_yesno(text)
    if qtype == "symptoms":
        return _extract_symptoms(text)
    return text.strip()  # plain text field (history)


# ----------------------------------------------------------------------
# Main voice-intake UI: renders one question at a time using session_state
# ----------------------------------------------------------------------

def render_voice_intake() -> Optional[Dict[str, Any]]:
    """Returns a completed patient_data dict once all questions are
    answered, otherwise None (still in progress)."""

    if "voice_step" not in st.session_state:
        st.session_state.voice_step = 0
        st.session_state.voice_answers = {}

    step = st.session_state.voice_step

    st.subheader("🎙️ Voice Intake Assistant")
    progress = step / len(QUESTIONS)
    st.progress(progress)

    if step >= len(QUESTIONS):
        st.success("All questions answered. Building your assessment...")
        return _finalize(st.session_state.voice_answers)

    question = QUESTIONS[step]

    st.write(f"**Question {step + 1} of {len(QUESTIONS)}:** {question['prompt']}")
    speak(question["prompt"])

    audio = mic_recorder(
        start_prompt="🎤 Start speaking",
        stop_prompt="⏹️ Stop",
        key=f"mic_{step}",
    )

    if audio and audio.get("bytes"):
        transcript = transcribe(audio["bytes"])
        st.write(f"You said: *{transcript}*")

        value = extract_value(question, transcript)

        if value is None or value == [] or value == "":
            st.warning("Sorry, I couldn't understand that clearly. Please try again.")
        else:
            st.session_state.voice_answers[question["key"]] = value
            st.session_state.voice_step += 1
            st.rerun()

    # Manual fallback in case speech recognition keeps failing
    with st.expander("Having trouble? Type your answer instead"):
        manual = st.text_input("Your answer", key=f"manual_{step}")
        if st.button("Submit typed answer", key=f"manual_btn_{step}"):
            value = extract_value(question, manual)
            if value is None or value == [] or value == "":
                st.warning("Could not interpret that answer, please rephrase.")
            else:
                st.session_state.voice_answers[question["key"]] = value
                st.session_state.voice_step += 1
                st.rerun()

    return None


def _finalize(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Shape collected answers exactly like render_patient_form()'s output."""
    return {
        "age": answers.get("age", 0),
        "sex": answers.get("sex", "Prefer not to say"),
        "symptoms": answers.get("symptoms", []),
        "duration_days": answers.get("duration_days", 0),
        "severity": answers.get("severity", "Mild"),
        "progression": answers.get("progression", "Stable"),
        "history": answers.get("history", ""),
        "consent": bool(answers.get("consent", False)),
    }


def reset_voice_intake() -> None:
    st.session_state.voice_step = 0
    st.session_state.voice_answers = {}