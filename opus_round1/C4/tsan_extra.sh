#!/usr/bin/env bash
# C4 TSan hook (run by opus_round1/ci/run_ci.sh tsan): searches with a v2 net (shared read-only weights,
# per-worker refresh caches) at Threads 4 and 2, short fixed depths, each run under its own timeout.
# The v2 net is a replica of the compiled-in net with 8 mirrored king buckets (tools/nnue/forge_nnue_v2.py),
# so it exercises bucket-change refreshes; run_ci.sh fails the job on any TSan report file.
# usage: tsan_extra.sh <forge_exe> <out_dir>
set -uo pipefail
EXE=$1
OUT=$2
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
mkdir -p "$OUT"
NET="$OUT/c4_tsan_rm8.fnn2"
python3 "$ROOT/tools/nnue/forge_nnue_v2.py" from-inc "$ROOT/src/nnue_weights.inc" "$NET" --replica rm8 || exit 1
# A Windows engine (local dry runs under MSYS) needs a Windows path.
NET_ARG=$(cygpath -w "$NET" 2>/dev/null || echo "$NET")
status=0
run() { # name threads depth fen
  local name=$1 threads=$2 depth=$3 fen=$4
  echo "== C4 tsan: $name (Threads $threads, depth $depth)"
  timeout --kill-after=10 300 python3 "$ROOT/opus_round1/C4/uci_go.py" "$EXE" "$threads" "$depth" "$fen" \
    --set "NNUEFile=$NET_ARG" --set NNUEKingBuckets=8 --timeout 280 || { echo "   FAIL: $name"; status=1; }
}
run kings_endgame 4 15 "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"
run middlegame 4 10 "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
run back_rank 2 14 "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1"
echo "C4 tsan_extra status=$status"
exit $status
