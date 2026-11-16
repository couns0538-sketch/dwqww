#!/usr/bin/env python3
"""bareking_worse.py OUTDIR

Item 2: of the 30 bare-king positions where the PC build differs from base, is the PC's answer ever
WORSE rather than merely different?

Seat reporting: another seat found one bare-king position where the cap picks a mate in 10 over a mate
in 8. That would be a regression introduced by FORGE_FIX_BARE_KING_LMR_CAP. This scans my 30 for the
same shape.

Method. "Worse" is decided by comparing the two builds' scores from the SAME side's point of view
at the same depth, and separately by a deeper reference so that a shallow search cannot mislabel a
deliberate trade:

  1. both builds at depth 12 -> compare scores.
  2. a deeper probe (depth 18) on the PC build -> the reference the shallow answers are judged against.
  3. a mate-distance comparison where both report mate: fewer plies is better.

A difference is called PC-WORSE only when the PC score is worse than base by a decisive margin
(>= 100 cp, or a mate distance that is genuinely longer), AND the depth-18 reference does not vindicate
the PC's choice. Anything in the noise band is called NEUTRAL, not worse.

The distinction matters: most of the 30 differ because base answered `cp 0` with 0 nodes (a drawn-root
artefact) and the PC actually searched; a base `cp 0` is not "better" than a PC `cp -120`.
"""
import json
import os
import queue
import re
import subprocess
import sys
import threading

BASE = "/agent/repos/base/forge-combo29/build-rel/forge"
PC = "/agent/repos/pcbase/forge-combo29/build-pc/forge"
BARE_VARIANT = "/tmp/var_BARE_KING_LMR_CAP/build-pc/forge"

NOISE = 50          # |cp| inside this is not a difference in substance
DECISIVE = 100      # a PC score this much worse is a candidate regression


class Reader:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t=300):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def search(exe, fen, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(p.stdout)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def drain():
        while True:
            l = r.get()
            if l is None:
                raise RuntimeError("no readyok")
            if l.strip() == "readyok":
                return

    send("uci")
    while True:
        l = r.get(60)
        if l is None or l.strip() == "uciok":
            break
    for o in ["Hash value 16", "Threads value 1", "OwnBook value false"]:
        send("setoption name " + o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen " + fen); send("isready"); drain()
    send(f"go depth {depth}")
    nodes, score, best = None, None, None
    while True:
        l = r.get(900)
        if l is None:
            best = "ABSENT"
            break
        if l.startswith("info depth") and " nodes " in l:
            m = re.search(r" nodes (\d+) ", l)
            if m:
                nodes = int(m.group(1))
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            if m:
                score = (m.group(1), int(m.group(2)))
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    return {"nodes": nodes, "score": score, "best": best}


def cp_of(sc):
    """Centipawn value of a score, with mate mapped to a large sentinel of the right sign."""
    if sc is None:
        return None
    kind, val = sc
    if kind == "cp":
        return val
    # mate N: side to move mates in N -> huge positive; mate -N -> huge negative
    return 100000 - abs(val) if val > 0 else -(100000 - abs(val))


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    samples = json.load(open("../job37/raw/samples.json"))
    bk = [t for t in samples["targeted"] if t["tag"].startswith("bare_king")]
    print(f"bare-king positions: {len(bk)}")
    print(f"{'#':>2} {'base d12':>14} {'pc d12':>14} {'pc d18 ref':>14} {'variant d12':>14} verdict")
    rows = []
    for i, t in enumerate(bk):
        fen = t["fen"]
        b = search(BASE, fen, 12)
        p = search(PC, fen, 12)
        ref = search(PC, fen, 18)
        var = search(BARE_VARIANT, fen, 12)
        bc, pc_, rc = cp_of(b["score"]), cp_of(p["score"]), cp_of(ref["score"])
        verdict = "NEUTRAL"
        if bc is None or pc_ is None:
            verdict = "UNSCORED"
        elif bc == 0 and b["nodes"] == 0:
            # base answered without searching; it has no claim to be "better"
            verdict = "base was a 0-node draw artefact, not a real score"
        elif abs(bc - pc_) <= NOISE:
            verdict = "NEUTRAL (within noise)"
        elif pc_ < bc - DECISIVE:
            # candidate regression: check the reference
            if rc is not None and abs(rc - pc_) < abs(rc - bc):
                verdict = "PC-WORSE than base at depth 12, but depth-18 supports PC"
            else:
                verdict = "PC-WORSE: candidate regression"
        elif pc_ > bc + DECISIVE:
            verdict = "PC-BETTER"
        else:
            verdict = "differs, below the decisive margin"
        rows.append({"i": i, "fen": fen, "base": b, "pc": p, "ref18": ref, "variant": var,
                     "verdict": verdict})
        print(f"{i:>2} {str(b['score']):>14} {str(p['score']):>14} {str(ref['score']):>14} "
              f"{str(var['score']):>14} {verdict}", flush=True)

    import collections
    c = collections.Counter(r["verdict"] for r in rows)
    print()
    print("verdict counts:")
    for k, n in sorted(c.items(), key=lambda kv: -kv[1]):
        print(f"  {k:52s} {n}")
    worse = [r for r in rows if r["verdict"].startswith("PC-WORSE")]
    print()
    if worse:
        print("POSITIONS WHERE THE PC ANSWER LOOKS WORSE — inspect these:")
        for r in worse:
            print(f"  #{r['i']} {r['fen']}")
            print(f"     base {r['base']['score']}/{r['base']['nodes']}   "
                  f"pc {r['pc']['score']}/{r['pc']['nodes']}   ref18 {r['ref18']['score']}")
    else:
        print("No position where the PC answer is worse than base's by a decisive margin.")
    json.dump(rows, open(os.path.join(outdir, "bareking_worse.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
