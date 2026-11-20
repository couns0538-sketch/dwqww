#!/usr/bin/env bash
# Honesty check of exe B. One fresh process per line. No setoption.
set -u
EXE=/tmp/forge-B/forge
OUT=forge-combo29/grok/056
mkdir -p "$OUT"
sha=$(sha256sum "$EXE" | awk '{print $1}')
idname=$(printf 'uci\nquit\n' | "$EXE" | awk -F'id name ' '/^id name /{print $2; exit}')
run_one() {
  local tag="$1"
  local cmd="$2"
  local raw="$OUT/honesty_b_${tag}.txt"
  local meta="$OUT/honesty_b_${tag}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$raw"
  {
    echo "exe=$EXE"
    echo "sha256=$sha"
    echo "id_name=$idname"
    echo "options_sent=none"
    echo "command=$cmd"
  } > "$meta"
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
python3 - << 'PY'
from pathlib import Path
out = Path("forge-combo29/grok/056")
expect = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}
lines = []
ok = True
for tag, want in expect.items():
    text = (out / f"honesty_b_{tag}.txt").read_text()
    got = None
    for line in text.splitlines():
        if "nodes " in line:
            parts = line.replace(":", " ").split()
            if "nodes" in parts:
                got = int(parts[parts.index("nodes") + 1])
    match = got == want
    ok = ok and match
    lines.append(f"{tag} nodes {got} expect {want} {'OK' if match else 'MISMATCH'}")
text = "\n".join(lines) + ("\nHONESTY_B PASS\n" if ok else "\nHONESTY_B FAIL\n")
(out / "HONESTY_B.txt").write_text(text)
print(text, end="")
PY
