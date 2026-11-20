#!/usr/bin/env bash
# Evaluate a partner patch on a fresh base worktree. Harness is measure.py / honesty style, not the partner's.
# Usage: partner_eval.sh PATCH_FILE
set -u
PATCH="$1"
S=$(cat ~/grok_seat.txt)
DIR="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7
git -C "$(cat ~/grok_repo.txt)" worktree remove --force /tmp/partner-work 2>/dev/null || true
rm -rf /tmp/partner-work /tmp/build-partner
git -C "$(cat ~/grok_repo.txt)" worktree prune
git -C "$(cat ~/grok_repo.txt)" worktree add /tmp/partner-work "$BASE"
cd /tmp/partner-work
git apply --check "$PATCH"
echo APPLY_CHECK_OK
git apply "$PATCH"
echo APPLY_OK
cmake -S /tmp/partner-work/forge-combo29 -B /tmp/build-partner -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/build-partner -j4
EXE=/tmp/build-partner/forge
sha=$(sha256sum "$EXE" | awk '{print $1}')
idname=$(printf 'uci\nquit\n' | "$EXE" | sed -n 's/^id name //p' | head -1)
for spec in "11 bench 11" "13 bench 13" "16 bench 16" "5 go perft 5"; do
  set -- $spec
  tag=$1
  shift
  cmd="$*"
  {
    echo "exe=$EXE"
    echo "sha256=$sha"
    echo "id_name=$idname"
    echo "command=$cmd"
    echo "options_sent=none"
  } > "$DIR/partner_honesty_${tag}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$DIR/partner_honesty_${tag}.txt"
done
python3 - << 'PY'
import pathlib, re
d = pathlib.Path("/agent/repos/dwqww/forge-combo29/grok/071")
rows = [("bench 11","partner_honesty_11.txt",312866),("bench 13","partner_honesty_13.txt",862329),("bench 16","partner_honesty_16.txt",3024920),("go perft 5","partner_honesty_5.txt",4865609)]
lines=["command\texpected\tnodes\tmatch"]
ok=True
for cmd,name,expected in rows:
    text=(d/name).read_text(errors="replace")
    found=[int(n) for n in re.findall(r"nodes (\d+)", text)]
    nodes=found[-1] if found else -1
    match=nodes==expected
    ok=ok and match
    lines.append(f"{cmd}\t{expected}\t{nodes}\t{'yes' if match else 'NO'}")
lines.append("all_match\t"+("yes" if ok else "NO"))
(d/"PARTNER_HONESTY.txt").write_text("\n".join(lines)+"\n")
print("\n".join(lines))
PY
python3 "$DIR/measure.py" "$EXE" 12 "$DIR/O.fens" "$DIR/partner_off_o" \
  "setoption name IdeaS26 value false" \
  "setoption name IdeaS26_Floor value 7" \
  "setoption name IdeaS26_OrderDepth value 6"
python3 "$DIR/measure.py" "$EXE" 12 "$DIR/O.fens" "$DIR/partner_on_o" \
  "setoption name IdeaS26 value true" \
  "setoption name IdeaS26_Floor value 7" \
  "setoption name IdeaS26_OrderDepth value 6"
echo PARTNER_MEASURE_DONE
