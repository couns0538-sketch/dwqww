#!/usr/bin/env bash
# e2e_r8v5.sh OUT_DIR [ROWS] - Opus R14-B item 2 "works in Forge": the frozen relabel2.py end to end on R8 v5 data, the
# format of the 50M runbook: prepare (R8 v5 shards 271 + 272, --rows ROWS (default 3000), --jobs 2) -> run (LTO+PGO
# probe, 20k nodes, 2 workers, CPUs 2-3) -> status -> assemble -> Forge's fen2bin (.pos) and hce_dump (.hce) on both
# outputs. Checks: fen2bin records = lines with bad=0, hce_dump bad_fen=0 clamped=0, train + val rows = prepare.json,
# MANIFEST game_overlap 0, every shard's summary records the job's node limit / hash / probe sha256, a second run
# labels nothing, a second assemble is refused (exit 3). OUT_DIR must not exist. Exit 0 = every check passed.
set -u
out=${1:?out dir}
rows=${2:-3000}
[ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }
mkdir -p "$out"
W=/d/grok-pc-data/dwqww/.claude/worktrees
I2=$W/o14b-r2/opus_r14b/item2
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
S=/d/grok-pc-data/selfplay_out_r8v5_20261029
PROBE='C:\o14b\pgo2\pgo\forge_data_probe.exe'
BIN='F:\opus_scratch\rescore_d8\bin'
LOW=$(cygpath -w "$W/o14b-status/opus_r14b/tools/lowrun.ps1")
J=$out/job
fails=0
ok() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
echo "relabel2.py $(sha256sum < "$I2/relabel2.py" | cut -c1-16) (branch head $(git -C "$W/o14b-r2" log -1 --format=%h)), probe $(sha256sum < "$(cygpath -u "$PROBE")" | cut -c1-16), $(date '+%F %T')"
R() { "$PY" -I -B "$I2/relabel2.py" "$@"; }
R prepare --job "$J" --run-id e2e --rows "$rows" --jobs 2 \
  --selfplay "$S/forge_selfplay_fast_271.dedup.txt" "$S/forge_selfplay_fast_272.dedup.txt" > "$out/prepare.out" 2> "$out/prepare.err"
ok "prepare exit 0" "[ $? = 0 ]"
R run --job "$J" --run-id e2e --probe "$PROBE" --nodes 20000 --workers 2 --shard-size 1000 > "$out/run.out" 2> "$out/run.err"
ok "run exit 0" "[ $? = 0 ]"
R status --job "$J" > "$out/status.out" 2> "$out/status.err"
ok "status exit 0, all shards published" "grep -q ' shards, ' '$out/status.out' && ! grep -q 'not run yet' '$out/status.out'"
R assemble --job "$J" --run-id e2e > "$out/assemble.out" 2> "$out/assemble.err"
ok "assemble exit 0" "[ $? = 0 ]"
R run --job "$J" --run-id e2e --probe "$PROBE" --nodes 20000 --workers 2 --shard-size 1000 > "$out/run2.out" 2> "$out/run2.err"
ok "second run labels nothing" "[ $? = 0 ] && grep -q 'nothing left to label' '$J/sessions.log'"
R assemble --job "$J" --run-id e2e > "$out/assemble2.out" 2> "$out/assemble2.err"
ok "second assemble refused (exit 3, final exists)" "[ $? = 3 ] && grep -q 'final exists' '$out/assemble2.err'"
"$PY" -I -B - "$J" > "$out/job_checks.txt" 2>&1 <<'EOF'
import glob, json, os, sys
j = sys.argv[1]
prep = json.load(open(os.path.join(j, "prepare.json")))
cfg = json.load(open(os.path.join(j, "run_config.json")))
man = json.load(open(os.path.join(j, "final", "MANIFEST.json")))
lines = {n: sum(1 for _ in open(os.path.join(j, "final", n), encoding="utf-8")) for n in ("train.txt", "val.txt")}
summ = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(j, "shards", "shard_?????", "summary.json")))]
same = all((s.get("nodes_limit"), s.get("hash_mb"), s.get("probe_sha256")) == (cfg["nodes"], cfg["hash_mb"], cfg["probe_sha256"]) for s in summ)
print(f"rows {prep['rows']} = train {lines['train.txt']} + val {lines['val.txt']}: {prep['rows'] == lines['train.txt'] + lines['val.txt']}")
print(f"MANIFEST game_overlap {man['game_overlap']}, train_rows {man['train_rows']}, val_rows {man['val_rows']}")
print(f"shards {len(summ)}, every summary records nodes_limit / hash_mb / probe_sha256 of run_config.json: {same}")
sys.exit(0 if prep["rows"] == lines["train.txt"] + lines["val.txt"] and man["game_overlap"] == 0 and summ and same else 1)
EOF
ok "rows, game overlap, shard settings" "[ $? = 0 ]"
cat "$out/job_checks.txt"
for f in train val; do
  n=$(wc -l < "$J/final/$f.txt")
  for tool in fen2bin hce_dump; do
    ext=$([ $tool = fen2bin ] && echo pos || echo hce)
    powershell -NoProfile -File "$LOW" -Mask 0xC -Priority BelowNormal -Exe "$BIN\\$tool.exe" \
      -ArgLine "$(cygpath -w "$J/final/$f.txt") $(cygpath -w "$out/$f.$ext")" > "$out/$tool.$f.log" 2>&1
    rc=$?
    info=$(tr -d '\r' < "$out/$f.$ext.info" 2>/dev/null | tr '\n' ' ')
    echo "$tool $f.txt ($n lines): exit $rc; $info"
    if [ $tool = fen2bin ]; then
      ok "fen2bin $f: records = $n lines, bad 0" "[ $rc = 0 ] && [[ ' $info' == *' records=$n '* ]] && [[ ' $info' == *' bad=0 '* ]]"
    else
      ok "hce_dump $f: records = $n lines, bad_fen 0, clamped 0" "[ $rc = 0 ] && [[ ' $info' == *' records=$n '* ]] && [[ ' $info' == *' bad_fen=0 '* ]] && [[ ' $info' == *' clamped=0 '* ]]"
    fi
  done
done
echo "=== failures: $fails $(date '+%F %T')"
exit $((fails > 0))
