#!/usr/bin/env bash
# test_gate_summary.sh OUT_DIR - self-test of gate_summary.py on finished crew gates (read-only; copies go to OUT_DIR).
# Six finished gates (normal end, SPRT stops with games in flight, a time forfeit, [-5, 5] bounds, an early H0) must
# reproduce their printed blocks exactly; a copy with one printed number changed must FAIL; a folder without a PGN is
# skipped; usage errors exit 2. Exit 0 = all as expected.
set -u
out=${1:?out dir}; [ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }; mkdir -p "$out"
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
GS="$(cd "$(dirname "$0")" && pwd)/gate_summary.py"
F=/f/forge_push
fails=0; n=0
case_() { name=$1; want=$2; shift 2; n=$((n + 1))
  "$PY" -I -B "$GS" "$@" > "$out/$name.txt" 2>&1; rc=$?
  if [ "$rc" = "$want" ]; then echo "PASS $name (exit $rc): $(tail -1 "$out/$name.txt")"; else echo "FAIL $name: exit $rc, want $want: $(grep -E 'PROBLEM|gate_summary' "$out/$name.txt" | head -3 | tr '\n' ' ')"; fails=$((fails + 1)); fi; }
case_ six_finished 0 "$F/gate_stB_lmrttcapall1_vs_AL1" "$F/gate_stA_v2_corrsignedkey1_vs_AL1" \
  "$F/gateR11H2H_A2_e9best_vs_e19final_plainz5" "$F/gate_npts3_ep06_vs_AL1" "$F/gate68_bundle_g43g33g49_vs_h256e12" \
  "$F/gateR7_ttexclusive_nonreg_vs_r7off" --json "$(cygpath -w "$out")\\six.json"
[ "$(grep -c "'llr': True" "$out/six_finished.txt")" = 6 ] || { echo "FAIL six_finished: not 6 LLR matches"; fails=$((fails + 1)); }
grep -q "time forfeits 1 (log 1)" "$out/six_finished.txt" || { echo "FAIL six_finished: the R11 time forfeit not counted"; fails=$((fails + 1)); }
# tampered copy: one printed number changed (Wins 326 -> 327) must be caught
t="$out/gate_stB_lmrttcapall1_vs_AL1"; mkdir -p "$t"
cp "$F/gate_stB_lmrttcapall1_vs_AL1/gate_stB_lmrttcapall1_vs_AL1.pgn" "$t/"
sed 's/Wins: 326, Losses: 352/Wins: 327, Losses: 352/' "$F/gate_stB_lmrttcapall1_vs_AL1/gate_stB_lmrttcapall1_vs_AL1.log" > "$t/gate_stB_lmrttcapall1_vs_AL1.log"
grep -q 'Wins: 327, Losses: 352' "$t/gate_stB_lmrttcapall1_vs_AL1.log" || { echo "FAIL tamper: sed did not change the copy"; fails=$((fails + 1)); }
case_ tampered_log 1 "$t"
mkdir -p "$out/empty_gate"
case_ no_pgn_skipped 0 "$out/empty_gate"
case_ no_args 2
case_ json_exists 2 "$F/gate_stB_lmrttcapall1_vs_AL1" --json "$(cygpath -w "$out")\\six.json"
case_ not_a_folder 1 "$out/no_such_gate"
echo "$((n - fails)) / $n cases as expected (+2 content checks)"
[ $fails = 0 ] && echo "ALL PASS" || echo "FAILURES: $fails"
exit $fails
