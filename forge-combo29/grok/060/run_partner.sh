#!/usr/bin/env bash
# Evaluate seat 010's idea.patch.txt with this seat's own harness.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
cd "$REPO"
PARTNER=010
DIR="$REPO/forge-combo29/grok/$S"
git fetch -q --depth 1 origin "for-fable-and-opus/grok-$PARTNER"
if ! git cat-file -e "FETCH_HEAD:forge-combo29/grok/$PARTNER/idea.patch.txt"; then
  echo NO_PATCH
  exit 3
fi
git show "FETCH_HEAD:forge-combo29/grok/$PARTNER/idea.patch.txt" > "$DIR/partner.patch.txt"
git show "FETCH_HEAD:forge-combo29/grok/$PARTNER/p_on_O_d12.rows" > "$DIR/partner_on_O.rows"
git show "FETCH_HEAD:forge-combo29/grok/$PARTNER/p_on_O_d12.sum" > "$DIR/partner_on_O.sum"
git show "FETCH_HEAD:forge-combo29/grok/$PARTNER/p_off_O_d12.sum" > "$DIR/partner_off_O.sum"
git show "FETCH_HEAD:forge-combo29/grok/$PARTNER/match_on_vs_off.parse" > "$DIR/partner_match.parse"
git show "FETCH_HEAD:forge-combo29/grok/$PARTNER/design.txt" > "$DIR/partner_design.txt"
git rev-parse FETCH_HEAD > "$DIR/partner_commit.txt"
if [ -d /tmp/partner ]; then
  git worktree remove --force /tmp/partner || rm -rf /tmp/partner
fi
git worktree add --detach /tmp/partner 6b98f2170a3210e71beed04bbd2553972c253ed7
cd /tmp/partner
if ! git apply --check "$DIR/partner.patch.txt"; then
  echo APPLY_CHECK_FAIL
  exit 4
fi
echo APPLY_CHECK_OK
git apply "$DIR/partner.patch.txt"
rm -rf /tmp/forge-partner
cmake -S /tmp/partner/forge-combo29 -B /tmp/forge-partner -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++-13
cmake --build /tmp/forge-partner -j4
EXE=/tmp/forge-partner/forge
cd "$REPO"
mkdir -p "$DIR/partner_honesty"
python3 "$DIR/honesty_run.py" "$EXE" "$DIR/partner_honesty" "$DIR/PARTNER_HONESTY.txt"
python3 "$DIR/search_set.py" "$EXE" "$DIR/O.fens" 12 "$DIR/partner_off_O" false IdeaS24
python3 "$DIR/search_set.py" "$EXE" "$DIR/O.fens" 12 "$DIR/partner_on_O" true IdeaS24
python3 "$DIR/compare_rows.py" "$DIR/B_O_d12.tsv" "$DIR/partner_off_O.tsv" > "$DIR/partner_proof_off.txt"
python3 "$DIR/partner_rows_to_tsv.py" "$DIR/partner_on_O.rows" "$DIR/partner_claimed_on.tsv"
python3 "$DIR/compare_rows.py" "$DIR/partner_claimed_on.tsv" "$DIR/partner_on_O.tsv" > "$DIR/partner_proof_on.txt"
python3 "$DIR/sum_nodes.py" "$DIR/partner_on_O.tsv" 12 > "$DIR/partner_on_sum.txt"
python3 "$DIR/sum_nodes.py" "$DIR/partner_off_O.tsv" 12 > "$DIR/partner_off_sum.txt"
bash "$DIR/run_r_match.sh" "$EXE" IdeaS24 "$DIR/partner_match_stdout.txt" "$DIR/partner_match.pgn"
python3 "$DIR/match_summary.py" "$DIR/partner_match_stdout.txt" > "$DIR/partner_match_summary.txt"
if [ -f "$DIR/config.json" ]; then
  mv "$DIR/config.json" "$DIR/partner_config.json"
  git checkout -- "forge-combo29/grok/$S/config.json"
fi
echo PARTNER_EVAL_DONE
