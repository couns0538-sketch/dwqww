"""Probe P: what "no bestmove" actually means, in the two regimes.

The findings file records that `go ponder` with no clock gives no bestmove
after 20 s and is "still climbing". Two different mechanisms can produce
"no bestmove", and they carry different hazards for a runner:

  RUNAWAY     the search never ends: CPU stays at ~100% and depth keeps
              rising. Cost grows without bound until someone sends `stop`.
  WITHHELD    the search has FINISHED its own limit and is holding the
              answer: CPU drops to ~0 and depth stops rising. The engine is
              idle, not working, and will wait forever.

Both are "unbounded" from a runner's point of view (no bestmove without a
command) but only the first burns a core. The probe measures CPU% and depth
at several horizons so the regime is observed, not inferred.

It also measures the disagreement between the two clocks inside the engine:
the `time` field of the info lines counts from the `go` command, while the
stop decision counts from `ponderhit`.
"""

import argparse
import json
import os
import subprocess
import time

from uci_driver import Engine, bestmoves, info_lines, is_bestmove

FEN_A = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 6 6"
BASE = [("OwnBook", "false"), ("Threads", "1"), ("Hash", "32"), ("Move Overhead", "10")]


def fresh(exe, options=None):
    e = Engine(exe)
    e.uci_handshake()
    for n, v in (options if options is not None else BASE):
        e.set_option(n, v)
    return e


def infos(lines):
    return [i for _, i in info_lines(lines) if i and "depth" in i]


def cpu_percent(pid):
    try:
        out = subprocess.run(["ps", "-o", "%cpu=", "-p", str(pid)],
                             capture_output=True, text=True, timeout=5).stdout.strip()
        return float(out) if out else None
    except Exception:
        return None


def probe_p_regime(exe, horizon_s=30.0, cap_s=45.0):
    rows = []
    for label, go_line in [
        ("ponder_clocked_10s", "go ponder wtime 10000 btime 10000"),
        ("ponder_clockless", "go ponder"),
        ("ponder_selflimited_depth12", "go ponder depth 12"),
        ("ponder_selflimited_nodes_500k", "go ponder nodes 500000"),
    ]:
        e = fresh(exe)
        try:
            e.send(f"position fen {FEN_A}")
            mark = e.mark()
            t_go = e.send(go_line)
            pid = e.proc.pid
            samples = []
            for at in (1, 3, 8, 15, horizon_s):
                if at > horizon_s:
                    break
                gap = at - (time.monotonic() - t_go)
                if gap > 0:
                    time.sleep(gap)
                il = infos(e.since(mark))
                samples.append({
                    "at_s": at,
                    "depth": il[-1]["depth"] if il else None,
                    "nodes": il[-1]["nodes"] if il else None,
                    "info_lines": len(il),
                    "cpu_percent": cpu_percent(pid),
                    "bestmoves": len(bestmoves(e.since(mark))),
                })
            # Now prove the search is answerable: one stop, one bestmove.
            t_stop = e.send("stop")
            got = e.wait_for(is_bestmove, 15.0, mark)
            rows.append({
                "case": label, "go_line": go_line, "horizon_s": horizon_s,
                "samples": samples,
                "depth_rose_after_8s": (samples[-1]["depth"] or 0) > (samples[2]["depth"] or 0)
                if len(samples) > 2 else None,
                "cpu_at_horizon": samples[-1]["cpu_percent"] if samples else None,
                "regime": "RUNAWAY" if samples and (samples[-1]["cpu_percent"] or 0) > 50 else "WITHHELD",
                "bestmoves_during_horizon": samples[-1]["bestmoves"] if samples else None,
                "stop_returns_bestmove": got is not None,
                "t_stop_to_best_ms": round((got[0].t - t_stop) * 1000.0, 1) if got else None,
                "bestmove_line": got[0].text if got else None,
            })
            if got is None:
                e.kill()
        finally:
            e.close()
    return rows


def probe_p_time_disagreement(exe, cap_s=40.0):
    """Two clocks: the info `time` field (from go) vs the budget (from hit)."""
    rows = []
    for clock, ps in [(10000, 0.5), (10000, 3.0), (60000, 3.0)]:
        e = fresh(exe)
        try:
            e.send(f"position fen {FEN_A}")
            mark = e.mark()
            t_go = e.send(f"go ponder wtime {clock} btime {clock}")
            time.sleep(ps)
            pre = infos(e.since(mark))
            t_hit = e.send("ponderhit")
            got = e.wait_for(is_bestmove, cap_s, mark)
            if got is None:
                rows.append({"clock": clock, "ponder_s": ps, "verdict": "CAPPED"})
                e.kill()
                continue
            tail = e.since(mark)
            before = tail[:tail.index(got[0])]
            post = infos(tail)
            soft = (clock - 10) // 22
            hard = min((clock - 10) * 60 // 100, soft * 5)
            wall_hit = (got[0].t - t_hit) * 1000.0
            wall_go = (got[0].t - t_go) * 1000.0
            time_field = post[-1].get("time") if post else None
            rows.append({
                "clock": clock, "ponder_s": ps, "verdict": "RETURNED",
                "planned_soft_ms": soft, "planned_hard_ms": hard,
                "info_time_at_best_ms": time_field,
                "wall_from_ponderhit_ms": round(wall_hit, 1),
                "wall_from_go_ms": round(wall_go, 1),
                # This is the point: one number counts the ponder, the other does not.
                "info_time_matches": "go" if time_field is not None and
                abs(time_field - wall_go) < abs(time_field - wall_hit) else "ponderhit",
                "budget_matches": "ponderhit" if abs(wall_hit - hard) < abs(wall_hit - soft) * 2
                else "go",
                "two_clocks_disagree": True,
            })
        finally:
            e.close()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="/tmp/forge-build/forge")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "evidence"))
    ap.add_argument("--horizon", type=float, default=30.0)
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    res = {
        "p_regime": probe_p_regime(args.exe, horizon_s=args.horizon),
        "p_time_disagreement": probe_p_time_disagreement(args.exe),
    }
    path = os.path.join(out, "probe8_results.json")
    with open(path, "w") as fh:
        json.dump(res, fh, indent=2, sort_keys=True)
    for r in res["p_regime"]:
        print(r["case"], "->", r["regime"], "cpu", r["cpu_at_horizon"],
              "depth rose:", r["depth_rose_after_8s"],
              "| stop returns:", r["stop_returns_bestmove"])
    for r in res["p_time_disagreement"]:
        print("clock", r["clock"], "info_time", r.get("info_time_at_best_ms"),
              "wall_hit", r.get("wall_from_ponderhit_ms"), "hard", r.get("planned_hard_ms"))
    print("wrote", path)


if __name__ == "__main__":
    main()
