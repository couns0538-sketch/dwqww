#!/usr/bin/env python3
"""fl_distribution.py - Opus R14-B: compare what the live loader configuration (old DLL, --num-workers 4: three
decode workers, each with its own adaptive piece-count filter state; not reproducible) feeds the trainer with what
the fast loader feeds it (= the old --num-workers 1 stream), as distributions over many batches (own code, stdlib).

usage: python -I -B fl_distribution.py stats --loader old|fast --dll D --workers N --batches 2000 --out X.json
       python -I -B fl_distribution.py compare A.json B.json
Per batch it accumulates: piece count (0-32), side to move, outcome (0 / 0.5 / 1), queen bucket (0-3), score in
100-cp bins (clipped to +-3000) and the score sum / sum of squares. compare prints the total-variation distance per
histogram, a chi-square statistic with its degrees of freedom, and the score mean difference in standard errors
(batch-to-batch spread, since positions inside one shuffle window are not independent).
"""

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fl_equal  # noqa: E402  (stream classes, low priority, peak memory)


def stats(a) -> int:
    fl_equal.need_new_output(a.out)  # before the run, not after it (bug hunt #16)
    for path, what in ((a.dll, "--dll"), (a.data, "--data")):
        if not os.path.isfile(path):
            fl_equal.fail(f"{what} {path}: file not found")
    fl_equal.set_low(a.mask, a.priority)
    cls = fl_equal.OldStream if a.loader == "old" else fl_equal.NewStream
    st = cls(a.dll, a.data, a.batch, a.workers, True, a.window, fl_equal.make_skip(""))
    import numpy as np

    h = {"piece_count": np.zeros(33, np.int64), "stm_white": np.zeros(2, np.int64), "outcome": np.zeros(3, np.int64),
         "queen_bucket": np.zeros(4, np.int64), "score_bin": np.zeros(61, np.int64)}
    batch_means = []
    n_total = 0
    for _ in range(a.batches):
        p = st.next()
        if p is None:
            break
        b = p.contents
        n = b.size
        fl = np.ctypeslib.as_array(b.is_white, shape=(3 * n,))
        pc = np.ctypeslib.as_array(b.piece_count, shape=(n,))
        qb = np.ctypeslib.as_array(b.queen_bucket, shape=(n,))
        score = fl[2 * n:3 * n].astype(np.float64)
        h["piece_count"] += np.bincount(pc, minlength=33)[:33]
        h["stm_white"] += np.bincount((fl[:n] == 1.0).astype(np.int64), minlength=2)
        h["outcome"] += np.bincount(np.rint(fl[n:2 * n] * 2).astype(np.int64), minlength=3)[:3]
        h["queen_bucket"] += np.bincount(qb, minlength=4)[:4]
        h["score_bin"] += np.bincount(((np.clip(score, -3000, 3000) + 3000) // 100).astype(np.int64), minlength=61)[:61]
        batch_means.append(float(score.mean()))
        n_total += n
        st.release(p)
    st.close()
    h = {k: [int(x) for x in v] for k, v in h.items()}
    m = sum(batch_means) / len(batch_means)
    sd = math.sqrt(sum((x - m) ** 2 for x in batch_means) / max(1, len(batch_means) - 1))
    out = {"loader": a.loader, "dll": os.path.abspath(a.dll), "workers": a.workers, "batches": len(batch_means),
           "positions": n_total, "hist": h, "score_mean": m, "score_mean_se": sd / math.sqrt(len(batch_means)),
           "peak_working_set_mb": round(fl_equal.peak_working_set_mb(), 1)}
    with open(a.out, "x", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1)
    print(f"{a.loader} w{a.workers}: {len(batch_means)} batches, score mean {m:.2f} +- {out['score_mean_se']:.2f}")
    return 0


def load_stats(path):
    """A stats file written by `stats`; exit 2 with a clear line otherwise (bug hunt #16: was a traceback)."""
    try:
        with open(path, encoding="utf-8") as f:
            s = json.load(f)
        missing = [k for k in ("loader", "workers", "positions", "hist", "score_mean", "score_mean_se") if k not in s]
        if missing:
            raise KeyError(", ".join(missing))
        if not s["hist"] or not all(sum(h) > 0 for h in s["hist"].values()) or s["positions"] <= 0:
            raise ValueError("empty histograms")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
        fl_equal.fail(f"{path}: not a fl_distribution.py stats file ({type(e).__name__}: {e})")
    return s


def compare(pa, pb) -> int:
    A, B = load_stats(pa), load_stats(pb)
    if {k: len(v) for k, v in A["hist"].items()} != {k: len(v) for k, v in B["hist"].items()}:
        fl_equal.fail(f"{pa} and {pb} hold different histograms: not comparable")
    print(f"A = {A['loader']} w{A['workers']} ({A['positions']:,} positions), B = {B['loader']} w{B['workers']} "
          f"({B['positions']:,})")
    for key in A["hist"]:
        ha, hb = A["hist"][key], B["hist"][key]
        na, nb = sum(ha), sum(hb)
        tv = 0.5 * sum(abs(x / na - y / nb) for x, y in zip(ha, hb))
        chi, dof = 0.0, -1
        for x, y in zip(ha, hb):
            if x + y == 0:
                continue
            e_a = (x + y) * na / (na + nb)
            e_b = (x + y) * nb / (na + nb)
            chi += (x - e_a) ** 2 / e_a + (y - e_b) ** 2 / e_b
            dof += 1
        print(f"  {key:13s} total-variation {tv:.5f}  chi-square {chi:,.1f} on {dof} dof")
    d = A["score_mean"] - B["score_mean"]
    se = math.hypot(A["score_mean_se"], B["score_mean_se"])
    print(f"  score mean   {A['score_mean']:.2f} vs {B['score_mean']:.2f}: difference {d:+.2f} = {d / se:+.2f} SE")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stats")
    s.add_argument("--loader", choices=["old", "fast"], required=True)
    s.add_argument("--dll", required=True)
    s.add_argument("--workers", type=int, required=True)
    s.add_argument("--data", default=r"F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack")
    s.add_argument("--batch", type=int, default=16384)
    s.add_argument("--window", type=int, default=1048576)
    s.add_argument("--batches", type=int, default=2000)
    s.add_argument("--out", required=True)
    s.add_argument("--mask", default="0xC")
    s.add_argument("--priority", default="BelowNormal", choices=["BelowNormal", "Idle"])
    c = sub.add_parser("compare")
    c.add_argument("a")
    c.add_argument("b")
    a = ap.parse_args()
    return stats(a) if a.cmd == "stats" else compare(a.a, a.b)


if __name__ == "__main__":
    sys.exit(main())
