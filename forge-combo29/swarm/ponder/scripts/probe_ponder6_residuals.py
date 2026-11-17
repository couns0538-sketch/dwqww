"""Probe N: the residuals, each with the control that makes its null meaningful.

  n1. Node growth after ponderhit in the extreme case (ponder far longer than
      the whole planned budget). Zero added nodes proves the post-hit search
      had nothing left to do rather than that it was cut short.
  n2. Is the `stop` bestmove the move the search had found? Measured against
      the last info PV across 6 positions x 3 ponder lengths.
  n3. The origin of the info `time` field: from `go`, or from `ponderhit`?
  n4. The zero-ms stop answer, against the EOF-abort artifact, on TWO
      positions. Findings 7.1/7.2d0 warn that a piped abort fabricates
      `bestmove a2a3` with zero info lines; if the two are byte-identical the
      honest report is "indistinguishable", not "a real answer".
  n5. The info shape of a terminal/drawn root under ponder (64 info lines for
      a search that visits 0 nodes).
"""

import argparse
import json
import os
import time

from uci_driver import Engine, bestmoves, info_lines, is_bestmove, parse_bestmove

POSITIONS = [
    ("middlegame_white", "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 6 6"),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
    ("mid2", "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10"),
    ("mid3", "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R1BQKB1R w KQ - 0 8"),
    ("mid4", "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1"),
    ("endgame_black", "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1"),
]
FEN_A = POSITIONS[0][1]
FEN_B = POSITIONS[-1][1]
REP_MOVES = "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8"

BASE = [("OwnBook", "false"), ("Threads", "1"), ("Hash", "32"), ("Move Overhead", "10")]


def fresh(exe, options=None):
    e = Engine(exe)
    e.uci_handshake()
    for n, v in (options if options is not None else BASE):
        e.set_option(n, v)
    return e


def infos(lines):
    return [i for _, i in info_lines(lines) if i and "depth" in i]


def probe_n1_node_growth(exe, cap_s=40.0):
    """The hard-limit fingerprint: is the post-hit budget a FRESH clock?

    Ponder far past the whole planned budget, then hit. If the budget were
    measured from the original `go`, a 6 s ponder against a 225 ms hard limit
    would already be 26x over at the hit and could not then run for another
    225 ms. If the budget is rebased at the hit, hit->best lands on the clock's
    own hard value.

    NOTE on `nodes_added_after_hit`: info lines are emitted only at iteration
    boundaries, so a zero here means "no iteration COMPLETED after the hit",
    not "no work was done". The work inside an aborted iteration is not
    visible on the wire; the field is named accordingly and is not read as a
    node count of the post-hit window.
    """
    rows = []
    for clock, ps in [(1000, 6.0), (500, 4.0), (2000, 8.0), (10000, 6.0)]:
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
                rows.append({"clock": clock, "ponder_s": ps, "verdict": "CAPPED", "cap_s": cap_s})
                e.kill()
                continue
            tail = e.since(mark)
            before = tail[:tail.index(got[0])]
            pre_before_hit = [i for i in infos(before) if True][:len(pre)]
            post = infos(tail)
            new = post[len(pre_before_hit):]
            soft = (clock - 10) // 22
            hard = min((clock - 10) * 60 // 100, soft * 5)
            hit_ms = round((got[0].t - t_hit) * 1000.0, 1)
            rows.append({
                "clock": clock, "ponder_s": ps, "verdict": "RETURNED",
                "planned_soft_ms": soft, "planned_hard_ms": hard,
                "ponder_ms": round((t_hit - t_go) * 1000.0, 1),
                "ponder_over_hard": round(((t_hit - t_go) * 1000.0) / hard, 2),
                "t_hit_to_best_ms": hit_ms,
                "hit_to_best_over_hard": round(hit_ms / hard, 3),
                "hit_to_best_minus_hard_ms": round(hit_ms - hard, 1),
                "depth_at_hit": pre_before_hit[-1]["depth"] if pre_before_hit else None,
                "depth_at_best": post[-1]["depth"] if post else None,
                "iterations_completed_after_hit": len(new),
                "time_field_at_hit": pre_before_hit[-1].get("time") if pre_before_hit else None,
                "time_field_at_best": post[-1].get("time") if post else None,
                "wall_go_to_best_ms": round((got[0].t - t_go) * 1000.0, 1),
            })
        finally:
            e.close()
    return rows


def probe_n2_stop_move(exe, cap_s=20.0):
    """Does `stop` return the move the search had found?

    The comparison must be against the last info line that arrived BEFORE the
    bestmove, not the last one the harness happened to have read when it sent
    `stop`: an iteration can complete in that gap, and the first version of
    this probe reported one such case as a disagreement.
    """
    rows = []
    agree = 0
    total = 0
    for name, fen in POSITIONS:
        for ps in (0.4, 0.9, 1.7):
            e = fresh(exe)
            try:
                e.send(f"position fen {fen}")
                mark = e.mark()
                e.send("go ponder wtime 10000 btime 10000")
                time.sleep(ps)
                info_at_stop = len(infos(e.since(mark)))
                e.send("stop")
                got = e.wait_for(is_bestmove, cap_s, mark)
                if got is None:
                    rows.append({"pos": name, "ponder_s": ps, "verdict": "CAPPED"})
                    e.kill()
                    continue
                tail = e.since(mark)
                # Everything that arrived before the bestmove line.
                before = tail[:tail.index(got[0])]
                infos_before = infos(before)
                best = parse_bestmove(got[0].text)[0]
                last_pv = (infos_before[-1].get("pv") or [None])[0] if infos_before else None
                last_depth = infos_before[-1].get("depth") if infos_before else None
                total += 1
                if best == last_pv:
                    agree += 1
                rows.append({
                    "pos": name, "ponder_s": ps, "verdict": "RETURNED",
                    "bestmove": best,
                    "last_pv_before_bestmove": last_pv,
                    "agrees": best == last_pv,
                    "last_depth_before_bestmove": last_depth,
                    "info_lines_before_bestmove": len(infos_before),
                    "info_lines_at_moment_of_stop": info_at_stop,
                    "late_info_lines": len(infos_before) - info_at_stop,
                    "is_0000": best == "0000",
                })
            finally:
                e.close()
    return {"rows": rows, "agree": agree, "total": total}


def probe_n3_time_field(exe, cap_s=40.0):
    rows = []
    for ps in (0.3, 3.0):
        e = fresh(exe)
        try:
            e.send(f"position fen {FEN_A}")
            mark = e.mark()
            t_go = e.send("go ponder wtime 10000 btime 10000")
            time.sleep(ps)
            pre = infos(e.since(mark))
            t_hit = e.send("ponderhit")
            got = e.wait_for(is_bestmove, cap_s, mark)
            if got is None:
                rows.append({"ponder_s": ps, "verdict": "CAPPED"})
                e.kill()
                continue
            post = infos(e.since(mark))
            new = post[len(pre):]
            wall_go = round((got[0].t - t_go) * 1000.0, 1)
            wall_hit = round((got[0].t - t_hit) * 1000.0, 1)
            last_time = post[-1].get("time") if post else None
            rows.append({
                "ponder_s": ps, "verdict": "RETURNED",
                "last_time_before_hit_ms": pre[-1].get("time") if pre else None,
                "wall_go_to_hit_ms": round((t_hit - t_go) * 1000.0, 1),
                "post_hit_time_values": [i.get("time") for i in new],
                "wall_go_to_best_ms": wall_go,
                "wall_hit_to_best_ms": wall_hit,
                "time_field_minus_wall_go_ms": None if last_time is None else round(last_time - wall_go, 1),
                "time_field_minus_wall_hit_ms": None if last_time is None else round(last_time - wall_hit, 1),
                "tracks": "go" if last_time is not None and abs(last_time - wall_go) < abs(last_time - wall_hit) else "ponderhit",
            })
        finally:
            e.close()
    return rows


def probe_n4_zero_stop_vs_eof(exe, cap_s=20.0):
    """Three arms per position: zero-ms stop, immediate EOF, 300ms-then-EOF."""
    rows = []
    for name, fen in (("position_A", FEN_A), ("position_B", FEN_B)):
        # perft 1 order = the reference for "first legal move". perft 1 does
        # NOT separate all hypotheses in general, but here it only needs to say
        # which move the generator lists first.
        e = fresh(exe)
        try:
            e.send(f"position fen {fen}")
            mark = e.mark()
            e.send("go perft 1")
            e.wait_for(lambda s: s.startswith("nodes "), 20.0, mark)
            order = []
            total = None
            for line in e.since(mark):
                if line.text.startswith("nodes "):
                    total = line.text
                elif ":" in line.text and not line.text.startswith("info"):
                    order.append(line.text.split(":")[0].strip())
        finally:
            e.close()

        # arm 1: go ponder then stop with no pause at all
        e = fresh(exe)
        try:
            e.send(f"position fen {fen}")
            mark = e.mark()
            e.send("go ponder wtime 10000 btime 10000")
            e.send("stop")
            got = e.wait_for(is_bestmove, cap_s, mark)
            arm1 = got[0].text if got else None
            arm1_info = len(infos(e.since(mark)))
            if got is None:
                e.kill()
        finally:
            e.close()

        # arm 2: immediate EOF (stdin closed before any info line)
        e = Engine(exe)
        e.uci_handshake()
        for n, v in BASE:
            e.set_option(n, v)
        e.send(f"position fen {fen}")
        mark = e.mark()
        e.send("go ponder wtime 10000 btime 10000")
        e.proc.stdin.close()
        got = e.wait_for(is_bestmove, cap_s, mark)
        arm2 = got[0].text if got else None
        arm2_info = len(infos(e.since(mark)))
        if got is None:
            e.kill()
        else:
            e.close()

        # arm 3: EOF after real search, as the findings describe
        e = fresh(exe)
        try:
            e.send(f"position fen {fen}")
            mark = e.mark()
            e.send("go ponder wtime 10000 btime 10000")
            time.sleep(0.3)
            info_before = len(infos(e.since(mark)))
            e.proc.stdin.close()
            got = e.wait_for(is_bestmove, cap_s, mark)
            arm3 = got[0].text if got else None
            if got is None:
                e.kill()
            else:
                e.close()
        except Exception:
            arm3 = None
            info_before = None

        rows.append({
            "pos": name, "fen": fen,
            "perft1_first_legal": order[0] if order else None,
            "perft1_order_head": order[:4], "perft1_total": total,
            "zero_ms_stop": arm1, "zero_ms_stop_info_lines": arm1_info,
            "immediate_eof": arm2, "immediate_eof_info_lines": arm2_info,
            "eof_after_300ms": arm3, "eof_after_300ms_info_before": info_before,
            "zero_stop_equals_immediate_eof": arm1 == arm2,
            "zero_stop_is_first_legal": (arm1.split()[1] == order[0]) if (arm1 and order) else None,
            "zero_stop_is_0000": (arm1.split()[1] == "0000") if arm1 else None,
        })
    return rows


def probe_n5_terminal_root(exe, cap_s=20.0):
    rows = []
    e = fresh(exe)
    try:
        e.send(f"position startpos moves {REP_MOVES}")
        mark = e.mark()
        e.send("go ponder wtime 10000 btime 10000")
        time.sleep(1.5)
        pre = e.since(mark)
        pre_i = infos(pre)
        early = bestmoves(pre)
        t_hit = e.send("ponderhit")
        got = e.wait_for(is_bestmove, cap_s, mark)
        rows.append({
            "case": "threefold_root_by_move_list_under_ponder",
            "info_lines_during_ponder": len(pre_i),
            "max_depth_during_ponder": max((i["depth"] for i in pre_i), default=None),
            "nodes_reported_at_max_depth": pre_i[-1]["nodes"] if pre_i else None,
            "bestmove_withheld_during_ponder": len(early) == 0,
            "early_bestmoves": [b.text for b in early],
            "verdict": "RETURNED" if got else "CAPPED",
            "t_hit_to_best_ms": round((got[0].t - t_hit) * 1000.0, 1) if got else None,
            "bestmove_line": got[0].text if got else None,
            "bestmove_count": len(bestmoves(e.since(mark))),
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
    ap.add_argument("--only", default="n1,n2,n3,n4,n5")
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    only = set(args.only.split(","))
    res = {}
    if "n1" in only:
        print("n1 node growth ...", flush=True)
        res["n1_node_growth_after_hit"] = probe_n1_node_growth(args.exe)
    if "n2" in only:
        print("n2 stop move ...", flush=True)
        res["n2_stop_returns_found_move"] = probe_n2_stop_move(args.exe)
    if "n3" in only:
        print("n3 time field ...", flush=True)
        res["n3_time_field_origin"] = probe_n3_time_field(args.exe)
    if "n4" in only:
        print("n4 zero stop vs EOF ...", flush=True)
        res["n4_zero_stop_vs_eof"] = probe_n4_zero_stop_vs_eof(args.exe)
    if "n5" in only:
        print("n5 terminal root ...", flush=True)
        res["n5_terminal_root"] = probe_n5_terminal_root(args.exe)
    path = os.path.join(out, "probe6_results.json")
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
