"""The decisive, race-free test of what `time` counts from on the ponder path.

`Worker::elapsed_ms()` -- the clock that enforces the budget -- returns 0 while a
ponder search has no ponderhit:

    std::int64_t Worker::elapsed_ms() const {
        auto origin = start_;
        if (pondering_) {
            const std::int64_t hit_ns = shared_.ponder_hit_ns.load(...);
            if (hit_ns == 0) return 0;          // <-- budget clock reads ZERO
            origin = ...hit_ns...;
        }
        ...

But `emit` does not call elapsed_ms(); it recomputes from `start_`:

    const std::int64_t elapsed = duration_cast<milliseconds>(
        steady_clock::now() - start_).count();   // <-- counts from `go`

So DURING a ponder (before ponderhit), the engine should publish `time` > 0 and
a non-zero `nps` while its own budget clock is pinned at 0.

That is observable without any stop race: read the lines the engine emits while
it is still pondering. If any such line shows time > 0, the two clocks disagree
by construction, and the size of that disagreement is the ponder wait.

Control: the same reading on a non-ponder search, where both clocks share one
origin -- there, `time` must equal the wall clock since `go`.
"""

import json
import os
import time

import uci

ENGINE = os.environ.get("FORGE_BIN", "/agent/repos/work-infofields/build/forge")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
SET = {"build": "g++ -DFORGE_MARCH=x86-64-v4 Release NDEBUG", "base_commit": "6b98f217",
       "threads": 1, "hash_mb": "default 32", "own_book": False, "fen": "startpos"}
SNAP_AT = (0.5, 1.0, 2.0, 3.0, 4.5)


def drain(e, budget_s=0.15):
    got = []
    deadline = time.monotonic() + budget_s
    while time.monotonic() < deadline:
        try:
            got.append(e.lines.get(timeout=0.02))
        except Exception:
            break
    return [g for g in got if g and g.startswith("info depth")]


def parse_time(line):
    f, _ = uci.parse_info(line)
    return int(f["time"]), int(f["nps"]), int(f["nodes"])


def main():
    e = uci.Engine(ENGINE)
    e.handshake()
    e.setoption("OwnBook", "false")
    e.position()

    t0 = time.monotonic()
    e.send("go ponder wtime 600000 btime 600000")

    snapshots = []
    # consume as we go so the queue never lags behind the search
    last_seen = None
    next_at = list(SNAP_AT)
    while next_at:
        target = next_at[0]
        remaining = target - (time.monotonic() - t0)
        if remaining > 0:
            time.sleep(min(remaining, 0.05))
        batch = drain(e, 0.02)
        if batch:
            last_seen = batch[-1]
        if time.monotonic() - t0 >= target:
            wall = time.monotonic() - t0
            rec = {"wall_since_go_s": round(wall, 3), "last_line": last_seen}
            if last_seen:
                tm, nps, nodes = parse_time(last_seen)
                rec.update({"reported_time_ms": tm, "reported_nps": nps,
                            "reported_nodes": nodes,
                            "reported_time_vs_wall_ms": tm - round(wall * 1000)})
            snapshots.append(rec)
            next_at.pop(0)

    # now hit and finish
    e.send("ponderhit")
    rest = e.read_until(lambda l: l.startswith("bestmove"), timeout=180)
    final = [l for l in rest if l.startswith("info depth")]
    final_rec = None
    if final:
        tm, nps, nodes = parse_time(final[-1])
        final_rec = {"reported_time_ms": tm, "reported_nps": nps,
                     "reported_nodes": nodes, "last_line": final[-1]}
    e.quit()

    # control: no ponder, same kind of snapshot
    c = uci.Engine(ENGINE)
    c.handshake()
    c.setoption("OwnBook", "false")
    c.position()
    t0c = time.monotonic()
    c.send("go infinite")
    ctrl = []
    for target in SNAP_AT:
        remaining = target - (time.monotonic() - t0c)
        if remaining > 0:
            time.sleep(min(remaining, 0.05))
        batch = drain(c, 0.02)
        if batch:
            tm, nps, nodes = parse_time(batch[-1])
            ctrl.append({"wall_since_go_s": round(time.monotonic() - t0c, 3),
                         "reported_time_ms": tm, "reported_nps": nps})
    c.send("stop")
    c.read_until(lambda l: l.startswith("bestmove"), timeout=120)
    c.quit()

    payload = {"settings": SET, "go": "go ponder wtime 600000 btime 600000",
               "snapshots_during_ponder": snapshots,
               "final_after_ponderhit": final_rec,
               "control_go_infinite_snapshots": ctrl,
               "budget_clock_during_ponder_per_source": 0}
    with open(os.path.join(OUT, "time_during_ponder.json"), "w") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)

    print("DURING PONDER (budget clock elapsed_ms() is hard-coded to 0 here):")
    print("  wall_since_go  reported `time`  reported nps  time-wall")
    for s in snapshots:
        if "reported_time_ms" in s:
            print("  %-13.2f  %-15d  %-12d  %+d ms" % (
                s["wall_since_go_s"], s["reported_time_ms"], s["reported_nps"],
                s["reported_time_vs_wall_ms"]))
    print("\nCONTROL go infinite (both clocks share one origin):")
    for s in ctrl:
        print("  wall %-5.2f -> time %-6d nps %d" % (
            s["wall_since_go_s"], s["reported_time_ms"], s["reported_nps"]))
    if final_rec:
        print("\nfinal after ponderhit: time %d ms, nodes %d" % (
            final_rec["reported_time_ms"], final_rec["reported_nodes"]))


if __name__ == "__main__":
    main()
