#!/bin/sh
{ printf 'setoption name AspFailHighReduce value 1\nsetoption name AspFailHighMaxReduce value 3\n'; cat; } | tee -a /tmp/glmflash/probe_asp_uci_in.log | /tmp/forge_packc28/build/forge
