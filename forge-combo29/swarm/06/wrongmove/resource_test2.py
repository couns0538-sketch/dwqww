#!/usr/bin/env python3
"""Resource test: is the wrong-move choice RESOURCE-LIMITED (hash/time) rather than a static ordering flaw?

PC r15 at depth 20 and BASE at depth 18. Each arm: fresh process, Threads 1, full option set, and the
engine's FREE choice (no searchmoves). Arms vary Hash and the time budget only.

usage: resource_test2.py EXE LABEL MODE DEPTH OUTFILE
"""
import hashlib
import subprocess
import sys
import time

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BAD = ("unknown option", "invalid value", "ERROR")
FEN = "1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183"


def one(exe, hash_mb, go_cmd, mode):
    opts = PC20 if mode == "PC20" else S14
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def w(c):
        p.stdin.write(c + "\n"); p.stdin.flush()

    def r():
        line = p.stdout.readline()
        if line == "":
            raise RuntimeError("engine died")
        return line

    def ready():
        while True:
            line = r().strip()
            if any(m in line for m in BAD):
                raise RuntimeError(line)
            if line == "readyok":
                return

    w("uci")
    while r().strip() != "uciok":
        pass
    for n, v in [("Threads", "1"), ("Hash", str(hash_mb))] + opts:
        w("setoption name %s value %s" % (n, v)); w("isready"); ready()
    w("ucinewgame"); w("isready"); ready()
    w("position fen " + FEN); w("isready"); ready()
    t0 = time.monotonic()
    w(go_cmd)
    last = None; bm = None
    while True:
        line = r().strip()
        if any(m in line for m in BAD):
            raise RuntimeError(line)
        if line.startswith("info") and " pv " in line:
            last = line.split()
        if line.startswith("bestmove"):
            bm = line.split()[1]; break
    el = time.monotonic() - t0
    p.kill()
    d = {"bm": bm, "wall_s": round(el, 1)}
    if last:
        d["kind"] = last[last.index("score") + 1]
        d["score"] = int(last[last.index("score") + 2])
        d["nodes"] = int(last[last.index("nodes") + 1])
        d["depth"] = int(last[last.index("depth") + 1]) if "depth" in last else None
    return d


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    exe, label, mode, depth, outfile = sys.argv[1:6]
    depth = int(depth)
    L = ["BUILD      : " + label, "EXE        : " + exe, "SHA256     : " + sha256(exe),
         "SETTINGS   : %s, Threads 1, fresh process per arm, OwnBook false" % mode,
         "FEN        : " + FEN,
         "QUESTION   : does the free choice become c6d6 (the better move) when resources are generous?",
         "Cost facts : at depth 20 (PC) the better move c6d6 needs ~142.5M nodes; the played c6c7 ~16.1M.",
         ""]
    L.append("| arm | hash | go | free choice | depth | score | nodes | wall s |")
    L.append("|---|---|---|---|---|---|---|---|")
    arms = [
        ("1 reported", 16, "go depth %d" % depth),
        ("2 big hash", 2048, "go depth %d" % depth),
        ("3 big hash + long clock", 2048, "go movetime 300000"),
        ("4 reported hash + long clock", 16, "go movetime 300000"),
    ]
    res = {}
    for name, h, go in arms:
        try:
            d = one(exe, h, go, mode)
        except RuntimeError as e:
            d = {"bm": "ERROR " + str(e), "wall_s": None}
        res[name] = d
        L.append("| %s | %d MB | `%s` | %s | %s | %s %s | %s | %s |" %
                 (name, h, go, d.get("bm"), d.get("depth"), d.get("kind"), d.get("score"),
                  d.get("nodes"), d.get("wall_s")))
    L.append("")
    picks = {k: v.get("bm") for k, v in res.items()}
    L.append("free choice per arm: " + "; ".join("%s -> %s" % kv for kv in picks.items()))
    better = "c6d6"
    if all(v == better for v in picks.values()):
        L.append("VERDICT: EVERY arm picks %s, including the reported setting - the choice is not sensitive to" % better)
        L.append("         hash or time here, so this arm set does not show a resource limit.")
    elif picks["1 reported"] != better and any(v == better for k, v in picks.items() if k != "1 reported"):
        L.append("VERDICT: RESOURCE-LIMITED. With more hash/time the engine switches to %s, so the wrong" % better)
        L.append("         choice is a budget effect, not a static ordering flaw.")
    else:
        L.append("VERDICT: NOT resource-limited. Generous hash and a 300 s clock do NOT make it choose %s." % better)
        L.append("         The flaw is not explained by a node or time bound.")
    text = "\n".join(L) + "\n"
    open(outfile, "w").write(text)
    print(text)


if __name__ == "__main__":
    main()
