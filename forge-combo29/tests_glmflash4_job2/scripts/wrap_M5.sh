#!/bin/sh
# wrap_M5.sh: the undeclared options first, then fastchess's own input, to the unchanged exe
{ printf 'setoption name PawnHist value 1\nsetoption name ContHist4Pct value 45\nsetoption name EvalOnlyStore value 1\nsetoption name EvalOnlyStoreMinDepth value 2\n'; cat; } | /tmp/build_bnd68_noexpose/forge
