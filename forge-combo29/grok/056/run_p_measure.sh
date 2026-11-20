#!/usr/bin/env bash
# Measure exe P. Honesty has no setoption. Depth runs use S14 inside depth_sum.py.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT=forge-combo29/grok/$S
EXE=/tmp/forge-P/forge
bash "$OUT/honesty_exe.sh" "$EXE" P "$OUT"
python3 "$OUT/depth_sum.py" --exe "$EXE" --fens /tmp/O.fens --depth 12 --prefix "$OUT/P_off_O_d12" --setoption IdeaS34=false
python3 "$OUT/depth_sum.py" --exe "$EXE" --fens /tmp/G.epd --depth 12 --prefix "$OUT/P_off_G_d12" --setoption IdeaS34=false
python3 "$OUT/depth_sum.py" --exe "$EXE" --fens /tmp/O.fens --depth 12 --prefix "$OUT/P_on_O_d12" \
  --setoption IdeaS34=true \
  --setoption IdeaS34_EaseZero=2 \
  --setoption IdeaS34_EaseMid=1 \
  --setoption IdeaS34_Couple=2 \
  --setoption IdeaS34_Full=4 \
  --setoption IdeaS34_NoTt=2
printf 'uci\nquit\n' | "$EXE" > "$OUT/P_uci.txt"
python3 - "$OUT/P_uci.txt" << 'PY'
import sys
text = open(sys.argv[1], encoding="utf-8").read().splitlines()
want = {
    "IdeaS34": "option name IdeaS34 type check default false",
    "IdeaS34_EaseZero": "option name IdeaS34_EaseZero type spin default 2 min 0 max 8",
    "IdeaS34_EaseMid": "option name IdeaS34_EaseMid type spin default 1 min 0 max 8",
    "IdeaS34_Couple": "option name IdeaS34_Couple type spin default 2 min 0 max 32",
    "IdeaS34_Full": "option name IdeaS34_Full type spin default 4 min 0 max 32",
    "IdeaS34_NoTt": "option name IdeaS34_NoTt type spin default 2 min 1 max 8",
}
print("uci_option_check")
ok = True
for name, expect in want.items():
    hits = [line for line in text if line.startswith(f"option name {name} ")]
    match = len(hits) == 1 and hits[0] == expect
    ok = ok and match
    print(("OK" if match else "MISMATCH"), hits[0] if hits else "MISSING")
print("UCI_OPTIONS", "PASS" if ok else "FAIL")
PY
python3 "$OUT/compare_nodes.py" "$OUT/B_O_d12.nodes" "$OUT/P_off_O_d12.nodes"
python3 "$OUT/compare_nodes.py" "$OUT/B_G_d12.nodes" "$OUT/P_off_G_d12.nodes"
python3 "$OUT/compare_nodes.py" "$OUT/B_O_d12.nodes" "$OUT/P_on_O_d12.nodes"
