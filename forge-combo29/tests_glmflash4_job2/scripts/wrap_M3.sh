#!/bin/sh
# wrap_M3.sh: the undeclared options first, then fastchess's own input, to the unchanged exe
{ printf 'setoption name ContHist4Pct value 45\n'; cat; } | /tmp/build_bnd68_noexpose/forge
