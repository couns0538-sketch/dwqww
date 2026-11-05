#!/usr/bin/env bash
# stub run: exits 78 on its first call, 0 afterwards (owner fix list item 1 verify)
c=/d/o30/tmp/runner_fix1_test/calls.txt; n=$(cat $c 2>/dev/null || echo 0); n=$((n+1)); echo $n > $c
echo "stub run $1 call $n: plan.done now: [$(cat /d/o30/tmp/runner_fix1_test/plan.done 2>/dev/null | tr "\n" " ")]"
[ $n = 1 ] && exit 78; exit 0
