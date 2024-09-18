import argparse
import json
import re
import shutil
from typing import List

import pandas as pd
from tqdm import tqdm
from anki_utils.deck import load_deck, write_deck


def load_wiktextract(file_path: str) -> pd.DataFrame:
    """Loads JSONL file with wiktextract data (See: https://github.com/tatuylonen/wiktextract)"""
    df: pd.DataFrame = pd.read_json(file_path, lines=True)
    return df.fillna("")


def get_entries(wikt_df: pd.DataFrame, word: str) -> pd.DataFrame:
    return wikt_df[wikt_df["word"].str.lower() == word.lower()]


def process_senses(
    senses: List[dict], word: str, filter_words: List[str] = []
) -> tuple[List[dict], str]:
    """Processes Wiktionary senses and extracts meanings and examples.

    Parameters
    ----------
    senses : List[dict]
        The senses extracted from Wiktionary

    Returns
    -------
    tuple[List[dict], str]
        A list of processed senses and a string representation of the meanings
    """
    senses_processed = []

    for sense in senses:
        if "glosses" not in sense and "raw_glosses" not in sense:
            continue

        meaning = (
            sense["raw_glosses"][0]
            if "raw_glosses" in sense
            else sense["glosses"][0]  # Always take the first, main meaning
        )
        meaning = re.sub(
            word, "___", meaning, flags=re.IGNORECASE
        )  # So that when guessing, the word is not given away

        if filter_words and any(
            f_word.lower() in meaning.lower() for f_word in filter_words
        ):
            continue

        # Check if the meaning is already in the list
        sense_dict = next(
            (s for s in senses_processed if s["meaning"] == meaning),
            {"meaning": meaning},
        )
        # if the only key was "meaning"
        created_new = len(sense_dict) == 1

        if "examples" in sense:
            examples = sense_dict.get("examples", [])
            for ex in sense["examples"]:
                if "english" not in ex:
                    examples.append(ex["text"])
                else:
                    examples.append(ex["text"] + " ― " + ex["english"])
            sense_dict["examples"] = examples
        if created_new:  # Only append if a new sense dict was created
            senses_processed.append(sense_dict)

    meanings_formatted = [sense["meaning"] for sense in senses_processed]
    senses_str = "; ".join(meanings_formatted)
    return senses_processed, senses_str


def json_dump_entries(
    entries: pd.DataFrame, word: str, filter_words: List[str] = []
) -> tuple[str, str]:
    """Converts Wiktionary entries to a JSON string and a short string representation (for the back field.)

    Parameters
    ----------
    entries : pd.DataFrame
        Entries that were extracted from Wiktionary

    Returns
    -------
    tuple[str, str]
        Converted JSON string and a short string representation
    """
    out_entries = []
    entries_short_str = []
    for _, row in entries.iterrows():
        cur_entry = {}
        cur_entry["pos"] = row["pos"]

        if "synonyms" in row and row["synonyms"]:  # Synonyms can be NaN
            cur_entry["synonyms"] = [syn["word"] for syn in row["synonyms"]]

        if "etymology_text" in row and row["etymology_text"]:
            cur_entry["etymology"] = row["etymology_text"]

        cur_entry["meanings"], senses_string = process_senses(
            row["senses"], word=word, filter_words=filter_words
        )
        if not cur_entry["meanings"]:
            continue

        out_entries.append(cur_entry)

        entries_short_str.append(f"{row['pos']}: {senses_string}")

    short_meanings = " | ".join(entries_short_str)

    json_string = json.dumps(out_entries, ensure_ascii=False)
    return json_string, short_meanings


def extract_and_fill(
    wikt_extract: str,
    deck_csv_path: str,
    filters: str = "Sino-Vietnamese Reading of",
    refill: bool = False,
):
    """Extracts and fills the Anki deck with Wiktionary data.

    Parameters
    ----------
    wikt_extract : str
        Path to the wiktextract JSONL file
    deck_csv_path : str
        Path to the Anki deck CSV file, which uses tab as a separator by default. The deck should be exported with identifiers.
    filters : str, optional
        Test
    refill : bool, optional
        Refill the deck even if it has Wiktionary data already
    """
    # Currently, the deck consist of three fields (vi, en, examples). Extract the deck to a list:
    print("Loading the deck and Wiktionary data...")
    deck, metadata = load_deck(deck_csv_path)

    print("Loading Wiktionary data...")
    wikt_df = load_wiktextract(wikt_extract)

    filter_words = filters.split(";")
    print("Filters:", filter_words)

    not_found = []

    # Process the deck
    with tqdm(total=len(deck)) as pbar:
        for note_dict in deck:
            pbar.set_description(f"Processing {note_dict['vi']}")
            pbar.update(1)

            # Skip the word if it already has Wiktionary data and we are not refilling
            if "wiktdata" in note_dict and note_dict["wiktdata"] and not refill:
                continue

            found_entries = get_entries(wikt_df, note_dict["vi"])
            if not found_entries.empty:
                json_str, short_str = json_dump_entries(
                    found_entries, word=note_dict["vi"], filter_words=filter_words
                )
                note_dict["en"] = short_str
                note_dict["wiktdata"] = json_str
            else:
                note_dict["wiktdata"] = "None"
                not_found.append(note_dict["vi"])

    out_path = deck_csv_path.split("/")[-1].replace(".", "_wikt.")
    print("Writing the deck...")
    write_deck(deck, metadata, out_path)

    if not_found:
        print(
            f"Definitions for {len(not_found)} words were not found. They were written to not_found.txt"
        )
        with open("not_found.txt", "w", encoding="utf-8") as f:
            for word in not_found:
                f.write(word + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extracts and fills the Anki deck with Wiktionary data."
    )
    parser.add_argument(
        "--wikt_extract", type=str, help="Path to the wiktextract JSONL file"
    )
    parser.add_argument(
        "--deck",
        type=str,
        help="Path to the Anki deck CSV file, which uses tab as a separator by default. The deck should be exported with identifiers.",
    )
    parser.add_argument(
        "--filters",
        type=str,
        default="Sino-Vietnamese Reading of",
        help="Semicolon (;) separated list of filters",
    )
    parser.add_argument(
        "--refill",
        action="store_true",
        help="Refill the deck even if it has Wiktionary data already",
    )

    args = parser.parse_args()

    # Backup the original deck first
    shutil.copy(args.deck, args.deck + ".bak")

    extract_and_fill(args.wikt_extract, args.deck, args.filters, args.refill)
