#!/bin/sh
# wrap_packa.sh: packa's three undeclared options first, then fastchess's own input, to the unchanged exe
{ printf 'setoption name NonPawnCorr value 1\nsetoption name PawnHist value 1\nsetoption name NonPawnCorrWeight value 50\n'; cat; } | /tmp/forge_packa/build/forge
