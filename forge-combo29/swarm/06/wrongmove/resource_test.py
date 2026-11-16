#!/usr/bin/env python3
"""Resource test for the reported wrong-move defect.

Hypothesis: the engine's free choice is resource-limited, not statically wrong. At depth 18 the
CORRECT move needed 21.4M nodes while the wrong one needed 0.4M, so with Hash 16 the search may be
thrashing the transposition table, and the deeper/correct line may be unreachable within the budget.

If the hypothesis holds, giving the engine much more hash (and/or much more time) should make its FREE
choice switch to c6d6, the move its own restricted search scores better.

Arms (all Threads 1 - owner's rule - fresh process each, PC20):
  A  Hash 16,  go depth 18              (the reported setting, for reference)
  B  Hash 512, go depth 18              (hash only)
  C  Hash 16,  go movetime 60000        (time only, 60 s)
  D  Hash 512, go movetime 60000        (both)

Also the two restricted scores at the LARGER hash, so we can tell whether the engine's opinion of the
two moves itself changes or only its ability to reach that opinion.

usage: resource_test.py EXE OUTFILE
"""
import hashlib
import subprocess
import sys

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BAD = ("unknown option", "invalid value", "ERROR")
FEN = "1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183"


def one(exe, hash_mb, go_cmd, searchmove=None):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def w(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

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
    for n, v in [("Threads", "1"), ("Hash", str(hash_mb))] + PC20:
        w("setoption name %s value %s" % (n, v))
        w("isready")
        ready()
    w("ucinewgame")
    w("isready")
    ready()
    w("position fen " + FEN)
    w("isready")
    ready()
    cmd = go_cmd + ((" searchmoves " + searchmove) if searchmove else "")
    w(cmd)
    last = None
    bm = None
    while True:
        line = r().strip()
        if any(m in line for m in BAD):
            raise RuntimeError(line)
        if line.startswith("info") and " pv " in line:
            last = line.split()
        if line.startswith("bestmove"):
            bm = line.split()[1]
            break
    p.kill()
    score_kind = score = nodes = depth = None
    if last:
        score_kind = last[last.index("score") + 1]
        score = int(last[last.index("score") + 2])
        nodes = int(last[last.index("nodes") + 1])
        if "depth" in last:
            depth = int(last[last.index("depth") + 1])
    return {"bm": bm, "kind": score_kind, "score": score, "nodes": nodes, "depth": depth}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    exe, outfile = sys.argv[1:3]
    lines = ["EXE        : " + exe, "EXE SHA256 : " + sha256(exe),
             "FEN        : " + FEN,
             "SETTINGS   : PC20, Threads 1, fresh process per number, OwnBook false",
             "Hypothesis : the wrong choice is RESOURCE-LIMITED (hash/time), not a static ordering error.",
             ""]
    lines.append("=== free choice (no searchmoves) under different resources ===")
    lines.append("| arm | hash | go | bestmove | depth | score | nodes |")
    lines.append("|---|---|---|---|---|---|---|")
    arms = [("A reported setting", 16, "go depth 18"),
            ("B hash only", 512, "go depth 18"),
            ("C time only", 16, "go movetime 60000"),
            ("D hash and time", 512, "go movetime 60000")]
    free = {}
    for label, h, go in arms:
        r = one(exe, h, go)
        free[label] = r
        lines.append("| %s | %d MB | `%s` | %s | %s | %s %s | %s |" %
                     (label, h, go, r["bm"], r["depth"], r["kind"], r["score"], r["nodes"]))
    lines.append("")
    lines.append("=== each move's OWN score under the larger hash (restricted root) ===")
    lines.append("| move | hash | go | score | nodes |")
    lines.append("|---|---|---|---|---|")
    for mv in ("c6c7", "c6d6"):
        for h, go in ((16, "go depth 18"), (512, "go depth 18")):
            r = one(exe, h, go, mv)
            lines.append("| %s | %d MB | `%s` | %s %s | %s |" % (mv, h, go, r["kind"], r["score"], r["nodes"]))
    lines.append("")
    chose = {k: v["bm"] for k, v in free.items()}
    good = "c6d6"
    lines.append("free choice per arm: " + "; ".join("%s -> %s" % (k, v) for k, v in chose.items()))
    if all(v == good for v in chose.values()):
        lines.append("VERDICT: with more resources the engine chooses %s in EVERY arm - consistent with a" % good)
        lines.append("         resource limit, but note the reported setting also chose it, so this arm set")
        lines.append("         does not isolate the cause.")
    elif chose["A reported setting"] != good and any(v == good for k, v in chose.items() if k != "A reported setting"):
        lines.append("VERDICT: the free choice CHANGES to %s when resources grow -> RESOURCE-LIMITED search" % good)
        lines.append("         failure, not a static ordering error.")
    else:
        lines.append("VERDICT: the free choice does NOT switch to %s under larger resources -> the wrong" % good)
        lines.append("         choice is not merely a budget effect.")
    text = "\n".join(lines) + "\n"
    open(outfile, "w").write(text)
    print(text)


if __name__ == "__main__":
    main()
