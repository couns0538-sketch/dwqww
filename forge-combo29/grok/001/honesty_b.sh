#!/usr/bin/env bash
# Honesty check of exe B. One fresh process per line. No setoption.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE="/agent/repos/base/forge-combo29/build/forge"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | sed -n 's/^id name //p' | head -n 1)

run_one() {
  local tag="$1"
  local cmd="$2"
  local raw="$OUT/${tag}.txt"
  local meta="$OUT/${tag}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$raw"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$IDNAME"
    echo "options_sent=none"
    echo "command=$cmd"
  } > "$meta"
  echo "WROTE $raw"
}

run_one honesty_b_bench11 "bench 11"
run_one honesty_b_bench13 "bench 13"
run_one honesty_b_bench16 "bench 16"
run_one honesty_b_perft5 "go perft 5"

python3 - "$OUT" <<'PY'
import pathlib, sys
out = pathlib.Path(sys.argv[1])
expect = {
    "honesty_b_bench11.txt": ("bench depth 11 nodes 312866", 312866),
    "honesty_b_bench13.txt": ("bench depth 13 nodes 862329", 862329),
    "honesty_b_bench16.txt": ("bench depth 16 nodes 3024920", 3024920),
    "honesty_b_perft5.txt": ("nodes 4865609", 4865609),
}
lines = []
ok = True
for name, (needle, nodes) in expect.items():
    text = (out / name).read_text()
    hit = [ln.strip() for ln in text.splitlines() if needle in ln]
    good = len(hit) == 1
    ok = ok and good
    lines.append(f"{name} {'PASS' if good else 'FAIL'} hits={len(hit)} expected_nodes={nodes}")
    for ln in hit:
        lines.append(ln)
    if not good:
        lines.append("--- raw ---")
        lines.append(text.rstrip())
        lines.append("--- end ---")
lines.append("HONESTY_B " + ("PASS" if ok else "FAIL"))
text = "\n".join(lines) + "\n"
(out / "HONESTY_B.txt").write_text(text)
print(text, end="")
sys.exit(0 if ok else 1)
PY
