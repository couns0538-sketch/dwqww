#!/usr/bin/env bash
# opus2 SMP pack (opus_smp_layout/SPEC.md section 6): extra ThreadSanitizer evidence, called by opus_round1/ci/run_ci.sh
# in tsan mode as: tsan_extra.sh <forge exe> <out dir>. TSAN_OPTIONS (log_path=...) is inherited from run_ci.sh, which
# fails the job if any report file appears. Two parts:
#   1. the pack's two test binaries again, with their full output kept (ctest hides passing output): the contention
#      fixture's incoherent count and the positive control's result under TSan;
#   2. the real engine (TSan build) driven over UCI at Threads 2 and 4 with TtLockless false and true: go movetime,
#      go nodes, go infinite + stop, go ponder + ponderhit, Clear Hash, Hash and Threads changes, ucinewgame, quit.
#      A 'go' is ended by the next UCI line in this engine (stop path); the sleeps give each search time to run.
set -uo pipefail
FORGE=$1
OUT=$2
BD=$(dirname "$FORGE")
LOG="$OUT/opus2_smp_tsan_extra.log"
status=0
echo "== opus2 SMP tsan_extra $(date -u +%FT%TZ) forge=$FORGE" | tee -a "$LOG"
for t in forge_tt_lockless_tests forge_smp_lifecycle_tests; do
  if [ -x "$BD/$t" ]; then
    echo "== $t" | tee -a "$LOG"
    # Each test writes its own file, so the summary below shows only this test's lines (before a675c04+1 the
    # summary grepped the shared log and re-printed the previous test's lines: display only, no double run).
    FORGE_TT_LOCKLESS_SECONDS=3 "$BD/$t" > "$OUT/opus2_smp_$t.log" 2>&1 || { echo "FAIL $t" | tee -a "$LOG"; status=1; }
    cat "$OUT/opus2_smp_$t.log" >> "$LOG"
    grep -E 'contention|positive control|differential|All |failure' "$OUT/opus2_smp_$t.log" | tail -12
  else
    echo "MISSING $BD/$t (FORGE_SMP_LAYOUT=ON expected)" | tee -a "$LOG"; status=1
  fi
done
KIWI='r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'
for mode in false true; do
  for th in 2 4; do
    f="$OUT/opus2_uci_tsan_TtLockless-${mode}_T${th}.log"
    {
      printf 'uci\nsetoption name Threads value %s\nsetoption name TtLockless value %s\nsetoption name Hash value 16\nsetoption name OwnBook value false\nisready\n' "$th" "$mode"
      printf 'position startpos\ngo movetime 4000\n'; sleep 6
      printf 'position fen %s\ngo nodes 150000\n' "$KIWI"; sleep 10
      printf 'position startpos moves e2e4 e7e5 g1f3\ngo infinite\n'; sleep 3; printf 'stop\n'; sleep 1
      printf 'position startpos moves d2d4\ngo ponder movetime 2000\n'; sleep 2; printf 'ponderhit\n'; sleep 5
      printf 'setoption name Clear Hash\nsetoption name Hash value 4\nsetoption name Threads value %s\nisready\n' "$(( th == 2 ? 3 : 2 ))"; sleep 1
      printf 'ucinewgame\nposition fen %s\ngo depth 8\n' "$KIWI"; sleep 12
      printf 'isready\n'; sleep 1
      printf 'quit\n'
    } | "$FORGE" > "$f" 2>&1
    rc=$?
    nb=$(grep -c '^bestmove' "$f")
    echo "uci TtLockless=$mode Threads=$th: exit $rc, bestmove lines $nb, readyok $(grep -c '^readyok' "$f")" | tee -a "$LOG"
    [ "$rc" -eq 0 ] || status=1
    [ "$nb" -ge 4 ] || { echo "FAIL: expected >= 4 bestmove lines in $f" | tee -a "$LOG"; status=1; }
  done
done
echo "== opus2 SMP tsan_extra status=$status" | tee -a "$LOG"
exit $status
