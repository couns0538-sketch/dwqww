"""The four honesty pins. Gate: nothing gets recorded unless all four match.

bench N must arrive on STDIN as a UCI command. `./forge bench 11` as an argv
prints nothing and exits 0 (findings §2), so the argv form is rejected here.
"""

import json
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from engine import Engine  # noqa: E402

PINS = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}
BENCH_RE = re.compile(r"bench depth (\d+) nodes (\d+)")


def run_pins(binary):
    out = {}
    with Engine(binary, hash_mb=64, threads=1) as eng:
        for depth in (11, 13, 16):
            eng.ucinewgame()
            eng.send(f"bench {depth}")
            lines = []
            eng.read_until(lambda l: l.strip() == "readyok" or l.startswith("info string bench"), timeout=600.0, collect=lines)
            seen = None
            for line in lines:
                m = BENCH_RE.search(line)
                if m:
                    seen = int(m.group(2))
            if seen is None:
                raise RuntimeError(f"bench {depth} printed no node line; got {lines[-3:]}")
            out[f"bench{depth}"] = seen
        eng.ucinewgame()
        eng.position(None)
        eng.send("go perft 5")
        lines = []
        eng.read_until(lambda l: re.match(r"^nodes \d+", l) is not None, timeout=600.0, collect=lines)
        total = None
        for line in lines:
            m = re.match(r"^nodes (\d+)", line)
            if m:
                total = int(m.group(1))
        out["perft5"] = total
    return out


def main():
    binary = sys.argv[1]
    got = run_pins(binary)
    ok = all(got.get(k) == v for k, v in PINS.items())
    for k, v in PINS.items():
        print(f"{k:8s} expected {v:>9d}  got {got.get(k)}  {'OK' if got.get(k) == v else 'MISMATCH'}")
    print("PINS", "PASS" if ok else "FAIL")
    print(json.dumps({"build": binary, "expected": PINS, "got": got, "pass": ok}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
