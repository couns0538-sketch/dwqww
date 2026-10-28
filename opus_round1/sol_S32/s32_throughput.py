"""S32 throughput table (advisory: shared PC, nice 19 / IDLE, CPUs 4-11, machine exclusive: no).

Alternating blocks A (datagen v2: forge datagen) and B (forge_selfplay.py, the PC's generator, 1 worker), the same
settings (5000 nodes/move, 8 random plies, max ply 300, win adjudication 2000 cp x 4 plies, |score| <= 3000) and
the same seed per block pair. Each block runs under run_pinned.py, which reports wall time and the CPU time of the
whole process tree (B: parent + worker + engine). Positions: A = records written; B = "eligible" (before its
persistent dedupe; the deduplicated count is reported too).

  python -I -B s32_throughput.py --datagen EXE --lock EXE --selfplay COPY.py --work DIR --pairs 3 --games 30 --out T.json
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOTAL = re.compile(r"TOTAL: games=([\d,]+) positions=([\d,]+) .* eligible=([\d,]+)")


def pinned(command: list[str], timing: Path, log: Path) -> dict:
    with open(log, "x", encoding="utf-8") as out:
        rc = subprocess.run([sys.executable, "-I", "-B", str(HERE / "run_pinned.py"), "--json", str(timing), "--", *command],
                            stdout=out, stderr=subprocess.STDOUT).returncode
    if rc != 0:
        raise SystemExit(f"block failed ({rc}): see {log}")
    return json.loads(timing.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datagen", required=True)
    ap.add_argument("--lock", required=True)
    ap.add_argument("--selfplay", required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--pairs", type=int, default=3)
    ap.add_argument("--games", type=int, default=30)
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    a.work.mkdir(parents=True, exist_ok=False)
    rows = []
    for pair in range(a.pairs):
        seed = a.seed + pair
        for kind in ("A_datagen", "B_selfplay"):
            tag = f"{pair}_{kind}"
            if kind == "A_datagen":
                cmd = [a.datagen, "datagen", "--out", str(a.work / tag / "g"), "--games", str(a.games), "--seed", str(seed)]
            else:
                cmd = [sys.executable, "-I", "-B", a.selfplay, "--engine", a.lock, "--workers", "1", "--cpus", "4-11",
                       "--nodes", "5000", "--out", str(a.work / tag), "--games-per-worker", str(a.games), "--seed", str(seed),
                       "--progress-seconds", "100000", "--engine-timeout", "180"]
            t = pinned(cmd, a.work / f"{tag}.time.json", a.work / f"{tag}.log")
            text = (a.work / f"{tag}.log").read_text(encoding="utf-8")
            if kind == "A_datagen":
                s = json.loads(next(line for line in text.splitlines() if line.startswith('{"mode"')))
                games, positions, dedup, plies = s["games"], s["positions"], None, s["searched_plies"]
            else:
                m = TOTAL.findall(text)[-1]
                games, dedup, positions = (int(x.replace(",", "")) for x in m)
                plies = None
            rows.append({"pair": pair, "kind": kind, "seed": seed, "games": games, "positions": positions,
                         "positions_dedup": dedup, "searched_plies": plies, "wall_s": t["wall_s"], "cpu_s": t["cpu_s"],
                         "pos_per_wall_s": positions / t["wall_s"], "pos_per_cpu_s": positions / t["cpu_s"]})
            print(json.dumps(rows[-1]), flush=True)
    summary = {}
    for metric in ("pos_per_wall_s", "pos_per_cpu_s"):
        ratios = [a_["%s" % metric] / b_[metric] for a_, b_ in zip(rows[0::2], rows[1::2])]
        summary[metric] = {"A_median": statistics.median(r[metric] for r in rows[0::2]),
                           "B_median": statistics.median(r[metric] for r in rows[1::2]),
                           "ratio_per_pair": ratios, "ratio_median": statistics.median(ratios)}
    report = {"tool": "s32_throughput", "machine_exclusive": "no", "priority": "IDLE, CPUs 4-11", "games_per_block": a.games,
              "rows": rows, "summary": summary}
    a.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
