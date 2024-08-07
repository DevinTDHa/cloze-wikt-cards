import csv
import json
from typing import List

import fire
import pandas as pd
from tqdm import tqdm


def load_wiktextract(file_path: str) -> pd.DataFrame:
    """Loads JSONL file with wiktextract data (See: https://github.com/tatuylonen/wiktextract)"""

    with open(file_path) as f:
        lines = f.read().splitlines()

    line_dicts: List[dict] = [json.loads(line) for line in lines]
    df: pd.DataFrame = pd.DataFrame(line_dicts)

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
        ).replace(
            word, "___"
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


def load_deck(deck_csv_path: str) -> tuple[list[dict], list[str]]:
    deck: list[dict] = []
    metadata: list[str] = []

    with open(deck_csv_path, "r") as csv_file:
        # Extract the metadata comment strings at the beginning of the file
        for line in csv_file:
            if line.startswith("#"):
                metadata.append(line)
            else:
                break

        reader = csv.reader(csv_file, delimiter="\t")
        for row in reader:
            assert (
                len(row) >= 4
            ), "The deck should have four or five fields: id, vi, en, examples, [wiktdata]. (Make sure you export with id)"
            row_dict = {
                "id": row[0],
                "vi": row[1],
                "en": row[2],
                "examples": row[3],
            }
            if len(row) == 5:
                row_dict["wiktdata"] = row[4]
            deck.append(row_dict)

    return deck, metadata


def extract_and_fill(
    wikt_extract_path: str, deck_csv_path: str, filters: str = "", refill: bool = False
):
    """Extracts and fills the Anki deck with Wiktionary data.

    Parameters
    ----------
    wikt_extract_path : str
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
    wikt_df = load_wiktextract(wikt_extract_path)

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
                note_dict["wiktdata"] = ""
                not_found.append(note_dict["vi"])

    out_path = deck_csv_path.split("/")[-1].replace(".", "_filled.")
    with open(out_path, "w", newline="", encoding="utf-8") as csv_file:
        fieldnames = ["id", "vi", "en", "examples", "wiktdata"]
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
            delimiter="\t",
            quoting=csv.QUOTE_NONE,
            quotechar="",
            escapechar="",
        )

        for metadata_line in metadata:
            csv_file.write(metadata_line)

        for note_dict in deck:
            writer.writerow(note_dict)

    print(f"Deck filled and saved to {out_path}")

    if not_found:
        print(
            f"Definitions for {len(not_found)} words were not found. They were written to not_found.txt"
        )
        with open("not_found.txt", "w", encoding="utf-8") as f:
            for word in not_found:
                f.write(word + "\n")


if __name__ == "__main__":
    fire.Fire(extract_and_fill)
