#!/usr/bin/env bash
# Seat 061 partner check. Harness is this seat's harness.py, not the partner's.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7
mkdir -p "$D"
# Seats with idea 11: 011, 061, 111. Next after 061 is 111, then 011.
pick=""
for cand in 111 011; do
  if git ls-remote --heads origin "refs/heads/for-fable-and-opus/grok-$cand" | grep -q .; then
    pick=$cand
    break
  fi
done
if [ -z "$pick" ]; then
  echo "none" > "$D/partner_seat.txt"
  echo "NO_PARTNER" > "$D/partner_status.txt"
  exit 0
fi
echo "$pick" > "$D/partner_seat.txt"
found=0
for try in $(seq 1 11); do
  git fetch -q --depth 1 origin "for-fable-and-opus/grok-$pick" || true
  if git cat-file -e "FETCH_HEAD:forge-combo29/grok/$pick/idea.patch.txt" 2>/dev/null; then
    git show "FETCH_HEAD:forge-combo29/grok/$pick/idea.patch.txt" > "$D/partner.patch.txt"
    found=1
    break
  fi
  if [ "$try" -eq 11 ]; then
    break
  fi
  sleep 60
done
if [ "$found" -ne 1 ]; then
  echo "NO_PATCH" > "$D/partner_status.txt"
  exit 0
fi
echo "HAS_PATCH" > "$D/partner_status.txt"
# Claims, if the partner already wrote them.
git cat-file -e "FETCH_HEAD:forge-combo29/grok/$pick/RESULT.txt" 2>/dev/null && \
  git show "FETCH_HEAD:forge-combo29/grok/$pick/RESULT.txt" > "$D/partner_RESULT.txt" || true
git ls-tree -r --name-only FETCH_HEAD "forge-combo29/grok/$pick" > "$D/partner_files.txt"
WT=/tmp/partner-base
if [ ! -d "$WT" ]; then
  git worktree add "$WT" "$BASE"
fi
# Reset the tree in case a previous apply left changes.
git -C "$WT" checkout -f "$BASE" >/dev/null
git -C "$WT" clean -fd -e forge-combo29/build >/dev/null 2>&1 || true
if ! git -C "$WT" apply --check "$PWD/$D/partner.patch.txt" > "$D/partner_apply_check.txt" 2>&1; then
  echo "APPLY_CHECK_FAIL" >> "$D/partner_status.txt"
  exit 0
fi
echo "APPLY_CHECK_OK" >> "$D/partner_status.txt"
if ! git -C "$WT" apply "$PWD/$D/partner.patch.txt" > "$D/partner_apply.txt" 2>&1; then
  echo "APPLY_FAIL" >> "$D/partner_status.txt"
  exit 0
fi
echo "APPLY_OK" >> "$D/partner_status.txt"
rm -rf /tmp/forge-partner
if ! cmake -S "$WT/forge-combo29" -B /tmp/forge-partner -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ > "$D/partner_cmake.log" 2>&1; then
  echo "BUILD_FAIL" >> "$D/partner_status.txt"
  exit 0
fi
if ! cmake --build /tmp/forge-partner -j4 > "$D/partner_build.log" 2>&1; then
  echo "BUILD_FAIL" >> "$D/partner_status.txt"
  exit 0
fi
echo "BUILD_OK" >> "$D/partner_status.txt"
EXE=/tmp/forge-partner/forge
python3 "$D/harness.py" honesty --exe "$EXE" --out-dir "$D/partner_honesty" > "$D/partner_honesty.runlog" 2>&1 || echo "HONESTY_FAIL" >> "$D/partner_status.txt"
python3 "$D/tables.py" honesty "$D/partner_honesty" > "$D/partner_honesty_table.txt" || true
python3 "$D/harness.py" depth --exe "$EXE" --fens "$D/O.fens" --depth 12 --out "$D/partner_O_off_d12.txt" --s14 --idea false > "$D/partner_O_off.runlog" 2>&1 || echo "OFF_FAIL" >> "$D/partner_status.txt"
python3 "$D/tables.py" diff "$D/O_b_d12.txt" "$D/partner_O_off_d12.txt" > "$D/partner_off_diff.txt" || true
python3 "$D/harness.py" depth --exe "$EXE" --fens "$D/O.fens" --depth 12 --out "$D/partner_O_on_d12.txt" --s14 --idea true > "$D/partner_O_on.runlog" 2>&1 || echo "ON_FAIL" >> "$D/partner_status.txt"
python3 "$D/tables.py" sum "$D/partner_O_on_d12.txt" > "$D/partner_on_sum.txt" || true
# Their own on-rows, if a transcript with bestmove lines exists and is not the patch.
python3 - << PY
from pathlib import Path
import subprocess
root = Path("$D")
listing = (root / "partner_files.txt").read_text().splitlines()
cands = [p for p in listing if p.endswith(".txt") and "patch" not in p and "SEAT" not in p and "stamp" not in p]
(root / "partner_row_candidates.txt").write_text("\n".join(cands) + "\n")
print("candidates", len(cands))
PY
echo "MEASURED" >> "$D/partner_status.txt"
OPTS="option.Threads=1 option.Hash=16 option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=partner_on nodes=20000 $OPTS option.IdeaS25=true \
  -engine cmd="$EXE" name=partner_off nodes=20000 $OPTS option.IdeaS25=false \
  -openings file="$PWD/$D/R.fens" format=epd order=sequential \
  -rounds 300 -repeat -concurrency 3 \
  -pgnout file="$PWD/$D/partner_match.pgn" notation=uci nodes=true \
  > "$D/partner_match.txt" 2>&1
echo "MATCH_EXIT:$?" >> "$D/partner_status.txt"
