#!/usr/bin/env python3
"""
Job 36 In-Engine Loop Driver for v2 and v3 (`loop_v3_driver.py`):
Captures raw `sg`, `sgend`, and `sgerror` lines per attempt, parses both v2 `sgend`
(no `fen`) and v3 `sgend` (`... nodes <n> fen <FEN> moves ...`), and supports
custom `selfgame` command suffixes for Control CK.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import pathlib
import random
import sys
from typing import Optional

sys.dont_write_bytecode = True
import chess

JOB35 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job35")
sys.path.insert(0, str(JOB35))

from loop_driver import parse_sgend as parse_sgend_v2, parse_sgerror_v2
from ref_driver import EngineProcess, RunSettings, format_game_records


@dataclass
class V3AttemptDetail:
    attempt: int
    finished: bool
    opening_moves: list[str]
    loop_moves: list[str]
    sg_lines: list[str]
    sgend_line: Optional[str]
    sgerror_line: Optional[str]
    final_fen: Optional[str]
    records: int
    result: Optional[int]
    plies: int
    searches: int
    nodes: int
    end_reason: str
    text_sha256: str


@dataclass
class V3SuiteRun:
    version: int
    full_sha256: str
    first10_sha256: str
    attempts: int
    finished: int
    thrown_away: int
    total_records: int
    total_sg_lines: int
    moves_finished: int
    moves_all: int
    total_searches: int
    total_nodes: int
    w_wins: int
    draws: int
    b_wins: int
    details: list[V3AttemptDetail]


def parse_sgend_v3(line: str) -> tuple[int, str, int, int, int, int, str, list[str], str]:
    """
    Format:
      sgend result <1|0|-1> reason <reason> plies <plies> run <run> searches <k> nodes <sum> fen <FEN> moves[ m1 m2 ...]
    Returns:
      (result, reason, plies, run, searches, nodes, fen, loop_moves, stripped_v2_line)
    """
    if not line.startswith("sgend "):
        raise ValueError(f"Malformed v3 sgend line: {line!r}")
    fen_marker = " fen "
    moves_marker = " moves"
    idx_fen = line.find(fen_marker)
    if idx_fen < 0:
        raise ValueError(f"Missing ' fen ' in v3 sgend line: {line!r}")
    idx_moves = line.find(moves_marker, idx_fen + len(fen_marker))
    if idx_moves < 0:
        raise ValueError(f"Missing ' moves' after fen in v3 sgend line: {line!r}")

    head = line[:idx_fen].split()
    fen_str = line[idx_fen + len(fen_marker) : idx_moves]
    tail = line[idx_moves + len(moves_marker) :].strip()
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
        or not fen_str
    ):
        raise ValueError(f"Malformed v3 sgend header: {line!r}")

    stripped_v2_line = line[:idx_fen] + line[idx_moves:]
    return (
        int(head[2]),
        head[4],
        int(head[6]),
        int(head[8]),
        int(head[10]),
        int(head[12]),
        fen_str,
        loop_moves,
        stripped_v2_line,
    )


def run_loop_detailed(
    exe_path: str,
    version: int,
    seed: str,
    attempts: int,
    settings: RunSettings,
    cpu_pin: Optional[int] = None,
    custom_sg_cmd: Optional[str] = None,
) -> V3SuiteRun:
    assert version in (2, 3)
    rng = random.Random(seed)
    eng = EngineProcess(exe_path, settings.net_path, cpu_pin=cpu_pin)

    full_hasher = hashlib.sha256()
    first10_hasher = hashlib.sha256()

    finished = 0
    thrown_away = 0
    total_records = 0
    total_sg_lines = 0
    moves_finished = 0
    moves_all = 0
    total_searches = 0
    total_nodes = 0
    w_wins = 0
    draws = 0
    b_wins = 0
    details: list[V3AttemptDetail] = []

    if custom_sg_cmd is not None:
        sg_cmd_suffix = custom_sg_cmd.rstrip("\n") + "\n"
    else:
        sg_cmd_suffix = (
            f"selfgame softnodes {settings.N} evallimit {settings.E} maxply {settings.M} "
            f"writeminply {settings.W} drawply {settings.P} drawscore {settings.S} drawcount {settings.C}\n"
        )

    try:
        for attempt_idx in range(1, attempts + 1):
            board = chess.Board()
            opening_moves: list[str] = []
            rng.sample(range(0, 8), 8)

            eng.send("ucinewgame\nisready\n")
            eng.wait_for("readyok")

            ended_in_opening = False
            result = 0
            end_reason = ""

            while len(opening_moves) < 8:
                ply = len(opening_moves)
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
                opening_moves.append(mv.uci())

            if ended_in_opening:
                finished += 1
                moves_finished += len(opening_moves)
                moves_all += len(opening_moves)
                if result == 1:
                    w_wins += 1
                elif result == 0:
                    draws += 1
                else:
                    b_wins += 1
                details.append(
                    V3AttemptDetail(
                        attempt=attempt_idx,
                        finished=True,
                        opening_moves=opening_moves,
                        loop_moves=[],
                        sg_lines=[],
                        sgend_line=None,
                        sgerror_line=None,
                        final_fen=board.fen(),
                        records=0,
                        result=result,
                        plies=len(opening_moves),
                        searches=0,
                        nodes=0,
                        end_reason=end_reason,
                        text_sha256=hashlib.sha256(b"").hexdigest(),
                    )
                )
                continue

            pos_cmd = (
                "position startpos moves " + " ".join(opening_moves)
                if opening_moves
                else "position startpos"
            )
            eng.send(f"{pos_cmd}\n{sg_cmd_suffix}")

            records: list[tuple[str, str, int, int, bool]] = []
            sg_lines: list[str] = []
            sgend_line: Optional[str] = None
            sgerror_line: Optional[str] = None
            final_fen: Optional[str] = None
            loop_moves: list[str] = []
            thrown = False
            att_plies = len(opening_moves)
            att_searches = 0
            att_nodes = 0

            while True:
                line = eng.readline()
                if line.startswith("sg "):
                    sg_lines.append(line)
                    _, ply_s, x_s, mv_s, fen_s = line.split(" ", 4)
                    was_white = fen_s.split(" ", 2)[1] == "w"
                    records.append((fen_s, mv_s, int(x_s), int(ply_s), was_white))
                elif line.startswith("sgend "):
                    sgend_line = line
                    if version == 2:
                        (
                            result,
                            end_reason,
                            att_plies,
                            _run_val,
                            att_searches,
                            att_nodes,
                            loop_moves,
                        ) = parse_sgend_v2(line)
                        final_fen = None
                    else:
                        (
                            result,
                            end_reason,
                            att_plies,
                            _run_val,
                            att_searches,
                            att_nodes,
                            final_fen,
                            loop_moves,
                            _stripped,
                        ) = parse_sgend_v3(line)
                    break
                elif line.startswith("sgerror "):
                    sgerror_line = line
                    kind, thrown_ply, att_searches, att_nodes, _err_fen = parse_sgerror_v2(line)
                    thrown = True
                    att_plies = thrown_ply
                    end_reason = f"thrown@{thrown_ply}" if kind == "noscore" else f"{kind}@{thrown_ply}"
                    eng.quit_and_reap()
                    eng = EngineProcess(exe_path, settings.net_path, cpu_pin=cpu_pin)
                    break
                else:
                    raise ValueError(f"Unexpected line during selfgame: {line!r}")

            total_sg_lines += len(sg_lines)
            moves_all += att_plies
            total_searches += att_searches
            total_nodes += att_nodes

            if thrown:
                thrown_away += 1
                details.append(
                    V3AttemptDetail(
                        attempt=attempt_idx,
                        finished=False,
                        opening_moves=opening_moves,
                        loop_moves=[],
                        sg_lines=sg_lines,
                        sgend_line=None,
                        sgerror_line=sgerror_line,
                        final_fen=None,
                        records=0,
                        result=None,
                        plies=att_plies,
                        searches=att_searches,
                        nodes=att_nodes,
                        end_reason=end_reason,
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
                details.append(
                    V3AttemptDetail(
                        attempt=attempt_idx,
                        finished=True,
                        opening_moves=opening_moves,
                        loop_moves=loop_moves,
                        sg_lines=sg_lines,
                        sgend_line=sgend_line,
                        sgerror_line=None,
                        final_fen=final_fen,
                        records=len(records),
                        result=result,
                        plies=att_plies,
                        searches=att_searches,
                        nodes=att_nodes,
                        end_reason=end_reason,
                        text_sha256=hashlib.sha256(game_bytes).hexdigest(),
                    )
                )
    finally:
        eng.quit_and_reap()

    return V3SuiteRun(
        version=version,
        full_sha256=full_hasher.hexdigest(),
        first10_sha256=first10_hasher.hexdigest(),
        attempts=attempts,
        finished=finished,
        thrown_away=thrown_away,
        total_records=total_records,
        total_sg_lines=total_sg_lines,
        moves_finished=moves_finished,
        moves_all=moves_all,
        total_searches=total_searches,
        total_nodes=total_nodes,
        w_wins=w_wins,
        draws=draws,
        b_wins=b_wins,
        details=details,
    )


def write_v2_v3_rows(path: pathlib.Path, header: str, run: V3SuiteRun) -> None:
    lines = [
        f"# {header}",
        f"# attempts={run.attempts} finished={run.finished} thrown_away={run.thrown_away} "
        f"records={run.total_records} sg_lines={run.total_sg_lines} "
        f"moves_finished={run.moves_finished} moves_all={run.moves_all} "
        f"searches={run.total_searches} final_nodes={run.total_nodes} "
        f"W/D/B={run.w_wins}/{run.draws}/{run.b_wins}",
        f"# full_sha256={run.full_sha256}",
        f"# first10_sha256={run.first10_sha256}",
    ]
    if run.version == 3:
        lines.append("attempt\tstatus\trecords\tresult\tmoves\tsearches\tnodes\tend_reason\ttext_sha256\tfinal_fen")
        for d in run.details:
            st = "FIN" if d.finished else "THROWN"
            res = "-" if d.result is None else str(d.result)
            ff = d.final_fen if d.final_fen is not None else "-"
            lines.append(
                f"{d.attempt}\t{st}\t{d.records}\t{res}\t{d.plies}\t{d.searches}\t{d.nodes}\t{d.end_reason}\t{d.text_sha256}\t{ff}"
            )
    else:
        lines.append("attempt\tstatus\trecords\tresult\tmoves\tsearches\tnodes\tend_reason\ttext_sha256")
        for d in run.details:
            st = "FIN" if d.finished else "THROWN"
            res = "-" if d.result is None else str(d.result)
            lines.append(
                f"{d.attempt}\t{st}\t{d.records}\t{res}\t{d.plies}\t{d.searches}\t{d.nodes}\t{d.end_reason}\t{d.text_sha256}"
            )
    path.write_text("\n".join(lines) + "\n")
