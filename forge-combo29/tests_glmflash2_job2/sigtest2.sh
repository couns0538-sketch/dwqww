#!/bin/bash
# SIGINT graceful-stop test 2: 200-game match, SIGINT after 12 s.
cd /tmp/fc
rm -f sigtest2.pgn sigtest2_out.txt
/tmp/fastchess/fastchess \
  -engine cmd=/tmp/forgebuild/forge name=cand option.Threads=1 option.Hash=16 option.LmrDeeperShallower=true \
  -engine cmd=/tmp/forgebuild/forge name=base option.Threads=1 option.Hash=16 \
  -each proto=uci nodes=20000 \
  -openings file=/tmp/UHO_Lichess_4852_v1.epd format=epd order=random \
  -srand 99 -rounds 100 -games 2 -repeat -concurrency 4 -recover -ratinginterval 100 \
  -pgnout file=/tmp/fc/sigtest2.pgn min=true > /tmp/fc/sigtest2_out.txt 2>&1 &
FCPID=$!
echo "FCPID $FCPID"
sleep 12
if kill -0 $FCPID 2>/dev/null; then
  echo SENDING_SIGINT
  kill -INT $FCPID
else
  echo ALREADY_EXITED
fi
sleep 10
if kill -0 $FCPID 2>/dev/null; then
  echo STILL_RUNNING_10S_AFTER_SIGINT
  kill -9 $FCPID
else
  echo EXITED_AFTER_SIGINT
fi
echo "--- tail of output:"
tail -n 10 /tmp/fc/sigtest2_out.txt
echo "--- PGN event lines: $(grep -c '\[Event' /tmp/fc/sigtest2.pgn 2>/dev/null)"
