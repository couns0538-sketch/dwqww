"""Third-round probes: the residuals that decide how to word the claims.

  F. A clean three-clock table at one fixed ponder duration, so the
     ponderhit->bestmove column is apples-to-apples across clocks.
  G. Does `Ponder=true` make the engine ponder on its own after a bestmove?
     (Control: the same search with Ponder=false, which must be silent.)
  H. What is the `a2a3`-with-no-info-line answer after `stop` at 0 ms?
     The findings report says a 0-node `a2a3` is the EOF abort, so this must
     be told apart from that: same command on TWO positions whose first legal
     move differs, plus a perft-1 order reference, plus the EOF-abort control
     for comparison. A fixed fabrication would not track the position.
  I. The `time` field origin: does the info `time` count the ponder?
"""

import argparse
import json
import os
import time

from uci_driver import Engine, bestmoves, info_lines, is_bestmove, parse_bestmove

# White to move; first legal move in this engine's generator order is not a2a3
# (that is what H measures, not assumes).
FEN_A = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 6 6"
# Black to move, lone-king-ish endgame: a completely different first legal move.
FEN_B = "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1"

BASE = [("OwnBook", "false"), ("Threads", "1"), ("Hash", "32"), ("Move Overhead", "10")]


def fresh(exe, options=None):
    e = Engine(exe)
    e.uci_handshake()
    for n, v in (options if options is not None else BASE):
        e.set_option(n, v)
    return e


def infos(lines):
    return [i for _, i in info_lines(lines) if i and "depth" in i]


def probe_f_three_clocks(exe, clocks=(2000, 10000, 60000), ponder_s=2.0, cap_s=60.0):
    rows = []
    for clock in clocks:
        e = fresh(exe)
        try:
            e.send(f"position fen {FEN_A}")
            mark = e.mark()
            e.send(f"go ponder wtime {clock} btime {clock}")
            time.sleep(ponder_s)
            pre_i = infos(e.since(mark))
            t_hit = e.send("ponderhit")
            got = e.wait_for(is_bestmove, cap_s, mark)
            if got is None:
                rows.append({"clock": clock, "verdict": "CAPPED", "cap_s": cap_s})
                e.kill()
                continue
            post_i = infos(e.since(mark))
            soft = (clock - 10) // 22
            hard = min((clock - 10) * 60 // 100, soft * 5)
            rows.append({
                "clock": clock, "ponder_s": ponder_s, "verdict": "RETURNED",
                "t_hit_to_best_ms": round((got[0].t - t_hit) * 1000.0, 1),
                "planned_soft_ms": soft, "planned_hard_ms": hard,
                "hit_to_best_over_hard": round((got[0].t - t_hit) * 1000.0 / hard, 3),
                "depth_at_hit": pre_i[-1]["depth"] if pre_i else None,
                "depth_at_best": post_i[-1]["depth"] if post_i else None,
                "bestmove": parse_bestmove(got[0].text)[0],
                "bestmove_count": len(bestmoves(e.since(mark))),
            })
        finally:
            e.close()
    return rows


def probe_g_self_ponder(exe, cap_s=30.0):
    rows = []
    for pon in ("false", "true"):
        e = fresh(exe, BASE + [("Ponder", pon)])
        try:
            e.send(f"position fen {FEN_A}")
            mark = e.mark()
            t0 = e.send("go wtime 2000 btime 2000")
            got = e.wait_for(is_bestmove, cap_s, mark)
            if got is None:
                rows.append({"Ponder": pon, "verdict": "CAPPED"})
                e.kill()
                continue
            idx = e.since(mark).index(got[0])
            # Watch for 3 s after bestmove: an engine that ponder-on-own would
            # keep emitting info lines or later a bestmove.
            e.wait_quiet(3.0, 5.0)
            tail = e.since(mark)
            rows.append({
                "Ponder": pon,
                "verdict": "RETURNED",
                "bestmove_line": got[0].text,
                "t_bestmove_ms": round((got[0].t - t0) * 1000.0, 1),
                "lines_after_bestmove": [l.text for l in tail[idx + 1:]],
                "info_lines_after_bestmove": len([l for l in tail[idx + 1:] if l.text.startswith("info depth")]),
                "second_bestmove": [l.text for l in bestmoves(tail[idx + 1:])],
                "self_pondered": len([l for l in tail[idx + 1:] if l.text.startswith("info")]) > 0,
            })
        finally:
            e.close()
    return rows


def probe_h_zero_ms_stop(exe, cap_s=20.0):
    """The degenerate answer after an immediate stop, on two positions."""
    rows = []
    for label, fen in (("position_A_white", FEN_A), ("position_B_black", FEN_B)):
        # Reference 1: the engine's own legal-move order at perft 1.
        e = fresh(exe)
        try:
            e.send(f"position fen {fen}")
            mark = e.mark()
            e.send("go perft 1")
            got = e.wait_for(lambda s: s.startswith("nodes "), 20.0, mark)
            order = [l.text.split(":")[0] for l in e.since(mark) if ":" in l.text and l.text.endswith(tuple("0123456789"))]
            nodes_line = got[0].text if got else None
        finally:
            e.close()

        # Reference 2: a `go depth 1` search, i.e. a real one-ply answer.
        e = fresh(exe)
        try:
            e.send(f"position fen {fen}")
            mark = e.mark()
            e.send("go depth 1")
            g2 = e.wait_for(is_bestmove, 20.0, mark)
            depth1 = g2[0].text if g2 else None
        finally:
            e.close()

        # Subject: go ponder, stop at 0 ms, stdin never closed.
        e = fresh(exe)
        try:
            e.send(f"position fen {fen}")
            mark = e.mark()
            e.send("go ponder wtime 10000 btime 10000")
            t0 = e.send("stop")
            got = e.wait_for(is_bestmove, cap_s, mark)
            zero_stop = got[0].text if got else None
            zero_info = len(infos(e.since(mark)))
            zero_ms = round((got[0].t - t0) * 1000.0, 1) if got else None
            if got is None:
                e.kill()
        finally:
            e.close()

        # Control: the EOF abort the findings describe - close stdin mid-search.
        e = Engine(exe)
        e.uci_handshake()
        for n, v in BASE:
            e.set_option(n, v)
        e.send(f"position fen {fen}")
        mark = e.mark()
        e.send("go ponder wtime 10000 btime 10000")
        time.sleep(0.3)
        eof_info = len(infos(e.since(mark)))
        e.proc.stdin.close()
        got = e.wait_for(is_bestmove, cap_s, mark)
        eof_best = got[0].text if got else None
        if got is None:
            e.kill()
        else:
            e.close()

        rows.append({
            "case": label, "fen": fen,
            "perft1_order_head": order[:4], "perft1_total": nodes_line,
            "depth1_bestmove": depth1,
            "zero_ms_stop_bestmove": zero_stop,
            "zero_ms_stop_info_lines": zero_info,
            "zero_ms_stop_ms": zero_ms,
            "eof_abort_bestmove": eof_best,
            "eof_abort_info_lines_before_eof": eof_info,
            "zero_stop_equals_first_legal": (zero_stop.split()[1] == order[0]) if (zero_stop and order) else None,
            "zero_stop_equals_eof_abort": zero_stop == eof_best,
            "zero_stop_is_0000": (zero_stop.split()[1] == "0000") if zero_stop else None,
        })
    return rows


def probe_i_time_field(exe, cap_s=60.0):
    """Does the info `time` field count the ponder, or restart at the hit?"""
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
            rows.append({
                "ponder_s": ps, "verdict": "RETURNED",
                "last_time_before_hit_ms": pre[-1].get("time") if pre else None,
                "first_time_after_hit_ms": new[0].get("time") if new else None,
                "last_time_at_best_ms": post[-1].get("time") if post else None,
                "wall_from_go_to_best_ms": round((got[0].t - t_go) * 1000.0, 1),
                "wall_from_hit_to_best_ms": round((got[0].t - t_hit) * 1000.0, 1),
                "time_field_tracks_go": None,  # filled below
                "post_hit_time_values": [i.get("time") for i in new],
            })
            last = post[-1].get("time") if post else None
            wall_go = round((got[0].t - t_go) * 1000.0, 1)
            rows[-1]["time_field_tracks_go"] = (
                last is not None and abs(last - wall_go) < 250)
        finally:
            e.close()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="/tmp/forge-build/forge")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "evidence"))
    ap.add_argument("--only", default="f,g,h,i")
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    only = set(args.only.split(","))
    res = {}
    if "f" in only:
        print("F three clocks ...", flush=True)
        res["f_three_clocks"] = probe_f_three_clocks(args.exe)
    if "g" in only:
        print("G self-ponder ...", flush=True)
        res["g_self_ponder"] = probe_g_self_ponder(args.exe)
    if "h" in only:
        print("H zero-ms stop ...", flush=True)
        res["h_zero_ms_stop"] = probe_h_zero_ms_stop(args.exe)
    if "i" in only:
        print("I time field ...", flush=True)
        res["i_time_field"] = probe_i_time_field(args.exe)
    path = os.path.join(out, "probe3_results.json")
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
