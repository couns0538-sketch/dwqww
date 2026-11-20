#!/usr/bin/env python3
"""
Job 40 Part M Match Runner (`run_partM.py`):
Runs `M0`, `M1`, or any `M2_<switch>` (`M2_K4`, `M2_S32`, `M2_B1`, `M2_S13`, `M2_S10`, `M2_B8`)
using official `fastchess`:
- Every engine gets ALL 20 `PC20` options (`option.X=value`, including `Threads=1`, `Hash=16`)
  plus explicit `option.Idea*=true/false` for all 6 bundle switches.
- Fixed nodes (`nodes=20000`, except `M0` side `HALF` with `nodes=10000`).
- ZERO adjudication (`no -draw`, `no -resign`, `no -maxmoves`, `no tablebases`).
- Official `UHO_Lichess_4852_v1.epd`, `format=epd`, `order=sequential`, `start=<line>`, `-rounds <R>`,
  `-games 2`, `-repeat`, `-concurrency 3` (`cores - 1`).
- Enforces optional UTC cutoff timestamp (`--cutoff-epoch`): if reached mid-match, sends `SIGINT`
  to `fastchess`, marks the match `CUT`, converts completed PGN games to `<tag>_games.tsv`,
  runs `recount_games_tsv`, and deletes the temporary PGN in `/tmp/carbon2_job40/`.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j40_lib import (  # noqa: E402
    ALL_SIX_FALSE,
    ALL_SIX_TRUE,
    FASTCHESS_BIN,
    JOB40,
    PC20_OPTIONS,
    SIX_SWITCHES,
    UHO_BOOK,
    WORK40,
    fmt_cmp,
    sha256_file,
    utc_now,
)
from recount_pgn import pgn_to_games_tsv, recount_games_tsv  # noqa: E402

EXE_PATH = WORK40 / "bld_bundle/forge"

MATCH_SPECS: dict[str, dict] = {
    "M0": {
        "eng1_name": "FULL",
        "eng1_nodes": 20000,
        "eng1_switches": ALL_SIX_FALSE,
        "eng2_name": "HALF",
        "eng2_nodes": 10000,
        "eng2_switches": ALL_SIX_FALSE,
        "start_line": 2100001,
        "rounds": 200,
    },
    "M1": {
        "eng1_name": "bundle_on",
        "eng1_nodes": 20000,
        "eng1_switches": ALL_SIX_TRUE,
        "eng2_name": "bundle_off",
        "eng2_nodes": 20000,
        "eng2_switches": ALL_SIX_FALSE,
        "start_line": 2000001,
        "rounds": 1500,
    },
    "M2_K4": {
        "eng1_name": "K4_on",
        "eng1_nodes": 20000,
        "eng1_switches": [(o, "true" if s == "K4" else "false") for s, o in SIX_SWITCHES],
        "eng2_name": "all_off",
        "eng2_nodes": 20000,
        "eng2_switches": ALL_SIX_FALSE,
        "start_line": 2001501,
        "rounds": 500,
    },
    "M2_S32": {
        "eng1_name": "S32_on",
        "eng1_nodes": 20000,
        "eng1_switches": [(o, "true" if s == "S32" else "false") for s, o in SIX_SWITCHES],
        "eng2_name": "all_off",
        "eng2_nodes": 20000,
        "eng2_switches": ALL_SIX_FALSE,
        "start_line": 2002001,
        "rounds": 500,
    },
    "M2_B1": {
        "eng1_name": "B1_on",
        "eng1_nodes": 20000,
        "eng1_switches": [(o, "true" if s == "B1" else "false") for s, o in SIX_SWITCHES],
        "eng2_name": "all_off",
        "eng2_nodes": 20000,
        "eng2_switches": ALL_SIX_FALSE,
        "start_line": 2002501,
        "rounds": 500,
    },
    "M2_S13": {
        "eng1_name": "S13_on",
        "eng1_nodes": 20000,
        "eng1_switches": [(o, "true" if s == "S13" else "false") for s, o in SIX_SWITCHES],
        "eng2_name": "all_off",
        "eng2_nodes": 20000,
        "eng2_switches": ALL_SIX_FALSE,
        "start_line": 2003001,
        "rounds": 500,
    },
    "M2_S10": {
        "eng1_name": "S10_on",
        "eng1_nodes": 20000,
        "eng1_switches": [(o, "true" if s == "S10" else "false") for s, o in SIX_SWITCHES],
        "eng2_name": "all_off",
        "eng2_nodes": 20000,
        "eng2_switches": ALL_SIX_FALSE,
        "start_line": 2003501,
        "rounds": 500,
    },
    "M2_B8": {
        "eng1_name": "B8_on",
        "eng1_nodes": 20000,
        "eng1_switches": [(o, "true" if s == "B8" else "false") for s, o in SIX_SWITCHES],
        "eng2_name": "all_off",
        "eng2_nodes": 20000,
        "eng2_switches": ALL_SIX_FALSE,
        "start_line": 2004001,
        "rounds": 500,
    },
}


def run_match(tag: str, cutoff_epoch: float | None = None) -> dict:
    spec = MATCH_SPECS[tag]
    cores = os.cpu_count() or 4
    conc = max(1, cores - 1)

    pgn_tmp = WORK40 / f"tmp_{tag}.pgn"
    if pgn_tmp.exists():
        pgn_tmp.unlink()

    fc_out_path = JOB40 / f"{tag}_fastchess.txt"
    tsv_out_path = JOB40 / f"{tag}_games.tsv"
    rec_out_path = JOB40 / f"{tag}_recount.txt"

    pc20_cli = [f"option.{k}={v}" for k, v in PC20_OPTIONS]
    e1_sw = [f"option.{k}={v}" for k, v in spec["eng1_switches"]]
    e2_sw = [f"option.{k}={v}" for k, v in spec["eng2_switches"]]

    cmd = [
        str(FASTCHESS_BIN),
        "-engine",
        f"cmd={EXE_PATH}",
        f"name={spec['eng1_name']}",
        f"nodes={spec['eng1_nodes']}",
        *e1_sw,
        "-engine",
        f"cmd={EXE_PATH}",
        f"name={spec['eng2_name']}",
        f"nodes={spec['eng2_nodes']}",
        *e2_sw,
        "-each",
        "proto=uci",
        *pc20_cli,
        "-openings",
        f"file={UHO_BOOK}",
        "format=epd",
        "order=sequential",
        f"start={spec['start_line']}",
        "-rounds",
        str(spec["rounds"]),
        "-games",
        "2",
        "-repeat",
        "-concurrency",
        str(conc),
        "-pgnout",
        f"file={pgn_tmp}",
        "notation=uci",
        "-ratinginterval",
        "25",
    ]

    t0 = time.time()
    start_u = utc_now()
    was_cut = False
    with open(fc_out_path, "wb") as out_f:
        proc = subprocess.Popen(cmd, stdout=out_f, stderr=subprocess.STDOUT, cwd=str(WORK40))
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

    meta_lines = [
        f"match_tag: {tag}",
        f"exe_path: {EXE_PATH}",
        f"exe_sha256({EXE_PATH}): {sha256_file(EXE_PATH)}",
        f"fastchess_path: {FASTCHESS_BIN}",
        f"fastchess_sha256({FASTCHESS_BIN}): {sha256_file(FASTCHESS_BIN)}",
        f"book_path: {UHO_BOOK}",
        f"book_sha256({UHO_BOOK}): {sha256_file(UHO_BOOK)}",
        f"start_line: {spec['start_line']}",
        f"rounds: {spec['rounds']}",
        f"concurrency: {conc}",
        f"command: {' '.join(cmd)}",
        f"start_utc: {start_u}",
        f"end_utc: {end_u}",
        f"wall_s: {wall_s:.3f}",
        f"exit_code: {rc}",
        f"was_cut: {was_cut}",
    ]
    (JOB40 / f"{tag}_fastchess.txt.meta").write_text("\n".join(meta_lines) + "\n", encoding="utf-8")

    n_games = pgn_to_games_tsv(pgn_tmp, tsv_out_path, spec["eng1_name"], spec["eng2_name"])
    # Delete temporary PGN immediately so PGN is NEVER left around or committed
    if pgn_tmp.exists():
        pgn_tmp.unlink()

    if n_games < spec["rounds"] * 2:
        was_cut = True

    rec = recount_games_tsv(
        tag=tag,
        tsv_path=tsv_out_path,
        fc_txt_path=fc_out_path,
        out_recount_path=rec_out_path,
        engine1=spec["eng1_name"],
        engine2=spec["eng2_name"],
        book_path=UHO_BOOK,
        start_line=spec["start_line"],
        target_rounds=spec["rounds"],
        was_cut=was_cut,
    )
    rec["wall_s"] = wall_s
    rec["exit_code"] = rc

    if tag == "M0":
        ok_m0, s_m0 = fmt_cmp("M0 PASS check (FULL Elo > +20.0)", rec["elo"] > 20.0, True)
        with open(rec_out_path, "a", encoding="utf-8") as rf:
            rf.write(f"{s_m0} (observed Elo = {rec['elo']:+.2f} vs threshold +20.00)\n")
        print(f"{s_m0} (observed Elo = {rec['elo']:+.2f} vs threshold +20.00)")
        if not ok_m0:
            raise RuntimeError(f"M0 control FAILED: FULL Elo {rec['elo']:+.2f} <= +20.0")

    print(f"[{utc_now()}] {tag} finished in {wall_s:.1f}s (status={rec['status']}, games={rec['games']})", flush=True)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("matches", nargs="+", choices=list(MATCH_SPECS.keys()))
    ap.add_argument("--cutoff-epoch", type=float, default=None)
    args = ap.parse_args()

    for m in args.matches:
        if args.cutoff_epoch is not None and time.time() >= args.cutoff_epoch:
            print(f"[{utc_now()}] Reached cutoff before starting {m}; skipping {m}.", flush=True)
            break
        rec = run_match(m, cutoff_epoch=args.cutoff_epoch)
        if rec["status"] == "CUT":
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
