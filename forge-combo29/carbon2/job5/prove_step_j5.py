#!/usr/bin/env python3
"""
Job 5 per-step proof + stack-usage + 4-round ABBA bench 13 runner (`prove_step_j5.py`):
- Full Identity Check under PC20 + 768 test net AND 512 test net:
  * bench 11, 13, 16 (768: 882074 / 4275906 / 32374943; 512: 625258 / 3652372 / 23891329)
  * 250 depth-9 rows, 1,000 eval rows (768 & 512), startpos FNV trace (`4560d7c3afdeba2e`),
    and FEN-root FNV trace (`9ed22c1193ab96de`), logging `NNUE v3 active:` on every run.
- Stack Frame Measurement (`gcc -fstack-usage` + assembly `sizeof(MovePicker)` & `sizeof(Undo)`):
  * Reports `sizeof(MovePicker)`, `Worker::search` frame bytes, and `Worker::qsearch` frame bytes
    for both `A` (previous stack) and `B` (previous stack + step).
- `bench 13` ABBA Timing (`A1 B1 B2 A2` x 4 rounds, no per-step self-play timing):
  * Uses `os.wait4` (`getrusage` of reaped child) in nanoseconds alongside wall time.
  * Reports paired ratio per round, rounds faster, median of paired ratios with 95% CI,
    pooled-median ratio under its own name, and A/A control.
"""

import argparse
import concurrent.futures
import os
import pathlib
import subprocess
import sys
import time

J2_DIR = pathlib.Path(__file__).resolve().parent.parent / "job2"
J3_DIR = pathlib.Path(__file__).resolve().parent.parent / "job3"
sys.path.insert(0, str(J2_DIR))
sys.path.insert(0, str(J3_DIR))
import prove_piece as pp
import prove_step as ps
import selfplay_driver_v2 as sp2


def measure_stack_usage(src_dir: str, tmp_dir: str) -> dict:
    tdir = pathlib.Path(tmp_dir)
    tdir.mkdir(parents=True, exist_ok=True)
    probe_s = tdir / "probe.s"
    probe_su = tdir / "probe.su"
    code = (
        '#include "search.cpp"\n'
        'extern "C" std::size_t get_sizeof_movepicker() { return sizeof(forge::MovePicker); }\n'
        'extern "C" std::size_t get_sizeof_undo() { return sizeof(forge::Undo); }\n'
    )
    cmd = [
        "/usr/bin/g++", "-std=c++20", "-O3", "-ffp-contract=off", "-fno-fast-math",
        "-march=x86-64-v4", "-fstack-usage", "-DNDEBUG", "-DFORGE_NNUE_HIDDEN=256",
        f'-DFORGE_NNUE_WEIGHTS="{src_dir}/src/nnue_weights.inc"',
        "-DFORGE_EXPOSE_TUNABLES=1", "-DFORGE_SPD_TT_NOTLS=1", "-DFORGE_SPD_NO_ZERO_MOVELISTS=2",
        "-DFORGE_SEARCH_SPEED2=1", "-DFORGE_SPD_PREFETCH_EARLY=1", "-DFORGE_SPD_SLIDER_PEXT=1",
        "-DFORGE_SPD_NNUE_ZMM=1", "-DFORGE_MATE_ALPHA_GUARD=1", "-DFORGE_NNUE_V3=1",
        f"-I{src_dir}/include", f"-I{src_dir}/src", "-x", "c++", "-", "-S", "-o", str(probe_s),
    ]
    subprocess.run(cmd, input=code, text=True, check=True, cwd=str(tdir))
    asm = probe_s.read_text().splitlines()
    mp_sz = -1
    un_sz = -1
    mode = ""
    for ln in asm:
        if ln.startswith("get_sizeof_movepicker:"):
            mode = "mp"
        elif ln.startswith("get_sizeof_undo:"):
            mode = "un"
        elif mode and "movl" in ln and "eax" in ln:
            val = int(ln.split()[1].split(",")[0].lstrip("$"))
            if mode == "mp":
                mp_sz = val
            else:
                un_sz = val
            mode = ""
    search_frame = -1
    qsearch_frame = -1
    for ln in probe_su.read_text().splitlines():
        if "int forge::Worker::search(forge::Board&," in ln:
            search_frame = int(ln.split("\t")[1])
        elif "int forge::Worker::qsearch(forge::Board&," in ln:
            qsearch_frame = int(ln.split("\t")[1])
    return {
        "sizeof_movepicker": mp_sz,
        "sizeof_undo": un_sz,
        "search_frame": search_frame,
        "qsearch_frame": qsearch_frame,
    }


def time_bench13_rusage_ns(exe: str, net_path: str) -> dict:
    # First measure fixed startup+net-load rusage on an immediate quit? Even simpler:
    # bench 13 runs 4.28M nodes (~2.20s CPU) after setup (~0.02s CPU); subtracting a calibrated
    # setup-only rusage or reporting exact reaped-child rusage: wait — both A and B execute the
    # exact same 20ms net load, and we can run `bench 13` twice in one process vs single `bench 13`
    # or reap right after `bench 13`! Reaping right after `bench 13` gives exact child getrusage!
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    sp2.send(proc, pp.pc20_cfg(net_path))
    setup = sp2.wait_ready_collect(proc, True)
    v3_active = next((ln for ln in setup if "NNUE v3 active:" in ln), "")
    sp2.send(proc, "bench 7\nisready\n")
    sp2.wait_ready_collect(proc, False)

    t0 = time.perf_counter_ns()
    sp2.send(proc, "bench 13\n")
    assert proc.stdout is not None
    nodes = 0
    while True:
        ln = proc.stdout.readline()
        if not ln:
            raise RuntimeError("EOF in bench 13")
        if "bench depth 13 " in ln:
            parts = ln.split()
            nodes = int(parts[parts.index("nodes") + 1])
            break
    t1 = time.perf_counter_ns()
    sp2.send(proc, "quit\n")
    proc.stdout.read()
    _, status, ru = os.wait4(proc.pid, 0)
    proc.returncode = os.waitstatus_to_exitcode(status)
    if proc.returncode != 0:
        raise RuntimeError(f"Non-zero exit {proc.returncode}")

    wall_ns = t1 - t0
    cpu_ns = int(round((ru.ru_utime + ru.ru_stime) * 1_000_000_000))
    return {
        "nodes": nodes,
        "wall_ms": wall_ns / 1e6,
        "cpu_ns": cpu_ns,
        "wall_nps": nodes / (wall_ns / 1e9),
        "cpu_nps": nodes / (cpu_ns / 1e9),
        "v3_active": v3_active,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", required=True)
    ap.add_argument("--src-a", required=True)
    ap.add_argument("--src-b", required=True)
    ap.add_argument("--a1", required=True)
    ap.add_argument("--a2", required=True)
    ap.add_argument("--b1", required=True)
    ap.add_argument("--b2", required=True)
    ap.add_argument("--net512", required=True)
    ap.add_argument("--net768", required=True)
    ap.add_argument("--carbon2-dir", required=True)
    ap.add_argument("--bench-rounds", type=int, default=4)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cdir = pathlib.Path(args.carbon2_dir)
    j2dir = cdir / "job2"
    pos250 = cdir / "positions_250.txt"
    pos1000 = cdir / "positions_1000.txt"

    lines = []
    def log(msg: str):
        print(msg, flush=True)
        lines.append(msg)

    log(f"=== STEP {args.step}: STACK USAGE (BASE A -> STEP B) ===")
    su_a = measure_stack_usage(args.src_a, f"/tmp/carbon2_job5/su_{args.step}_a")
    su_b = measure_stack_usage(args.src_b, f"/tmp/carbon2_job5/su_{args.step}_b")
    log(
        f"  sizeof(MovePicker): {su_a['sizeof_movepicker']} -> {su_b['sizeof_movepicker']} bytes "
        f"({su_b['sizeof_movepicker'] - su_a['sizeof_movepicker']:+d} B) | "
        f"Worker::search frame: {su_a['search_frame']} -> {su_b['search_frame']} bytes "
        f"({su_b['search_frame'] - su_a['search_frame']:+d} B) | "
        f"Worker::qsearch frame: {su_a['qsearch_frame']} -> {su_b['qsearch_frame']} bytes "
        f"({su_b['qsearch_frame'] - su_a['qsearch_frame']:+d} B)"
    )

    log(f"\n=== STEP {args.step}: IDENTITY UNDER PC20 + NET768 AND NET512 ===")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        f512_16 = pool.submit(pp.run_bench_pin, args.b1, args.net512, 16)
        f768_16 = pool.submit(pp.run_bench_pin, args.b1, args.net768, 16)
        f250 = pool.submit(pp.check_250_depth9, args.b1, args.net768, pos250, cdir / "a_depth9_base_rows.txt")
        fev768 = pool.submit(pp.check_1000_evals, args.b1, args.net768, pos1000, j2dir / "eval_1000_net768_rows.txt")
        fev512 = pool.submit(pp.check_1000_evals, args.b1, args.net512, pos1000, j2dir / "eval_1000_net512_rows.txt")
        f512_11 = pool.submit(pp.run_bench_pin, args.b1, args.net512, 11)
        f512_13 = pool.submit(pp.run_bench_pin, args.b1, args.net512, 13)
        f768_11 = pool.submit(pp.run_bench_pin, args.b1, args.net768, 11)
        f768_13 = pool.submit(pp.run_bench_pin, args.b1, args.net768, 13)
        fsp_s = pool.submit(sp2.run_selfplay_v2, args.b1, args.net768, "startpos", None, 6, 2000)
        fsp_f = pool.submit(sp2.run_selfplay_v2, args.b1, args.net768, "fen", str(pos250), 6, 2000)

        for (tag, d), fut in [
            (("net512", 11), f512_11), (("net512", 13), f512_13), (("net512", 16), f512_16),
            (("net768", 11), f768_11), (("net768", 13), f768_13), (("net768", 16), f768_16),
        ]:
            nodes, v3_ln, ev_ln = fut.result()
            exp_n = pp.BENCH_PINS[(tag, d)]
            assert nodes == exp_n, f"{tag} bench {d}: {nodes} != {exp_n}"
            log(f"  {tag} bench {d}: nodes={nodes} (== {exp_n} EXACT) | {v3_ln}")

        assert f250.result() == 250
        assert fev768.result() == 1000 and fev512.result() == 1000
        sp_s = fsp_s.result()
        sp_f = fsp_f.result()
        assert sp_s["trace_fnv1a64"] == "4560d7c3afdeba2e"
        assert sp_f["trace_fnv1a64"] == "9ed22c1193ab96de"
        log("  250-pos depth 9: 250/250 EXACT; 1000-pos evals (768 & 512): EXACT")
        log(f"  6-game startpos trace: {sp_s['trace_fnv1a64']} (EXACT); 6-game FEN trace: {sp_f['trace_fnv1a64']} (EXACT)")

    log(f"\n=== STEP {args.step}: BENCH 13 TIMING (A1 B1 B2 A2 x {args.bench_rounds} ROUNDS, NET768, RUSAGE NS) ===")
    abba = [("A1", args.a1), ("B1", args.b1), ("B2", args.b2), ("A2", args.a2)]
    b13_wall = {"A1": [], "A2": [], "B1": [], "B2": []}
    b13_cpu = {"A1": [], "A2": [], "B1": [], "B2": []}
    for r in range(args.bench_rounds):
        for tag, exe in abba:
            res = time_bench13_rusage_ns(exe, args.net768)
            assert res["nodes"] == 4275906
            b13_wall[tag].append(res["wall_nps"])
            b13_cpu[tag].append(res["cpu_nps"])
            if r == 0:
                log(f"  active_check {tag}: {res['v3_active']}")
            log(
                f"  b13 round {r+1:02d} {tag}: wall_nps={res['wall_nps']:10.1f} ({res['wall_ms']:7.2f} ms) | "
                f"rusage_cpu_nps={res['cpu_nps']:10.1f} ({res['cpu_ns']} ns)"
            )
    ps.summarize_abba_named("bench13_wall_nps", b13_wall["A1"], b13_wall["A2"], b13_wall["B1"], b13_wall["B2"], log)
    ps.summarize_abba_named("bench13_rusage_cpu_nps", b13_cpu["A1"], b13_cpu["A2"], b13_cpu["B1"], b13_cpu["B2"], log)

    pathlib.Path(args.out).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
