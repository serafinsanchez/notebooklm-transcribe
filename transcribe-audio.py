import assemblyai as aai

aai.settings.api_key = "61d241cdcdf4455d8af14f4d40514ebc"

# You can use a local filepath:
# audio_file = "./example.mp3"

# Or use a publicly-accessible URL:
audio_file = (
    "https://assembly.ai/wildfires.mp3"
)

config = aai.TranscriptionConfig(
  speaker_labels=True,
)

transcript = aai.Transcriber().transcribe(audio_file, config)

speaker_mapping = {}
speaker_names = ["Karen", "Peter"]
current_speaker = 0

for utterance in transcript.utterances:
    if utterance.speaker not in speaker_mapping:
        if current_speaker < len(speaker_names):
            speaker_mapping[utterance.speaker] = speaker_names[current_speaker]
            current_speaker += 1
        else:
            speaker_mapping[utterance.speaker] = f"Speaker {current_speaker + 1}"
    
    print(f"{speaker_mapping[utterance.speaker]}: {utterance.text}")