#!/usr/bin/env bash
# refreeze.sh TAG - Opus R14-B: the re-check after a relabel2.py-only change once the code is frozen (the probe builds,
# the loader DLL and the adoption rehearsal do not depend on relabel2.py, so they are not repeated):
#   1 the test suite from the worktree   2 the suite from a fresh clone (this PC's default git settings)
#   3 the bridge to the 1M proof         4 function-level diff vs the proof's frozen code (5c88438f)
#   5 the new sha256 to write into RELABEL_HANDOFF.md, RESULTS.md, the skill, FINAL_REPORT.md and memory
# Strictly one step after the other on CPUs 2-3 (the tools pin themselves). Outputs under C:/o14b/rf_TAG (must not
# exist). Exit 0 = every step passed. About 5 minutes on a free core.
set -u
tag=${1:?tag}
out=/c/o14b/rf_$tag
[ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }
mkdir -p "$out"
W=/d/grok-pc-data/dwqww/.claude/worktrees
I2=$W/o14b-r2/opus_r14b/item2
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
fails=0
sha=$(sha256sum < "$I2/relabel2.py" | cut -d' ' -f1)
dirty=$(git -C "$W/o14b-r2" status --porcelain -- opus_r14b/item2/relabel2.py)
echo "=== 0 relabel2.py $sha, branch head $(git -C "$W/o14b-r2" log -1 --format=%h) $(date '+%F %T')"
[ -z "$dirty" ] || { echo "relabel2.py has uncommitted changes: commit first (the fresh clone tests the commit)"; exit 2; }
echo "=== 1 suite from the worktree $(date '+%T')"
bash "$I2/test_relabel2.sh" "$out/tests" > "$out/tests.log" 2>&1
rc=$?; echo "exit=$rc PASS $(grep -c '^PASS' "$out/tests.log") FAIL $(grep -c '^FAIL' "$out/tests.log")"
grep '^FAIL' "$out/tests.log" | head -5
[ $rc = 0 ] || { echo "=== the suite failed: stopped"; exit 1; }
echo "=== 2 suite from a fresh clone $(date '+%T')"
git clone -q --shared --no-checkout /d/grok-pc-data/dwqww "$out/clone" && git -C "$out/clone" checkout -q origin/opus-r14b-relabel \
  || { echo "FAIL clone"; exit 1; }
csha=$(sha256sum < "$out/clone/opus_r14b/item2/relabel2.py" | cut -d' ' -f1)
echo "clone at $(git -C "$out/clone" rev-parse --short HEAD), relabel2.py $csha"
[ "$csha" = "$sha" ] || { echo "FAIL the clone's relabel2.py differs from the worktree's (push / commit?)"; fails=$((fails + 1)); }
bash "$out/clone/opus_r14b/item2/test_relabel2.sh" "$out/clone_tests" > "$out/clone_tests.log" 2>&1
rc=$?; echo "exit=$rc PASS $(grep -c '^PASS' "$out/clone_tests.log") FAIL $(grep -c '^FAIL' "$out/clone_tests.log")"
[ $rc = 0 ] || fails=$((fails + 1))
echo "=== 3 bridge to the 1M proof $(date '+%T')"
bash "$I2/bridge_check.sh" /d/o14b/r2/proof "$out/bridge" > "$out/bridge.log" 2>&1
rc=$?; grep -v "^  " "$out/bridge.log"; [ $rc = 0 ] || fails=$((fails + 1))
echo "=== 4 function diff vs the proof's frozen code $(date '+%T')"
git -C "$W/o14b-r2" show 5fa7b7d5:opus_r14b/item2/relabel2.py > "$out/relabel2_frozen_5c88438f.py"
"$PY" -I -B "$I2/fn_diff.py" "$out/relabel2_frozen_5c88438f.py" "$I2/relabel2.py" > "$out/fn_diff_frozen_vs_${sha:0:8}.txt"
head -4 "$out/fn_diff_frozen_vs_${sha:0:8}.txt"
for f in file_hash label_shard load_prepare new_game board_stats read_shard_rows row_offsets verify_shard; do
  grep -q "^identical:.* $f\( \|$\)" "$out/fn_diff_frozen_vs_${sha:0:8}.txt" \
    || { echo "NOTE labelling function $f changed: the bridge above is then the evidence that labels still match"; }
done
echo "=== 5 new sha256 $sha (write it into RELABEL_HANDOFF.md, RESULTS.md, the skill, FINAL_REPORT.md, memory)"
echo "=== failures: $fails $(date '+%F %T')"
exit $((fails > 0))
