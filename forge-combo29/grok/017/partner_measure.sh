#!/usr/bin/env bash
# Measure a partner build that partner_review.sh already produced.
# Usage: partner_measure.sh NNN
set -u
PARTNER="${1:?partner seat}"
REPO=$(cat ~/grok_repo.txt)
SEAT=$(cat ~/grok_seat.txt)
DIR="$REPO/forge-combo29/grok/$SEAT"
EXE=/tmp/build-partner/forge
cd "$DIR"
python3 honesty_check.py "$EXE" . "Partner$PARTNER"
python3 uci_suite.py --exe "$EXE" --positions O.fens --depth 12 --out "raw_partner_${PARTNER}_off_O_d12.txt" --options s14.txt --options s15_off.txt
python3 uci_suite.py --exe "$EXE" --positions O.fens --depth 12 --out "raw_partner_${PARTNER}_on_O_d12.txt" --options s14.txt --options s15_on.txt
echo "==== off versus B ===="
python3 compare_nodes.py raw_B_O_d12.txt "raw_partner_${PARTNER}_off_O_d12.txt" | tee "compare_partner_${PARTNER}_off.txt"
echo "==== on versus B ===="
python3 compare_nodes.py raw_B_O_d12.txt "raw_partner_${PARTNER}_on_O_d12.txt" | tee "compare_partner_${PARTNER}_on_vs_B.txt"
echo "==== on versus partner rows ===="
python3 - "$PARTNER" << 'PY' | tee "compare_partner_${PARTNER}_on_vs_theirs.txt"
import sys
from pathlib import Path
partner = sys.argv[1]
theirs = []
for line in Path(f"partner_{partner}_O_on.nodes").read_text().splitlines():
    if not line.strip():
        continue
    theirs.append(int(line.split()[1]))
mine = []
last = None
for line in Path(f"raw_partner_{partner}_on_O_d12.txt").read_text().splitlines():
    if line.startswith("info ") and " nodes " in line:
        last = int(line.split(" nodes ")[1].split()[0])
    if line.startswith("bestmove "):
        mine.append(last)
        last = None
differ = [i for i, (a, b) in enumerate(zip(mine, theirs), start=1) if a != b]
print(f"mine {len(mine)} sum {sum(mine)}")
print(f"theirs {len(theirs)} sum {sum(theirs)}")
print(f"differ {len(differ)} of {len(mine)}")
PY
bash match.sh "$EXE" 300 "$DIR/R.epd" "match_partner_${PARTNER}.log" "match_partner_${PARTNER}.pgn" PartnerOn PartnerOff option.IdeaS15=true option.IdeaS15=false
python3 parse_match.py "match_partner_${PARTNER}.log" | tee "match_partner_${PARTNER}_summary.txt"
