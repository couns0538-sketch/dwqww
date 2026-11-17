"""Job 3 FINAL: rank order over 2, 3 and 5 candidates, pinned-alone vs a VALIDATED
reference, with the reference's own error measured beside every denominator.

The question.  A verifier that wants a per-move number from this engine has one
tool: pin the move with `searchmoves` and read the score.  To rank 3 or 5
candidates it pins each one alone and sorts.  Does that sort equal the engine's
own sort of the same candidates?

References, each measured before it is used:
  R1  MultiPV 5, unrestricted      -- one search, but secondary lines run in a
      separate worker (src/search.cpp:2384) and its rank-1 does not always equal
      the plain search's bestmove.  VALIDATED per position: used only where
      R1 rank-1 move AND score equal the plain `go depth 12` answer.
  R3  MultiPV 5 RESTRICTED to the same 5 candidates -- same candidate set as the
      pinned arm, one search, main worker for rank 1.

Controls (a script that cannot fail proves nothing):
  * determinism: same command twice in two fresh processes must agree.
  * R1 validity: the fraction above; printed with its denominator.
  * the pinned arm MUST reproduce the plain bestmove when k=1 pins it (job2 does
    this at 60/60; repeated here for the k=2 subset).

POWER, fixed before the run:
  k=3 gives 3 pairs per position, k=5 gives 10.  At 60 positions that is 180 and
  600 pair comparisons.  For an observed proportion p with n comparisons the 95%
  Wilson half-width at p=0.90, n=180 is 0.0431 and at n=600 is 0.0240.  So a
  true rate of 0.90 is separable (95%) from 0.95 and from 0.80 at both k.  A
  perfect 180/180 has a one-sided 95% lower bound of 0.9872; 600/600 gives
  0.9950.  A rate is only called "preserved" if the lower bound clears 0.95.

Run: python3 job3/rank_final.py [--limit N] [--depth D]
Writes job3/rank_final.txt, job3/rank_final_pairs.csv
"""
import csv
import itertools
import math
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def multipv(fen, depth, k=5, restricted=None):
    opts = list(engine.S14) + [("MultiPV", str(k))]
    cmd = f"go depth {depth}"
    if restricted:
        cmd += f" searchmoves {' '.join(restricted)}"
    r = engine.run_session(f"position fen {fen}", cmd, options=opts)
    got = {}
    for line in r.raw_go.split("\n"):
        if " multipv " not in line or " pv " not in line:
            continue
        try:
            idx = int(line.split(" multipv ")[1].split()[0])
            kind = line.split(" score ")[1].split()[0]
            val = int(line.split(" score ")[1].split()[1])
            mv = line.split(" pv ")[1].split()[0]
        except (IndexError, ValueError):
            continue
        got[idx] = (val if kind == "cp" else (100000 - val if val > 0 else -100000 - val), mv)
    order = [got[i][1] for i in sorted(got)]
    return order, {got[i][1]: got[i][0] for i in got}, r


def wilson(p, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - s) / d, (c + s) / d)


def main():
    limit, depth = None, 12
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    if "--depth" in sys.argv:
        depth = int(sys.argv[sys.argv.index("--depth") + 1])

    with open(os.path.join(HERE, "..", "job1", "pinpool.epd")) as fh:
        fens = [l.strip() for l in fh if l.strip()]
    if limit:
        fens = fens[:limit]

    out = [f"engine {engine.ENGINE}", f"depth {depth}", f"positions offered {len(fens)}", ""]
    det = r1valid = mono = 0
    n = 0
    pairs = []
    pos = []

    for idx, fen in enumerate(fens):
        legal = [m.uci() for m in chess.Board(fen).legal_moves]
        got, err, _ = engine.perft1(fen)
        if got != len(legal):
            out.append(f"SKIP {fen}: perft1 {got} != {len(legal)} err={err}")
            continue
        cmdpos = f"position fen {fen}"
        p1 = engine.run_session(cmdpos, f"go depth {depth}")
        p2 = engine.run_session(cmdpos, f"go depth {depth}")
        if p1.fatal or p2.fatal:
            out.append(f"SKIP {idx}: fatal {p1.fatal}/{p2.fatal}")
            continue
        n += 1
        det += int(p1.bestmove == p2.bestmove and p1.score == p2.score)

        order1, sc1, mr1 = multipv(fen, depth, 5)
        if len(order1) < 5 or mr1.fatal:
            out.append(f"SKIP {idx}: R1 short {len(order1)}")
            continue
        valid = int(order1[0] == p1.bestmove and sc1[order1[0]] == p1.signed_score)
        r1valid += valid
        vals = [sc1[m] for m in order1]
        mono += int(all(vals[i] >= vals[i + 1] for i in range(len(vals) - 1)))

        cand = order1[:5]
        order3, sc3, mr3 = multipv(fen, depth, 5, restricted=cand)
        if len(order3) < 5 or mr3.fatal:
            out.append(f"SKIP {idx}: R3 short {len(order3)}")
            continue

        pinned = {}
        for mv in cand:
            r = engine.run_session(cmdpos, f"go depth {depth} searchmoves {mv}")
            if r.fatal or r.signed_score is None:
                out.append(f"SKIP {idx}: pinned {mv} {r.fatal}")
                break
            pinned[mv] = r.signed_score
        if len(pinned) < 5:
            continue

        per = {"idx": idx, "fen": fen, "r1valid": valid,
               "p1": p1.bestmove, "r1_first": order1[0], "r3_first": order3[0]}
        for k in (2, 3, 5):
            cc = cand[:k]
            for a, b in itertools.combinations(cc, 2):
                for ref, scores in (("R1", sc1), ("R3", sc3)):
                    same = int((scores[a] > scores[b]) == (pinned[a] > pinned[b]))
                    pairs.append(dict(idx=idx, k=k, ref=ref, a=a, b=b, same=same,
                                      base_gap=abs(scores[a] - scores[b]),
                                      base_a=scores[a], base_b=scores[b],
                                      pin_a=pinned[a], pin_b=pinned[b],
                                      r1valid=valid))
            for ref, scores in (("R1", sc1), ("R3", sc3)):
                br = sorted(cc, key=lambda m: -scores[m])
                pr = sorted(cc, key=lambda m: -pinned[m])
                pos.append(dict(idx=idx, k=k, ref=ref, exact=int(br == pr), r1valid=valid))
        out.append(f"[{idx:2d}] valid {valid} p1 {p1.bestmove} r1 {order1[0]} r3 {order3[0]}")

    out += ["", "== CONTROLS ==",
            f"determinism, same command twice, bestmove+score identical : {det}/{n}",
            f"R1 (unrestricted MultiPV) rank-1 == plain bestmove+score  : {r1valid}/{n}",
            f"R1 scores non-increasing over ranks                       : {mono}/{n}"]
    out.append(f"positions used in the agreement tables: {len({p['idx'] for p in pos})}")

    out += ["", "== RANK AGREEMENT (pinned-alone vs reference), ALL VALIDATED POSITIONS ==",
            "ref | k | pair comparisons | agree | Wilson 95% | positions | exact order"]
    for ref in ("R1", "R3"):
        for k in (2, 3, 5):
            pr = [p for p in pairs if p["ref"] == ref and p["k"] == k and p["r1valid"]]
            ps = [p for p in pos if p["ref"] == ref and p["k"] == k and p["r1valid"]]
            if not pr:
                continue
            a = sum(p["same"] for p in pr)
            lo, hi = wilson(a / len(pr), len(pr))
            out.append(f"{ref} | {k} | {len(pr)} | {a}/{len(pr)} | "
                       f"[{lo:.3f},{hi:.3f}] | {len(ps)} | {sum(p['exact'] for p in ps)}/{len(ps)}")

    out += ["", "== SAME, ONLY POSITIONS WHERE R1 IS VALIDATED, SPLIT BY BASELINE GAP =="]
    for ref in ("R1", "R3"):
        for k in (2, 3, 5):
            pr = [p for p in pairs if p["ref"] == ref and p["k"] == k and p["r1valid"]]
            for label, lo_, hi_ in (("gap>=10", 10, 10 ** 9), ("gap 1-9", 1, 9), ("gap 0", 0, 0)):
                sub = [p for p in pr if lo_ <= p["base_gap"] <= hi_]
                if sub:
                    out.append(f"{ref} k={k} {label:8s}: {sum(p['same'] for p in sub)}/{len(sub)}")

    with open(os.path.join(HERE, "rank_final_pairs.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(pairs[0].keys()))
        w.writeheader()
        w.writerows(pairs)
    text = "\n".join(out)
    with open(os.path.join(HERE, "rank_final.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
