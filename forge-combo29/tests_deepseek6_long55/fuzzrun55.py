#!/usr/bin/env python3
"""fuzzrun55.py -- run the 20,000 mutated FENs under a sanitizer build.
One process per 500 FENs (a crash restarts the process and is counted). Per FEN:
`position fen <it>` + `isready` (record the answer lines; stop-markers recorded) + `go depth 2`
+ bestmove. Classes: refused / accepted+pc-valid / accepted+pc-INVALID / crashes / sanitizer
lines / illegal bestmoves (for accepted pc-valid FENs)."""
import chess
import json
import subprocess
import sys
import threading
import queue

exe = sys.argv[1]
outdir = sys.argv[2]
rows = [l.rstrip("\n") for l in open("/tmp/fuzz55.fens") if l.strip()]
BATCH = 500
cls = {"refused": 0, "accepted_valid": 0, "accepted_invalid": 0, "crashes": 0,
       "san_lines": 0, "illegal_bestmoves": 0}
special = []   # accepted + python-chess INVALID rows
crash_rows = []
san_rows = []
illegal_rows = []
idx = 0
restarts = 0
while idx < len(rows):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    q = queue.Queue()
    err = []
    def rd():
        try:
            for l in p.stdout:
                q.put(l)
        except Exception:
            pass
        q.put(None)
    def rde():
        try:
            for l in p.stderr:
                err.append(l)
        except Exception:
            pass
    threading.Thread(target=rd, daemon=True).start()
    threading.Thread(target=rde, daemon=True).start()
    def send(s):
        try:
            p.stdin.write(s + "\n"); p.stdin.flush()
        except Exception:
            pass
    def rl(tmo=5.0):
        try:
            return q.get(timeout=tmo)
        except queue.Empty:
            return ""
    send("uci")
    while True:
        l = rl()
        if not l or l.strip() == "uciok":
            break
    for _ in range(idx):
        pass
    batch_end = min(idx + BATCH, len(rows))
    died = False
    for j in range(idx, batch_end):
        no, kind, note, fen = rows[j].split("|", 3)
        # a fresh board per FEN: the engine keeps its old position on refusal, so send
        # ucinewgame + the START position first to have a known base
        send("ucinewgame")
        send("position startpos")
        send("isready")
        while True:
            l = rl()
            if not l or l.strip() == "readyok":
                break
        send(f"position fen {fen}")
        send("isready")
        refused = None
        while True:
            l = rl(10)
            if not l:
                break
            l = l.strip()
            if l.startswith("readyok"):
                break
            if "invalid FEN" in l or "illegal move" in l or "invalid" in l.lower():
                refused = l
                while True:
                    l2 = rl(2)
                    if not l2 or l2.strip().startswith("readyok"):
                        break
                break
        if p.poll() is not None:
            cls["crashes"] += 1
            crash_rows.append(f"{no}|{kind}|{note}|{fen}")
            died = True
            break
        if refused:
            cls["refused"] += 1
            continue
        try:
            b = chess.Board(fen)
            valid = b.is_valid()
        except ValueError:
            valid = False  # python-chess cannot even parse it: counted as pc-INVALID
        send("go depth 2")
        best = None
        import time
        t0 = time.monotonic()
        while time.monotonic() - t0 < 30:
            l = rl()
            if not l:
                if time.monotonic() - t0 > 30:
                    break
                continue
            l = l.strip()
            if l.startswith("bestmove"):
                best = l.split()[1]
                break
        if p.poll() is not None:
            cls["crashes"] += 1
            crash_rows.append(f"{no}|{kind}|{note}|{fen}")
            died = True
            break
        if valid:
            cls["accepted_valid"] += 1
            legal = any(m.uci() == best for m in chess.Board(fen).legal_moves) if best else False
            if not legal:
                cls["illegal_bestmoves"] += 1
                illegal_rows.append(f"{no}|{kind}|{note}|{fen}|{best}")
        else:
            cls["accepted_invalid"] += 1
            special.append(f"{no}|{kind}|{note}|{fen}|bestmove {best}")
    san = [l for l in err if "AddressSanitizer" in l or "runtime error" in l or "LeakSanitizer" in l or "SUMMARY" in l]
    if san:
        cls["san_lines"] += len(san)
        san_rows.append(f"# batch starting at FEN {idx}: {len(san)} sanitizer lines")
        san_rows.extend(san[:5])
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    if died:
        restarts += 1
        idx = batch_end if not crash_rows or j == batch_end - 1 else j
        # restart at the NEXT FEN after the one that killed the process
        idx = j + 1
    else:
        idx = batch_end
print(f"refused {cls['refused']}, accepted+valid {cls['accepted_valid']}, "
      f"accepted+pc-INVALID {cls['accepted_invalid']}, crashes {cls['crashes']} "
      f"(restarts {restarts}), sanitizer lines {cls['san_lines']}, "
      f"illegal bestmoves {cls['illegal_bestmoves']}")
open(f"{outdir}/classes.txt", "w").write(
    f"refused {cls['refused']}\naccepted_valid {cls['accepted_valid']}\n"
    f"accepted_invalid {cls['accepted_invalid']}\ncrashes {cls['crashes']}\n"
    f"restarts {restarts}\nsanitizer_lines {cls['san_lines']}\nillegal_bestmoves {cls['illegal_bestmoves']}\n")
open(f"{outdir}/special_invalid_accepted.txt", "w").write("\n".join(special) + "\n")
open(f"{outdir}/crashes.txt", "w").write("\n".join(crash_rows) + "\n")
open(f"{outdir}/sanitizer.txt", "w").write("\n".join(san_rows) + "\n")
open(f"{outdir}/illegal_bestmoves.txt", "w").write("\n".join(illegal_rows) + "\n")
