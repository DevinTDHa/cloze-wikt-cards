import argparse
import os
import re
from typing import Optional

import torch
from flask import Flask, request, send_from_directory
from transformers import pipeline
from cloze_wikt_cards.wiktionary_defs.fill_with_wikt import (
    get_entries,
    json_dump_entries,
    load_wiktextract,
)
from cloze_wikt_cards.anki_utils.deck import load_deck
import pandas as pd


class TranscriptionProcessor:
    def __init__(
        self,
        wikt_path: str,
        model_name: str = "vinai/PhoWhisper-medium",
        deck_path: Optional[str] = None,
    ):
        print("Loading Wiktionary data...")
        self.wikt_df = load_wiktextract(wikt_path)

        print(f"Loading the transcriber model {model_name}...")
        self.transcriber = pipeline(
            "automatic-speech-recognition",
            model=model_name,
            device="cuda" if torch.cuda.is_available() else "cpu",
        )
        # self.sampling_rate = self.transcriber.feature_extractor.sampling_rate
        self.deck_df: pd.DataFrame | None = None
        if deck_path is not None:
            print(f"Loading Deck: {deck_path}")
            cur_deck, _ = load_deck(deck_path)
            self.deck_df = pd.DataFrame(cur_deck)

    def get_wikt_entry(self, word: str) -> dict:
        found_entries = get_entries(self.wikt_df, word)

        if not found_entries.empty:
            # Assume we want to exclude entries that are already in the deck
            json_str, short_str = json_dump_entries(found_entries, word=word)
        else:
            json_str, short_str = "", ""

        return {"json": json_str, "short": short_str}

    def process_audio(
        self, audio_bytes: bytes, max_n_gram: int = 4
    ) -> tuple[str, dict, list[str]]:
        # Assume the audio is in a correct format for ffmpeg to read
        # and has the correct sampling rate can handle it.
        transcription: str = self.transcriber(audio_bytes)["text"]
        transcription = re.sub(r"(^\W|\W$)", "", transcription.lower())
        word_splits = transcription.split()

        result_dict = {}
        searched_words = []

        if max_n_gram > 0:
            for n in range(1, max_n_gram + 1):
                for j in range(len(word_splits)):
                    word = " ".join(word_splits[j : j + n])
                    if word in result_dict:
                        continue

                    result = self.get_wikt_entry(word)
                    result_dict[word] = result
                    searched_words.append(word)
        else:  # If max_n_gram is 0, search for the whole transcription
            word = transcription
            result = self.get_wikt_entry(word)
            result_dict[word] = result
            searched_words.append(word)

        result_dict = {k: v for k, v in result_dict.items() if v["json"]}

        existing_words = pd.Series()
        if self.deck_df is not None:
            searched = pd.Series(searched_words)
            existing_words: pd.Series = searched[searched.isin(self.deck_df["vi"])]

        return transcription, result_dict, existing_words.to_list()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ASR Adder Server")

    # Step 3: Add arguments for wikt_path, model_name, and deck
    parser.add_argument(
        "--wikt_path", type=str, required=True, help="Path to the Wiktionary JSONL file"
    )
    parser.add_argument(
        "--model_name", type=str, required=True, help="Name of the ASR model"
    )
    parser.add_argument("--deck", type=str, required=False, help="Name of the deck")

    # Step 4: Parse the arguments
    args = parser.parse_args()

    # Check if all files exist
    if not os.path.exists(args.wikt_path):
        raise FileNotFoundError(f"File not found: {args.wikt_path}")

    # Step 5: Use the parsed arguments to initialize the TranscriptionProcessor
    app = Flask(__name__)
    processor = TranscriptionProcessor(
        wikt_path=args.wikt_path, model_name=args.model_name, deck_path=args.deck
    )

    @app.route("/process_audio", methods=["POST"])
    def process_audio():
        if "audio" not in request.files:
            return "No audio file found", 400

        if "max_n_gram" in request.form:
            max_n_gram = int(request.form["max_n_gram"])
        else:
            max_n_gram = 4

        audio_file = request.files["audio"].read()

        # Debug, get the latest file
        if os.getenv("SERVER_DEBUG") == "1":
            with open("most_recent.wav", "wb") as f:
                f.write(audio_file)

        transcription, result, existing_words = processor.process_audio(
            audio_file, max_n_gram
        )
        print(f"Finished processing audio: {transcription}")
        return {
            "transcription": transcription,
            "result": result,
            "existing_words": existing_words,
        }

    @app.route("/")
    def serve_gui():
        return send_from_directory(
            os.path.join(os.getcwd(), "client-gui"),
            "gui.html",
        )

    @app.route("/deck", methods=["GET"])
    def deck():
        if processor.deck_df is not None:
            return (
                {"deck": len(processor.deck_df)},
                200,
                {"Content-Type": "application/json"},
            )
        else:
            return {"deck": 0}, 200, {"Content-Type": "application/json"}

    app.run(debug=False)
