#!/bin/sh
# wrap_bnd68.sh: bnd68's six undeclared options first, then fastchess's own input, to the unchanged exe
{ printf 'setoption name NonPawnCorr value 1\nsetoption name PawnHist value 1\nsetoption name NonPawnCorrWeight value 50\nsetoption name ContHist4Pct value 45\nsetoption name EvalOnlyStore value 1\nsetoption name EvalOnlyStoreMinDepth value 2\n'; cat; } | /tmp/forge_bnd68/build/forge
