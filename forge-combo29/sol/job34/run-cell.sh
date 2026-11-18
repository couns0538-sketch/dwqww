#!/usr/bin/env bash
set -euo pipefail
cd /workspace/work/sol-job34
label=${1:?provide a run label}
observer=()
case "$label" in
    K24a|K24b) build=r15d; mode=softnodes; first=1001; last=1020; quiet=93; cpu=1 ;;
    C24)       build=r15d; mode=softnodes; first=1001; last=1020; quiet=60; cpu=1 ;;
    T1-r15d)   build=r15d; mode=softnodes; first=1001; last=2000; quiet=93; cpu=1 ;;
    T1-kF)     build=kF;   mode=softnodes; first=1001; last=2000; quiet=93; cpu=2 ;;
    T2-r15d)   build=r15d; mode=nodes; first=2001; last=2200; quiet=93; cpu=1 ;;
    T2-kF)     build=kF;   mode=nodes; first=2001; last=2200; quiet=93; cpu=2 ;;
    T2-observed-r15d) build=r15d; mode=nodes; first=2001; last=2200; quiet=93; cpu=1; observer=(--record-missing-info) ;;
    T2-observed-kF)   build=kF;   mode=nodes; first=2001; last=2200; quiet=93; cpu=2; observer=(--record-missing-info) ;;
    *) printf 'Unknown run %s\n' "$label" >&2; exit 2 ;;
esac
read -r engine_sha _ < "build-evidence/$build.binary.sha256"
cutoff=$(( $(cat claim.epoch) + 3000 ))
if (( $(date +%s) >= cutoff )); then
    printf 'Minute 50 reached before %s could start\n' "$label" >&2
    exit 3
fi
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/work/sol-job3/deps
mkdir -p raw
date -u +%FT%TZ > "$label.wrapper.start.stamp"
status=0
taskset -c "$cpu" python3 -u whole_games34.py "$build/forge" \
    /workspace/work/sol-job12/UHO_Lichess_4852_v1.epd net768.nnue "raw/$label.records.txt" \
    "$mode" "$first" "$last" --lmr-quiet-base "$quiet" --expected-engine-sha "$engine_sha" \
    --deadline "$cutoff" "${observer[@]}" > "raw/$label.run.txt" 2>&1 || status=$?
date -u +%FT%TZ > "$label.wrapper.end.stamp"
printf '%d\n' "$status" > "$label.wrapper.exit"
exit "$status"
