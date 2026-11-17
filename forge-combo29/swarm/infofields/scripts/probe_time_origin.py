"""A clean discriminator for what the `time` field counts from.

The earlier test (fixed movetime, varied ponder wait) is confounded: the final
`time` is stamped when the last COMPLETED iteration ended, which can be well
before the stop fires, so the excess over the budget is not the wait.

Clean design -- hold the stop instant fixed and move only the ponderhit:

    t0        : go ponder wtime 600000 btime 600000     (no budget will fire)
    t0 + W    : ponderhit
    t0 + W + X: stop

Then read the last info line's `time`. With W and X known:

    counts from `go`   -> time ~= W + X
    counts from `hit`  -> time ~= X

X is chosen large (4 s) so the two predictions are far apart and cannot be
confused by one iteration's latency. A no-ponder control with the same X
validates the harness: there, both predictions coincide, and time should be ~X.
"""

import json
import os
import time

import uci

ENGINE = os.environ.get("FORGE_BIN", "/agent/repos/work-infofields/build/forge")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
SET = {"build": "g++ -DFORGE_MARCH=x86-64-v4 Release NDEBUG", "base_commit": "6b98f217",
       "threads": 1, "hash_mb": "default 32", "own_book": False, "fen": "startpos"}


def last_info(lines):
    rows = [l for l in lines if l.startswith("info depth")]
    if not rows:
        return None, None
    f, _ = uci.parse_info(rows[-1])
    return int(f["time"]), rows[-1]


def ponder_case(wait_s, extra_s):
    e = uci.Engine(ENGINE)
    e.handshake()
    e.setoption("OwnBook", "false")
    e.position()
    t0 = time.monotonic()
    e.send("go ponder wtime 600000 btime 600000")
    time.sleep(wait_s)
    t_hit = time.monotonic()
    e.send("ponderhit")
    time.sleep(extra_s)
    e.send("stop")
    lines = e.read_until(lambda l: l.startswith("bestmove"), timeout=180)
    t_stop = time.monotonic()
    e.quit()
    tm, line = last_info(lines)
    return {
        "go_to_hit_s": round(t_hit - t0, 3),
        "hit_to_stop_s": round(t_stop - t_hit, 3),
        "go_to_stop_s": round(t_stop - t0, 3),
        "reported_time_ms": tm,
        "predicted_from_go_ms": round((t_stop - t0) * 1000),
        "predicted_from_hit_ms": round((t_stop - t_hit) * 1000),
        "error_from_go_ms": None if tm is None else tm - round((t_stop - t0) * 1000),
        "error_from_hit_ms": None if tm is None else tm - round((t_stop - t_hit) * 1000),
        "last_line": line,
    }


def ordinary_case(extra_s):
    """Control: no ponder. time must track the wall clock from `go`."""
    e = uci.Engine(ENGINE)
    e.handshake()
    e.setoption("OwnBook", "false")
    e.position()
    t0 = time.monotonic()
    e.send("go infinite")
    time.sleep(extra_s)
    e.send("stop")
    lines = e.read_until(lambda l: l.startswith("bestmove"), timeout=180)
    t_stop = time.monotonic()
    e.quit()
    tm, line = last_info(lines)
    return {"go_to_stop_s": round(t_stop - t0, 3), "reported_time_ms": tm,
            "predicted_from_go_ms": round((t_stop - t0) * 1000),
            "error_from_go_ms": None if tm is None else tm - round((t_stop - t0) * 1000),
            "last_line": line}


def main():
    control = ordinary_case(4.0)
    trials = []
    for wait in (0.0, 1.0, 3.0, 6.0):
        t = ponder_case(wait, 4.0)
        t["wait_s"] = wait
        trials.append(t)

    payload = {"settings": SET, "control_go_infinite": control, "ponder_trials": trials}
    with open(os.path.join(OUT, "time_origin.json"), "w") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)

    print("CONTROL (go infinite, stop after 4s, no ponder):")
    print("  reported %s ms; wall from go %s ms; error %s ms" % (
        control["reported_time_ms"], control["predicted_from_go_ms"],
        control["error_from_go_ms"]))
    print("\nPONDER (hit at W, stop 4s after hit):")
    print("  W    go->stop  reported  err_from_go  err_from_hit   verdict")
    for t in trials:
        verdict = ("counts from GO" if abs(t["error_from_go_ms"]) < abs(t["error_from_hit_ms"])
                   else "counts from HIT")
        print("  %-4.1f %-9.2f %-9s %-12d %-13d %s" % (
            t["wait_s"], t["go_to_stop_s"], t["reported_time_ms"],
            t["error_from_go_ms"], t["error_from_hit_ms"], verdict))
    print("\nThe 4 s separation makes the two predictions differ by the whole wait,")
    print("so a single reading discriminates without relying on iteration latency.")


if __name__ == "__main__":
    main()
