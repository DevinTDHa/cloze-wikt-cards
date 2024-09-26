#!/bin/bash
set -e

USAGE="Usage: fill_all.sh --deck <deck_name> --out <output_dir> --wikt_extract <wiktionary_extract> --corpus <corpus_dir> [--refill]"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
    --deck)
        DECK="$2"
        shift
        ;;
    --out)
        OUT="$2"
        shift
        ;;
    --wikt_extract)
        WIKT_EXTRACT="$2"
        shift
        ;;
    --corpus)
        CORPUS="$2"
        shift
        ;;
    --refill)
        REFILL="--refill"
        shift
        ;;
    *)
        echo "Unknown parameter passed: $1"
        echo "$USAGE"
        exit 1
        ;;
    esac
    shift
done

# Check if all arguments are provided
if [ -z "$DECK" ] || [ -z "$OUT" ] || [ -z "$WIKT_EXTRACT" ] || [ -z "$CORPUS" ]; then
    echo "$USAGE"
    exit 1
fi

echo "Deck: $DECK"
echo "Output: $OUT"
echo "Wiktionary Extract: $WIKT_EXTRACT"
echo "Corpus: $CORPUS"

echo "FILLING WITH WIKTIONARY DEFINITIONS..."
python3 wiktionary_defs/fill_with_wikt.py --deck $DECK --out $OUT --wikt_extract $WIKT_EXTRACT $REFILL

echo "FILLING WITH EXAMPLE SENTENCES..."
python3 anki_examples/fill_examples.py --deck $OUT --out $OUT --corpus $CORPUS

echo "All Done!"
