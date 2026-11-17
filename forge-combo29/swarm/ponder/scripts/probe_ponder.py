"""Ponder-protocol probes for forge-combo29 at base commit 6b98f217.

Six probes, one engine process per measurement, every wait deadline-bounded.
A deadline hit is reported as CAPPED and the process is SIGKILLed, never
inherited as a hang.

Usage:
  python3 probe_ponder.py [--exe PATH] [--out DIR] [--only p1,p2,...]
"""

import argparse
import json
import os
import statistics
import sys
import time

from uci_driver import Engine, bestmoves, info_lines, is_bestmove, parse_bestmove

NO_BOOK_FEN = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 6 6"
KL_FEN = "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1"

# A fresh process per measurement: warm TT / history state shifts scores and
# wall time (forge-findings.md 7.3). Every probe sets OwnBook false unless the
# book is the subject, because a book reply short-circuits the search entirely.
BASE_OPTIONS = [("OwnBook", "false"), ("Threads", "1"), ("Hash", "32"), ("Move Overhead", "10")]


def fresh(exe, options=None):
    e = Engine(exe)
    e.uci_handshake()
    for name, value in (options if options is not None else BASE_OPTIONS):
        e.set_option(name, value)
    return e


def depth_series(lines):
    out = []
    for line, info in info_lines(lines):
        if info and "depth" in info:
            out.append({"t": round(line.t, 4), "depth": info.get("depth"),
                        "nodes": info.get("nodes"), "time_ms": info.get("time"),
                        "score": info.get("score"), "pv0": (info.get("pv") or [None])[0]})
    return out


# ---------------------------------------------------------------------------
# P1: full ponder cycle -> ponderhit. Where does the budget start?
# ---------------------------------------------------------------------------
def probe_p1(exe, clocks, ponder_s, cap_s=40.0):
    """Return one row per (clock, ponder duration).

    t_go->t_best is the whole cycle; t_hit->t_best is the quantity under test.
    """
    rows = []
    for wtime, btime in clocks:
        for ps in ponder_s:
            e = fresh(exe)
            try:
                e.send(f"position fen {NO_BOOK_FEN}")
                mark = e.mark()
                t_go = e.send(f"go ponder wtime {wtime} btime {btime}")
                # Let the ponder search run for exactly ps seconds.
                time.sleep(ps)
                pre = e.since(mark)
                pre_best = bestmoves(pre)
                pre_info = depth_series(pre)
                t_hit = e.send("ponderhit")
                got = e.wait_for(is_bestmove, cap_s, mark)
                if got is None:
                    rows.append({
                        "clock": [wtime, btime], "ponder_s": ps, "verdict": "CAPPED",
                        "cap_s": cap_s,
                        "depth_at_hit": pre_info[-1]["depth"] if pre_info else None,
                        "info_before_hit": len(pre_info),
                        "bestmove_before_hit": [b.text for b in pre_best],
                    })
                    e.kill()
                    continue
                line, _ = got
                post = e.since(mark)
                all_best = bestmoves(post)
                post_info = depth_series(post)
                best, ponder_move = parse_bestmove(line.text)
                rows.append({
                    "clock": [wtime, btime], "ponder_s": ps, "verdict": "RETURNED",
                    "t_go_to_best_ms": round((line.t - t_go) * 1000.0, 1),
                    "t_hit_to_best_ms": round((line.t - t_hit) * 1000.0, 1),
                    "bestmove": best, "ponder_suffix": ponder_move,
                    "bestmove_count": len(all_best),
                    "depth_at_hit": pre_info[-1]["depth"] if pre_info else None,
                    "depth_at_best": post_info[-1]["depth"] if post_info else None,
                    "info_before_hit": len(pre_info),
                    "info_after_hit": len(post_info) - len(pre_info),
                    "nodes_at_hit": pre_info[-1]["nodes"] if pre_info else None,
                    "nodes_at_best": post_info[-1]["nodes"] if post_info else None,
                    "reported_time_last_info_ms": post_info[-1]["time_ms"] if post_info else None,
                    "last_info_before_hit": pre_info[-1] if pre_info else None,
                })
            finally:
                e.close()
    return rows


# ---------------------------------------------------------------------------
# P1 control: the same clocks WITHOUT ponder, to get the reference budget.
# ---------------------------------------------------------------------------
def probe_p1_control(exe, clocks, cap_s=40.0, repeats=1):
    rows = []
    for wtime, btime in clocks:
        for _ in range(repeats):
            e = fresh(exe)
            try:
                e.send(f"position fen {NO_BOOK_FEN}")
                mark = e.mark()
                t_go = e.send(f"go wtime {wtime} btime {btime}")
                got = e.wait_for(is_bestmove, cap_s, mark)
                if got is None:
                    rows.append({"clock": [wtime, btime], "verdict": "CAPPED", "cap_s": cap_s})
                    e.kill()
                    continue
                line, _ = got
                infos = depth_series(e.since(mark))
                best, pm = parse_bestmove(line.text)
                rows.append({
                    "clock": [wtime, btime], "verdict": "RETURNED",
                    "t_go_to_best_ms": round((line.t - t_go) * 1000.0, 1),
                    "bestmove": best, "ponder_suffix": pm,
                    "depth_at_best": infos[-1]["depth"] if infos else None,
                    "last_info_time_ms": infos[-1]["time_ms"] if infos else None,
                    "bestmove_count": len(bestmoves(e.since(mark))),
                })
            finally:
                e.close()
    return rows


# ---------------------------------------------------------------------------
# P2: go ponder then stop, no ponderhit. Which move comes back?
# ---------------------------------------------------------------------------
def probe_p2(exe, cap_s=20.0):
    rows = []
    # (label, go line, how long to let it ponder before stop)
    cases = [
        ("ponder_then_stop_after_1s", "go ponder wtime 10000 btime 10000", 1.0),
        ("ponder_then_stop_immediately", "go ponder wtime 10000 btime 10000", 0.0),
        ("ponder_clockless_then_stop_after_1s", "go ponder", 1.0),
        ("ponder_then_pause_then_stop_2s", "go ponder wtime 10000 btime 10000", 2.0),
    ]
    for label, go_line, pause in cases:
        e = fresh(exe)
        try:
            e.send(f"position fen {NO_BOOK_FEN}")
            mark = e.mark()
            t_go = e.send(go_line)
            if pause > 0:
                time.sleep(pause)
            pre = e.since(mark)
            pre_info = depth_series(pre)
            t_stop = e.send("stop")
            got = e.wait_for(is_bestmove, cap_s, mark)
            if got is None:
                rows.append({"case": label, "verdict": "CAPPED", "cap_s": cap_s,
                             "depth_before_stop": pre_info[-1]["depth"] if pre_info else None})
                e.kill()
                continue
            line, _ = got
            best, pm = parse_bestmove(line.text)
            last_pv = pre_info[-1]["pv0"] if pre_info else None
            rows.append({
                "case": label, "verdict": "RETURNED",
                "t_stop_to_best_ms": round((line.t - t_stop) * 1000.0, 1),
                "t_go_to_best_ms": round((line.t - t_go) * 1000.0, 1),
                "bestmove": best, "ponder_suffix": pm,
                "bestmove_is_0000": best == "0000",
                "depth_before_stop": pre_info[-1]["depth"] if pre_info else None,
                "last_pv_before_stop": last_pv,
                "bestmove_equals_last_pv": best == last_pv,
                "info_before_stop": len(pre_info),
                "bestmove_count": len(bestmoves(e.since(mark))),
            })
        finally:
            e.close()
    return rows


# ---------------------------------------------------------------------------
# P3: go ponder WITH a clock, no ponderhit. Bounded or not?
# ---------------------------------------------------------------------------
def probe_p3(exe, cap_s=20.0):
    rows = []
    for label, go_line in [
        ("ponder_clocked_10s", "go ponder wtime 10000 btime 10000"),
        ("ponder_clocked_1000ms", "go ponder wtime 1000 btime 1000"),
        ("ponder_clockless", "go ponder"),
        ("control_movetime_1000_ponder", "go ponder movetime 1000"),
    ]:
        e = fresh(exe)
        try:
            e.send(f"position fen {NO_BOOK_FEN}")
            mark = e.mark()
            t_go = e.send(go_line)
            snapshots = []
            # Sample the depth curve while waiting so "still climbing" is
            # measured, not asserted; the deadline is the same cap_s.
            for at in (1, 3, 5, 10, 15, 19):
                if at > cap_s:
                    break
                now = time.monotonic()
                if now - t_go < at:
                    time.sleep(min(at - (now - t_go), 0.5))
                infos = depth_series(e.since(mark))
                snapshots.append({"at_s": at, "depth": infos[-1]["depth"] if infos else None,
                                  "nodes": infos[-1]["nodes"] if infos else None})
            got = e.wait_for(is_bestmove, max(0.05, cap_s - (time.monotonic() - t_go)), mark)
            if got is None:
                infos = depth_series(e.since(mark))
                rows.append({
                    "case": label, "verdict": "UNBOUNDED_NO_BESTMOVE", "cap_s": cap_s,
                    "depth_at_cap": infos[-1]["depth"] if infos else None,
                    "nodes_at_cap": infos[-1]["nodes"] if infos else None,
                    "depth_curve": snapshots,
                    "bestmove_count": len(bestmoves(e.since(mark))),
                })
                e.kill()
                continue
            line, _ = got
            best, pm = parse_bestmove(line.text)
            rows.append({
                "case": label, "verdict": "RETURNED",
                "t_go_to_best_ms": round((line.t - t_go) * 1000.0, 1),
                "bestmove": best, "depth_curve": snapshots,
            })
        finally:
            e.close()
    return rows


# ---------------------------------------------------------------------------
# P4: ponderhit with no ponder search running.
# ---------------------------------------------------------------------------
def probe_p4(exe):
    rows = []
    # 4a: at idle, right after handshake.
    for label, setup in [
        ("idle_after_startup", None),
        ("after_a_completed_search", "search"),
        ("ponderhit_twice", "ponder"),
        ("ponderhit_after_stop", "ponder_stop"),
    ]:
        e = fresh(exe)
        try:
            if setup == "search":
                e.send(f"position fen {NO_BOOK_FEN}")
                mark = e.mark()
                e.send("go depth 6")
                e.wait_for(is_bestmove, 20.0, mark)
            elif setup in ("ponder", "ponder_stop"):
                e.send(f"position fen {NO_BOOK_FEN}")
                mark = e.mark()
                e.send("go ponder wtime 10000 btime 10000")
                time.sleep(0.4)
                if setup == "ponder_stop":
                    e.send("stop")
                    e.wait_for(is_bestmove, 20.0, mark)
                    e.wait_quiet(0.2, 1.0)
                else:
                    e.send("ponderhit")
                    e.wait_for(is_bestmove, 20.0, mark)
                    e.wait_quiet(0.2, 1.0)
            mark = e.mark()
            t_hit = e.send("ponderhit")
            silent = e.wait_quiet(0.5, 2.0)
            got_out = e.since(mark)
            # Liveness: the engine must still answer after a stray ponderhit.
            mark2 = e.mark()
            e.send("isready")
            ready = e.wait_for(lambda s: s.strip() == "readyok", 5.0, mark2)
            if label == "ponderhit_twice":
                # second one, and confirm still silent + alive
                e.send("ponderhit")
                m3 = e.mark()
                e.wait_quiet(0.4, 1.5)
                twice_out = [l.text for l in e.since(m3)]
            else:
                twice_out = None
            rows.append({
                "case": label,
                "output_after_stray_ponderhit": [l.text for l in got_out],
                "said_anything": len(got_out) > 0,
                "quiet_within_2s": silent,
                "alive_after": ready is not None,
                "second_ponderhit_output": twice_out,
            })
        finally:
            e.close()

    # 4b: the discriminating control - the SAME command on a live ponder must
    # convert. Without this, "silent at idle" is equally consistent with
    # "ponderhit is never handled at all".
    e = fresh(exe)
    try:
        e.send(f"position fen {NO_BOOK_FEN}")
        mark = e.mark()
        e.send("go ponder wtime 10000 btime 10000")
        time.sleep(0.5)
        t_hit = e.send("ponderhit")
        got = e.wait_for(is_bestmove, 30.0, mark)
        rows.append({
            "case": "CONTROL_live_ponder_ponderhit_converts",
            "verdict": "RETURNED" if got else "CAPPED",
            "t_hit_to_best_ms": round((got[0].t - t_hit) * 1000.0, 1) if got else None,
            "bestmove": parse_bestmove(got[0].text)[0] if got else None,
        })
        if got is None:
            e.kill()
    finally:
        e.close()
    return rows


# ---------------------------------------------------------------------------
# P5: the Ponder option, true vs false.
# ---------------------------------------------------------------------------
def probe_p5(exe):
    rows = []
    for pon in ("false", "true"):
        # (a) fixed-depth search: option must not move a single node.
        e = fresh(exe, BASE_OPTIONS + [("Ponder", pon)])
        try:
            e.send(f"position fen {NO_BOOK_FEN}")
            mark = e.mark()
            t0 = e.send("go depth 8")
            got = e.wait_for(is_bestmove, 40.0, mark)
            if got is None:
                rows.append({"probe": "depth8", "Ponder": pon, "verdict": "CAPPED"})
                e.kill()
                continue
            infos = depth_series(e.since(mark))
            best, pm = parse_bestmove(got[0].text)
            rows.append({
                "probe": "depth8", "Ponder": pon, "verdict": "RETURNED",
                "bestmove": best, "ponder_suffix": pm,
                "last_depth": infos[-1]["depth"] if infos else None,
                "last_nodes": infos[-1]["nodes"] if infos else None,
                "bestmove_line": got[0].text,
                "ms": round((got[0].t - t0) * 1000.0, 1),
            })
        finally:
            e.close()

        # (b) clocked search: does Ponder alter the move choice or budget?
        e = fresh(exe, BASE_OPTIONS + [("Ponder", pon)])
        try:
            e.send(f"position fen {NO_BOOK_FEN}")
            mark = e.mark()
            t0 = e.send("go wtime 6000 btime 6000")
            got = e.wait_for(is_bestmove, 30.0, mark)
            if got is None:
                rows.append({"probe": "clocked", "Ponder": pon, "verdict": "CAPPED"})
                e.kill()
                continue
            infos = depth_series(e.since(mark))
            best, pm = parse_bestmove(got[0].text)
            rows.append({
                "probe": "clocked", "Ponder": pon, "verdict": "RETURNED",
                "bestmove": best, "ponder_suffix": pm,
                "last_depth": infos[-1]["depth"] if infos else None,
                "bestmove_line": got[0].text,
                "ms": round((got[0].t - t0) * 1000.0, 1),
            })
        finally:
            e.close()

        # (c) book path with OwnBook on: the option also gates the book's
        #     predicted reply.
        e = fresh(exe, [("Threads", "1"), ("Hash", "32"), ("OwnBook", "true"), ("Ponder", pon)])
        try:
            e.send("position startpos moves e2e4")
            mark = e.mark()
            e.send("go wtime 10000 btime 10000")
            got = e.wait_for(is_bestmove, 20.0, mark)
            rows.append({
                "probe": "book", "Ponder": pon,
                "verdict": "RETURNED" if got else "CAPPED",
                "bestmove_line": got[0].text if got else None,
                "used_book": any("book move" in l.text for l in e.since(mark)),
            })
            if got is None:
                e.kill()
        finally:
            e.close()

        # (d) does the option change how `go ponder ...` behaves at all?
        e = fresh(exe, BASE_OPTIONS + [("Ponder", pon)])
        try:
            e.send(f"position fen {NO_BOOK_FEN}")
            mark = e.mark()
            e.send("go ponder wtime 10000 btime 10000")
            time.sleep(0.4)
            t_hit = e.send("ponderhit")
            got = e.wait_for(is_bestmove, 30.0, mark)
            rows.append({
                "probe": "go_ponder_cycle", "Ponder": pon,
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


# ---------------------------------------------------------------------------
# P6: output shape during pondering, and bestmove uniqueness under stress.
# ---------------------------------------------------------------------------
def probe_p6(exe, cap_s=30.0):
    rows = []
    # 6a: info during ponder, one bestmove, and no info after it.
    e = fresh(exe)
    try:
        e.send(f"position fen {NO_BOOK_FEN}")
        mark = e.mark()
        t_go = e.send("go ponder wtime 10000 btime 10000")
        time.sleep(2.0)
        pre = e.since(mark)
        t_hit = e.send("ponderhit")
        got = e.wait_for(is_bestmove, cap_s, mark)
        after = e.since(mark)
        idx_best = len(after) - 1 if got else None
        # Anything emitted after bestmove?
        e.wait_quiet(0.5, 2.0)
        tail = e.since(mark)
        post_best = [l.text for l in tail[idx_best + 1:]] if idx_best is not None else []
        rows.append({
            "case": "info_volume_while_pondering",
            "info_lines_before_hit": len(depth_series(pre)),
            "info_ms_before_hit": round((t_hit - t_go) * 1000.0, 1),
            "info_per_s": round(len(depth_series(pre)) / max((t_hit - t_go), 1e-9), 1),
            "bestmove_count_total": len(bestmoves(tail)),
            "lines_after_bestmove": post_best,
            "verdict": "RETURNED" if got else "CAPPED",
        })
        if got is None:
            e.kill()
    finally:
        e.close()

    # 6b: ponderhit then immediate stop - two stop-shaped commands racing.
    for label, cmds in [
        ("ponderhit_then_stop", [("ponderhit", 0.0), ("stop", 0.0)]),
        ("ponderhit_then_stop_50ms", [("ponderhit", 0.0), ("stop", 0.05)]),
        ("stop_then_stop", [("stop", 0.0), ("stop", 0.05)]),
        ("ponderhit_then_ponderhit", [("ponderhit", 0.0), ("ponderhit", 0.2)]),
    ]:
        e = fresh(exe)
        try:
            e.send(f"position fen {NO_BOOK_FEN}")
            mark = e.mark()
            e.send("go ponder wtime 10000 btime 10000")
            time.sleep(0.4)
            for cmd, pause in cmds:
                if pause:
                    time.sleep(pause)
                e.send(cmd)
            got = e.wait_for(is_bestmove, cap_s, mark)
            e.wait_quiet(0.6, 3.0)
            tail = e.since(mark)
            rows.append({
                "case": label, "verdict": "RETURNED" if got else "CAPPED",
                "bestmove_count": len(bestmoves(tail)),
                "bestmove_lines": [l.text for l in bestmoves(tail)],
                "lines_after_last_bestmove": [l.text for l in tail[tail.index(bestmoves(tail)[-1]) + 1:]]
                if bestmoves(tail) else [],
            })
            if got is None:
                e.kill()
        finally:
            e.close()

    # 6c: is `go ponder` after the option Ponder=false still a ponder search?
    #     (the option must not gate the protocol token)
    for option_val in ("false", "true"):
        e = fresh(exe, BASE_OPTIONS + [("Ponder", option_val)])
        try:
            e.send(f"position fen {NO_BOOK_FEN}")
            mark = e.mark()
            e.send("go ponder wtime 10000 btime 10000")
            time.sleep(0.3)
            t_hit = e.send("ponderhit")
            got = e.wait_for(is_bestmove, cap_s, mark)
            rows.append({
                "case": f"go_ponder_token_with_Ponder_{option_val}",
                "verdict": "RETURNED" if got else "CAPPED",
                "t_hit_to_best_ms": round((got[0].t - t_hit) * 1000.0, 1) if got else None,
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
    ap.add_argument("--only", default="p1,p1c,p2,p3,p4,p5,p6")
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    only = set(args.only.split(","))
    clocks = [(10000, 10000), (60000, 60000), (2000, 2000)]
    result = {}

    if "p1" in only:
        print("P1 ponderhit timing ...", flush=True)
        result["p1_ponderhit"] = probe_p1(args.exe, clocks, [0.3, 3.0])
    if "p1c" in only:
        print("P1 control ...", flush=True)
        result["p1_control_no_ponder"] = probe_p1_control(args.exe, clocks, repeats=2)
    if "p2" in only:
        print("P2 stop without ponderhit ...", flush=True)
        result["p2_stop_without_hit"] = probe_p2(args.exe)
    if "p3" in only:
        print("P3 clocked ponder bounded? ...", flush=True)
        result["p3_clocked_ponder"] = probe_p3(args.exe)
    if "p4" in only:
        print("P4 stray ponderhit ...", flush=True)
        result["p4_stray_ponderhit"] = probe_p4(args.exe)
    if "p5" in only:
        print("P5 Ponder option ...", flush=True)
        result["p5_ponder_option"] = probe_p5(args.exe)
    if "p6" in only:
        print("P6 output shape ...", flush=True)
        result["p6_output_shape"] = probe_p6(args.exe)

    path = os.path.join(out, "probe_results.json")
    old = {}
    if os.path.exists(path):
        with open(path) as fh:
            old = json.load(fh)
    old.update(result)
    with open(path, "w") as fh:
        json.dump(old, fh, indent=2, sort_keys=True)
    print("wrote", path)


if __name__ == "__main__":
    main()
