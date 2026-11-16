#!/usr/bin/env bash
# honesty.sh EXE OUTDIR : four honesty numbers, one fresh process per line, raw output saved
set -u
EXE="$1"; OUT="$2"; mkdir -p "$OUT"
echo "uci" | "$EXE" > "$OUT/uci.txt" 2>&1
{
 echo "exe: $EXE"
 echo "sha256: $(sha256sum "$EXE" | awk '{print $1}')"
 echo "id name: $(grep -m1 '^id name' "$OUT/uci.txt")"
 echo "options sent: none (bench/perft need none)"
 echo "host: $(uname -srm)"
 echo "cores: $(nproc)"
 echo "gcc: $(g++ --version | head -1)"
} > "$OUT/honesty.meta"
for d in 11 13 16; do
  { echo "bench $d"; echo "quit"; } | timeout 600 "$EXE" > "$OUT/bench$d.txt" 2>&1
  echo "bench$d exit=$? nodes=$(grep -o 'nodes [0-9]*' "$OUT/bench$d.txt" | tail -1)"
done
{ echo "position startpos"; echo "go perft 5"; echo "quit"; } | timeout 600 "$EXE" > "$OUT/perft5.txt" 2>&1
echo "perft5 exit=$? nodes=$(grep -o 'Nodes searched: [0-9]*' "$OUT/perft5.txt" | tail -1)"
