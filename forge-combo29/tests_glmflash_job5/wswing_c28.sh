#!/bin/sh
{ printf 'setoption name EvalSwingMult value 24\nsetoption name EvalSwingMax value 200\n'; cat; } | /tmp/forge_packc28/build/forge
