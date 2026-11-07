#!/usr/bin/env bash
# t1_run.sh <book_key> <rounds> <out_tag> - OSS scout trial T1 (book resolution): one fastchess match of the lock exe
# at 20000 nodes per move vs the same exe at 10000 nodes per move on one book. Fixed nodes, Threads 1: results do not
# depend on CPU load. Runs at the session's Idle priority on CPUs 2-3 (inherited). Refuses to overwrite an output dir.
# book_key: uho | 8moves
set -euo pipefail
book=${1:?book key uho|8moves}
rounds=${2:?rounds}
tag=${3:?out tag}
SC=C:/opus_5h/oss_scout
FC=$SC/dl/fastchess-1.8.2-alpha/x/fastchess-windows-x86-64/fastchess.exe
EXE=$SC/build/lock/forge_trial_w6.exe
case $book in
  uho)    open="file=$SC/data/books/UHO_Lichess_4852_v1.epd format=epd order=random" ;;
  8moves) open="file=$SC/data/books/8moves_v3.pgn format=pgn order=random" ;;
  *) echo "unknown book $book"; exit 2 ;;
esac
OUT=$SC/build/t1_books/$tag
if [ -e "$OUT" ]; then echo "refusing: $OUT exists"; exit 2; fi
mkdir -p "$OUT"
echo "start $(date '+%Y-%m-%d %H:%M:%S') book=$book rounds=$rounds" > "$OUT/run_info.txt"
# shellcheck disable=SC2086
"$FC" \
  -engine cmd=$EXE name=n20k nodes=20000 \
  -engine cmd=$EXE name=n10k nodes=10000 \
  -each proto=uci option.OwnBook=false option.Hash=16 option.Threads=1 \
  -openings $open \
  -srand 20261106 -games 2 -repeat -rounds "$rounds" -concurrency 2 \
  -ratinginterval 50 -report penta=true -recover \
  -event oss_scout_t1_$tag \
  -pgnout file=$OUT/games.pgn \
  -log file=$OUT/fastchess.log level=warn engine=false \
  > "$OUT/stdout.txt" 2>&1
rc=$?
echo "end $(date '+%Y-%m-%d %H:%M:%S') rc=$rc" >> "$OUT/run_info.txt"
exit $rc
