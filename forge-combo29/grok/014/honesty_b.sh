#!/usr/bin/env bash
# Fresh process per honesty line. No setoption.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
EXE=/agent/repos/base/forge-combo29/build/forge
OUT="forge-combo29/grok/$S"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDLINE=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name/{print; exit}')
rm -f "$OUT/_B.txt" "$OUT/_B.meta"
runone() {
  local tag="$1"
  local cmd="$2"
  local raw="$OUT/${tag}_B.txt"
  local meta="$OUT/${tag}_B.meta"
  local start end
  start=$(date +%s)
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$raw"
  end=$(date +%s)
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$IDLINE"
    echo "options=none"
    echo "command=$cmd"
    echo "seconds=$((end - start))"
  } > "$meta"
  echo "$tag seconds=$((end - start))"
  awk '/nodes/{line=$0} END{print line}' "$raw"
}
runone bench11 "bench 11"
runone bench13 "bench 13"
runone bench16 "bench 16"
runone perft5 "go perft 5"
python3 - "$OUT" << 'PY'
import pathlib, sys
out = pathlib.Path(sys.argv[1])
expect = {"bench11": "312866", "bench13": "862329", "bench16": "3024920", "perft5": "4865609"}
lines = []
for tag, nodes in expect.items():
    raw = (out / f"{tag}_B.txt").read_text().splitlines()
    hit = [ln.strip() for ln in raw if "nodes" in ln]
    lines.append(f"{tag} expect {nodes}")
    lines.append(hit[-1] if hit else "MISSING")
(out / "HONESTY_B.txt").write_text("\n".join(lines) + "\n")
print((out / "HONESTY_B.txt").read_text())
PY
