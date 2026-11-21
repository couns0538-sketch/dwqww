#!/usr/bin/env python3
"""
Job 50 Step 0 (`run_step0.py`):
On `bundle12` (`/tmp/carbon2_job50/bld_bundle12/forge`) unless named:
- Pins with no option (`312866 / 862329 / 4865609`);
- `PC20` `bench 11 / 13` (`278024 / 587276`, both default-off and explicit falses + HdLower defaults);
- `K4`: `bench 13` with `HindsightDepth=true` and no other option == `840387` on BOTH `bundle9` AND `bundle12`;
- Under `PC20` at depth `12` on `O` (`200` pos) and `G` (`353` pos):
  (a) all off on `bundle12` vs Job 48 Step 0 all-off rows (`O = 8,315,168`, `G = 17,611,204`), position by position;
  (b) `K2`: `HindsightDepth=true` at defaults on `bundle9` AND on `bundle12` (plus explicit `1/1/100` on `O`): equal position by position;
  (c) `K3`: `HindsightDepth=false` with `HdLowerWithheld=8, HdLowerDepth=16, HdLowerLoss=400`: equal to (a) position by position;
  (d) Planted `HdLowerLos=167` search: runner MUST stop immediately on the engine's `unknown option` line (`0` searches run).
Every `.rows.txt` writes `<rows_file>.meta` beside it (`path`, `sha256`, `id name`, options sent, pre-`readyok` lines).
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import pathlib
import sys

sys.dont_write_bytecode = True

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from j50_lib import (  # noqa: E402
    ALL_NINE_IDEA_FALSE,
    ALL_TEN_FALSE,
    EXP_BENCH11_NOOPT,
    EXP_BENCH11_PC20,
    EXP_BENCH13_NOOPT,
    EXP_BENCH13_PC20,
    EXP_BUNDLE9_SHA,
    EXP_K4_HD_BENCH13,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_PERFT5_NOOPT,
    G_EPD_PATH,
    HD_LOWER_DEFAULTS,
    JOB48,
    JOB50,
    O_FENS_PATH,
    PC20_OPTIONS,
    WORK50,
    EngineReplyStopError,
    ensure_bundle9_exe,
    fmt_cmp,
    read_j39_rows,
    run_epd_depth12_strict,
    run_fresh_bench_strict,
    run_fresh_perft5_strict,
    sha256_file,
    utc_now,
)


def compare_rows_pos_by_pos(
    r_got: list[tuple[int, int, str, str]],
    r_exp: list[tuple[int, int, str, str]],
) -> tuple[int, int, int]:
    if len(r_got) != len(r_exp):
        raise RuntimeError(f"Row length mismatch: {len(r_got)} != {len(r_exp)}")
    nb_eq = sum(1 for a, b in zip(r_got, r_exp) if (a[0], a[1], a[2]) == (b[0], b[1], b[2]))
    full_eq = sum(1 for a, b in zip(r_got, r_exp) if a == b)
    return len(r_exp), nb_eq, full_eq


def main() -> None:
    JOB50.mkdir(parents=True, exist_ok=True)
    WORK50.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    all_ok = True

    def rec(ok: bool, msg: str) -> None:
        nonlocal all_ok
        if not ok:
            all_ok = False
        lines.append(msg)
        print(msg, flush=True)

    lines.append(f"=== JOB 50 STEP 0 VERIFICATION ({utc_now()}) ===")

    b9_exe, b9_sha, _ = ensure_bundle9_exe()
    b12_p = WORK50 / "bld_bundle12/forge"
    if not b12_p.exists():
        raise RuntimeError(f"Missing {b12_p}; run run_p12.py first!")
    b12_exe = str(b12_p)
    b12_sha = sha256_file(b12_p)

    rec(*fmt_cmp(f"bundle9 exe sha256({b9_exe})", b9_sha, EXP_BUNDLE9_SHA))
    lines.append(f"  bundle12 exe path: {b12_exe}")
    lines.append(f"  bundle12 exe sha256({b12_exe}): {b12_sha}")

    # (d) Planted misspelt option check FIRST (`HdLowerLos=167` must STOP immediately before any search)
    lines.append("--- (d) Planted Misspelt Option Check (HdLowerLos=167) ---")
    planted_rows_p = WORK50 / "planted_never_written.rows.txt"
    planted_meta_p = WORK50 / "planted_never_written.rows.txt.meta"
    if planted_rows_p.exists():
        planted_rows_p.unlink()
    planted_stopped = False
    planted_engine_line = ""
    planted_marker = ""
    try:
        run_epd_depth12_strict(
            b12_exe,
            O_FENS_PATH,
            PC20_OPTIONS,
            ALL_NINE_IDEA_FALSE + [("HindsightDepth", "true"), ("HdLowerLos", "167")],
            planted_rows_p,
            planted_meta_p,
        )
    except EngineReplyStopError as exc:
        planted_stopped = True
        planted_engine_line = exc.engine_line
        planted_marker = exc.marker

    rec(*fmt_cmp("Step 0 (d) planted HdLowerLos=167 stopped runner via EngineReplyStopError", planted_stopped, True))
    rec(*fmt_cmp("Step 0 (d) planted stop marker", planted_marker, "unknown option"))
    rec(*fmt_cmp("Step 0 (d) planted search rows file not written (0 searches run)", planted_rows_p.exists(), False))
    lines.append(f"  planted_engine_unknown_option_line_verbatim: {planted_engine_line}")
    print(f"  planted_engine_unknown_option_line_verbatim: {planted_engine_line}", flush=True)

    # Pins & K4
    lines.append("--- Pins (no option), PC20 bench 11/13, and K4 (bench 13 HindsightDepth=true) ---")
    b11_no = run_fresh_bench_strict(b12_exe, 11, [])
    b13_no = run_fresh_bench_strict(b12_exe, 13, [])
    pf5_no = run_fresh_perft5_strict(b12_exe)
    rec(*fmt_cmp("bundle12 no-option bench 11", b11_no, EXP_BENCH11_NOOPT))
    rec(*fmt_cmp("bundle12 no-option bench 13", b13_no, EXP_BENCH13_NOOPT))
    rec(*fmt_cmp("bundle12 no-option perft 5", pf5_no, EXP_PERFT5_NOOPT))

    b11_pc20_def = run_fresh_bench_strict(b12_exe, 11, PC20_OPTIONS)
    b13_pc20_def = run_fresh_bench_strict(b12_exe, 13, PC20_OPTIONS)
    b11_pc20_exp = run_fresh_bench_strict(b12_exe, 11, PC20_OPTIONS + ALL_TEN_FALSE + HD_LOWER_DEFAULTS)
    b13_pc20_exp = run_fresh_bench_strict(b12_exe, 13, PC20_OPTIONS + ALL_TEN_FALSE + HD_LOWER_DEFAULTS)
    rec(*fmt_cmp("bundle12 PC20 (default off) bench 11", b11_pc20_def, EXP_BENCH11_PC20))
    rec(*fmt_cmp("bundle12 PC20 (default off) bench 13", b13_pc20_def, EXP_BENCH13_PC20))
    rec(*fmt_cmp("bundle12 PC20 (explicit 10 false + HdLower defaults) bench 11", b11_pc20_exp, EXP_BENCH11_PC20))
    rec(*fmt_cmp("bundle12 PC20 (explicit 10 false + HdLower defaults) bench 13", b13_pc20_exp, EXP_BENCH13_PC20))

    k4_b9 = run_fresh_bench_strict(b9_exe, 13, [("HindsightDepth", "true")])
    k4_b12_def = run_fresh_bench_strict(b12_exe, 13, [("HindsightDepth", "true")])
    k4_b12_exp = run_fresh_bench_strict(b12_exe, 13, [("HindsightDepth", "true")] + HD_LOWER_DEFAULTS)
    rec(*fmt_cmp("Step 0 K4 bundle9 bench 13 (HindsightDepth=true, no other option)", k4_b9, EXP_K4_HD_BENCH13))
    rec(*fmt_cmp("Step 0 K4 bundle12 bench 13 (HindsightDepth=true, implicit defaults)", k4_b12_def, EXP_K4_HD_BENCH13))
    rec(*fmt_cmp("Step 0 K4 bundle12 bench 13 (HindsightDepth=true, explicit 1/1/100)", k4_b12_exp, EXP_K4_HD_BENCH13))

    # Depth-12 O and G sweeps for (a), (b), and (c) across 4 parallel pinned workers
    lines.append("--- Step 0 (a), (b) [K2], and (c) [K3] Depth-12 Sweeps on O (200) and G (353) ---")
    hd_true_opts = ALL_NINE_IDEA_FALSE + [("HindsightDepth", "true")]
    k3_max_opts = ALL_TEN_FALSE + [
        ("HdLowerWithheld", "8"),
        ("HdLowerDepth", "16"),
        ("HdLowerLoss", "400"),
    ]

    tasks = [
        # (key, exe, set_path, extra_opts, rows_filename)
        ("a_O", b12_exe, O_FENS_PATH, ALL_TEN_FALSE, "step0_a_bundle12_all_off_O_d12.rows.txt"),
        ("a_G", b12_exe, G_EPD_PATH, ALL_TEN_FALSE, "step0_a_bundle12_all_off_G_d12.rows.txt"),
        ("b9_O", b9_exe, O_FENS_PATH, hd_true_opts, "step0_b_bundle9_HD_defaults_O_d12.rows.txt"),
        ("b9_G", b9_exe, G_EPD_PATH, hd_true_opts, "step0_b_bundle9_HD_defaults_G_d12.rows.txt"),
        ("b12_O", b12_exe, O_FENS_PATH, hd_true_opts, "step0_b_bundle12_HD_defaults_O_d12.rows.txt"),
        ("b12_G", b12_exe, G_EPD_PATH, hd_true_opts, "step0_b_bundle12_HD_defaults_G_d12.rows.txt"),
        (
            "b12_exp_O",
            b12_exe,
            O_FENS_PATH,
            hd_true_opts + HD_LOWER_DEFAULTS,
            "step0_b_bundle12_HD_explicit_defaults_O_d12.rows.txt",
        ),
        ("c_O", b12_exe, O_FENS_PATH, k3_max_opts, "step0_c_bundle12_HD_false_max_O_d12.rows.txt"),
        ("c_G", b12_exe, G_EPD_PATH, k3_max_opts, "step0_c_bundle12_HD_false_max_G_d12.rows.txt"),
    ]

    results_map: dict[str, list[tuple[int, int, str, str]]] = {}

    def _worker(idx_task: tuple[int, tuple[str, str, pathlib.Path, list[tuple[str, str]], str]]) -> tuple[str, list[tuple[int, int, str, str]]]:
        idx, (t_key, t_exe, t_set, t_extra, t_fn) = idx_task
        rp = JOB50 / t_fn
        mp = JOB50 / f"{t_fn}.meta"
        rows = run_epd_depth12_strict(
            t_exe,
            t_set,
            PC20_OPTIONS,
            t_extra,
            rp,
            mp,
            depth=12,
            cpu_pin=idx % 4,
        )
        return t_key, rows

    with ThreadPoolExecutor(max_workers=4) as ex:
        for tk, trows in ex.map(_worker, enumerate(tasks)):
            results_map[tk] = trows

    j48_o_ref = read_j39_rows(JOB48 / "step0_bundle9_PC20_all_off_O_d12.rows.txt")
    j48_g_ref = read_j39_rows(JOB48 / "step0_bundle9_PC20_all_off_G_d12.rows.txt")

    # Verify (a) against Job 48 Step 0 all-off rows
    sum_a_o = sum(r[1] for r in results_map["a_O"])
    sum_a_g = sum(r[1] for r in results_map["a_G"])
    n_o, nb_a_o, full_a_o = compare_rows_pos_by_pos(results_map["a_O"], j48_o_ref)
    n_g, nb_a_g, full_a_g = compare_rows_pos_by_pos(results_map["a_G"], j48_g_ref)
    rec(*fmt_cmp("Step 0 (a) bundle12 all_off O d12 sum vs known 8315168", sum_a_o, EXP_OFF_O_SUM))
    rec(*fmt_cmp("Step 0 (a) bundle12 all_off O d12 nodes+bestmove equal vs job48 Step 0", nb_a_o, n_o))
    rec(*fmt_cmp("Step 0 (a) bundle12 all_off O d12 full-row equal vs job48 Step 0", full_a_o, n_o))
    rec(*fmt_cmp("Step 0 (a) bundle12 all_off G d12 sum vs known 17611204", sum_a_g, EXP_OFF_G_SUM))
    rec(*fmt_cmp("Step 0 (a) bundle12 all_off G d12 nodes+bestmove equal vs job48 Step 0", nb_a_g, n_g))
    rec(*fmt_cmp("Step 0 (a) bundle12 all_off G d12 full-row equal vs job48 Step 0", full_a_g, n_g))

    # Verify (b) K2: bundle12 HD=true at defaults == bundle9 HD=true on O and G
    sum_b9_o = sum(r[1] for r in results_map["b9_O"])
    sum_b12_o = sum(r[1] for r in results_map["b12_O"])
    sum_b12_exp_o = sum(r[1] for r in results_map["b12_exp_O"])
    sum_b9_g = sum(r[1] for r in results_map["b9_G"])
    sum_b12_g = sum(r[1] for r in results_map["b12_G"])
    _, nb_b_o, full_b_o = compare_rows_pos_by_pos(results_map["b12_O"], results_map["b9_O"])
    _, nb_b_exp_o, full_b_exp_o = compare_rows_pos_by_pos(results_map["b12_exp_O"], results_map["b12_O"])
    _, nb_b_g, full_b_g = compare_rows_pos_by_pos(results_map["b12_G"], results_map["b9_G"])
    rec(*fmt_cmp("Step 0 (b) K2 HD=true defaults O d12 sum (bundle12 vs bundle9)", sum_b12_o, sum_b9_o))
    rec(*fmt_cmp("Step 0 (b) K2 HD=true defaults O d12 nodes+bestmove equal (bundle12 vs bundle9)", nb_b_o, n_o))
    rec(*fmt_cmp("Step 0 (b) K2 HD=true defaults O d12 full-row equal (bundle12 vs bundle9)", full_b_o, n_o))
    rec(*fmt_cmp("Step 0 (b) K2 HD=true explicit 1/1/100 O d12 sum vs implicit defaults", sum_b12_exp_o, sum_b12_o))
    rec(*fmt_cmp("Step 0 (b) K2 HD=true explicit 1/1/100 O d12 full-row equal vs implicit", full_b_exp_o, n_o))
    rec(*fmt_cmp("Step 0 (b) K2 HD=true defaults G d12 sum (bundle12 vs bundle9)", sum_b12_g, sum_b9_g))
    rec(*fmt_cmp("Step 0 (b) K2 HD=true defaults G d12 nodes+bestmove equal (bundle12 vs bundle9)", nb_b_g, n_g))
    rec(*fmt_cmp("Step 0 (b) K2 HD=true defaults G d12 full-row equal (bundle12 vs bundle9)", full_b_g, n_g))

    # Verify (c) K3: HindsightDepth=false with 8/16/400 == (a) position by position on O and G
    sum_c_o = sum(r[1] for r in results_map["c_O"])
    sum_c_g = sum(r[1] for r in results_map["c_G"])
    _, nb_c_o, full_c_o = compare_rows_pos_by_pos(results_map["c_O"], results_map["a_O"])
    _, nb_c_g, full_c_g = compare_rows_pos_by_pos(results_map["c_G"], results_map["a_G"])
    rec(*fmt_cmp("Step 0 (c) K3 HD=false (8/16/400) O d12 sum vs (a)", sum_c_o, sum_a_o))
    rec(*fmt_cmp("Step 0 (c) K3 HD=false (8/16/400) O d12 nodes+bestmove equal vs (a)", nb_c_o, n_o))
    rec(*fmt_cmp("Step 0 (c) K3 HD=false (8/16/400) O d12 full-row equal vs (a)", full_c_o, n_o))
    rec(*fmt_cmp("Step 0 (c) K3 HD=false (8/16/400) G d12 sum vs (a)", sum_c_g, sum_a_g))
    rec(*fmt_cmp("Step 0 (c) K3 HD=false (8/16/400) G d12 nodes+bestmove equal vs (a)", nb_c_g, n_g))
    rec(*fmt_cmp("Step 0 (c) K3 HD=false (8/16/400) G d12 full-row equal vs (a)", full_c_g, n_g))

    rec(*fmt_cmp("STEP 0 OVERALL", 1 if all_ok else 0, 1))
    (JOB50 / "step0_raw.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not all_ok:
        raise RuntimeError("Step 0 failed — stopping Job 50!")


if __name__ == "__main__":
    main()
