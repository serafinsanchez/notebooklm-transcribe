# NotebookLM Multi-Language Transcriber

A Streamlit web app for transcribing audio files in multiple languages using [AssemblyAI](https://www.assemblyai.com/) and optionally translating transcripts with [Google Cloud Translate](https://cloud.google.com/translate).

## Features

- Upload audio files (`.mp3`, `.wav`, `.ogg`)
- Transcribe in multiple languages
- Assign custom speaker names
- Translate transcripts to other languages
- Download transcripts and subtitles (TXT, SRT, VTT)
- Clean, modern UI

## Demo

![App Demo](/screenshot.png)

## Setup

1. **Clone the repo:**
   ```bash
   git clone https://github.com/yourusername/assembly-ai.git
   cd assembly-ai
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   - Copy `.env.example` to `.env` and fill in your keys:
     ```
     cp .env.example .env
     ```
   - Add your [AssemblyAI API key](https://www.assemblyai.com/) and [Google Cloud credentials](https://cloud.google.com/translate/docs/setup).

4. **Run the app:**
   ```bash
   streamlit run transcribe_multilang.py
   ```

## Usage

- Select the source language.
- Upload your audio file.
- Wait for transcription.
- (Optional) Assign custom speaker names.
- (Optional) Translate the transcript.
- Download your results.

## License

MIT License

## Credits

- [AssemblyAI](https://www.assemblyai.com/)
- [Google Cloud Translate](https://cloud.google.com/translate)
- UI inspired by shadcn 