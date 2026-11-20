#!/usr/bin/env bash
# Measured depth-12 searches. S14, Threads 1, Hash 16 are inside harness_depth.py.
set -euo pipefail
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
B=/agent/repos/base/forge-combo29/build-release/forge
P=/agent/repos/work/forge-combo29/build-release/forge
O=/tmp/kimi5/first200.fens
G=/tmp/kimi5/set_G.epd
H="python3 $DIR/harness_depth.py"

$H "$B" "$O" 12 o_b_d12 "$DIR"
$H "$B" "$G" 12 g_b_d12 "$DIR"
$H "$P" "$O" 12 o_p_off_d12 "$DIR" IdeaK9 false
$H "$P" "$G" 12 g_p_off_d12 "$DIR" IdeaK9 false
$H "$P" "$O" 12 o_p_on_d12 "$DIR" IdeaK9 true IdeaK9_Cap 3
$H "$P" "$O" 12 o_p_cap0_d12 "$DIR" IdeaK9 true IdeaK9_Cap 0

python3 "$DIR/summarize_depth.py" \
  o_b="$DIR/o_b_d12.raw.txt" \
  o_p_off="$DIR/o_p_off_d12.raw.txt" \
  o_p_on="$DIR/o_p_on_d12.raw.txt" \
  o_p_cap0="$DIR/o_p_cap0_d12.raw.txt" \
  > "$DIR/proof_o.txt"
python3 "$DIR/summarize_depth.py" \
  g_b="$DIR/g_b_d12.raw.txt" \
  g_p_off="$DIR/g_p_off_d12.raw.txt" \
  > "$DIR/proof_g.txt"
echo "===== proof_o ====="
cat "$DIR/proof_o.txt"
echo "===== proof_g ====="
cat "$DIR/proof_g.txt"
