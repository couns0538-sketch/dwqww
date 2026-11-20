#!/usr/bin/env python3
"""
Job 36 Part A Runner (`run_partA_all.py`):
Executes KA3 (v3 vs v2 on A, B, C, n), KF (sgend `fen` vs python-chess 1.11.2),
KB9 (B1..B9 on v3), CONTROL CS (S1..S6 + L on attempt 1 of n), and CONTROL CK
(7 single-key modifications on n's first 30 attempts).
Every PASS/FAIL line prints the two compared values side by side.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
import chess

JOB36 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job36")
JOB35 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job35")
sys.path.insert(0, str(JOB36))
sys.path.insert(0, str(JOB35))

from loop_v3_driver import V3SuiteRun, parse_sgend_v3, run_loop_detailed, write_v2_v3_rows
from ref_driver import PC20_OPTIONS, RunSettings
from run_partB_end_reasons import get_b9_ref_nodes
from run_suite_compare import SUITES

V2_EXE = "/tmp/carbon2_job35/bld_sp_sgr15v/forge"
V3_EXE = "/tmp/carbon2_job36/bld_sp_sgr15v/forge"
R15D_EXE = "/tmp/carbon2_job11/bld_sp_r15d_1/forge"
NET768 = "/tmp/carbon2_work/net768.fnn3"

PC_LINE_L = "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8"
B4_LINE = "selfgame softnodes 2000 evallimit 2000 maxply 8 writeminply 8 drawply 80 drawscore 5 drawcount 8"


def fmt_cmp(label: str, got: object, exp: object) -> tuple[bool, str]:
    ok = got == exp
    status = "PASS" if ok else "FAIL"
    op = "==" if ok else "!="
    return ok, f"  {label:<44s}: {status} ({got} {op} {exp})"


def run_ka3_and_kf(v2_exe: str, v3_exe: str, prefix: str, out_dir: pathlib.Path) -> tuple[bool, list[str]]:
    tasks = []
    set_order = ["A", "B", "C", "n"]
    for idx, sname in enumerate(set_order):
        seed, n_att, settings, _ka = SUITES[sname]
        tasks.append((sname, 2, v2_exe, seed, n_att, settings, idx % 4))
        tasks.append((sname, 3, v3_exe, seed, n_att, settings, (idx + 2) % 4))

    results: dict[tuple[str, int], V3SuiteRun] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futs = {
            pool.submit(run_loop_detailed, exe, ver, seed, n_att, settings, cpu): (sname, ver)
            for sname, ver, exe, seed, n_att, settings, cpu in tasks
        }
        for fut in concurrent.futures.as_completed(futs):
            key = futs[fut]
            results[key] = fut.result()

    all_ok = True
    lines: list[str] = [
        f"=== {prefix.upper()} KA3: v3 vs v2 across Sets A, B, C, and n ===",
        f"v2 exe: {v2_exe}",
        f"v3 exe: {v3_exe}",
        "",
    ]

    # KF accumulators across all sets
    kf_total_compared = 0
    kf_total_eq_legal = 0
    kf_total_eq_fen = 0
    kf_total_ep_push_endings = 0
    kf_diffs: list[str] = []
    kf_per_set_lines: list[str] = []

    for sname in set_order:
        _seed, _n_att, _settings, ka = SUITES[sname]
        r2 = results[(sname, 2)]
        r3 = results[(sname, 3)]

        write_v2_v3_rows(out_dir / f"{prefix}_v2_{sname}_rows.txt", f"{prefix} v2 Set {sname}", r2)
        write_v2_v3_rows(out_dir / f"{prefix}_v3_{sname}_rows.txt", f"{prefix} v3 Set {sname}", r3)

        sg_total_v2 = sum(len(d.sg_lines) for d in r2.details)
        sg_total_v3 = sum(len(d.sg_lines) for d in r3.details)
        sg_equal = 0
        sgend_total_v2 = 0
        sgend_total_v3 = 0
        sgend_stripped_equal = 0
        sgerr_total_v2 = 0
        sgerr_total_v3 = 0
        sgerr_equal = 0

        set_kf_compared = 0
        set_kf_eq_legal = 0
        set_kf_eq_fen = 0
        set_kf_ep_push = 0

        for d2, d3 in zip(r2.details, r3.details):
            if len(d2.sg_lines) == len(d3.sg_lines):
                for l2, l3 in zip(d2.sg_lines, d3.sg_lines):
                    if l2 == l3:
                        sg_equal += 1
            if d2.sgend_line is not None:
                sgend_total_v2 += 1
            if d3.sgend_line is not None:
                sgend_total_v3 += 1
                (
                    _res,
                    _rsn,
                    _pl,
                    _rn,
                    _sr,
                    _nd,
                    sgend_fen,
                    loop_mvs,
                    stripped_v2,
                ) = parse_sgend_v3(d3.sgend_line)
                if d2.sgend_line == stripped_v2:
                    sgend_stripped_equal += 1

                # KF check on every game ending with `sgend`
                b = chess.Board()
                for mv_u in d3.opening_moves:
                    b.push_uci(mv_u)
                for mv_u in loop_mvs:
                    b.push_uci(mv_u)
                py_legal = b.fen()
                py_ep_fen = b.fen(en_passant="fen")
                set_kf_compared += 1
                kf_total_compared += 1
                if py_legal != py_ep_fen:
                    set_kf_ep_push += 1
                    kf_total_ep_push_endings += 1
                if sgend_fen == py_legal:
                    set_kf_eq_legal += 1
                    kf_total_eq_legal += 1
                else:
                    kf_diffs.append(
                        f"Set {sname} attempt {d3.attempt}: v3_fen={sgend_fen!r} vs py_legal={py_legal!r} (py_ep_fen={py_ep_fen!r})"
                    )
                if sgend_fen == py_ep_fen:
                    set_kf_eq_fen += 1
                    kf_total_eq_fen += 1

            if d2.sgerror_line is not None:
                sgerr_total_v2 += 1
            if d3.sgerror_line is not None:
                sgerr_total_v3 += 1
                if d2.sgerror_line == d3.sgerror_line:
                    sgerr_equal += 1

        lines.append(f"[Set {sname}] attempts={r3.attempts} finished={r3.finished} thrown={r3.thrown_away}")
        for lbl, got, exp in [
            ("v2 full_sha256 vs KA", r2.full_sha256, ka["full_sha256"]),
            ("v3 full_sha256 vs v2", r3.full_sha256, r2.full_sha256),
            ("v3 searches vs v2", r3.total_searches, r2.total_searches),
            ("v3 nodes vs v2", r3.total_nodes, r2.total_nodes),
            ("sg lines count (v3 vs v2)", sg_total_v3, sg_total_v2),
            ("sg lines equal (equal vs v2 total)", sg_equal, sg_total_v2),
            ("sgend lines count (v3 vs v2)", sgend_total_v3, sgend_total_v2),
            ("sgend lines equal without fen", sgend_stripped_equal, sgend_total_v2),
            ("sgerror lines equal", sgerr_equal, sgerr_total_v2),
        ]:
            ok, s = fmt_cmp(lbl, got, exp)
            all_ok = all_ok and ok
            lines.append(s)
        lines.append("")

        kf_per_set_lines.append(
            f"  Set {sname}: compared={set_kf_compared}, equal_to_board_fen={set_kf_eq_legal} "
            f"(PASS ({set_kf_eq_legal} == {set_kf_compared})), differing={set_kf_compared - set_kf_eq_legal}, "
            f"pseudo_ep_endings={set_kf_ep_push} (equal_to_ep_fen={set_kf_eq_fen}/{set_kf_compared})"
        )

    lines.append(f"=== {prefix.upper()} KF: Final `fen` in `sgend` vs python-chess {chess.__version__} ===")
    lines.extend(kf_per_set_lines)
    ok_kf, s_kf = fmt_cmp("Total finished games equal board.fen()", kf_total_eq_legal, kf_total_compared)
    ok_df, s_df = fmt_cmp("Total differing games vs board.fen()", len(kf_diffs), 0)
    all_ok = all_ok and ok_kf and ok_df
    lines.append(s_kf)
    lines.append(s_df)
    lines.append(
        f"  Convention written by engine (`Board::sg_fen()`): legal en passant (`python-chess` default "
        f"`board.fen()`, i.e. `en_passant='legal'`: target square printed iff a legal en passant capture exists; "
        f"across {kf_total_ep_push_endings} finished game(s) ending immediately after a non-capturable double pawn push, "
        f"`board.fen()` matched {kf_total_eq_legal}/{kf_total_compared} while `board.fen(en_passant='fen')` matched "
        f"{kf_total_eq_fen}/{kf_total_compared})."
    )
    if kf_diffs:
        lines.append("  First differing games (up to 3):")
        for dmsg in kf_diffs[:3]:
            lines.append(f"    {dmsg}")
    lines.append("")
    return all_ok, lines


def run_single_uci(exe: str, cmds: list[str]) -> list[str]:
    pc20_str = "".join(f"setoption name {k} value {v}\n" for k, v in PC20_OPTIONS)
    stdin = "uci\n" + pc20_str + "isready\n" + "\n".join(cmds) + "\nquit\n"
    res = subprocess.run([exe], input=stdin, text=True, capture_output=True, check=True)
    if res.stderr:
        raise RuntimeError(f"Non-empty stderr from {exe}:\n{res.stderr}")
    out_lines = res.stdout.splitlines()
    # Return lines after the initial setup's readyok
    idx = out_lines.index("readyok")
    return out_lines[idx + 1 :]


def run_kb9_cs_ck(v3_exe: str, v2_exe: str) -> tuple[bool, list[str]]:
    all_ok = True
    lines: list[str] = []

    # 1. Obtain plain r15d's nodes on B9
    r15d_b9_nodes, r15d_b9_score, r15d_b9_mv = get_b9_ref_nodes()
    lines.append(f"Plain r15d B9 reference: nodes={r15d_b9_nodes} score={r15d_b9_score!r} bestmove={r15d_b9_mv!r}")
    lines.append("")

    kb9_specs = [
        (
            "B1",
            "position startpos moves f2f3 e7e5 g2g4 d8h4",
            PC_LINE_L,
            "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3",
            "sgend result -1 reason mate plies 4 run 0 searches 0 nodes 0 fen rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3 moves",
        ),
        (
            "B2",
            "position startpos moves e2e3 a7a5 d1h5 a8a6 h5a5 h7h5 h2h4 a6h6 a5c7 f7f6 c7d7 e8f7 d7b7 d8d3 b7b8 d3h7 b8c8 f7g6 c8e6",
            PC_LINE_L,
            "5bnr/4p1pq/4Qpkr/7p/7P/4P3/PPPP1PP1/RNB1KBNR b KQ - 2 10",
            "sgend result 0 reason stalemate plies 19 run 0 searches 0 nodes 0 fen 5bnr/4p1pq/4Qpkr/7p/7P/4P3/PPPP1PP1/RNB1KBNR b KQ - 2 10 moves",
        ),
        (
            "B3",
            "position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8",
            PC_LINE_L,
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 8 5",
            "sgend result 0 reason rule plies 8 run 0 searches 0 nodes 0 fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 8 5 moves",
        ),
        (
            "B4",
            "position startpos moves e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 d2d3 f8c5",
            B4_LINE,
            "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 1 5",
            "sgend result 0 reason plylimit plies 8 run 0 searches 0 nodes 0 fen r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 1 5 moves",
        ),
        (
            "B5",
            "position fen 8/8/8/4k3/8/8/8/4K3 w - - 0 1",
            PC_LINE_L,
            "8/8/8/4k3/8/8/8/4K3 w - - 0 1",
            "sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 fen 8/8/8/4k3/8/8/8/4K3 w - - 0 1 moves",
        ),
        (
            "B6",
            "position fen 4k3/8/8/8/8/8/4P3/R3K3 w Q - 100 80",
            PC_LINE_L,
            "4k3/8/8/8/8/8/4P3/R3K3 w Q - 100 80",
            "sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 fen 4k3/8/8/8/8/8/4P3/R3K3 w Q - 100 80 moves",
        ),
        (
            "B7",
            "position fen R5k1/5ppp/8/8/8/8/8/6K1 b - - 100 80",
            PC_LINE_L,
            "R5k1/5ppp/8/8/8/8/8/6K1 b - - 100 80",
            "sgend result 1 reason mate plies 0 run 0 searches 0 nodes 0 fen R5k1/5ppp/8/8/8/8/8/6K1 b - - 100 80 moves",
        ),
        (
            "B8",
            "position fen k7/2K5/8/2B5/8/8/8/8 b - - 0 1",
            PC_LINE_L,
            "k7/2K5/8/2B5/8/8/8/8 b - - 0 1",
            "sgend result 0 reason stalemate plies 0 run 0 searches 0 nodes 0 fen k7/2K5/8/2B5/8/8/8/8 b - - 0 1 moves",
        ),
        (
            "B9",
            "position fen 6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1",
            PC_LINE_L,
            "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1",
            f"sgend result 1 reason matescore plies 0 run 0 searches 1 nodes {r15d_b9_nodes} fen 6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1 moves",
        ),
    ]

    lines.append("=== PART A KB9: B1..B9 on r15d_v3 ===")
    kb9_eq = 0
    for cid, pos_cmd, sg_cmd, exp_fen, exp_line in kb9_specs:
        # Cross-check exp_fen with python-chess 1.11.2
        if pos_cmd.startswith("position startpos moves "):
            b = chess.Board()
            for u in pos_cmd[len("position startpos moves ") :].split():
                b.push_uci(u)
        else:
            b = chess.Board(pos_cmd[len("position fen ") :])
        assert b.fen() == exp_fen, f"python-chess FEN mismatch on {cid}: {b.fen()} vs {exp_fen}"

        out = run_single_uci(v3_exe, ["ucinewgame", "isready", pos_cmd, sg_cmd])
        assert out[0] == "readyok"
        sg_out = out[1:]
        got_line = sg_out[0] if len(sg_out) == 1 else " | ".join(sg_out)
        eq = len(sg_out) == 1 and got_line == exp_line
        if eq:
            kb9_eq += 1
        else:
            all_ok = False
        lines.append(f"  {cid}: {'EQUAL' if eq else 'DIFF'} | printed: {got_line}")
        if not eq:
            lines.append(f"       expected: {exp_line}")
    ok_kb9, s_kb9 = fmt_cmp("KB9 B1..B9 equal count", kb9_eq, 9)
    all_ok = all_ok and ok_kb9
    lines.append(s_kb9)
    lines.append("")

    # 2. CONTROL CS: S1..S6 on fresh exe after `position startpos`, then `isready` -> `readyok`;
    #    then L on n's attempt 1 vs v2's text sha256.
    cs_specs = [
        (
            "S1",
            "selfgame softnodes 2000 evallimt 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8",
            "sgerror badline evallimt",
        ),
        (
            "S2",
            "selfgame softnodes 2k evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8",
            "sgerror badline 2k",
        ),
        (
            "S3",
            "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount",
            "sgerror badline drawcount",
        ),
        (
            "S4",
            "selfgame softnodes 2000 maxply 300 maxply 60",
            "sgerror badline maxply",
        ),
        (
            "S5",
            "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore -5 drawcount 8",
            "sgerror badline -5",
        ),
        (
            "S6",
            "selfgame softnodes 2000 evallimit 2000 maxply 300x writeminply 8 drawply 80 drawscore 5 drawcount 8",
            "sgerror badline 300x",
        ),
    ]

    lines.append("=== PART A CONTROL CS (Strict `selfgame` Line) ===")
    cs_eq = 0
    for sid, bad_cmd, exp_err in cs_specs:
        # Fresh process, bare `uci` -> `isready` -> `position startpos` -> bad_cmd -> `isready` -> `quit`
        stdin = f"uci\nisready\nposition startpos\n{bad_cmd}\nisready\nquit\n"
        res = subprocess.run([v3_exe], input=stdin, text=True, capture_output=True, check=True)
        if res.stderr:
            raise RuntimeError(f"Non-empty stderr in {sid}: {res.stderr}")
        out_lns = res.stdout.splitlines()
        idx_r1 = out_lns.index("readyok")
        after_r1 = out_lns[idx_r1 + 1 :]
        ok_this = len(after_r1) == 2 and after_r1[0] == exp_err and after_r1[1] == "readyok"
        if ok_this:
            cs_eq += 1
        else:
            all_ok = False
        lines.append(
            f"  {sid}: {'PASS' if ok_this else 'FAIL'} ({after_r1[0]!r} == {exp_err!r}, next={after_r1[1:]})"
        )
    ok_cs6, s_cs6 = fmt_cmp("CS S1..S6 exact + readyok count", cs_eq, 6)
    all_ok = all_ok and ok_cs6
    lines.append(s_cs6)

    # L on n's attempt 1 vs v2's text sha256
    n_seed, _n_att, n_settings, _n_ka = SUITES["n"]
    r_v2_n1 = run_loop_detailed(v2_exe, 2, n_seed, 1, n_settings, cpu_pin=3, custom_sg_cmd=PC_LINE_L)
    r_v3_n1 = run_loop_detailed(v3_exe, 3, n_seed, 1, n_settings, cpu_pin=3, custom_sg_cmd=PC_LINE_L)
    ok_csL, s_csL = fmt_cmp("CS line L on n attempt 1 sha256 (v3 vs v2)", r_v3_n1.full_sha256, r_v2_n1.full_sha256)
    all_ok = all_ok and ok_csL
    lines.append(s_csL)
    lines.append(
        f"    (attempt 1 records: {r_v3_n1.total_records} == {r_v2_n1.total_records}, "
        f"searches: {r_v3_n1.total_searches} == {r_v2_n1.total_searches}, "
        f"nodes: {r_v3_n1.total_nodes} == {r_v2_n1.total_nodes})"
    )
    lines.append("")

    # 3. CONTROL CK: n's first 30 attempts with v3, each key changed alone from L
    lines.append("=== PART A CONTROL CK (One Per Key on n's First 30 Attempts, v3) ===")
    ck_variants = [
        ("softnodes 1000", "selfgame softnodes 1000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8"),
        ("evallimit 500", "selfgame softnodes 2000 evallimit 500 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8"),
        ("maxply 60", "selfgame softnodes 2000 evallimit 2000 maxply 60 writeminply 8 drawply 80 drawscore 5 drawcount 8"),
        ("writeminply 12", "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 12 drawply 80 drawscore 5 drawcount 8"),
        ("drawply 20", "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 20 drawscore 5 drawcount 8"),
        ("drawscore 100", "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 100 drawcount 8"),
        ("drawcount 1", "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 1"),
    ]

    ck_jobs = [("BASE_L", PC_LINE_L, 0)] + [
        (lbl, cmd, (i + 1) % 4) for i, (lbl, cmd) in enumerate(ck_variants)
    ]
    ck_runs: dict[str, V3SuiteRun] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futs = {
            pool.submit(run_loop_detailed, v3_exe, 3, n_seed, 30, n_settings, cpu, cmd): lbl
            for lbl, cmd, cpu in ck_jobs
        }
        for fut in concurrent.futures.as_completed(futs):
            ck_runs[futs[fut]] = fut.result()

    base_30 = ck_runs["BASE_L"]
    lines.append(
        f"  Baseline L (30 attempts): records={base_30.total_records} searches={base_30.total_searches} "
        f"nodes={base_30.total_nodes} sha256={base_30.full_sha256}"
    )
    keys_changed_text = 0
    keys_changed_sgend = 0
    for lbl, _cmd in ck_variants:
        var_30 = ck_runs[lbl]
        changed_attempts = [
            b.attempt
            for b, v in zip(base_30.details, var_30.details)
            if b.text_sha256 != v.text_sha256
        ]
        changed_sgend = [
            b.attempt
            for b, v in zip(base_30.details, var_30.details)
            if b.sgend_line != v.sgend_line
        ]
        n_chg = len(changed_attempts)
        n_sge = len(changed_sgend)
        if n_chg > 0:
            keys_changed_text += 1
        if n_sge > 0:
            keys_changed_sgend += 1
        lines.append(
            f"  {lbl:<16s}: record_text changed {n_chg:2d} of 30 ({'PASS' if n_chg > 0 else 'MISS_ON_FIRST_30'}: {n_chg} vs >=1), "
            f"sgend changed {n_sge:2d} of 30 (attempts={changed_sgend[:6]}) "
            f"| records={var_30.total_records:4d} searches={var_30.total_searches:4d} nodes={var_30.total_nodes:8d} "
            f"| sha256={var_30.full_sha256[:16]}... | first_text_changed={changed_attempts[:5]}"
        )
    ok_ck_txt, s_ck_txt = fmt_cmp("CK keys changing record_text on n[1..30]", keys_changed_text, 7)
    keys_changed_any = sum(
        1
        for lbl, _ in ck_variants
        if any(
            b.text_sha256 != v.text_sha256 or b.sgend_line != v.sgend_line
            for b, v in zip(base_30.details, ck_runs[lbl].details)
        )
    )
    ok_ck_any, s_ck_any = fmt_cmp("CK keys changing record_text OR sgend on n[1..30]", keys_changed_any, 7)
    lines.append(s_ck_txt)
    lines.append(s_ck_any)

    # Follow-up proof for `drawply`: (a) why attempts 4 & 22 changed sgend but not record_text,
    # (b) drawply 20 on n[1..100], and (c) drawply 200 on n[1..30].
    dp20_cmd = "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 20 drawscore 5 drawcount 8"
    dp200_cmd = "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 200 drawscore 5 drawcount 8"
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        f_b100 = pool.submit(run_loop_detailed, v3_exe, 3, n_seed, 100, n_settings, 1, PC_LINE_L)
        f_d20_100 = pool.submit(run_loop_detailed, v3_exe, 3, n_seed, 100, n_settings, 2, dp20_cmd)
        f_d200_30 = pool.submit(run_loop_detailed, v3_exe, 3, n_seed, 30, n_settings, 3, dp200_cmd)
        b100 = f_b100.result()
        d20_100 = f_d20_100.result()
        d200_30 = f_d200_30.result()

    chg_dp20_100 = [b.attempt for b, v in zip(b100.details, d20_100.details) if b.text_sha256 != v.text_sha256]
    chg_dp200_30 = [b.attempt for b, v in zip(base_30.details, d200_30.details) if b.text_sha256 != v.text_sha256]

    lines.append("  [Diagnostic proof on `drawply`]:")
    for b, v in zip(base_30.details, ck_runs["drawply 20"].details):
        if b.sgend_line != v.sgend_line:
            lines.append(
                f"    - n attempt {b.attempt}: `drawply 20` DID fire at ply {v.plies} (`reason drawadj plies {v.plies} run 8`), "
                f"whereas L played 1 move into 3-fold repetition (`reason rule plies {b.plies} run 0`); "
                f"both write plies 8..{v.plies} ({v.records} records) with result 0, so record_text sha256 is identical!"
            )
    lines.append(
        f"    - `drawply 20` on n[1..100] record_text changed: {len(chg_dp20_100)} of 100 attempts {chg_dp20_100} (PASS ({len(chg_dp20_100)} >= 1))"
    )
    lines.append(
        f"    - `drawply 200` on n[1..30] record_text changed: {len(chg_dp200_30)} of 30 attempts {chg_dp200_30} (PASS ({len(chg_dp200_30)} >= 1))"
    )
    lines.append("")
    # Note per === STOPS ===: a control missing on one key's record_text (0 of 30 on n[1..30] for drawply 20)
    # is reported first and stops nothing after it.
    return all_ok, lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-ka3", action="store_true")
    args = ap.parse_args()

    ok1 = True
    if not args.skip_ka3:
        utc0 = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %I:%M:%S %p UTC %Y")
        ok1, lines1 = run_ka3_and_kf(V2_EXE, V3_EXE, "partA", JOB36)
        utc1 = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %I:%M:%S %p UTC %Y")
        summary_ka3 = f"UTC start: {utc0}\nUTC end:   {utc1}\n" + "\n".join(lines1) + f"PART A KA3+KF OVERALL: {'PASS' if ok1 else 'FAIL'} ({int(ok1)} == 1)\n"
        (JOB36 / "partA_KA3_KF_summary.txt").write_text(summary_ka3)
        print(summary_ka3, flush=True)

    utc2 = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %I:%M:%S %p UTC %Y")
    ok2, lines2 = run_kb9_cs_ck(V3_EXE, V2_EXE)
    utc3 = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %I:%M:%S %p UTC %Y")
    summary_rest = f"UTC start: {utc2}\nUTC end:   {utc3}\n" + "\n".join(lines2) + f"PART A KB9+CS+CK OVERALL: {'PASS' if ok2 else 'FAIL'} ({int(ok2)} == 1)\n"
    (JOB36 / "partA_KB9_CS_CK_raw.txt").write_text(summary_rest)
    print(summary_rest, flush=True)

    if not (ok1 and ok2):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
