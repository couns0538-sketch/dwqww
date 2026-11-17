#!/usr/bin/env python3
"""Is the in-process answer WORSE than the fresh answer, or only different?

A different bestmove at depth 8 is only a defect if it is a worse move. The oracle here is
a deeper search of the SAME position in a FRESH process (depth 14), which is independent of
both the session's warm table and the depth-8 fresh answer.

Two-sided: for each diverging ply where the session and fresh depth-8 answers differ, ask
the depth-14 fresh search to score BOTH moves from the same root. Report the score difference
(session move minus fresh move), so a positive number means the session's move is BETTER.
"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evio import load_json, load_plies
from uci import Engine
from replay import run_search, pos_cmd

ENG = os.environ.get("FORGE_BIN", "forge-combo29/build/forge")
DEEP = "go depth 14"


def load(name):
    """Per-ply records keyed by (game, ply); reads the committed short-key evidence."""
    return load_plies(name)


def main():
    corpus = {g["id"]: g for g in load_json("games")["games"]}
    s = load("session")
    f = load("fresh")
    div = [k for k in sorted(f) if s[k]["bm"] != f[k]["bm"]]
    print(f"diverging plies in the 40-game sample: {len(div)}")

    random.seed(20261117)
    sample = random.sample(div, 200)
    rows = []
    eng = Engine(ENG)
    for i, k in enumerate(sample):
        g = corpus[k[0]]
        pos = pos_cmd(g, k[1])
        if i % 20 == 0:
            eng.quit(); eng = Engine(ENG); eng.uci(); eng.sync()
        sm, fm = s[k]["bm"], f[k]["bm"]
        r1 = run_search(eng, pos + f" searchmoves {sm}", DEEP)
        r2 = run_search(eng, pos + f" searchmoves {fm}", DEEP)
        def val(r):
            if not r["score"]:
                return None
            kind, v = r["score"].split()
            v = int(v)
            # mate scores: fold into a large finite scale so differences are orderable
            return v * 10000 if kind == "mate" else v
        v1, v2 = val(r1), val(r2)
        rows.append({"game": k[0], "ply": k[1], "session_bm": sm, "fresh_bm": fm,
                     "deep_session_move": v1, "deep_fresh_move": v2,
                     "delta": None if (v1 is None or v2 is None) else v1 - v2,
                     "d8_session": s[k]["score"], "d8_fresh": f[k]["score"]})
    eng.quit()
    json.dump(rows, open("evidence/move_quality.json", "w"), indent=0)

    d = [r["delta"] for r in rows if r["delta"] is not None]
    d.sort()
    import statistics
    print(f"n={len(d)} (of {len(rows)}; missing where a move score failed)")
    print(f"  session move better: {sum(1 for x in d if x>0)}")
    print(f"  equal:               {sum(1 for x in d if x==0)}")
    print(f"  session move worse:  {sum(1 for x in d if x<0)}")
    print(f"  median delta {statistics.median(d):+.0f} cp, mean {sum(d)/len(d):+.0f}, "
          f"p10 {d[len(d)//10]:+.0f}, p90 {d[int(.9*len(d))]:+.0f}, min {d[0]:+.0f}, max {d[-1]:+.0f}")
    big = [x for x in d if abs(x) >= 100]
    print(f"  |delta| >= 100 cp: {len(big)} of {len(d)} ({100*len(big)/len(d):.1f}%)")


if __name__ == "__main__":
    main()
