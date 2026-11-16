#!/usr/bin/env python3
"""analyse_19f7_data.py FILE — recount seat 19's own baseA/baseB times for 19-F7.

Reads the committed `forge-combo29/swarm/19/job2/four_builds_times.txt` (fetched read-only; nothing of
seat 19 is written) and asks: is the 4.2 % difference between baseA and baseB a BUILD difference, or a
shift WITHIN each block of runs?

Evidence for "a shift, not a build":
  - each block is monotone in the sense that its early runs are slow and its late runs are fast;
  - baseA's fast tail (424-426 ms) is exactly the level of baseB's whole block (423-430 ms), so the two
    blocks overlap completely once the drift is removed;
  - the first and last runs of the SAME build differ by more than the two builds' medians do.

Also recounts 19-F7's number: median(baseB)/median(baseA) - 1, and the same after removing each block's
first third (a crude warm-up/state correction).
"""
import statistics
import sys


def parse(path):
    blocks, cur = {}, None
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        if line.endswith(":") and not line[0].isdigit():
            cur = line[:-1]
            blocks[cur] = []
            continue
        p = line.split()
        if len(p) == 3 and cur:
            blocks[cur].append((int(p[0]), int(p[1]), int(p[2])))
    return blocks


def main() -> int:
    blocks = parse(sys.argv[1])
    a = [t for _n, t, _p in blocks["baseA"]]
    b = [t for _n, t, _p in blocks["baseB"]]
    print("| block | n | times (ms, in order) | median | min | max |")
    print("|---|---|---|---|---|---|")
    for name in ("baseA", "baseB"):
        ts = [t for _n, t, _p in blocks[name]]
        print(f"| {name} | {len(ts)} | {ts} | {statistics.median(ts)} | {min(ts)} | {max(ts)} |")

    ma, mb = statistics.median(a), statistics.median(b)
    print()
    print(f"19-F7's number: median(baseA) {ma}, median(baseB) {mb}, "
          f"difference {abs(ma-mb)/ma*100:.1f} %")

    # The drift test: split each block in half and compare halves WITHIN one build.
    for name, ts in (("baseA", a), ("baseB", b)):
        h = len(ts) // 2
        print(f"{name}: first half median {statistics.median(ts[:h])}, "
              f"second half median {statistics.median(ts[h:])}, "
              f"within-build drift {abs(statistics.median(ts[:h])-statistics.median(ts[h:]))}"
              f" ms")

    # Overlap test: is baseA's fast tail at baseB's level?
    a_tail = a[len(a) - 4:]
    print(f"baseA last 4 runs {a_tail} vs baseB whole block median {mb}: "
          f"{'SAME LEVEL' if abs(statistics.median(a_tail) - mb) <= 2 else 'DIFFERENT'}")

    # Same comparison after dropping each block's first third.
    ka = a[len(a) // 3:]
    kb = b[len(b) // 3:]
    print(f"after dropping each block's first third: baseA median {statistics.median(ka)} "
          f"({len(ka)} runs), baseB median {statistics.median(kb)} ({len(kb)} runs), "
          f"difference {abs(statistics.median(ka)-statistics.median(kb))/statistics.median(ka)*100:.2f} %")

    # And the strongest single test: interleave-free comparison of the two builds' OVERLAPPING ranges.
    lo, hi = max(min(a), min(b)), min(max(a), max(b))
    ina = sum(1 for t in a if lo <= t <= hi)
    inb = sum(1 for t in b if lo <= t <= hi)
    print(f"ranges overlap on [{lo}, {hi}] ms: baseA has {ina}/{len(a)} runs there, "
          f"baseB {inb}/{len(b)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
