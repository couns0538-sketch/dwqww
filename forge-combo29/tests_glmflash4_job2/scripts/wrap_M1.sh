#!/bin/sh
# wrap_M1.sh: the undeclared options first, then fastchess's own input, to the unchanged exe
{ printf 'setoption name NonPawnCorr value 1\nsetoption name NonPawnCorrWeight value 50\n'; cat; } | /tmp/build_bnd68_noexpose/forge
