import numpy as np
from find_examples import CorpusExamples
from tqdm import tqdm
import signal
import sys
import pickle
import shutil
import argparse


csv_cur = []
NA_FILLER = "None"


def save_examples(out_path):
    if csv_cur:
        with open(out_path, "w") as f:
            for entry in csv_cur:
                f.write(";".join(entry) + "\n")
    else:
        print("Error: No examples to save.")


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
            pickle.dump(csv_cur, open("fill_script.pickle", "wb"))

            sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Fills a CSV with examples from a corpus."
    )
    parser.add_argument("--corpus", type=str, help="Path to the corpus folder")
    parser.add_argument("--csv", type=str, help="Path to the input CSV file")
    parser.add_argument("--out", type=str, help="Path to the output CSV file")
    parser.add_argument(
        "--num_examples",
        type=int,
        default=10,
        help="Number of examples to fill each line",
    )
    parser.add_argument("--ex_sep", type=str, default="|", help="Example separator")

    num_examples = 10
    args = parser.parse_args()
    csv_path = args.csv
    out_path = args.out
    num_examples = args.num_examples
    ex_sep = args.ex_sep

    # Check all arguments filled
    if not all([csv_path, out_path, args.corpus]):
        print("Error: Missing arguments")
        sys.exit(1)

    corpus = CorpusExamples(args.corpus)

    # backup the original file first
    shutil.copy(csv_path, csv_path + ".bak")
    setup_signal_handler(out_path)

    with open(csv_path, "r") as f:
        csv_cur = [line.strip().split(";") for line in f]

    try:
        with tqdm(total=len(csv_cur)) as pbar:
            for entry in csv_cur:
                if len(entry) != 3:
                    pbar.update(1)
                    continue
                vi, en, exs = entry
                if exs == NA_FILLER:
                    pbar.update(1)
                    continue
                pbar.set_postfix(current=vi)

                existing_examples = exs.split(ex_sep) if exs else []
                num_ex_filled = len(existing_examples) if exs else 0
                if num_ex_filled >= num_examples:
                    pbar.update(1)
                    continue
                found_exs = corpus.find_examples(vi)[: num_examples - num_ex_filled]
                if len(found_exs) == 0:
                    entry[2] = NA_FILLER if not exs else exs
                    continue

                entry[2] = ex_sep.join(
                    existing_examples + [e["text"] for e in found_exs]
                )
                pbar.update(1)
    except Exception as e:
        print("Error:", e)
        save_examples(out_path)
        sys.exit(1)

    # Save the results
    save_examples(out_path)
    print("Done!")
