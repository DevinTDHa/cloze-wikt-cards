"""
Script to update tags in a deck by merging with tags from a master deck
and appending additional tags.
"""

import pandas as pd
import argparse
import sys
from pathlib import Path


def load_deck(file_path: str) -> pd.DataFrame:
    """Load a deck from TSV file with the expected column structure."""
    try:
        deck = pd.read_csv(
            file_path,
            comment="#",
            sep="\t",
            header=None,
            names=["id", "vi", "en", "ex", "wikt", "tags"],
            keep_default_na=False,
        )
        deck["tags"] = deck["tags"].str.split(" ")
        return deck
    except Exception as e:
        print(f"Error loading file {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


def merge_tags(
    all_notes_deck: pd.DataFrame, target_deck: pd.DataFrame, extra_tags: list
) -> pd.DataFrame:
    """
    Merge tags from all_notes_deck into target_deck and append extra_tags.

    Args:
        all_notes_deck: DataFrame with all notes containing existing tags
        target_deck: DataFrame with target deck to update
        extra_tags: List of additional tags to append

    Returns:
        Updated target_deck with merged tags
    """
    # Merge target_deck with all_notes on the 'vi' column
    merged = target_deck.merge(
        all_notes_deck[["vi", "tags"]], on="vi", how="left", suffixes=("", "_all_notes")
    )

    # Update the tags in target_deck with the tags from all_notes where there's a match
    target_deck["tags"] = merged["tags_all_notes"].combine_first(target_deck["tags"])

    # Check matches for reporting
    matches = target_deck["vi"].isin(all_notes_deck["vi"])
    print(f"Number of matches: {matches.sum()}")
    print(f"Total notes in target deck: {len(target_deck)}")
    print(f"Percentage of matches: {matches.sum()/len(target_deck)*100:.1f}%")

    # Add extra tags to each entry
    target_deck["tags"] = target_deck["tags"].apply(
        lambda x: x + extra_tags if isinstance(x, list) else extra_tags
    )

    # Convert tags back to space-separated string
    target_deck["tags"] = target_deck["tags"].apply(lambda x: " ".join(x))

    return target_deck


def main():
    """Main function to process deck tags."""
    parser = argparse.ArgumentParser(
        description="Update tags in a deck by merging with a master deck and adding extra tags"
    )
    parser.add_argument(
        "all_notes_path",
        help="Path to the TSV file containing all notes with existing tags",
    )
    parser.add_argument(
        "target_deck_path",
        help="Path to the TSV file containing the deck to be updated",
    )
    parser.add_argument(
        "extra_tags",
        help="Space-separated string of additional tags to append (e.g. 'VP101 VP101L2')",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (default: adds '_merged_tags' suffix to target deck name)",
    )

    args = parser.parse_args()

    # Parse extra tags
    extra_tags = args.extra_tags.split()
    if not extra_tags:
        print("Error: No extra tags provided", file=sys.stderr)
        sys.exit(1)

    # Load decks
    print(f"Loading all notes from: {args.all_notes_path}")
    all_notes = load_deck(args.all_notes_path)

    print(f"Loading target deck from: {args.target_deck_path}")
    target_deck = load_deck(args.target_deck_path)

    print(f"Extra tags to add: {extra_tags}")

    # Merge tags
    print("\nMerging tags...")
    updated_deck = merge_tags(all_notes, target_deck, extra_tags)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        target_path = Path(args.target_deck_path)
        output_path = (
            target_path.parent / f"{target_path.stem}_merged_tags{target_path.suffix}"
        )

    # Export to TSV
    print(f"\nExporting to: {output_path}")
    updated_deck.to_csv(
        output_path,
        sep="\t",
        index=False,
        header=False,
    )

    print("Done!")


if __name__ == "__main__":
    main()
