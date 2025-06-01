#!/bin/bash
python fill_examples.py \
    --deck "/home/ducha/Dropbox/TiếngViệt/vocab/vn_latest.txt" \
    --corpus /mnt/SSDSHARED/VN/corpora/subs_segmented \
    --out deck_refilled.tsv \
    --refill
