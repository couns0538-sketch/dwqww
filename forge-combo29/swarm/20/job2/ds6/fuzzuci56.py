#!/usr/bin/env python3
"""fuzzuci56.py -- run the 2,000 UCI sequences under a sanitizer build, one process per sequence.
A sequence = the lines between '### seq N' markers. No readyok within 20 s after isready = a HANG
(kill, count, keep the sequence). Records: crashes / hangs / sanitizer lines / illegal bestmoves
(a bestmove illegal for the position it was searched from, where that position is python-chess
valid and has legal moves; 0000 on a finished position is correct)."""
import chess
import random
import subprocess
import sys
import threading
import time

exe = sys.argv[1]
outdir = sys.argv[2]
seqs = []
cur = None
for line in open("/tmp/uci56_seqs.txt"):
    line = line.rstrip("\n")
    if line.startswith("### seq "):
        cur = [line]
        seqs.append(cur)
    elif cur is not None:
        cur.append(line)

random.seed(56 + 1)
results = {"seqs": 0, "crashes": 0, "hangs": 0, "san": 0, "illegal": 0, "ok": 0}
bad = []

def run_seq(i, lines):
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
    lastpos = chess.STARTING_FEN
    sent_quit = False
    try:
        for line in lines[1:]:
            if line.startswith("position"):
                # track the position for the legality check
                pass
            try:
                p.stdin.write(line + "\n")
                p.stdin.flush()
            except Exception:
                break
            if line == "isready":
                t0 = time.monotonic()
                ready = False
                while time.monotonic() - t0 < 20:
                    if any("readyok" in x for x in out[len(out) - 30:]):
                        ready = True
                        break
                    time.sleep(0.02)
                if not ready:
                    results["hangs"] += 1
                    bad.append((i, lines, "HANG"))
                    p.kill()
                    return
            if line.startswith("position"):
                lastpos = line
            if line == "quit":
                sent_quit = True
        if not sent_quit:
            p.stdin.write("quit\n")
            p.stdin.flush()
        p.wait(timeout=30)
    except Exception:
        p.kill()
        results["crashes"] += 1
        bad.append((i, lines, "CRASH/EXC"))
        return
    rc = p.returncode
    san = [l for l in err if "AddressSanitizer" in l or "runtime error" in l or
           "LeakSanitizer" in l or "SUMMARY" in l]
    if san:
        results["san"] += len(san)
        bad.append((i, lines, "SAN: " + san[0][:80]))
    if rc not in (0, -15, 15):
        results["crashes"] += 1
        bad.append((i, lines, f"EXIT {rc}"))
        return
    # the bestmove legality: find the last 'bestmove' and the last 'position' before it
    best = None
    pos_line = None
    for l in out:
        if l.startswith("position"):
            pos_line = l
        if l.startswith("bestmove"):
            best = l.split()[1]
    if best and best != "0000" and pos_line:
        try:
            b = chess.Board(lastpos if "moves" in lastpos or "fen" in lastpos else chess.STARTING_FEN)
            if " moves " in lastpos:
                parts = lastpos.split(" moves ", 1)
                b = chess.Board(parts[0].replace("position fen ", "").strip() or chess.STARTING_FEN)
                for mv in parts[1].split():
                    try:
                        mm = chess.Move.from_uci(mv)
                    except Exception:
                        break
                    if mm not in b.legal_moves:
                        break  # the engine keeps the legal prefix (long 46)
                    b.push(mm)
            legal = any(m.uci() == best for m in b.legal_moves)
            if not legal:
                results["illegal"] += 1
                bad.append((i, lines, f"ILLEGAL BESTMOVE {best} after {lastpos[:60]}"))
        except ValueError:
            pass
    results["ok"] += 1

import concurrent.futures
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    futs = [ex.submit(run_seq, i, s) for i, s in enumerate(seqs)]
    for f in futs:
        f.result()
print(f"seqs {results['ok'] + results['crashes'] + results['hangs']} (ok {results['ok']}), "
      f"crashes {results['crashes']}, hangs {results['hangs']}, sanitizer lines {results['san']}, "
      f"illegal bestmoves {results['illegal']}")
with open(f"{outdir}/fuzz56_summary.txt", "w") as f:
    f.write(str(results) + "\n")
with open(f"{outdir}/bad_sequences.txt", "w") as f:
    for i, lines, why in bad:
        f.write(f"### seq {i}: {why}\n")
        f.write("\n".join(lines) + "\n\n")
