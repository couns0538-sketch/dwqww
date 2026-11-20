#!/usr/bin/env python3
"""
Job 33 Part B — KB1 & Control CR:
Compare `sgstate` after EVERY move in >= 300,000 seeded random legal move positions
(from startpos and from 24 positions with 3 to 6 pieces) against python-chess 1.11.2,
and verify Control CR fires against both fen(en_passant="fen") and is_repetition(2).
"""
from __future__ import annotations

import datetime
import pathlib
import random
import subprocess
import time

import chess

FEW_PIECE_FENS: list[str] = [
    "8/8/4k3/8/8/3KN3/4P3/8 w - - 0 1",
    "8/8/4k3/3p4/8/3KB3/8/8 b - - 0 1",
    "8/3k4/8/2b5/5B2/8/3K4/8 w - - 0 1",
    "8/3k4/8/3b4/5B2/8/3K4/8 w - - 0 1",
    "8/8/3k4/8/8/3K4/1B1B4/8 w - - 0 1",
    "8/8/3k4/8/8/3K4/1B2B3/8 w - - 0 1",
    "8/8/3k4/8/8/3K4/1N1N4/8 w - - 0 1",
    "8/3k1q2/8/8/8/3KN3/8/8 w - - 0 1",
    "6k1/8/6K1/8/8/8/7Q/8 w - - 0 1",
    "7k/5K2/8/8/8/8/6Q1/8 w - - 0 1",
    "7k/5K2/8/8/8/8/6R1/8 w - - 0 1",
    "8/3k4/3r4/8/8/3R4/3K4/8 w - - 0 1",
    "8/3k1n2/8/8/8/3K1N2/8/8 w - - 0 1",
    "8/3k1b2/8/8/8/3K1N2/8/8 w - - 0 1",
    "8/1p2k3/8/2P5/8/4K3/8/8 b - - 0 1",
    "8/1p6/8/k1P4R/8/4K3/8/8 b - - 0 1",
    "7b/4p3/8/3P4/8/1K6/8/6k1 b - - 0 1",
    "4k3/3p1p2/8/4P3/8/8/8/4K3 b - - 0 1",
    "r3k3/8/8/8/8/8/8/4K2R w Kq - 0 1",
    "4k2r/8/8/8/8/8/8/R3K3 b Qk - 0 1",
    "8/2p1k3/8/8/3p4/8/2P1P3/4K3 w - - 0 1",
    "6k1/5p2/6p1/8/8/8/6Q1/6K1 w - - 0 1",
    "1k6/1p6/1K6/8/8/8/1R6/8 w - - 0 1",
    "8/8/1k1q4/8/8/2K1B3/2P5/8 b - - 0 1",
    "7k/8/4Q1K1/8/8/8/8/8 w - - 0 1",
    "k7/8/1K6/2Q5/8/8/8/8 w - - 0 1",
    "8/8/8/8/4k3/8/6b1/6K1 w - - 0 1",
    "8/8/8/4k3/8/4K3/5n2/8 w - - 0 1",
]


def parse_sgstate(line: str) -> tuple[int, int, int, int, int, str]:
    # Format: sgstate legal <0|1> check <0|1> material <0|1> clock <clock> rep3 <0|1> fen <FEN>
    parts = line.split(" ", 12)
    if (
        len(parts) != 13
        or parts[0] != "sgstate"
        or parts[1] != "legal"
        or parts[3] != "check"
        or parts[5] != "material"
        or parts[7] != "clock"
        or parts[9] != "rep3"
        or parts[11] != "fen"
    ):
        raise ValueError(f"Malformed sgstate line: {line!r}")
    return (
        int(parts[2]),
        int(parts[4]),
        int(parts[6]),
        int(parts[8]),
        int(parts[10]),
        parts[12],
    )


def run_kb1(exe_path: str, seed: str = "carbon2-job33-kb1", target_positions: int = 500_000) -> dict:
    for fen in FEW_PIECE_FENS:
        b = chess.Board(fen)
        pc = len(b.piece_map())
        assert b.is_valid() and 3 <= pc <= 6, f"Invalid 3..6 piece FEN {fen} (pieces={pc})"

    rng = random.Random(seed)
    t0 = time.perf_counter()

    proc = subprocess.Popen(
        ["taskset", "-c", "3", exe_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    proc.stdin.write("uci\nisready\n")
    proc.stdin.flush()
    while True:
        ln = proc.stdout.readline().rstrip("\r\n")
        if ln == "readyok":
            break

    total_positions = 0
    startpos_games = 0
    fewpiece_games = 0
    startpos_positions = 0
    fewpiece_positions = 0
    diffs = 0
    first_diff_msg = ""

    seen_material1 = 0
    seen_rep3 = 0
    seen_clock100 = 0
    seen_mates = 0
    seen_stalemates = 0
    seen_ep_in_fen = 0
    seen_double_push_dash = 0

    # Control CR counters
    cr_ep_fen_diffs = 0
    cr_ep_fen_first = ""
    cr_rep2_diffs = 0
    cr_rep2_first = ""

    seq_idx = 0
    while total_positions < target_positions:
        # Alternate: 2 startpos sequences, 2 few-piece sequences
        use_startpos = (seq_idx % 4) < 2
        if use_startpos:
            root_spec = "startpos"
            board = chess.Board()
            max_len = 220
            startpos_games += 1
        else:
            fen = FEW_PIECE_FENS[(seq_idx // 2) % len(FEW_PIECE_FENS)]
            root_spec = f"fen {fen}"
            board = chess.Board(fen)
            max_len = 160
            fewpiece_games += 1
        seq_idx += 1

        moves_uci: list[str] = []
        expected_list: list[tuple[int, int, int, int, int, str, bool, str, int]] = []
        cmd_lines: list[str] = ["ucinewgame\n"]

        for _ in range(max_len):
            legal_mvs = list(board.legal_moves)
            if not legal_mvs:
                break
            mv = rng.choice(legal_mvs)
            piece = board.piece_at(mv.from_square)
            just_dp = (
                piece is not None
                and piece.piece_type == chess.PAWN
                and abs(chess.square_rank(mv.to_square) - chess.square_rank(mv.from_square)) == 2
            )
            board.push(mv)
            moves_uci.append(mv.uci())

            exp_legal = 1 if any(board.legal_moves) else 0
            exp_check = 1 if board.is_check() else 0
            exp_mat = 1 if board.is_insufficient_material() else 0
            exp_clock = board.halfmove_clock
            exp_rep3 = 1 if board.is_repetition(3) else 0
            exp_fen = board.fen()
            cr_fen_raw = board.fen(en_passant="fen")
            cr_rep2_val = 1 if board.is_repetition(2) else 0

            expected_list.append(
                (exp_legal, exp_check, exp_mat, exp_clock, exp_rep3, exp_fen, just_dp, cr_fen_raw, cr_rep2_val)
            )
            cmd_lines.append(f"position {root_spec} moves {' '.join(moves_uci)}\nsgstate\n")

            if exp_legal == 0:
                break

        if not expected_list:
            continue

        proc.stdin.write("".join(cmd_lines))
        proc.stdin.flush()

        for ply_i, exp in enumerate(expected_list, start=1):
            raw = proc.stdout.readline()
            if not raw:
                raise RuntimeError("EOF while reading sgstate")
            got = parse_sgstate(raw.rstrip("\r\n"))
            exp_tup = exp[:6]
            just_dp, cr_fen_raw, cr_rep2_val = exp[6], exp[7], exp[8]

            if got != exp_tup:
                diffs += 1
                if not first_diff_msg:
                    first_diff_msg = f"seq={seq_idx} root={root_spec} ply={ply_i} got={got} exp={exp_tup}"

            g_legal, g_check, g_mat, g_clock, g_rep3, g_fen = got
            if g_mat == 1:
                seen_material1 += 1
            if g_rep3 == 1:
                seen_rep3 += 1
            if g_clock >= 100:
                seen_clock100 += 1
            if g_legal == 0 and g_check == 1:
                seen_mates += 1
            if g_legal == 0 and g_check == 0:
                seen_stalemates += 1
            ep_field = g_fen.split(" ")[3]
            if ep_field != "-":
                seen_ep_in_fen += 1
            elif just_dp:
                seen_double_push_dash += 1

            if g_fen != cr_fen_raw:
                cr_ep_fen_diffs += 1
                if not cr_ep_fen_first:
                    cr_ep_fen_first = f"seq={seq_idx} ply={ply_i} sg_fen='{g_fen}' vs raw_ep_fen='{cr_fen_raw}'"
            if g_rep3 != cr_rep2_val:
                cr_rep2_diffs += 1
                if not cr_rep2_first:
                    cr_rep2_first = f"seq={seq_idx} ply={ply_i} sg_rep3={g_rep3} vs is_repetition(2)={cr_rep2_val}"

        n_pos = len(expected_list)
        total_positions += n_pos
        if use_startpos:
            startpos_positions += n_pos
        else:
            fewpiece_positions += n_pos

    proc.stdin.write("quit\n")
    proc.stdin.flush()
    stderr_txt = proc.stderr.read() if proc.stderr else ""
    rc = proc.wait()
    if rc != 0 or stderr_txt:
        raise RuntimeError(f"Engine exited rc={rc} stderr={stderr_txt!r}")

    wall_s = time.perf_counter() - t0
    return {
        "seed": seed,
        "total_positions": total_positions,
        "startpos_games": startpos_games,
        "startpos_positions": startpos_positions,
        "fewpiece_roots": len(FEW_PIECE_FENS),
        "fewpiece_games": fewpiece_games,
        "fewpiece_positions": fewpiece_positions,
        "diffs": diffs,
        "first_diff_msg": first_diff_msg,
        "seen_material1": seen_material1,
        "seen_rep3": seen_rep3,
        "seen_clock100": seen_clock100,
        "seen_mates": seen_mates,
        "seen_stalemates": seen_stalemates,
        "seen_ep_in_fen": seen_ep_in_fen,
        "seen_double_push_dash": seen_double_push_dash,
        "cr_ep_fen_diffs": cr_ep_fen_diffs,
        "cr_ep_fen_first": cr_ep_fen_first,
        "cr_rep2_diffs": cr_rep2_diffs,
        "cr_rep2_first": cr_rep2_first,
        "wall_s": wall_s,
    }


def main() -> None:
    exe = "/tmp/carbon2_job33/bld_sp_sgr15d/forge"
    out_path = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job33/partB_KB1_CR_raw.txt")
    res = run_kb1(exe)

    checks = [
        ("total_positions >= 300000", res["total_positions"] >= 300_000, res["total_positions"], 300_000),
        ("fewpiece_roots >= 20", res["fewpiece_roots"] >= 20, res["fewpiece_roots"], 20),
        ("differences == 0", res["diffs"] == 0, res["diffs"], 0),
        ("material == 1 >= 200", res["seen_material1"] >= 200, res["seen_material1"], 200),
        ("rep3 == 1 >= 200", res["seen_rep3"] >= 200, res["seen_rep3"], 200),
        ("clock >= 100 >= 20", res["seen_clock100"] >= 20, res["seen_clock100"], 20),
        ("mates >= 50", res["seen_mates"] >= 50, res["seen_mates"], 50),
        ("stalemates >= 50", res["seen_stalemates"] >= 50, res["seen_stalemates"], 50),
        ("ep_in_fen >= 100", res["seen_ep_in_fen"] >= 100, res["seen_ep_in_fen"], 100),
        ("double_push_dash >= 100", res["seen_double_push_dash"] >= 100, res["seen_double_push_dash"], 100),
        ("CONTROL CR fen(en_passant='fen') > 0", res["cr_ep_fen_diffs"] > 0, res["cr_ep_fen_diffs"], 1),
        ("CONTROL CR is_repetition(2) > 0", res["cr_rep2_diffs"] > 0, res["cr_rep2_diffs"], 1),
    ]

    lines = [
        f"UTC: {datetime.datetime.now(datetime.timezone.utc).strftime('%a %b %d %I:%M:%S %p UTC %Y')}",
        "=== JOB 33 PART B — KB1 & CONTROL CR ===",
        f"exe: {exe}",
        f"python-chess: {chess.__version__}",
        f"seed: {res['seed']}",
        f"wall_s: {res['wall_s']:.3f}",
        f"total_positions: {res['total_positions']} (startpos: {res['startpos_positions']} across {res['startpos_games']} seqs; "
        f"3..6-piece: {res['fewpiece_positions']} across {res['fewpiece_games']} seqs from {res['fewpiece_roots']} distinct roots)",
        f"differences_vs_library: {res['diffs']}",
        "",
        "--- Class Counts & Threshold Checks ---",
    ]
    all_ok = True
    for label, ok, got_v, req_v in checks:
        all_ok = all_ok and ok
        lines.append(f"  {label:38s}: got={got_v:8d} (req={req_v:6d}) [{'PASS' if ok else 'FAIL'}]")

    lines.extend([
        "",
        "--- CONTROL CR First Witness Examples ---",
        f"  CR1 fen(en_passant='fen') diffs={res['cr_ep_fen_diffs']}: {res['cr_ep_fen_first']}",
        f"  CR2 is_repetition(2)      diffs={res['cr_rep2_diffs']}: {res['cr_rep2_first']}",
    ])
    if res["first_diff_msg"]:
        lines.append(f"  FIRST DIFF: {res['first_diff_msg']}")

    txt = "\n".join(lines) + "\n"
    out_path.write_text(txt)
    print(txt, flush=True)
    assert all_ok, "One or more KB1 / Control CR checks failed!"


if __name__ == "__main__":
    main()
