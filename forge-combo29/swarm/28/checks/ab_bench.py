#!/usr/bin/env python3
"""ab_bench.py EXE_A EXE_B ROUNDS OUTDIR — alternating bench-13 runs, A B A B ...

Each run is a fresh process (`printf 'ucinewgame\\nbench 13\\nquit'`), reading the engine's own
`time` and `nps` fields from its `info string bench` line. Reports medians, the paired ratio and a
bootstrap 95 % interval for it.

Usage: ab_bench.py EXE_A EXE_B ROUNDS OUTDIR
"""
import os
import random
import re
import statistics
import subprocess
import sys

LINE = re.compile(r"bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)")


def run(exe):
    out = subprocess.run(["bash", "-c", f"printf 'ucinewgame\\nbench 13\\nquit\\n' | {exe}"],
                         capture_output=True, text=True, check=True).stdout
    m = LINE.search(out)
    if not m:
        raise SystemExit(f"no bench line from {exe}: {out[-300:]}")
    return int(m.group(2)), int(m.group(3)), int(m.group(4))


def main() -> int:
    a, b, rounds, outdir = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    run(a)
    run(b)
    for i in range(rounds):
        na, ta, pa = run(a)
        nb, tb, pb = run(b)
        rows.append((i, na, ta, pa, nb, tb, pb))
        print(f"{i}\tA nodes={na} time={ta} nps={pa}\tB nodes={nb} time={tb} nps={pb}", flush=True)
    with open(os.path.join(outdir, "ab_runs.tsv"), "w") as fh:
        fh.write("round\ta_nodes\ta_time\ta_nps\tb_nodes\tb_time\tb_nps\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")

    ta = [r[2] for r in rows]
    tb = [r[5] for r in rows]
    pa = [r[3] for r in rows]
    pb = [r[6] for r in rows]
    ma, mb = statistics.median(ta), statistics.median(tb)
    print()
    print(f"nodes all equal: {len({r[1] for r in rows} | {r[4] for r in rows}) == 1} "
          f"(value {rows[0][1]})")
    print(f"A time median {ma} ms, B time median {mb} ms")
    print(f"A nps median {statistics.median(pa)}, B nps median {statistics.median(pb)}")
    ratio = mb / ma
    print(f"median ratio B/A (time) = {ratio:.4f}")
    print(f"spread |A-B|/mean = {abs(ma - mb) / statistics.mean([ma, mb]) * 100:.2f} %")

    rng = random.Random(2801)
    boots = []
    for _ in range(4000):
        idx = [rng.randrange(len(rows)) for _ in rows]
        boots.append(statistics.median([tb[i] for i in idx]) / statistics.median([ta[i] for i in idx]))
    boots.sort()
    lo, hi = boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots))]
    print(f"paired bootstrap 95 % interval for B/A = [{lo:.4f}, {hi:.4f}]")

    with open(os.path.join(outdir, "ab_summary.txt"), "w") as fh:
        fh.write(f"rounds {rounds}\n")
        fh.write(f"A_time_median {ma}\nB_time_median {mb}\n")
        fh.write(f"A_nps_median {statistics.median(pa)}\nB_nps_median {statistics.median(pb)}\n")
        fh.write(f"ratio_B_over_A {ratio:.4f}\n")
        fh.write(f"boot95 [{lo:.4f}, {hi:.4f}]\n")
        fh.write("timesA " + repr(ta) + "\n" + "timesB " + repr(tb) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
