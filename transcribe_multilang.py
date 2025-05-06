import streamlit as st
import assemblyai as aai
import tempfile
import os
import uuid
from dotenv import load_dotenv
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
import html
import re
import io
import logging

# Set Streamlit page config and hide default header/footer and all sidebar artifacts except for our custom oval
st.set_page_config(page_title="NotebookLM Multi-Language Transcriber", page_icon="🌍", layout="centered")
st.markdown('''
    <style>
        header[data-testid="stHeader"], footer, section[data-testid="stSidebar"],
        div[data-testid="stSidebarUserContent"], div[data-testid="stDecoration"],
        div[data-testid="stSidebarNav"], div[data-testid="stSidebarContent"],
        div[data-testid="stSidebarCollapseControl"] {
            display: none !important;
        }
        div.block-container {
            padding-left: 0rem !important;
            margin-left: 0rem !important;
        }
        .custom-oval-container {
            width: 100%;
            max-width: 700px;
            margin: 2.5rem auto 2.5rem auto;
            background: #23232a;
            border-radius: 2.5rem;
            box-shadow: 0 4px 32px 0 rgba(0,0,0,0.18);
            padding: 2.2rem 2.5rem 2.2rem 2.5rem;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            justify-content: center;
        }
        .custom-oval-container h1 {
            color: #60a5fa;
            font-size: 2.6rem;
            font-weight: 800;
            margin: 0 0 1.2rem 0;
            letter-spacing: 0.01em;
            text-shadow: 0 2px 8px #18181b;
        }
        .custom-oval-container ul, .custom-oval-container ol {
            margin-left: 1.2rem;
        }
        .custom-oval-container li {
            margin-bottom: 0.3rem;
        }
        .custom-oval-container strong {
            color: #f4f4f5;
        }
        .custom-oval-container code {
            background: #18181b;
            color: #a7f3d0;
            border-radius: 0.3rem;
            padding: 0.1rem 0.4rem;
            font-size: 0.95em;
        }
    </style>
    <div class="custom-oval-container">
        <h1>NotebookLM Multi-Language Transcriber</h1>
        <div style="color:#f4f4f5; font-size:1.08rem;">
            <p>Welcome! This app lets you transcribe audio files in multiple languages using AssemblyAI, and optionally translate the transcript to another language using Google Cloud Translate. You can also assign custom names to speakers and download transcripts or subtitles.</p>
            <strong>How to use:</strong>
            <ol>
                <li>Select the source language of your audio.</li>
                <li>Upload an audio file (<code>.mp3</code>, <code>.wav</code>, or <code>.ogg</code>).</li>
                <li>Wait for the transcription to complete (progress shown).</li>
                <li>Review a sample of the transcript.</li>
                <li>(Optional) Enter custom names for Speaker A and Speaker B, then click 'Generate Custom Transcript'.</li>
                <li>Or, click 'Generate Default Transcript' to use generic speaker labels.</li>
                <li>(Optional) Select a target language and click 'Translate' to translate the transcript.</li>
                <li>Download the transcript or subtitles in your preferred format.</li>
            </ol>
            <strong>Requirements:</strong>
            <ul>
                <li>You must have a valid AssemblyAI API key set in your <code>.env</code> file as <code>ASSEMBLYAI_API_KEY</code>.</li>
                <li>For translation, set <code>GOOGLE_APPLICATION_CREDENTIALS</code> in your environment to your Google Cloud service account credentials file.</li>
            </ul>
        </div>
    </div>
''', unsafe_allow_html=True)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

# Get the path to the service account file from an environment variable
service_account_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

if service_account_file:
    if os.path.exists(service_account_file):
        google_credentials = service_account.Credentials.from_service_account_file(
            service_account_file)
        translate_client = translate.Client(credentials=google_credentials)
    else:
        print(f"Error: The file {service_account_file} does not exist.")
else:
    print("Error: GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")

# Define supported languages
SUPPORTED_LANGUAGES = {
    "Global English": "en",
    "Australian English": "en-AU",
    "British English": "en-GB",
    "US English": "en-US",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Dutch": "nl",
    "Hindi": "hi",
    "Japanese": "ja",
    "Chinese": "zh",
    "Finnish": "fi",
    "Korean": "ko",
    "Polish": "pl",
    "Russian": "ru",
    "Turkish": "tr",
    "Ukrainian": "uk",
    "Vietnamese": "vi"
}

@st.cache_data(show_spinner=False)
def transcribe_audio(audio_file, language):
    config = aai.TranscriptionConfig(
        speaker_labels=True,
        language_code=SUPPORTED_LANGUAGES[language]
    )
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

@st.cache_data
def translate_text(text, target_language):
    try:
        logging.info(f"Attempting to translate to {target_language}")
        result = translate_client.translate(text, target_language=target_language)
        logging.info("Translation successful")
        return result['translatedText']
    except Exception as e:
        logging.error(f"Translation failed: {str(e)}")
        return f"Translation failed: {str(e)}"

def update_speaker_names():
    st.session_state.speaker_names = {
        'A': st.session_state.speaker_a_name,
        'B': st.session_state.speaker_b_name
    }

def reset_session():
    for key in ['transcript_data', 'speaker_names', 'speaker_a_name', 'speaker_b_name', 'show_full_transcript', 'translated_text']:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.file_uploader_key = str(uuid.uuid4())

def sanitize_text(text):
    # Decode HTML entities
    text = html.unescape(text)
    
    # Specifically replace 'd&#39;' with 'd''
    text = text.replace('d&#39;', "d'")
    
    # Replace common problematic characters
    text = text.replace("'", "'").replace('"', '"').replace('"', '"')
    
    # Remove any remaining HTML tags
    text = re.sub('<[^<]+?>', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text

def create_subtitle_file(transcript, format='srt'):
    lines = transcript.split('\n')
    subtitle_content = io.StringIO()
    
    for i, line in enumerate(lines, 1):
        if format == 'srt':
            subtitle_content.write(f"{i}\n00:00:00,000 --> 00:00:05,000\n{line}\n\n")
        elif format == 'vtt':
            subtitle_content.write(f"WEBVTT\n\n{i}\n00:00:00.000 --> 00:00:05.000\n{line}\n\n")
    
    return subtitle_content.getvalue()

def format_transcript(text):
    # This pattern looks for any word(s) followed by a single letter and a colon
    pattern = r'(\S+\s+[A-Z]\s*:)'    
    # Split the text by speaker indicators
    parts = re.split(pattern, text)
    formatted_lines = []
    
    for i in range(1, len(parts), 2):
        speaker = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        
        # Combine speaker and content on one line
        full_line = f"{speaker} {content}"
        
        # Add the line to our formatted lines
        formatted_lines.append(full_line)

    # Join the lines with double newlines to add space between speakers
    return '\n\n'.join(formatted_lines)

def display_translated_text(text):
    # Decode HTML entities and ensure proper Unicode handling
    decoded_text = html.unescape(text)
    
    # Use st.markdown with unsafe_allow_html=True to render the text
    st.markdown(f"<pre style='white-space: pre-wrap;'>{decoded_text}</pre>", unsafe_allow_html=True)

def main():
    # Initialize session state variables at the very top
    if 'transcript_data' not in st.session_state:
        st.session_state.transcript_data = None
    if 'speaker_names' not in st.session_state:
        st.session_state.speaker_names = {'A': '', 'B': ''}
    if 'file_uploader_key' not in st.session_state:
        st.session_state.file_uploader_key = str(uuid.uuid4())
    if 'translated_text' not in st.session_state:
        st.session_state.translated_text = None

    # Inject shadcn-inspired dark theme CSS for elegant styling
    st.markdown('''
        <style>
            body, .stApp {
                background: #18181b !important;
                font-family: "Inter", "Segoe UI", Arial, sans-serif;
                color: #f4f4f5 !important;
            }
            .shadcn-container {
                background: #23232a;
                border-radius: 1.2rem;
                box-shadow: 0 4px 24px 0 rgba(0,0,0,0.25);
                padding: 2.5rem 2rem 2rem 2rem;
                max-width: 650px;
                margin: 2.5rem auto 2rem auto;
                color: #f4f4f5;
            }
            .stButton > button, .stDownloadButton > button {
                background: linear-gradient(90deg, #6366f1 0%, #06b6d4 100%);
                color: #fff;
                border-radius: 0.6rem;
                border: none;
                padding: 0.7rem 1.5rem;
                font-weight: 600;
                font-size: 1rem;
                margin: 0.5rem 0.5rem 0.5rem 0;
                box-shadow: 0 2px 8px 0 rgba(0,0,0,0.18);
                transition: background 0.2s, box-shadow 0.2s;
            }
            .stButton > button:hover, .stDownloadButton > button:hover {
                background: linear-gradient(90deg, #818cf8 0%, #22d3ee 100%);
                box-shadow: 0 4px 16px 0 rgba(0,0,0,0.28);
            }
            .stTextInput > div > input {
                border-radius: 0.5rem;
                border: 1px solid #334155;
                padding: 0.6rem 1rem;
                font-size: 1rem;
                background: #18181b;
                color: #f4f4f5;
                margin-bottom: 0.5rem;
            }
            .stTextInput > div > input:focus {
                border: 1.5px solid #06b6d4;
                background: #23232a;
                color: #fff;
            }
            .stTextInput label {
                color: #60a5fa !important;
                font-weight: 700;
                text-shadow: 0 2px 8px #18181b;
            }
            .stFileUploader > div {
                border-radius: 0.7rem;
                border: 1.5px dashed #334155;
                background: #23232a;
                color: #f4f4f5;
                padding: 1.2rem;
            }
            .stFileUploader label {
                color: #60a5fa !important;
                font-weight: 700;
                font-size: 1.1rem;
                text-shadow: 0 2px 8px #18181b;
            }
            .stSubheader {
                color: #60a5fa !important;
                font-weight: 700;
                text-shadow: 0 2px 8px #18181b;
            }
            .stSubheader, .stMarkdown h2, .stMarkdown h3 {
                color: #f4f4f5;
                font-weight: 700;
                margin-top: 1.5rem;
            }
            .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
                color: #60a5fa !important;
                text-shadow: 0 2px 8px #18181b;
            }
            .stInfo, .stAlert {
                border-radius: 0.7rem;
                background: #0f172a;
                color: #e0e7ef;
                border: 1px solid #334155;
            }
            .stMarkdown, .stText, .stTextInput, .stFileUploader, .stDownloadButton, .stButton {
                color: #f4f4f5 !important;
            }
            /* Fix for Streamlit Deploy button/header if present */
            header[role="banner"] h1, header[role="banner"] .stDeployButton {
                color: #60a5fa !important;
                background: #23232a !important;
                text-shadow: 0 2px 8px #18181b;
            }
        </style>
    ''', unsafe_allow_html=True)

    # Render the Start New Session button above the container
    if st.button("Start New Session", key="new_session"):
        reset_session()
        st.rerun()

    st.markdown('<div class="shadcn-container">', unsafe_allow_html=True)

    # Language selection
    source_language = st.selectbox("Select source language", options=list(SUPPORTED_LANGUAGES.keys()))

    # File uploader with dynamic key
    uploaded_file = st.file_uploader("Choose an audio file", type=['mp3', 'wav', 'ogg'], key=st.session_state.file_uploader_key)

    if uploaded_file is not None and st.session_state.transcript_data is None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        with st.spinner('Transcribing audio...'):
            st.session_state.transcript_data = transcribe_audio(tmp_file_path, source_language)

        os.unlink(tmp_file_path)

    if st.session_state.transcript_data is not None:
        st.subheader("Sample of transcript:")
        for utterance in st.session_state.transcript_data["utterances"][:5]:
            st.text(f"Speaker {utterance['speaker']}: {utterance['text']}")

        col1, col2 = st.columns(2)
        with col1:
            speaker_a = st.text_input("Enter name for Speaker A:", key="speaker_a_name", value=st.session_state.speaker_names['A'])
        with col2:
            speaker_b = st.text_input("Enter name for Speaker B:", key="speaker_b_name", value=st.session_state.speaker_names['B'])

        apply_names_disabled = not (speaker_a and speaker_b)
        if st.button('Generate Custom Transcript', on_click=update_speaker_names, disabled=apply_names_disabled):
            st.rerun()

        if st.button('Generate Default Transcript'):
            st.session_state.show_full_transcript = True
            st.rerun()

        if st.session_state.get('show_full_transcript', False) or (st.session_state.speaker_names['A'] and st.session_state.speaker_names['B']):
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

            # Translation feature
            language_names = {
                'en': 'English',
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'it': 'Italian',
                'pt': 'Portuguese',
                'nl': 'Dutch',
                'ru': 'Russian',
                'zh': 'Chinese',
                'ja': 'Japanese',
                'ko': 'Korean',
                'ar': 'Arabic',
                'hi': 'Hindi',
                'bn': 'Bengali',
                'ur': 'Urdu',
                'tr': 'Turkish',
                'pl': 'Polish',
                'uk': 'Ukrainian',
                'vi': 'Vietnamese',
                'th': 'Thai'
            }
            language_options = [(name, code) for code, name in language_names.items()]
            language_options.sort(key=lambda x: x[0])
            selected_language_name, target_language = st.selectbox(
                "Select target language",
                options=language_options,
                format_func=lambda x: x[0]
            )

            if st.button("Translate"):
                if full_transcript:
                    with st.spinner("Translating..."):
                        st.session_state.translated_text = translate_text(full_transcript, target_language)
                        if st.session_state.translated_text.startswith("Translation failed"):
                            st.error(st.session_state.translated_text)
                        else:
                            st.success("Translation completed!")
                else:
                    st.warning("Please upload an audio file and transcribe it first.")

            if st.session_state.translated_text:
                st.subheader("Translated Transcript")
                display_translated_text(st.session_state.translated_text)
                srt_content = create_subtitle_file(st.session_state.translated_text, 'srt')
                vtt_content = create_subtitle_file(st.session_state.translated_text, 'vtt')
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="Download SRT",
                        data=srt_content,
                        file_name="translated_transcript.srt",
                        mime="text/plain"
                    )
                with col2:
                    st.download_button(
                        label="Download VTT",
                        data=vtt_content,
                        file_name="translated_transcript.vtt",
                        mime="text/plain"
                    )
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
            if st.session_state.translated_text:
                st.download_button(
                    label="Download Translated Transcript (TXT)",
                    data=st.session_state.translated_text,
                    file_name="translated_transcript.txt",
                    mime="text/plain",
                    key="download_translated"
                )
        else:
            st.info("Enter names for both speakers and click 'Generate Custom Transcript' to see the full transcript with custom names, or click 'Generate Default Transcript' to see the full transcript with generic speaker labels.")
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
