#!/usr/bin/env bash
# Honesty check. One fresh process per line. No setoption.
# Usage: honesty_check.sh EXE TAG
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE="$1"
TAG="$2"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDLINE=$(printf 'uci\nquit\n' | "$EXE" | grep '^id name ' | head -n 1)

write_meta() {
  local out="$1"
  local cmd="$2"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$IDLINE"
    echo "options_sent=none"
    echo "command=$cmd"
    echo "started=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "raw=$out"
  } > "${out}.meta"
}

run_one() {
  local cmd="$1"
  local out="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$out"
  write_meta "$out" "$cmd"
}

run_one "bench 11" "$DIR/HONESTY_${TAG}_bench11.txt"
run_one "bench 13" "$DIR/HONESTY_${TAG}_bench13.txt"
run_one "bench 16" "$DIR/HONESTY_${TAG}_bench16.txt"
run_one "go perft 5" "$DIR/HONESTY_${TAG}_perft5.txt"

python3 - "$DIR" "$TAG" << 'PY'
import pathlib, sys
d = pathlib.Path(sys.argv[1])
tag = sys.argv[2]
want = {
    f"HONESTY_{tag}_bench11.txt": ("bench 11", 312866),
    f"HONESTY_{tag}_bench13.txt": ("bench 13", 862329),
    f"HONESTY_{tag}_bench16.txt": ("bench 16", 3024920),
    f"HONESTY_{tag}_perft5.txt": ("go perft 5", 4865609),
}
lines = []
ok = True
for name, (label, expected) in want.items():
    text = (d / name).read_text(errors="replace")
    nodes = None
    for line in text.splitlines():
        parts = line.split()
        if "nodes" in parts:
            nodes = int(parts[parts.index("nodes") + 1])
    match = nodes == expected
    ok = ok and match
    lines.append(f"{label}\tnodes\t{nodes}\texpected\t{expected}\t{'OK' if match else 'MISS'}")
summary = d / f"HONESTY_{tag}.txt"
summary.write_text("\n".join(lines) + f"\nall_ok\t{str(ok).lower()}\n")
print(summary.read_text(), end="")
sys.exit(0 if ok else 1)
PY
