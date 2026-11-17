"""Second-round probes: the discriminating controls the first round lacked.

The first round established that every case returns. What it cannot yet show
is *which* budget the post-ponderhit search is measured against, because a flat
hit->best time is consistent with two explanations. These probes separate them:

  A. Ponder-DURATION sweep at a fixed clock. If the budget were measured from
     the original `go`, a longer ponder would leave less of it and hit->best
     would SHRINK towards zero. If it restarts at the hit, hit->best is flat in
     the ponder duration.
  B. A ponder far longer than the whole planned budget, at a small clock, so
     the two hypotheses predict values an order of magnitude apart.
  C. `position`/`ucinewgame`/`setoption` arriving mid-ponder: does the abort
     emit an extra bestmove that a runner would attribute to the next search?
  D. The Ponder option, with the path proven to have run.
  E. Ponderhit before the first info line, and with several threads.
"""

import argparse
import json
import os
import sys
import time

from uci_driver import Engine, bestmoves, info_lines, is_bestmove, parse_bestmove

NO_BOOK_FEN = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 6 6"
BASE = [("OwnBook", "false"), ("Threads", "1"), ("Hash", "32"), ("Move Overhead", "10")]


def fresh(exe, options=None):
    e = Engine(exe)
    e.uci_handshake()
    for n, v in (options if options is not None else BASE):
        e.set_option(n, v)
    return e


def infos(lines):
    return [i for _, i in info_lines(lines) if i and "depth" in i]


def probe_a_sweep(exe, clock, durations, cap_s=45.0):
    """Fixed clock, rising ponder duration. Budget origin discriminator."""
    rows = []
    for ps in durations:
        e = fresh(exe)
        try:
            e.send(f"position fen {NO_BOOK_FEN}")
            mark = e.mark()
            t_go = e.send(f"go ponder wtime {clock} btime {clock}")
            time.sleep(ps)
            pre = e.since(mark)
            pre_i = infos(pre)
            t_hit = e.send("ponderhit")
            got = e.wait_for(is_bestmove, cap_s, mark)
            if got is None:
                rows.append({"clock": clock, "ponder_s": ps, "verdict": "CAPPED", "cap_s": cap_s})
                e.kill()
                continue
            post = e.since(mark)
            post_i = infos(post)
            new_after_hit = post_i[len(pre_i):]
            rows.append({
                "clock": clock, "ponder_s": ps, "verdict": "RETURNED",
                "t_hit_to_best_ms": round((got[0].t - t_hit) * 1000.0, 1),
                "depth_at_hit": pre_i[-1]["depth"] if pre_i else None,
                "depth_at_best": post_i[-1]["depth"] if post_i else None,
                "iterations_after_hit": len(new_after_hit),
                "reported_time_at_best_ms": post_i[-1].get("time") if post_i else None,
                "bestmove": parse_bestmove(got[0].text)[0],
                "bestmove_count": len(bestmoves(post)),
            })
        finally:
            e.close()
    return rows


def probe_b_long_ponder_small_clock(exe, cap_s=45.0):
    """A 6 s ponder against a 1000 ms clock: the two hypotheses differ by ~10x."""
    rows = []
    for clock, ps in [(1000, 0.2), (1000, 6.0), (500, 4.0)]:
        e = fresh(exe)
        try:
            e.send(f"position fen {NO_BOOK_FEN}")
            mark = e.mark()
            t_go = e.send(f"go ponder wtime {clock} btime {clock}")
            time.sleep(ps)
            pre_i = infos(e.since(mark))
            t_hit = e.send("ponderhit")
            got = e.wait_for(is_bestmove, cap_s, mark)
            if got is None:
                rows.append({"clock": clock, "ponder_s": ps, "verdict": "CAPPED"})
                e.kill()
                continue
            post_i = infos(e.since(mark))
            rows.append({
                "clock": clock, "ponder_s": ps, "verdict": "RETURNED",
                "t_hit_to_best_ms": round((got[0].t - t_hit) * 1000.0, 1),
                "planned_soft_ms": (clock - 10) // 22,
                "planned_hard_ms": min((clock - 10) * 60 // 100, ((clock - 10) // 22) * 5),
                "depth_at_hit": pre_i[-1]["depth"] if pre_i else None,
                "iterations_after_hit": max(0, len(post_i) - len(pre_i)),
                "bestmove_count": len(bestmoves(e.since(mark))),
            })
        finally:
            e.close()
    return rows


def probe_c_interrupt(exe, cap_s=20.0):
    """Command arriving mid-ponder. Does the abort leak a bestmove?"""
    rows = []
    cases = [
        ("position_during_ponder", f"position fen {NO_BOOK_FEN}"),
        ("ucinewgame_during_ponder", "ucinewgame"),
        ("setoption_during_ponder", "setoption name Hash value 64"),
        ("go_during_ponder", f"position fen {NO_BOOK_FEN}"),
    ]
    for label, interrupt in cases:
        e = fresh(exe)
        try:
            e.send(f"position fen {NO_BOOK_FEN}")
            mark = e.mark()
            t_go = e.send("go ponder wtime 10000 btime 10000")
            time.sleep(0.6)
            t_cmd = e.send(interrupt)
            # Give the abort a bounded window, then start a normal search and
            # count every bestmove the client sees across the whole episode.
            e.wait_quiet(0.4, 4.0)
            after_interrupt = e.since(mark)
            leaked = [l.text for l in bestmoves(after_interrupt)]
            mark2 = e.mark()
            e.send(f"position fen {NO_BOOK_FEN}")
            e.send("go depth 5")
            got = e.wait_for(is_bestmove, cap_s, mark2)
            second = [l.text for l in bestmoves(e.since(mark2))]
            rows.append({
                "case": label, "verdict": "RETURNED" if got else "CAPPED",
                "bestmove_from_the_abort": leaked,
                "abort_bestmove_count": len(leaked),
                "t_go_to_abort_bestmove_ms": round((after_interrupt[-1].t - t_cmd) * 1000.0, 1)
                if after_interrupt else None,
                "bestmove_from_next_search": second,
                "engine_alive": e.alive(),
            })
            if got is None:
                e.kill()
        finally:
            e.close()
    return rows


def probe_d_ponder_option_path(exe, cap_s=30.0):
    """Prove the Ponder option's one observable effect, and that the search
    numbers are untouched: three searches per arm, node counts compared."""
    rows = []
    for pon in ("false", "true"):
        e = fresh(exe, BASE + [("Ponder", pon)])
        try:
            # Depth 10 on a quiet position: PV length 2 is guaranteed, so the
            # suffix path is reachable if the option gates it.
            e.send(f"position fen {NO_BOOK_FEN}")
            mark = e.mark()
            e.send("go depth 10")
            got = e.wait_for(is_bestmove, cap_s, mark)
            if got is None:
                rows.append({"Ponder": pon, "verdict": "CAPPED"})
                e.kill()
                continue
            i = infos(e.since(mark))
            best, pm = parse_bestmove(got[0].text)
            rows.append({
                "Ponder": pon,
                "verdict": "RETURNED",
                "bestmove_line": got[0].text,
                "suffix_present": pm is not None,
                "bestmove": best,
                "nodes": i[-1]["nodes"] if i else None,
                "depth": i[-1]["depth"] if i else None,
                "pv_len": len(i[-1].get("pv") or []) if i else None,
                "pv_head": (i[-1].get("pv") or [])[:3] if i else None,
            })
        finally:
            e.close()
    return rows


def probe_e_edges(exe, cap_s=30.0):
    rows = []
    # e1: ponderhit before the first info line arrives.
    e = fresh(exe)
    try:
        e.send(f"position fen {NO_BOOK_FEN}")
        mark = e.mark()
        e.send("go ponder wtime 10000 btime 10000")
        pre = e.since(mark)
        t_hit = e.send("ponderhit")  # no sleep at all
        got = e.wait_for(is_bestmove, cap_s, mark)
        i = infos(e.since(mark))
        rows.append({
            "case": "ponderhit_before_first_info",
            "info_lines_at_hit": len(infos(pre)),
            "verdict": "RETURNED" if got else "CAPPED",
            "t_hit_to_best_ms": round((got[0].t - t_hit) * 1000.0, 1) if got else None,
            "bestmove": parse_bestmove(got[0].text)[0] if got else None,
            "depth_at_best": i[-1]["depth"] if i else None,
            "bestmove_count": len(bestmoves(e.since(mark))),
        })
        if got is None:
            e.kill()
    finally:
        e.close()

    # e2/e3: thread count. Helpers ignore the clock, so this is where a second
    # bestmove or a never-returning helper would show.
    for threads in (2, 4):
        e = fresh(exe, BASE + [("Threads", str(threads))])
        try:
            e.send(f"position fen {NO_BOOK_FEN}")
            mark = e.mark()
            e.send("go ponder wtime 10000 btime 10000")
            time.sleep(1.0)
            pre_i = infos(e.since(mark))
            t_hit = e.send("ponderhit")
            got = e.wait_for(is_bestmove, cap_s, mark)
            e.wait_quiet(0.5, 3.0)
            post = e.since(mark)
            post_i = infos(post)
            rows.append({
                "case": f"threads_{threads}_ponderhit",
                "verdict": "RETURNED" if got else "CAPPED",
                "t_hit_to_best_ms": round((got[0].t - t_hit) * 1000.0, 1) if got else None,
                "depth_at_hit": pre_i[-1]["depth"] if pre_i else None,
                "depth_at_best": post_i[-1]["depth"] if post_i else None,
                "bestmove_count": len(bestmoves(post)),
                "lines_after_bestmove": [l.text for l in post[post.index(bestmoves(post)[-1]) + 1:]]
                if bestmoves(post) else [],
            })
            if got is None:
                e.kill()
        finally:
            e.close()

    # e4: stop BEFORE any info line, with a reference row beside it, so the
    # a2a3-shaped answer can be told apart from the EOF abort.
    for label, pause in [("stop_at_0ms", 0.0), ("stop_at_30ms", 0.03), ("stop_at_300ms", 0.3)]:
        e = fresh(exe)
        try:
            e.send(f"position fen {NO_BOOK_FEN}")
            mark = e.mark()
            e.send("go ponder wtime 10000 btime 10000")
            if pause:
                time.sleep(pause)
            pre = e.since(mark)
            e.send("stop")
            got = e.wait_for(is_bestmove, cap_s, mark)
            rows.append({
                "case": label,
                "verdict": "RETURNED" if got else "CAPPED",
                "info_before_stop": len(infos(pre)),
                "last_pv_before_stop": (infos(pre)[-1].get("pv") or [None])[0] if infos(pre) else None,
                "bestmove": parse_bestmove(got[0].text)[0] if got else None,
                "bestmove_line": got[0].text if got else None,
                "engine_alive": e.alive(),
            })
            if got is None:
                e.kill()
        finally:
            e.close()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="/tmp/forge-build/forge")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "evidence"))
    ap.add_argument("--only", default="a,b,c,d,e")
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    only = set(args.only.split(","))
    res = {}
    if "a" in only:
        print("A sweep ...", flush=True)
        # 10000 ms: soft 454, hard 2270. 60000: soft 2726, hard 13630.
        res["a_ponder_duration_sweep_10000"] = probe_a_sweep(args.exe, 10000, [0.2, 1.0, 3.0, 6.0])
        res["a_ponder_duration_sweep_2000"] = probe_a_sweep(args.exe, 2000, [0.2, 1.0, 3.0, 6.0])
    if "b" in only:
        print("B long ponder small clock ...", flush=True)
        res["b_budget_origin"] = probe_b_long_ponder_small_clock(args.exe)
    if "c" in only:
        print("C mid-ponder interrupts ...", flush=True)
        res["c_interrupt_mid_ponder"] = probe_c_interrupt(args.exe)
    if "d" in only:
        print("D Ponder option path ...", flush=True)
        res["d_ponder_option_path"] = probe_d_ponder_option_path(args.exe)
    if "e" in only:
        print("E edges ...", flush=True)
        res["e_edges"] = probe_e_edges(args.exe)
    path = os.path.join(out, "probe2_results.json")
    old = {}
    if os.path.exists(path):
        with open(path) as fh:
            old = json.load(fh)
    old.update(res)
    with open(path, "w") as fh:
        json.dump(old, fh, indent=2, sort_keys=True)
    print("wrote", path)


if __name__ == "__main__":
    main()
