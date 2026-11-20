#!/usr/bin/env bash
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
P=/agent/repos/work/forge-combo29/build-release/forge
python3 "$D/honesty_check.py" "$P" HONESTY_P || echo HONESTY_FAIL
python3 "$D/search_set.py" --exe "$P" --fens "$D/first200.fens" --depth 12 --out P_off_O --switch false || echo OFF_O_FAIL
python3 "$D/search_set.py" --exe "$P" --fens "$D/set_G.epd" --depth 12 --out P_off_G --switch false || echo OFF_G_FAIL
python3 "$D/search_set.py" --exe "$P" --fens "$D/first200.fens" --depth 12 --out P_on_O --switch true || echo ON_O_FAIL
python3 "$D/cmp_rows.py" "$D/B_O_d12.rows" "$D/P_off_O.rows" > "$D/cmp_off_O.txt"
python3 "$D/cmp_rows.py" "$D/B_G_d12.rows" "$D/P_off_G.rows" > "$D/cmp_off_G.txt"
python3 "$D/cmp_rows.py" "$D/B_O_d12.rows" "$D/P_on_O.rows" > "$D/cmp_on_O.txt"
python3 "$D/sum_rows.py" "$D/P_on_O.rows" > "$D/P_on_O.sum"
echo PROOFS_DONE
