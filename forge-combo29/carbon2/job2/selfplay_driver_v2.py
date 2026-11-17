#!/usr/bin/env python3
"""
Job 2 self-play workload driver (selfplay_driver_v2.py):
- Supports both FEN-rooted games (`position fen <book_fen> moves <all moves so far>`, matching the PC's self-play)
  and startpos-rooted games (`position startpos moves <all moves so far>` with 8 random plies).
- Sends `eval` once after NNUE v3 setup and records both `NNUE v3 active:` and `info string eval` lines.
- Measures both wall-clock time (`perf_counter_ns`) and the engine process's own CPU time
  (`utime + stime` from `/proc/<pid>/stat`, excluding Python driver CPU time).
- Computes deterministic FNV-1a 64-bit trace hash over every (game, ply, bestmove, nodes, score).
"""

import argparse
import json
import os
import pathlib
import random
import subprocess
import time

PC20_OPTIONS = [
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

CLK_TCK = os.sysconf("SC_CLK_TCK")


def read_proc_cpu_ms(pid: int) -> float:
    """Reads utime + stime (fields 14 and 15, 1-indexed) from /proc/<pid>/stat in milliseconds."""
    raw = pathlib.Path(f"/proc/{pid}/stat").read_text()
    rparen = raw.rfind(")")
    fields = raw[rparen + 2 :].split()
    utime_ticks = int(fields[11])
    stime_ticks = int(fields[12])
    return (utime_ticks + stime_ticks) * (1000.0 / CLK_TCK)


class MinimalBoardTracker:
    """Tracks board placement, castling, ep, halfmove clock, and 3-fold repetition from startpos or FEN."""

    def __init__(self):
        self.grid = ["."] * 64
        self.stm = "w"
        self.castling = "KQkq"
        self.ep = -1
        self.halfmove = 0
        self.fullmove = 1
        self.counts = {}
        self.load_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    @staticmethod
    def sq(name: str) -> int:
        return (ord(name[1]) - ord("1")) * 8 + (ord(name[0]) - ord("a"))

    @staticmethod
    def sq_name(idx: int) -> str:
        return chr(ord("a") + (idx & 7)) + chr(ord("1") + (idx >> 3))

    def load_fen(self, fen: str):
        parts = fen.strip().split()
        self.grid = ["."] * 64
        ranks = parts[0].split("/")
        for r_idx, row_str in enumerate(ranks):
            rank = 7 - r_idx
            file_i = 0
            for ch in row_str:
                if ch.isdigit():
                    file_i += int(ch)
                else:
                    self.grid[rank * 8 + file_i] = ch
                    file_i += 1
        self.stm = parts[1]
        self.castling = "" if parts[2] == "-" else parts[2]
        self.ep = -1 if parts[3] == "-" else self.sq(parts[3])
        self.halfmove = int(parts[4]) if len(parts) > 4 else 0
        self.fullmove = int(parts[5]) if len(parts) > 5 else 1
        self.counts = {}
        self._record()

    def _key(self):
        return ("".join(self.grid), self.stm, self.castling, self.ep)

    def _record(self):
        k = self._key()
        self.counts[k] = self.counts.get(k, 0) + 1

    def push_uci(self, uci: str):
        fr = self.sq(uci[0:2])
        to = self.sq(uci[2:4])
        promo = uci[4] if len(uci) == 5 else ""
        piece = self.grid[fr]
        target = self.grid[to]
        is_pawn = piece in ("P", "p")
        is_cap = target != "." or (is_pawn and to == self.ep)

        new_ep = -1
        if is_pawn and to == self.ep:
            cap_sq = to - 8 if self.stm == "w" else to + 8
            self.grid[cap_sq] = "."
        elif piece == "K" and fr == 4 and to == 6:
            self.grid[7] = "."
            self.grid[5] = "R"
        elif piece == "K" and fr == 4 and to == 2:
            self.grid[0] = "."
            self.grid[3] = "R"
        elif piece == "k" and fr == 60 and to == 62:
            self.grid[63] = "."
            self.grid[61] = "r"
        elif piece == "k" and fr == 60 and to == 58:
            self.grid[56] = "."
            self.grid[59] = "r"

        self.grid[fr] = "."
        if promo:
            self.grid[to] = promo.upper() if self.stm == "w" else promo.lower()
        else:
            self.grid[to] = piece

        if is_pawn and abs(to - fr) == 16:
            mid = (fr + to) // 2
            opp_pawn = "p" if self.stm == "w" else "P"
            f_file = to & 7
            if (f_file > 0 and self.grid[to - 1] == opp_pawn) or (f_file < 7 and self.grid[to + 1] == opp_pawn):
                new_ep = mid

        for ch, sq_idx in (("K", 4), ("Q", 4), ("K", 7), ("Q", 0), ("k", 60), ("q", 60), ("k", 63), ("q", 56)):
            if fr == sq_idx or to == sq_idx:
                self.castling = self.castling.replace(ch, "")

        self.ep = new_ep
        if is_pawn or is_cap:
            self.halfmove = 0
            self.counts.clear()
        else:
            self.halfmove += 1
        if self.stm == "b":
            self.fullmove += 1
        self.stm = "b" if self.stm == "w" else "w"
        self._record()

    def is_draw(self) -> bool:
        return self.halfmove >= 100 or self.counts.get(self._key(), 0) >= 3


def fnv1a64_str(h: int, s: str) -> int:
    mask = (1 << 64) - 1
    for b in s.encode("ascii"):
        h = ((h ^ b) * 1099511628211) & mask
    return h


def send(proc: subprocess.Popen, text: str):
    assert proc.stdin is not None
    proc.stdin.write(text)
    proc.stdin.flush()


def wait_ready_collect(proc: subprocess.Popen, check_errors: bool = True) -> list[str]:
    assert proc.stdout is not None
    collected = []
    while True:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("Engine EOF before readyok")
        s = line.strip()
        if check_errors and any(bad in s for bad in ("unknown option", "invalid value", "ERROR")):
            raise RuntimeError(f"Engine setup error: {s}")
        if s == "readyok":
            return collected
        collected.append(s)


def perft1_moves(proc: subprocess.Popen, moves: list[str]) -> list[str]:
    assert proc.stdout is not None
    pos_cmd = "position startpos" + (" moves " + " ".join(moves) if moves else "") + "\ngo perft 1\n"
    send(proc, pos_cmd)
    legal = []
    while True:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("Engine EOF during go perft 1")
        s = line.strip()
        if s.startswith("nodes "):
            break
        if ": " in s and not s.startswith("info "):
            legal.append(s.split(": ", 1)[0])
    legal.sort()
    return legal


def generate_startpos_openings(proc: subprocess.Popen, num_games: int, random_plies: int, seed: int) -> list[list[str]]:
    rng = random.Random(seed)
    openings = []
    while len(openings) < num_games:
        moves: list[str] = []
        ok = True
        for _ in range(random_plies):
            legal = perft1_moves(proc, moves)
            if not legal:
                ok = False
                break
            moves.append(rng.choice(legal))
        if ok and perft1_moves(proc, moves):
            openings.append(moves)
    return openings


def select_book_fens(fen_file: str, num_games: int) -> list[str]:
    all_fens = [ln.strip() for ln in pathlib.Path(fen_file).read_text().splitlines() if ln.strip()]
    # Prefer rich early-game book positions (>= 26 pieces) so games play full realistic lengths;
    # fall back to strided positions if fewer exist.
    rich = [f for f in all_fens if sum(1 for c in f.split()[0] if c.isalpha()) >= 26]
    pool = rich if len(rich) >= num_games else all_fens
    return [pool[int(i * len(pool) / num_games)] for i in range(num_games)]


def run_selfplay_v2(
    engine_path: str,
    net_path: str,
    mode: str = "fen",
    fen_file: str | None = None,
    num_games: int = 6,
    softnodes: int = 2000,
    random_plies: int = 8,
    max_plies: int = 300,
    seed: int = 20261117,
) -> dict:
    proc = subprocess.Popen(
        [engine_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    try:
        cfg_lines = ["uci\n"] + [f"setoption name {k} value {v}\n" for k, v in PC20_OPTIONS] + [
            f"setoption name NNUEArchFile value {net_path}\n",
            "setoption name NNUEArch value true\n",
            "position startpos\n",
            "eval\n",
            "isready\n",
        ]
        send(proc, "".join(cfg_lines))
        setup_lines = wait_ready_collect(proc, check_errors=True)
        v3_active_line = next((ln for ln in setup_lines if "NNUE v3 active:" in ln), "")
        eval_line = next((ln for ln in setup_lines if ln.startswith("info string eval ")), "")
        if not v3_active_line or not eval_line:
            raise RuntimeError(f"Missing v3 active or eval line in setup: {setup_lines}")

        if mode == "startpos":
            roots = [("startpos", mv_list) for mv_list in generate_startpos_openings(proc, num_games, random_plies, seed)]
        elif mode == "fen":
            assert fen_file is not None, "fen_file required when mode == 'fen'"
            roots = [(fen, []) for fen in select_book_fens(fen_file, num_games)]
        else:
            raise ValueError(f"Unknown mode: {mode}")

        # Untimed 1-search warmup
        send(proc, "ucinewgame\nisready\n")
        wait_ready_collect(proc, check_errors=True)
        r0_kind, r0_moves = roots[0]
        w_cmd = (
            f"position startpos moves {' '.join(r0_moves)}\n"
            if r0_kind == "startpos"
            else f"position fen {r0_kind}\n"
        )
        send(proc, w_cmd + f"go softnodes {softnodes}\n")
        assert proc.stdout is not None
        while True:
            ln = proc.stdout.readline()
            if not ln or ln.startswith("bestmove "):
                break

        total_searches = 0
        total_nodes = 0
        trace_hash = 14695981039346656037

        cpu_ms_0 = read_proc_cpu_ms(proc.pid)
        t0 = time.perf_counter_ns()

        for g_idx, (root_spec, init_moves) in enumerate(roots):
            send(proc, "ucinewgame\nisready\n")
            wait_ready_collect(proc, check_errors=False)

            moves = list(init_moves)
            tracker = MinimalBoardTracker()
            if root_spec != "startpos":
                tracker.load_fen(root_spec)
            for mv in moves:
                tracker.push_uci(mv)

            start_ply = len(moves)
            for ply in range(start_ply, max_plies):
                if tracker.is_draw():
                    break
                if root_spec == "startpos":
                    pos_str = "position startpos" + (" moves " + " ".join(moves) if moves else "")
                else:
                    pos_str = f"position fen {root_spec}" + (" moves " + " ".join(moves) if moves else "")
                send(proc, f"{pos_str}\ngo softnodes {softnodes}\n")

                last_nodes = 0
                last_score = ""
                bestmove = "0000"
                while True:
                    line = proc.stdout.readline()
                    if not line:
                        raise RuntimeError("Engine EOF during search")
                    if line.startswith("info depth "):
                        parts = line.split()
                        for i, tok in enumerate(parts):
                            if tok == "nodes" and i + 1 < len(parts):
                                last_nodes = int(parts[i + 1])
                            elif tok == "score" and i + 2 < len(parts):
                                last_score = f"{parts[i + 1]}:{parts[i + 2]}"
                    elif line.startswith("bestmove "):
                        bestmove = line.split()[1]
                        break

                total_searches += 1
                total_nodes += last_nodes
                trace_hash = fnv1a64_str(trace_hash, f"{g_idx},{ply},{bestmove},{last_nodes},{last_score};")

                if bestmove == "0000" or last_nodes == 0:
                    break
                moves.append(bestmove)
                tracker.push_uci(bestmove)

        t1 = time.perf_counter_ns()
        cpu_ms_1 = read_proc_cpu_ms(proc.pid)

        send(proc, "quit\n")
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()

    wall_ms = (t1 - t0) / 1e6
    cpu_ms = max(0.001, cpu_ms_1 - cpu_ms_0)
    return {
        "mode": mode,
        "games": num_games,
        "searches": total_searches,
        "total_nodes": total_nodes,
        "wall_ms": round(wall_ms, 3),
        "engine_cpu_ms": round(cpu_ms, 3),
        "wall_searches_per_sec": round(total_searches / (wall_ms / 1000.0), 2),
        "cpu_searches_per_sec": round(total_searches / (cpu_ms / 1000.0), 2),
        "effective_nps": round(total_nodes / (wall_ms / 1000.0), 1),
        "trace_fnv1a64": f"{trace_hash:016x}",
        "v3_active": v3_active_line,
        "setup_eval": eval_line,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--net", required=True)
    ap.add_argument("--mode", choices=["fen", "startpos"], default="fen")
    ap.add_argument("--fen-file", default=None)
    ap.add_argument("--games", type=int, default=6)
    ap.add_argument("--softnodes", type=int, default=2000)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    res = run_selfplay_v2(
        engine_path=args.engine,
        net_path=args.net,
        mode=args.mode,
        fen_file=args.fen_file,
        num_games=args.games,
        softnodes=args.softnodes,
    )
    if args.json:
        print(json.dumps(res))
    else:
        for k, v in res.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
