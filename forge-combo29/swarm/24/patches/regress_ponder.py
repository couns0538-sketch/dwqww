#!/usr/bin/env python3
"""Regression test for seat 24's two-hang patch: the PONDER path on a NORMAL board must still work end to end.

The patch skips `stop_cv.wait` when the root has no legal move. On a normal board that condition is false, so the
ponder path must be unchanged:
  * `go ponder <clock>` must NOT print a bestmove before `ponderhit`;
  * `ponderhit` must make it finish within a few seconds;
  * the bestmove must be legal.
Run against the unpatched PC build and the patched one and compare.
"""
import argparse
import queue
import subprocess
import sys
import threading
import time

import chess

OPEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def probe(exe, label, pre_wait=1.0, post_wait=5.0):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0)
    q = queue.Queue()

    def rd():
        for l in p.stdout:
            q.put(l.decode("utf-8", "replace").rstrip())
        q.put(None)

    threading.Thread(target=rd, daemon=True).start()

    def send(s):
        p.stdin.write((s + "\n").encode()); p.stdin.flush()

    def drain(to):
        out = []; t0 = time.monotonic()
        while time.monotonic() - t0 < to:
            try:
                l = q.get(timeout=max(0.01, to - (time.monotonic() - t0)))
            except queue.Empty:
                break
            if l is None:
                break
            out.append(l)
        return out

    send("uci"); drain(1.0)
    send("setoption name OwnBook value false"); send("isready"); drain(1.0)
    send("position fen " + OPEN); send("isready"); drain(1.0)
    send("go ponder wtime 3000 btime 3000")
    pre = drain(pre_wait)
    early = [l for l in pre if l.startswith("bestmove")]
    send("ponderhit")
    post = drain(post_wait)
    bm = [l for l in post if l.startswith("bestmove")]
    board = chess.Board(OPEN)
    legal = "n/a"
    if bm:
        mv = bm[0].split()[1]
        legal = "legal" if (mv != "0000" and chess.Move.from_uci(mv) in board.legal_moves) else "ILLEGAL"
    try:
        send("quit"); p.wait(10)
    except Exception:
        p.kill()
    return {"label": label, "early": bool(early), "bm": bm[0][:30] if bm else "MISSING",
            "legal": legal, "ninfo": len([l for l in pre + post if l.startswith("info")])}


ap = argparse.ArgumentParser()
ap.add_argument("--unpatched", required=True)
ap.add_argument("--patched", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()

rows = [probe(a.unpatched, "PC unpatched"), probe(a.patched, "PC + patch")]
with open(a.out, "w") as f:
    def w(s):
        print(s); f.write(s + "\n")
    w("| build | bestmove before ponderhit | bestmove after ponderhit | legal | info lines |")
    w("|---|---|---|---|---|")
    for r in rows:
        w(f"| {r['label']} | {'YES (BUG)' if r['early'] else 'no (correct)'} | {r['bm']} | {r['legal']} | {r['ninfo']} |")
    w("")
    ok = (not rows[0]["early"]) and (not rows[1]["early"]) and rows[1]["bm"] != "MISSING" and rows[1]["legal"] == "legal"
    w("VERDICT: " + ("PASS - the patch leaves the ponder path unchanged on a normal board" if ok
                     else "FAIL - the patch changed the ponder path"))
sys.exit(0 if ok else 2)
