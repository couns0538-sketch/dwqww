#!/usr/bin/env bash
# run_pc20.sh — re-run seat 08's own findings on the PC build under PC20. Guarded.
set -u
EXE="$HOME/builds/pc/forge"
D="$(cd "$(dirname "$0")" && pwd)"
cd "$D"

if pgrep -f 'pc20_timing|builds/pc/forge|builds/release/forge' >/dev/null; then
  echo "GUARD: another engine process is running; refusing to start"; exit 1
fi
LOAD=$(cut -d' ' -f1 /proc/loadavg)
if awk -v l="$LOAD" 'BEGIN{exit !(l > 0.5)}'; then
  echo "GUARD: load $LOAD > 0.5; refusing to start"; exit 1
fi
echo "GUARD ok: load $LOAD, no other engine process"

mkdir -p raw
cp ../job1/OG200.fens .
sha256sum "$EXE" > raw/exe_sha256.txt
{
  echo "exe_started $EXE"
  echo "sha256 $(cut -d' ' -f1 raw/exe_sha256.txt)"
  printf 'uci\nquit\n' | "$EXE" | grep -E '^id name'
  echo "SETTINGS: PC20 = S14 (14 lines) + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,"
  echo "          MateAlphaGuard true, OwnBook false, then Threads 1 and Hash 16."
  echo "          ucinewgame + isready before every search."
  echo "BUILD: PC r15, patch sha256 d6bd72c531f785f4..., applied with patch -p1 --fuzz=0 to a separate 6b98f217 worktree."
  echo "guard: load at start $(cut -d' ' -f1-3 /proc/loadavg), no other engine process"
} > raw/.meta
: > stamps.txt
date -u >> stamps.txt

# 08-F2: movetime plan
python3 pc20_timing.py "$EXE" OG200.fens "movetime 50" raw/mt50_a.jsonl "pc20_mt50_a" && date -u >> stamps.txt
python3 pc20_timing.py "$EXE" OG200.fens "movetime 50" raw/mt50_b.jsonl "pc20_mt50_b" && date -u >> stamps.txt
python3 pc20_timing.py "$EXE" OG200.fens "movetime 500" raw/mt500.jsonl "pc20_mt500" && date -u >> stamps.txt
# 08-F1/F9/F10/F11/F14: clocked behaviour and the tail
python3 pc20_timing.py "$EXE" OG200.fens "wtime 1000 btime 1000 winc 0 binc 0" raw/tc1000.jsonl "pc20_tc1000" && date -u >> stamps.txt
python3 pc20_timing.py "$EXE" OG200.fens "wtime 10000 btime 10000 winc 0 binc 0" raw/tc10000.jsonl "pc20_tc10000" && date -u >> stamps.txt
# 08-F8: movestogo at the hard limit
for mg in 1 2; do
  python3 pc20_timing.py "$EXE" OG200.fens "wtime 1000 btime 1000 movestogo $mg" "raw/mtg${mg}.jsonl" "pc20_mtg${mg}" \
    && date -u >> stamps.txt
done
echo DONE_PC20 >> stamps.txt
