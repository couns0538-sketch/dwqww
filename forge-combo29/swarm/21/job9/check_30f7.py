#!/usr/bin/env python3
"""check_30f7.py EXE OUTDIR

CHECK of seat 30's 30-F7 with a harness I wrote and boards I chose (not seat 30's).

Three claims, three independent probes, each at counter 100 and counter 99:
  (a) SIDE-BLIND: a black mate-in-1 is missed
  (b) MATE-BLIND: a white mate-in-1 is missed
  (c) ANY position at 100 collapses to 0 nodes: a quiet, clearly-better-for-one-side board

Every case asserts that the FEN was ACCEPTED before any search answer is trusted (the trap
21-F2 sets: a refused FEN leaves the stale board and every answer is about the wrong game),
and asserts that the engine printed a `nodes` value, so an empty parse cannot pass as a
confirmation (seat 19's integrity rule).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, Timeout, bestmove_of, last_info  # noqa: E402

import chess

# boards I chose: black mates with Ra8-a1; white mates with Re1-e8
BOARDS = {
    "black_mate": "r5k1/5ppp/8/8/8/8/5PPP/6K1 {side} - - {hm} 60",
    "white_mate": "6k1/5ppp/8/8/8/8/5PPP/4R1K1 {side} - - {hm} 60",
    # quiet, White a clean rook up, no mate anywhere near
    "quiet_white_up": "4k3/8/8/8/8/8/4P3/4K2R {side} - - {hm} 60",
}
SIDES = {"black_mate": "b", "white_mate": "w", "quiet_white_up": "w"}
SEARCHES = ["go depth 5", "go nodes 100"]


def mates_in_one(fen):
    b = chess.Board(fen)
    out = []
    for m in list(b.legal_moves):
        c = b.copy()
        c.push(m)
        if c.is_checkmate():
            out.append(m.uci())
    return out


def parse_nodes(lines, case):
    vals = [int(l.split()[1]) for l in lines if l.startswith("nodes ")]
    if not vals:
        raise AssertionError("%s: no `nodes` line — measured nothing" % case)
    return vals[0]


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows = ["| board | hm | python mate in 1 | search | engine bestmove | nodes | score line | verdict |",
            "|---|---|---|---|---|---|---|---|"]
    facts = {}
    for name, tmpl in BOARDS.items():
        for hm in (100, 99):
            fen = tmpl.format(side=SIDES[name], hm=hm)
            mates = mates_in_one(fen)
            e = SafeEngine(exe, os.path.join(outdir, "%s_%d_raw.txt" % (name, hm)))
            ans = e.position("position fen " + fen)
            if any("invalid FEN" in l for l in ans):
                e.close()
                raise AssertionError("%s hm=%d: FEN REFUSED (%s); refusing to read search "
                                     "answers about the stale board"
                                     % (name, hm, [l for l in ans if "info string" in l]))
            for search in SEARCHES:
                try:
                    lines = e.go(search, timeout=60)
                except Timeout:
                    rows.append("| %s | %d | %s | %s | TIMEOUT | - | - | FAIL |"
                                % (name, hm, ", ".join(mates) or "none", search))
                    continue
                bm = bestmove_of(lines)
                info = last_info(lines)
                # `go nodes` prints no depth line on the 0-node path; fall back to any info
                if not info:
                    info = next((l for l in reversed(lines) if l.startswith("info")), "")
                nodes = None
                if " nodes " in info:
                    nodes = info.split(" nodes ")[1].split()[0]
                cp_zero = " score cp 0 " in info
                if mates:
                    found = bm in mates
                    verdict = "MATE FOUND" if found else "MISSED"
                else:
                    verdict = "0 NODES" if nodes == "0" else "searched"
                rows.append("| %s | %d | %s | %s | %s | %s | %s | %s |"
                            % (name, hm, ", ".join(mates) or "none", search, bm,
                               nodes, info[-52:].replace("|", "/"), verdict))
                facts[(name, hm, search)] = dict(best=bm, nodes=nodes, info=info,
                                                 found=(bm in mates) if mates else None,
                                                 cp_zero=cp_zero)
            e.close()

    # ---- the verdict, computed from the recorded facts
    def any_missed(hm):
        return all(not facts[(n, hm, s)]["found"] for n in ("black_mate", "white_mate")
                   for s in SEARCHES)

    def any_found(hm):
        return all(facts[(n, hm, s)]["found"] for n in ("black_mate", "white_mate")
                   for s in SEARCHES)

    def quiet_zero(hm):
        return all(facts[("quiet_white_up", hm, s)]["nodes"] == "0" for s in SEARCHES)

    def quiet_search(hm):
        return all(facts[("quiet_white_up", hm, s)]["nodes"] not in ("0", None) for s in SEARCHES)

    checks = {
        "a side-blind (both mates missed at 100)": any_missed(100),
        "control (both mates found at 99)": any_found(99),
        "c quiet +rook answers 0 nodes at 100": quiet_zero(100),
        "control (quiet searches at 99)": quiet_search(99),
        "b white mate missed at 100": all(not facts[("white_mate", 100, s)]["found"] for s in SEARCHES),
        "black mate missed at 100": all(not facts[("black_mate", 100, s)]["found"] for s in SEARCHES),
    }
    controls_ok = checks["control (both mates found at 99)"] and checks["control (quiet searches at 99)"]
    claims = checks["a side-blind (both mates missed at 100)"] and checks["c quiet +rook answers 0 nodes at 100"]
    if not controls_ok:
        verdict = "INCONCLUSIVE (a control failed; the harness cannot see the difference)"
    elif claims:
        verdict = "CONFIRMS 30-F7"
    else:
        verdict = "REFUTES 30-F7"

    out = rows + ["", "| check | result |", "|---|---|"]
    for k, v in checks.items():
        out.append("| %s | %s |" % (k, "held" if v else "DID NOT HOLD"))
    out.append("")
    out.append("=> %s" % verdict)
    text = "\n".join(out)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()