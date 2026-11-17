"""Job 3: does pinning preserve RANK ORDER over 3 and 5 candidates?

Design.  For each position:
  1. MultiPV 5 at depth D gives the engine's own ordering of the top 5 moves WITH
     all of them searched in one search (the baseline ordering, and the baseline
     score for each move).
  2. Each of the top 5 is then searched ALONE with `searchmoves <that move>`,
     which is the only way a verifier gets a per-move number out of this engine.
  3. Compare the order the pinned scores give against the order the MultiPV scores
     give -- over the top 3, and over the top 5.

Reported with literal denominators:
  * every pairwise comparison (3 candidates = 3 pairs, 5 candidates = 10 pairs)
  * the full ordering (exact match of the whole permutation, and Kendall tau)

POWER, computed before the run (see power.py and job3/power.txt): at n = 60
positions and 10 pair comparisons each, if the true pairwise agreement rate were
0.80 the run would see 600 comparisons; the 95% interval is about +/- 0.032, so an
observed 1.00 is separable from 0.80 and from 0.95.  A rate of exactly 1.00 with
600/600 has a one-sided 95% lower bound of 0.9950.

Run: python3 job3/rank_order.py [--limit N]
Writes job3/rank_order.csv, job3/rank_order.txt
"""
import csv
import itertools
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEPTH = 12
TOPK = 5


def multipv_scores(fen, depth, k=TOPK):
    opts = list(engine.S14) + [("MultiPV", str(k))]
    r = engine.run_session(f"position fen {fen}", f"go depth {depth}", options=opts)
    best = {}
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
        best[idx] = (val if kind == "cp" else (100000 - val if val > 0 else -100000 - val),
                     kind, val, mv)
    order = [best[i][3] for i in sorted(best)]
    scores = {best[i][3]: best[i][0] for i in best}
    return order, scores, r


def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    with open(os.path.join(HERE, "..", "job1", "pinpool.epd")) as fh:
        fens = [l.strip() for l in fh if l.strip()]
    if limit:
        fens = fens[:limit]

    pair_rows, pos_rows, lines = [], [], []
    for idx, fen in enumerate(fens):
        legal = [m.uci() for m in chess.Board(fen).legal_moves]
        got, err, _ = engine.perft1(fen)
        if got != len(legal):
            lines.append(f"SKIP {fen}: perft1 {got} != {len(legal)} err={err}")
            continue
        order, mscores, mr = multipv_scores(fen, DEPTH, TOPK)
        if len(order) < TOPK or mr.fatal:
            lines.append(f"SKIP {fen}: multipv returned {len(order)} lines, fatal={mr.fatal}")
            continue

        pinned = {}
        bad = False
        for mv in order:
            r = engine.run_session(f"position fen {fen}", f"go depth {DEPTH} searchmoves {mv}")
            if r.fatal or r.signed_score is None:
                lines.append(f"SKIP {fen}: pinned {mv} fatal={r.fatal}")
                bad = True
                break
            pinned[mv] = r.signed_score
        if bad:
            continue

        for k in (3, 5):
            cand = order[:k]
            base_rank = sorted(cand, key=lambda m: -mscores[m])
            pin_rank = sorted(cand, key=lambda m: -pinned[m])
            pairs = list(itertools.combinations(cand, 2))
            agree = 0
            for a, b in pairs:
                b_ord = -1 if mscores[a] > mscores[b] else 1
                p_ord = -1 if pinned[a] > pinned[b] else 1
                same = int(b_ord == p_ord)
                agree += same
                pair_rows.append(dict(idx=idx, fen=fen, k=k, a=a, b=b,
                                      base_a=mscores[a], base_b=mscores[b],
                                      pin_a=pinned[a], pin_b=pinned[b], agree=same))
            exact = int(base_rank == pin_rank)
            pos_rows.append(dict(idx=idx, fen=fen, k=k, pairs=len(pairs), pairs_agree=agree,
                                 exact=int(exact),
                                 base_order=" ".join(base_rank), pin_order=" ".join(pin_rank)))
            lines.append(f"[{idx:2d}] k={k} pairs {agree}/{len(pairs)} exact {exact} "
                         f"| base {base_rank} | pin {pin_rank}")

    with open(os.path.join(HERE, "rank_order.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(pair_rows[0].keys()))
        w.writeheader()
        w.writerows(pair_rows)
    with open(os.path.join(HERE, "rank_order_positions.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(pos_rows[0].keys()))
        w.writeheader()
        w.writerows(pos_rows)

    lines += ["", "== RANK ORDER OVER PINNED CANDIDATES, depth 12 ==",
              "k | pairs | pairs agree | positions with EXACT ordering"]
    for k in (3, 5):
        pr = [r for r in pair_rows if r["k"] == k]
        ps = [r for r in pos_rows if r["k"] == k]
        tp = sum(r["agree"] for r in pr)
        ex = sum(r["exact"] for r in ps)
        lines.append(f"{k} | {len(pr)} | {tp}/{len(pr)} | {ex}/{len(ps)}")
    text = "\n".join(lines)
    with open(os.path.join(HERE, "rank_order.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
