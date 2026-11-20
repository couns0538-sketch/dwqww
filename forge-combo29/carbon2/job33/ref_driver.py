#!/usr/bin/env python3
"""
Job 33 Reference Self-Play Driver (Ref) implementing PC rules R0-R4 using python-chess.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import os
import pathlib
import random
import resource
import subprocess
import time
from typing import Optional

import chess

PC20_OPTIONS: list[tuple[str, str]] = [
    ("LmrQuietBase", "93"),
    ("LmrQuietDivisor", "205"),
    ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"),
    ("LmrHistoryDivisor", "5643"),
    ("NullMoveBase", "5"),
    ("LmpBase", "8"),
    ("HistoryPruneMultiplier", "2220"),
    ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"),
    ("HistoryBonusMax", "2212"),
    ("SingularDepth", "6"),
    ("IirDepth", "2"),
    ("NonPawnCorrection", "true"),
    ("CuckooRep", "true"),
    ("HistRework", "2"),
    ("TtPruneV2", "true"),
    ("CorrHistV2", "true"),
    ("MateAlphaGuard", "true"),
    ("OwnBook", "false"),
    ("Threads", "1"),
    ("Hash", "16"),
]


@dataclasses.dataclass
class RunSettings:
    N: int = 2000
    E: int = 2000
    M: int = 300
    W: int = 8
    P: int = 80
    S: int = 5
    C: int = 8
    net_path: Optional[str] = None


@dataclasses.dataclass
class AttemptRow:
    attempt: int
    finished: bool
    records: int
    result: Optional[int]
    moves: int
    searches: int
    nodes: int
    end_reason: str
    thrown_ply: Optional[int]
    text_sha256: str


@dataclasses.dataclass
class RunResult:
    attempts: int
    finished: int
    thrown_away: int
    records: int
    moves_finished: int
    moves_all: int
    searches: int
    final_nodes: int
    white_wins: int
    draws: int
    black_wins: int
    full_sha256: str
    first10_sha256: str
    wall_s: float
    driver_cpu_s: float
    engine_cpu_s: float
    rows: list[AttemptRow]


class EngineProcess:
    def __init__(self, exe_path: str, net_path: Optional[str] = None, cpu_pin: Optional[int] = None) -> None:
        cmd = [exe_path] if cpu_pin is None else ["taskset", "-c", str(cpu_pin), exe_path]
        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        assert self.proc.stdin is not None and self.proc.stdout is not None
        self.reaped_cpu_s = 0.0
        self._init_uci(net_path)

    def _init_uci(self, net_path: Optional[str]) -> None:
        self.send("uci\n")
        self.wait_for("uciok")
        opts = list(PC20_OPTIONS)
        if net_path is not None:
            opts.append(("NNUEArchFile", net_path))
            opts.append(("NNUEArch", "true"))
        buf = "".join(f"setoption name {k} value {v}\n" for k, v in opts) + "isready\n"
        self.send(buf)
        self.wait_for("readyok")

    def send(self, data: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(data)
        self.proc.stdin.flush()

    def readline(self) -> str:
        assert self.proc.stdout is not None
        line = self.proc.stdout.readline()
        if line == "":
            raise RuntimeError("Unexpected EOF from engine stdout")
        return line.rstrip("\r\n")

    def wait_for(self, token: str) -> None:
        while True:
            if self.readline() == token:
                return

    def quit_and_reap(self) -> float:
        if self.proc.poll() is None:
            try:
                self.send("quit\n")
            except BrokenPipeError:
                pass
        _, status, rusage = os.wait4(self.proc.pid, 0)
        if self.proc.stdin:
            self.proc.stdin.close()
        if self.proc.stdout:
            self.proc.stdout.close()
        if self.proc.stderr:
            stderr_txt = self.proc.stderr.read()
            self.proc.stderr.close()
            if stderr_txt:
                raise RuntimeError(f"Engine stderr non-empty:\n{stderr_txt}")
        if status != 0:
            raise RuntimeError(f"Engine exited with nonzero status {status}")
        self.reaped_cpu_s = float(rusage.ru_utime + rusage.ru_stime)
        return self.reaped_cpu_s


def format_game_records(records: list[tuple[str, str, int, int, bool]], result: int) -> str:
    if not records:
        return ""
    chunks: list[str] = []
    for fen_str, move_str, score_x, rec_ply, was_white in records:
        if result == 0:
            r = 0
        else:
            r = result if was_white else -result
        chunks.append(
            f"fen {fen_str}\nmove {move_str}\nscore {score_x}\nply {rec_ply}\nresult {r}\ne\n"
        )
    return "".join(chunks)


def run_ref(
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

    try:
        for attempt_idx in range(1, attempts + 1):
            board = chess.Board()
            moves: list[str] = []
            run_adj = 0
            rng.sample(range(0, 8), 8)

            eng.send("ucinewgame\nisready\n")
            eng.wait_for("readyok")

            records: list[tuple[str, str, int, int, bool]] = []
            att_searches = 0
            att_nodes = 0
            thrown = False
            thrown_ply: Optional[int] = None
            result = 0
            end_reason = ""

            while True:
                ply = len(moves)

                # (a) Side to move has no legal move
                if not any(board.legal_moves):
                    if not board.is_check():
                        result = 0
                        end_reason = "stalemate"
                    else:
                        result = -1 if board.turn == chess.WHITE else 1
                        end_reason = "mate"
                    break

                # (b) Rule draw or ply >= M
                is_rule_draw = (
                    board.is_insufficient_material()
                    or board.halfmove_clock >= 100
                    or board.is_repetition(3)
                )
                if is_rule_draw or ply >= settings.M:
                    result = 0
                    end_reason = "rule" if is_rule_draw else "plylimit"
                    break

                # (c) Random opening ply < 8
                if ply < 8:
                    mv = rng.choice(list(board.legal_moves))
                    board.push(mv)
                    moves.append(mv.uci())
                    continue

                # (d) Search at ply >= 8
                if moves:
                    pos_cmd = "position startpos moves " + " ".join(moves)
                else:
                    pos_cmd = "position startpos"
                eng.send(f"{pos_cmd}\ngo softnodes {settings.N}\n")

                last_score_kind: Optional[str] = None
                last_score_val = 0
                search_nodes: Optional[int] = None
                last_info_nodes = 0
                bestmove_uci = ""

                while True:
                    line = eng.readline()
                    if line.startswith("info "):
                        if line.startswith("info string softnodes nodes "):
                            parts = line.split()
                            search_nodes = int(parts[4])
                        else:
                            if " score " in line:
                                after_sc = line.split(" score ", 1)[1].split()
                                last_score_kind = after_sc[0]
                                last_score_val = int(after_sc[1])
                            if " nodes " in line:
                                after_nd = line.split(" nodes ", 1)[1].split()
                                last_info_nodes = int(after_nd[0])
                    elif line.startswith("bestmove "):
                        bestmove_uci = line.split()[1]
                        break

                final_n = search_nodes if search_nodes is not None else last_info_nodes
                att_searches += 1
                att_nodes += final_n
                total_searches += 1
                total_nodes += final_n

                if last_score_kind is None:
                    thrown = True
                    thrown_ply = ply
                    end_reason = f"thrown@{ply}"
                    engine_cpu_total += eng.quit_and_reap()
                    eng = EngineProcess(exe_path, settings.net_path, cpu_pin=cpu_pin)
                    break

                white_turn = board.turn == chess.WHITE
                # (e) mate X
                if last_score_kind == "mate":
                    result = 1 if (white_turn == (last_score_val > 0)) else -1
                    end_reason = "matescore"
                    break

                # (f) cp X with |X| >= E
                assert last_score_kind == "cp"
                x_val = last_score_val
                if abs(x_val) >= settings.E:
                    result = 1 if (white_turn == (x_val > 0)) else -1
                    end_reason = "evallimit"
                    break

                # (g) Record when ply >= W
                if ply >= settings.W:
                    records.append((board.fen(), bestmove_uci, x_val, ply, white_turn))

                # (h) Draw adjudication
                if ply >= settings.P and abs(x_val) <= settings.S:
                    run_adj += 1
                    if run_adj >= settings.C:
                        result = 0
                        end_reason = "drawadj"
                        break
                else:
                    run_adj = 0

                # (i) Play bestmove
                mv = chess.Move.from_uci(bestmove_uci)
                board.push(mv)
                moves.append(bestmove_uci)

            moves_all += len(moves)
            if thrown:
                thrown_away += 1
                rows.append(
                    AttemptRow(
                        attempt=attempt_idx,
                        finished=False,
                        records=0,
                        result=None,
                        moves=len(moves),
                        searches=att_searches,
                        nodes=att_nodes,
                        end_reason=end_reason,
                        thrown_ply=thrown_ply,
                        text_sha256=hashlib.sha256(b"").hexdigest(),
                    )
                )
            else:
                finished += 1
                moves_finished += len(moves)
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
                        moves=len(moves),
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


def write_attempt_rows(path: pathlib.Path, header_comment: str, res: RunResult) -> None:
    lines = [
        f"# {header_comment}",
        f"# attempts={res.attempts} finished={res.finished} thrown_away={res.thrown_away} "
        f"records={res.records} moves_finished={res.moves_finished} moves_all={res.moves_all} "
        f"searches={res.searches} final_nodes={res.final_nodes} "
        f"W/D/B={res.white_wins}/{res.draws}/{res.black_wins}",
        f"# full_sha256={res.full_sha256}",
        f"# first10_sha256={res.first10_sha256}",
        "attempt\tstatus\trecords\tresult\tmoves\tsearches\tnodes\tend_reason\ttext_sha256",
    ]
    for r in res.rows:
        st = "FIN" if r.finished else "THROWN"
        res_s = "-" if r.result is None else str(r.result)
        lines.append(
            f"{r.attempt}\t{st}\t{r.records}\t{res_s}\t{r.moves}\t{r.searches}\t{r.nodes}\t{r.end_reason}\t{r.text_sha256}"
        )
    path.write_text("\n".join(lines) + "\n")


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
    res = run_ref(
        args.exe, args.seed, args.attempts, settings, cpu_pin=args.cpu, out_records_path=args.records_out
    )
    if args.rows_out is not None:
        write_attempt_rows(args.rows_out, f"Ref seed={args.seed} attempts={args.attempts}", res)
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
