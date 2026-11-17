"""Probe M: the runner-side desync a real match harness can hit.

A runner that starts the next ponder without sending `stop` first gets one
bestmove from the aborted search and one from the new one. Nothing on the wire
labels which is which, so a runner that pairs the FIRST bestmove with the
`ponderhit` it just sent attributes the aborted search's answer to the new
position.

The script measures that directly: two positions with different best moves, so
an attribution error is visible in the move itself rather than in a count.
"""

import argparse
import json
import os
import sys
import time

from uci_driver import Engine, bestmoves, parse_bestmove

# Two positions whose best moves differ (measured in probe H / round 1).
FEN_1 = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 6 6"
# Same board, knight on f3 -> e5 is not legal here, so use a different structure:
# a quiet position where the engine prefers e1g1 at fixed depth 6.
FEN_2 = "rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 2 2"

BASE = [("OwnBook", "false"), ("Threads", "1"), ("Hash", "32"), ("Move Overhead", "10")]


def fresh(exe):
    e = Engine(exe)
    e.uci_handshake()
    for n, v in BASE:
        e.set_option(n, v)
    return e


def run(exe, stop_first, cap_s=30.0):
    e = fresh(exe)
    try:
        e.send(f"position fen {FEN_1}")
        mark = e.mark()
        e.send("go ponder wtime 10000 btime 10000")
        time.sleep(0.8)
        if stop_first:
            e.send("stop")
            got = e.wait_for(lambda s: s.startswith("bestmove"), cap_s, mark)
            if got is None:
                e.kill()
                return {"stop_first": stop_first, "verdict": "CAPPED"}
            e.wait_quiet(0.2, 1.5)
        t_second = e.send(f"position fen {FEN_2}")
        e.send("go ponder wtime 10000 btime 10000")
        time.sleep(0.8)
        t_hit = e.send("ponderhit")
        got = e.wait_for(lambda s: s.startswith("bestmove") and len(bestmoves(e.since(mark))) >= (2 if not stop_first else 2),
                         cap_s, mark)
        e.wait_quiet(0.5, 3.0)
        tail = e.since(mark)
        bms = bestmoves(tail)
        timed = [{"t_rel_second_go_ms": round((b.t - t_second) * 1000.0, 1),
                  "line": b.text,
                  "move": parse_bestmove(b.text)[0]} for b in bms]
        return {
            "stop_first": stop_first,
            "verdict": "RETURNED" if got else "CAPPED",
            "bestmoves": timed,
            "bestmove_count": len(bms),
            "first_bestmove_before_second_go": bool(timed) and timed[0]["t_rel_second_go_ms"] < 0,
            "ambiguous": len(bms) > 1,
        }
    finally:
        e.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="/tmp/forge-build/forge")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "evidence"))
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    res = {"m_desync": [run(args.exe, stop_first=True), run(args.exe, stop_first=False)]}
    path = os.path.join(out, "probe5_results.json")
    with open(path, "w") as fh:
        json.dump(res, fh, indent=2, sort_keys=True)
    print(json.dumps(res, indent=1))
    print("wrote", path)


if __name__ == "__main__":
    main()
