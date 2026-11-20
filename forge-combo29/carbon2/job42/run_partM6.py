#!/usr/bin/env python3
"""
Job 42 Part M6 Match Runner (`run_partM6.py`):
Plays the Leaders' Bundle match (`M6`, 3,000 games = 1,500 rounds x 2 games)
on `/tmp/carbon2_job42/bld_bundle7/forge` (Job 41's `bundle_grok7` build verified in Job 42 Step 0):
- Pre-check: verifies Job 40's M0 control (`forge-combo29/carbon2/job41/M0_recount.txt`) passed (`Elo > +20.0`).
- Side A (`B8b_HindsightDepth_on`): `nodes=20000`, `IdeaB8b=true`, `HindsightDepth=true`,
  and all other 6 `Idea*` switches (`IdeaK4`, `IdeaS32`, `IdeaB1`, `IdeaS13`, `IdeaS10`, `IdeaB8`) explicitly `false`.
- Side B (`all_off`): `nodes=20000`, all 7 `Idea*` switches + `HindsightDepth` explicitly `false`.
- Shared `-each`: `proto=uci` plus all 20 `PC20` options (`Threads=1`, `Hash=16`, built-in evaluation, etc.).
- Book: `/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd`, `format=epd`, `order=sequential`, `start=2007501`
  (lines `2,007,501..2,009,000`, none used before), `-rounds 1500`, `-games 2`, `-repeat`, `-concurrency 3`.
- Zero adjudication (`no -draw`, `no -resign`, `no -maxmoves`, `no tablebases`).
- Converts temporary `/tmp/carbon2_job42/tmp_M6.pgn` -> `forge-combo29/carbon2/job42/M6_games.tsv`,
  deletes temporary `.pgn`, and recounts W-L-D, pentanomial, Elo, and 95% CI into `M6_recount.txt`.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j42_lib import (  # noqa: E402
    ALL_SEVEN_FALSE,
    FASTCHESS_BIN,
    JOB41,
    JOB42,
    PC20_OPTIONS,
    SEVEN_SWITCH_NAMES,
    UHO_BOOK,
    WORK42,
    fmt_cmp,
    pgn_to_games_tsv,
    recount_games_tsv,
    sha256_file,
    utc_now,
)

EXE_PATH = WORK42 / "bld_bundle7/forge"
M0_RECOUNT_PATH = JOB41 / "M0_recount.txt"


def verify_m0_passed() -> tuple[bool, float]:
    if not M0_RECOUNT_PATH.exists():
        raise RuntimeError(f"Missing M0 recount file: {M0_RECOUNT_PATH}")
    txt = M0_RECOUNT_PATH.read_text(encoding="utf-8")
    m = re.search(r"recounted_Elo\s*:\s*([+-]?\d+\.\d+)\s*\+/-", txt)
    if not m:
        raise RuntimeError(f"Could not parse M0 Elo from {M0_RECOUNT_PATH}")
    m0_elo = float(m.group(1))
    ok = ("M0 PASS check (FULL Elo > +20.0)" in txt) and ("PASS (True == True)" in txt) and (m0_elo > 20.0)
    return ok, m0_elo


def run_m6(cutoff_epoch: float | None = None) -> dict:
    ok_m0, m0_elo = verify_m0_passed()
    ok_chk, s_chk = fmt_cmp("Pre-check Job 40/41 M0 control passed (Elo > +20.0)", ok_m0, True)
    print(f"{s_chk} (M0 observed Elo = {m0_elo:+.2f} in {M0_RECOUNT_PATH})", flush=True)
    if not ok_chk:
        raise RuntimeError("M0 control did not pass; M6 must not be played.")

    cores = os.cpu_count() or 4
    conc = max(1, cores - 1)

    tag = "M6"
    eng1_name = "B8b_HindsightDepth_on"
    eng2_name = "all_off"
    start_line = 2007501
    rounds = 1500

    eng1_switches = [
        (o, "true" if o == "IdeaB8b" else "false") for o in SEVEN_SWITCH_NAMES
    ] + [("HindsightDepth", "true")]
    eng2_switches = ALL_SEVEN_FALSE + [("HindsightDepth", "false")]

    pgn_tmp = WORK42 / f"tmp_{tag}.pgn"
    if pgn_tmp.exists():
        pgn_tmp.unlink()

    fc_out_path = JOB42 / f"{tag}_fastchess.txt"
    tsv_out_path = JOB42 / f"{tag}_games.tsv"
    rec_out_path = JOB42 / f"{tag}_recount.txt"

    pc20_cli = [f"option.{k}={v}" for k, v in PC20_OPTIONS]
    e1_sw = [f"option.{k}={v}" for k, v in eng1_switches]
    e2_sw = [f"option.{k}={v}" for k, v in eng2_switches]

    cmd = [
        str(FASTCHESS_BIN),
        "-engine",
        f"cmd={EXE_PATH}",
        f"name={eng1_name}",
        "nodes=20000",
        *e1_sw,
        "-engine",
        f"cmd={EXE_PATH}",
        f"name={eng2_name}",
        "nodes=20000",
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
        "25",
    ]

    print(f"[{utc_now()}] Starting {tag}: {rounds * 2} games (book lines {start_line}..{start_line + rounds - 1}, concurrency={conc})", flush=True)
    t0 = time.time()
    start_u = utc_now()
    was_cut = False
    with open(fc_out_path, "wb") as out_f:
        proc = subprocess.Popen(cmd, stdout=out_f, stderr=subprocess.STDOUT, cwd=str(WORK42))
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
        f"m0_precheck_path: {M0_RECOUNT_PATH}",
        f"m0_precheck_sha256({M0_RECOUNT_PATH}): {sha256_file(M0_RECOUNT_PATH)}",
        f"m0_precheck_elo: {m0_elo:+.2f}",
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
        f"concurrency: {conc}",
        f"command: {' '.join(cmd)}",
        f"start_utc: {start_u}",
        f"end_utc: {end_u}",
        f"wall_s: {wall_s:.3f}",
        f"exit_code: {rc}",
        f"was_cut: {was_cut}",
    ]
    (JOB42 / f"{tag}_fastchess.txt.meta").write_text("\n".join(meta_lines) + "\n", encoding="utf-8")

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
    rec["wall_s"] = wall_s
    rec["exit_code"] = rc

    above_max_m3_m4 = rec["elo"] > 13.73
    with open(rec_out_path, "a", encoding="utf-8") as rf:
        rf.write(
            f"comparison_vs_job41_larger_single (max(M3=+8.69, M4=+13.73) = +13.73): "
            f"observed={rec['elo']:+.2f} > +13.73 is {above_max_m3_m4}\n"
        )

    print(
        f"[{utc_now()}] {tag} finished in {wall_s:.1f}s "
        f"(status={rec['status']}, games={rec['games']}, elo={rec['elo']:+.2f} +/- {rec['err95']:.2f})",
        flush=True,
    )
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff-epoch", type=float, default=None)
    args = ap.parse_args()
    run_m6(cutoff_epoch=args.cutoff_epoch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
