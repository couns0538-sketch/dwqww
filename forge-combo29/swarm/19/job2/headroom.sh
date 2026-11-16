#!/usr/bin/env bash
# headroom.sh TAG : builds one variant of the source in ~/h/<TAG> and times 15 runs of `bench 13`.
# $1 tag, $2 python edit script (may be empty for base). Prints the per-run times and the median.
set -u
TAG="${1:?tag}"
H="${2:-}"
SRC=~/base/forge-combo29
DST=~/h/$TAG/src
BD=~/h/$TAG/build
rm -rf ~/h/$TAG && mkdir -p ~/h/$TAG
cp -a "$SRC" "$DST"
if [ -n "$H" ]; then (cd "$DST" && python3 "$H") || { echo "EDIT FAILED"; exit 2; }; fi
cmake -S "$DST" -B "$BD" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ > /dev/null 2>&1 || { echo "CMAKE FAILED"; exit 2; }
make -C "$BD" -j4 > "$BD/build.log" 2>&1 || { echo "BUILD FAILED"; tail -5 "$BD/build.log"; exit 2; }
{
  for i in $(seq 1 15); do echo "bench 13"; done; echo quit
} > ~/h/$TAG/stdin.txt
"$BD/forge" < ~/h/$TAG/stdin.txt > ~/h/$TAG/out.txt 2>&1
grep -E '^info string bench depth 13' ~/h/$TAG/out.txt | sed 's/.*nodes \([0-9]*\) time \([0-9]*\) nps \([0-9]*\)/\1 \2 \3/' > ~/h/$TAG/times.txt
echo "=== $TAG"
awk '{print $1}' ~/h/$TAG/times.txt | sort -u | sed 's/^/nodes: /'
sort -n -k2 ~/h/$TAG/times.txt | awk '{t[NR]=$2} END {m=t[int((NR+1)/2)]; printf "median ms %d  min %d  max %d  n %d\n", m, t[1], t[NR], NR}'
awk '{s+=$2; n++} END {printf "mean ms %.1f over %d runs\n", s/n, n}' ~/h/$TAG/times.txt
