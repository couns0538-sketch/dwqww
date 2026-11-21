#!/usr/bin/env python3
"""
Job 51 Shared Harness Library (`j51_lib.py`):
- Reuses `j48_lib.py`'s strict UCI runner (`StrictEngineSession`, `EngineReplyStopError`,
  `run_epd_depth12_strict`) and adds `WORK51`-isolated match execution, programmatic extraction
  of Job 49 `M17-2k` Side B options directly from `forge-combo29/carbon2/job49/M17-2k_fastchess.txt.meta`
  (never retyped by hand), and 3-way uncertainty propagation for `M20 + M21 - M17-2k`.
- Every runner keeps every line the engine prints before EVERY `readyok` (recording them in `.meta`)
  and STOPS IMMEDIATELY on `unknown option`, `invalid value`, `illegal`, `invalid FEN`, and `ERROR`,
  and checks that every option it sends is in the executable's own `uci` option list.
"""
from __future__ import annotations

import math
import os
import pathlib
import re
import signal
import subprocess
import sys
import time
from typing import Optional, Sequence

sys.dont_write_bytecode = True

REPO = pathlib.Path("/agent/repos/dwqww")
JOB51 = REPO / "forge-combo29/carbon2/job51"
JOB50 = REPO / "forge-combo29/carbon2/job50"
JOB49 = REPO / "forge-combo29/carbon2/job49"
JOB48 = REPO / "forge-combo29/carbon2/job48"
JOB39 = REPO / "forge-combo29/carbon2/job39"

WORK51 = pathlib.Path("/tmp/carbon2_job51")

sys.path.insert(0, str(JOB48))
from j48_lib import (  # noqa: E402,F401
    ALL_NINE_IDEA_FALSE,
    ALL_TEN_FALSE,
    BUNDLE7_PATCH,
    EXP_BENCH11_NOOPT,
    EXP_BENCH11_PC20,
    EXP_BENCH13_NOOPT,
    EXP_BENCH13_PC20,
    EXP_BUNDLE9_SHA,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_P8_HOIST_SHA,
    EXP_P9_B8_FAST_SHA,
    EXP_PERFT5_NOOPT,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    FASTCHESS_BIN,
    G_EPD_PATH,
    NINE_SWITCH_NAMES,
    O_FENS_PATH,
    P8_HOIST_PATCH,
    P9_B8_FAST_PATCH,
    PC20_OPTIONS,
    TPL_V3,
    UHO_BOOK,
    EngineReplyStopError,
    StrictEngineSession,
    apply_bundle9_to_fresh_v3,
    build_release_v3,
    count_row_diffs,
    diff_elo_interval,
    ensure_bundle9_exe,
    fmt_cmp,
    get_id_name_strict,
    load_fens,
    make_leave_one_out_options,
    pgn_to_games_tsv,
    read_j39_rows,
    recount_games_tsv,
    run_epd_depth12_strict,
    run_fresh_bench_strict,
    run_fresh_perft5_strict,
    sha256_file,
    utc_now,
)

P13_PATCH_PATH = JOB51 / "P13_histrework_split.patch.txt"
_WORD_ERROR_RE = re.compile(r"\berror\b", re.IGNORECASE)


def parse_m17_2k_sideB_options_from_meta(
    meta_path: pathlib.Path = JOB49 / "M17-2k_fastchess.txt.meta",
) -> tuple[list[tuple[str, str]], list[tuple[str, str]], str]:
    """
    Programmatically extracts Side B (`all_off_PC20`) engine-specific `option.<k>=<v>`
    and shared `-each` `option.<k>=<v>` directly from `forge-combo29/carbon2/job49/M17-2k_fastchess.txt.meta`
    (never retyped by hand, per File 51 lines 144-146).
    """
    cmd_line = ""
    for ln in meta_path.read_text(encoding="utf-8").splitlines():
        if ln.startswith("command: "):
            cmd_line = ln[len("command: ") :].strip()
            break
    if not cmd_line:
        raise RuntimeError(f"Missing 'command: ' line in {meta_path}")

    toks = cmd_line.split()
    eng_indices = [i for i, t in enumerate(toks) if t == "-engine"]
    each_indices = [i for i, t in enumerate(toks) if t == "-each"]
    openings_indices = [i for i, t in enumerate(toks) if t == "-openings"]
    if len(eng_indices) != 2 or len(each_indices) != 1 or len(openings_indices) != 1:
        raise RuntimeError(f"Unexpected fastchess command layout in {meta_path}: {cmd_line}")

    eng2_slice = toks[eng_indices[1] + 1 : each_indices[0]]
    each_slice = toks[each_indices[0] + 1 : openings_indices[0]]

    if "name=all_off_PC20" not in eng2_slice:
        raise RuntimeError(f"Second engine in {meta_path} is not all_off_PC20: {eng2_slice}")

    sideB_engine_opts: list[tuple[str, str]] = []
    for tok in eng2_slice:
        if tok.startswith("option."):
            k, v = tok[len("option.") :].split("=", 1)
            sideB_engine_opts.append((k, v))

    each_opts: list[tuple[str, str]] = []
    for tok in each_slice:
        if tok.startswith("option."):
            k, v = tok[len("option.") :].split("=", 1)
            each_opts.append((k, v))

    if len(sideB_engine_opts) != 11 or len(each_opts) != 21:
        raise RuntimeError(
            f"Unexpected option counts parsed from {meta_path}: "
            f"sideB_engine_opts={len(sideB_engine_opts)}, each_opts={len(each_opts)}"
        )
    return sideB_engine_opts, each_opts, cmd_line


def three_way_additivity_interval(
    elo_20: float,
    hw95_20: float,
    elo_21: float,
    hw95_21: float,
    elo_17: float,
    hw95_17: float,
) -> tuple[float, float, float, float]:
    """
    File 51 lines 156-158:
      val = M20 + M21 - M17-2k
      se = sqrt(se_20^2 + se_21^2 + se_17^2), where se = half-width / 1.96
      hw95 = 1.96 * se
    """
    val = elo_20 + elo_21 - elo_17
    se_20 = hw95_20 / 1.96
    se_21 = hw95_21 / 1.96
    se_17 = hw95_17 / 1.96
    se = math.sqrt(se_20 * se_20 + se_21 * se_21 + se_17 * se_17)
    hw95 = 1.96 * se
    return val, hw95, val - hw95, val + hw95


def run_match_strict_j51(
    *,
    tag: str,
    out_dir: pathlib.Path,
    exe_path: pathlib.Path,
    eng1_name: str,
    eng2_name: str,
    e1_switches: Sequence[tuple[str, str]],
    e2_switches: Sequence[tuple[str, str]],
    each_base_opts: Sequence[tuple[str, str]],
    nodes: int,
    start_line: int,
    rounds: int,
    cutoff_epoch: Optional[float] = None,
    concurrency: Optional[int] = None,
) -> dict[str, object]:
    WORK51.mkdir(parents=True, exist_ok=True)
    s_a = StrictEngineSession(str(exe_path))
    s_a.apply_options(list(each_base_opts) + list(e1_switches), f"{tag}_SideA_preflight")
    pre_a = list(s_a.pre_readyok_lines)
    ver_a = s_a.verified_option_count
    id_name = s_a.id_name
    s_a.close()

    s_b = StrictEngineSession(str(exe_path))
    s_b.apply_options(list(each_base_opts) + list(e2_switches), f"{tag}_SideB_preflight")
    pre_b = list(s_b.pre_readyok_lines)
    ver_b = s_b.verified_option_count
    s_b.close()

    cores = os.cpu_count() or 4
    conc = concurrency if concurrency is not None else cores

    pgn_tmp = WORK51 / f"tmp_{tag}.pgn"
    if pgn_tmp.exists():
        pgn_tmp.unlink()

    fc_out_path = out_dir / f"{tag}_fastchess.txt"
    meta_out_path = out_dir / f"{tag}_fastchess.txt.meta"
    tsv_out_path = out_dir / f"{tag}_games.tsv"
    rec_out_path = out_dir / f"{tag}_recount.txt"

    each_cli = [f"option.{k}={v}" for k, v in each_base_opts]
    e1_cli = [f"option.{k}={v}" for k, v in e1_switches]
    e2_cli = [f"option.{k}={v}" for k, v in e2_switches]

    cmd = [
        str(FASTCHESS_BIN),
        "-engine",
        f"cmd={exe_path}",
        f"name={eng1_name}",
        f"nodes={nodes}",
        *e1_cli,
        "-engine",
        f"cmd={exe_path}",
        f"name={eng2_name}",
        f"nodes={nodes}",
        *e2_cli,
        "-each",
        "proto=uci",
        *each_cli,
        "-openings",
        f"file={UHO_BOOK}",
        "format=epd",
        "order=sequential",
        f"start={start_line}",
        "-rounds",
        str(rounds),
        "-games",
        "2",
        "-repeat",
        "-concurrency",
        str(conc),
        "-pgnout",
        f"file={pgn_tmp}",
        "notation=uci",
        "-ratinginterval",
        "100",
    ]

    print(
        f"[{utc_now()}] Starting {tag}: {rounds * 2} games at nodes={nodes} "
        f"(book lines {start_line}..{start_line + rounds - 1}, concurrency={conc})",
        flush=True,
    )
    t0 = time.time()
    start_u = utc_now()
    was_cut = False
    with open(fc_out_path, "wb") as out_f:
        proc = subprocess.Popen(cmd, stdout=out_f, stderr=subprocess.STDOUT, cwd=str(WORK51))
        while True:
            rc = proc.poll()
            if rc is not None:
                break
            if cutoff_epoch is not None and time.time() >= cutoff_epoch:
                was_cut = True
                proc.send_signal(signal.SIGINT)
                try:
                    rc = proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    rc = proc.wait()
                break
            time.sleep(1.0)
    wall_s = time.time() - t0
    end_u = utc_now()

    fc_text = fc_out_path.read_text(encoding="utf-8", errors="replace")
    bad_fc_lines: list[str] = []
    for ln in fc_text.splitlines():
        low = ln.lower()
        if (
            "unknown option" in low
            or "invalid value" in low
            or "illegal" in low
            or "invalid fen" in low
            or "ERROR" in ln
            or _WORD_ERROR_RE.search(ln)
        ):
            bad_fc_lines.append(ln)

    n_games = pgn_to_games_tsv(pgn_tmp, tsv_out_path, eng1_name, eng2_name) if pgn_tmp.exists() else 0
    if pgn_tmp.exists():
        pgn_tmp.unlink()
    if n_games < rounds * 2:
        was_cut = True

    meta_lines = [
        f"match_tag: {tag}",
        f"exe_path: {exe_path}",
        f"exe_sha256({exe_path}): {sha256_file(exe_path)}",
        f"id_name: {id_name}",
        f"copied_base_options_from: {JOB49 / 'M17-2k_fastchess.txt.meta'}",
        f"sideA_options_verified_in_uci_list: {ver_a}",
        f"sideB_options_verified_in_uci_list: {ver_b}",
        f"sideA_preflight_pre_readyok_lines: {len(pre_a)}",
        f"sideB_preflight_pre_readyok_lines: {len(pre_b)}",
        f"fastchess_path: {FASTCHESS_BIN}",
        f"fastchess_sha256({FASTCHESS_BIN}): {sha256_file(FASTCHESS_BIN)}",
        f"book_path: {UHO_BOOK}",
        f"book_sha256({UHO_BOOK}): {sha256_file(UHO_BOOK)}",
        f"start_line: {start_line}",
        f"end_line_target: {start_line + rounds - 1}",
        f"rounds: {rounds}",
        f"target_games: {rounds * 2}",
        f"finished_games: {n_games}",
        f"nodes_per_move: {nodes}",
        f"concurrency: {conc}",
        f"bad_error_lines_in_fastchess_output: {len(bad_fc_lines)}",
        f"command: {' '.join(cmd)}",
        f"start_utc: {start_u}",
        f"end_utc: {end_u}",
        f"wall_s: {wall_s:.3f}",
        f"exit_code: {rc}",
        f"was_cut: {was_cut}",
    ]
    meta_out_path.write_text("\n".join(meta_lines) + "\n", encoding="utf-8")

    rec = recount_games_tsv(
        tag=tag,
        tsv_path=tsv_out_path,
        fc_txt_path=fc_out_path,
        out_recount_path=rec_out_path,
        engine1=eng1_name,
        engine2=eng2_name,
        book_path=UHO_BOOK,
        start_line=start_line,
        target_rounds=rounds,
        was_cut=was_cut,
    )
    ok_bad, s_bad = fmt_cmp(f"{tag} fastchess error/unknown/invalid/illegal lines", len(bad_fc_lines), 0)
    with open(rec_out_path, "a", encoding="utf-8") as rf:
        rf.write(s_bad + "\n")
        rf.write(f"tsv_sha256({tsv_out_path}): {sha256_file(tsv_out_path)}\n")
        rf.write(f"fastchess_txt_sha256({fc_out_path}): {sha256_file(fc_out_path)}\n")
    if not ok_bad:
        raise RuntimeError(f"{tag} fastchess output had error lines: {bad_fc_lines[:5]}")
    rec["W"] = int(rec["w"])
    rec["L"] = int(rec["l"])
    rec["D"] = int(rec["d"])
    rec["hw95"] = round(float(rec["err95"]), 2) if rec.get("err95") is not None else 0.0
    rec["elo"] = round(float(rec["elo"]), 2) if rec.get("elo") is not None else 0.0
    rec["ci_lo"] = round(rec["elo"] - rec["hw95"], 2)
    rec["ci_hi"] = round(rec["elo"] + rec["hw95"], 2)
    rec["fc_elo"] = round(float(rec.get("fc_elo", rec["elo"])), 2)
    rec["fc_hw95"] = round(float(rec.get("fc_err95", rec["hw95"])), 2)
    rec["wall_s"] = wall_s
    rec["was_cut"] = was_cut
    return rec
