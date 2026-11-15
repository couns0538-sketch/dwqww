#!/bin/bash
# M3 evidence wrapper: records every UCI line fastchess sends to the candidate
# engine (which is the same B1 forge exe underneath), then execs it.
exec tee -a /tmp/glmflash/m3_cand_uci_in.log | exec /tmp/forge_engine/build/forge
