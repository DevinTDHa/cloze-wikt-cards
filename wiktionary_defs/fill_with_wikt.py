import json
import pandas as pd
from typing import List
import fire
from tqdm import tqdm


def load_wiktextract(file_path: str) -> pd.DataFrame:
    """Loads JSONL file with wiktextract data (See: https://github.com/tatuylonen/wiktextract)"""

    with open(file_path) as f:
        lines = f.read().splitlines()

    line_dicts: List[dict] = [json.loads(line) for line in lines]
    df: pd.DataFrame = pd.DataFrame(line_dicts)

    return df.fillna("")


def get_entries(wikt_df: pd.DataFrame, word: str) -> pd.DataFrame:
    return wikt_df[wikt_df["word"] == word]


def process_senses(senses: List[dict]) -> tuple[List[dict], str]:
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
            sense["raw_glosses"][0] if "raw_glosses" in sense else sense["glosses"][0]
        )  # Always take the first, main meaning

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


def json_dump_entries(entries: pd.DataFrame) -> tuple[str, str]:
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
        cur_entry["meanings"], senses_string = process_senses(row["senses"])
        if not cur_entry["meanings"]:
            continue
        out_entries.append(cur_entry)

        entries_short_str.append(f"{row['pos']}: {senses_string}")

    short_meanings = " | ".join(entries_short_str)

    return json.dumps(out_entries), short_meanings


def fill_deck(deck: List[dict]):
    """Fills the Anki deck with Wiktionary data.

    Parameters
    ----------
    deck : List[dict]
        The Anki deck that will be filled with Wiktionary data
    """
    for row in tqdm(deck):
        pass


def extract_and_fill(wikt_extract_path: str, deck_csv_path: str):
    """Extracts and fills the Anki deck with Wiktionary data.

    Parameters
    ----------
    wikt_extract_path : str
        Path to the wiktextract JSONL file
    deck_csv_path : str
        Path to the Anki deck CSV file, which uses tab as a separator by default. The deck should be exported with identifiers.
    """
    # Currently, the deck consist of three fields. Extract the deck to a list:
    # TODO


    json_str, short_str = json_dump_entries(ex_entries)
    with open("example.json", "w", encoding="utf-8") as f:
        f.write(json_str)


if __name__ == "__main__":
    fire.Fire(extract_and_fill)
