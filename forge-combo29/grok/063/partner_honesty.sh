#!/usr/bin/env bash
# Honesty check of the partner build. Fresh process per line. No setoption.
set -u
EXE=/tmp/partner/forge-combo29/build/forge
OUT="$(cd "$(dirname "$0")" && pwd)"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
ID=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{print; exit}')
run_one() {
  local name="$1"
  local cmd="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$OUT/${name}.txt"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$ID"
    echo "options=none"
    echo "command=$cmd"
  } > "$OUT/${name}.meta"
}
run_one partner_bench11 "bench 11"
run_one partner_bench13 "bench 13"
run_one partner_bench16 "bench 16"
run_one partner_perft5 "go perft 5"
python3 - << 'PY'
import pathlib, re
here = pathlib.Path("/agent/repos/dwqww/forge-combo29/grok/063")
expected = {
    "partner_bench11": 312866,
    "partner_bench13": 862329,
    "partner_bench16": 3024920,
    "partner_perft5": 4865609,
}
lines = []
ok = True
for name, want in expected.items():
    found = [int(n) for n in re.findall(r"nodes (\d+)", (here / f"{name}.txt").read_text())]
    got = found[-1] if found else None
    match = got == want
    ok = ok and match
    lines.append(f"{name} nodes {got} expected {want} match {str(match).lower()}")
lines.append(f"partner_honesty {str(ok).lower()}")
(here / "partner_honesty.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
PY
