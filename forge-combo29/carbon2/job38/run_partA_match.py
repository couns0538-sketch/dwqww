#!/usr/bin/env python3
"""
Job 38 Part A3 Match Runner (`run_partA_match.py`):
Runs the exact 1,106-game `fastchess` match (`nodes=20000`, `Threads=1`, `Hash=16`,
`S14`, openings `O` + `G` = `553` positions x `2` games = `1,106` games,
`concurrency = cores - 1 = 3`) from a single script for:
  1) `s10_variant` (`IdeaS10=true` vs `IdeaS10=false`) -> `fastchess_s10_variant.txt`
  2) seat `031` (`IdeaS10=true` vs `IdeaS10=false`)     -> `fastchess_031.txt`
Writes whole `fastchess` stdout/stderr output for each match into `job38/`.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j38_harness import FENS_G, FENS_O, OUT38, S14_OPTIONS, WORK38, load_fens, sha256_file, utc_now

FC = WORK38 / "fastchess/fastchess"
OPENINGS_553 = WORK38 / "inputs/OG553.epd"


def prepare_openings() -> int:
    o_lines = load_fens(FENS_O)
    g_lines = load_fens(FENS_G)
    assert len(o_lines) == 200, f"Expected 200 O FENs, got {len(o_lines)}"
    assert len(g_lines) == 353, f"Expected 353 G FENs, got {len(g_lines)}"
    all_lines = o_lines + g_lines
    OPENINGS_553.write_text("\n".join(all_lines) + "\n", encoding="utf-8")
    return len(all_lines)


def run_one_match(
    label: str,
    exe_path: pathlib.Path,
    name_on: str,
    name_off: str,
    out_txt: pathlib.Path,
    pgn_tmp: pathlib.Path,
) -> int:
    cores = os.cpu_count() or 4
    conc = max(1, cores - 1)
    if pgn_tmp.exists():
        pgn_tmp.unlink()

    each_opts = [f"option.{k}={v}" for k, v in S14_OPTIONS]
    cmd = [
        str(FC),
        "-engine", f"cmd={exe_path}", f"name={name_on}", "option.IdeaS10=true",
        "-engine", f"cmd={exe_path}", f"name={name_off}", "option.IdeaS10=false",
        "-each", "proto=uci", "nodes=20000", *each_opts,
        "-openings", f"file={OPENINGS_553}", "format=epd", "order=sequential",
        "-rounds", "553",
        "-games", "2",
        "-concurrency", str(conc),
        "-pgnout", f"file={pgn_tmp}", "notation=uci", "nodes=true", "min=true",
        "-ratinginterval", "50",
    ]

    header = [
        f"match_label {label}",
        f"start_utc {utc_now()}",
        f"exe {exe_path}",
        f"exe_sha256 {sha256_file(exe_path)}",
        f"fastchess {FC}",
        f"fastchess_sha256 {sha256_file(FC)}",
        f"openings {OPENINGS_553} (553 positions, sequential, 2 games/round = 1106 games)",
        f"cores {cores} concurrency {conc}",
        f"cmd {' '.join(cmd)}",
        "--- FASTCHESS OUTPUT BEGIN ---",
    ]
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(header) + "\n")
        f.flush()
        proc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, text=True, cwd=str(WORK38))
        f.write("--- FASTCHESS OUTPUT END ---\n")
        f.write(f"match_exit {proc.returncode}\n")
        f.write(f"end_utc {utc_now()}\n")
    return proc.returncode


def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    status_file = WORK38 / "match_done.status"
    if status_file.exists():
        status_file.unlink()
    n_pos = prepare_openings()
    print(f"[{utc_now()}] Prepared {n_pos} openings in {OPENINGS_553} (mode={only})", flush=True)

    rc1 = 0
    if only in ("all", "s10_variant"):
        rc1 = run_one_match(
            "s10_variant_on_vs_off",
            WORK38 / "bld_s10_variant/forge",
            "var_on",
            "var_off",
            OUT38 / "fastchess_s10_variant.txt",
            WORK38 / "match_s10_variant.pgn",
        )
        print(f"[{utc_now()}] s10_variant match finished rc={rc1}", flush=True)

    rc2 = 0
    if only in ("all", "031"):
        rc2 = run_one_match(
            "seat_031_on_vs_off",
            WORK38 / "bld_031/forge",
            "s031_on",
            "s031_off",
            OUT38 / "fastchess_031.txt",
            WORK38 / "match_031.pgn",
        )
        print(f"[{utc_now()}] seat 031 match finished rc={rc2}", flush=True)

    overall = 0 if (rc1 == 0 and rc2 == 0) else 1
    status_file.write_text(f"{overall}\n", encoding="utf-8")
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
