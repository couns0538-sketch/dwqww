#!/usr/bin/env bash
# Partner review. This seat's harness only.
set -eu
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
DIR="$REPO/forge-combo29/grok/$S"
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7
PARTNER="${1:?partner seat}"
cd "$REPO"
git fetch -q --depth 1 origin "for-fable-and-opus/grok-$PARTNER"
git ls-tree -r --name-only FETCH_HEAD | grep "forge-combo29/grok/$PARTNER/" | tee "$DIR/partner_files.txt"
if ! git cat-file -e "FETCH_HEAD:forge-combo29/grok/$PARTNER/idea.patch.txt"; then
  echo "NO_PATCH"
  exit 0
fi
git show "FETCH_HEAD:forge-combo29/grok/$PARTNER/idea.patch.txt" > "$DIR/partner.patch.txt"
# Keep a copy of their tree files that look like depth-12 raw output, if any.
mkdir -p "$DIR/partner_raw"
git ls-tree -r --name-only FETCH_HEAD | grep "forge-combo29/grok/$PARTNER/" | while read -r path; do
  base=$(basename "$path")
  case "$base" in
    *.txt|*.rows|*.md|*.epd|*.fens) git show "FETCH_HEAD:$path" > "$DIR/partner_raw/$base" ;;
  esac
done
rm -rf /tmp/partner-base
git worktree add --detach /tmp/partner-base "$BASE"
cd /tmp/partner-base
if ! git apply --check "$DIR/partner.patch.txt"; then
  echo "APPLY_CHECK_FAIL"
  exit 1
fi
echo "APPLY_CHECK_OK"
git apply "$DIR/partner.patch.txt"
echo "APPLY_OK"
cmake -S forge-combo29 -B /tmp/partner-build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/partner-build -j 4
echo "BUILD_OK $(date -u +%Y-%m-%dT%H:%M:%SZ)"
python3 "$DIR/run_honesty_exe.py" /tmp/partner-build/forge "$DIR/partner_honesty"
python3 "$DIR/run_depth_set.py" /tmp/partner-build/forge /tmp/positions/first200.fens 12 false "$DIR/partner_O_off_d12.txt"
python3 "$DIR/run_depth_set.py" /tmp/partner-build/forge /tmp/positions/first200.fens 12 true "$DIR/partner_O_on_d12.txt"
python3 "$DIR/report_nodes.py" "$DIR/partner_O_off_d12.txt" "$DIR/O_B_d12.txt" | tee "$DIR/partner_off_vs_B.txt"
python3 "$DIR/report_nodes.py" "$DIR/partner_O_on_d12.txt" | tee "$DIR/partner_on_sum.txt"
echo "DEPTH_OK $(date -u +%Y-%m-%dT%H:%M:%SZ)"
