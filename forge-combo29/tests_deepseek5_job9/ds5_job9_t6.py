#!/usr/bin/env python3
"""job9 Part B: T6 - setoption Hash DURING a running search (no stop first); + the ASan T5 block."""
import sys, time, json, random
sys.path.insert(0, "/tmp/glmflash")
import ds5_job8_storms as H
import chess

import ds5_job8_storms as _H8
_H8.ENGINE = sys.argv[1]
ENGINE = sys.argv[1]
tag = sys.argv[2]
fens = [l.strip() for l in open(H.EPD, encoding="utf-8", errors="replace")]
rng = random.Random(7356)
e = H.Eng(threads=4, tag=tag, block="T6")
best_counts = []; readyok = 0; missing = 0; doubles = 0; illegal = 0; lat = []
for i in range(100):
    fen = fens[rng.randrange(len(fens))]
    e.send("ucinewgame"); e.send("isready")
    try:
        e.expect("readyok", 120)
    except Exception:
        missing += 1; continue
    e.send(f"position fen {fen}")
    e.send("go infinite")
    time.sleep(rng.uniform(1, 300) / 1000.0)
    e.send(f"setoption name Hash value {16 if i % 2 == 0 else 32}")
    n_best = 0
    try:
        t0 = time.monotonic_ns()
        line = e.expect("bestmove", 120)
        lat.append((time.monotonic_ns() - t0) / 1e6)
        n_best += 1
        best = line.split()[1]
        board = chess.Board(); board.set_fen(fen)
        try:
            if chess.Move.from_uci(best) not in board.legal_moves:
                illegal += 1
        except Exception:
            illegal += 1
        n_best += sum(1 for x in e.drain(0.5) if x.startswith("bestmove"))
    except Exception:
        missing += 1
    e.send("isready")
    try:
        e.expect("readyok", 60); readyok += 1
    except Exception:
        pass
    best_counts.append(n_best)
    doubles += max(0, n_best - 1)
try:
    e.send("quit")
except Exception:
    pass
e.p.wait(timeout=60)
import os
err = e.p.stderr.read() if e.p.stderr else ""
open(f"{H.FOLDER}/{tag}_T6.stderr.txt", "w").write(err)
n, first, files = H.warnings_in(tag, "T6")
vals = sorted(lat)
res = {"tag": tag, "block": "T6", "storms": len(best_counts), "missing": missing,
       "doubles": doubles, "illegal": illegal,
       "one_bestmove_storms": sum(1 for c in best_counts if c == 1),
       "zero_bestmove_storms": sum(1 for c in best_counts if c == 0),
       "readyok_seen": readyok, "median_ms": vals[len(vals)//2] if vals else None,
       "max_ms": vals[-1] if vals else None,
       "exit_code": e.p.returncode, "report_files": files, "warnings": n,
       "first_report": first, "stderr_bytes": len(err.encode())}
json.dump(res, open(f"{H.FOLDER}/{tag}_T6.json", "w"), indent=1)
print(json.dumps(res), flush=True)
