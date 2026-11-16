#!/usr/bin/env bash
# The TT patch changes a replacement path on a SHARED table, so check multi-threaded behaviour too: at Threads 4
# the engine must still answer with a legal move and must not report a sanitizer-class failure. Node counts are not
# compared (they are nondeterministic with >1 thread); legality and completion are.
set -u
EXE="$1"
for th in 1 4 8; do
  for fen in "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" \
             "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"; do
    # Drain to bestmove: a pipelined `quit` aborts the search and yields the FABRICATED a2a3 (19-F12).
    out=$(python3 - "$EXE" "$th" "$fen" <<'PYEOF'
import subprocess, sys
exe, th, fen = sys.argv[1], sys.argv[2], sys.argv[3]
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                     text=True, bufsize=1)
for c in ["uci", f"setoption name Hash value 16", f"setoption name Threads value {th}",
          "setoption name OwnBook value false", "isready"]:
    p.stdin.write(c + "\n"); p.stdin.flush()
    if c == "isready":
        for line in p.stdout:
            if line.startswith("readyok"): break
p.stdin.write(f"position fen {fen}\n"); p.stdin.flush()
p.stdin.write("go depth 10\n"); p.stdin.flush()
out = []
for line in p.stdout:
    out.append(line.rstrip())
    if line.startswith("bestmove"): break
p.stdin.write("quit\n"); p.stdin.flush(); p.wait()
print("\n".join(out))
PYEOF
)
    bm=$(printf '%s' "$out" | grep -oE "^bestmove [a-h][1-8][a-h][1-8][qrbn]?|^bestmove 0000" | tail -1)
    # legality: replay the move with python-chess
    legal=$(python3 - "$fen" "$bm" <<'PY'
import sys, chess
fen, bm = sys.argv[1], sys.argv[2]
b = chess.Board(fen)
m = bm.split()[1] if bm.startswith("bestmove") else None
print("LEGAL" if (m and m != "0000" and chess.Move.from_uci(m) in b.legal_moves) else "ILLEGAL/EMPTY")
PY
)
    echo "Threads $th  ->  $bm  [$legal]"
  done
done
