#!/bin/sh
# wrap_M2.sh: the undeclared options first, then fastchess's own input, to the unchanged exe
{ printf 'setoption name PawnHist value 1\n'; cat; } | /tmp/build_bnd68_noexpose/forge
