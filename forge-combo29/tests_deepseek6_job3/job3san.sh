#!/usr/bin/env bash
# job3san.sh -- the sanitizer half of job 3: FailHighBlend values 0,1,2,4,7 at depth 10 on O and G.
set -u
D=/agent/repos/base/forge-combo29/tests_deepseek6_job3
S14=$(cat /agent/repos/base/forge-combo29/tests_deepseek6_job1/s14.txt)
EXE=/agent/repos/work/build-j3san/forge
mkdir -p "$D/runs_san"
for v in 0 1 2 4 7; do
  for setname in O G; do
    if [ "$setname" = O ]; then sf=$D/first200.fens; else sf=$D/set_G.epd; fi
    tag="fhb${v}_${setname}"
    if [ -s "$D/runs_san/$tag.rows" ]; then echo "skip $tag"; continue; fi
    echo "--- $tag $(date -u) ---"
    python3 $D/sanrun.py --exe "$EXE" --set "$sf" --out "$D/runs_san/$tag.rows" --opts "$S14;FailHighBlend=$v" --depth 10
    python3 $D/sancount.py "$D/runs_san/$tag.rows"
  done
done
echo "JOB3SAN DONE $(date -u)"
