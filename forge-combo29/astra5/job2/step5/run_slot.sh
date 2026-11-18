#!/usr/bin/env bash
# Usage: bash run_slot.sh EXE EPD_DIR JOB2_DIR OUTPUT_DIR
set -euo pipefail
exe=$1
epds=$2
job=$3
out=$4
script_dir=$(dirname "$0")
for phase in first20 full; do
    mkdir -p "$out/$phase"
    args=()
    check_args=()
    if [[ $phase == first20 ]]; then
        args=(--first 20)
        check_args=(--first20)
    fi
    for suite in G O; do
        for setting in base fhb7 del del_fhb7; do
            python3 "$job/run_counts.py" set "$exe" "$epds/$suite.epd" "$setting" \
                "$out/$phase/${suite}_${setting}.tsv" --slots 17 "${args[@]}"
        done
    done
    python3 "$script_dir/check_slot.py" "$job/step4" "$out/$phase" "${check_args[@]}" \
        | tee "$out/$phase-summary.txt"
done
