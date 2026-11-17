#!/usr/bin/env python3
"""Verify the documented bench pins and perft on a binary.

LOCK.md records, for Threads 1 / Hash 16 / OwnBook false:

  net on  (UseNNUE true):  312866 / 862329 / 3024920 / 12389307 / 34048354
  net off (UseNNUE false): 375354 / 907205 / 2448617 / 13573040 / 24506465
  perft 5 startpos:        4865609

at bench depths 11 / 13 / 16 / 20 / 22.

This prints one line per (net, depth) and exits 1 on any mismatch, so a patch
cannot be called search-neutral unless it reproduces every documented pin.

Note: `bench` is run with Hash 16 and Threads 1 as LOCK.md specifies; the engine
advertises Hash 32 by default, and a different table size changes nothing here
because the pins were taken at 16. Both settings are checked once so the choice is
visible in the output.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine  # noqa: E402

DEPTHS = (11, 13, 16, 20, 22)
PINS = {
    "true":  (312866, 862329, 3024920, 12389307, 34048354),
    "false": (375354, 907205, 2448617, 13573040, 24506465),
}
PERFT5 = 4865609


def bench(binary: str, use_nnue: str, depth: int) -> int | None:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        eng.setoption("Hash", "16")
        eng.setoption("Threads", "1")
        eng.setoption("OwnBook", "false")
        eng.setoption("UseNNUE", use_nnue)
        # `bench` prints `info string bench depth D nodes N ...` and no bestmove,
        # so wait for that line rather than for bestmove.
        eng.send(f"bench {depth}")
        r = eng.read_until(lambda ln: "bench depth" in ln, timeout=600.0)
        if r.timed_out:
            return None
        m = re.search(r"nodes (\d+)", "\n".join(r.lines))
        return int(m.group(1)) if m else None
    finally:
        eng.quit()


def perft5(binary: str) -> int | None:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.position_checked("startpos")
        eng.send("go perft 5")
        r = eng.read_until(lambda ln: ln.startswith("nodes "), timeout=600.0)
        if r.timed_out:
            return None
        for ln in reversed(r.lines):
            if ln.startswith("nodes "):
                return int(ln.split()[1])
        return None
    finally:
        eng.quit()


def main() -> int:
    binary = sys.argv[1] if len(sys.argv) > 1 else "/tmp/b6b98build/forge"
    print(f"binary {binary}")
    print(f"{'net':<6} {'depth':>5} {'expected':>10} {'got':>10}  result")
    bad = 0
    for net, expected in PINS.items():
        for depth, want in zip(DEPTHS, expected):
            got = bench(binary, net, depth)
            ok = got == want
            bad += 0 if ok else 1
            print(f"{net:<6} {depth:>5} {want:>10} {str(got):>10}  {'OK' if ok else 'MISMATCH'}")

    p = perft5(binary)
    ok = p == PERFT5
    bad += 0 if ok else 1
    print(f"{'perft5':<6} {'-':>5} {PERFT5:>10} {str(p):>10}  {'OK' if ok else 'MISMATCH'}")

    print()
    if bad:
        print(f"{bad} pin mismatch(es) — this binary is NOT the lock's node behaviour")
        return 1
    print("all 11 documented pins reproduce")
    return 0


if __name__ == "__main__":
    sys.exit(main())
