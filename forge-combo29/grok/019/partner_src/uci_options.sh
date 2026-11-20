#!/usr/bin/env bash
# Record the uci option list of one exe. No setoption.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE="$1"
TAG="$2"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
printf 'uci\nquit\n' | "$EXE" > "$DIR/UCI_${TAG}.txt"
{
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "id_name=$(grep '^id name ' "$DIR/UCI_${TAG}.txt" | head -n 1)"
  echo "options_sent=none"
  echo "command=uci"
  echo "started=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "raw=$DIR/UCI_${TAG}.txt"
} > "$DIR/UCI_${TAG}.txt.meta"
python3 - "$DIR/UCI_${TAG}.txt" << 'PY'
import sys
text = open(sys.argv[1], encoding="utf-8", errors="replace").read().splitlines()
want = {
    "IdeaS20": "option name IdeaS20 type check default false",
    "IdeaS20_MinPly": "option name IdeaS20_MinPly type spin default 2 min 2 max 8",
}
for line in text:
    if "IdeaS20" in line:
        print(line)
for key, exact in want.items():
    hit = [line for line in text if line == exact]
    print(f"{key}\t{'OK' if hit else 'MISS'}")
PY
