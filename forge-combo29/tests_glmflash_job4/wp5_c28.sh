#!/bin/sh
{ printf 'setoption name AspFailHighReduce value 1\nsetoption name AspFailHighMaxReduce value 3\nsetoption name EvalSwingMult value 24\nsetoption name EvalSwingMax value 200\nsetoption name TtCutoffHistory value 1\n'; cat; } | tee -a /tmp/glmflash/probe_5_uci_in.log | /tmp/forge_packc28/build/forge
