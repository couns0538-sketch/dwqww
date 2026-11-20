#!/usr/bin/env bash
# Prove a partner patch on a fresh base worktree. My harness, not theirs.
# Usage: partner_prove.sh PATCH OPTION ON_NODES_FILE
# ON_NODES_FILE is the partner's own O depth-12 .nodes, or - if they have none.
set -u
PATCH="$1"
OPTION="$2"
THEIR_ON="$3"
REPO="$(cat ~/grok_repo.txt)"
S="$(cat ~/grok_seat.txt)"
OUT="$REPO/forge-combo29/grok/$S"
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7
SRC=/tmp/partner-src
if [ ! -d "$SRC/.git" ] && [ ! -f "$SRC/.git" ]; then
  git -C "$REPO" worktree add "$SRC" "$BASE"
fi
cd "$SRC"
git reset -q --hard "$BASE"
git clean -qfdx -e build -e build-asan
echo "---- apply check ----"
if git apply --check "$PATCH"; then
  echo APPLY_CHECK_OK
else
  echo APPLY_CHECK_FAIL
  exit 2
fi
git apply "$PATCH"
echo "---- build ----"
cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build build -j 4
EXE="$SRC/build/forge"
echo "---- honesty ----"
python3 - "$EXE" "$OUT" << 'PY'
import hashlib, subprocess, sys
from pathlib import Path
exe = Path(sys.argv[1])
out = Path(sys.argv[2])
expected = {"bench 11": 312866, "bench 13": 862329, "bench 16": 3024920, "go perft 5": 4865609}
digest = hashlib.sha256(exe.read_bytes()).hexdigest()
summary = [f"exe={exe}", f"sha256={digest}", "setoption=none"]
fail = False
for command, want in expected.items():
    proc = subprocess.run([str(exe)], input=command + "\nquit\n", text=True, capture_output=True, timeout=180)
    text = proc.stdout + proc.stderr
    slug = "partner_honesty_" + command.replace(" ", "_")
    (out / f"{slug}.txt").write_text(text)
    if command.startswith("bench"):
        line = next(l for l in text.splitlines() if l.startswith("info string bench"))
        parts = line.split()
        got = int(parts[parts.index("nodes") + 1])
    else:
        got = int(next(l for l in reversed(text.splitlines()) if l.startswith("nodes ")).split()[1])
    status = "OK" if got == want else "FAIL"
    if status != "OK":
        fail = True
    summary.append(f"{command} nodes {got} expected {want} {status}")
    (out / f"{slug}.meta").write_text(f"exe={exe}\nsha256={digest}\nid_name=see uci\noptions=\ncommand={command}\nnodes={got}\nexpected={want}\nmatch={str(got==want).lower()}\n")
(out / "PARTNER_HONESTY.txt").write_text("\n".join(summary) + "\n")
print("\n".join(summary))
sys.exit(1 if fail else 0)
PY
echo "---- off and on ----"
python3 "$OUT/depth_set.py" "$EXE" /tmp/first200.fens 12 PARTNER_off_O "setoption name $OPTION value false"
python3 "$OUT/depth_set.py" "$EXE" /tmp/first200.fens 12 PARTNER_on_O "setoption name $OPTION value true"
echo "---- compare off to exe B ----"
python3 "$OUT/compare_nodes.py" "$OUT/B_O_d12.nodes" "$OUT/PARTNER_off_O.nodes" 12 | tee "$OUT/partner_off_vs_B.txt"
if [ "$THEIR_ON" != "-" ] && [ -f "$THEIR_ON" ]; then
  echo "---- compare on to partner rows ----"
  python3 "$OUT/partner_vs_rows.py" "$THEIR_ON" "$OUT/PARTNER_on_O.nodes" | tee "$OUT/partner_on_vs_theirs.txt"
else
  echo "NO_PARTNER_ON_ROWS" | tee "$OUT/partner_on_vs_theirs.txt"
fi
echo "---- compare on to exe B ----"
python3 "$OUT/compare_nodes.py" "$OUT/B_O_d12.nodes" "$OUT/PARTNER_on_O.nodes" 12 | tee "$OUT/partner_on_vs_B.txt"
echo PARTNER_PROVE_DONE
