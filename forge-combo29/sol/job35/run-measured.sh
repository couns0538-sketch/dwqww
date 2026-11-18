#!/usr/bin/env bash
set -euo pipefail
cd /workspace/work/sol-job35
test -s step0.push.stamp
test -s controls.push.stamp
test -s prediction.push.stamp
cutoff=$(( $(cat claim.epoch) + 3000 ))
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/work/sol-job3/deps

for phase in U1 U2; do
    if (( $(date +%s) >= cutoff )); then break; fi
    case "$phase" in U1) first=1; last=1000 ;; U2) first=1001; last=1500 ;; esac
    left_openings="openings/$phase-r15d.openings.txt"
    right_openings="openings/$phase-kF.openings.txt"
    {
        printf 'cmp %s %s\n' "$left_openings" "$right_openings"
        cmp "$left_openings" "$right_openings"
        printf 'Exit 0\n'
        sha256sum "$left_openings" "$right_openings"
        date -u +%FT%TZ
    } > "$phase.openings-cmp.txt"
    bash run-cell.sh "$phase-r15d" &
    left_pid=$!
    bash run-cell.sh "$phase-kF" &
    right_pid=$!
    left_exit=0 right_exit=0 cmp_exit=0
    wait "$left_pid" || left_exit=$?
    wait "$right_pid" || right_exit=$?
    left="raw/$phase-r15d.records.txt"
    right="raw/$phase-kF.records.txt"
    cmp "$left" "$right" > "$phase.cmp.raw.txt" 2>&1 || cmp_exit=$?
    {
        printf 'cmp %s %s\n' "$left" "$right"
        cat "$phase.cmp.raw.txt"
        printf 'Exit %d\n' "$cmp_exit"
    } > "$phase.cmp.txt"
    test "$cmp_exit" -le 1
    python3 compare_games35.py "$left_openings" "$right_openings" "$left" "$right" \
        --first "$first" --last "$last" --json "$phase.json" --prefix "$phase.first-position.txt" > "$phase.txt"
    bash publish-phase.sh "$phase"
    if (( left_exit != 0 || right_exit != 0 )); then
        printf '%s r15d exit %d, kF exit %d\n' "$phase" "$left_exit" "$right_exit"
        exit 0
    fi
done
