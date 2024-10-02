import streamlit as st
import assemblyai as aai
import tempfile
import os
import uuid
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Read the API key from the environment variable
aai.settings.api_key = os.environ.get("ASSEMBLYAI_API_KEY")

@st.cache_data(show_spinner=False)
def transcribe_audio(audio_file):
    config = aai.TranscriptionConfig(speaker_labels=True)
    transcript = aai.Transcriber().transcribe(audio_file, config)
    return {
        "text": transcript.text,
        "utterances": [
            {"speaker": u.speaker, "text": u.text}
            for u in transcript.utterances
        ],
        "srt_subtitles": transcript.export_subtitles_srt(),
        "vtt_subtitles": transcript.export_subtitles_vtt()
    }

def update_speaker_names():
    st.session_state.speaker_names = {
        'A': st.session_state.speaker_a_name,
        'B': st.session_state.speaker_b_name
    }

def reset_session():
    for key in ['transcript_data', 'speaker_names', 'speaker_a_name', 'speaker_b_name', 'show_full_transcript']:
        if key in st.session_state:
            del st.session_state[key]
    # Generate a new unique key for the file uploader
    st.session_state.file_uploader_key = str(uuid.uuid4())

def main():
    st.title("NotebookLM Transcriber")

    # Initialize session state
    if 'transcript_data' not in st.session_state:
        st.session_state.transcript_data = None
    if 'speaker_names' not in st.session_state:
        st.session_state.speaker_names = {'A': '', 'B': ''}
    if 'file_uploader_key' not in st.session_state:
        st.session_state.file_uploader_key = str(uuid.uuid4())

    # New Session button
    if st.button("Start New Session", key="new_session"):
        reset_session()
        st.rerun()

    # File uploader with dynamic key
    uploaded_file = st.file_uploader("Choose an audio file", type=['mp3', 'wav', 'ogg'], key=st.session_state.file_uploader_key)

    if uploaded_file is not None and st.session_state.transcript_data is None:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        # Transcribe the audio and show sample
        with st.spinner('Transcribing audio...'):
            st.session_state.transcript_data = transcribe_audio(tmp_file_path)

        # Clean up the temporary file
        os.unlink(tmp_file_path)

    if st.session_state.transcript_data is not None:
        # Display a sample of the transcript
        st.subheader("Sample of transcript:")
        for utterance in st.session_state.transcript_data["utterances"][:5]:
            st.text(f"Speaker {utterance['speaker']}: {utterance['text']}")

        # Speaker name inputs in one row
        col1, col2 = st.columns(2)
        with col1:
            speaker_a = st.text_input("Enter name for Speaker A:", key="speaker_a_name", value=st.session_state.speaker_names['A'])
        with col2:
            speaker_b = st.text_input("Enter name for Speaker B:", key="speaker_b_name", value=st.session_state.speaker_names['B'])

        # Buttons in separate rows
        apply_names_disabled = not (speaker_a and speaker_b)
        if st.button('Generate Custom Transcript', on_click=update_speaker_names, disabled=apply_names_disabled):
            st.rerun()

        if st.button('Generate Default Transcript'):
            st.session_state.show_full_transcript = True
            st.rerun()

        if st.session_state.get('show_full_transcript', False) or (st.session_state.speaker_names['A'] and st.session_state.speaker_names['B']):
            # Display full transcript
            st.subheader("Full transcript:")
            full_transcript = ""
            for utterance in st.session_state.transcript_data["utterances"]:
                if st.session_state.speaker_names['A'] and st.session_state.speaker_names['B']:
                    speaker_name = st.session_state.speaker_names[utterance['speaker']]
                else:
                    speaker_name = f"Speaker {utterance['speaker']}"
                line = f"{speaker_name}: {utterance['text']}\n"
                st.text(line)
                full_transcript += line

            # Add download buttons
            st.download_button(
                label="Download Full Transcript (TXT)",
                data=full_transcript,
                file_name="transcript.txt",
                mime="text/plain",
                key="download_transcript"
            )

            st.download_button(
                label="Download SRT Subtitles",
                data=st.session_state.transcript_data["srt_subtitles"],
                file_name="subtitles.srt",
                mime="text/plain",
                key="download_srt"
            )

            st.download_button(
                label="Download VTT Subtitles",
                data=st.session_state.transcript_data["vtt_subtitles"],
                file_name="subtitles.vtt",
                mime="text/plain",
                key="download_vtt"
            )
        else:
            st.info("Enter names for both speakers and click 'Generate Custom Transcript' to see the full transcript with custom names, or click 'Generate Default Transcript' to see the full transcript with generic speaker labels.")

if __name__ == "__main__":
    main()