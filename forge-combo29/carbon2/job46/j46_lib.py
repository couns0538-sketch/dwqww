#!/usr/bin/env python3
"""
Job 46 Shared Library (`j46_lib.py`):
- Reuses `bundle9` (`/tmp/carbon2_job44/bld_bundle9/forge`, `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`).
- Defines `S14_EXPLICIT_OPTIONS`: `PC20_OPTIONS` with the 5 PC-loop search switches explicitly set to their
  `r15d` defaults (`CuckooRep=false`, `HistRework=0`, `TtPruneV2=false`, `CorrHistV2=false`, `MateAlphaGuard=false`).
- Provides `run_epd_depth12_custom` which verifies zero `unknown option` / `invalid value` lines on UCI setup
  and writes named-path `.meta` files beside every `.rows.txt`.
- Provides `run_match_generic` for `M13`, `M11`, and `M12` with `cutoff_epoch` support and exact recounting.
"""
from __future__ import annotations

import os
import pathlib
import signal
import subprocess
import sys
import time
from typing import Optional

sys.dont_write_bytecode = True

REPO = pathlib.Path("/agent/repos/dwqww")
JOB46 = REPO / "forge-combo29/carbon2/job46"
JOB45 = REPO / "forge-combo29/carbon2/job45"
JOB44 = REPO / "forge-combo29/carbon2/job44"
JOB43 = REPO / "forge-combo29/carbon2/job43"
JOB42 = REPO / "forge-combo29/carbon2/job42"
JOB41 = REPO / "forge-combo29/carbon2/job41"
JOB40 = REPO / "forge-combo29/carbon2/job40"
JOB39 = REPO / "forge-combo29/carbon2/job39"
JOB36 = REPO / "forge-combo29/carbon2/job36"
JOB35 = REPO / "forge-combo29/carbon2/job35"

WORK46 = pathlib.Path("/tmp/carbon2_job46")
WORK45 = pathlib.Path("/tmp/carbon2_job45")
WORK44 = pathlib.Path("/tmp/carbon2_job44")
WORK40 = pathlib.Path("/tmp/carbon2_job40")
TPL_V3 = pathlib.Path("/tmp/carbon2_job36/tpl_r15d_v3")

EXP_BUNDLE9_SHA = "9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef"
EXP_BASE_V3_SHA = "09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c"
EXP_S10_O_SUM = 8314153
EXP_S10_VS_OFF_ND_DIFF = 17
EXP_S10_VS_OFF_BM_DIFF = 2
EXP_S13_ALONE_O_SUM = 8077984
EXP_S13_VS_OFF_ND_DIFF = 200

sys.path.insert(0, str(JOB44))
sys.path.insert(0, str(JOB43))
sys.path.insert(0, str(JOB42))
sys.path.insert(0, str(JOB41))
sys.path.insert(0, str(JOB40))
sys.path.insert(0, str(JOB39))
sys.path.insert(0, str(JOB36))
sys.path.insert(0, str(JOB35))

from j44_lib import (  # noqa: E402
    ALL_NINE_IDEA_FALSE,
    ALL_TEN_FALSE,
    BUNDLE7_PATCH,
    EXP_B8B_O_SUM,
    EXP_BUNDLE7_SHA,
    EXP_NOPC20_HD_FALSE_BENCH13,
    EXP_NOPC20_HD_TRUE_BENCH13,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_P8_HOIST_SHA,
    EXP_P9_B8_FAST_SHA,
    EXP_PC_S13_HOIST_G_FIRST5,
    EXP_PC_S13_HOIST_G_SUM,
    EXP_PC_S13_HOIST_O_FIRST5,
    EXP_PC_S13_HOIST_O_SUM,
    EXP_SETA_L_NODES,
    EXP_SETA_L_RECORDS,
    EXP_SETA_L_SHA,
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
    UHO_BOOK,
    apply_bundle9_to_fresh_v3,
    build_release_v3,
    diff_breakdown_with_samples,
    fmt_cmp,
    get_id_name,
    load_fens,
    pgn_to_games_tsv,
    read_j39_rows,
    recount_games_tsv,
    run_fresh_bench,
    sha256_file,
    utc_now,
    verify_all_off_numbers,
    verify_uci_option_check,
)

FIVE_S14_OVERRIDES: dict[str, str] = {
    "CuckooRep": "false",
    "HistRework": "0",
    "TtPruneV2": "false",
    "CorrHistV2": "false",
    "MateAlphaGuard": "false",
}

S14_EXPLICIT_OPTIONS: list[tuple[str, str]] = [
    (k, FIVE_S14_OVERRIDES.get(k, v)) for k, v in PC20_OPTIONS
]


def count_row_diffs(
    rows_a: list[tuple[int, int, str, str]],
    rows_b: list[tuple[int, int, str, str]],
) -> dict[str, int]:
    """Read-from-runs comparison of two `(idx, nodes, bestmove, score)` row lists."""
    assert len(rows_a) == len(rows_b), f"Row length mismatch: {len(rows_a)} != {len(rows_b)}"
    equal_all = 0
    nodes_diff = 0
    bestmove_diff = 0
    score_diff = 0
    any_diff = 0
    for a, b in zip(rows_a, rows_b):
        assert a[0] == b[0], f"Position index mismatch: {a[0]} != {b[0]}"
        if a[1:] == b[1:]:
            equal_all += 1
        else:
            any_diff += 1
        if a[1] != b[1]:
            nodes_diff += 1
        if a[2] != b[2]:
            bestmove_diff += 1
        if a[3] != b[3]:
            score_diff += 1
    return {
        "positions": len(rows_a),
        "equal": equal_all,
        "any_diff": any_diff,
        "nodes_diff": nodes_diff,
        "bestmove_diff": bestmove_diff,
        "score_diff": score_diff,
        "sum_a": sum(r[1] for r in rows_a),
        "sum_b": sum(r[1] for r in rows_b),
    }


def verify_options_accepted_cleanly(
    exe_path: str,
    opt_pairs: list[tuple[str, str]],
) -> tuple[bool, list[str]]:
    """
    Sends `uci`, every `setoption name <k> value <v>` in `opt_pairs`, `isready`, `quit`.
    Verifies `readyok` arrives and zero stdout/stderr lines contain `unknown option` or `invalid value`.
    """
    stdin = (
        "uci\n"
        + "".join(f"setoption name {k} value {v}\n" for k, v in opt_pairs)
        + "isready\nquit\n"
    )
    res = subprocess.run([exe_path], input=stdin, text=True, capture_output=True, check=True)
    out_lines = res.stdout.splitlines()
    saw_ready = any(ln.strip() == "readyok" for ln in out_lines)
    bad_hits = [
        ln
        for ln in out_lines + res.stderr.splitlines()
        if ("unknown option" in ln.lower() or "invalid value" in ln.lower())
    ]
    stderr_len = len(res.stderr.encode("utf-8"))
    ok1, s1 = fmt_cmp("options handshake readyok", saw_ready, True)
    ok2, s2 = fmt_cmp("options handshake unknown/invalid lines", len(bad_hits), 0)
    ok3, s3 = fmt_cmp("options handshake stderr bytes", stderr_len, 0)
    return (ok1 and ok2 and ok3), [s1, s2, s3]


def run_epd_depth12_custom(
    exe_path: str,
    set_path: pathlib.Path,
    base_opts: list[tuple[str, str]],
    extra_opts: Optional[list[tuple[str, str]]],
    out_rows: pathlib.Path,
    out_meta: pathlib.Path,
    depth: int = 12,
    cpu_pin: Optional[int] = None,
) -> tuple[list[tuple[int, int, str, str]], list[str]]:
    """
    Runs `set_path` at `depth` under `base_opts + extra_opts`, sending `ucinewgame` + `isready`
    before EVERY search. Captures any `unknown option` / `invalid value` lines during option setup.
    Writes `out_rows` and `out_meta` (with named paths beside sha256s).
    Returns `(rows, bad_option_lines)`.
    """
    fens = load_fens(set_path)
    all_opts = list(base_opts) + (list(extra_opts) if extra_opts else [])
    opt_lines = [f"setoption name {k} value {v}" for k, v in all_opts]
    cmd = [exe_path] if cpu_pin is None else ["taskset", "-c", str(cpu_pin), exe_path]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None

    proc.stdin.write("uci\n")
    proc.stdin.flush()
    id_name = "id name <unknown>"
    while True:
        ln = proc.stdout.readline()
        if ln == "":
            raise RuntimeError(f"EOF waiting for uciok from {exe_path}")
        ln = ln.rstrip("\r\n")
        if ln.startswith("id name "):
            id_name = ln
        elif ln == "uciok":
            break

    proc.stdin.write("".join(o + "\n" for o in opt_lines) + "isready\n")
    proc.stdin.flush()
    bad_opt_lines: list[str] = []
    while True:
        ln = proc.stdout.readline()
        if ln == "":
            raise RuntimeError(f"EOF waiting for readyok after options from {exe_path}")
        ln = ln.rstrip("\r\n")
        if "unknown option" in ln.lower() or "invalid value" in ln.lower():
            bad_opt_lines.append(ln)
        if ln == "readyok":
            break

    rows: list[tuple[int, int, str, str]] = []
    for idx, fen in enumerate(fens, start=1):
        proc.stdin.write(f"ucinewgame\nisready\nposition fen {fen}\ngo depth {depth}\n")
        proc.stdin.flush()
        saw_ready = False
        d_nodes: Optional[int] = None
        d_score: Optional[str] = None
        bestmove: Optional[str] = None
        while True:
            ln = proc.stdout.readline()
            if ln == "":
                raise RuntimeError(f"EOF at position {idx} from {exe_path}")
            ln = ln.rstrip("\r\n")
            if "unknown option" in ln.lower() or "invalid value" in ln.lower():
                bad_opt_lines.append(ln)
            if not saw_ready:
                if ln == "readyok":
                    saw_ready = True
                continue
            if ln.startswith(f"info depth {depth} ") and " nodes " in ln and " score " in ln:
                toks = ln.split()
                ni = toks.index("nodes")
                si = toks.index("score")
                d_nodes = int(toks[ni + 1])
                d_score = f"{toks[si + 1]} {toks[si + 2]}"
            elif ln.startswith("bestmove "):
                bestmove = ln.split()[1]
                break
        if d_nodes is None or d_score is None or bestmove is None:
            raise RuntimeError(
                f"Missing depth-{depth} info or bestmove at pos {idx}: "
                f"nodes={d_nodes} score={d_score} bestmove={bestmove}"
            )
        rows.append((idx, d_nodes, bestmove, d_score))

    proc.stdin.write("quit\n")
    proc.stdin.flush()
    stderr_txt = proc.stderr.read() if proc.stderr else ""
    rc = proc.wait()
    for sln in stderr_txt.splitlines():
        if "unknown option" in sln.lower() or "invalid value" in sln.lower():
            bad_opt_lines.append(sln)
    if rc != 0 or stderr_txt:
        raise RuntimeError(f"Engine exited rc={rc} stderr={stderr_txt!r}")

    total_nodes = sum(r[1] for r in rows)
    header = [
        f"# set={set_path.name} positions={len(rows)} depth={depth} sum_nodes={total_nodes}",
        "position\tnodes\tbestmove\tscore",
    ]
    body = [f"{pos}\t{nd}\t{bm}\t{sc}" for pos, nd, bm, sc in rows]
    out_rows.write_text("\n".join(header + body) + "\n", encoding="utf-8")

    meta = [
        f"exe_path: {exe_path}",
        f"exe_sha256({exe_path}): {sha256_file(exe_path)}",
        f"id_name: {id_name}",
        f"set_path: {set_path}",
        f"set_sha256({set_path}): {sha256_file(set_path)}",
        f"positions: {len(rows)}",
        f"depth: {depth}",
        f"sum_nodes: {total_nodes}",
        f"bad_option_lines_count: {len(bad_opt_lines)}",
        "per_search_reset: ucinewgame + isready",
        "options_sent_begin:",
        *[f"  {o}" for o in opt_lines],
        "options_sent_end",
        f"utc_completed: {utc_now()}",
    ]
    out_meta.write_text("\n".join(meta) + "\n", encoding="utf-8")
    return rows, bad_opt_lines


def run_match_generic(
    *,
    tag: str,
    exe_path: pathlib.Path,
    eng1_name: str,
    eng2_name: str,
    e1_switches: list[tuple[str, str]],
    e2_switches: list[tuple[str, str]],
    each_base_opts: list[tuple[str, str]],
    nodes: int,
    start_line: int,
    rounds: int,
    cutoff_epoch: Optional[float] = None,
    concurrency: Optional[int] = None,
) -> dict[str, object]:
    """
    Runs a `fastchess` match into `JOB46 / {tag}_fastchess.txt`, `{tag}_fastchess.txt.meta`,
    `{tag}_games.tsv`, and `{tag}_recount.txt`. Also scans `{tag}_fastchess.txt` for any
    `unknown option` or `invalid value` line.
    """
    WORK46.mkdir(parents=True, exist_ok=True)
    cores = os.cpu_count() or 4
    conc = concurrency if concurrency is not None else max(1, cores - 1)

    pgn_tmp = WORK46 / f"tmp_{tag}.pgn"
    if pgn_tmp.exists():
        pgn_tmp.unlink()

    fc_out_path = JOB46 / f"{tag}_fastchess.txt"
    meta_out_path = JOB46 / f"{tag}_fastchess.txt.meta"
    tsv_out_path = JOB46 / f"{tag}_games.tsv"
    rec_out_path = JOB46 / f"{tag}_recount.txt"

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
        proc = subprocess.Popen(cmd, stdout=out_f, stderr=subprocess.STDOUT, cwd=str(WORK46))
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
    bad_fc_lines = [
        ln
        for ln in fc_text.splitlines()
        if ("unknown option" in ln.lower() or "invalid value" in ln.lower())
    ]

    n_games = pgn_to_games_tsv(pgn_tmp, tsv_out_path, eng1_name, eng2_name) if pgn_tmp.exists() else 0
    if pgn_tmp.exists():
        pgn_tmp.unlink()
    if n_games < rounds * 2:
        was_cut = True

    meta_lines = [
        f"match_tag: {tag}",
        f"exe_path: {exe_path}",
        f"exe_sha256({exe_path}): {sha256_file(exe_path)}",
        f"id_name: {get_id_name(str(exe_path))}",
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
        f"bad_option_lines_in_fastchess_output: {len(bad_fc_lines)}",
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
    ok_bad, s_bad = fmt_cmp(f"{tag} fastchess unknown/invalid option lines", len(bad_fc_lines), 0)
    with open(rec_out_path, "a", encoding="utf-8") as rf:
        rf.write(s_bad + "\n")
        rf.write(f"tsv_sha256({tsv_out_path}): {sha256_file(tsv_out_path)}\n")
        rf.write(f"fastchess_txt_sha256({fc_out_path}): {sha256_file(fc_out_path)}\n")
    rec["bad_option_lines"] = bad_fc_lines
    rec["ok_bad_options"] = ok_bad
    rec["wall_s"] = wall_s
    print(
        f"[{utc_now()}] {tag} finished in {wall_s:.1f}s "
        f"(status={rec['status']}, games={rec['games']}, elo={rec['elo']:+.2f} +/- {rec['err95']:.2f}, "
        f"bad_opt_lines={len(bad_fc_lines)})",
        flush=True,
    )
    return rec
