#!/usr/bin/env bash
# Review the partner patch with this seat's own harness. Not a copy of theirs.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
PARTNER="${1:?partner seat}"
cd "$REPO"
OUT="forge-combo29/grok/$S"
mkdir -p "$OUT/partner"
git fetch -q --depth 1 origin "for-fable-and-opus/grok-$PARTNER"
git show "FETCH_HEAD:forge-combo29/grok/$PARTNER/idea.patch.txt" > "$OUT/partner/idea.patch.txt"
echo "fetched $(git rev-parse FETCH_HEAD)" > "$OUT/partner/fetch.txt"
# Fresh worktree of the base. Remove a previous one if this script is repeated.
git worktree remove --force ../partner 2>/dev/null || true
rm -rf ../partner
git worktree add ../partner 6b98f2170a3210e71beed04bbd2553972c253ed7
cd ../partner
if git apply --check "$REPO/$OUT/partner/idea.patch.txt" > "$REPO/$OUT/partner/apply_check.txt" 2>&1; then
  echo APPLY_CHECK_OK >> "$REPO/$OUT/partner/apply_check.txt"
else
  echo APPLY_CHECK_FAIL >> "$REPO/$OUT/partner/apply_check.txt"
  exit 2
fi
git apply "$REPO/$OUT/partner/idea.patch.txt"
cmake -S forge-combo29 -B /tmp/forge-partner -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/forge-partner -j 4
cd "$REPO"
# honesty_p.sh writes the seat's HONESTY_P names. Save them and put them back.
mkdir -p /tmp/honesty_save
cp "$OUT"/honesty_p_*.txt "$OUT"/honesty_p_*.meta "$OUT/HONESTY_P.txt" /tmp/honesty_save/
bash "$OUT/honesty_p.sh" /tmp/forge-partner/forge
cp "$OUT/HONESTY_P.txt" "$OUT/partner/HONESTY.txt"
cp "$OUT/honesty_p_bench11.txt" "$OUT/partner/honesty_bench11.txt"
cp "$OUT/honesty_p_bench13.txt" "$OUT/partner/honesty_bench13.txt"
cp "$OUT/honesty_p_bench16.txt" "$OUT/partner/honesty_bench16.txt"
cp "$OUT/honesty_p_perft5.txt" "$OUT/partner/honesty_perft5.txt"
cp "$OUT/honesty_p_bench11.meta" "$OUT/partner/honesty_bench11.meta"
cp "$OUT/honesty_p_bench13.meta" "$OUT/partner/honesty_bench13.meta"
cp "$OUT/honesty_p_bench16.meta" "$OUT/partner/honesty_bench16.meta"
cp "$OUT/honesty_p_perft5.meta" "$OUT/partner/honesty_perft5.meta"
cp /tmp/honesty_save/* "$OUT/"
python3 "$OUT/depth_set.py" /tmp/forge-partner/forge "$OUT/first200.fens" 12 "$OUT/partner/off_O" "IdeaK11 false"
python3 "$OUT/depth_set.py" /tmp/forge-partner/forge "$OUT/first200.fens" 12 "$OUT/partner/on_O" "IdeaK11 true"
python3 "$OUT/compare_rows.py" "$OUT/B_O_d12.rows" "$OUT/partner/off_O.rows" > "$OUT/partner/compare_off.txt"
python3 "$OUT/compare_rows.py" "$OUT/B_O_d12.rows" "$OUT/partner/on_O.rows" > "$OUT/partner/compare_on_vs_B.txt"
echo PARTNER_SEARCH_DONE
