#!/usr/bin/env bash
# O1 self-play robustness run: Forge vs Forge at Threads 4 with fastchess (built from the commit in
# tools/match/fastchess-provenance.json), fast TC, PGN in UCI notation, then the independent
# python-chess legality check (pgn_legality.py).
# usage: selfplay.sh <forge_exe> <games> <out_dir> <fastchess_srand> [engine-A-only args, e.g. option.SmpBestThread=true]
# The srand values used by CI are robustness-run seeds, not gate seeds (gate seeds are QA's).
set -euo pipefail
FORGE=$1; GAMES=$2; OUT=$3; SEED=$4; shift 4
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
mkdir -p "$OUT"
FC=${FASTCHESS:-}
if [ -z "$FC" ]; then
  git clone -q https://github.com/Disservin/fastchess "$OUT/fastchess-src"
  git -C "$OUT/fastchess-src" checkout -q 60d7a7a26c6b0582a15c112fb29a1829bef2adb3
  make -C "$OUT/fastchess-src" -j"$(nproc)" > "$OUT/fastchess_build.log" 2>&1
  FC="$OUT/fastchess-src/fastchess"
fi
"$FC" -version | tee "$OUT/fastchess_version.txt"
set -x
"$FC" -engine cmd="$FORGE" name=A "$@" -engine cmd="$FORGE" name=B \
  -each proto=uci tc=1+0.01 timemargin=1000 option.Threads=4 option.Hash=16 option.OwnBook=false \
  -openings file="$ROOT/tools/openings/forge-10000.epd" format=epd order=random -srand "$SEED" \
  -rounds $((GAMES / 2)) -games 2 -repeat -concurrency 1 -recover \
  -pgnout file="$OUT/games.pgn" notation=uci nodes=true timeleft=true \
  -log file="$OUT/fastchess.log" level=warn > "$OUT/fastchess_stdout.log" 2>&1
set +x
tail -n 15 "$OUT/fastchess_stdout.log"
python3 "$ROOT/opus_round1/O1/pgn_legality.py" "$OUT/games.pgn" | tee "$OUT/pgn_legality.log"
