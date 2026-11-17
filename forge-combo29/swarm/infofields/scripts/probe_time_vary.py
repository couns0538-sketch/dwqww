"""`time` vs the budget on the ponder path, with the wait varied.

UCI defines the `time` field as "the time spent searching so far, in
milliseconds". It does not say "since the go command", but a search that has not
started (still pondering, no ponderhit) has spent no budget, and the engine's own
budget clock (`elapsed_ms()`) restarts at ponderhit. So a client pairs `time`
with the time control it sent; if `time` counts from `go` while the budget
counts from `ponderhit`, the two disagree by exactly the ponder wait.

Test: hold the budget fixed at movetime 1000 and vary the ponder wait. If the
final `time` grows one-for-one with the wait, `time` counts from `go`.

Control: the same budget with no ponder at all, which must report ~990 ms.
"""

import json
import os
import time

import uci

ENGINE = os.environ.get("FORGE_BIN", "/agent/repos/work-infofields/build/forge")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
SET = {"build": "g++ -DFORGE_MARCH=x86-64-v4 Release NDEBUG", "base_commit": "6b98f217",
       "threads": 1, "hash_mb": "default 32", "own_book": False,
       "fen": "startpos", "move_overhead_ms": 10}


def last_time(lines):
    rows = [l for l in lines if l.startswith("info depth")]
    if not rows:
        return None, None
    for l in rows:
        pass
    f, _ = uci.parse_info(rows[-1])
    return int(f["time"]), rows[-1]


def run_ponder(wait_s, movetime):
    e = uci.Engine(ENGINE)
    e.handshake()
    e.setoption("OwnBook", "false")
    e.position()
    t_go = time.monotonic()
    e.send("go ponder movetime %d" % movetime)
    time.sleep(wait_s)
    t_hit = time.monotonic()
    e.send("ponderhit")
    lines = e.read_until(lambda l: l.startswith("bestmove"), timeout=180)
    t_end = time.monotonic()
    e.quit()
    return {"wait_s": round(t_hit - t_go, 3),
            "after_hit_s": round(t_end - t_hit, 3),
            "reported_time_ms": last_time(lines)[0],
            "last_line": last_time(lines)[1]}


def run_ordinary(movetime):
    e = uci.Engine(ENGINE)
    e.handshake()
    e.setoption("OwnBook", "false")
    e.position()
    t0 = time.monotonic()
    lines, bm = e.search("movetime %d" % movetime, timeout=120)
    wall = time.monotonic() - t0
    e.quit()
    return {"wall_s": round(wall, 3), "reported_time_ms": last_time(lines)[0],
            "last_line": last_time(lines)[1]}


def main():
    budget = 1000
    control = run_ordinary(budget)
    trials = []
    for wait in (0.5, 1.0, 2.0, 3.0, 4.0):
        r = run_ponder(wait, budget)
        r["budget_ms"] = budget - SET["move_overhead_ms"]
        r["excess_over_budget_ms"] = (r["reported_time_ms"] or 0) - (budget - 10)
        r["excess_minus_wait_ms"] = r["excess_over_budget_ms"] - round(r["wait_s"] * 1000)
        trials.append(r)

    payload = {"settings": SET, "budget_movetime_ms": budget,
               "control_no_ponder": control, "ponder_trials": trials}
    with open(os.path.join(OUT, "time_ponder_vary.json"), "w") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)

    print("control (no ponder, movetime %d): reported %s ms, wall %.2fs" % (
        budget, control["reported_time_ms"], control["wall_s"]))
    print("\nponder wait vs reported `time` (budget fixed at %d ms, budget clock = %d ms):" % (
        budget, budget - 10))
    print("  wait_s  after_hit_s  reported_ms  excess_over_budget  excess_minus_wait")
    for t in trials:
        print("  %-6.2f  %-11.3f  %-11s  %-19s  %s" % (
            t["wait_s"], t["after_hit_s"], t["reported_time_ms"],
            t["excess_over_budget_ms"], t["excess_minus_wait_ms"]))
    print("\nInterpretation: if excess_minus_wait is ~0, `time` counts the ponder")
    print("wait; the budget does not. The two clocks differ by the whole wait.")


if __name__ == "__main__":
    main()
