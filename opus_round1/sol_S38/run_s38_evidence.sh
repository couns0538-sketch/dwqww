#!/usr/bin/env bash
# run_s38_evidence.sh (S38, opus 2026-10-27): regenerate every S38 artifact and log in this folder.
# Scratch (fixtures, test temp, mutants, real-gate COPIES) lives under $S on F:. The real gate files are read from
# D:\grok-pc-data\forge_push only to copy them (cp -p) and to re-hash them; nothing is written there. No engine runs.
set -u
J=$(cd "$(dirname "$0")" && pwd); cd "$J"
S=${S38_SCRATCH:-/f/opus_scratch/sol_s38}; SW=$(cygpath -w "$S"); RUN=$S/ev_$$; mkdir -p "$RUN" "$S/tmp"
export TMP="$SW\\tmp" TEMP="$SW\\tmp"
PY="nice -n 19 python -I -B"; TOOL=forge_sol_S38_gate_time_audit_20261027.py
mkdir -p logs fixtures sample_reports real_run
LIVE=/d/grok-pc-data/forge_push; REAL=$S/real
CSV=/d/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039/7_history/gate_results/GATE_RESULTS.csv

{ echo "# step1 fixture: generated twice (deterministic), hashes, tarball, golden sample reports ($(date '+%F %T %z'))"
  $PY make_s38_fixture.py --out "$RUN/fx1"; $PY make_s38_fixture.py --out "$RUN/fx2"
  (cd "$RUN/fx1" && sha256sum s38fx_* | sed 's/ \*/  /') > fixtures/fixture.sha256
  (cd "$RUN/fx2" && sha256sum s38fx_* | sed 's/ \*/  /') | diff - fixtures/fixture.sha256 && echo "two generator runs byte-identical"
  cat fixtures/fixture.sha256
  tar -czf fixtures/s38_fixture_20261027.tar.gz -C "$RUN/fx1" $(cd "$RUN/fx1" && ls s38fx_*)
  ls -l fixtures/s38_fixture_20261027.tar.gz
  $PY $TOOL --pgn "$RUN/fx1/s38fx_REF.pgn" --log "$RUN/fx1/s38fx_REF.log" --engine-log "$RUN/fx1/s38fx_REF_engine_io.log" --label s38fx_REF \
      --out-json sample_reports/s38fx_REF_report.json --out-md sample_reports/s38fx_REF_report.md > /dev/null; echo "REF report exit $?"
  $PY $TOOL --pgn "$RUN/fx1/s38fx_A.pgn" --log "$RUN/fx1/s38fx_A.log" --engine-log "$RUN/fx1/s38fx_A_engine_io.log" --ref sample_reports/s38fx_REF_report.json \
      --per-game-nps 5 --label s38fx_A --out-json sample_reports/s38fx_A_report.json --out-md sample_reports/s38fx_A_report.md > /dev/null; echo "A report exit $? (1 = flags raised, expected)"
  grep -E '^Flags' sample_reports/s38fx_REF_report.md sample_reports/s38fx_A_report.md
} > logs/step1_fixture.log 2>&1

mkdir -p "$S/tests_$$"
{ echo "# step2 unit + fixture tests: S38_SCRATCH=$SW\\tests_$$ python -I -B test_gate_time_audit.py"
  S38_SCRATCH="$SW\\tests_$$" $PY test_gate_time_audit.py 2>&1; echo "exit code: $?"; } > logs/step2_unit_tests.log

{ echo "# step3 nps hand count (awk, s38_hand_count.sh) vs the tool's --per-game-nps 5, first 5 games per engine"
  echo "## synthetic fixture s38fx_A"
  for e in base_s38 cand_s38; do bash s38_hand_count.sh "$RUN/fx1/s38fx_A_engine_io.log" $e 5; done > "$RUN/hand_fx.txt"
  grep -E '^- .* game ' sample_reports/s38fx_A_report.md > "$RUN/tool_fx.txt"; cat "$RUN/hand_fx.txt"
  diff "$RUN/tool_fx.txt" "$RUN/hand_fx.txt" && echo "fixture: tool == hand count (10/10 rows)"
  echo "## real gate G125 engine_io.head.log (copy)"
  G=$REAL/gate125_e48f042_vs_AL1
  $PY $TOOL --pgn $G/gate125_e48f042_vs_AL1.pgn --engine-log $G/engine_io.head.log --per-game-nps 5 --label G125 --out-md "$RUN/g125_pg.md" > /dev/null
  grep -E '^- .* game ' "$RUN/g125_pg.md" > "$RUN/tool_g125.txt"
  for e in base_AUTOLOCK_1_gate120_e32f003rec_s198 cand_h256_e48f042; do nice -n 19 bash s38_hand_count.sh $G/engine_io.head.log $e 5; done > "$RUN/hand_g125.txt"
  cat "$RUN/hand_g125.txt"; diff "$RUN/tool_g125.txt" "$RUN/hand_g125.txt" && echo "G125: tool == hand count (10/10 rows)"
} > logs/step3_hand_count.log 2>&1

{ echo "# step4 mutation check: python -I -B mutation_check_s38.py --scratch $SW\\mut_$$"
  $PY mutation_check_s38.py --scratch "$SW\\mut_$$" 2>&1; echo "exit code: $?"; } > logs/step4_mutation_check.log

{ echo "# step5 real-file run on COPIES of 7 PC gates (copied read-only from $LIVE with cp -p to $REAL)"
  echo "## copies == originals (sha256 re-computed now on both sides)"
  (cd "$REAL" && find . -type f | LC_ALL=C sort | xargs sha256sum | sed 's# \*\./#  #') > "$RUN/copies.sha"
  (cd "$LIVE" && cut -c67- "$RUN/copies.sha" | xargs nice -n 19 sha256sum | sed 's/ \*/  /') > "$RUN/orig.sha"
  diff "$RUN/copies.sha" "$RUN/orig.sha" && echo "all $(wc -l < "$RUN/copies.sha") copied files identical to the originals"
  ref=""; items=""
  for pair in G120:gate120_e32f003rec_s198_vs_h256e12 G120c:gate120_e32f003rec_s198_vs_h256e12_confirm G104:gate104_e48f006_vs_h256e12 \
              G104c:gate104_e48f006_vs_h256e12_confirm G124:gate124_e48f034_vs_AL1 G124c:gate124_e48f034_vs_AL1_confirm G125:gate125_e48f042_vs_AL1; do
    lab=${pair%%:*}; tag=${pair#*:}; G=$REAL/$tag; el=""; [ -f $G/engine_io.head.log ] && el="--engine-log $G/engine_io.head.log"
    $PY $TOOL --pgn $G/$tag.pgn --log $G/$tag.log $el $ref --label "$lab $tag" --out-json "$RUN/$lab.json" --out-md real_run/$lab.md > /dev/null
    echo "$lab $tag: exit $? ; $(grep -E '^Flags' real_run/$lab.md)"
    [ "$lab" = G120 ] && ref="--ref $RUN/G120.json"
    items="$items $tag=$(cygpath -w "$RUN/$lab.json")=$(cygpath -w "$G/RESULT.md")"
  done
  echo "## tool vs the driver's RESULT.md and GATE_RESULTS.csv (lock archive copy)"
  $PY s38_compare_result_md.py --csv "$(cygpath -w "$CSV")" $items; echo "exit code: $?"
  (cd "$RUN" && tar -czf "$J/real_run/real_reports_json.tar.gz" G120.json G120c.json G104.json G104c.json G124.json G124c.json G125.json)
  ls -l real_run/real_reports_json.tar.gz
} > logs/step5_real_file_run.log 2>&1
tail -3 logs/step2_unit_tests.log; tail -2 logs/step4_mutation_check.log; grep -E 'identical|tool ==|all gates equal' logs/step*.log
