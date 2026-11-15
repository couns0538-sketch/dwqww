#!/bin/sh
# wrap_M6.sh: the undeclared options first, then fastchess's own input, to the unchanged exe
{ printf 'setoption name AspFailHighReduce value 1\nsetoption name AspFailHighMaxReduce value 3\n'; cat; } | /tmp/build_packc28_noexpose/forge
