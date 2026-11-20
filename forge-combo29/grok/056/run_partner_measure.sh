#!/usr/bin/env bash
# Partner patch, my harness. Honesty has no setoption.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT=forge-combo29/grok/$S
EXE=/tmp/forge-partner/forge
bash "$OUT/honesty_exe.sh" "$EXE" PARTNER "$OUT"
python3 "$OUT/depth_sum.py" --exe "$EXE" --fens /tmp/O.fens --depth 12 \
  --prefix "$OUT/partner_off_O_d12" --setoption IdeaS34=false
python3 "$OUT/depth_sum.py" --exe "$EXE" --fens /tmp/O.fens --depth 12 \
  --prefix "$OUT/partner_on_O_d12" \
  --setoption IdeaS34=true \
  --setoption IdeaS34_None=2 \
  --setoption IdeaS34_After=1 \
  --setoption IdeaS34_Stop=4 \
  --setoption IdeaS34_Bare=2
python3 "$OUT/compare_nodes.py" "$OUT/B_O_d12.nodes" "$OUT/partner_off_O_d12.nodes"
python3 "$OUT/compare_partner_on.py" "$OUT/partner_on_O_d12.nodes" "$OUT/partner006_P_on_O_d12.rows"
