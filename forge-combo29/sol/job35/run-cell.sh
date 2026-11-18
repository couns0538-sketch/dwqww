#!/usr/bin/env bash
set -euo pipefail
cd /workspace/work/sol-job35
previous=/workspace/work/sol-job34
label=${1:?provide a run label}
case "$label" in
    K25a|K25b) build=r15d; first=1; last=20; quiet=93; cpu=1 ;;
    C25)       build=r15d; first=1; last=20; quiet=60; cpu=1 ;;
    U1-r15d)   build=r15d; first=1; last=1000; quiet=93; cpu=1 ;;
    U1-kF)     build=kF;   first=1; last=1000; quiet=93; cpu=2 ;;
    U2-r15d)   build=r15d; first=1001; last=1500; quiet=93; cpu=1 ;;
    U2-kF)     build=kF;   first=1001; last=1500; quiet=93; cpu=2 ;;
    *) printf 'Unknown run %s\n' "$label" >&2; exit 2 ;;
esac
read -r engine_sha _ < "$previous/build-evidence/$build.binary.sha256"
cutoff=$(( $(cat claim.epoch) + 3000 ))
if (( $(date +%s) >= cutoff )); then
    printf 'Minute 50 reached before %s could start\n' "$label" >&2
    exit 3
fi
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/work/sol-job3/deps
mkdir -p raw
date -u +%FT%TZ > "$label.wrapper.start.stamp"
status=0
taskset -c "$cpu" python3 -u whole_games35.py "$previous/$build/forge" \
    "openings/$label.openings.txt" "$previous/net768.nnue" "raw/$label.records.txt" \
    "$first" "$last" --lmr-quiet-base "$quiet" --expected-engine-sha "$engine_sha" \
    --deadline "$cutoff" > "raw/$label.run.txt" 2>&1 || status=$?
date -u +%FT%TZ > "$label.wrapper.end.stamp"
printf '%d\n' "$status" > "$label.wrapper.exit"
exit "$status"
