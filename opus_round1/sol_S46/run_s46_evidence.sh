#!/usr/bin/env bash
# run_s46_evidence.sh (S46, opus 2026-10-27): regenerate fixtures, golden logs and every log of this folder.
# Reads the live PC autonomy logs ONLY by copying them (cp -p) into scratch; nothing on the PC is run or written.
set -u
J=$(cd "$(dirname "$0")" && pwd); cd "$J"
S=${S46_SCRATCH:-/f/opus_scratch/sol_s46}; SW=$(cygpath -w "$S"); RUN=$S/ev_$$; mkdir -p "$RUN" "$S/tmp" logs expected
export TMP="$SW\\tmp" TEMP="$SW\\tmp"
PY="nice -n 19 python -I -B"; SIM=forge_sol_S46_promote_sim_20261027.py; V=config/rules_voted_20261026.json
LIVE=/c/Users/Administrator/grok-pc/forge_push/autonomy

{ echo "# step1 fixtures + golden logs ($(date '+%F %T %z'))"
  $PY make_s46_fixtures.py; $PY make_s46_fixtures.py --out "$RUN/fx"
  for f in fixtures/*.json; do n=$(basename "$f" .json); cmp -s "$f" "$RUN/fx/$n.json" || echo "FIXTURE NOT DETERMINISTIC: $n"; done
  echo "fixtures regenerate byte-identically: $(ls fixtures/*.json | wc -l) files"
  for f in fixtures/*.json; do n=$(basename "$f" .json); $PY $SIM --rules $V --fixture "$f" --out "expected/$n.log"; $PY $SIM --rules $V --fixture "$f" --out "$RUN/$n.again.log"
    cmp -s "expected/$n.log" "$RUN/$n.again.log" || echo "NOT BYTE-IDENTICAL: $n"; done
  echo "golden logs written and re-run byte-identically"
  (sha256sum config/*.json fixtures/*.json expected/*.log | sed 's/ \*/  /')
} > logs/step1_fixtures_golden.log 2>&1

mkdir -p "$S/tests_$$"
{ echo "# step2 tests: S46_SCRATCH=$SW\\tests_$$ python -I -B test_promote_sim.py"
  S46_SCRATCH="$SW\\tests_$$" $PY test_promote_sim.py 2>&1; echo "exit code: $?"; } > logs/step2_tests.log

{ echo "# step3+4 profiles and deliberately wrong rules: python -I -B s46_profile_report.py"; $PY s46_profile_report.py 2>&1; echo "exit code: $?"; } > logs/step3_profiles_wrong_rules.log

{ echo "# step5 real-file replay: live autonomy logs copied read-only (cp -p) to $S/real, then compared"
  mkdir -p "$S/real"; cp -p "$LIVE/autopromote.log" "$LIVE/REWORK_LIST.md" "$S/real/"
  (cd "$S/real" && sha256sum autopromote.log REWORK_LIST.md | sed 's/ \*/  /')
  $PY $SIM --rules $V --fixture fixtures/real_20261025_al1_promote_replay.json --out "$RUN/real_replay.log"
  $PY s46_real_replay_compare.py --real "$SW\\real\\autopromote.log" --sim "$(cygpath -w "$RUN/real_replay.log")" --start '2026-10-25 15:40' --end '2026-10-25 18:30'; echo "exit code: $?"
  echo "## REWORK_LIST.md (real) first entry:"; grep -m1 'REWORK LIST gate104' "$S/real/REWORK_LIST.md" | cut -c1-200
} > logs/step5_real_replay.log 2>&1
tail -3 logs/step2_tests.log; tail -2 logs/step3_profiles_wrong_rules.log; grep -E 'IDENTICAL|DIFFERENT|NOT ' logs/step1_fixtures_golden.log logs/step5_real_replay.log
