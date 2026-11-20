#!/usr/bin/env bash
# Record the uci option list of one exe. No setoption.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
EXE="$1"
TAG="$2"
OUT="forge-combo29/grok/$S/${TAG}.txt"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
printf 'uci\nquit\n' | "$EXE" > "$OUT"
{
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "id_name=$(sed -n 's/^id name //p' "$OUT" | head -n 1)"
  echo "options_sent=none"
  echo "command=uci"
} > "forge-combo29/grok/$S/${TAG}.meta"
python3 - "$OUT" <<'PY'
import sys
text = open(sys.argv[1]).read().splitlines()
want = ("option name EvalRule50Damp ", "option name EvalRule50Damp_Span ")
for w in want:
    hits = [ln for ln in text if ln.startswith(w)]
    print(f"hits {len(hits)} {w.strip()}")
    for ln in hits:
        print(ln)
PY
