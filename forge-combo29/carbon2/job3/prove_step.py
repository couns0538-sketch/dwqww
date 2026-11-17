#!/usr/bin/env python3
"""
Job 3 proof and ABBA timing runner (`prove_step.py`):
- Verifies complete identity under PC20 + 768 net AND 512 net:
  * bench 11, 13, 16 (768: 882074 / 4275906 / 32374943; 512: 625258 / 3652372 / 23891329)
  * 250 depth-9 rows (`a_depth9_base_rows.txt`)
  * 1,000 eval rows on `positions_1000.txt` (768 and 512)
  * 6-game startpos FNV trace (`4560d7c3afdeba2e`) and 6-game FEN-root FNV trace (`9ed22c1193ab96de`)
  * Logs engine's `NNUE v3 active:` line in every run.
- Runs 8 ABBA rounds (`A1 B1 B2 A2`) on FEN-root self-play + 4 ABBA rounds on `bench 13`, recording
  both wall time and engine CPU time (`utime + stime` from `/proc/<pid>/stat`).
- Explicitly distinguishes and reports BOTH:
  1. `ratio_of_pooled_medians` (`median(B1+B2) / median(A1+A2)`) with 10,000-resample bootstrap 95% CI
  2. `median_of_paired_round_ratios` (`median_r(mean(B1_r,B2_r) / mean(A1_r,A2_r))`) with exact paired bootstrap 95% CI
"""

import argparse
import concurrent.futures
import pathlib
import random
import statistics
import sys

J2_DIR = pathlib.Path(__file__).resolve().parent.parent / "job2"
sys.path.insert(0, str(J2_DIR))
import prove_piece as pp
import selfplay_driver_v2 as sp2


def summarize_abba_named(label: str, a1: list[float], a2: list[float], b1: list[float], b2: list[float], log):
    rounds = len(a1)
    paired = [((b1[r] + b2[r]) * 0.5) / ((a1[r] + a2[r]) * 0.5) for r in range(rounds)]
    faster = sum(1 for x in paired if x > 1.0)
    pooled_ratio, pooled_lo, pooled_hi = pp.bootstrap_ci(a1, a2, b1, b2, iters=10000)

    med_paired = statistics.median(paired)
    rng = random.Random(20261117)
    paired_boots = []
    for _ in range(10000):
        sample = [rng.choice(paired) for _ in paired]
        paired_boots.append(statistics.median(sample))
    paired_boots.sort()
    paired_lo = paired_boots[250]
    paired_hi = paired_boots[9750]

    aa_a = statistics.median(a2) / statistics.median(a1)
    aa_b = statistics.median(b2) / statistics.median(b1)
    aa_spread = max(abs(aa_a - 1.0), abs(aa_b - 1.0))
    effect = abs(pooled_ratio - 1.0)
    verdict = "MEASURED" if (effect > 0 and aa_spread < 0.45 * effect) else "not measured"

    paired_str = ", ".join(f"{x:.4f}" for x in paired)
    log(
        f"  [{label}] build medians: A1={statistics.median(a1):.2f}, A2={statistics.median(a2):.2f} "
        f"(pooled A={statistics.median(a1+a2):.2f}) | B1={statistics.median(b1):.2f}, B2={statistics.median(b2):.2f} "
        f"(pooled B={statistics.median(b1+b2):.2f})"
    )
    log(f"  [{label}] paired ratio per round: [{paired_str}] | rounds faster: {faster}/{rounds}")
    log(
        f"  [{label}] ratio_of_pooled_medians (median(B)/median(A)): {pooled_ratio:.4f}x "
        f"({(pooled_ratio-1)*100:+.2f}%), 95% CI [{pooled_lo:.4f}x, {pooled_hi:.4f}x]"
    )
    log(
        f"  [{label}] median_of_paired_round_ratios (median(B_r/A_r)): {med_paired:.4f}x "
        f"({(med_paired-1)*100:+.2f}%), 95% CI [{paired_lo:.4f}x, {paired_hi:.4f}x]"
    )
    log(
        f"  [{label}] A/A control: A2/A1={aa_a:.4f}, B2/B1={aa_b:.4f} "
        f"(max A/A spread {aa_spread*100:.2f}%) -> {verdict}"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", required=True)
    ap.add_argument("--a1", required=True)
    ap.add_argument("--a2", required=True)
    ap.add_argument("--b1", required=True)
    ap.add_argument("--b2", required=True)
    ap.add_argument("--net512", required=True)
    ap.add_argument("--net768", required=True)
    ap.add_argument("--carbon2-dir", required=True)
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
    exp_start_hash = "4560d7c3afdeba2e"
    exp_fen_hash = "9ed22c1193ab96de"

    lines = []
    def log(msg: str):
        print(msg, flush=True)
        lines.append(msg)

    log(f"=== STEP {args.step}: PROOF 1 (IDENTITY UNDER PC20 + NET768 AND NET512) ===")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        f512_16 = pool.submit(pp.run_bench_pin, args.b1, args.net512, 16)
        f768_16 = pool.submit(pp.run_bench_pin, args.b1, args.net768, 16)
        f250 = pool.submit(pp.check_250_depth9, args.b1, args.net768, pos250, exp_rows250)
        fev768 = pool.submit(pp.check_1000_evals, args.b1, args.net768, pos1000, exp_eval768)
        fev512 = pool.submit(pp.check_1000_evals, args.b1, args.net512, pos1000, exp_eval512)
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
            log(f"  {tag} bench {d}: nodes={nodes} (== {exp_n} EXACT) | {v3_ln} | {ev_ln}")

        n250 = f250.result()
        n768 = fev768.result()
        n512 = fev512.result()
        sp_s = fsp_s.result()
        sp_f = fsp_f.result()
        assert sp_s["trace_fnv1a64"] == exp_start_hash
        assert sp_f["trace_fnv1a64"] == exp_fen_hash
        log(f"  250-pos depth 9 (net768): {n250}/250 EXACT MATCH")
        log(f"  1000-pos eval (net768 & net512): {n768}/1000 & {n512}/1000 EXACT MATCH")
        log(f"  6-game startpos FNV trace: {sp_s['trace_fnv1a64']} (EXACT, searches={sp_s['searches']}, nodes={sp_s['total_nodes']})")
        log(f"  6-game FEN-root FNV trace: {sp_f['trace_fnv1a64']} (EXACT, searches={sp_f['searches']}, nodes={sp_f['total_nodes']})")

    log(f"\n=== STEP {args.step}: PROOF 3 (ABBA TIMING: A1 B1 B2 A2 x {args.rounds} ROUNDS, FEN-ROOT SELF-PLAY, NET768) ===")
    wall_s = {"A1": [], "A2": [], "B1": [], "B2": []}
    cpu_s = {"A1": [], "A2": [], "B1": [], "B2": []}
    cpu_ms_tot = {"A": 0.0, "B": 0.0}
    wall_ms_tot = {"A": 0.0, "B": 0.0}
    abba = [("A1", args.a1), ("B1", args.b1), ("B2", args.b2), ("A2", args.a2)]

    for r in range(args.rounds):
        for tag, exe in abba:
            res = sp2.run_selfplay_v2(exe, args.net768, "fen", str(pos250), 6, 2000)
            assert res["trace_fnv1a64"] == exp_fen_hash
            wall_s[tag].append(res["wall_searches_per_sec"])
            cpu_s[tag].append(res["cpu_searches_per_sec"])
            cpu_ms_tot[tag[0]] += res["engine_cpu_ms"]
            wall_ms_tot[tag[0]] += res["wall_ms"]
            if r == 0:
                log(f"  setup_check {tag}: {res['v3_active']} | {res['setup_eval']}")
            log(
                f"  round {r+1:02d} {tag}: wall={res['wall_searches_per_sec']:7.2f} s/s ({res['wall_ms']:7.1f} ms) | "
                f"eng_cpu={res['cpu_searches_per_sec']:7.2f} s/s ({res['engine_cpu_ms']:7.1f} ms) | "
                f"searches={res['searches']} nodes={res['total_nodes']} hash={res['trace_fnv1a64']}"
            )

    summarize_abba_named("selfplay_wall_searches_per_s", wall_s["A1"], wall_s["A2"], wall_s["B1"], wall_s["B2"], log)
    summarize_abba_named("selfplay_eng_cpu_searches_per_s", cpu_s["A1"], cpu_s["A2"], cpu_s["B1"], cpu_s["B2"], log)
    log(
        f"  [selfplay_totals_across_{2*args.rounds}_runs] A: wall={wall_ms_tot['A']:.1f} ms, engine_cpu={cpu_ms_tot['A']:.1f} ms | "
        f"B: wall={wall_ms_tot['B']:.1f} ms, engine_cpu={cpu_ms_tot['B']:.1f} ms "
        f"(A/B total engine_cpu ratio = {cpu_ms_tot['A']/cpu_ms_tot['B']:.4f}x)"
    )

    log(f"\n=== STEP {args.step}: COARSER CHECK (bench 13, A1 B1 B2 A2 x {args.bench_rounds} ROUNDS, NET768) ===")
    b13_wall = {"A1": [], "A2": [], "B1": [], "B2": []}
    b13_cpu = {"A1": [], "A2": [], "B1": [], "B2": []}
    for r in range(args.bench_rounds):
        for tag, exe in abba:
            res = pp.time_bench13_cpu_wall(exe, args.net768)
            assert res["nodes"] == 4275906
            b13_wall[tag].append(res["wall_nps"])
            b13_cpu[tag].append(res["cpu_nps"])
            log(
                f"  b13 round {r+1:02d} {tag}: wall_nps={res['wall_nps']:10.1f} ({res['wall_ms']:7.1f} ms) | "
                f"cpu_nps={res['cpu_nps']:10.1f} ({res['cpu_ms']:7.1f} ms)"
            )
    summarize_abba_named("bench13_wall_nps", b13_wall["A1"], b13_wall["A2"], b13_wall["B1"], b13_wall["B2"], log)
    summarize_abba_named("bench13_eng_cpu_nps", b13_cpu["A1"], b13_cpu["A2"], b13_cpu["B1"], b13_cpu["B2"], log)

    pathlib.Path(args.out).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
