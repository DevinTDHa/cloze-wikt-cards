from server import TranscriptionProcessor

if __name__ == "__main__":
    processor = TranscriptionProcessor(
        wikt_path="/mnt/SSDSHARED/VN/wikt/kaikki.org-dictionary-Vietnamese.jsonl",
        model_name="vinai/PhoWhisper-medium",
        deck_path="/home/ducha/Dropbox/TiếngViệt/vocab/vn_latest.txt",
    )

    test_file = (
        "/home/ducha/Dropbox/Projects/cloze-wikt-cards/asr-adder/notebooks/sample.wav"
    )

    with open(test_file, "rb") as f:
        audio_bytes = f.read()

    transcription, result, existing_words = processor.process_audio(audio_bytes)
    print("Transcription:", transcription)
    print("Existing words:", existing_words)

    for r, v in result.items():
        print("Word:", r)
        print("  Short:", v["short"])
