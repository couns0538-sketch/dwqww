#!/usr/bin/env bash
# Apply the extracted partner patch on a fresh base and measure it with our harness.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
cd "$REPO"
DIR="$REPO/forge-combo29/grok/$S"
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7
PATCH="$DIR/partner_src/idea.patch.txt"
WT=/tmp/pwt
git worktree remove -f "$WT" 2>/dev/null || true
rm -rf "$WT"
git worktree add --detach "$WT" "$BASE"
{
  echo "apply_check_begin $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if git -C "$WT" apply --check "$PATCH"; then
    echo "APPLY_CHECK_OK"
  else
    echo "APPLY_CHECK_FAIL"
    exit 2
  fi
  git -C "$WT" apply "$PATCH"
  echo "APPLY_OK"
} > "$DIR/partner_apply.txt"
cat "$DIR/partner_apply.txt"
grep -q APPLY_OK "$DIR/partner_apply.txt"
cmake -S "$WT/forge-combo29" -B "$WT/forge-combo29/build-rel" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build "$WT/forge-combo29/build-rel" -j4
EXE="$WT/forge-combo29/build-rel/forge"
test -x "$EXE"
bash "$DIR/honesty_one.sh" "$EXE" partner_h
printf 'uci\nquit\n' | "$EXE" > "$DIR/partner_uci.txt"
python3 - "$DIR" << 'PY'
import sys
from pathlib import Path
d = Path(sys.argv[1])
base = Path("/agent/repos/base/forge-combo29/build-rel/forge")
import subprocess
base_uci = subprocess.check_output([str(base)], input="uci\nquit\n", text=True).splitlines()
new = []
base_set = set(base_uci)
for line in (d / "partner_uci.txt").read_text().splitlines():
    if line.startswith("option name ") and line not in base_set:
        new.append(line)
(d / "partner_new_options.txt").write_text("\n".join(new) + ("\n" if new else ""))
checks = []
for line in new:
    parts = line.split()
    # option name <name...> type check default <bool>
    if "type" in parts and parts[parts.index("type") + 1] == "check":
        name = " ".join(parts[2:parts.index("type")])
        checks.append(name)
(d / "partner_checks.txt").write_text("\n".join(checks) + ("\n" if checks else ""))
print("new_options", len(new))
print("checks", checks)
PY
# Prefer the idea's check name. Fall back to the only new check.
CHECK=$(python3 - << 'PY'
from pathlib import Path
import os
d = Path(os.environ["DIR"]) if False else Path(open("/home/ubuntu/grok_repo.txt").read().strip()) / "forge-combo29" / "grok" / open("/home/ubuntu/grok_seat.txt").read().strip()
names = [ln.strip() for ln in (d / "partner_checks.txt").read_text().splitlines() if ln.strip()]
prefer = [n for n in names if n in ("IdeaS20", "S20") or "S20" in n]
if prefer:
    print(prefer[0])
elif len(names) == 1:
    print(names[0])
else:
    print("")
PY
)
echo "USING_CHECK=$CHECK" | tee "$DIR/partner_using_check.txt"
if [ -z "$CHECK" ]; then
  echo "NO_CHECK_OPTION" | tee -a "$DIR/partner_status.txt"
  exit 3
fi
printf '%s false\n' "$CHECK" > "$DIR/partner_opt_off.txt"
printf '%s true\n' "$CHECK" > "$DIR/partner_opt_on.txt"
python3 "$DIR/measure_depth.py" "$EXE" "$DIR/O.fens" 12 "$DIR/partner_off_O" - "$DIR/partner_opt_off.txt"
python3 "$DIR/measure_depth.py" "$EXE" "$DIR/O.fens" 12 "$DIR/partner_on_O" - "$DIR/partner_opt_on.txt"
echo "PROVE_MEASURED $(date -u +%Y-%m-%dT%H:%M:%SZ)"
