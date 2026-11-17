#!/usr/bin/env python3
"""
Complete per-piece proof and ABBA timing runner for Job 2 (`prove_piece.py`):
1. Full Identity Check under PC20 + 768 test net AND 512 test net:
   - Logs engine `NNUE v3 active:` line + setup `eval` line.
   - `bench 11`, `bench 13`, and `bench 16` under PC20 + net768 and PC20 + net512.
   - 250-position depth-9 node count, score, and best move against `a_depth9_base_rows.txt`.
   - 1,000-position `eval` values on `positions_1000.txt` (both net768 and net512) against baseline row files.
   - Driver FNV-1a trace on 6 games from `startpos` AND 6 games from book FENs of `positions_250.txt`.
2. Timing Check (2 builds of A, 2 builds of B, strict ABBA order `A1 B1 B2 A2` for 8 rounds on the FEN-rooted
   self-play driver, plus 4 ABBA rounds on `bench 13`):
   - Reports paired ratio per round, rounds faster out of 8, median ratio with 95% bootstrap interval,
     A/A control (`A2 / A1` and `B2 / B1`), and engine CPU time (`utime + stime` from `/proc/<pid>/stat`)
     alongside wall time. Flags `"not measured"` automatically if the A/A spread is not well under half the effect.
"""

import argparse
import concurrent.futures
import pathlib
import random
import statistics
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import selfplay_driver_v2 as sp2

BENCH_PINS = {
    ("net512", 11): 625258,
    ("net512", 13): 3652372,
    ("net512", 16): 23891329,
    ("net768", 11): 882074,
    ("net768", 13): 4275906,
    ("net768", 16): 32374943,
}


def pc20_cfg(net_path: str) -> str:
    lines = ["uci\n"] + [f"setoption name {k} value {v}\n" for k, v in sp2.PC20_OPTIONS] + [
        f"setoption name NNUEArchFile value {net_path}\n",
        "setoption name NNUEArch value true\n",
        "position startpos\n",
        "eval\n",
        "isready\n",
    ]
    return "".join(lines)


def run_bench_pin(exe: str, net_path: str, depth: int) -> tuple[int, str, str]:
    cmd = pc20_cfg(net_path) + f"bench {depth}\nquit\n"
    res = subprocess.run([exe], input=cmd, text=True, capture_output=True, check=True)
    v3_line = ""
    ev_line = ""
    nodes = -1
    for ln in res.stdout.splitlines():
        s = ln.strip()
        if any(bad in s for bad in ("unknown option", "invalid value", "ERROR")):
            raise RuntimeError(f"Error line in bench {depth}: {s}")
        if "NNUE v3 active:" in s:
            v3_line = s
        elif s.startswith("info string eval ") and not ev_line:
            ev_line = s
        elif f"bench depth {depth} " in s:
            parts = s.split()
            nodes = int(parts[parts.index("nodes") + 1])
    if nodes < 0 or not v3_line or not ev_line:
        raise RuntimeError(f"Incomplete bench output for depth {depth}")
    return nodes, v3_line, ev_line


def check_250_depth9(exe: str, net768: str, pos250_path: pathlib.Path, expected_rows_path: pathlib.Path) -> int:
    fens = [ln.strip() for ln in pos250_path.read_text().splitlines() if ln.strip()]
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    try:
        sp2.send(proc, pc20_cfg(net768))
        sp2.wait_ready_collect(proc, True)
        rows = []
        for idx, fen in enumerate(fens):
            sp2.send(proc, "ucinewgame\nisready\n")
            sp2.wait_ready_collect(proc, False)
            sp2.send(proc, f"position fen {fen}\ngo depth 9\n")
            assert proc.stdout is not None
            last_nodes = 0
            last_score = ""
            last_hf = -1
            bm = "0000"
            while True:
                ln = proc.stdout.readline()
                if ln.startswith("info depth "):
                    parts = ln.split()
                    for i, tok in enumerate(parts):
                        if tok == "nodes" and i + 1 < len(parts):
                            last_nodes = int(parts[i + 1])
                        elif tok == "score" and i + 2 < len(parts):
                            last_score = f"{parts[i + 1]} {parts[i + 2]}"
                        elif tok == "hashfull" and i + 1 < len(parts):
                            last_hf = int(parts[i + 1])
                elif ln.startswith("bestmove "):
                    bm = ln.split()[1]
                    break
            rows.append(f"{idx}\t{bm}\t{last_nodes}\t{last_score}\thashfull={last_hf}\t{fen}")
        sp2.send(proc, "quit\n")
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()
    got = "\n".join(rows) + "\n"
    exp = expected_rows_path.read_text()
    if got != exp:
        raise AssertionError("250-position depth-9 rows mismatch!")
    return len(rows)


def check_1000_evals(exe: str, net_path: str, pos1000_path: pathlib.Path, expected_eval_path: pathlib.Path) -> int:
    fens = [ln.strip() for ln in pos1000_path.read_text().splitlines() if ln.strip()]
    cmd = (
        "".join([f"setoption name {k} value {v}\n" for k, v in sp2.PC20_OPTIONS])
        + f"setoption name NNUEArchFile value {net_path}\nsetoption name NNUEArch value true\nisready\n"
        + "".join([f"position fen {f}\neval\n" for f in fens])
        + "quit\n"
    )
    res = subprocess.run([exe], input=cmd, text=True, capture_output=True, check=True)
    eval_lines = [ln.strip() for ln in res.stdout.splitlines() if ln.startswith("info string eval ")]
    if len(eval_lines) != 1000:
        raise RuntimeError(f"Expected 1000 eval lines, got {len(eval_lines)}")
    got = "\n".join(f"{i}\t{eval_lines[i]}" for i in range(1000)) + "\n"
    if not expected_eval_path.exists():
        expected_eval_path.write_text(got)
    else:
        if got != expected_eval_path.read_text():
            raise AssertionError(f"1000-position eval mismatch against {expected_eval_path.name}!")
    return 1000


def time_bench13_cpu_wall(exe: str, net_path: str) -> dict:
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    try:
        sp2.send(proc, pc20_cfg(net_path))
        setup = sp2.wait_ready_collect(proc, True)
        v3_active = next((ln for ln in setup if "NNUE v3 active:" in ln), "")
        ev_line = next((ln for ln in setup if ln.startswith("info string eval ")), "")
        sp2.send(proc, "bench 7\nisready\n")
        sp2.wait_ready_collect(proc, False)

        cpu0 = sp2.read_proc_cpu_ms(proc.pid)
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
        cpu1 = sp2.read_proc_cpu_ms(proc.pid)
        sp2.send(proc, "quit\n")
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()
    wall_ms = (t1 - t0) / 1e6
    cpu_ms = max(0.001, cpu1 - cpu0)
    return {
        "nodes": nodes,
        "wall_ms": wall_ms,
        "cpu_ms": cpu_ms,
        "wall_nps": nodes / (wall_ms / 1000.0),
        "cpu_nps": nodes / (cpu_ms / 1000.0),
        "v3_active": v3_active,
        "setup_eval": ev_line,
    }


def bootstrap_ci(a1: list[float], a2: list[float], b1: list[float], b2: list[float], iters: int = 10000) -> tuple[float, float, float]:
    med_a = statistics.median(a1 + a2)
    med_b = statistics.median(b1 + b2)
    point = med_b / med_a
    rng = random.Random(20261117)
    vals = []
    for _ in range(iters):
        sa = [rng.choice(a1) for _ in a1] + [rng.choice(a2) for _ in a2]
        sb = [rng.choice(b1) for _ in b1] + [rng.choice(b2) for _ in b2]
        vals.append(statistics.median(sb) / statistics.median(sa))
    vals.sort()
    return point, vals[int(0.025 * iters)], vals[int(0.975 * iters)]


def summarize_abba(label: str, a1: list[float], a2: list[float], b1: list[float], b2: list[float], log) -> dict:
    rounds = len(a1)
    paired = [((b1[r] + b2[r]) * 0.5) / ((a1[r] + a2[r]) * 0.5) for r in range(rounds)]
    faster = sum(1 for x in paired if x > 1.0)
    med_ratio, ci_lo, ci_hi = bootstrap_ci(a1, a2, b1, b2)
    aa_a = statistics.median(a2) / statistics.median(a1)
    aa_b = statistics.median(b2) / statistics.median(b1)
    aa_spread = max(abs(aa_a - 1.0), abs(aa_b - 1.0))
    effect = abs(med_ratio - 1.0)
    verdict = "MEASURED" if (effect > 0 and aa_spread < 0.45 * effect) else "not measured"
    paired_str = ", ".join(f"{x:.4f}" for x in paired)
    log(f"  [{label}] medians: A1={statistics.median(a1):.2f}, A2={statistics.median(a2):.2f}, "
        f"B1={statistics.median(b1):.2f}, B2={statistics.median(b2):.2f}")
    log(f"  [{label}] paired ratio/round: [{paired_str}] | rounds faster: {faster}/{rounds}")
    log(f"  [{label}] median ratio (B/A): {med_ratio:.4f}x ({(med_ratio-1)*100:+.2f}%), "
        f"95% CI [{ci_lo:.4f}x, {ci_hi:.4f}x] | A/A: A2/A1={aa_a:.4f}, B2/B1={aa_b:.4f} (max spread {aa_spread*100:.2f}%) -> {verdict}")
    return {
        "paired": paired,
        "faster": faster,
        "rounds": rounds,
        "med_ratio": med_ratio,
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "aa_a": aa_a,
        "aa_b": aa_b,
        "verdict": verdict,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--piece", required=True)
    ap.add_argument("--a1", required=True)
    ap.add_argument("--a2", required=True)
    ap.add_argument("--b1", required=True)
    ap.add_argument("--b2", required=True)
    ap.add_argument("--net512", required=True)
    ap.add_argument("--net768", required=True)
    ap.add_argument("--carbon2-dir", required=True)
    ap.add_argument("--exp-startpos-hash", required=True)
    ap.add_argument("--exp-fen-hash", required=True)
    ap.add_argument("--rounds", type=int, default=8)
    ap.add_argument("--bench-rounds", type=int, default=4)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cdir = pathlib.Path(args.carbon2_dir)
    j2dir = cdir / "job2"
    pos250 = cdir / "positions_250.txt"
    pos1000 = cdir / "positions_1000.txt"
    exp_rows250 = cdir / "a_depth9_base_rows.txt"
    exp_eval768 = j2dir / "eval_1000_net768_rows.txt"
    exp_eval512 = j2dir / "eval_1000_net512_rows.txt"

    lines = []
    def log(msg: str):
        print(msg, flush=True)
        lines.append(msg)

    log(f"=== PIECE {args.piece}: PROOF 1 (IDENTITY UNDER PC20 + NET768 AND NET512) ===")
    # Run deterministic identity checks concurrently across 4 cores (no timing yet!)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        fut_b512_16 = pool.submit(run_bench_pin, args.b1, args.net512, 16)
        fut_b768_16 = pool.submit(run_bench_pin, args.b1, args.net768, 16)
        fut_250 = pool.submit(check_250_depth9, args.b1, args.net768, pos250, exp_rows250)
        fut_ev768 = pool.submit(check_1000_evals, args.b1, args.net768, pos1000, exp_eval768)
        fut_ev512 = pool.submit(check_1000_evals, args.b1, args.net512, pos1000, exp_eval512)
        fut_b512_11 = pool.submit(run_bench_pin, args.b1, args.net512, 11)
        fut_b512_13 = pool.submit(run_bench_pin, args.b1, args.net512, 13)
        fut_b768_11 = pool.submit(run_bench_pin, args.b1, args.net768, 11)
        fut_b768_13 = pool.submit(run_bench_pin, args.b1, args.net768, 13)
        fut_sp_start = pool.submit(sp2.run_selfplay_v2, args.b1, args.net768, "startpos", None, 6, 2000)
        fut_sp_fen = pool.submit(sp2.run_selfplay_v2, args.b1, args.net768, "fen", str(pos250), 6, 2000)

        for (tag, d), fut in [
            (("net512", 11), fut_b512_11),
            (("net512", 13), fut_b512_13),
            (("net512", 16), fut_b512_16),
            (("net768", 11), fut_b768_11),
            (("net768", 13), fut_b768_13),
            (("net768", 16), fut_b768_16),
        ]:
            nodes, v3_ln, ev_ln = fut.result()
            exp_n = BENCH_PINS[(tag, d)]
            assert nodes == exp_n, f"{tag} bench {d}: {nodes} != {exp_n}"
            log(f"  {tag} bench {d}: nodes={nodes} (== {exp_n} EXACT) | {v3_ln} | {ev_ln}")

        n250 = fut_250.result()
        n_ev768 = fut_ev768.result()
        n_ev512 = fut_ev512.result()
        sp_start = fut_sp_start.result()
        sp_fen = fut_sp_fen.result()
        assert sp_start["trace_fnv1a64"] == args.exp_startpos_hash, (
            f"startpos trace {sp_start['trace_fnv1a64']} != {args.exp_startpos_hash}"
        )
        assert sp_fen["trace_fnv1a64"] == args.exp_fen_hash, (
            f"fen trace {sp_fen['trace_fnv1a64']} != {args.exp_fen_hash}"
        )
        log(f"  250-pos depth 9 (net768): {n250}/250 EXACT MATCH")
        log(f"  1000-pos eval (net768 & net512): {n_ev768}/1000 & {n_ev512}/1000 EXACT MATCH")
        log(f"  6-game startpos FNV trace: {sp_start['trace_fnv1a64']} (EXACT, searches={sp_start['searches']}, nodes={sp_start['total_nodes']})")
        log(f"  6-game FEN-root FNV trace: {sp_fen['trace_fnv1a64']} (EXACT, searches={sp_fen['searches']}, nodes={sp_fen['total_nodes']})")

    # Strictly sequential idle-machine ABBA timing (`A1 B1 B2 A2`)
    log(f"\n=== PIECE {args.piece}: PROOF 2 (ABBA TIMING: A1 B1 B2 A2 x {args.rounds} ROUNDS, FEN-ROOT SELF-PLAY, NET768) ===")
    wall_s = {"A1": [], "A2": [], "B1": [], "B2": []}
    cpu_s = {"A1": [], "A2": [], "B1": [], "B2": []}
    cpu_ms_tot = {"A": 0.0, "B": 0.0}
    wall_ms_tot = {"A": 0.0, "B": 0.0}
    abba = [("A1", args.a1), ("B1", args.b1), ("B2", args.b2), ("A2", args.a2)]

    for r in range(args.rounds):
        for tag, exe in abba:
            res = sp2.run_selfplay_v2(exe, args.net768, "fen", str(pos250), 6, 2000)
            assert res["trace_fnv1a64"] == args.exp_fen_hash
            wall_s[tag].append(res["wall_searches_per_sec"])
            cpu_s[tag].append(res["cpu_searches_per_sec"])
            side = tag[0]
            cpu_ms_tot[side] += res["engine_cpu_ms"]
            wall_ms_tot[side] += res["wall_ms"]
            if r == 0:
                log(f"  setup_check {tag}: {res['v3_active']} | {res['setup_eval']}")
            log(
                f"  round {r+1:02d} {tag}: wall={res['wall_searches_per_sec']:7.2f} s/s ({res['wall_ms']:7.1f} ms) | "
                f"eng_cpu={res['cpu_searches_per_sec']:7.2f} s/s ({res['engine_cpu_ms']:7.1f} ms) | "
                f"searches={res['searches']} nodes={res['total_nodes']} hash={res['trace_fnv1a64']}"
            )

    summarize_abba("selfplay_wall_searches_per_s", wall_s["A1"], wall_s["A2"], wall_s["B1"], wall_s["B2"], log)
    summarize_abba("selfplay_eng_cpu_searches_per_s", cpu_s["A1"], cpu_s["A2"], cpu_s["B1"], cpu_s["B2"], log)
    log(
        f"  [selfplay_totals_across_{2*args.rounds}_runs] A: wall={wall_ms_tot['A']:.1f} ms, engine_cpu={cpu_ms_tot['A']:.1f} ms | "
        f"B: wall={wall_ms_tot['B']:.1f} ms, engine_cpu={cpu_ms_tot['B']:.1f} ms "
        f"(A/B engine_cpu ratio = {cpu_ms_tot['A']/cpu_ms_tot['B']:.4f}x)"
    )

    log(f"\n=== PIECE {args.piece}: COARSER CHECK (bench 13, A1 B1 B2 A2 x {args.bench_rounds} ROUNDS, NET768) ===")
    b13_wall = {"A1": [], "A2": [], "B1": [], "B2": []}
    b13_cpu = {"A1": [], "A2": [], "B1": [], "B2": []}
    for r in range(args.bench_rounds):
        for tag, exe in abba:
            res = time_bench13_cpu_wall(exe, args.net768)
            assert res["nodes"] == 4275906
            b13_wall[tag].append(res["wall_nps"])
            b13_cpu[tag].append(res["cpu_nps"])
            log(
                f"  b13 round {r+1:02d} {tag}: wall_nps={res['wall_nps']:10.1f} ({res['wall_ms']:7.1f} ms) | "
                f"cpu_nps={res['cpu_nps']:10.1f} ({res['cpu_ms']:7.1f} ms)"
            )
    summarize_abba("bench13_wall_nps", b13_wall["A1"], b13_wall["A2"], b13_wall["B1"], b13_wall["B2"], log)
    summarize_abba("bench13_eng_cpu_nps", b13_cpu["A1"], b13_cpu["A2"], b13_cpu["B1"], b13_cpu["B2"], log)

    pathlib.Path(args.out).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
