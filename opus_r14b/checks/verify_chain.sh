#!/usr/bin/env bash
# verify_chain.sh TAG - Opus R14-B: the full check chain, strictly one step after the other on CPUs 2-3 (one physical
# core): 1 test suite from the worktree, 2 bridge to the 1M proof, 3 fresh-clone checks (+ adoption rehearsal),
# 4 loader ABBA in the live setting (old w4 vs fast with 2 builders), 5 prepare of R8 v5 shards 271 + 272 (--jobs 2),
# 6 end to end on R8 v5 data (3,000 rows, PGO probe) through assemble and fen2bin.
# Outputs under C:/o14b/vc_TAG (must not exist). A failing suite (step 1) stops the chain; any other failing step
# is reported and the chain goes on.
set -u
tag=${1:?tag}
out=/c/o14b/vc_$tag
[ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }
mkdir -p "$out"
W=/d/grok-pc-data/dwqww/.claude/worktrees
I2=$W/o14b-r2/opus_r14b/item2
I1=$W/o14b-l1/opus_r14b/item1
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
LOAD=$W/o14b-status/opus_r14b/tools/cpu_users.ps1
fails=0
step() { echo; echo "=== $1 $(date '+%F %T')"; powershell -NoProfile -File "$LOAD" -Mask 0xC -Seconds 3 | head -4; }
step "0 code: relabel2.py $(sha256sum < "$I2/relabel2.py" | cut -c1-16), branch heads r2 $(git -C "$W/o14b-r2" log -1 --format=%h) l1 $(git -C "$W/o14b-l1" log -1 --format=%h)"
step "1 test suite"
bash "$I2/test_relabel2.sh" "$out/tests" > "$out/tests.log" 2>&1
rc=$?; echo "exit=$rc PASS $(grep -c '^PASS' "$out/tests.log") FAIL $(grep -c '^FAIL' "$out/tests.log")"
grep '^FAIL' "$out/tests.log" | head -5
[ $rc = 0 ] || { echo "=== the suite failed: chain stopped (fix, then run the chain again) $(date '+%F %T')"; exit 1; }
step "2 bridge to the 1M proof"
bash "$I2/bridge_check.sh" /d/o14b/r2/proof "$out/bridge" > "$out/bridge.log" 2>&1
rc=$?; cat "$out/bridge.log"; [ $rc = 0 ] || fails=$((fails + 1))
step "3 fresh-clone checks"
# final bug hunt (04:27): this ran a scratch copy (/d/o14b/r2/fresh_checkout_checks.sh, ~20:30, patched by sed) and not
# the committed script next to this one, which takes OUT_DIR as its argument: an old check, and none in another checkout
bash "$(cd "$(dirname "$0")" && pwd)/fresh_checkout_checks.sh" "$out/fresh" > "$out/fresh.log" 2>&1
rc=$?; grep "^clone\|^PASS\|^FAIL\|^exit=\|^===\|identical\|differ\|not OK\|copied" "$out/fresh.log"; [ $rc = 0 ] || fails=$((fails + 1))
step "4 loader ABBA in the live setting"
"$PY" -I -B "$I1/tools/fl_abba.py" --out "$(cygpath -w "$out/abba_live")" --pairs 10 \
  --a 'old:D:\o14b\ref\libtraining_data_loader.dll:4' --b 'fast:D:\o14b\fl\b5_install\forge_fastloader.dll:2' \
  --mask 0xC --priority BelowNormal > "$out/abba_live.log" 2>&1
rc=$?; tail -4 "$out/abba_live.log"; [ $rc = 0 ] || fails=$((fails + 1))
step "5 prepare of one full R8 v5 shard"
S=/d/grok-pc-data/selfplay_out_r8v5_20261029
t0=$(date +%s)
"$PY" -I -B "$I2/relabel2.py" prepare --job "$out/r8v5_272" --run-id r8v5-272 --jobs 2 \
  --selfplay "$S/forge_selfplay_fast_271.dedup.txt" "$S/forge_selfplay_fast_272.dedup.txt" > "$out/r8v5.log" 2>&1
rc=$?; echo "exit=$rc in $(( $(date +%s) - t0 )) s"; cat "$out/r8v5.log" | cut -c1-400; [ $rc = 0 ] || fails=$((fails + 1))
step "6 end to end on R8 v5 data: 3,000 rows -> 20k-node labels (PGO probe, 2 workers) -> assemble -> fen2bin"
J=$out/r8v5_e2e
LOW=$(cygpath -w "$W/o14b-status/opus_r14b/tools/lowrun.ps1")
"$PY" -I -B "$I2/relabel2.py" prepare --job "$J" --run-id e2e --rows 3000 --jobs 2 \
  --selfplay "$S/forge_selfplay_fast_271.dedup.txt" "$S/forge_selfplay_fast_272.dedup.txt" > "$out/e2e.log" 2>&1 \
&& "$PY" -I -B "$I2/relabel2.py" run --job "$J" --run-id e2e --probe 'C:\o14b\pgo2\pgo\forge_data_probe.exe' \
  --nodes 20000 --workers 2 --shard-size 1000 >> "$out/e2e.log" 2>&1 \
&& "$PY" -I -B "$I2/relabel2.py" assemble --job "$J" --run-id e2e >> "$out/e2e.log" 2>&1 \
&& powershell -NoProfile -File "$LOW" -Mask 0xC -Priority BelowNormal -Exe 'F:\opus_scratch\rescore_d8\bin\fen2bin.exe' \
  -ArgLine "$(cygpath -w "$J/final/train.txt") $(cygpath -w "$out/e2e_train.pos")" >> "$out/e2e.log" 2>&1
rc=$?
"$PY" -I -B "$I2/relabel2.py" status --job "$J" 2>&1 | head -1 | cut -c1-200
rows=$(wc -l < "$J/final/train.txt" 2>/dev/null || echo 0)
info=$(tr -d '\r' < "$out/e2e_train.pos.info" 2>/dev/null | tr '\n' ' ')  # fen2bin writes CRLF
echo "exit=$rc; train.txt $rows rows; fen2bin: $info"
if [ $rc = 0 ] && [[ " $info" == *" bad=0 "* ]] && [[ " $info" == *" records=$rows "* ]]; then
  echo "PASS R8 v5 end to end (fen2bin records = train rows, 0 bad)"
else
  echo "FAIL R8 v5 end to end (see $out/e2e.log)"; fails=$((fails + 1))
fi
echo; echo "=== chain failures: $fails $(date '+%F %T')"
exit $((fails > 0))
