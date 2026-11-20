#!/usr/bin/env bash
# Honesty check of exe B. One fresh process per line. No setoption.
set -u
EXE=/agent/repos/base/forge-combo29/build-rel/forge
OUT="$(cd "$(dirname "$0")" && pwd)"
sha=$(sha256sum "$EXE" | awk '{print $1}')
printf 'uci\nquit\n' | "$EXE" > "$OUT/id_B.txt"
id_name=$(sed -n 's/^id name //p' "$OUT/id_B.txt" | head -1)

run_one() {
  local name="$1"
  local cmd="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$OUT/${name}.txt"
  {
    echo "exe=$EXE"
    echo "sha256=$sha"
    echo "id_name=$id_name"
    echo "option_lines=none"
    echo "command=$cmd"
    echo "started=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$OUT/${name}.meta"
}

run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"

python3 - "$OUT" << 'PY'
import pathlib, sys
out = pathlib.Path(sys.argv[1])
expect = {
    "bench11": ("bench 11", 312866),
    "bench13": ("bench 13", 862329),
    "bench16": ("bench 16", 3024920),
    "perft5": ("go perft 5", 4865609),
}
lines = []
ok = True
for name, (label, want) in expect.items():
    text = (out / f"{name}.txt").read_text(errors="replace")
    got = None
    for line in text.splitlines():
        if name.startswith("bench") and "nodes" in line and "bench" in line:
            parts = line.split()
            if "nodes" in parts:
                got = int(parts[parts.index("nodes") + 1])
        if name == "perft5" and line.startswith("nodes "):
            got = int(line.split()[1])
    status = "PASS" if got == want else "FAIL"
    if got != want:
        ok = False
    lines.append(f"{label} nodes {got} expect {want} {status}")
    print(lines[-1])
text = "\n".join(lines) + "\n" + ("HONESTY_B ALL PASS\n" if ok else "HONESTY_B FAIL\n")
(out / "HONESTY_B.txt").write_text(text)
print(text, end="")
PY
