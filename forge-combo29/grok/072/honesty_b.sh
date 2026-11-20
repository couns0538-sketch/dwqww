#!/usr/bin/env bash
# Honesty check of exe B. One fresh process per line. No setoption.
set -eu
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
EXE=/agent/repos/base/build/forge
DIR="forge-combo29/grok/$S"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | grep '^id name ' | head -1)

write_meta() {
  local stem="$1"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$IDNAME"
    echo "options_sent:"
    echo "(none)"
  } > "$DIR/${stem}.meta"
}

run_one() {
  local stem="$1"
  local cmd="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$DIR/${stem}.txt"
  write_meta "$stem"
}

run_one honesty_b_bench11 "bench 11"
run_one honesty_b_bench13 "bench 13"
run_one honesty_b_bench16 "bench 16"
run_one honesty_b_perft5 "go perft 5"

python3 - "$DIR" << 'PY'
import re, sys
from pathlib import Path
d = Path(sys.argv[1])
expect = {
    "honesty_b_bench11": 312866,
    "honesty_b_bench13": 862329,
    "honesty_b_bench16": 3024920,
    "honesty_b_perft5": 4865609,
}
lines = []
ok = True
for stem, want in expect.items():
    text = (d / f"{stem}.txt").read_text(errors="replace")
    if stem.startswith("honesty_b_bench"):
        m = re.search(r"info string bench depth \d+ nodes (\d+)", text)
    else:
        m = None
        for line in text.splitlines():
            if re.fullmatch(r"nodes \d+", line.strip()):
                m = re.match(r"nodes (\d+)", line.strip())
    got = int(m.group(1)) if m else -1
    flag = "OK" if got == want else "MISS"
    if got != want:
        ok = False
    lines.append(f"{stem} nodes {got} expected {want} {flag}")
lines.append("HONESTY_B " + ("PASS" if ok else "FAIL"))
out = "\n".join(lines) + "\n"
(d / "HONESTY_B.txt").write_text(out)
print(out, end="")
sys.exit(0 if ok else 1)
PY
