#!/usr/bin/env bash
# waitloop.sh -- one wait-loop cycle: sleep ~20 min, look for the next deepseek6 job file,
# fetch my branch tip (the peer instance pushes there too), print a short status.
set -u
sleep 1140
cd /tmp/ds6_work
git fetch -q --depth 1 origin handoff/fable-opus-combo29-all-20261114
git fetch -q --depth 1 origin for-fable-and-opus/deepseek6-work 2>/dev/null
echo "== $(date -u +%FT%TZ)"
echo "job files:"; git ls-tree --name-only FETCH_HEAD:forge-combo29/soak_all/ 2>/dev/null | grep "FABLE_TO_deepseek6_" | tail -3
echo "my branch remote tip:"; git log --oneline -1 origin/for-fable-and-opus/deepseek6-work 2>/dev/null || git log --oneline -1 FETCH_HEAD
