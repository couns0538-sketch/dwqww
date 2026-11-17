"""Probe Q: the upper bound on the post-ponderhit budget, over 16 offsets.

The single most decisive measurement in this audit, and the cheapest to
mis-read. The engine's clock plan for `wtime T btime T` with Move Overhead 10,
TmSoftDivisor 22, TmHardPercent 60, TmHardSoftMultiple 5 is

    usable = T - 10
    soft   = usable / 22
    hard   = min(usable * 60 / 100, soft * 5)

If the budget were measured from the original `go`, then after a ponder longer
than `hard` there would be nothing left and `ponderhit` would return instantly.
The prediction of that hypothesis is hit->best ~= 0 for every long ponder.

Instead the sweep puts the hit at different points inside the iteration and
reports hit->best against `hard`. The claim this probe supports is an UPPER
BOUND, not an equality: hit->best never exceeded hard + 1.1 ms in 16 offsets,
which is the signature of a budget that (a) starts at the hit and (b) is capped
by the hard limit. It is NOT "hit->best == hard"; most rows stop earlier, at the
soft deadline or at the end of the iteration in progress.
"""

import argparse
import json
import os
import time

from uci_driver import Engine, bestmoves, info_lines, is_bestmove

FEN_A = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 6 6"
BASE = [("OwnBook", "false"), ("Threads", "1"), ("Hash", "32"), ("Move Overhead", "10")]


def fresh(exe):
    e = Engine(exe)
    e.uci_handshake()
    for n, v in BASE:
        e.set_option(n, v)
    return e


def infos(lines):
    return [i for _, i in info_lines(lines) if i and "depth" in i]


def plan(clock):
    usable = clock - 10
    soft = usable // 22
    hard = min(usable * 60 // 100, soft * 5)
    return soft, hard


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="/tmp/forge-build/forge")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "evidence"))
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    rows = []
    for clock in (2000, 10000):
        soft, hard = plan(clock)
        for ps in (0.3, 0.5, 0.8, 1.2, 1.8, 2.5, 3.5, 5.0):
            e = fresh(args.exe)
            try:
                e.send(f"position fen {FEN_A}")
                mark = e.mark()
                e.send(f"go ponder wtime {clock} btime {clock}")
                time.sleep(ps)
                pre = infos(e.since(mark))
                t_hit = e.send("ponderhit")
                got = e.wait_for(is_bestmove, 40.0, mark)
                if got is None:
                    rows.append({"clock": clock, "ponder_s": ps, "verdict": "CAPPED"})
                    e.kill()
                    continue
                post = infos(e.since(mark))
                hb = round((got[0].t - t_hit) * 1000.0, 1)
                rows.append({
                    "clock": clock, "soft_ms": soft, "hard_ms": hard,
                    "ponder_s": ps, "verdict": "RETURNED",
                    "t_hit_to_best_ms": hb,
                    "over_hard_ms": round(hb - hard, 1),
                    "within_hard": hb <= hard + 1.5,
                    "over_soft": hb > soft,
                    "iterations_after_hit": len(post) - len(pre),
                    "depth_at_hit": pre[-1]["depth"] if pre else None,
                    "bestmove": got[0].text.split()[1],
                    "bestmove_count": len(bestmoves(e.since(mark))),
                })
            finally:
                e.close()

    finished = [r for r in rows if r["verdict"] == "RETURNED"]
    summary = {
        "n": len(finished),
        "max_over_hard_ms": max((r["over_hard_ms"] for r in finished), default=None),
        "all_within_hard": all(r["within_hard"] for r in finished),
        "rows_over_soft": sum(1 for r in finished if r["over_soft"]),
        "n_zero_ms": sum(1 for r in finished if r["t_hit_to_best_ms"] < 5.0),
    }
    res = {"q_budget_upper_bound": {"rows": rows, "summary": summary}}
    path = os.path.join(out, "probe9_results.json")
    with open(path, "w") as fh:
        json.dump(res, fh, indent=2, sort_keys=True)

    print(f"{'clock':>6}{'soft':>6}{'hard':>6}{'ponder':>8}{'hit->best':>11}"
          f"{'over hard':>11}{'iters':>7}")
    for r in finished:
        print(f"{r['clock']:>6}{r['soft_ms']:>6}{r['hard_ms']:>6}{r['ponder_s']:>8}"
              f"{r['t_hit_to_best_ms']:>11}{r['over_hard_ms']:>11}{r['iterations_after_hit']:>7}")
    print()
    print(f"n = {summary['n']}")
    print(f"max(hit->best - hard) = {summary['max_over_hard_ms']} ms")
    print(f"every row within hard + 1.5 ms: {summary['all_within_hard']}")
    print(f"rows that stopped at ~0 ms (the 'budget already spent' prediction): "
          f"{summary['n_zero_ms']}")
    print("wrote", path)


if __name__ == "__main__":
    main()
