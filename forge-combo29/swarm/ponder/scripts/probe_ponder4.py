"""Fourth-round probes: protocol edges a match runner can actually hit.

  J. `go ponder depth N` / `go ponder nodes N`: a ponder search whose own
     limit is reached BEFORE ponderhit. Is the bestmove withheld until
     ponderhit/stop, or emitted early (which would desynchronise a runner)?
  K. A terminal / drawn root under `go ponder`: same question, because that
     branch returns from the search immediately.
  L. `ponderhit` arriving after `stop` has already emitted the bestmove for
     the SAME ponder search (a race a real runner hits when the opponent
     moves at the moment stockfish's stop lands).
"""

import argparse
import json
import os
import time

from uci_driver import Engine, bestmoves, info_lines, is_bestmove, parse_bestmove

FEN_A = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 6 6"
# A threefold-repetition root reached by MOVE LIST (findings 7.2d: position fen
# cannot carry repetition history, so this must be a move list).
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


def probe_j_self_limited_ponder(exe, cap_s=20.0):
    rows = []
    for label, go_line, wait in [
        ("ponder_depth6", "go ponder depth 6", 2.5),
        ("ponder_nodes_200000", "go ponder nodes 200000", 2.5),
        ("ponder_depth6_then_hit", "go ponder depth 6", 0.5),
    ]:
        e = fresh(exe)
        try:
            e.send(f"position fen {FEN_A}")
            mark = e.mark()
            t_go = e.send(go_line)
            time.sleep(wait)
            pre = e.since(mark)
            emitted = bestmoves(pre)
            pre_i = infos(pre)
            row = {
                "case": label,
                "bestmove_before_hit": [b.text for b in emitted],
                "bestmove_withheld": len(emitted) == 0,
                "info_lines_before_hit": len(pre_i),
                "last_depth_before_hit": pre_i[-1]["depth"] if pre_i else None,
                "t_to_first_info_ms": round((pre_i and (pre[0].t - t_go) * 1000.0) or 0, 1),
            }
            if emitted:
                row["warn_early_bestmove"] = True
            t_hit = e.send("ponderhit")
            got = e.wait_for(is_bestmove, cap_s, mark)
            row["verdict"] = "RETURNED" if got else "CAPPED"
            row["t_hit_to_best_ms"] = round((got[0].t - t_hit) * 1000.0, 1) if got else None
            row["bestmove_line"] = got[0].text if got else None
            row["bestmove_count"] = len(bestmoves(e.since(mark)))
            row["depth_at_best"] = (infos(e.since(mark)) or [{}])[-1].get("depth")
            rows.append(row)
            if got is None:
                e.kill()
        finally:
            e.close()
    return rows


def probe_k_terminal_root(exe, cap_s=20.0):
    rows = []
    # Reference: what does a NORMAL clocked search do on this drawn root?
    e = fresh(exe)
    try:
        e.send(f"position startpos moves {REP_MOVES}")
        mark = e.mark()
        e.send("go depth 6")
        got = e.wait_for(is_bestmove, cap_s, mark)
        ref = got[0].text if got else None
        ref_i = infos(e.since(mark))
        ref_info = ({"lines": len(ref_i), "first": ref_i[0] if ref_i else None})
    finally:
        e.close()

    # Subject: the same drawn root under go ponder.
    e = fresh(exe)
    try:
        e.send(f"position startpos moves {REP_MOVES}")
        mark = e.mark()
        t_go = e.send("go ponder wtime 10000 btime 10000")
        time.sleep(1.5)
        pre = e.since(mark)
        pre_i = infos(pre)
        early = bestmoves(pre)
        t_hit = e.send("ponderhit")
        got = e.wait_for(is_bestmove, cap_s, mark)
        rows.append({
            "case": "drawn_root_under_ponder",
            "reference_normal_depth6": ref,
            "reference_info": ref_info,
            "bestmove_withheld_during_ponder": len(early) == 0,
            "early_bestmoves": [b.text for b in early],
            "info_lines_during_ponder": len(pre_i),
            "max_depth_during_ponder": max((i["depth"] for i in pre_i), default=None),
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


def probe_l_hit_after_stop(exe, cap_s=20.0):
    rows = []
    for delay in (0.05, 0.3, 1.0):
        e = fresh(exe)
        try:
            e.send(f"position fen {FEN_A}")
            mark = e.mark()
            e.send("go ponder wtime 10000 btime 10000")
            time.sleep(0.5)
            e.send("stop")
            got = e.wait_for(is_bestmove, cap_s, mark)
            best_after_stop = got[0].text if got else None
            e.wait_quiet(0.3, 1.5)
            t_hit = e.send("ponderhit")
            e.wait_quiet(0.6, 3.0)
            tail = e.since(mark)
            # Anything after the hit? And does a FOLLOW-UP search still work?
            mark2 = e.mark()
            e.send(f"position fen {FEN_A}")
            e.send("go depth 5")
            g2 = e.wait_for(is_bestmove, cap_s, mark2)
            rows.append({
                "case": f"stop_then_hit_after_{int(delay*1000)}ms",
                "bestmove_after_stop": best_after_stop,
                "total_bestmoves": len(bestmoves(tail)),
                "output_after_late_hit": [l.text for l in tail if l.t >= t_hit][:4],
                "next_search_ok": g2 is not None,
                "next_search_bestmove": g2[0].text if g2 else None,
                "engine_alive": e.alive(),
            })
            time.sleep(delay)
            if g2 is None:
                e.kill()
        finally:
            e.close()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="/tmp/forge-build/forge")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "evidence"))
    ap.add_argument("--only", default="j,k,l")
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    only = set(args.only.split(","))
    res = {}
    if "j" in only:
        print("J self-limited ponder ...", flush=True)
        res["j_self_limited_ponder"] = probe_j_self_limited_ponder(args.exe)
    if "k" in only:
        print("K terminal root ...", flush=True)
        res["k_terminal_root"] = probe_k_terminal_root(args.exe)
    if "l" in only:
        print("L late ponderhit ...", flush=True)
        res["l_hit_after_stop"] = probe_l_hit_after_stop(args.exe)
    path = os.path.join(out, "probe4_results.json")
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
