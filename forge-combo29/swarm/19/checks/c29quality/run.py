#!/usr/bin/env python3
"""19-C48: independent check of seat 29's 29-F55 (PC20 vs S14 move quality, depth 14).

Design decisions, fixed before running (see PREDICTION.md):
  - positions: R_2911.fens ODD lines only (1,3,5,...) -> 200 positions, my own slice
  - S14 vs PC20, Threads 1, Hash 16, fresh process per search, drained to bestmove
  - each disagreement judged under the NEUTRAL S14 regime at depth 17, both moves played
  - the mover's score = -(score of the resulting position), since the opponent is to move
Report:
  - agreement count and denominator EXPLICITLY checked against the number of differing bestmoves
  - judged tally, plus the same tally restricted to cp-only judgements (seat 29's trap 2)
"""
import subprocess, sys, os, hashlib, re, json

PCPATH = os.path.expanduser("~/pcbuild/build/forge")
BASEPATH = os.path.expanduser("~/build_rel/forge")
FENS = "/home/ubuntu/peerchk/29/R_2911.fens"
OUTDIR = os.path.dirname(os.path.abspath(__file__))

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

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def run(exe, fen, opts, depth, moves=()):
    """One search, fresh process, drained to bestmove. Returns (bestmove, score, pv_len, depth, nodes)."""
    lines = []
    for k, v in opts:
        lines.append("setoption name %s value %s" % (k, v))
    for m in moves:
        pass
    # TRAP 1/3c: piping the whole script and closing stdin sends EOF during the search, which aborts it
    # and makes the engine return a legal but FABRICATED bestmove with no info lines. The tell is exactly
    # what I saw: bestmove only, score None, 95 ms. So: keep stdin OPEN, read until bestmove, then quit.
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    for ln in lines:
        send(ln)
    send("isready")
    send("position fen %s%s" % (fen, (" moves " + " ".join(moves)) if moves else ""))
    send("isready")
    send("go depth %d" % depth)

    collected = []
    while True:
        ln = p.stdout.readline()
        if not ln:
            break
        collected.append(ln.rstrip("\n"))
        if ln.startswith("bestmove"):
            break
    try:
        send("quit")
        p.wait(timeout=30)
    except Exception:
        p.kill()
    out = "\n".join(collected)
    for b in BAD:
        if b in out:
            raise RuntimeError("harness guard tripped: %r in output\n%s" % (b, out[:2000]))
    best, score, dep, nodes, pvlen = None, None, None, None, 0
    for ln in out.splitlines():
        t = ln.split()
        if not t:
            continue
        if t[0] == "bestmove":
            best = t[1]
        elif t[0] == "info" and " pv " in ln:
            # last complete info line describing the final PV
            m = re.search(r"\bscore (cp|mate) (-?\d+)", ln)
            if m:
                score = (m.group(1), int(m.group(2)))
            m = re.search(r"\bdepth (\d+)", ln)
            if m:
                dep = int(m.group(1))
            m = re.search(r"\bnodes (\d+)", ln)
            if m:
                nodes = int(m.group(1))
            pvlen = len(ln.split(" pv ")[1].split())
    # TRAP 1/3c closing check: a search happened only if nodes > 0 AND a PV exists.
    if nodes is None or nodes == 0 or pvlen == 0 or score is None:
        raise RuntimeError(
            "no real search happened (nodes=%r pvlen=%r score=%r best=%r) - "
            "this is the fabricated-bestmove trap, not a result\nOUTPUT:\n%s"
            % (nodes, pvlen, score, best, out[:1500]))
    return best, score, pvlen, dep, nodes


def meta():
    m = {}
    for tag, path in (("pc20", PCPATH), ("base", BASEPATH)):
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        p = subprocess.run([path], input="uci\nquit\n", capture_output=True, text=True)
        name = [l for l in p.stdout.splitlines() if l.startswith("id name")]
        m[tag] = {"exe": path, "sha256": h, "id": name[0] if name else "?"}
    m["s14"] = S14
    m["pc20_extra"] = PC20EXTRA
    return m


def main():
    pos = [l.strip() for l in open(FENS) if l.strip()]
    slice_ = pos[0::2][:200]
    json.dump(meta(), open(os.path.join(OUTDIR, "run.meta"), "w"), indent=1)

    rows = []
    agree = 0
    for i, fen in enumerate(slice_):
        b_s14, s_s14, pvl1, d1, n1 = run(BASEPATH, fen, S14, 14)
        b_pc, s_pc, pvl2, d2, n2 = run(PCPATH, fen, S14 + PC20EXTRA, 14)
        same = (b_s14 == b_pc)
        if same:
            agree += 1
        rows.append({"i": i, "fen": fen, "s14": b_s14, "pc20": b_pc, "same": same,
                     "s14_score": s_s14, "pc20_score": s_pc, "nodes_s14": n1, "nodes_pc20": n2})
        if (i + 1) % 20 == 0:
            print("searched %d/%d, agree %d" % (i + 1, len(slice_), agree), flush=True)

    # sanity: agreement denominator must match the actual count of identical bestmoves
    n_same = sum(1 for r in rows if r["same"])
    assert n_same == agree, "agreement bookkeeping error"

    dis = [r for r in rows if not r["same"]]
    print("\nAGREEMENT %d of %d = %.1f %%" % (agree, len(rows), 100.0 * agree / len(rows)), flush=True)
    print("DISAGREEMENTS %d" % len(dis), flush=True)

    judged = []
    for r in dis:
        # play each move, judge the RESULTING position under neutral S14 at depth 17
        _, sc_a, _, _, _ = run(BASEPATH, r["fen"], S14, 17, moves=[r["s14"]])
        _, sc_b, _, _, _ = run(BASEPATH, r["fen"], S14, 17, moves=[r["pc20"]])
        # opponent is to move after our move, so our score is the negation
        def to_mover(sc):
            if sc is None:
                return None
            kind, v = sc
            if kind == "mate":
                # mate 0 means we are mated; negate and keep mate semantics
                return ("mate", -v)
            return ("cp", -v)
        ma, mb = to_mover(sc_a), to_mover(sc_b)

        def better(x, y):
            """+1 if x better for the mover than y, -1 if worse, 0 tie. Mate scores dominate cp."""
            if x is None or y is None:
                return 0
            if x[0] == "mate" and y[0] != "mate":
                return 1 if x[1] > 0 else -1
            if y[0] == "mate" and x[0] != "mate":
                return -1 if y[1] > 0 else 1
            if x[0] == "mate" and y[0] == "mate":
                if x[1] == y[1]:
                    return 0
                return 1 if x[1] > y[1] else -1
            if abs(x[1] - y[1]) <= 0:
                return 0
            return 1 if x[1] > y[1] else -1

        w = better(mb, ma)  # +1 -> PC20's move better
        judged.append({"i": r["i"], "fen": r["fen"], "s14": r["s14"], "pc20": r["pc20"],
                       "score_s14_move": ma, "score_pc20_move": mb, "winner": w,
                       "cp_only": (ma and mb and ma[0] == "cp" and mb[0] == "cp")})
        print("judged %s vs %s -> %+d" % (r["s14"], r["pc20"], w), flush=True)

    n = len(judged)
    pw = sum(1 for j in judged if j["winner"] > 0)
    sw = sum(1 for j in judged if j["winner"] < 0)
    ti = n - pw - sw
    cpj = [j for j in judged if j["cp_only"]]
    cpw = sum(1 for j in cpj if j["winner"] > 0)
    csw = sum(1 for j in cpj if j["winner"] < 0)

    with open(os.path.join(OUTDIR, "raw_result.txt"), "w") as f:
        f.write("19-C48 independent check of 29-F55 | builds: %s : %s\n" % (
            PCPATH, meta()["pc20"]["sha256"]))
        f.write("positions: R_2911.fens odd lines 1,3,5,... -> %d\n\n" % len(rows))
        f.write("AGREEMENT %d of %d = %.2f %%\n" % (agree, len(rows), 100.0 * agree / len(rows)))
        f.write("DISAGREEMENTS %d\n\n" % n)
        f.write("judged under neutral S14, depth 17:\n")
        f.write("  PC20 better %d | S14 better %d | tie %d\n" % (pw, sw, ti))
        f.write("  cp-only judgements: PC20 %d | S14 %d\n\n" % (cpw, csw))
        f.write("per-position:\n")
        for r in rows:
            f.write("  %3d %s s14=%s pc20=%s %s n=%s/%s\n" % (
                r["i"], r["fen"], r["s14"], r["pc20"], "SAME" if r["same"] else "DIFF",
                r["nodes_s14"], r["nodes_pc20"]))
        f.write("\njudgements:\n")
        for j in judged:
            f.write("  %3d %s vs %s  s14move=%s pc20move=%s winner=%+d\n" % (
                j["i"], j["s14"], j["pc20"], j["score_s14_move"], j["score_pc20_move"], j["winner"]))
    print("\nPC20 better %d | S14 better %d | tie %d  (cp-only %d/%d)" % (pw, sw, ti, cpw, csw))


if __name__ == "__main__":
    main()
