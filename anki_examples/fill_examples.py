from anki_utils.deck import load_deck, write_deck
from find_examples import CorpusExamples
from tqdm import tqdm
import signal
import sys
import pickle
import shutil
import argparse


deck = []
metadata = []
NA_FILLER = "None"


def save_examples(out_path):
    if deck:
        write_deck(deck, metadata, out_path)
    else:
        print("Error: No examples to save.")
        sys.exit(1)


def setup_signal_handler(out_path):
    def signal_handler(signal, frame):
        print("\n\nInterrupted. Saving progress...")
        try:
            save_examples(out_path)
            sys.exit(0)
        except Exception as e:
            print(
                "Error saving progress, saving progress as `current_progress.pickle`:",
                e,
            )
            pickle.dump(deck, open("fill_script.pickle", "wb"))

            sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fills a CSV with examples from a corpus."
    )
    parser.add_argument("--deck", type=str, help="Path to the input CSV deck")
    parser.add_argument("--out", type=str, help="Path to the output CSV file")
    parser.add_argument("--corpus", type=str, help="Path to the corpus folder")
    parser.add_argument(
        "--num_examples",
        type=int,
        default=20,
        help="Number of examples to fill each line",
    )

    args = parser.parse_args()
    csv_path = args.deck
    out_path = args.out
    num_examples = args.num_examples
    ex_sep = "|"

    # Check all arguments filled
    if not all([csv_path, out_path, args.corpus]):
        print("Error: Missing arguments")
        sys.exit(1)

    corpus = CorpusExamples(args.corpus)

    # backup the original file first
    shutil.copy(csv_path, csv_path + ".ex_bak")
    setup_signal_handler(out_path)

    # Load the deck
    deck, metadata = load_deck(csv_path)

    try:
        with tqdm(total=len(deck)) as pbar:
            for card in deck:
                if card["examples"] == NA_FILLER:
                    pbar.update(1)
                    continue
                pbar.set_postfix(current=card["vi"])

                exs = card["examples"].strip()
                existing_examples = list(set(exs.split(ex_sep))) if exs else []
                num_ex_filled = len(existing_examples) if exs else 0

                pbar.update(1)

                if num_ex_filled >= num_examples:
                    continue

                found_exs = corpus.find_examples(
                    card["vi"], num_examples=num_examples - num_ex_filled
                )
                if len(found_exs) == 0 and num_ex_filled == 0:
                    card["examples"] = NA_FILLER
                    continue

                card["examples"] = ex_sep.join(
                    existing_examples + [e["text"] for e in found_exs]
                )

    except Exception as e:
        print("Error:", e)
        save_examples(out_path)
        sys.exit(1)

    # Save the results
    save_examples(out_path)
    print("Examples Done!")
