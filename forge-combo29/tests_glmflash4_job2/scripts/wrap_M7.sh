#!/bin/sh
# wrap_M7.sh: the undeclared options first, then fastchess's own input, to the unchanged exe
{ printf 'setoption name EvalSwingMult value 24\nsetoption name EvalSwingMax value 200\n'; cat; } | /tmp/build_packc28_noexpose/forge
