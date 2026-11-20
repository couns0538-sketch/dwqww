#!/usr/bin/env python3
"""
Job 45 Part M10 (`run_partM10.py`): `IdeaB8b` ON TOP OF `HindsightDepth`.
Plays 4,000 games (2,000 pairs) on `/tmp/carbon2_job45/bld_bundle8/forge`, `PC20`, built-in evaluation,
`nodes=20000`, UHO book lines `2,013,501..2,015,500`:
  - Side A (`B8b_HindsightDepth_on`): `nodes=20000`, `IdeaB8b=true`, `HindsightDepth=true`,
    all other 7 `Idea*` switches (`IdeaK4`, `IdeaS32`, `IdeaB1`, `IdeaS13`, `IdeaS13_Hoist`, `IdeaS10`, `IdeaB8`) explicitly `false`.
  - Side B (`only_HindsightDepth`): `nodes=20000`, `IdeaB8b=false`, `HindsightDepth=true`,
    all other 7 `Idea*` switches explicitly `false`.
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

from j45_lib import (  # noqa: E402
    ALL_EIGHT_IDEA_FALSE,
    EIGHT_SWITCH_NAMES,
    FASTCHESS_BIN,
    JOB45,
    PC20_OPTIONS,
    UHO_BOOK,
    WORK45,
    pgn_to_games_tsv,
    recount_games_tsv,
    sha256_file,
    utc_now,
)

EXE_PATH = WORK45 / "bld_bundle8/forge"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff-epoch", type=float, default=None)
    args = ap.parse_args()

    tag = "M10"
    eng1_name = "B8b_HindsightDepth_on"
    eng2_name = "only_HindsightDepth"
    start_line = 2013501
    rounds = 2000
    nodes = 20000

    e1_switches = [(o, "true" if o == "IdeaB8b" else "false") for o in EIGHT_SWITCH_NAMES] + [("HindsightDepth", "true")]
    e2_switches = ALL_EIGHT_IDEA_FALSE + [("HindsightDepth", "true")]

    cores = os.cpu_count() or 4
    conc = max(1, cores - 1)

    pgn_tmp = WORK45 / f"tmp_{tag}.pgn"
    if pgn_tmp.exists():
        pgn_tmp.unlink()

    fc_out_path = JOB45 / f"{tag}_fastchess.txt"
    tsv_out_path = JOB45 / f"{tag}_games.tsv"
    rec_out_path = JOB45 / f"{tag}_recount.txt"

    pc20_cli = [f"option.{k}={v}" for k, v in PC20_OPTIONS]
    e1_sw = [f"option.{k}={v}" for k, v in e1_switches]
    e2_sw = [f"option.{k}={v}" for k, v in e2_switches]

    cmd = [
        str(FASTCHESS_BIN),
        "-engine",
        f"cmd={EXE_PATH}",
        f"name={eng1_name}",
        f"nodes={nodes}",
        *e1_sw,
        "-engine",
        f"cmd={EXE_PATH}",
        f"name={eng2_name}",
        f"nodes={nodes}",
        *e2_sw,
        "-each",
        "proto=uci",
        *pc20_cli,
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
        "50",
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
        proc = subprocess.Popen(cmd, stdout=out_f, stderr=subprocess.STDOUT, cwd=str(WORK45))
        while True:
            rc = proc.poll()
            if rc is not None:
                break
            if args.cutoff_epoch is not None and time.time() >= args.cutoff_epoch:
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
        f"start_line: {start_line}",
        f"end_line_target: {start_line + rounds - 1}",
        f"rounds: {rounds}",
        f"target_games: {rounds * 2}",
        f"nodes_per_move: {nodes}",
        f"concurrency: {conc}",
        f"command: {' '.join(cmd)}",
        f"start_utc: {start_u}",
        f"end_utc: {end_u}",
        f"wall_s: {wall_s:.3f}",
        f"exit_code: {rc}",
        f"was_cut: {was_cut}",
    ]
    (JOB45 / f"{tag}_fastchess.txt.meta").write_text("\n".join(meta_lines) + "\n", encoding="utf-8")

    n_games = pgn_to_games_tsv(pgn_tmp, tsv_out_path, eng1_name, eng2_name)
    if pgn_tmp.exists():
        pgn_tmp.unlink()
    if n_games < rounds * 2:
        was_cut = True

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
    print(
        f"[{utc_now()}] {tag} finished in {wall_s:.1f}s "
        f"(status={rec['status']}, games={rec['games']}, elo={rec['elo']:+.2f} +/- {rec['err95']:.2f})",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
