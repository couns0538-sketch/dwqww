#!/usr/bin/env python3
"""recount56.py -- seat 10's OWN recount of deepseek6 long56.

Independent of the original runner: it does NOT import fuzzuci56.py.  It:
  1. regenerates the 2,000 sequences with make_uci56-style logic at seed 56 writing to
     ./seqs56.txt (kept, so the exact input is committed);
  2. runs each sequence in its own process with a 20 s readyok deadline;
  3. classifies every `bestmove` line against python-chess, taking the position from the
     LAST `position` command IT SENT (not from engine output);
  4. counts crashes (exit codes), hangs, sanitizer lines on stderr, illegal bestmoves.

Usage: recount56.py EXE OUTDIR
"""
import concurrent.futures
import json
import os
import random
import re
import subprocess
import sys
import threading
import time

import chess

EXE = os.path.abspath(sys.argv[1])
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

OPTIONS = ["Hash", "Threads", "OwnBook", "MultiPV", "LmpBase", "RfpMargin", "QsSeeMargin",
           "SingularMargin", "IirDepth", "HistoryBonusMax", "AspirationDelta", "NonPawnCorrection",
           "IirAtRoot", "NoRfpAtCut", "BogusOption"]
VALUES = ["0", "1", "2", "16", "64", "256", "-5", "999999", "banana", "true", "false", ""]
G_EPD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw", "set_G.epd")
FENS = [l.strip() for l in open(G_EPD) if l.strip()][:50]


def random_move(rng):
    a = rng.choice("abcdefgh") + rng.choice("12345678")
    b = rng.choice("abcdefgh") + rng.choice("12345678")
    return a + b + rng.choice(["", "", "", "q", "n", "b", "r"])


def gen_seq(rng):
    n = rng.randint(5, 30)
    seq = ["uci"]
    body = []
    for _ in range(n - 2):
        t = rng.random()
        if t < 0.12:
            body.append("isready")
        elif t < 0.20:
            body.append("ucinewgame")
        elif t < 0.38:
            opt = rng.choice(OPTIONS)
            if rng.random() < 0.15:
                body.append("setoption name %s" % opt)
            else:
                body.append("setoption name %s value %s" % (opt, rng.choice(VALUES)))
        elif t < 0.58:
            if rng.random() < 0.5:
                body.append("position startpos")
            else:
                body.append("position fen %s" % rng.choice(FENS))
            k = rng.randint(0, 40)
            mv = " ".join(random_move(rng) for _ in range(k))
            body.append("position startpos moves " + mv if rng.random() < 0.5
                        else "position startpos moves e2e4 " + mv)
        elif t < 0.78:
            kind = rng.choice(["depth", "nodes", "movetime", "infinite", "ponder", "depth"])
            if kind == "depth":
                body.append("go depth %d" % rng.randint(1, 6))
            elif kind == "nodes":
                body.append("go nodes %d" % rng.randint(1, 5000))
            elif kind == "movetime":
                body.append("go movetime %d" % rng.randint(1, 50))
            elif kind == "infinite":
                body.append("go infinite")
            else:
                body.append("go ponder")
        elif t < 0.88:
            body.append(rng.choice(["stop", "ponderhit"]))
        else:
            body.append(rng.choice(["garbage line", "go banana", "position", "setoption name",
                                    "go depth -3", "###"]))
    seq.extend(body)
    seq.append("isready")
    seq.append("quit")
    return seq


def board_after(pos_line):
    """Position python-chess has after a `position ...` line, or None if unparseable."""
    body = pos_line[len("position "):]
    try:
        if body.startswith("startpos"):
            b = chess.Board()
            if " moves " in body:
                for mv in body.split(" moves ", 1)[1].split():
                    try:
                        m = chess.Move.from_uci(mv)
                    except ValueError:
                        return b          # engine keeps the legal prefix
                    if m not in b.legal_moves:
                        return b
                    b.push(m)
            return b
        if body.startswith("fen "):
            return chess.Board(body[4:].strip())
    except ValueError:
        return None
    return None


SAN = ("AddressSanitizer", "LeakSanitizer", "ThreadSanitizer", "runtime error", "SUMMARY",
       "UndefinedBehaviorSanitizer")


def run_seq(args):
    idx, lines = args
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    out, err = [], []

    def rd(stream, sink):
        try:
            for l in stream:
                sink.append(l)
        except Exception:
            pass

    threading.Thread(target=rd, args=(p.stdout, out), daemon=True).start()
    threading.Thread(target=rd, args=(p.stderr, err), daemon=True).start()
    last_pos = None
    nready = 0
    go_positions = []      # the position in force at each `go` we send, in order
    verdict = {"i": idx, "hang": False, "crash": None, "san": 0, "illegal": [], "bestmoves": 0}
    try:
        for line in lines:
            if line != "###" and not line.startswith("### seq"):
                p.stdin.write(line + "\n")
                p.stdin.flush()
            if line.startswith("position "):
                last_pos = line
            if line.startswith("go "):
                go_positions.append(last_pos)
            if line == "isready":
                want = nready + 1
                t0 = time.monotonic()
                while time.monotonic() - t0 < 20:
                    if sum(1 for x in out if x.strip() == "readyok") >= want:
                        nready = want
                        break
                    time.sleep(0.02)
                else:
                    verdict["hang"] = True
                    p.kill()
                    return verdict
        p.wait(timeout=30)
    except Exception as e:
        try:
            p.kill()
        except Exception:
            pass
        verdict["crash"] = "exception %s" % e
        return verdict
    verdict["rc"] = p.returncode
    if p.returncode not in (0, -15, 15, -9):
        verdict["crash"] = "exit %s" % p.returncode
    verdict["san"] = sum(1 for l in err if any(s in l for s in SAN))
    # legality: bestmove k is checked against the position in force at go k (WE track it)
    k = 0
    for l in out:
        if not l.startswith("bestmove"):
            continue
        verdict["bestmoves"] += 1
        mv = l.split()[1]
        pos = go_positions[k] if k < len(go_positions) else None
        k += 1
        if mv == "0000":
            continue
        b = board_after(pos) if pos else chess.Board()
        if b is None:
            continue
        try:
            m = chess.Move.from_uci(mv)
        except ValueError:
            verdict["illegal"].append((l.strip(), mv, "unparseable", pos))
            continue
        if m not in b.legal_moves:
            verdict["illegal"].append((l.strip(), mv, pos, str(b.fen())))
    return verdict


def main():
    rng = random.Random(56)
    seqs = [gen_seq(rng) for _ in range(2000)]
    with open(os.path.join(OUT, "seqs56.txt"), "w") as f:
        for i, s in enumerate(seqs):
            f.write("### seq %d\n" % i)
            for l in s:
                f.write(l + "\n")

    t0 = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(run_seq, list(enumerate(seqs))))
    wall = time.monotonic() - t0

    tot = {"sequences": len(results),
           "completed": sum(1 for r in results if not r["hang"] and not r["crash"]),
           "hangs": sum(1 for r in results if r["hang"]),
           "crashes": sum(1 for r in results if r["crash"]),
           "sanitizer_lines": sum(r["san"] for r in results),
           "bestmoves_seen": sum(r["bestmoves"] for r in results),
           "illegal_bestmoves": sum(len(r["illegal"]) for r in results)}
    tot["wall_seconds"] = round(wall, 1)

    with open(os.path.join(OUT, "recount56_summary.json"), "w") as f:
        json.dump(tot, f, indent=2)
        f.write("\n")
    with open(os.path.join(OUT, "recount56_bad.txt"), "w") as f:
        for r in results:
            if r["hang"] or r["crash"] or r["san"] or r["illegal"]:
                f.write("### seq %d hang=%s crash=%s san=%d illegal=%s\n"
                        % (r["i"], r["hang"], r["crash"], r["san"], r["illegal"]))
    print(json.dumps(tot, indent=2))


main()
