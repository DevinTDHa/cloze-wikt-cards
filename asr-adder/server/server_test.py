from server import TranscriptionProcessor

if __name__ == "__main__":
    processor = TranscriptionProcessor(
        wikt_path="/mnt/SSDSHARED/VN/wikt/kaikki.org-dictionary-Vietnamese.jsonl",
        model_name="vinai/PhoWhisper-medium",
    )
    test_file = (
        "/home/ducha/Dropbox/Projects/cloze-wikt-cards/asr-adder/notebooks/sample.wav"
    )
    with open(test_file, "rb") as f:
        audio_bytes = f.read()

    result = processor.process_audio(audio_bytes)

    for r, v in result.items():
        print("Word:", r)
        print("  Short:", v["short"])
