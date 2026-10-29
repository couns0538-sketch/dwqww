#!/usr/bin/env bash
# FB1 TSan hook (run by opus_round1/ci/run_ci.sh tsan): searches with a v3 net (NNUEArch on: shared read-only
# weights, per-worker accumulator stacks and refresh caches) at Threads 4 and 2 to short fixed depths, and runs
# `bench 10` with the net at Threads 1; run_ci.sh fails the job on any TSan report file.
# The net is a random H64 / 8 mirrored king buckets / 8 output buckets net written by forge_nnue_v3_tool (built
# next to the engine; no Python packages needed), so king-bucket refreshes and every output head are exercised.
# usage: tsan_extra.sh <forge_exe> <out_dir>
set -uo pipefail
EXE=$1
OUT=$2
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
mkdir -p "$OUT"
NET="$OUT/fb1_tsan_h64.fnn3"
TOOL="$(dirname "$EXE")/forge_nnue_v3_tool"
[ -x "$TOOL" ] || TOOL="$TOOL.exe"
"$TOOL" random "$NET" 64 8 8 1 11 || exit 1
# A Windows engine (local dry runs under MSYS) needs a Windows path.
NET_ARG=$(cygpath -w "$NET" 2>/dev/null || echo "$NET")
status=0
run() { # name threads depth fen
  local name=$1 threads=$2 depth=$3 fen=$4
  echo "== FB1 tsan: $name (Threads $threads, depth $depth, NNUEArch on)"
  timeout --kill-after=10 300 ${PYTHON:-python3} "$ROOT/tools/nnue/fable_nnue_uci.py" "$EXE" --threads "$threads" --hash 16 \
    --net "$NET_ARG" --arch true --fen "$fen" --go-depth "$depth" --expect-exit 0 --timeout 280 \
    | grep -E "BESTMOVE|EXIT|FAIL|ERROR|active" || { echo "   FAIL: $name"; status=1; }
}
run kings_endgame 4 13 "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"
run middlegame 4 9 "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
run back_rank 2 12 "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1"
# FB2-J5 SmpV2: helpers one ply ahead / wider aspiration, deepest helper result selected after the join.
run_smp() { # name threads depth fen
  local name=$1 threads=$2 depth=$3 fen=$4
  echo "== FB2-J5 tsan: $name (Threads $threads, depth $depth, SmpV2 on, NNUEArch on)"
  timeout --kill-after=10 300 ${PYTHON:-python3} "$ROOT/tools/nnue/fable_nnue_uci.py" "$EXE" --threads "$threads" --hash 16 \
    --setoption SmpV2=true --net "$NET_ARG" --arch true --fen "$fen" --go-depth "$depth" --expect-exit 0 --timeout 280 \
    | grep -E "BESTMOVE|EXIT|FAIL|ERROR|active" || { echo "   FAIL: $name"; status=1; }
}
run_smp smp_middlegame 3 10 "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
run_smp smp_endgame 4 12 "2r3k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1"
run_smp smp_open 2 11 "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
echo "== FB1 tsan: bench 10 with the net at Threads 1"
timeout --kill-after=10 300 ${PYTHON:-python3} "$ROOT/tools/nnue/fable_nnue_uci.py" "$EXE" --threads 1 --hash 16 \
  --net "$NET_ARG" --arch true --bench 10 --expect-exit 0 --timeout 280 | grep -E "BENCH|EXIT|FAIL|ERROR" || { echo "   FAIL: bench"; status=1; }
echo "FB1 tsan_extra status=$status"
exit $status
