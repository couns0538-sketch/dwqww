#!/usr/bin/env python3
"""
Job 49 Shared Harness Library (`j49_lib.py`):
Reuses `j48_lib.py`'s strict UCI runner (`StrictEngineSession`, `EngineReplyStopError`,
`run_epd_depth12_strict`, `run_match_strict_j48`, `diff_elo_interval`) so every runner:
1. Keeps every line the engine prints before EVERY `readyok` (recording them in `<rows>.meta`)
   and STOPS IMMEDIATELY on `unknown option`, `invalid value`, `illegal`, `invalid FEN`, and `ERROR`.
2. Checks that every option it sends is in the executable's own `uci` option list.
"""
from __future__ import annotations

import pathlib
import sys

sys.dont_write_bytecode = True

REPO = pathlib.Path("/agent/repos/dwqww")
JOB49 = REPO / "forge-combo29/carbon2/job49"
JOB48 = REPO / "forge-combo29/carbon2/job48"
JOB47 = REPO / "forge-combo29/carbon2/job47"
JOB46 = REPO / "forge-combo29/carbon2/job46"
JOB44 = REPO / "forge-combo29/carbon2/job44"

WORK49 = pathlib.Path("/tmp/carbon2_job49")
WORK47 = pathlib.Path("/tmp/carbon2_job47")

sys.path.insert(0, str(JOB48))
from j48_lib import (  # noqa: E402,F401
    ALL_NINE_IDEA_FALSE,
    ALL_TEN_FALSE,
    BUNDLE7_PATCH,
    BUNDLE9_SIDE_A_SWITCHES,
    BUNDLE9_SIDE_B_SWITCHES,
    EXP_BENCH11_NOOPT,
    EXP_BENCH11_PC20,
    EXP_BENCH13_NOOPT,
    EXP_BENCH13_PC20,
    EXP_BUNDLE9_SHA,
    EXP_OFF_O_SUM,
    EXP_P8_HOIST_SHA,
    EXP_P9_B8_FAST_SHA,
    EXP_PERFT5_NOOPT,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    FASTCHESS_BIN,
    LEAVE_ONE_OUT_SPECS,
    NINE_SWITCH_NAMES,
    O_FENS_PATH,
    P8_HOIST_PATCH,
    P9_B8_FAST_PATCH,
    PC20_OPTIONS,
    TPL_V3,
    UHO_BOOK,
    EngineReplyStopError,
    StrictEngineSession,
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
    run_match_strict_j48,
    sha256_file,
    utc_now,
)
