#!/usr/bin/env python3
"""
Job 51 Step 0 (`run_step0.py`):
On `bundle13` (`/tmp/carbon2_job51/bld_bundle13/forge`):
1. Pins with no option (`312866 / 862329 / 4865609`); `PC20` bench 11 / 13 (`278024 / 587276`,
   both default-off and explicit falses + explicit `HistReworkQuiet=-1, HistReworkCorrection=-1`).
2. (e) Planted check: one search with misspelt `HistReworkQuite=0`; runner MUST stop immediately
   on `info string unknown option HistReworkQuite` (`0` searches run).
3. Under `PC20` with every Idea switch and `HindsightDepth` off (`ALL_TEN_FALSE`), depth 12,
   on `O` (`200` pos) and `G` (`353` pos) (4-core parallel single-threaded `Threads=1` sessions):
   (a) K2: defaults (`-1, -1`, both implicit and explicit) against Job 39 `OFF` rows
       (`OFF_O_d12.rows.txt`, sum `8,315,168`; `OFF_G_d12.rows.txt`, sum `17,611,204`),
       position by position (`200 == 200` and `353 == 353`).
   (b) `HistRework=0` (with defaults `-1, -1`) against Job 48 Part L `L2` rows
       (`partL_L2_all_off_O_d12.rows.txt`, sum `8,658,059`;
        `partL_L2_all_off_G_d12.rows.txt`, sum `17,155,595`), position by position.
   (c) K3's two identities, position by position against (a) and (b):
       - `K3_id1`: `HistRework=0` + `HistReworkQuiet=2` + `HistReworkCorrection=2` == `(a)` (`O` & `G`)
       - `K3_id2`: `HistRework=2` + `HistReworkQuiet=0` + `HistReworkCorrection=0` == `(b)` (`O` & `G`)
   (d) K4's five split settings on `O` and `G` (verifying all 40 known numbers: `O` sum,
       `O` first 3 node counts, `O` node diffs vs defaults, `O` bestmove diffs vs defaults,
       `G` sum, `G` first 3 node counts, `G` node diffs vs defaults, `G` bestmove diffs vs defaults).
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from j51_lib import (  # noqa: E402
    ALL_TEN_FALSE,
    EXP_BENCH11_NOOPT,
    EXP_BENCH11_PC20,
    EXP_BENCH13_NOOPT,
    EXP_BENCH13_PC20,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_PERFT5_NOOPT,
    G_EPD_PATH,
    JOB39,
    JOB48,
    JOB51,
    O_FENS_PATH,
    PC20_OPTIONS,
    WORK51,
    EngineReplyStopError,
    count_row_diffs,
    fmt_cmp,
    load_fens,
    make_leave_one_out_options,
    parse_m17_2k_sideB_options_from_meta,
    read_j39_rows,
    run_epd_depth12_strict,
    run_fresh_bench_strict,
    run_fresh_perft5_strict,
    sha256_file,
    utc_now,
)

def replace_pc20_option(opt_name: str, new_val: str) -> list[tuple[str, str]]:
    found = False
    out: list[tuple[str, str]] = []
    for k, v in PC20_OPTIONS:
        if k == opt_name:
            out.append((k, new_val))
            found = True
        else:
            out.append((k, v))
    if not found:
        raise RuntimeError(f"Option {opt_name!r} not in PC20_OPTIONS")
    return out
EXP_L2_O_SUM = 8658059
EXP_L2_G_SUM = 17155595

K4_SPECS = [
    {
        "key": "quiet0",
        "label": "HistReworkQuiet=0 (twin off, joint at 2)",
        "extra_opts": [("HistReworkQuiet", "0")],
        "exp_O_sum": 8474461,
        "exp_O_first3": [18942, 17838, 32827],
        "exp_O_nd": 200,
        "exp_O_bm": 45,
        "exp_G_sum": 17467287,
        "exp_G_first3": [37023, 63367, 92047],
        "exp_G_nd": 322,
        "exp_G_bm": 72,
    },
    {
        "key": "corr0",
        "label": "HistReworkCorrection=0 (joint off, twin at 2)",
        "extra_opts": [("HistReworkCorrection", "0")],
        "exp_O_sum": 8814382,
        "exp_O_first3": [20146, 24598, 38821],
        "exp_O_nd": 200,
        "exp_O_bm": 42,
        "exp_G_sum": 16925856,
        "exp_G_first3": [28972, 44163, 110782],
        "exp_G_nd": 349,
        "exp_G_bm": 82,
    },
    {
        "key": "quiet3",
        "label": "HistReworkQuiet=3 (twin at 3, joint at 2)",
        "extra_opts": [("HistReworkQuiet", "3")],
        "exp_O_sum": 8422552,
        "exp_O_first3": [11228, 22544, 67692],
        "exp_O_nd": 200,
        "exp_O_bm": 56,
        "exp_G_sum": 17154344,
        "exp_G_first3": [31592, 46444, 77818],
        "exp_G_nd": 322,
        "exp_G_bm": 71,
    },
    {
        "key": "corr3",
        "label": "HistReworkCorrection=3 (joint at 3, twin at 2)",
        "extra_opts": [("HistReworkCorrection", "3")],
        "exp_O_sum": 8331634,
        "exp_O_first3": [21105, 21973, 35198],
        "exp_O_nd": 200,
        "exp_O_bm": 49,
        "exp_G_sum": 17334720,
        "exp_G_first3": [39328, 62723, 54598],
        "exp_G_nd": 346,
        "exp_G_bm": 88,
    },
    {
        "key": "hr3",
        "label": "HistRework=3 (both at 3)",
        "extra_opts": [],
        "override_pc20": ("HistRework", "3"),
        "exp_O_sum": 8496156,
        "exp_O_first3": [16288, 20422, 68229],
        "exp_O_nd": 200,
        "exp_O_bm": 46,
        "exp_G_sum": 17546670,
        "exp_G_first3": [75373, 49624, 69445],
        "exp_G_nd": 349,
        "exp_G_bm": 87,
    },
]


def run_raw_planted_histreworkquite_check(exe_path: pathlib.Path, first_fen: str) -> dict[str, object]:
    """
    Sends misspelt `setoption name HistReworkQuite value 0` followed by `isready` directly to `bundle13`
    BEFORE any `go depth 12` search, verifying that our pre-`readyok` reply monitor stops immediately
    on `info string unknown option HistReworkQuite` with `0` searches run!
    """
    proc = subprocess.Popen(
        [str(exe_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    proc.stdin.write("uci\n")
    proc.stdin.flush()
    while True:
        ln = proc.stdout.readline()
        if not ln or ln.strip() == "uciok":
            break

    proc.stdin.write("setoption name HistReworkQuite value 0\nisready\n")
    proc.stdin.flush()

    pre_ready_lines: list[str] = []
    caught_line: str = ""
    searches_run = 0
    while True:
        raw = proc.stdout.readline()
        if not raw:
            break
        s = raw.rstrip("\r\n")
        if s == "readyok":
            break
        pre_ready_lines.append(s)
        low = s.lower()
        if (
            "unknown option" in low
            or "invalid value" in low
            or "illegal" in low
            or "invalid fen" in low
            or "ERROR" in s
        ):
            caught_line = s
            break

    try:
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        proc.wait(timeout=3)
    except Exception:
        proc.kill()
        proc.wait()

    if not caught_line:
        raise RuntimeError(f"Planted check did NOT catch unknown option! pre_ready_lines={pre_ready_lines}")
    return {
        "planted_option": "HistReworkQuite=0",
        "first_fen_never_searched": first_fen,
        "caught_line": caught_line,
        "pre_readyok_lines": pre_ready_lines,
        "searches_run": searches_run,
    }


def main() -> None:
    b13_exe = WORK51 / "bld_bundle13/forge"
    if not b13_exe.exists():
        raise RuntimeError(f"bundle13 binary not found at {b13_exe}; run run_p13.py first.")
    b13_str = str(b13_exe)

    lines: list[str] = []
    all_ok = True

    def rec(ok: bool, msg: str) -> None:
        nonlocal all_ok
        if not ok:
            all_ok = False
        lines.append(msg)
        print(msg, flush=True)

    lines.append(f"=== JOB 51 STEP 0 VERIFICATION ({utc_now()}) ===")
    b13_sha = sha256_file(b13_exe)
    lines.append(f"  bundle13 exe sha256({b13_exe}): {b13_sha}")

    # Verify programmatic extraction from Job 49 M17-2k_fastchess.txt.meta
    sideB_m17, each_m17, _ = parse_m17_2k_sideB_options_from_meta()
    rec(*fmt_cmp("M17-2k.meta Side B engine option count", len(sideB_m17), 11))
    rec(*fmt_cmp("M17-2k.meta -each option count", len(each_m17), 21))

    # 1. Pins with no option + PC20 bench 11/13
    b11_no = run_fresh_bench_strict(b13_str, 11, [])
    b13_no = run_fresh_bench_strict(b13_str, 13, [])
    p5_no = run_fresh_perft5_strict(b13_str)
    rec(*fmt_cmp("bundle13 bench 11 (no options)", b11_no, EXP_BENCH11_NOOPT))
    rec(*fmt_cmp("bundle13 bench 13 (no options)", b13_no, EXP_BENCH13_NOOPT))
    rec(*fmt_cmp("bundle13 perft 5 (no options)", p5_no, EXP_PERFT5_NOOPT))

    b11_pc20_def = run_fresh_bench_strict(b13_str, 11, PC20_OPTIONS)
    b13_pc20_def = run_fresh_bench_strict(b13_str, 13, PC20_OPTIONS)
    rec(*fmt_cmp("bundle13 PC20 bench 11 (implicit -1,-1)", b11_pc20_def, EXP_BENCH11_PC20))
    rec(*fmt_cmp("bundle13 PC20 bench 13 (implicit -1,-1)", b13_pc20_def, EXP_BENCH13_PC20))

    explicit_def_opts = list(PC20_OPTIONS) + list(ALL_TEN_FALSE) + [
        ("HistReworkQuiet", "-1"),
        ("HistReworkCorrection", "-1"),
    ]
    b11_pc20_exp = run_fresh_bench_strict(b13_str, 11, explicit_def_opts)
    b13_pc20_exp = run_fresh_bench_strict(b13_str, 13, explicit_def_opts)
    rec(*fmt_cmp("bundle13 PC20 bench 11 (explicit falses + -1,-1)", b11_pc20_exp, EXP_BENCH11_PC20))
    rec(*fmt_cmp("bundle13 PC20 bench 13 (explicit falses + -1,-1)", b13_pc20_exp, EXP_BENCH13_PC20))

    # 2. (e) Planted check: misspelt `HistReworkQuite=0` (both UCI-list precheck and raw engine reply monitor)
    fens_O = load_fens(O_FENS_PATH)
    fens_G = load_fens(G_EPD_PATH)
    rec(*fmt_cmp(f"O position count ({O_FENS_PATH})", len(fens_O), 200))
    rec(*fmt_cmp(f"G position count ({G_EPD_PATH})", len(fens_G), 353))

    uci_list_caught = ""
    try:
        run_fresh_bench_strict(b13_str, 11, [("HistReworkQuite", "0")])
    except EngineReplyStopError as exc:
        uci_list_caught = str(exc)
    rec(*fmt_cmp("Planted HistReworkQuite=0 caught by UCI-list check", 1 if "HistReworkQuite" in uci_list_caught else 0, 1))

    raw_planted = run_raw_planted_histreworkquite_check(b13_exe, fens_O[0])
    rec(
        *fmt_cmp(
            "Planted HistReworkQuite=0 caught immediately on engine pre-readyok line",
            raw_planted["caught_line"],
            "info string unknown option HistReworkQuite",
        )
    )
    rec(*fmt_cmp("Planted HistReworkQuite=0 searches run before stop", raw_planted["searches_run"], 0))
    (JOB51 / "step0_planted_HistReworkQuite.txt").write_text(
        "\n".join(
            [
                f"planted_option: {raw_planted['planted_option']}",
                f"uci_list_guard_exception: {uci_list_caught}",
                f"engine_pre_readyok_stop_line: {raw_planted['caught_line']}",
                f"searches_run: {raw_planted['searches_run']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # 3. Load reference rows from Job 39 (`OFF`) and Job 48 (`L2`)
    j39_off_O_path = JOB39 / "OFF_O_d12.rows.txt"
    j39_off_G_path = JOB39 / "OFF_G_d12.rows.txt"
    j48_l2_O_path = JOB48 / "partL_L2_all_off_O_d12.rows.txt"
    j48_l2_G_path = JOB48 / "partL_L2_all_off_G_d12.rows.txt"

    j39_O_rows = read_j39_rows(j39_off_O_path)
    j39_G_rows = read_j39_rows(j39_off_G_path)
    j48_O_rows = read_j39_rows(j48_l2_O_path)
    j48_G_rows = read_j39_rows(j48_l2_G_path)
    j39_O_sum = sum(r[1] for r in j39_O_rows)
    j39_G_sum = sum(r[1] for r in j39_G_rows)
    j48_O_sum = sum(r[1] for r in j48_O_rows)
    j48_G_sum = sum(r[1] for r in j48_G_rows)
    rec(*fmt_cmp(f"Job 39 OFF_O sum ({j39_off_O_path})", j39_O_sum, EXP_OFF_O_SUM))
    rec(*fmt_cmp(f"Job 39 OFF_G sum ({j39_off_G_path})", j39_G_sum, EXP_OFF_G_SUM))
    rec(*fmt_cmp(f"Job 48 L2_O sum ({j48_l2_O_path})", j48_O_sum, EXP_L2_O_SUM))
    rec(*fmt_cmp(f"Job 48 L2_G sum ({j48_l2_G_path})", j48_G_sum, EXP_L2_G_SUM))

    base_pc20_off = [("Threads", "1"), ("Hash", "16")] + list(PC20_OPTIONS) + list(ALL_TEN_FALSE)
    b_hr0_opts = [("Threads", "1"), ("Hash", "16")] + replace_pc20_option("HistRework", "0") + list(ALL_TEN_FALSE)

    # Build sweep task list (20 depth-12 sweeps across O and G, run on 4 cores with deterministic single-threaded search)
    tasks: list[tuple[str, pathlib.Path, list[tuple[str, str]], list[tuple[str, str]], pathlib.Path]] = [
        ("a_imp_O", O_FENS_PATH, base_pc20_off, [], JOB51 / "step0_a_defaults_imp_O_d12.rows.txt"),
        ("a_imp_G", G_EPD_PATH, base_pc20_off, [], JOB51 / "step0_a_defaults_imp_G_d12.rows.txt"),
        (
            "a_exp_O",
            O_FENS_PATH,
            base_pc20_off,
            [("HistReworkQuiet", "-1"), ("HistReworkCorrection", "-1")],
            JOB51 / "step0_a_defaults_exp_O_d12.rows.txt",
        ),
        (
            "a_exp_G",
            G_EPD_PATH,
            base_pc20_off,
            [("HistReworkQuiet", "-1"), ("HistReworkCorrection", "-1")],
            JOB51 / "step0_a_defaults_exp_G_d12.rows.txt",
        ),
        ("b_O", O_FENS_PATH, b_hr0_opts, [], JOB51 / "step0_b_hr0_O_d12.rows.txt"),
        ("b_G", G_EPD_PATH, b_hr0_opts, [], JOB51 / "step0_b_hr0_G_d12.rows.txt"),
        (
            "c1_O",
            O_FENS_PATH,
            b_hr0_opts,
            [("HistReworkQuiet", "2"), ("HistReworkCorrection", "2")],
            JOB51 / "step0_c1_hr0_q2_c2_O_d12.rows.txt",
        ),
        (
            "c1_G",
            G_EPD_PATH,
            b_hr0_opts,
            [("HistReworkQuiet", "2"), ("HistReworkCorrection", "2")],
            JOB51 / "step0_c1_hr0_q2_c2_G_d12.rows.txt",
        ),
        (
            "c2_O",
            O_FENS_PATH,
            base_pc20_off,
            [("HistReworkQuiet", "0"), ("HistReworkCorrection", "0")],
            JOB51 / "step0_c2_hr2_q0_c0_O_d12.rows.txt",
        ),
        (
            "c2_G",
            G_EPD_PATH,
            base_pc20_off,
            [("HistReworkQuiet", "0"), ("HistReworkCorrection", "0")],
            JOB51 / "step0_c2_hr2_q0_c0_G_d12.rows.txt",
        ),
    ]

    for sp in K4_SPECS:
        key = str(sp["key"])
        if "override_pc20" in sp:
            ov_k, ov_v = sp["override_pc20"]  # type: ignore[misc]
            b_opts = [("Threads", "1"), ("Hash", "16")] + replace_pc20_option(ov_k, ov_v) + list(ALL_TEN_FALSE)
            ex_opts: list[tuple[str, str]] = []
        else:
            b_opts = list(base_pc20_off)
            ex_opts = list(sp["extra_opts"])  # type: ignore[arg-type]
        tasks.append((f"d_{key}_O", O_FENS_PATH, b_opts, ex_opts, JOB51 / f"step0_d_{key}_O_d12.rows.txt"))
        tasks.append((f"d_{key}_G", G_EPD_PATH, b_opts, ex_opts, JOB51 / f"step0_d_{key}_G_d12.rows.txt"))

    sweep_map: dict[str, tuple[list[tuple[int, int, str, str]], int]] = {}

    def _run_one(item: tuple[int, tuple[str, pathlib.Path, list[tuple[str, str]], list[tuple[str, str]], pathlib.Path]]) -> tuple[str, list[tuple[int, int, str, str]], int]:
        idx, (t_id, s_path, b_o, ex_o, out_r) = item
        out_m = pathlib.Path(str(out_r) + ".meta")
        rows = run_epd_depth12_strict(
            exe_path=b13_str,
            set_path=s_path,
            base_opts=b_o,
            extra_opts=ex_o,
            out_rows=out_r,
            out_meta=out_m,
            depth=12,
            cpu_pin=idx % 4,
        )
        return t_id, rows, sum(r[1] for r in rows)

    with ThreadPoolExecutor(max_workers=4) as pool:
        for t_id, rows, tot in pool.map(_run_one, enumerate(tasks)):
            sweep_map[t_id] = (rows, tot)

    a_imp_O_rows, a_imp_O_sum = sweep_map["a_imp_O"]
    a_imp_G_rows, a_imp_G_sum = sweep_map["a_imp_G"]
    a_exp_O_rows, a_exp_O_sum = sweep_map["a_exp_O"]
    a_exp_G_rows, a_exp_G_sum = sweep_map["a_exp_G"]
    b_O_rows, b_O_sum = sweep_map["b_O"]
    b_G_rows, b_G_sum = sweep_map["b_G"]
    c1_O_rows, c1_O_sum = sweep_map["c1_O"]
    c1_G_rows, c1_G_sum = sweep_map["c1_G"]
    c2_O_rows, c2_O_sum = sweep_map["c2_O"]
    c2_G_rows, c2_G_sum = sweep_map["c2_G"]

    rec(*fmt_cmp("(a) K2 implicit defaults O sum vs Job 39 OFF_O", a_imp_O_sum, EXP_OFF_O_SUM))
    rec(*fmt_cmp("(a) K2 implicit defaults O exact rows vs Job 39 OFF_O", sum(1 for x, y in zip(a_imp_O_rows, j39_O_rows) if x == y), 200))
    rec(*fmt_cmp("(a) K2 implicit defaults G sum vs Job 39 OFF_G", a_imp_G_sum, EXP_OFF_G_SUM))
    rec(*fmt_cmp("(a) K2 implicit defaults G exact rows vs Job 39 OFF_G", sum(1 for x, y in zip(a_imp_G_rows, j39_G_rows) if x == y), 353))
    rec(*fmt_cmp("(a) K2 explicit (-1,-1) O exact rows vs Job 39 OFF_O", sum(1 for x, y in zip(a_exp_O_rows, j39_O_rows) if x == y), 200))
    rec(*fmt_cmp("(a) K2 explicit (-1,-1) G exact rows vs Job 39 OFF_G", sum(1 for x, y in zip(a_exp_G_rows, j39_G_rows) if x == y), 353))

    rec(*fmt_cmp("(b) HistRework=0 O sum vs Job 48 L2_O", b_O_sum, EXP_L2_O_SUM))
    rec(*fmt_cmp("(b) HistRework=0 O exact rows vs Job 48 L2_O", sum(1 for x, y in zip(b_O_rows, j48_O_rows) if x == y), 200))
    rec(*fmt_cmp("(b) HistRework=0 G sum vs Job 48 L2_G", b_G_sum, EXP_L2_G_SUM))
    rec(*fmt_cmp("(b) HistRework=0 G exact rows vs Job 48 L2_G", sum(1 for x, y in zip(b_G_rows, j48_G_rows) if x == y), 353))

    rec(*fmt_cmp("(c1) K3 HistRework=0 + Q=2,C=2 O sum vs (a)", c1_O_sum, EXP_OFF_O_SUM))
    rec(*fmt_cmp("(c1) K3 HistRework=0 + Q=2,C=2 O exact rows vs (a)", sum(1 for x, y in zip(c1_O_rows, a_imp_O_rows) if x == y), 200))
    rec(*fmt_cmp("(c1) K3 HistRework=0 + Q=2,C=2 G sum vs (a)", c1_G_sum, EXP_OFF_G_SUM))
    rec(*fmt_cmp("(c1) K3 HistRework=0 + Q=2,C=2 G exact rows vs (a)", sum(1 for x, y in zip(c1_G_rows, a_imp_G_rows) if x == y), 353))

    rec(*fmt_cmp("(c2) K3 HistRework=2 + Q=0,C=0 O sum vs (b)", c2_O_sum, EXP_L2_O_SUM))
    rec(*fmt_cmp("(c2) K3 HistRework=2 + Q=0,C=0 O exact rows vs (b)", sum(1 for x, y in zip(c2_O_rows, b_O_rows) if x == y), 200))
    rec(*fmt_cmp("(c2) K3 HistRework=2 + Q=0,C=0 G sum vs (b)", c2_G_sum, EXP_L2_G_SUM))
    rec(*fmt_cmp("(c2) K3 HistRework=2 + Q=0,C=0 G exact rows vs (b)", sum(1 for x, y in zip(c2_G_rows, b_G_rows) if x == y), 353))

    k4_results: list[dict[str, object]] = []
    for sp in K4_SPECS:
        key = str(sp["key"])
        o_path = JOB51 / f"step0_d_{key}_O_d12.rows.txt"
        g_path = JOB51 / f"step0_d_{key}_G_d12.rows.txt"
        o_rows, o_sum = sweep_map[f"d_{key}_O"]
        g_rows, g_sum = sweep_map[f"d_{key}_G"]

        o_first3 = [int(r[1]) for r in o_rows[:3]]
        g_first3 = [int(r[1]) for r in g_rows[:3]]
        o_diff_d = count_row_diffs(o_rows, a_imp_O_rows)
        g_diff_d = count_row_diffs(g_rows, a_imp_G_rows)
        o_nd, o_bm = o_diff_d["nodes_diff"], o_diff_d["bestmove_diff"]
        g_nd, g_bm = g_diff_d["nodes_diff"], g_diff_d["bestmove_diff"]

        rec(*fmt_cmp(f"(d) K4 {key} O sum", o_sum, sp["exp_O_sum"]))
        rec(*fmt_cmp(f"(d) K4 {key} O first3 nodes", o_first3, sp["exp_O_first3"]))
        rec(*fmt_cmp(f"(d) K4 {key} O node diffs vs defaults", o_nd, sp["exp_O_nd"]))
        rec(*fmt_cmp(f"(d) K4 {key} O bestmove diffs vs defaults", o_bm, sp["exp_O_bm"]))
        rec(*fmt_cmp(f"(d) K4 {key} G sum", g_sum, sp["exp_G_sum"]))
        rec(*fmt_cmp(f"(d) K4 {key} G first3 nodes", g_first3, sp["exp_G_first3"]))
        rec(*fmt_cmp(f"(d) K4 {key} G node diffs vs defaults", g_nd, sp["exp_G_nd"]))
        rec(*fmt_cmp(f"(d) K4 {key} G bestmove diffs vs defaults", g_bm, sp["exp_G_bm"]))

        k4_results.append(
            {
                "key": key,
                "label": sp["label"],
                "O_rows_file": str(o_path),
                "O_rows_sha256": sha256_file(o_path),
                "O_sum": o_sum,
                "O_delta_vs_defaults": o_sum - EXP_OFF_O_SUM,
                "O_first3": o_first3,
                "O_node_diffs": o_nd,
                "O_bestmove_diffs": o_bm,
                "G_rows_file": str(g_path),
                "G_rows_sha256": sha256_file(g_path),
                "G_sum": g_sum,
                "G_delta_vs_defaults": g_sum - EXP_OFF_G_SUM,
                "G_first3": g_first3,
                "G_node_diffs": g_nd,
                "G_bestmove_diffs": g_bm,
            }
        )

    rec(*fmt_cmp("STEP 0 OVERALL", 1 if all_ok else 0, 1))
    (JOB51 / "step0_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (JOB51 / "step0_results.json").write_text(
        json.dumps(
            {
                "bundle13_exe": str(b13_exe),
                "bundle13_sha256": b13_sha,
                "planted": raw_planted,
                "uci_list_caught": uci_list_caught,
                "a_imp_O_sum": a_imp_O_sum,
                "a_imp_G_sum": a_imp_G_sum,
                "a_exp_O_sum": a_exp_O_sum,
                "a_exp_G_sum": a_exp_G_sum,
                "b_O_sum": b_O_sum,
                "b_G_sum": b_G_sum,
                "c1_O_sum": c1_O_sum,
                "c1_G_sum": c1_G_sum,
                "c2_O_sum": c2_O_sum,
                "c2_G_sum": c2_G_sum,
                "k4": k4_results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if not all_ok:
        raise RuntimeError("Step 0 failed!")


if __name__ == "__main__":
    main()
