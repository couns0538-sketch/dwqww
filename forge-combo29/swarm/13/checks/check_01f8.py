#!/usr/bin/env python3
"""Check of seat 01's S-F8: are halfmove/fullmove above 65535 silently CLAMPED to 65535?

Their claim: a FEN whose halfmove or fullmove field exceeds 65535 is ACCEPTED, and the stored value is
clamped to 65535 by a `uint16_t` store, so the engine's counter is not what the FEN said. They note the
only search consequence is the `>= 100` drawn-root branch.

That is a sharp, checkable claim, and it matters because I verified the drawn-root repair (S-F17) by
feeding halfmove 100 and 150 — so the counter's exact storage is adjacent to my own work. If clamping
happens, the question is whether it is visible in behaviour.

HOW TO OBSERVE IT WITHOUT INSTRUMENTATION: the drawn-root branch fires when halfmove >= 100. If a FEN
carrying halfmove 70000 is stored as 65535, halfmove >= 100 still holds, so behaviour is unchanged —
which is what seat 01 says (only the >= 100 branch matters). To make the STORED VALUE observable at all I
need a discriminator between "clamped to 65535" and "refused" and "stored exactly":

  * refused             -> the engine keeps the PREVIOUS position (visible: perft of that position)
  * accepted, any value -> perft of the FEN's position
  * stored exactly      -> nothing further is observable from UCI, since 70000 and 65535 are both >= 100

So the honest test is: (a) is such a FEN ACCEPTED at all (not refused)? (b) does the drawn-root branch
still fire for it? (c) is there any behaviour difference between halfmove 65535 and 70000, which would be
the signature of clamping at the boundary?

A FEN with halfmove 0 and fullmove 70000 tests the same store from the other field.

Usage: clampcheck.py EXE OUTDIR
"""
import json
import os
import re
import subprocess
import sys

import chess

EXE = sys.argv[1]
OUTDIR = sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from settings import BASE  # noqa: E402

BAD = ("unknown option", "invalid value", "error")
# a mate-in-1 board, so the drawn-root branch is visible: with halfmove >= 100 the base build misses the
# mate (0 nodes, first legal move); with halfmove < 100 it finds it. That makes the STORED counter's
# crossing of 100 observable through UCI alone.
MATE = "6k1/5ppp/8/8/8/8/8/R5K1 w - - {} {}"
FENS = [
    ("halfmove 0      fullmove 1          (control)", MATE.format(0, 1)),
    ("halfmove 99     fullmove 1          (below threshold)", MATE.format(99, 1)),
    ("halfmove 100    fullmove 1          (threshold)", MATE.format(100, 1)),
    ("halfmove 65535  fullmove 1          (uint16 max)", MATE.format(65535, 1)),
    ("halfmove 65536  fullmove 1          (one past uint16)", MATE.format(65536, 1)),
    ("halfmove 70000  fullmove 1          (well past)", MATE.format(70000, 1)),
    ("halfmove 300000 fullmove 1          (far past)", MATE.format(300000, 1)),
    ("halfmove 0      fullmove 1000000000 (fullmove far past)", MATE.format(0, 1000000000)),
    ("halfmove 70000  fullmove 70000      (both past)", MATE.format(70000, 70000)),
]


def run(fen, prev=None):
    """Search this FEN. If `prev` is given, first set that position, so a refusal is detectable."""
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pred):
        while True:
            l = p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died")
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                return l            # an invalid-FEN style line: return it, the caller records it
            if pred(l):
                return l

    send("uci")
    seen = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died in uci handshake")
        l = l.rstrip("\n")
        if l.startswith("option name"):
            seen.append(l)
        if l == "uciok":
            break
    for n, v in BASE:
        if any(o.startswith("option name %s " % n) for o in seen):
            send("setoption name %s value %s" % (n, v))
            send("isready")
            until(lambda s: s == "readyok")
    if prev:
        send("position fen " + prev)
        send("isready")
        until(lambda s: s == "readyok")
    send("position fen " + fen)
    send("isready")
    refusal = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: engine died")
        l = l.rstrip("\n")
        if "invalid FEN" in l.lower() or "invalid" in l.lower() and "fen" in l.lower():
            refusal = l
        if l == "readyok":
            break
    send("go depth 8")
    last = None
    bm = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died during search")
        l = l.rstrip("\n")
        if l.startswith("info depth"):
            last = l
        if l.startswith("bestmove"):
            bm = l
            break
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    nd = re.search(r"\bnodes (\d+)", last) if last else None
    mt = re.search(r"score mate (-?\d+)", last) if last else None
    return {"bestmove": (bm.split()[1] if bm and len(bm.split()) > 1 else None),
            "nodes": int(nd.group(1)) if nd else 0,
            "mate": int(mt.group(1)) if mt else None,
            "refusal": refusal}


rows = []
for label, fen in FENS:
    r = run(fen)
    r.update({"label": label, "fen": fen})
    rows.append(r)
    print("%-52s nodes %-7s mate %-5s bm %-8s %s"
          % (label, r["nodes"], r["mate"], r["bestmove"], "REFUSED" if r["refusal"] else "accepted"),
          flush=True)

# refusal isolation: start from a DIFFERENT position first, so a refusal shows as "kept the old board"
PROBE = "position startpos"
print()
print("refusal isolation (set startpos first, then the odd FEN, then perft 1):")


def perft_after(fen):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    while p.stdout.readline().rstrip("\n") != "uciok":
        pass
    send("position startpos"); send("isready")
    while p.stdout.readline().rstrip("\n") != "readyok":
        pass
    send("position fen " + fen); send("isready")
    refusals = []
    while True:
        l = p.stdout.readline().rstrip("\n")
        if "invalid" in l.lower():
            refusals.append(l)
        if l == "readyok":
            break
    send("go perft 1")
    n = None
    while True:
        l = p.stdout.readline().rstrip("\n")
        if l.startswith("nodes "):
            n = int(l.split()[1])
            break
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    return n, refusals


iso = []
for label, fen in (("halfmove 65536 (startpos set first)", MATE.format(65536, 1)),
                   ("halfmove 70000 (startpos set first)", MATE.format(70000, 1)),
                   ("control: halfmove 50 (startpos set first)", MATE.format(50, 1))):
    n, ref = perft_after(fen)
    iso.append({"label": label, "perft1": n, "refusals": ref})
    # lesson C: COMPUTE the expected values rather than typing them
    startpos_legal = chess.Board().legal_moves.count()
    mate_legal = chess.Board(MATE.format(50, 1)).legal_moves.count()
    verdict = ("ACCEPTED (the new board)" if n == mate_legal
               else "STARTED FROM STARTPOS - the FEN was probably refused" if n == startpos_legal
               else "UNEXPECTED - investigate")
    print("  %-44s perft 1 = %-5s refusals=%s  [startpos=%d, mate board=%d] -> %s"
          % (label, n, ref or "none", startpos_legal, mate_legal, verdict))

summary = {"exe": os.path.abspath(EXE), "fens": len(FENS),
           "accepted_over_65535": sum(1 for r in rows if r["refusal"] is None and "6553" in r["label"] or
                                      "70000" in r["label"] or "300000" in r["label"]),
           "rows": rows, "refusal_isolation": iso,
           "note": "The stored counter is NOT directly observable from UCI; this tests acceptance and the "
                   "behavioural crossing of the >=100 drawn-root branch."}
json.dump(summary, open(os.path.join(OUTDIR, "clampcheck.json"), "w"), indent=1)
print()
print("acceptance of every over-65535 FEN:", all(r["refusal"] is None for r in rows))
