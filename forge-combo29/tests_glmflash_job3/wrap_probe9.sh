#!/bin/sh
exec tee -a /tmp/glmflash/probe9_uci_in.log | exec /tmp/forge_engine/build/forge
