#!/usr/bin/env python3
"""
Job 43 Part M Match & Pooled-Recount Runner (`run_partM.py`):
Runs `M6b` and `M7` on `/tmp/carbon2_job43/bld_bundle8/forge`:
- `M6b` (3,000 games, UHO book lines `2,009,001..2,010,500`):
  * Side A (`B8b_HindsightDepth_on`): `nodes=20000`, `IdeaB8b=true`, `HindsightDepth=true`,
    all other 7 `Idea*` switches (`IdeaK4`, `IdeaS32`, `IdeaB1`, `IdeaS13`, `IdeaS13_Hoist`, `IdeaS10`, `IdeaB8`) explicitly `false`.
  * Side B (`all_off`): `nodes=20000`, all 8 `Idea*` switches + `HindsightDepth` explicitly `false`.
  * Also recounts `M6 + M6b` pooled (`6,000` games / `3,000` pairs, lines `2,007,501..2,010,500`) directly
    from the two committed per-game lists (`job42/M6_games.tsv` and `job43/M6b_games.tsv`) into `M6_M6b_pooled_recount.txt`.
- `M7` (2,000 games, UHO book lines `2,010,501..2,011,500`):
  * Side A (`S13_Hoist_on`): `nodes=20000`, `IdeaS13=true`, `IdeaS13_Hoist=true`,
    all other 6 `Idea*` switches + `HindsightDepth` explicitly `false`.
  * Side B (`all_off`): `nodes=20000`, all 8 `Idea*` switches + `HindsightDepth` explicitly `false`.
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

from j43_lib import (  # noqa: E402
    ALL_EIGHT_IDEA_FALSE,
    EIGHT_SWITCH_NAMES,
    FASTCHESS_BIN,
    JOB42,
    JOB43,
    PC20_OPTIONS,
    UHO_BOOK,
    WORK43,
    fmt_cmp,
    pgn_to_games_tsv,
    recount_games_tsv,
    sha256_file,
    utc_now,
)
from j40_lib import compute_pentanomial_elo  # noqa: E402
from recount_pgn import load_book_slice, normalize_fen4, pts_for_engine1  # noqa: E402

EXE_PATH = WORK43 / "bld_bundle8/forge"
ALL_NINE_FALSE = ALL_EIGHT_IDEA_FALSE + [("HindsightDepth", "false")]

MATCH_SPECS: dict[str, dict] = {
    "M6b": {
        "eng1_name": "B8b_HindsightDepth_on",
        "eng1_nodes": 20000,
        "eng1_switches": [(o, "true" if o == "IdeaB8b" else "false") for o in EIGHT_SWITCH_NAMES] + [("HindsightDepth", "true")],
        "eng2_name": "all_off",
        "eng2_nodes": 20000,
        "eng2_switches": ALL_NINE_FALSE,
        "start_line": 2009001,
        "rounds": 1500,
    },
    "M7": {
        "eng1_name": "S13_Hoist_on",
        "eng1_nodes": 20000,
        "eng1_switches": [(o, "true" if o in ("IdeaS13", "IdeaS13_Hoist") else "false") for o in EIGHT_SWITCH_NAMES] + [("HindsightDepth", "false")],
        "eng2_name": "all_off",
        "eng2_nodes": 20000,
        "eng2_switches": ALL_NINE_FALSE,
        "start_line": 2010501,
        "rounds": 1000,
    },
}


def recount_pooled_m6_m6b(m6_tsv: pathlib.Path, m6b_tsv: pathlib.Path, out_path: pathlib.Path, m6b_was_cut: bool) -> dict:
    engine1 = "B8b_HindsightDepth_on"
    engine2 = "all_off"

    def read_tsv(p: pathlib.Path) -> list[tuple[str, str, str, int, str, str]]:
        out: list[tuple[str, str, str, int, str, str]] = []
        for ln in p.read_text(encoding="utf-8").splitlines():
            if not ln or ln.startswith("#"):
                continue
            w, b, res, plies_s, term, fen = ln.split("\t")
            out.append((w, b, res, int(plies_s), term, fen))
        return out

    r_m6 = read_tsv(m6_tsv)
    r_m6b = read_tsv(m6b_tsv)
    rows = r_m6 + r_m6b

    w_cnt = l_cnt = d_cnt = non_normal = total_plies = 0
    for w, b, res, plies, term, _fen in rows:
        hp = pts_for_engine1(w, b, res, engine1)
        if hp == 2:
            w_cnt += 1
        elif hp == 1:
            d_cnt += 1
        else:
            l_cnt += 1
        if term != "normal":
            non_normal += 1
        total_plies += plies

    ptnml = [0, 0, 0, 0, 0]
    pair_fens4: list[str] = []
    unpaired = 0
    idx = 0
    while idx < len(rows):
        if idx + 1 < len(rows):
            g1, g2 = rows[idx], rows[idx + 1]
            if normalize_fen4(g1[5]) == normalize_fen4(g2[5]) and {g1[0], g2[0]} == {engine1, engine2}:
                hp_sum = pts_for_engine1(g1[0], g1[1], g1[2], engine1) + pts_for_engine1(g2[0], g2[1], g2[2], engine1)
                ptnml[hp_sum] += 1
                pair_fens4.append(normalize_fen4(g1[5]))
                idx += 2
                continue
        unpaired += 1
        idx += 1

    book_slice = load_book_slice(UHO_BOOK, 2007501, 3000)
    book_fens4 = [normalize_fen4(s) for s in book_slice]
    if not m6b_was_cut:
        book_matches = sum(1 for a, b in zip(pair_fens4, book_fens4) if a == b)
        exp_matches = 3000
    else:
        book_set = set(book_fens4)
        book_matches = sum(1 for a in pair_fens4 if a in book_set)
        exp_matches = len(pair_fens4)

    est = compute_pentanomial_elo(ptnml)
    checks: list[str] = []
    all_ok = True
    for lbl, got, exp in [
        ("M6+M6b pooled non-normal terminations", non_normal, 0),
        ("M6+M6b pooled opening FEN pairs matching lines 2007501..2010500", book_matches, exp_matches),
    ]:
        ok, s = fmt_cmp(lbl, got, exp)
        all_ok = all_ok and ok
        checks.append(s)
    if not m6b_was_cut:
        for lbl, got, exp in [
            ("M6+M6b pooled finished games vs target", len(rows), 6000),
            ("M6+M6b pooled finished pairs vs target", sum(ptnml), 3000),
        ]:
            ok, s = fmt_cmp(lbl, got, exp)
            all_ok = all_ok and ok
            checks.append(s)

    status_str = "PARTIAL_M6B_CUT" if m6b_was_cut else "COMPLETE"
    mean_plies = (total_plies / len(rows)) if rows else 0.0
    lines = [
        f"=== M6 + M6b POOLED RECOUNT FROM TWO COMMITTED PER-GAME LISTS ({status_str}) ===",
        f"m6_games_tsv_path: {m6_tsv}",
        f"m6_games_tsv_sha256({m6_tsv}): {sha256_file(m6_tsv)} (games={len(r_m6)})",
        f"m6b_games_tsv_path: {m6b_tsv}",
        f"m6b_games_tsv_sha256({m6b_tsv}): {sha256_file(m6b_tsv)} (games={len(r_m6b)})",
        f"book_slice: {UHO_BOOK} lines 2007501..2010500 (3000 openings = 1500 M6 + 1500 M6b)",
        f"status: {status_str}",
        f"engines: {engine1} vs {engine2}",
        f"pooled_games_finished: {len(rows)} (unpaired={unpaired}, mean_plies={mean_plies:.2f})",
        f"pooled_WLD ({engine1} vs {engine2}): {w_cnt} - {l_cnt} - {d_cnt} (score={est['score']:.6f})",
        f"pooled_pentanomial [LL, LD, WL+DD, WD, WW]: {ptnml} (pairs={sum(ptnml)})",
        f"pooled_Elo: {est['elo']:+.2f} +/- {est['err95']:.2f} (95% CI [{est['ci_low']:+.2f}, {est['ci_high']:+.2f}]; exact [{est['exact_ci_low']:+.2f}, {est['exact_ci_high']:+.2f}])",
        f"pooled_nElo: {est['nelo']:+.2f} +/- {est['nelo_err95']:.2f} | LOS: {est['los_pct']:.2f}%",
        "checks:",
        *checks,
        f"utc_recounted: {utc_now()}",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return {
        "games": len(rows),
        "pairs": sum(ptnml),
        "w": w_cnt,
        "l": l_cnt,
        "d": d_cnt,
        "ptnml": ptnml,
        "elo": float(est["elo"]),
        "err95": float(est["err95"]),
        "all_ok": all_ok,
    }


def run_match(tag: str, cutoff_epoch: float | None = None) -> dict:
    spec = MATCH_SPECS[tag]
    cores = os.cpu_count() or 4
    conc = max(1, cores - 1)

    pgn_tmp = WORK43 / f"tmp_{tag}.pgn"
    if pgn_tmp.exists():
        pgn_tmp.unlink()

    fc_out_path = JOB43 / f"{tag}_fastchess.txt"
    tsv_out_path = JOB43 / f"{tag}_games.tsv"
    rec_out_path = JOB43 / f"{tag}_recount.txt"

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

    print(
        f"[{utc_now()}] Starting {tag}: {spec['rounds'] * 2} games "
        f"(book lines {spec['start_line']}..{spec['start_line'] + spec['rounds'] - 1}, concurrency={conc})",
        flush=True,
    )
    t0 = time.time()
    start_u = utc_now()
    was_cut = False
    with open(fc_out_path, "wb") as out_f:
        proc = subprocess.Popen(cmd, stdout=out_f, stderr=subprocess.STDOUT, cwd=str(WORK43))
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
        f"end_line_target: {spec['start_line'] + spec['rounds'] - 1}",
        f"rounds: {spec['rounds']}",
        f"target_games: {spec['rounds'] * 2}",
        f"concurrency: {conc}",
        f"command: {' '.join(cmd)}",
        f"start_utc: {start_u}",
        f"end_utc: {end_u}",
        f"wall_s: {wall_s:.3f}",
        f"exit_code: {rc}",
        f"was_cut: {was_cut}",
    ]
    (JOB43 / f"{tag}_fastchess.txt.meta").write_text("\n".join(meta_lines) + "\n", encoding="utf-8")

    n_games = pgn_to_games_tsv(pgn_tmp, tsv_out_path, spec["eng1_name"], spec["eng2_name"])
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

    if tag == "M6b":
        inside_m6_ci = 0.27 <= rec["elo"] <= 16.64
        with open(rec_out_path, "a", encoding="utf-8") as rf:
            rf.write(
                f"inside_job42_M6_95ci ([+0.27, +16.64] from +8.46 +/- 8.18): "
                f"observed={rec['elo']:+.2f} in [+0.27, +16.64] is {inside_m6_ci}\n"
            )
        recount_pooled_m6_m6b(
            JOB42 / "M6_games.tsv",
            tsv_out_path,
            JOB43 / "M6_M6b_pooled_recount.txt",
            was_cut,
        )

    print(
        f"[{utc_now()}] {tag} finished in {wall_s:.1f}s "
        f"(status={rec['status']}, games={rec['games']}, elo={rec['elo']:+.2f} +/- {rec['err95']:.2f})",
        flush=True,
    )
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
