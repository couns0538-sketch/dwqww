#!/usr/bin/env bash
# f1_history_carryover.sh <exe> <outdir>
# Area 7 job 2: do the move-picker histories leak between searches inside one process?
# The histories live on Worker and are cleared only by Worker::clear() -- ucinewgame / Clear Hash /
# a Threads change (uci.cpp:255-257, search.cpp:1019-1030). A `position` command does not clear them.
# Driven by paced_session.py, which waits for bestmove after every `go`: writing a whole session at
# once makes each following command ABORT the running search (documented trap, see REPORT_job1.md).
set -u
EXE=$(readlink -f "${1:?exe}")
OUT="${2:?outdir}"
SESS="$OUT/sessions"
mkdir -p "$SESS"

S14='setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true'

A="r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
B="r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
C="8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"

preamble() {
  printf 'uci\nisready\nsetoption name Hash value 16\nsetoption name Threads value %s\n%s\nisready\nucinewgame\nisready\n' "$1" "$S14"
}

{ preamble 1; printf 'position fen %s\nisready\ngo depth 12\n' "$B"; } > "$SESS/B_alone.uci"
{ preamble 1; printf 'position fen %s\nisready\ngo depth 12\n' "$A"
  printf 'position fen %s\nisready\ngo depth 12\n' "$B"; } > "$SESS/A_then_B.uci"
{ preamble 1; printf 'position fen %s\nisready\ngo depth 12\n' "$A"
  printf 'ucinewgame\nisready\nposition fen %s\nisready\ngo depth 12\n' "$B"; } > "$SESS/A_ucinew_B.uci"
{ preamble 1; printf 'position fen %s\nisready\ngo depth 12\n' "$A"
  printf 'position fen %s\nisready\ngo depth 12\n' "$C"
  printf 'position fen %s\nisready\ngo depth 12\n' "$B"; } > "$SESS/A_C_B.uci"
{ preamble 1; printf 'position fen %s\nisready\ngo depth 12\n' "$B"
  printf 'ucinewgame\nisready\nposition fen %s\nisready\ngo depth 12\n' "$B"; } > "$SESS/B_twice.uci"
{ preamble 2; printf 'position fen %s\nisready\ngo depth 12\n' "$B"; } > "$SESS/B_threads2.uci"
{ preamble 1; printf 'position fen %s\nisready\ngo depth 12\n' "$B"
  printf 'setoption name Clear Hash\nisready\nposition fen %s\nisready\ngo depth 12\n' "$B"; } > "$SESS/B_clearhash.uci"

for s in "$SESS"/*.uci; do
  name=$(basename "$s" .uci)
  echo "== $name"
  python3 "$(dirname "$0")/paced_session.py" "$EXE" "$s" "$OUT/$name" 300 > "$OUT/$name.meta.json" 2>&1
done

# one table row per `go`, read from the raw output
echo
echo "| case | # | bestmove | nodes | score |"
echo "|---|---|---|---|---|"
for f in "$OUT"/*.out.txt; do
  name=$(basename "$f" .out.txt)
  python3 - "$f" "$name" <<'PY'
import re, sys
txt = open(sys.argv[1], errors="replace").read()
name = sys.argv[2]
chunks = re.split(r"^bestmove (\S+)", txt, flags=re.M)
i = 0
for k in range(0, len(chunks) - 1, 2):
    body, bm = chunks[k], chunks[k + 1]
    infos = [l for l in body.splitlines() if l.startswith("info depth")]
    last = infos[-1] if infos else ""
    nodes = re.search(r"nodes (\d+)", last)
    score = re.search(r"score (cp|mate) (-?\d+)", last)
    i += 1
    print("| %s | %d | %s | %s | %s |" % (name, i, bm,
          nodes.group(1) if nodes else "none",
          (score.group(1) + " " + score.group(2)) if score else "none"))
PY
done
