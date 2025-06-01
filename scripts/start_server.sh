#!/bin/bash
# export SERVER_DEBUG=1
cd /home/ducha/Dropbox/Projects/cloze-wikt-cards/asr-adder/ || exit
/home/ducha/mambaforge/envs/rapids-24.08/bin/python server/server.py \
    --wikt_path "/mnt/SSDSHARED/VN/dicts/wikt/kaikki.org-dictionary-Vietnamese.jsonl" \
    --wikt_path "/mnt/SSDSHARED/VN/dicts/FreeVietnameseDictionaryProjectExport/data/vietanh.dict.jsonl" \
    --model_name "vinai/PhoWhisper-medium" \
    --deck "/home/ducha/Dropbox/TiếngViệt/vocab/vn_latest.txt"
