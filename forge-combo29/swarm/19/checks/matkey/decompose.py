#!/usr/bin/env python3
"""19-C65: is the 27.7 % vs 52.5 % sign-share gap a BUDGET effect or a DEFINITION effect?

The two figures came from DIFFERENT samples (36/130 at 50k; 21/40 at 500k), so they were never
comparable. This runs the SAME 40 positions at BOTH budgets and decomposes every pair into
WIN / TIE / LOSS, so the tie fraction is explicit rather than hidden inside the non-win count.
"""
import subprocess, os, re, statistics as st, math

CTRL = "/home/ubuntu/mk/ctrl/forge-combo29/build/forge"
PF = "/home/ubuntu/mk/work/forge-combo29/build/forge"
FENS = "/agent/repos/dwqww/forge-combo29/swarm/19/checks/softgran/their_600.fens"
HERE = os.path.dirname(os.path.abspath(__file__))
NPOS = int(os.environ.get("NPOS", "40"))


def run(exe, fen, nodes):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    for s in ["position fen " + fen, "isready", "go nodes %d" % nodes]:
        p.stdin.write(s + "\n"); p.stdin.flush()
    coll = []
    while True:
        ln = p.stdout.readline()
        if not ln:
            break
        coll.append(ln.rstrip())
        if ln.startswith("bestmove"):
            break
    try:
        p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=90)
    except Exception:
        p.kill()
    n = t = None
    for ln in coll:
        if ln.startswith("info") and " pv " in ln:
            m = re.search(r"\bnodes (\d+)", ln)
            if m: n = int(m.group(1))
            m = re.search(r"\btime (\d+)", ln)
            if m: t = int(m.group(1))
    return n, t


def main():
    fens = [l.strip() for l in open(FENS) if l.strip()][:NPOS]
    out = []
    for budget in (50000, 500000):
        rows = []
        for i, fen in enumerate(fens):
            if i % 2 == 0:
                a = run(CTRL, fen, budget); b = run(PF, fen, budget)
            else:
                b = run(PF, fen, budget); a = run(CTRL, fen, budget)
            if a[1] and b[1]:
                rows.append((a, b))
        wins = sum(1 for a, b in rows if b[1] < a[1])
        ties = sum(1 for a, b in rows if b[1] == a[1])
        loss = sum(1 for a, b in rows if b[1] > a[1])
        med = st.median(a[1] for a, b in rows)
        ratios = [(b[1] / b[0]) / (a[1] / a[0]) for a, b in rows]
        g = math.exp(st.mean([math.log(x) for x in ratios]))
        out.append("BUDGET %d  (n=%d, median search %.0f ms)" % (budget, len(rows), med))
        out.append("  PF faster %d | EXACT TIE %d (%.1f %%) | PF slower %d" % (
            wins, ties, 100.0 * ties / len(rows), loss))
        out.append("  strict sign-share (wins / all)      = %d/%d = %.1f %%" % (wins, len(rows), 100.0 * wins / len(rows)))
        out.append("  wins / decided (ties excluded)      = %d/%d = %.1f %%" % (
            wins, wins + loss, 100.0 * wins / (wins + loss) if wins + loss else 0))
        out.append("  geometric per-node ratio %.4f" % g)
        out.append("")
        print("\n".join(out[-5:]), flush=True)
    out.append("READ: if the TIE fraction collapses at the longer budget, the two sign-shares differ because")
    out.append("      1 ms resolution creates ties at 50k - a DEFINITION effect, not a budget effect.")
    open(os.path.join(HERE, "decompose_result.txt"), "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
