#!/usr/bin/env python3
"""
Job 41 Shared Library (`j41_lib.py`):
- Build, OFF-number, UCI `HindsightDepth` option check, `O`/`G` depth-12 runner,
  `Set A line L` runner, Part T timing runner, and Part M `fastchess` + PGN recounter.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
from typing import Optional

sys.dont_write_bytecode = True

REPO = pathlib.Path("/agent/repos/dwqww")
JOB41 = REPO / "forge-combo29/carbon2/job41"
JOB40 = REPO / "forge-combo29/carbon2/job40"
JOB39 = REPO / "forge-combo29/carbon2/job39"
JOB36 = REPO / "forge-combo29/carbon2/job36"
JOB35 = REPO / "forge-combo29/carbon2/job35"

WORK41 = pathlib.Path("/tmp/carbon2_job41")
WORK40 = pathlib.Path("/tmp/carbon2_job40")
TPL_V3 = pathlib.Path("/tmp/carbon2_job36/tpl_r15d_v3")
O_FENS_PATH = pathlib.Path("/tmp/carbon2_job39/sets/first200.fens")
G_EPD_PATH = pathlib.Path("/tmp/carbon2_job39/sets/set_G.epd")

BUNDLE6_PATCH = JOB39 / "bundle_grok.patch.txt"
P6_B8_PATCH = JOB39 / "P6_B8_078.patch.txt"
EXP_BUNDLE6_SHA = "d0ae7f01f33be912ffe07ca2efdbc0f147c0386a77864a5a3547e0af21c001ec"
EXP_P6_B8_SHA = "b8bf053cdd0f8c22c977a07126c7412b689bbbf8b157d15122717282a32d2a92"
GROK_028_PATCH = WORK40 / "grok_028_idea.patch.txt"
EXP_GROK_028_SHA = "f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474"

FASTCHESS_BIN = WORK40 / "fastchess"
UHO_BOOK = WORK40 / "UHO_Lichess_4852_v1.epd"
EXP_UHO_LINES = 2632036
EXP_UHO_SHA = "7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a"

SIX_OLD_SWITCHES = [
    ("K4", "IdeaK4", "P1_K4_093_on_O_d12.rows.txt", 8080229),
    ("S32", "IdeaS32", "P2_S32_074_on_O_d12.rows.txt", 8339315),
    ("B1", "IdeaB1", "P3_B1_030_on_O_d12.rows.txt", 8548042),
    ("S13", "IdeaS13", "P4_S13_016_on_O_d12.rows.txt", 8077984),
    ("S10", "IdeaS10", "P5_S10_081_on_O_d12.rows.txt", 8314153),
    ("B8", "IdeaB8", "P6_B8_078_on_O_d12.rows.txt", 8262696),
]

SEVEN_SWITCH_NAMES = ["IdeaK4", "IdeaS32", "IdeaB1", "IdeaS13", "IdeaS10", "IdeaB8", "IdeaB8b"]
ALL_SEVEN_FALSE = [(opt, "false") for opt in SEVEN_SWITCH_NAMES]

EXP_OFF_O_SUM = 8315168
EXP_OFF_G_SUM = 17611204
EXP_HINDSIGHT_O_SUM = 8732910
EXP_HINDSIGHT_O_FIRST3 = [12572, 30191, 29126]

sys.path.insert(0, str(JOB40))
sys.path.insert(0, str(JOB39))
sys.path.insert(0, str(JOB36))
sys.path.insert(0, str(JOB35))

from j39_lib import (  # noqa: E402
    EXP_BENCH11_NOOPT,
    EXP_BENCH11_PC20,
    EXP_BENCH13_NOOPT,
    EXP_BENCH13_PC20,
    EXP_PERFT5_NOOPT,
    EXP_SETA_L_NODES,
    EXP_SETA_L_RECORDS,
    EXP_SETA_L_SHA,
    EXP_TREE_SHAS,
    apply_patch_to_fresh_v3,
    build_release_v3,
    diff_rows,
    fmt_cmp,
    generate_diff_u_patch,
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
from j40_lib import compute_pentanomial_elo, read_j39_rows  # noqa: E402
from loop_v3_driver import write_v2_v3_rows  # noqa: E402
from recount_pgn import pgn_to_games_tsv, recount_games_tsv  # noqa: E402
from ref_driver import PC20_OPTIONS  # noqa: E402


def verify_uci_option_check(exe_path: str, opt_name: str = "HindsightDepth") -> tuple[bool, list[str]]:
    """
    Reads `exe_path`'s `uci` option list and verifies `option name <opt_name> type check default false`
    is listed and that setting `true` and `false` produces zero `unknown option` / `invalid value` / stderr.
    """
    stdin = (
        "uci\n"
        f"setoption name {opt_name} value true\n"
        "isready\n"
        f"setoption name {opt_name} value false\n"
        "isready\n"
        "quit\n"
    )
    res = subprocess.run([exe_path], input=stdin, text=True, capture_output=True, check=True)
    expected_decl = f"option name {opt_name} type check default false"
    out_lines = res.stdout.splitlines()
    found_decl = any(ln.strip() == expected_decl for ln in out_lines)
    bad_hits = [
        ln
        for ln in out_lines
        if ("unknown option" in ln.lower() or "invalid value" in ln.lower())
    ]
    stderr_len = len(res.stderr.encode("utf-8"))
    ok1, s1 = fmt_cmp(f"{pathlib.Path(exe_path).parent.name} uci lists {opt_name}", found_decl, True)
    ok2, s2 = fmt_cmp(f"{pathlib.Path(exe_path).parent.name} {opt_name} bad responses", len(bad_hits), 0)
    ok3, s3 = fmt_cmp(f"{pathlib.Path(exe_path).parent.name} {opt_name} stderr bytes", stderr_len, 0)
    if not (ok1 and ok2 and ok3):
        raise RuntimeError(f"UCI check failed for {opt_name} on {exe_path}: found={found_decl} bad={bad_hits} stderr={res.stderr!r}")
    return (ok1 and ok2 and ok3), [s1, s2, s3]
