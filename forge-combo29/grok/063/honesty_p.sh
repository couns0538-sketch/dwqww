#!/usr/bin/env bash
# Honesty check on the patched engine. One fresh process per line. No setoption.
set -u
EXE=/agent/repos/work/forge-combo29/build/forge
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
run_one p_bench11 "bench 11"
run_one p_bench13 "bench 13"
run_one p_bench16 "bench 16"
run_one p_perft5 "go perft 5"
python3 - << 'PY'
import pathlib, re
here = pathlib.Path("/agent/repos/dwqww/forge-combo29/grok/063")
expected = {"p_bench11": 312866, "p_bench13": 862329, "p_bench16": 3024920, "p_perft5": 4865609}
lines = []
ok = True
for name, want in expected.items():
    text = (here / f"{name}.txt").read_text()
    found = [int(n) for n in re.findall(r"nodes (\d+)", text)]
    got = found[-1] if found else None
    match = got == want
    ok = ok and match
    lines.append(f"{name} nodes {got} expected {want} match {str(match).lower()}")
lines.append(f"honesty_p {str(ok).lower()}")
(here / "HONESTY_P.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
PY
