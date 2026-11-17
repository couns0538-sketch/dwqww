"""The four honesty pins. Gate: nothing is recorded unless all four match.

bench N is sent on STDIN as a UCI command. `./forge bench 11` as argv prints
nothing and exits 0 -- the silent no-number trap. Measured wire formats:

  bench N  ->  `info string bench depth N nodes <NODES> time <ms> nps <nps>`
  perft N  ->  `nodes <COUNT>`  (after per-root-move lines)
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucih import Uci

PINS = [("bench 11", 312866),
        ("bench 13", 862329),
        ("bench 16", 3024920),
        ("go perft 5", 4865609)]


def _sync(u):
    u.send("isready")
    while u.readline() != "readyok":
        pass


def run_pins(forge):
    """Return (ok, rows). rows = [(cmd, observed, wanted), ...]."""
    u = Uci(forge, timeout=1800)
    rows = []
    try:
        u.handshake()
        u.send("position startpos")
        _sync(u)
        for cmd, want in PINS:
            u.send(cmd)
            val = None
            if cmd.startswith("bench"):
                while True:
                    line = u.readline(1800)
                    m = re.search(r"bench depth \d+ nodes (\d+) time (\d+)", line)
                    if m:
                        val = int(m.group(1))
                        break
            else:
                while True:
                    line = u.readline(1800)
                    m = re.match(r"nodes\s+(\d+)\s*$", line)
                    if m:
                        val = int(m.group(1))
                        break
            rows.append((cmd, val, want))
            _sync(u)
    finally:
        u.close()
    ok = all(v == w for _, v, w in rows)
    return ok, rows


def main():
    forge = sys.argv[1]
    ok, rows = run_pins(forge)
    for cmd, val, want in rows:
        print(f"{cmd!r:16} observed={val} wanted={want} {'OK' if val == want else 'MISMATCH'}")
    print("PINS", "ALL-MATCH" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
