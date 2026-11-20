#!/usr/bin/env bash
# Honesty check of exe B. One fresh process per line. No setoption.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
cd "$REPO"
DIR="forge-combo29/grok/$S"
EXE="/agent/repos/base/forge-combo29/build-rel/forge"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | awk -F'\n' '/^id name /{print; exit}')
write_meta() {
  local out="$1"
  local sent="$2"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$IDNAME"
    echo "options_sent:"
    if [ -n "$sent" ]; then printf '%s\n' "$sent"; else echo "(none)"; fi
  } > "${out}.meta"
}
run_one() {
  local name="$1"
  local cmd="$2"
  local out="$DIR/$name"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$out"
  write_meta "$out" ""
  echo "WROTE $out"
}
run_one honesty_b_bench11.txt "bench 11"
run_one honesty_b_bench13.txt "bench 13"
run_one honesty_b_bench16.txt "bench 16"
run_one honesty_b_perft5.txt "go perft 5"
python3 - << 'PY'
import pathlib, os
repo = pathlib.Path(os.environ["REPO"]) if False else pathlib.Path(open(os.path.expanduser("~/grok_repo.txt")).read().strip())
S = open(os.path.expanduser("~/grok_seat.txt")).read().strip()
d = repo / "forge-combo29" / "grok" / S
expect = {
    "honesty_b_bench11.txt": ("bench 11", 312866),
    "honesty_b_bench13.txt": ("bench 13", 862329),
    "honesty_b_bench16.txt": ("bench 16", 3024920),
    "honesty_b_perft5.txt": ("go perft 5", 4865609),
}
lines = []
ok = True
for name, (label, want) in expect.items():
    text = (d / name).read_text(errors="replace")
    nodes = None
    for line in text.splitlines():
        if "nodes " in line:
            # last nodes token on the line
            parts = line.replace(":", " ").split()
            if "nodes" in parts:
                i = parts.index("nodes")
                if i + 1 < len(parts) and parts[i+1].isdigit():
                    nodes = int(parts[i+1])
    status = "PASS" if nodes == want else "FAIL"
    if nodes != want:
        ok = False
    lines.append(f"{label} nodes {nodes} expected {want} {status}")
    print(lines[-1])
out = d / "HONESTY_B.txt"
out.write_text("\n".join(lines) + "\n" + ("ALL PASS\n" if ok else "SOME FAILED\n"))
print(out.read_text())
PY
