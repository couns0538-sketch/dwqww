#!/usr/bin/env python3
"""swarm seat 01: is i=16's 18.4x work VERIFICATION or WASTE? Compare the PVs that did not exist before (S-C48).

i=16: PC20 spends 18.4x the nodes of S14 (238,009 vs 12,957) and reports the SAME score (`mate -3`) at the same
reported depth, seldepth 25 -> 51. Two explanations, and they are distinguishable:

  (a) VERIFICATION. PC20's principal variation contains a defence or resource that S14 never examined. Then the extra
      nodes buy a searched refutation of a line S14 left unexamined, and the identical score is better-founded.
  (b) WASTE. The PVs are the same line, and PC20 merely explored more siblings that changed nothing.

The test: capture the FULL PV at every depth for both settings and find the first depth where they diverge, then look
at what PC20's line contains that S14's does not. A divergence that names DIFFERENT BLACK (defending) moves in the same
position means PC20 examined a defence S14 did not. A divergence only in ordering/transposition of the same moves
means the same line.

Design notes from traps already paid for:
  * every depth's PV is captured, not just the last, because "diverges at depth k" is the question;
  * the move lists are compared as SEQUENCES, and also as SETS of defending moves, so "same line, different order" is
    distinguishable from "different resource";
  * this is one position analysed at one depth, so the conclusion is about i=16 and nothing wider.

Usage: pv_diverge.py <exe> <fen> <max-depth> <outdir>
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def pvs(exe, fen, opts, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, cwd="/tmp")

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pre):
        for line in p.stdout:
            if line.startswith(pre):
                return line.rstrip("\n")
        return None

    send("uci")
    until("uciok")
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    for n, v in opts:
        send("setoption name %s value %s" % (n, v))
    send("isready")
    until("readyok")
    send("ucinewgame")
    send("isready")
    until("readyok")
    send("position fen " + fen)
    send("isready")
    until("readyok")
    send("go depth %d" % depth)
    rows = []
    for line in p.stdout:
        line = line.rstrip("\n")
        if line.startswith("info depth") and " pv " in line:
            f = line.split()
            try:
                d = int(f[2])
                sd = int(f[4])
                sc = "%s %s" % (f[6], f[7])
                nodes = int(f[9])
            except (IndexError, ValueError):
                continue
            pv = f[f.index("pv") + 1:]
            rows.append({"depth": d, "seldepth": sd, "score": sc, "nodes": nodes, "pv": pv})
        if line.startswith("bestmove"):
            break
    send("quit")
    try:
        p.wait(timeout=120)
    except Exception:
        p.kill()
    return rows


def first_divergence(a, b):
    """The shallowest depth where the two PVs differ in their move sequence, restricted to depths both reached."""
    by_d_a = {r["depth"]: r for r in a}
    by_d_b = {r["depth"]: r for r in b}
    for d in sorted(set(by_d_a) & set(by_d_b)):
        if by_d_a[d]["pv"] != by_d_b[d]["pv"]:
            return d
    return None


def main():
    exe, fen, maxdepth, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), Path(sys.argv[4])
    out.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    a = pvs(exe, fen, S14, maxdepth)
    b = pvs(exe, fen, PC20, maxdepth)

    L = ["S-C48: is i=16's 18.4x work verification or waste? Full PV comparison.",
         "exe: %s" % exe, "sha256: %s" % sha, "fen: %s" % fen,
         "go depth %d, Threads 1, Hash 16, every depth's PV captured." % maxdepth, ""]
    L.append("depth\tscore S14\tnodes S14\tscore PC20\tnodes PC20\tPV S14\tPV PC20")
    da = {r["depth"]: r for r in a}
    db = {r["depth"]: r for r in b}
    for d in sorted(set(da) | set(db)):
        ra, rb = da.get(d), db.get(d)
        L.append("%d\t%s\t%s\t%s\t%s\t%s\t%s"
                 % (d,
                    ra["score"] if ra else "-", ra["nodes"] if ra else "-",
                    rb["score"] if rb else "-", rb["nodes"] if rb else "-",
                    " ".join(ra["pv"]) if ra else "-",
                    " ".join(rb["pv"]) if rb else "-"))
    L.append("")

    k = first_divergence(a, b)
    if k is None:
        L.append("PVs identical at every shared depth - the extra nodes bought no change in the line.")
    else:
        L.append("FIRST DIVERGENCE at depth %d" % k)
        if k in da and k in db:
            L.append("  S14  : %s   (%s, %d nodes)" % (" ".join(da[k]["pv"]), da[k]["score"], da[k]["nodes"]))
            L.append("  PC20 : %s   (%s, %d nodes)" % (" ".join(db[k]["pv"]), db[k]["score"], db[k]["nodes"]))
            pa, pb = da[k]["pv"], db[k]["pv"]
            # which side's moves appear only in one line
            only_b = [m for m in pb if m not in pa]
            only_a = [m for m in pa if m not in pb]
            L.append("  moves only in S14's line : %s" % (" ".join(only_a) or "none"))
            L.append("  moves only in PC20's line: %s" % (" ".join(only_b) or "none"))
            L.append("  same move SET: %s" % ("yes" if set(pa) == set(pb) else "no"))
            L.append("")
            if set(pa) == set(pb):
                L.append("VERDICT: WASTE - the same set of moves in a different order. PC20 re-ordered an existing")
                L.append("  line rather than examining a new one; the extra nodes bought no new resource.")
            elif only_b:
                L.append("VERDICT: VERIFICATION - PC20's line contains %d move(s) S14's does not, so the extra work"
                         % len(only_b))
                L.append("  examined resources outside S14's tree. The identical score is better-founded under PC20,")
                L.append("  because it survived defences S14 never looked at.")
            else:
                L.append("VERDICT: S14's line is a superset - unexpected; inspect by hand.")
    (out / "pv_diverge.json").write_text(json.dumps({"sha": sha, "fen": fen, "s14": a, "pc20": b,
                                                      "first_divergence": k}, indent=1))
    txt = "\n".join(L) + "\n"
    (out / "pv_diverge.txt").write_text(txt)
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
