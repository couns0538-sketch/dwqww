#!/bin/sh
{ printf 'setoption name EvalSwingMult value 24\nsetoption name EvalSwingMax value 200\n'; cat; } | tee -a /tmp/glmflash/probe_swing_uci_in.log | /tmp/forge_packc28/build/forge
