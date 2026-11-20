#!/usr/bin/env python3
"""
Job 40 Shared Library (`j40_lib.py`):
- Build & OFF/ON verification helpers for `r15d + v3` and `bundle_grok.patch.txt`
- Exact `PC20` options (`PC20_OPTIONS` from `forge-combo29/carbon2/job35/ref_driver.py`)
- Timing runner for Part T (`O` set, 200 positions, depth 12, wall time from `go` to `bestmove`)
- `fastchess` runner + PGN-to-per-game-list converter + independent pentanomial/WLD Elo recounter
  matching `fastchess`'s exact `EloPentanomial` formula (`elo_pentanomial.cpp`).
"""
from __future__ import annotations

import datetime
import hashlib
import math
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
from typing import Optional

sys.dont_write_bytecode = True

REPO = pathlib.Path("/agent/repos/dwqww")
JOB40 = REPO / "forge-combo29/carbon2/job40"
JOB39 = REPO / "forge-combo29/carbon2/job39"
JOB36 = REPO / "forge-combo29/carbon2/job36"
JOB35 = REPO / "forge-combo29/carbon2/job35"
WORK40 = pathlib.Path("/tmp/carbon2_job40")
TPL_V3 = pathlib.Path("/tmp/carbon2_job36/tpl_r15d_v3")
NET768 = "/tmp/carbon2_work/net768.fnn3"
O_FENS_PATH = pathlib.Path("/tmp/carbon2_job39/sets/first200.fens")

BUNDLE_PATCH = JOB39 / "bundle_grok.patch.txt"
EXP_BUNDLE_PATCH_SHA = "d0ae7f01f33be912ffe07ca2efdbc0f147c0386a77864a5a3547e0af21c001ec"

FASTCHESS_BIN = WORK40 / "fastchess"
UHO_BOOK = WORK40 / "UHO_Lichess_4852_v1.epd"
EXP_UHO_LINES = 2632036
EXP_UHO_SHA = "7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a"

# Job 39 Known Answers for Bundle ALL ON
EXP_J39_OFF_O_SUM = 8315168
EXP_J39_ALL_ON_O_SUM = 8035170
EXP_J39_ALL_ON_SETA_RECORDS = 27991
EXP_J39_ALL_ON_SETA_SEARCHES = 28117
EXP_J39_ALL_ON_SETA_NODES = 111242459
EXP_J39_ALL_ON_SETA_SHA = "c0da7ec87c6e6928320d0e8db3a15e12051d3f31b3391f09d4d5ef4590c58bce"

# Job 39 order of the six switches
SIX_SWITCHES = [
    ("K4", "IdeaK4"),
    ("S32", "IdeaS32"),
    ("B1", "IdeaB1"),
    ("S13", "IdeaS13"),
    ("S10", "IdeaS10"),
    ("B8", "IdeaB8"),
]

ALL_SIX_FALSE = [(opt, "false") for _, opt in SIX_SWITCHES]
ALL_SIX_TRUE = [(opt, "true") for _, opt in SIX_SWITCHES]

sys.path.insert(0, str(JOB39))
sys.path.insert(0, str(JOB36))
sys.path.insert(0, str(JOB35))

from j39_lib import (  # noqa: E402
    EXP_BENCH11_NOOPT,
    EXP_BENCH11_PC20,
    EXP_BENCH13_NOOPT,
    EXP_BENCH13_PC20,
    EXP_PERFT5_NOOPT,
    EXP_TREE_SHAS,
    apply_patch_to_fresh_v3,
    build_release_v3,
    diff_rows,
    fmt_cmp,
    get_id_name,
    load_fens,
    pc20_option_lines,
    run_epd_depth12,
    run_fresh_bench,
    run_fresh_perft5,
    run_selfgame_set_with_options,
    sha256_file,
    utc_now,
    verify_all_off_numbers,
    write_seta_meta,
)
from loop_v3_driver import write_v2_v3_rows  # noqa: E402
from ref_driver import PC20_OPTIONS  # noqa: E402

CI95ZSCORE = 1.959963984540054


def read_j39_rows(rows_path: pathlib.Path) -> list[tuple[int, int, str, str]]:
    out: list[tuple[int, int, str, str]] = []
    for ln in rows_path.read_text(encoding="utf-8").splitlines():
        if not ln or ln.startswith("#") or ln.startswith("position\t"):
            continue
        pos_s, nd_s, bm, sc = ln.split("\t")
        out.append((int(pos_s), int(nd_s), bm, sc))
    return out


def score_to_elo_diff(score: float) -> float:
    if score <= 0.0:
        return -float("inf")
    if score >= 1.0:
        return float("inf")
    return -400.0 * math.log10(1.0 / score - 1.0)


def compute_pentanomial_elo(ptnml: list[int]) -> dict[str, float | str]:
    """
    Exact match to `fastchess::elo::EloPentanomial` (`elo_pentanomial.cpp`).
    `ptnml = [LL, LD, WL_plus_DD, WD, WW]` for engine 1 vs engine 2.
    """
    ll, ld, wldd, wd, ww = ptnml
    pairs = ll + ld + wldd + wd + ww
    if pairs == 0:
        return {
            "pairs": 0,
            "score": 0.0,
            "elo": 0.0,
            "err95": 0.0,
            "ci_low": 0.0,
            "ci_high": 0.0,
            "los_pct": 50.0,
            "nelo": 0.0,
            "nelo_err95": 0.0,
        }
    p_ll = ll / pairs
    p_ld = ld / pairs
    p_wldd = wldd / pairs
    p_wd = wd / pairs
    p_ww = ww / pairs

    score = p_ww + 0.75 * p_wd + 0.5 * p_wldd + 0.25 * p_ld
    variance = (
        p_ww * ((1.0 - score) ** 2)
        + p_wd * ((0.75 - score) ** 2)
        + p_wldd * ((0.5 - score) ** 2)
        + p_ld * ((0.25 - score) ** 2)
        + p_ll * ((0.0 - score) ** 2)
    )
    var_pair = variance / pairs
    s_hi = score + CI95ZSCORE * math.sqrt(var_pair)
    s_lo = score - CI95ZSCORE * math.sqrt(var_pair)
    elo = score_to_elo_diff(score)
    if 0.0 < s_lo and s_hi < 1.0:
        elo_lo = score_to_elo_diff(s_lo)
        elo_hi = score_to_elo_diff(s_hi)
        err95 = (elo_hi - elo_lo) / 2.0
    else:
        elo_lo = float("-inf") if s_lo <= 0.0 else score_to_elo_diff(s_lo)
        elo_hi = float("inf") if s_hi >= 1.0 else score_to_elo_diff(s_hi)
        err95 = float("inf")
    los_pct = 50.0 if var_pair <= 0.0 else 100.0 * (1.0 - math.erf(-(score - 0.5) / math.sqrt(2.0 * var_pair))) / 2.0
    if variance > 0.0:
        c = 800.0 / math.log(10.0)
        nelo = (score - 0.5) / math.sqrt(2.0 * variance) * c
        nelo_hi = (s_hi - 0.5) / math.sqrt(2.0 * variance) * c
        nelo_lo = (s_lo - 0.5) / math.sqrt(2.0 * variance) * c
        nelo_err = (nelo_hi - nelo_lo) / 2.0
    else:
        nelo = 0.0
        nelo_err = 0.0
    return {
        "pairs": pairs,
        "score": score,
        "elo": elo,
        "err95": err95,
        "ci_low": elo - err95,
        "ci_high": elo + err95,
        "exact_ci_low": elo_lo,
        "exact_ci_high": elo_hi,
        "los_pct": los_pct,
        "nelo": nelo,
        "nelo_err95": nelo_err,
    }
