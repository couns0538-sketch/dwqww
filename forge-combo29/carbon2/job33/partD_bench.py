#!/usr/bin/env python3
"""
Job 33 Part D — For the Record:
1) Attempts 1..60 of Set A, Ref and Loop in turn (odd ABBA, even BAAB, 6 blocks, 1 engine on 1 pinned CPU).
2) Same with nproc - 1 = 3 pairs at once (odd ABBA, even BAAB, 2 blocks, engines pinned to CPUs 1, 2, 3).
Each leg runs in a fresh Python child process so Python driver CPU (ru_utime + ru_stime of that Python process)
and engine CPU (reaped via wait4 inside the driver) are isolated per leg.
"""
from __future__ import annotations

import concurrent.futures
import datetime
import json
import os
import pathlib
import statistics
import subprocess
import sys
import time

REF_EXE = "/tmp/carbon2_job11/bld_sp_r15d_1/forge"
LOOP_EXE = "/tmp/carbon2_job33/bld_sp_sgr15d/forge"
JOB33 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job33")
ATTEMPTS = 60
SEED = "carbon2-job33-a"

CHILD_CODE = r"""
import json, resource, sys
sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/carbon2/job33")
from ref_driver import RunSettings, run_ref
from loop_driver import run_loop

mode = sys.argv[1]
exe = sys.argv[2]
eng_cpu = int(sys.argv[3])
settings = RunSettings()
if mode == "Ref":
    res = run_ref(exe, "carbon2-job33-a", 60, settings, cpu_pin=eng_cpu)
else:
    res = run_loop(exe, "carbon2-job33-a", 60, settings, cpu_pin=eng_cpu)

# Capture full Python process user+sys CPU up to exit (including import/runtime overhead or post-init run_ref/run_loop)
ru = resource.getrusage(resource.RUSAGE_SELF)
print(json.dumps({
    "mode": mode,
    "finished": res.finished,
    "records": res.records,
    "searches": res.searches,
    "nodes": res.final_nodes,
    "full_sha256": res.full_sha256,
    "wall_s": res.wall_s,
    "driver_run_cpu_s": res.driver_cpu_s,
    "driver_proc_cpu_s": float(ru.ru_utime + ru.ru_stime),
    "engine_cpu_s": res.engine_cpu_s,
}))
"""


def run_one_leg(mode: str, drv_cpu: int, eng_cpu: int) -> dict:
    exe = REF_EXE if mode == "Ref" else LOOP_EXE
    cmd = ["taskset", "-c", str(drv_cpu), sys.executable, "-c", CHILD_CODE, mode, exe, str(eng_cpu)]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    t0 = time.perf_counter()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    _, status, rusage_child = os.wait4(proc.pid, 0)
    t1 = time.perf_counter()
    out = proc.stdout.read() if proc.stdout else ""
    err = proc.stderr.read() if proc.stderr else ""
    if proc.stdout:
        proc.stdout.close()
    if proc.stderr:
        proc.stderr.close()
    if status != 0 or err:
        raise RuntimeError(f"Child failed status={status} err={err!r}")
    data = json.loads(out.strip().splitlines()[-1])
    # rusage_child includes ONLY the Python child process itself (not grandchildren reaped by wait4 inside it?
    # Note: in Linux, RUSAGE_CHILDREN / wait4 on a child includes the child's own waited-for children too!
    # Therefore data['driver_run_cpu_s'] (RUSAGE_SELF inside the Python process around the 60-game run) and
    # data['driver_proc_cpu_s'] (RUSAGE_SELF of the Python process) are the exact Python-only CPU!)
    data["outer_wall_s"] = t1 - t0
    return data


def run_concurrent_leg(mode: str, n_pairs: int) -> dict:
    # Engines pinned to CPUs 1..n_pairs; Python drivers pinned to CPU 0
    t0 = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_pairs) as pool:
        futs = [pool.submit(run_one_leg, mode, 0, pair_i + 1) for pair_i in range(n_pairs)]
        pair_results = [f.result() for f in futs]
    t1 = time.perf_counter()
    ref_sha = pair_results[0]["full_sha256"]
    for pr in pair_results:
        assert pr["full_sha256"] == ref_sha
    return {
        "mode": mode,
        "n_pairs": n_pairs,
        "batch_wall_s": t1 - t0,
        "mean_pair_wall_s": statistics.mean(p["wall_s"] for p in pair_results),
        "sum_driver_cpu_s": sum(p["driver_run_cpu_s"] for p in pair_results),
        "sum_driver_proc_cpu_s": sum(p["driver_proc_cpu_s"] for p in pair_results),
        "sum_engine_cpu_s": sum(p["engine_cpu_s"] for p in pair_results),
        "full_sha256": ref_sha,
        "searches": pair_results[0]["searches"],
        "nodes": pair_results[0]["nodes"],
        "records": pair_results[0]["records"],
        "pairs": pair_results,
    }


def main() -> None:
    nproc = os.cpu_count() or 4
    n_conc = max(1, nproc - 1)
    lines: list[str] = [
        f"UTC_START: {datetime.datetime.now(datetime.timezone.utc).strftime('%a %b %d %I:%M:%S %p UTC %Y')}",
        "=== JOB 33 PART D — Paired ABBA Timing & CPU Share (Attempts 1..60 of Set A) ===",
        f"Ref exe:  {REF_EXE}",
        f"Loop exe: {LOOP_EXE}",
        f"Workload: seed={SEED}, attempts={ATTEMPTS} (built-in eval, N=2000, PC defaults)",
        f"nproc={nproc}, concurrent_pairs={n_conc}",
        "Pinning (1-pair): Python driver on CPU 0, engine on CPU 3.",
        f"Pinning ({n_conc}-pair): {n_conc} Python drivers on CPU 0, {n_conc} engines on CPUs 1..{n_conc}.",
        "",
        "--- SECTION 1: Single-Pair Pinned (6 Blocks, odd=Ref-Loop-Loop-Ref, even=Loop-Ref-Ref-Loop) ---",
    ]

    # Warmup 1 leg each (left out)
    w_ref = run_one_leg("Ref", 0, 3)
    w_loop = run_one_leg("Loop", 0, 3)
    assert w_ref["full_sha256"] == w_loop["full_sha256"]
    exp_sha = w_ref["full_sha256"]
    lines.append(
        f"Warmup (left out): sha256={exp_sha} records={w_ref['records']} searches={w_ref['searches']} nodes={w_ref['nodes']} | "
        f"Ref wall={w_ref['wall_s']:.4f}s Loop wall={w_loop['wall_s']:.4f}s"
    )

    ref_legs_1: list[dict] = []
    loop_legs_1: list[dict] = []
    block_ratios_loop_over_ref: list[float] = []
    block_ratios_ref_over_loop: list[float] = []

    for blk in range(1, 7):
        order = ["Ref", "Loop", "Loop", "Ref"] if (blk % 2 == 1) else ["Loop", "Ref", "Ref", "Loop"]
        blk_ref: list[dict] = []
        blk_loop: list[dict] = []
        for leg_i, mode in enumerate(order, start=1):
            d = run_one_leg(mode, 0, 3)
            assert d["full_sha256"] == exp_sha, f"SHA mismatch in block {blk} leg {leg_i}"
            if mode == "Ref":
                blk_ref.append(d)
                ref_legs_1.append(d)
            else:
                blk_loop.append(d)
                loop_legs_1.append(d)
            drv_share = d["driver_run_cpu_s"] / (d["driver_run_cpu_s"] + d["engine_cpu_s"])
            line = (
                f"  blk {blk:02d} leg {leg_i} ({mode:4s}): wall={d['wall_s']:.4f}s "
                f"({d['wall_s']*1000/ATTEMPTS:.2f} ms/g) | "
                f"drv_cpu={d['driver_run_cpu_s']:.4f}s ({d['driver_run_cpu_s']*1000/ATTEMPTS:.2f} ms/g, proc={d['driver_proc_cpu_s']:.4f}s) | "
                f"eng_cpu={d['engine_cpu_s']:.4f}s ({d['engine_cpu_s']*1000/ATTEMPTS:.2f} ms/g) | "
                f"drv_share={drv_share*100:.2f}%"
            )
            print(line, flush=True)
            lines.append(line)

        w_r = sum(x["wall_s"] for x in blk_ref)
        w_l = sum(x["wall_s"] for x in blk_loop)
        r_lr = w_l / w_r
        r_rl = w_r / w_l
        block_ratios_loop_over_ref.append(r_lr)
        block_ratios_ref_over_loop.append(r_rl)
        b_sum = (
            f"  --> blk {blk:02d} ({''.join(m[0] for m in order)}): "
            f"Ref_wall={w_r:.4f}s Loop_wall={w_l:.4f}s | "
            f"Loop/Ref={r_lr:.4f} | Ref/Loop={r_rl:.4f}"
        )
        print(b_sum, flush=True)
        lines.append(b_sum)

    n_games_1 = len(ref_legs_1) * ATTEMPTS
    sum_ref_wall = sum(x["wall_s"] for x in ref_legs_1)
    sum_loop_wall = sum(x["wall_s"] for x in loop_legs_1)
    sum_ref_drv = sum(x["driver_run_cpu_s"] for x in ref_legs_1)
    sum_loop_drv = sum(x["driver_run_cpu_s"] for x in loop_legs_1)
    sum_ref_drv_proc = sum(x["driver_proc_cpu_s"] for x in ref_legs_1)
    sum_loop_drv_proc = sum(x["driver_proc_cpu_s"] for x in loop_legs_1)
    sum_ref_eng = sum(x["engine_cpu_s"] for x in ref_legs_1)
    sum_loop_eng = sum(x["engine_cpu_s"] for x in loop_legs_1)

    ref_share_1 = sum_ref_drv / (sum_ref_drv + sum_ref_eng)
    loop_share_1 = sum_loop_drv / (sum_loop_drv + sum_loop_eng)
    ref_share_proc_1 = sum_ref_drv_proc / (sum_ref_drv_proc + sum_ref_eng)
    loop_share_proc_1 = sum_loop_drv_proc / (sum_loop_drv_proc + sum_loop_eng)

    lines.extend([
        "",
        f"1-Pair Pooled Summary across 6 blocks ({len(ref_legs_1)} legs = {n_games_1} games per mode):",
        f"  Ref  per game: wall={sum_ref_wall*1000/n_games_1:.3f} ms, driver_cpu={sum_ref_drv*1000/n_games_1:.3f} ms "
        f"(proc={sum_ref_drv_proc*1000/n_games_1:.3f} ms), engine_cpu={sum_ref_eng*1000/n_games_1:.3f} ms | "
        f"driver_share={ref_share_1:.5f} ({ref_share_1*100:.2f}%, proc={ref_share_proc_1*100:.2f}%)",
        f"  Loop per game: wall={sum_loop_wall*1000/n_games_1:.3f} ms, driver_cpu={sum_loop_drv*1000/n_games_1:.3f} ms "
        f"(proc={sum_loop_drv_proc*1000/n_games_1:.3f} ms), engine_cpu={sum_loop_eng*1000/n_games_1:.3f} ms | "
        f"driver_share={loop_share_1:.5f} ({loop_share_1*100:.2f}%, proc={loop_share_proc_1*100:.2f}%)",
        f"  Wall ratio Loop/Ref: pooled={sum_loop_wall/sum_ref_wall:.4f}, median={statistics.median(block_ratios_loop_over_ref):.4f}, "
        f"mean={statistics.mean(block_ratios_loop_over_ref):.4f}, blocks={[round(x, 4) for x in block_ratios_loop_over_ref]}",
        f"  Wall ratio Ref/Loop: pooled={sum_ref_wall/sum_loop_wall:.4f}, median={statistics.median(block_ratios_ref_over_loop):.4f}, "
        f"mean={statistics.mean(block_ratios_ref_over_loop):.4f}, blocks={[round(x, 4) for x in block_ratios_ref_over_loop]}",
        "",
        f"--- SECTION 2: Concurrent {n_conc} Pairs at Once (2 Blocks, odd=Ref-Loop-Loop-Ref, even=Loop-Ref-Ref-Loop) ---",
    ])

    # Warmup 1 concurrent batch each (left out)
    _ = run_concurrent_leg("Ref", n_conc)
    _ = run_concurrent_leg("Loop", n_conc)

    ref_legs_c: list[dict] = []
    loop_legs_c: list[dict] = []
    conc_ratios_lr: list[float] = []
    conc_ratios_rl: list[float] = []

    for blk in range(1, 3):
        order = ["Ref", "Loop", "Loop", "Ref"] if (blk % 2 == 1) else ["Loop", "Ref", "Ref", "Loop"]
        blk_ref_c: list[dict] = []
        blk_loop_c: list[dict] = []
        for leg_i, mode in enumerate(order, start=1):
            d = run_concurrent_leg(mode, n_conc)
            assert d["full_sha256"] == exp_sha
            if mode == "Ref":
                blk_ref_c.append(d)
                ref_legs_c.append(d)
            else:
                blk_loop_c.append(d)
                loop_legs_c.append(d)
            games_in_leg = n_conc * ATTEMPTS
            drv_share = d["sum_driver_cpu_s"] / (d["sum_driver_cpu_s"] + d["sum_engine_cpu_s"])
            line = (
                f"  conc blk {blk:02d} leg {leg_i} ({mode:4s}, {n_conc} pairs): "
                f"batch_wall={d['batch_wall_s']:.4f}s (eff {d['batch_wall_s']*1000/games_in_leg:.2f} ms/g; "
                f"pair_mean_wall={d['mean_pair_wall_s']*1000/ATTEMPTS:.2f} ms/g) | "
                f"drv_cpu={d['sum_driver_cpu_s']*1000/games_in_leg:.2f} ms/g | "
                f"eng_cpu={d['sum_engine_cpu_s']*1000/games_in_leg:.2f} ms/g | "
                f"drv_share={drv_share*100:.2f}%"
            )
            print(line, flush=True)
            lines.append(line)

        bw_r = sum(x["batch_wall_s"] for x in blk_ref_c)
        bw_l = sum(x["batch_wall_s"] for x in blk_loop_c)
        conc_ratios_lr.append(bw_l / bw_r)
        conc_ratios_rl.append(bw_r / bw_l)
        b_sum = (
            f"  --> conc blk {blk:02d} ({''.join(m[0] for m in order)}): "
            f"Ref_batch_wall={bw_r:.4f}s Loop_batch_wall={bw_l:.4f}s | "
            f"Loop/Ref={bw_l/bw_r:.4f} | Ref/Loop={bw_r/bw_l:.4f}"
        )
        print(b_sum, flush=True)
        lines.append(b_sum)

    n_games_c = len(ref_legs_c) * n_conc * ATTEMPTS
    sum_c_ref_bwall = sum(x["batch_wall_s"] for x in ref_legs_c)
    sum_c_loop_bwall = sum(x["batch_wall_s"] for x in loop_legs_c)
    sum_c_ref_pwall = sum(x["mean_pair_wall_s"] * n_conc for x in ref_legs_c)
    sum_c_loop_pwall = sum(x["mean_pair_wall_s"] * n_conc for x in loop_legs_c)
    sum_c_ref_drv = sum(x["sum_driver_cpu_s"] for x in ref_legs_c)
    sum_c_loop_drv = sum(x["sum_driver_cpu_s"] for x in loop_legs_c)
    sum_c_ref_drv_proc = sum(x["sum_driver_proc_cpu_s"] for x in ref_legs_c)
    sum_c_loop_drv_proc = sum(x["sum_driver_proc_cpu_s"] for x in loop_legs_c)
    sum_c_ref_eng = sum(x["sum_engine_cpu_s"] for x in ref_legs_c)
    sum_c_loop_eng = sum(x["sum_engine_cpu_s"] for x in loop_legs_c)

    ref_share_c = sum_c_ref_drv / (sum_c_ref_drv + sum_c_ref_eng)
    loop_share_c = sum_c_loop_drv / (sum_c_loop_drv + sum_c_loop_eng)

    lines.extend([
        "",
        f"{n_conc}-Pair Concurrent Pooled Summary across 2 blocks ({len(ref_legs_c)} legs * {n_conc} pairs = {n_games_c} games per mode):",
        f"  Ref  per game: eff_wall={sum_c_ref_bwall*1000/n_games_c:.3f} ms (pair_wall={sum_c_ref_pwall*1000/n_games_c:.3f} ms), "
        f"driver_cpu={sum_c_ref_drv*1000/n_games_c:.3f} ms (proc={sum_c_ref_drv_proc*1000/n_games_c:.3f} ms), "
        f"engine_cpu={sum_c_ref_eng*1000/n_games_c:.3f} ms | driver_share={ref_share_c:.5f} ({ref_share_c*100:.2f}%)",
        f"  Loop per game: eff_wall={sum_c_loop_bwall*1000/n_games_c:.3f} ms (pair_wall={sum_c_loop_pwall*1000/n_games_c:.3f} ms), "
        f"driver_cpu={sum_c_loop_drv*1000/n_games_c:.3f} ms (proc={sum_c_loop_drv_proc*1000/n_games_c:.3f} ms), "
        f"engine_cpu={sum_c_loop_eng*1000/n_games_c:.3f} ms | driver_share={loop_share_c:.5f} ({loop_share_c*100:.2f}%)",
        f"  Batch wall ratio Loop/Ref: pooled={sum_c_loop_bwall/sum_c_ref_bwall:.4f}, blocks={[round(x, 4) for x in conc_ratios_lr]} "
        f"(pair_wall Loop/Ref={sum_c_loop_pwall/sum_c_ref_pwall:.4f})",
        f"  Batch wall ratio Ref/Loop: pooled={sum_c_ref_bwall/sum_c_loop_bwall:.4f}, blocks={[round(x, 4) for x in conc_ratios_rl]} "
        f"(pair_wall Ref/Loop={sum_c_ref_pwall/sum_c_loop_pwall:.4f})",
        f"UTC_END: {datetime.datetime.now(datetime.timezone.utc).strftime('%a %b %d %I:%M:%S %p UTC %Y')}",
    ])

    out_txt = "\n".join(lines) + "\n"
    (JOB33 / "partD_timing_raw.txt").write_text(out_txt)
    print("\n=== PART D SUMMARY WRITTEN TO partD_timing_raw.txt ===", flush=True)


if __name__ == "__main__":
    main()
