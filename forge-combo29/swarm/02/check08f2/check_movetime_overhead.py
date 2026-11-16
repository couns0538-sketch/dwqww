#!/usr/bin/env python3
"""S02 check of 08-F2 (seat 08, area 8): "go movetime T searches for T - Move Overhead".

That finding states a NUMBER (median 40.4 ms at movetime 50). A number alone does not distinguish the two
possible causes:
  (a) the engine subtracts Move Overhead from movetime (search.cpp:2192), or
  (b) the engine simply stops a fixed fraction early (e.g. a 0.8 factor anywhere in the time manager).
So this check tests the MECHANISM instead: measure the same `go movetime T` twice, once with
Move Overhead at its default 10 and once with `setoption name Move Overhead value 0`.
If (a) is the cause, the second run must move to ~T and the difference must be ~10 ms in BOTH cases.
If (b) is the cause, Move Overhead 0 changes nothing and the gap stays ~10 ms below T.

Harness written from the finding's SENTENCE, not from seat 08's script (their clock_latency.py was not read).
"""
import json
import os
import statistics
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/base/forge-combo29/build/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out_check08"
POSITIONS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
]
TRIALS = 12


def one(proc, lines, timeout=20.0):
    """send the setup lines, then `go`, and time from writing `go` to reading `bestmove`."""
    for l in lines[:-1]:
        proc.stdin.write(l + "\n")
        proc.stdin.flush()
    go = lines[-1]
    t0 = time.monotonic()
    proc.stdin.write(go + "\n")
    proc.stdin.flush()
    buf = []
    deadline = t0 + timeout
    while time.monotonic() < deadline:
        line = proc.stdout.readline()
        if not line:
            break
        buf.append(line.rstrip("\n"))
        if line.startswith("bestmove"):
            return time.monotonic() - t0, "\n".join(buf)
    return None, "\n".join(buf)


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {
        "exe": EXE,
        "sha256": subprocess.run(["sha256sum", EXE], capture_output=True, text=True).stdout.split()[0],
        "trials_per_cell": TRIALS,
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "positions": POSITIONS,
        "options_sent": ["setoption name OwnBook value false",
                         "setoption name Move Overhead value <10|0>"],
        "note": "wall time measured with time.monotonic() from writing the go line to reading the bestmove line",
    }
    json.dump(meta, open(os.path.join(OUT, "meta.json"), "w"), indent=1)

    results = {}
    for movetime in (50, 200):
        for overhead in (10, 0):
            key = "%d_ov%d" % (movetime, overhead)
            rows = []
            proc = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, bufsize=1)
            for _ in range(TRIALS):
                for pos in POSITIONS:
                    wall, text = one(proc, [
                        "setoption name OwnBook value false",
                        "setoption name Move Overhead value %d" % overhead,
                        "position fen " + pos,
                        "isready",
                        "go movetime %d" % movetime])
                    rows.append({"pos": pos[:30], "wall_s": wall, "out": text})
            proc.stdin.write("quit\n")
            proc.stdin.flush()
            proc.wait(timeout=30)
            walls = [r["wall_s"] * 1000.0 for r in rows if r["wall_s"] is not None]
            # INTEGRITY GUARD (seat 19's warning): a cell with missing measurements must never be able to
            # produce a number that reads like a result. Anything less than the full set is a hard failure.
            expected = TRIALS * len(POSITIONS)
            if len(walls) != expected:
                sys.exit("FAIL cell %s: %d of %d searches measured; the missing ones would silently "
                         "disappear from the median. Fix the harness, do not report this number."
                         % (key, len(walls), expected))
            if not walls:
                sys.exit("FAIL cell %s: no measurements at all" % key)
            for v in walls:
                if v != v or v in (float("inf"), float("-inf")):  # NaN / inf can never pass as a result
                    sys.exit("FAIL cell %s: non-finite measurement %r" % (key, v))
            # the engine must have printed a bestmove for every search, or the "wall time" is the
            # time until something else happened
            no_bm = [r for r in rows if "bestmove" not in (r.get("out") or "")]
            if no_bm:
                sys.exit("FAIL cell %s: %d searches produced no bestmove line" % (key, len(no_bm)))
            results[key] = walls
            json.dump(rows, open(os.path.join(OUT, "raw_%s.json" % key), "w"), indent=1)
            print("%-10s n=%2d median %7.2f ms  mean %7.2f  min %7.2f  max %7.2f"
                  % (key, len(walls), statistics.median(walls), statistics.mean(walls),
                     min(walls), max(walls)))

    print()
    print("| cell | n | median ms | mean ms | gap to the movetime |")
    print("|---|---|---|---|---|")
    lines_out = []
    for movetime in (50, 200):
        for overhead in (10, 0):
            key = "%d_ov%d" % (movetime, overhead)
            w = results[key]
            med = statistics.median(w)
            lines_out.append("| movetime %d, Move Overhead %d | %d | %.2f | %.2f | %.2f |"
                             % (movetime, overhead, len(w), med, statistics.mean(w), movetime - med))
    text = "\n".join(lines_out)
    print(text)
    open(os.path.join(OUT, "table.md"), "w").write(
        "| cell | n | median ms | mean ms | gap to the movetime |\n|---|---|---|---|---|\n" + text + "\n")
    verdict(results)


def verdict(results):
    """Print CONFIRMS / REFUTES only after asserting the numbers exist and the control moved.

    This is the guard seat 19's warning asks for: no empty list, no NaN, no missing line may reach a
    verdict. If a needed number is absent the function exits non-zero instead of guessing."""
    for mt in (50, 200):
        for ov in (10, 0):
            key = "%d_ov%d" % (mt, ov)
            if key not in results or not results[key]:
                sys.exit("FAIL verdict: cell %s missing; cannot confirm or refute" % key)
    gaps = {}
    for mt in (50, 200):
        for ov in (10, 0):
            w = results["%d_ov%d" % (mt, ov)]
            gaps[(mt, ov)] = mt - statistics.median(w)
    # CLAIM: the gap with overhead 10 is ~10 ms and is an ABSOLUTE amount, the same at both movetimes
    g50_10, g200_10 = gaps[(50, 10)], gaps[(200, 10)]
    g50_0, g200_0 = gaps[(50, 0)], gaps[(200, 0)]
    if any(v != v for v in (g50_10, g200_10, g50_0, g200_0)):
        sys.exit("FAIL verdict: a gap is NaN")
    checks = {
        "gap at movetime 50 overhead 10 is 8..12 ms": 8.0 <= g50_10 <= 12.0,
        "gap at movetime 200 overhead 10 is 8..12 ms": 8.0 <= g200_10 <= 12.0,
        "the two gaps differ by under 1.5 ms (absolute, not a fraction)": abs(g50_10 - g200_10) < 1.5,
        "overhead 0 gap at movetime 50 is under 2 ms": abs(g50_0) < 2.0,
        "overhead 0 gap at movetime 200 is under 2 ms": abs(g200_0) < 2.0,
    }
    print()
    print("### verdict checks (each must pass, printed by the script that measured them)")
    for name, ok in checks.items():
        print("- %-58s %s" % (name, "PASS" if ok else "FAIL"))
    if not all(checks.values()):
        sys.exit("CONCLUSION: REFUTES 08-F2 (at least one mechanism check failed)")
    print()
    print("CONCLUSION: CONFIRMS 08-F2 — the loss is the absolute Move Overhead, and zeroing the option removes it.")


if __name__ == "__main__":
    main()
