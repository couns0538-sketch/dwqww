#!/usr/bin/env python3
"""selfplay60.py -- 40 games of the plain build against itself at `go nodes 20000` under ASan,
driven move by move by python-chess from the first 40 positions of O (one game per position).
Fresh process per GAME (not per move). Ends by python-chess's rules or at 300 plies."""
import chess
import subprocess
import sys
import threading
import queue
import time

exe = sys.argv[1]
outdir = sys.argv[2]
S14 = open("/tmp/ds6_work/forge-combo29/tests_deepseek6_long1/s14.txt").read().strip()
fens = [l.strip() for l in open("/tmp/o40_plant.fens") if l.strip()]

def game(gi, fen):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    out = []
    err = []
    def rdo():
        try:
            for l in p.stdout:
                out.append(l)
        except Exception:
            pass
    def rde():
        try:
            for l in p.stderr:
                err.append(l)
        except Exception:
            pass
    threading.Thread(target=rdo, daemon=True).start()
    threading.Thread(target=rde, daemon=True).start()
    def send(s):
        try:
            p.stdin.write(s + "\n"); p.stdin.flush()
        except Exception:
            pass
    send("uci")
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    send("setoption name OwnBook value false")
    for o in S14.split(";"):
        if o.strip():
            send(f"setoption name {o.replace('=', ' value ')}")
    send("isready")
    t0 = time.monotonic()
    while time.monotonic() - t0 < 30:
        if any("readyok" in x for x in out[-5:]):
            break
        time.sleep(0.05)
    b = chess.Board(fen)
    movelist = []
    reason = None
    while len(movelist) < 300:
        if b.is_checkmate():
            reason = "checkmate"
            break
        if b.is_stalemate():
            reason = "stalemate"
            break
        if b.can_claim_threefold_repetition() or b.is_repetition(3):
            reason = "threefold"
            break
        if b.halfmove_clock >= 100:
            reason = "fifty moves"
            break
        if b.is_insufficient_material():
            reason = "insufficient material"
            break
        send(f"position fen {b.fen()}")
        send("go nodes 20000")
        best = None
        t0 = time.monotonic()
        last_n = len(out)
        while time.monotonic() - t0 < 180:
            new_lines = out[last_n:]
            last_n = len(out)
            for l in new_lines:
                if l.startswith("bestmove "):
                    best = l.split()[1]
                    break
            if best is not None:
                break
            time.sleep(0.01)
        if best is None:
            reason = "NO BESTMOVE"
            break
        if best == "0000":
            reason = "engine says 0000"
            break
        try:
            mv = chess.Move.from_uci(best)
        except Exception:
            reason = f"UNPARSEABLE MOVE {best}"
            break
        if mv not in b.legal_moves:
            reason = f"ILLEGAL MOVE {best}"
            break
        b.push(mv)
        movelist.append(best)
    san = [l for l in err if "AddressSanitizer" in l or "runtime error" in l or "LeakSanitizer" in l or "SUMMARY" in l]
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    res = {"game": gi, "start_fen": fen, "plies": len(movelist), "reason": reason,
           "final_fen": b.fen(), "result": b.result() if reason not in (None, "NO BESTMOVE", "ILLEGAL MOVE") else "-",
           "san_lines": len(san), "exit": p.returncode}
    if san:
        res["san_first"] = san[0][:100]
    open(f"{outdir}/game_{gi}.txt", "w").write(
        f"start {fen}\nmoves {' '.join(movelist)}\nreason {reason}\nplies {len(movelist)}\n"
        f"result {res['result']}\nsan_lines {len(san)}\nexit {p.returncode}\nfinal {b.fen()}\n")
    return res

import os
os.makedirs(outdir, exist_ok=True)
import concurrent.futures
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    for r in ex.map(game, range(len(fens)), fens):
        results.append(r)
        print(f"game {r['game']}: plies {r['plies']}, reason {r['reason']}, san {r['san_lines']}, exit {r['exit']}")
crashes = sum(1 for r in results if r["exit"] not in (0, -15, 15))
san_tot = sum(r["san_lines"] for r in results)
illegal = sum(1 for r in results if r["reason"] and "ILLEGAL" in r["reason"])
reasons = {}
for r in results:
    reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
print(f"games {len(results)}; crashes {crashes}; sanitizer lines {san_tot}; illegal {illegal}")
print("reasons:", reasons)
open(f"{outdir}/summary.txt", "w").write(
    f"games {len(results)} crashes {crashes} san_lines {san_tot} illegal {illegal}\nreasons {reasons}\n")
