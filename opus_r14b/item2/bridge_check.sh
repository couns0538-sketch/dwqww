#!/usr/bin/env bash
# bridge_check.sh PROOF_DIR OUT_DIR - Opus R14-B item 2: show that the post-proof relabel2.py (the code next to this
# script) gives the proof's results. The proof ran on the frozen relabel2.py (sha256 5c88438f...).
#   1. prepare the proof's sample again (same inputs, --rows 1000000) with --jobs 1 and with --jobs 2:
#      rows.tsv must equal the proof's rows.tsv byte for byte (row ids, game ids, split, FENs, sources)
#   2. on a COPY of proof job A (rows.tsv, prepare.json, run_config.json, published shards; the proof folders are
#      only read): `run --accept-new-tool` re-verifies all published shards and has nothing left to do, then
#      `assemble`: train.txt / val.txt / labels.tsv must equal the proof's final files (md5)
# Idle on CPUs 2-3 (the tool's own --mask default). OUT_DIR must not exist. Exit 0 = every check passed.
set -u
proof=${1:?proof dir}
out=${2:?out dir}
[ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }
mkdir -p "$out"
PY=${PY:-/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe}
R=$(cd "$(dirname "$0")" && pwd)/relabel2.py
P=${PROBE:-'C:\o13\p5\forge_data_probe.exe'}
SP=/d/grok-pc-data/selfplay_out
fails=0
ok() { if "$@"; then echo "PASS $*"; else echo "FAIL $*"; fails=$((fails + 1)); fi; }
echo "code: $(sha256sum < "$R" | cut -c1-16) ($R)"
for jobs in 1 2; do
  t0=$(date +%s)
  "$PY" -I -B "$R" prepare --job "$out/prep_j$jobs" --run-id r14b-proof-A --rows 1000000 --jobs "$jobs" \
    --selfplay "$SP/forge_selfplay_001.txt" "$SP/forge_selfplay_002.txt" "$SP/forge_selfplay_003.txt" \
    "$SP/forge_selfplay_004.txt" > "$out/prep_j$jobs.out" 2> "$out/prep_j$jobs.err"
  echo "prepare --jobs $jobs: exit $? in $(( $(date +%s) - t0 )) s"
  ok cmp -s "$out/prep_j$jobs/rows.tsv" "$proof/jobA/rows.tsv"
done
c=$out/copyA
mkdir -p "$c"
cp "$proof/jobA/rows.tsv" "$proof/jobA/prepare.json" "$proof/jobA/run_config.json" "$c/"
cp -r "$proof/jobA/shards" "$c/shards"
"$PY" -I -B "$R" run --job "$c" --run-id r14b-proof-A --probe "$P" --nodes 20000 --workers 1 --accept-new-tool \
  > "$out/run_copy.out" 2> "$out/run_copy.err"
echo "run --accept-new-tool on the copy: exit $?; $(tail -1 "$c/sessions.log")"
"$PY" -I -B "$R" assemble --job "$c" --run-id r14b-proof-A > "$out/assemble_copy.out" 2> "$out/assemble_copy.err"
echo "assemble on the copy: exit $?"
for f in train.txt val.txt labels.tsv; do ok cmp -s "$c/final/$f" "$proof/jobA/final/$f"; done
echo "failures: $fails"
exit $((fails > 0))
