#!/usr/bin/env python3
"""19-C50: run MY harness on SEAT 27's positions.

Why this settles it: seat 27's exe sha256 (068f0927...) is the same build I used, so the build is not a
variable. If my harness reproduces its S14/PC20 cells on ITS positions, the harnesses agree and the remaining
difference is the position set. If it does not, there is a harness difference to find.

Two comparisons:
  (a) MY run on THEIR 600 positions vs THEIR reported cells  -> isolates harness
  (b) MY run on THEIR positions vs MY run on MY positions    -> isolates position set
"""
import subprocess, os, re, json, hashlib

PCPATH = os.path.expanduser("~/pcbuild/build/forge")
BASEPATH = os.path.expanduser("~/build_rel/forge")
HERE = os.path.dirname(os.path.abspath(__file__))
THEIR_FENS = os.path.join(HERE, "their_600.fens")
THEIR_JSON = "/home/ubuntu/s27/sign_600_2000.json"
OUTDIR = HERE

S14 = [
    ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
    ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
    ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
    ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
    ("IirDepth", 2), ("NonPawnCorrection", "true"),
]
PC20EXTRA = [
    ("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
    ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
]


def run(exe, fen, opts, go):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    for k, v in opts:
        send("setoption name %s value %s" % (k, v))
    send("isready")
    send("position fen %s" % fen)
    send("isready")
    send("go %s" % go)
    coll = []
    while True:
        ln = p.stdout.readline()
        if not ln:
            break
        coll.append(ln.rstrip("\n"))
        if ln.startswith("bestmove"):
            break
    try:
        send("quit")
        p.wait(timeout=30)
    except Exception:
        p.kill()
    best, dep, nodes, score = None, None, None, None
    for ln in coll:
        t = ln.split()
        if not t:
            continue
        if t[0] == "bestmove":
            best = t[1]
        elif t[0] == "info" and " pv " in ln:
            m = re.search(r"\bdepth (\d+)", ln)
            if m:
                dep = int(m.group(1))
            m = re.search(r"\bnodes (\d+)", ln)
            if m:
                nodes = int(m.group(1))
            m = re.search(r"\bscore (cp|mate) (-?\d+)", ln)
            if m:
                score = [m.group(1), int(m.group(2))]
    if nodes is None and best is not None:
        return {"depth": 0, "nodes": 0, "score": None, "bestmove": best, "degenerate": True}
    if nodes is None or best is None:
        raise RuntimeError("no search at all for %s\n%s" % (fen, "\n".join(coll)[:600]))
    return {"depth": dep, "nodes": nodes, "score": score, "bestmove": best, "degenerate": False}


def main():
    fens = [l.strip() for l in open(THEIR_FENS) if l.strip()]
    print("their positions:", len(fens), flush=True)
    cells = []
    for i, fen in enumerate(fens):
        s = run(BASEPATH, fen, S14, "softnodes 2000")
        p = run(PCPATH, fen, S14 + PC20EXTRA, "softnodes 2000")
        cells.append({"fen": fen, "S14": s, "PC20": p,
                      "d_depth": p["depth"] - s["depth"],
                      "same_move": s["bestmove"] == p["bestmove"]})
        if (i + 1) % 50 == 0:
            print("  %d/%d" % (i + 1, len(fens)), flush=True)

    theirs = json.load(open(THEIR_JSON))
    tc = theirs["cells"]

    # (a) agreement of my cells with their cells, cell by cell
    same_d = sum(1 for m, t in zip(cells, tc) if m["d_depth"] == t["d_depth"])
    same_s14 = sum(1 for m, t in zip(cells, tc)
                   if m["S14"]["bestmove"] == t["S14"]["bestmove"] and m["S14"]["depth"] == t["S14"]["depth"])
    same_pc = sum(1 for m, t in zip(cells, tc)
                  if m["PC20"]["bestmove"] == t["PC20"]["bestmove"] and m["PC20"]["depth"] == t["PC20"]["depth"])

    def tally(cs):
        sm = [c for c in cs if c["same_move"]]
        return (len(cs), sum(c["d_depth"] for c in cs),
                len(sm), sum(c["d_depth"] for c in sm))

    mine_n, mine_sum, mine_smn, mine_smsum = tally(cells)
    their_n, their_sum, their_smn, their_smsum = tally(tc)

    with open(os.path.join(OUTDIR, "crosscheck_their_positions.txt"), "w") as f:
        f.write("19-C50: MY harness on SEAT 27's 600 positions (softnodes 2000)\n")
        f.write("my  pc20 sha256 %s\n" % hashlib.sha256(open(PCPATH, "rb").read()).hexdigest())
        f.write("my  base sha256 %s\n" % hashlib.sha256(open(BASEPATH, "rb").read()).hexdigest())
        f.write("their stated sha256 %s\n\n" % theirs.get("sha256"))
        f.write("(a) CELL-BY-CELL AGREEMENT BETWEEN THE TWO HARNESSES\n")
        f.write("  identical d_depth      : %d of %d = %.1f %%\n" % (same_d, len(cells), 100.0 * same_d / len(cells)))
        f.write("  identical S14 cell     : %d of %d = %.1f %%\n" % (same_s14, len(cells), 100.0 * same_s14 / len(cells)))
        f.write("  identical PC20 cell    : %d of %d = %.1f %%\n" % (same_pc, len(cells), 100.0 * same_pc / len(cells)))
        f.write("\n(b) THE SAME TALLIES, BOTH HARNESSES, SAME POSITIONS\n")
        f.write("  MINE  : all %d cells sum_d %+d ; same-move %d cells sum_d %+d\n" % (
            mine_n, mine_sum, mine_smn, mine_smsum))
        f.write("  THEIRS: all %d cells sum_d %+d ; same-move %d cells sum_d %+d\n" % (
            their_n, their_sum, their_smn, their_smsum))
        f.write("\nper-cell disagreements (first 40):\n")
        k = 0
        for i, (m, t) in enumerate(zip(cells, tc)):
            if m["d_depth"] != t["d_depth"]:
                f.write("  %3d %s\n      mine   S14 d%-2d %-6s | PC20 d%-2d %-6s | d %+d\n"
                        "      theirs S14 d%-2d %-6s | PC20 d%-2d %-6s | d %+d\n" % (
                            i, m["fen"][:60],
                            m["S14"]["depth"], m["S14"]["bestmove"], m["PC20"]["depth"], m["PC20"]["bestmove"], m["d_depth"],
                            t["S14"]["depth"], t["S14"]["bestmove"], t["PC20"]["depth"], t["PC20"]["bestmove"], t["d_depth"]))
                k += 1
                if k >= 40:
                    break
    print("\n(a) identical d_depth %d/%d = %.1f%%" % (same_d, len(cells), 100.0 * same_d / len(cells)))
    print("    identical S14 cell %d/%d ; PC20 cell %d/%d" % (same_s14, len(cells), same_pc, len(cells)))
    print("(b) MINE  all sum %+d, same-move sum %+d" % (mine_sum, mine_smsum))
    print("    THEIRS all sum %+d, same-move sum %+d" % (their_sum, their_smsum))


if __name__ == "__main__":
    main()
