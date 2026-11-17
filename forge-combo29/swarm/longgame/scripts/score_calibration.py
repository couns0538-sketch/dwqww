#!/usr/bin/env python3
"""Is the SCORE the session reports less accurate than the fresh score?

An analysis tool shows a number, not just a move. Ground truth is a depth-18 fresh search of
the same position. For each sampled ply we compare |d8_score - d18_score| for the session arm
and for the fresh arm.

Positive control: the same instrument is run on a deliberately shallow depth-1 score, which
must show a larger error than depth 8. If depth 1 does not look worse, the error metric is
not measuring accuracy.
"""
import sys, os, json, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evio import load_json, load_plies
from sampling import sample
from uci import Engine
from replay import run_search, pos_cmd
from checks import require

ENG = os.environ.get("FORGE_BIN", "forge-combo29/build/forge")


def load(name):
    """Per-ply records keyed by (game, ply); reads the committed short-key evidence."""
    return load_plies(name)


def val(score):
    if not score:
        return None
    kind, v = score.split()
    v = int(v)
    # Mate scores folded onto a large scale, clipped so a mate dominates any cp reading.
    return max(-20000, min(20000, v * 10000)) if kind == "mate" else v


def main():
    corpus = {g["id"]: g for g in load_json("games")["games"]}
    s = load("session")
    f = load("fresh")
    keys = sorted(f)

    picked = sample(keys, 150, seed="longgame/score_calibration/424242")
    eng = Engine(ENG)
    rows = []
    for i, k in enumerate(picked):
        g = corpus[k[0]]
        pos = pos_cmd(g, k[1])
        if i % 25 == 0:
            eng.quit(); eng = Engine(ENG); eng.uci(); eng.sync()
        truth = val(run_search(eng, pos, "go depth 18")["score"])
        # CONTROL is run in its OWN process: in this warm one a depth-1 search answers from
        # the table the depth-18 search just filled, and returns the depth-18 score
        # (measured: err 0.0 at median, which is a broken control, not a good one).
        e1 = Engine(ENG); e1.uci(); e1.sync()
        d1 = val(run_search(e1, pos, "go depth 1")["score"])
        e1.quit()
        vs, vf = val(s[k]["score"]), val(f[k]["score"])
        if None in (truth, d1, vs, vf):
            continue
        rows.append({"game": k[0], "ply": k[1], "truth_d18": truth, "d1": d1,
                     "session_d8": vs, "fresh_d8": vf,
                     "err_session": abs(vs - truth), "err_fresh": abs(vf - truth),
                     "err_d1": abs(d1 - truth)})
    eng.quit()
    json.dump(rows, open("evidence/score_calibration.json", "w", encoding="utf-8"), indent=0)

    es = [r["err_session"] for r in rows]
    ef = [r["err_fresh"] for r in rows]
    e1 = [r["err_d1"] for r in rows]
    print(f"n = {len(rows)} plies, truth = depth 18 fresh")
    print(f"  mean |err| session d8 : {sum(es)/len(es):7.1f} cp   median {statistics.median(es):6.1f}")
    print(f"  mean |err| fresh   d8 : {sum(ef)/len(ef):7.1f} cp   median {statistics.median(ef):6.1f}")
    print(f"  mean |err| depth   1  : {sum(e1)/len(e1):7.1f} cp   median {statistics.median(e1):6.1f}   <- positive control")
    require(statistics.median(e1) > statistics.median(ef),
            "error metric cannot tell depth 1 from depth 8")
    w = sum(1 for r in rows if r["err_session"] > r["err_fresh"])
    t = sum(1 for r in rows if r["err_session"] < r["err_fresh"])
    print(f"  session worse than fresh: {w}   session better: {t}   tie: {len(rows)-w-t}")
    print(f"  paired mean err difference (session - fresh): {sum(a-b for a,b in zip(es,ef))/len(es):+.1f} cp")


if __name__ == "__main__":
    main()
