#!/usr/bin/env bash
# harness_refusal_control.sh — proof that the timing harness REFUSES to record a search on a FEN the engine
# rejected. Seat 21's 21-F2 showed a refused FEN leaves the PREVIOUS position on the board and still answers
# readyok; if clock_latency.py did not abort, a "latency for position X" would silently be latency for X-1.
set -u
EXE="$HOME/builds/release/forge"
D="$(cd "$(dirname "$0")/.." && pwd)"
cd "$D"
OUT=job4/harness_refusal_control.txt
: > "$OUT"

# a FEN list where the second entry is refused: 7 squares in rank 8
{
  echo "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"
  echo "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN w KQkq - 0 1"
} > /tmp/refusal_fens.txt

echo "## the FEN list used (line 2 is deliberately invalid)" | tee -a "$OUT"
cat /tmp/refusal_fens.txt | sed 's/^/    /' | tee -a "$OUT"
echo | tee -a "$OUT"
echo "## running the committed timing harness on it" | tee -a "$OUT"
echo '```' | tee -a "$OUT"
set +e
timeout 120 python3 job1/clock_latency.py "$EXE" /tmp/refusal_fens.txt "movetime 50" /tmp/refusal_out.jsonl x >> "$OUT" 2>&1
RC=$?
set -e
echo '```' | tee -a "$OUT"
echo | tee -a "$OUT"
echo "exit code: $RC" | tee -a "$OUT"
echo "records written before the abort: $(wc -l < /tmp/refusal_out.jsonl 2>/dev/null || echo 0)" | tee -a "$OUT"
echo | tee -a "$OUT"
if [ "$RC" -ne 0 ] && grep -q "invalid FEN" "$OUT"; then
  echo "**OK**: the harness aborted on the refused FEN and wrote nothing further. A refused position can never" | tee -a "$OUT"
  echo "be recorded as a latency of the position before it." | tee -a "$OUT"
else
  echo "**FAILED**: the harness did not abort - every latency number it ever produced is suspect." | tee -a "$OUT"
fi
