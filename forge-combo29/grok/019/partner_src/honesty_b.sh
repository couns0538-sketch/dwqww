#!/usr/bin/env bash
# Honesty check of exe B. One fresh process per line. No setoption.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE="${1:-/tmp/forge-B/forge}"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDLINE=$(printf 'uci\nquit\n' | "$EXE" | grep '^id name ' | head -n 1)

write_meta() {
  local out="$1"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$IDLINE"
    echo "options_sent=none"
    echo "command=$2"
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

run_one "bench 11" "$DIR/HONESTY_B_bench11.txt"
run_one "bench 13" "$DIR/HONESTY_B_bench13.txt"
run_one "bench 16" "$DIR/HONESTY_B_bench16.txt"
run_one "go perft 5" "$DIR/HONESTY_B_perft5.txt"

python3 - "$DIR" << 'PY'
import pathlib, sys
d = pathlib.Path(sys.argv[1])
want = {
    "HONESTY_B_bench11.txt": ("bench 11", 312866),
    "HONESTY_B_bench13.txt": ("bench 13", 862329),
    "HONESTY_B_bench16.txt": ("bench 16", 3024920),
    "HONESTY_B_perft5.txt": ("go perft 5", 4865609),
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
summary = d / "HONESTY_B.txt"
summary.write_text("\n".join(lines) + f"\nall_ok\t{str(ok).lower()}\n")
print(summary.read_text(), end="")
sys.exit(0 if ok else 1)
PY
