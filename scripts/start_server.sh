#!/bin/bash
# export SERVER_DEBUG=1
uv run src/asr_adder/server/server.py \
    --wikt_path "/mnt/SSDSHARED/VN/dicts/wikt/kaikki.org-dictionary-Vietnamese.jsonl" \
    --wikt_path "/mnt/SSDSHARED/VN/dicts/FreeVietnameseDictionaryProjectExport/data/vietanh.dict.jsonl" \
    --model_name "vinai/PhoWhisper-medium" \
    --deck "/home/ducha/Dropbox/TiếngViệt/vocab/vn_latest.txt"
