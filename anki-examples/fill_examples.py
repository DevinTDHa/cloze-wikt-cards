import csv
import pickle
import random
import sys
import csv
import random
import os
from find_examples import CorpusExamples
import signal


BOLD_ORANGE_START = "\033[1m\033[93m"
BOLD = "\033[1m"
RESET_SEQ = "\033[0m"


def find_examples(vietnamese_word):
    # This function should return a list of examples for the given Vietnamese word.
    # Replace the content of this function with your actual implementation.
    return ["Example 1", "Example 2", "Example 3", "..."]


def print_choices(vi, en, examples, total_missing_examples):
    print(f"\n\nMissing Examples   : {total_missing_examples}")
    print(f"Vietnamese word    : {BOLD_ORANGE_START}{vi}{RESET_SEQ}")
    print(f"English translation: {BOLD}{en}{RESET_SEQ}\n")
    print(
        f"Found {len(examples)} total examples, showing the first 10.\n"
        "Choose an example to add (0-9) or press 'r' to shuffle and refresh the list, 'z' to undo or 's' to skip:"
    )
    EXAMPLES_LIMIT = 10

    for i, example in enumerate(examples[:EXAMPLES_LIMIT]):
        file = example["file"][:33]
        text = example["text"]
        # num_words = example["num_words"]
        start = example["start"]
        end = example["end"]

        markup_text = (
            text[:start] + BOLD_ORANGE_START + text[start:end] + RESET_SEQ + text[end:]
        )
        print(f"{i}. {file:33s}... : {markup_text}")


def main(csv_path, corpus_folder):
    corpus_examples = CorpusExamples(corpus_folder)

    VIE_COLUMN_INDEX = 0
    ENG_COLUMN_INDEX = 1
    EXAMPLE_COLUMN_INDEX = 2

    with open(csv_path, mode="r", encoding="utf-8") as file:
        csv_reader = csv.reader(file, delimiter=";")
        rows = list(csv_reader)

    def signal_handler(signal, frame):
        print("\n\nInterrupted. Saving progress...")
        try:
            save_examples(csv_path, rows)
            sys.exit(0)
        except Exception as e:
            print(
                "Error saving progress, saving progress as `current_progress.pickle`:",
                e,
            )
            pickle.dump(rows, open("current_progress.pickle", "wb"))
            sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)

    total_missing_examples = sum(not row[EXAMPLE_COLUMN_INDEX] for row in rows)
    examples_to_add = []
    for row in rows:
        if not row[EXAMPLE_COLUMN_INDEX]:
            vi = row[VIE_COLUMN_INDEX]
            en = row[ENG_COLUMN_INDEX]
            examples = corpus_examples.find_examples(vi)

            if not examples:
                print(f"\n\nNo examples found for '{vi}'.")
                continue

            print_choices(
                vi, en, examples, total_missing_examples - len(examples_to_add)
            )

            while True:
                choice = input("Your choice: ").strip().lower()
                print("Chose:", choice)
                if choice == "r":
                    random.shuffle(examples)
                    print_choices(vi, en, examples, total_missing_examples)
                elif choice == "z" and examples_to_add:
                    last_entry = examples_to_add.pop()
                    print(f"Removed last entry: {last_entry}")
                    break
                elif choice.isdigit() and 0 <= int(choice) <= 9:
                    selected_example = examples[int(choice)]
                    examples_to_add.append((row[VIE_COLUMN_INDEX], selected_example))
                    row[EXAMPLE_COLUMN_INDEX] = selected_example
                    break
                elif choice == "s":
                    break
                else:
                    print("Invalid input. Please try again.")

    save_examples(csv_path, rows)


def save_examples(csv_path, rows):
    if not csv_path.endswith("_filled.csv"):
        result_path = csv_path.replace(".csv", "_filled.csv")
    else:
        result_path = csv_path
    with open(result_path, mode="w", encoding="utf-8", newline="") as file:
        csv_writer = csv.writer(file, delimiter=";")
        csv_writer.writerows(rows)
    print(f"\nCSV file updated with examples. Saved as '{result_path}'.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python fill_examples.py <corpus_folder> <csv_path>")
    else:
        corpus_folder = sys.argv[1]
        csv_path = sys.argv[2]

        # Check if the folder and file exists
        if not os.path.exists(corpus_folder):
            print(f"Folder '{corpus_folder}' does not exist.")
            sys.exit(1)
        if not os.path.exists(csv_path):
            print(f"File '{csv_path}' does not exist.")
            sys.exit(1)
        filled_csv_path = csv_path.replace(".csv", "_filled.csv")
        if os.path.exists(filled_csv_path):
            print(f"File '{filled_csv_path}' already exists. Loading...")
            csv_path = filled_csv_path

        main(csv_path, corpus_folder)
