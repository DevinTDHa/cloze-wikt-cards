import csv


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


def write_deck(deck: list[dict], metadata: list[str], out_path: str):
    with open(out_path, "w", newline="", encoding="utf-8") as csv_file:
        fieldnames = ["id", "vi", "en", "examples", "wiktdata"]
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
            delimiter="\t",
            quoting=csv.QUOTE_NONE,
            quotechar=None,
            escapechar=None,
        )

        for metadata_line in metadata:
            csv_file.write(metadata_line)

        for note_dict in deck:
            writer.writerow(note_dict)

    print(f"Deck filled and saved to {out_path}")
