#!/usr/bin/env bash
# Honesty check: one fresh process per line, no setoption.
# usage: honesty_fresh.sh EXE TAG
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE="$1"
TAG="$2"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | sed -n 's/^id name //p' | head -n 1)

run_one() {
  local tag="$1"
  local cmd="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$OUT/${tag}.txt"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$IDNAME"
    echo "options_sent=none"
    echo "command=$cmd"
  } > "$OUT/${tag}.meta"
}

run_one "${TAG}_bench11" "bench 11"
run_one "${TAG}_bench13" "bench 13"
run_one "${TAG}_bench16" "bench 16"
run_one "${TAG}_perft5" "go perft 5"

python3 - "$OUT" "$TAG" <<'PY'
import pathlib, sys
out = pathlib.Path(sys.argv[1])
tag = sys.argv[2]
expect = {
    f"{tag}_bench11.txt": "312866",
    f"{tag}_bench13.txt": "862329",
    f"{tag}_bench16.txt": "3024920",
    f"{tag}_perft5.txt": "4865609",
}
ok = True
for name, nodes in expect.items():
    text = (out / name).read_text()
    good = nodes in text
    ok = ok and good
    print(f"{name} {'PASS' if good else 'FAIL'}")
print(("HONESTY " + tag + " PASS") if ok else ("HONESTY " + tag + " FAIL"))
sys.exit(0 if ok else 1)
PY
