#!/usr/bin/env python3
"""
Job 33 In-Engine Loop Driver (Loop):
Uses `selfgame` on the patched engine after the 8 random opening plies, turning `sg` and `sgend`
lines into R3's record text and restarting the engine on `sgerror` per R4.
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import random
import resource
import time
from typing import Optional

import chess

from ref_driver import (
    AttemptRow,
    EngineProcess,
    RunResult,
    RunSettings,
    format_game_records,
    write_attempt_rows,
)


def parse_sgend(line: str) -> tuple[int, str, int, int, int, int, list[str]]:
    # Format:
    # sgend result <1|0|-1> reason <reason> plies <plies> run <run> searches <k> nodes <sum> moves[ m1 m2 ...]
    marker = " moves"
    idx = line.find(marker)
    if idx < 0 or not line.startswith("sgend "):
        raise ValueError(f"Malformed sgend line: {line!r}")
    head = line[:idx].split()
    tail = line[idx + len(marker) :].strip()
    loop_moves = tail.split() if tail else []
    if (
        len(head) != 13
        or head[0] != "sgend"
        or head[1] != "result"
        or head[3] != "reason"
        or head[5] != "plies"
        or head[7] != "run"
        or head[9] != "searches"
        or head[11] != "nodes"
    ):
        raise ValueError(f"Malformed sgend header: {line!r}")
    return (
        int(head[2]),
        head[4],
        int(head[6]),
        int(head[8]),
        int(head[10]),
        int(head[12]),
        loop_moves,
    )


def run_loop(
    exe_path: str,
    seed: str,
    attempts: int,
    settings: RunSettings,
    cpu_pin: Optional[int] = None,
    out_records_path: Optional[pathlib.Path] = None,
) -> RunResult:
    r_self_0 = resource.getrusage(resource.RUSAGE_SELF)
    t0 = time.perf_counter()

    rng = random.Random(seed)
    eng = EngineProcess(exe_path, settings.net_path, cpu_pin=cpu_pin)
    engine_cpu_total = 0.0

    full_hasher = hashlib.sha256()
    first10_hasher = hashlib.sha256()
    out_fp = out_records_path.open("wb") if out_records_path is not None else None

    finished = 0
    thrown_away = 0
    total_records = 0
    moves_finished = 0
    moves_all = 0
    total_searches = 0
    total_nodes = 0
    w_wins = 0
    draws = 0
    b_wins = 0
    rows: list[AttemptRow] = []

    sg_cmd_suffix = (
        f"selfgame softnodes {settings.N} evallimit {settings.E} maxply {settings.M} "
        f"writeminply {settings.W} drawply {settings.P} drawscore {settings.S} drawcount {settings.C}\n"
    )

    try:
        for attempt_idx in range(1, attempts + 1):
            board = chess.Board()
            moves: list[str] = []
            rng.sample(range(0, 8), 8)

            eng.send("ucinewgame\nisready\n")
            eng.wait_for("readyok")

            ended_in_opening = False
            result = 0
            end_reason = ""

            while len(moves) < 8:
                ply = len(moves)
                if not any(board.legal_moves):
                    if not board.is_check():
                        result = 0
                        end_reason = "stalemate"
                    else:
                        result = -1 if board.turn == chess.WHITE else 1
                        end_reason = "mate"
                    ended_in_opening = True
                    break

                is_rule_draw = (
                    board.is_insufficient_material()
                    or board.halfmove_clock >= 100
                    or board.is_repetition(3)
                )
                if is_rule_draw or ply >= settings.M:
                    result = 0
                    end_reason = "rule" if is_rule_draw else "plylimit"
                    ended_in_opening = True
                    break

                mv = rng.choice(list(board.legal_moves))
                board.push(mv)
                moves.append(mv.uci())

            if ended_in_opening:
                finished += 1
                moves_finished += len(moves)
                moves_all += len(moves)
                if result == 1:
                    w_wins += 1
                elif result == 0:
                    draws += 1
                else:
                    b_wins += 1
                rows.append(
                    AttemptRow(
                        attempt=attempt_idx,
                        finished=True,
                        records=0,
                        result=result,
                        moves=len(moves),
                        searches=0,
                        nodes=0,
                        end_reason=end_reason,
                        thrown_ply=None,
                        text_sha256=hashlib.sha256(b"").hexdigest(),
                    )
                )
                continue

            pos_cmd = "position startpos moves " + " ".join(moves) if moves else "position startpos"
            eng.send(f"{pos_cmd}\n{sg_cmd_suffix}")

            records: list[tuple[str, str, int, int, bool]] = []
            thrown = False
            thrown_ply: Optional[int] = None
            att_plies = len(moves)
            att_searches = 0
            att_nodes = 0

            while True:
                line = eng.readline()
                if line.startswith("sg "):
                    _, ply_s, x_s, mv_s, fen_s = line.split(" ", 4)
                    was_white = fen_s.split(" ", 2)[1] == "w"
                    records.append((fen_s, mv_s, int(x_s), int(ply_s), was_white))
                elif line.startswith("sgend "):
                    result, end_reason, att_plies, _run_val, att_searches, att_nodes, _loop_mvs = parse_sgend(line)
                    break
                elif line.startswith("sgerror "):
                    # Format: sgerror noscore ply <ply> fen <FEN>
                    parts = line.split(" ", 5)
                    if len(parts) != 6 or parts[1] != "noscore" or parts[2] != "ply" or parts[4] != "fen":
                        raise ValueError(f"Malformed sgerror line: {line!r}")
                    thrown = True
                    thrown_ply = int(parts[3])
                    att_plies = thrown_ply
                    att_searches = thrown_ply - len(moves) + 1
                    end_reason = f"thrown@{thrown_ply}"
                    engine_cpu_total += eng.quit_and_reap()
                    eng = EngineProcess(exe_path, settings.net_path, cpu_pin=cpu_pin)
                    break
                else:
                    raise ValueError(f"Unexpected line during selfgame: {line!r}")

            moves_all += att_plies
            total_searches += att_searches
            total_nodes += att_nodes

            if thrown:
                thrown_away += 1
                rows.append(
                    AttemptRow(
                        attempt=attempt_idx,
                        finished=False,
                        records=0,
                        result=None,
                        moves=att_plies,
                        searches=att_searches,
                        nodes=0,
                        end_reason=end_reason,
                        thrown_ply=thrown_ply,
                        text_sha256=hashlib.sha256(b"").hexdigest(),
                    )
                )
            else:
                finished += 1
                moves_finished += att_plies
                total_records += len(records)
                if result == 1:
                    w_wins += 1
                elif result == 0:
                    draws += 1
                else:
                    b_wins += 1
                game_txt = format_game_records(records, result)
                game_bytes = game_txt.encode("ascii")
                full_hasher.update(game_bytes)
                if attempt_idx <= 10:
                    first10_hasher.update(game_bytes)
                if out_fp is not None:
                    out_fp.write(game_bytes)
                rows.append(
                    AttemptRow(
                        attempt=attempt_idx,
                        finished=True,
                        records=len(records),
                        result=result,
                        moves=att_plies,
                        searches=att_searches,
                        nodes=att_nodes,
                        end_reason=end_reason,
                        thrown_ply=None,
                        text_sha256=hashlib.sha256(game_bytes).hexdigest(),
                    )
                )
    finally:
        if out_fp is not None:
            out_fp.close()
        engine_cpu_total += eng.quit_and_reap()

    t1 = time.perf_counter()
    r_self_1 = resource.getrusage(resource.RUSAGE_SELF)
    driver_cpu = float(
        (r_self_1.ru_utime - r_self_0.ru_utime) + (r_self_1.ru_stime - r_self_0.ru_stime)
    )

    return RunResult(
        attempts=attempts,
        finished=finished,
        thrown_away=thrown_away,
        records=total_records,
        moves_finished=moves_finished,
        moves_all=moves_all,
        searches=total_searches,
        final_nodes=total_nodes,
        white_wins=w_wins,
        draws=draws,
        black_wins=b_wins,
        full_sha256=full_hasher.hexdigest(),
        first10_sha256=first10_hasher.hexdigest(),
        wall_s=t1 - t0,
        driver_cpu_s=driver_cpu,
        engine_cpu_s=engine_cpu_total,
        rows=rows,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--seed", required=True)
    ap.add_argument("--attempts", type=int, required=True)
    ap.add_argument("--N", type=int, default=2000)
    ap.add_argument("--E", type=int, default=2000)
    ap.add_argument("--M", type=int, default=300)
    ap.add_argument("--W", type=int, default=8)
    ap.add_argument("--P", type=int, default=80)
    ap.add_argument("--S", type=int, default=5)
    ap.add_argument("--C", type=int, default=8)
    ap.add_argument("--net", default=None)
    ap.add_argument("--cpu", type=int, default=None)
    ap.add_argument("--rows-out", type=pathlib.Path, default=None)
    ap.add_argument("--records-out", type=pathlib.Path, default=None)
    args = ap.parse_args()

    settings = RunSettings(
        N=args.N, E=args.E, M=args.M, W=args.W, P=args.P, S=args.S, C=args.C, net_path=args.net
    )
    res = run_loop(
        args.exe, args.seed, args.attempts, settings, cpu_pin=args.cpu, out_records_path=args.records_out
    )
    if args.rows_out is not None:
        write_attempt_rows(args.rows_out, f"Loop seed={args.seed} attempts={args.attempts}", res)
    print(
        f"seed={args.seed} attempts={res.attempts} fin={res.finished} thrown={res.thrown_away} "
        f"records={res.records} moves_fin={res.moves_finished} moves_all={res.moves_all} "
        f"searches={res.searches} nodes={res.final_nodes} W/D/B={res.white_wins}/{res.draws}/{res.black_wins} "
        f"wall={res.wall_s:.3f}s drv_cpu={res.driver_cpu_s:.3f}s eng_cpu={res.engine_cpu_s:.3f}s\n"
        f"  full_sha256    = {res.full_sha256}\n"
        f"  first10_sha256 = {res.first10_sha256}"
    )


if __name__ == "__main__":
    main()
