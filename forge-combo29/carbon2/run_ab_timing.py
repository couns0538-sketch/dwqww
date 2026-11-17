#!/usr/bin/env python3
"""
Alternating 2-build-base vs 2-build-variant timing harness for Forge under PC20 + net768:
1. Self-play workload via selfplay_driver.py (persistent engine, ucinewgame + position startpos moves ... + go softnodes 2000).
2. Fixed-depth bench 13 (PC20 + net768, timed post-readyok via perf_counter_ns + engine's reported ms/nps).
Computes per-build medians, pooled median speedup ratio, and deterministic 10,000-iteration
stratified bootstrap 95% confidence intervals for the ratio of medians.
"""

import argparse
import pathlib
import platform
import random
import statistics
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import selfplay_driver as spd


def cpu_model_string() -> str:
    try:
        for ln in pathlib.Path("/proc/cpuinfo").read_text().splitlines():
            if ln.startswith("model name"):
                return ln.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def time_bench13(engine_path: str, net_path: str) -> dict:
    proc = subprocess.Popen(
        [engine_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    try:
        cfg = ["uci\n"] + [f"setoption name {k} value {v}\n" for k, v in spd.PC20_OPTIONS] + [
            f"setoption name NNUEArchFile value {net_path}\n",
            "setoption name NNUEArch value true\n",
            "isready\n",
        ]
        spd.send(proc, "".join(cfg))
        spd.wait_ready(proc, check_errors=True)
        # Short warmup search before timing bench 13 so pages & caches start in steady state
        spd.send(proc, "bench 7\nisready\n")
        spd.wait_ready(proc, check_errors=False)

        t0 = time.perf_counter_ns()
        spd.send(proc, "bench 13\n")
        assert proc.stdout is not None
        nodes = 0
        eng_ms = 0
        while True:
            ln = proc.stdout.readline()
            if not ln:
                raise RuntimeError("EOF before bench 13 finished")
            if "bench depth 13 " in ln:
                parts = ln.split()
                nodes = int(parts[parts.index("nodes") + 1])
                eng_ms = int(parts[parts.index("time") + 1])
                break
        t1 = time.perf_counter_ns()
        spd.send(proc, "quit\n")
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()

    wall_ms = (t1 - t0) / 1e6
    nps = nodes / ((t1 - t0) / 1e9)
    return {"nodes": nodes, "wall_ms": wall_ms, "engine_ms": eng_ms, "nps": nps}


def bootstrap_median_ratio_ci(
    b1: list[float], b2: list[float], v1: list[float], v2: list[float], iters: int = 10000, seed: int = 20261117
) -> tuple[float, float, float]:
    base_all = b1 + b2
    var_all = v1 + v2
    point = statistics.median(var_all) / statistics.median(base_all)
    rng = random.Random(seed)
    ratios = []
    for _ in range(iters):
        sb = [rng.choice(b1) for _ in b1] + [rng.choice(b2) for _ in b2]
        sv = [rng.choice(v1) for _ in v1] + [rng.choice(v2) for _ in v2]
        ratios.append(statistics.median(sv) / statistics.median(sb))
    ratios.sort()
    lo = ratios[int(0.025 * iters)]
    hi = ratios[int(0.975 * iters)]
    return point, lo, hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base1", required=True)
    ap.add_argument("--base2", required=True)
    ap.add_argument("--var1", required=True)
    ap.add_argument("--var2", required=True)
    ap.add_argument("--net", required=True)
    ap.add_argument("--rounds", type=int, default=8)
    ap.add_argument("--selfplay-games", type=int, default=6)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    lines = []
    def log(msg: str):
        print(msg, flush=True)
        lines.append(msg)

    log(f"CPU: {cpu_model_string()} (AVX-512 enabled, -march=x86-64-v4, g++ 13.3.0 -O3 -ffp-contract=off -fno-fast-math)")
    log(f"Net: {pathlib.Path(args.net).name} (FORGENN3 hidden=768, king_buckets=8 mirrored, output_buckets=8)")
    log(f"Protocol: 2 base builds + 2 variant builds, {args.rounds} counterbalanced alternating rounds ({2 * args.rounds} runs/side)")

    # 1. Self-play alternating benchmark
    log(f"\n=== WORKLOAD 1: Self-Play Driver ({args.selfplay_games} games/run, position startpos moves ... + go softnodes 2000) ===")
    sp_rates = {"base1": [], "base2": [], "var1": [], "var2": []}
    sp_hashes = set()
    builds = [("base1", args.base1), ("var1", args.var1), ("base2", args.base2), ("var2", args.var2)]
    for r in range(args.rounds):
        order = builds if (r % 2 == 0) else [builds[1], builds[0], builds[3], builds[2]]
        for name, exe in order:
            res = spd.run_selfplay(exe, args.net, args.selfplay_games, 2000, 8, 300, 20261117, [])
            sp_rates[name].append(res["searches_per_sec"])
            sp_hashes.add(res["trace_fnv1a64"])
            log(
                f"  round {r+1:02d} {name:5s}: {res['searches_per_sec']:7.2f} searches/s | "
                f"{res['effective_nps']:10.1f} eff_nps | {res['elapsed_ms']:8.2f} ms | "
                f"searches={res['searches']} nodes={res['total_nodes']} hash={res['trace_fnv1a64']}"
            )
    assert len(sp_hashes) == 1, f"Trace hash mismatch across runs: {sp_hashes}"
    sp_ratio, sp_lo, sp_hi = bootstrap_median_ratio_ci(
        sp_rates["base1"], sp_rates["base2"], sp_rates["var1"], sp_rates["var2"]
    )
    log(
        f"Self-play medians (searches/s): base1={statistics.median(sp_rates['base1']):.2f}, "
        f"base2={statistics.median(sp_rates['base2']):.2f}, base_pooled={statistics.median(sp_rates['base1']+sp_rates['base2']):.2f} | "
        f"var1={statistics.median(sp_rates['var1']):.2f}, var2={statistics.median(sp_rates['var2']):.2f}, "
        f"var_pooled={statistics.median(sp_rates['var1']+sp_rates['var2']):.2f}"
    )
    log(
        f"Self-play speedup (median var / median base): {sp_ratio:.4f}x "
        f"({(sp_ratio - 1.0) * 100.0:+.2f}%), 95% CI [{sp_lo:.4f}x, {sp_hi:.4f}x] "
        f"([{(sp_lo - 1.0) * 100.0:+.2f}%, {(sp_hi - 1.0) * 100.0:+.2f}%])"
    )

    # 2. bench 13 alternating benchmark
    log("\n=== WORKLOAD 2: bench 13 (PC20 + net768, 4,275,906 nodes) ===")
    b13_nps = {"base1": [], "base2": [], "var1": [], "var2": []}
    for r in range(args.rounds):
        order = builds if (r % 2 == 0) else [builds[1], builds[0], builds[3], builds[2]]
        for name, exe in order:
            res = time_bench13(exe, args.net)
            assert res["nodes"] == 4275906, f"Unexpected bench 13 nodes: {res['nodes']}"
            b13_nps[name].append(res["nps"])
            log(
                f"  round {r+1:02d} {name:5s}: {res['nps']:10.1f} nps | "
                f"wall={res['wall_ms']:8.2f} ms (engine_ms={res['engine_ms']}) | nodes={res['nodes']}"
            )
    b13_ratio, b13_lo, b13_hi = bootstrap_median_ratio_ci(
        b13_nps["base1"], b13_nps["base2"], b13_nps["var1"], b13_nps["var2"]
    )
    log(
        f"bench 13 medians (nps): base1={statistics.median(b13_nps['base1']):.1f}, "
        f"base2={statistics.median(b13_nps['base2']):.1f}, base_pooled={statistics.median(b13_nps['base1']+b13_nps['base2']):.1f} | "
        f"var1={statistics.median(b13_nps['var1']):.1f}, var2={statistics.median(b13_nps['var2']):.1f}, "
        f"var_pooled={statistics.median(b13_nps['var1']+b13_nps['var2']):.1f}"
    )
    log(
        f"bench 13 speedup (median var / median base): {b13_ratio:.4f}x "
        f"({(b13_ratio - 1.0) * 100.0:+.2f}%), 95% CI [{b13_lo:.4f}x, {b13_hi:.4f}x] "
        f"([{(b13_lo - 1.0) * 100.0:+.2f}%, {(b13_hi - 1.0) * 100.0:+.2f}%])"
    )

    pathlib.Path(args.out).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
