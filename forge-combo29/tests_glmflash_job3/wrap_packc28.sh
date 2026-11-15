#!/bin/sh
# wrap_packc28.sh: packc28's four undeclared options first, then fastchess's own input, to the unchanged exe
{ printf 'setoption name AspFailHighReduce value 1\nsetoption name AspFailHighMaxReduce value 3\nsetoption name EvalSwingMult value 24\nsetoption name EvalSwingMax value 200\n'; cat; } | /tmp/forge_packc28/build/forge
