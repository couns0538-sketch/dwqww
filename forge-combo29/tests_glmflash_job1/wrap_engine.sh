#!/bin/bash
# Control 3 evidence wrapper: records every UCI line fastchess sends to the
# candidate engine (which is the same forge exe underneath), then execs it.
exec tee -a /tmp/glmflash/ctrl3_cand_uci_in.log | exec /tmp/forge_engine/build/forge
