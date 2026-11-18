#!/usr/bin/env python3
"""
Deterministic single-process driver replicating the PC's self-play workload for Forge:
- One persistent engine process kept across all games.
- Configured with PC20 (in exact order), Threads 1, Hash 16, then FORGENN3 v3 net.
- Before timing: generates `num_games` deterministic 8-ply random legal openings from `seed`
  via the engine's own `go perft 1` legal-move listing.
- Timed loop per game:
    ucinewgame
    isready -> wait readyok
    for ply in 8 .. max_plies-1:
      position startpos moves <all moves so far>
      go softnodes 2000 -> wait bestmove
      stop game on checkmate/stalemate (0000), insufficient-material root (0 nodes),
      50-move rule (100 reversible halfmoves), threefold repetition, or ply == max_plies.
- Emits total searches, total nodes, searches/sec, effective nps, and an FNV-1a 64-bit
  hash over every (game, ply, bestmove, nodes, score) tuple to verify bit-exact search identity.
- Records final softnodes totals and a separate FNV-1a hash over (game, ply, final nodes).
- Optionally dumps sampled FENs / move-lists for position test suites.
"""

import argparse
from contextlib import ExitStack, nullcontext
import json
import pathlib
import random
import re
import subprocess
import sys
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

HLM_FIELDS = ("calls", "incheck", "nomove", "mismatch")
HLM_COUNTS = re.compile(r"info string hlm calls=([0-9]+) incheck=([0-9]+) nomove=([0-9]+) mismatch=([0-9]+)")
HLM_FIRST = re.compile(r"info string hlm first_mismatch fast=([01]) full=([01]) fen=(.+)")


class EngineAudit:
    def __init__(self, stdout, stderr, status):
        self.stdout, self.stderr, self.status = stdout, stderr, status
        self.context = {"phase": "setup"}
        self.failures = []
        self.active = []
        self.returncode = None

    def set_root(self, phase, game, ply, position):
        self.context = {"phase": phase, "game": game, "game_ply": ply, "position": position}

    def readline(self):
        line = self.source.readline()
        self.stdout.write(line)
        if line.startswith("info string NNUE v3 active: "):
            self.active.append(line.rstrip())
        if "REP VERIFY FAILED" in line:
            self.failures.append(self.context | {"line": line.rstrip()})
        return line

    def finish(self, returncode):
        self.returncode = returncode
        print(json.dumps({"engine_exit": returncode, "failure_count": len(self.failures),
                          "failures": self.failures, "active_net": self.active}), file=self.status)


class MinimalBoardTracker:
    """Tracks board placement, castling, ep, halfmove clock, and 3-fold repetition for UCI moves."""

    def __init__(self):
        self.grid = [
            "R", "N", "B", "Q", "K", "B", "N", "R",
            "P", "P", "P", "P", "P", "P", "P", "P",
            ".", ".", ".", ".", ".", ".", ".", ".",
            ".", ".", ".", ".", ".", ".", ".", ".",
            ".", ".", ".", ".", ".", ".", ".", ".",
            ".", ".", ".", ".", ".", ".", ".", ".",
            "p", "p", "p", "p", "p", "p", "p", "p",
            "r", "n", "b", "q", "k", "b", "n", "r",
        ]
        self.stm = "w"
        self.castling = "KQkq"
        self.ep = -1
        self.halfmove = 0
        self.fullmove = 1
        self.counts = {}
        self._record()

    @staticmethod
    def sq(name: str) -> int:
        return (ord(name[1]) - ord("1")) * 8 + (ord(name[0]) - ord("a"))

    @staticmethod
    def sq_name(idx: int) -> str:
        return chr(ord("a") + (idx & 7)) + chr(ord("1") + (idx >> 3))

    def _key(self):
        return ("".join(self.grid), self.stm, self.castling, self.ep)

    def _record(self):
        k = self._key()
        self.counts[k] = self.counts.get(k, 0) + 1

    def fen(self) -> str:
        rows = []
        for r in range(7, -1, -1):
            row = ""
            empty = 0
            for f in range(8):
                p = self.grid[r * 8 + f]
                if p == ".":
                    empty += 1
                else:
                    if empty:
                        row += str(empty)
                        empty = 0
                    row += p
            if empty:
                row += str(empty)
            rows.append(row)
        c = self.castling if self.castling else "-"
        ep_str = self.sq_name(self.ep) if self.ep >= 0 else "-"
        return f"{'/'.join(rows)} {self.stm} {c} {ep_str} {self.halfmove} {self.fullmove}"

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
            has_ep = False
            if f_file > 0 and self.grid[to - 1] == opp_pawn:
                has_ep = True
            if f_file < 7 and self.grid[to + 1] == opp_pawn:
                has_ep = True
            if has_ep:
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
        if self.halfmove >= 100:
            return True
        if self.counts.get(self._key(), 0) >= 3:
            return True
        return False


def fnv1a64_str(h: int, s: str) -> int:
    mask = (1 << 64) - 1
    for b in s.encode("ascii"):
        h = ((h ^ b) * 1099511628211) & mask
    return h


def parse_final_nodes(line: str, previous: int | None, context: str) -> int:
    if previous is not None:
        raise RuntimeError(f"Duplicate softnodes final count during {context}: {line.strip()}")
    parts = line.split()
    if (len(parts) != 5 or parts[:4] != ["info", "string", "softnodes", "nodes"]
            or not parts[4].isascii() or not parts[4].isdecimal()):
        raise RuntimeError(f"Malformed softnodes final count during {context}: {line.strip()}")
    return int(parts[4])


def send(proc: subprocess.Popen, text: str):
    assert proc.stdin is not None
    proc.stdin.write(text)
    proc.stdin.flush()


def wait_ready(proc: subprocess.Popen, check_errors: bool = True):
    assert proc.stdout is not None
    while True:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("Engine EOF before readyok")
        s = line.strip()
        if check_errors and any(bad in s for bad in ("unknown option", "invalid value", "ERROR")):
            raise RuntimeError(f"Engine option/setup error: {s}")
        if s == "readyok":
            return


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
            mv = s.split(": ", 1)[0]
            legal.append(mv)
    legal.sort()
    return legal


def generate_openings(proc: subprocess.Popen, num_games: int, random_plies: int, seed: int) -> list[list[str]]:
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


def run_selfplay(
    engine_path: str,
    net_path: str,
    num_games: int,
    softnodes: int,
    random_plies: int,
    max_plies: int,
    seed: int,
    extra_options: list[tuple[str, str]],
    dump_fens_path: str | None = None,
    trace=None,
    check_hlm: bool = False,
    audit=None,
):
    proc = subprocess.Popen(
        [engine_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=audit.stderr if audit else subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    if audit:
        audit.source, proc.stdout = proc.stdout, audit
    try:
        cfg_lines = ["uci\n"]
        for k, v in PC20_OPTIONS:
            cfg_lines.append(f"setoption name {k} value {v}\n")
        cfg_lines.append(f"setoption name NNUEArchFile value {net_path}\n")
        cfg_lines.append("setoption name NNUEArch value true\n")
        for k, v in extra_options:
            cfg_lines.append(f"setoption name {k} value {v}\n")
        cfg_lines.append("isready\n")
        send(proc, "".join(cfg_lines))
        wait_ready(proc, check_errors=True)

        openings = generate_openings(proc, num_games, random_plies, seed)
        # Warm up 1 game untimed so OS pages and allocator are faulted in before timing.
        send(proc, "ucinewgame\nisready\n")
        wait_ready(proc, check_errors=True)
        warm_position = f"position startpos moves {' '.join(openings[0])}"
        if audit:
            audit.set_root("warm-up", 0, random_plies, warm_position)
        send(proc, f"{warm_position}\ngo softnodes {softnodes}\n")
        assert proc.stdout is not None
        warm_final_nodes = None
        while True:
            ln = proc.stdout.readline()
            if not ln:
                raise RuntimeError("Engine EOF during warm-up search")
            if ln.startswith("info string softnodes nodes"):
                warm_final_nodes = parse_final_nodes(ln, warm_final_nodes, "warm-up")
            elif ln.startswith("bestmove "):
                if warm_final_nodes is None:
                    raise RuntimeError(f"Missing softnodes final count during warm-up: {ln.strip()}")
                break

        collected_fens: list[str] = []
        total_searches = 0
        total_nodes = 0
        trace_hash = 14695981039346656037
        final_sum = 0
        at_cap = 0
        terminal = 0
        final_hash = trace_hash
        hard_cap = 4 * softnodes
        hlm_totals = dict.fromkeys(HLM_FIELDS, 0) if check_hlm else None
        first_mismatch = None

        t0 = time.perf_counter_ns()
        for g_idx, opening in enumerate(openings):
            send(proc, "ucinewgame\nisready\n")
            wait_ready(proc, check_errors=False)

            moves = list(opening)
            tracker = MinimalBoardTracker()
            for mv in moves:
                tracker.push_uci(mv)

            for ply in range(random_plies, max_plies):
                if tracker.is_draw():
                    break
                if dump_fens_path is not None:
                    collected_fens.append(tracker.fen())

                position = f"position startpos moves {' '.join(moves)}"
                if audit:
                    audit.set_root("workload", g_idx, ply, position)
                send(proc, f"{position}\ngo softnodes {softnodes}\n")

                last_nodes = 0
                last_score = ""
                final_nodes = None
                last_info_nodes = None
                last_info_line = None
                final_line = None
                hlm_counts = None
                hlm_first = None
                bestmove = "0000"
                context = f"game {g_idx}, ply {ply}"
                while True:
                    line = proc.stdout.readline()
                    if not line:
                        raise RuntimeError("Engine EOF during search")
                    if line.startswith("info depth "):
                        parts = line.split()
                        last_info_nodes = None
                        last_info_line = line.rstrip("\r\n")
                        for i, tok in enumerate(parts):
                            if tok == "nodes" and i + 1 < len(parts):
                                last_info_nodes = last_nodes = int(parts[i + 1])
                            elif tok == "score" and i + 2 < len(parts):
                                last_score = f"{parts[i + 1]}:{parts[i + 2]}"
                    elif line.startswith("info string softnodes nodes"):
                        final_nodes = parse_final_nodes(line, final_nodes, context)
                        final_line = line.rstrip("\r\n")
                    elif check_hlm and line.startswith("info string hlm "):
                        detail = line.rstrip("\r\n")
                        if count := HLM_COUNTS.fullmatch(detail):
                            if hlm_counts is not None:
                                raise RuntimeError(f"Duplicate HLM counts during {context}: {detail}")
                            hlm_counts = dict(zip(HLM_FIELDS, map(int, count.groups())))
                            if any(hlm_counts[field] > hlm_counts["calls"] for field in HLM_FIELDS[1:]):
                                raise RuntimeError(f"Inconsistent HLM counts during {context}: {detail}")
                        elif mismatch := HLM_FIRST.fullmatch(detail):
                            fast, full, fen = mismatch.groups()
                            if hlm_first is not None or fast == full or len(fen.split()) != 6:
                                raise RuntimeError(f"Invalid HLM mismatch during {context}: {detail}")
                            hlm_first = {"game": g_idx, "ply": ply, "fast": int(fast),
                                         "full": int(full), "fen": fen, "line": detail}
                        else:
                            raise RuntimeError(f"Malformed HLM output during {context}: {detail}")
                    elif line.startswith("bestmove "):
                        bestmove = line.split()[1]
                        bestmove_line = line.rstrip("\r\n")
                        break

                terminal_fallback = final_nodes is None
                if terminal_fallback:
                    if bestmove != "0000" and last_info_nodes != 0:
                        raise RuntimeError(f"Missing softnodes final count during {context}: "
                                           f"bestmove {bestmove}, last info nodes {last_info_nodes}")
                    final_nodes = 0
                    terminal += 1
                if check_hlm:
                    if hlm_counts is None:
                        raise RuntimeError(f"Missing HLM counts during {context}")
                    if bool(hlm_counts["mismatch"]) != (hlm_first is not None):
                        raise RuntimeError(f"Inconsistent HLM first mismatch during {context}")
                    for field in HLM_FIELDS:
                        hlm_totals[field] += hlm_counts[field]
                    if first_mismatch is None:
                        first_mismatch = hlm_first

                total_searches += 1
                total_nodes += last_nodes
                trace_hash = fnv1a64_str(trace_hash, f"{g_idx},{ply},{bestmove},{last_nodes},{last_score};")
                final_sum += final_nodes
                at_cap += final_nodes == hard_cap
                final_hash = fnv1a64_str(final_hash, f"{g_idx},{ply},{final_nodes};")

                if trace is not None:
                    record = {"game": g_idx, "ply": ply, "position": position, "bestmove": bestmove,
                              "nodes": last_nodes, "score": last_score, "final": final_nodes,
                              "terminal": terminal_fallback, "last_info": last_info_line,
                              "final_line": final_line, "bestmove_line": bestmove_line}
                    if check_hlm:
                        record.update(hlm=hlm_counts, hlm_first_mismatch=hlm_first)
                    trace.write(json.dumps(record, separators=(",", ":")) + "\n")

                if bestmove == "0000" or last_nodes == 0:
                    break
                moves.append(bestmove)
                tracker.push_uci(bestmove)

        t1 = time.perf_counter_ns()
        send(proc, "quit\n")
        proc.wait(timeout=5)
    finally:
        if audit and audit.failures:
            proc.wait(timeout=5)
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
        if audit:
            while audit.readline():
                pass
            audit.finish(proc.returncode)

    if dump_fens_path is not None:
        pathlib.Path(dump_fens_path).write_text("\n".join(collected_fens) + "\n")

    elapsed_s = (t1 - t0) / 1e9
    summary = {
        "games": num_games,
        "searches": total_searches,
        "total_nodes": total_nodes,
        "avg_nodes_per_search": round(total_nodes / max(1, total_searches), 2),
        "avg_searches_per_game": round(total_searches / max(1, num_games), 2),
        "elapsed_ms": round(elapsed_s * 1000.0, 3),
        "searches_per_sec": round(total_searches / elapsed_s, 2),
        "effective_nps": round(total_nodes / elapsed_s, 1),
        "trace_fnv1a64": f"{trace_hash:016x}",
        "terminal": terminal,
        "final_sum": final_sum,
        "at_cap": at_cap,
        "final_fnv1a64": f"{final_hash:016x}",
    }
    if check_hlm:
        summary["hlm"] = hlm_totals | {"first_mismatch": first_mismatch}
    return summary


def main():
    ap = argparse.ArgumentParser(description="Deterministic Forge PC20 self-play workload benchmark driver.")
    ap.add_argument("--engine", required=True, help="Path to forge binary")
    ap.add_argument("--net", required=True, help="Path to FORGENN3 .fnn3 network file")
    ap.add_argument("--games", type=int, default=8, help="Number of self-play games per run")
    ap.add_argument("--softnodes", type=int, default=2000, help="Soft node target per search")
    ap.add_argument("--random-plies", type=int, default=8, help="Random opening plies per game")
    ap.add_argument("--max-plies", type=int, default=300, help="Maximum plies per game")
    ap.add_argument("--seed", type=int, default=20261117, help="Deterministic PRNG seed for openings")
    ap.add_argument("--option", action="append", default=[], help="Extra UCI option Name=Value")
    ap.add_argument("--dump-fens", default=None, help="Optional output file for visited FENs")
    ap.add_argument("--trace", type=pathlib.Path, help="Create a JSONL file of measured search evidence")
    ap.add_argument("--audit", type=pathlib.Path, required=True, help="Write observed UCI output and child exit")
    ap.add_argument("--hlm", action="store_true", help="Require and sum per-search has_legal_move probe counts")
    ap.add_argument("--json", action="store_true", help="Print JSON summary line")
    args = ap.parse_args()

    extra = []
    for item in args.option:
        if "=" not in item:
            ap.error(f"--option requires Name=Value, got {item}")
        k, v = item.split("=", 1)
        extra.append((k, v))

    trace_context = args.trace.open("x", encoding="ascii", buffering=1) if args.trace else nullcontext()
    with trace_context as trace, ExitStack() as output:
        def open_audit(suffix):
            return output.enter_context(pathlib.Path(str(args.audit) + suffix).open("x", encoding="ascii"))

        audit = EngineAudit(open_audit(".engine.stdout.txt"), open_audit(".engine.stderr.txt"),
                            open_audit(".engine_status.json"))
        try:
            summary = run_selfplay(
                engine_path=args.engine,
                net_path=args.net,
                num_games=args.games,
                softnodes=args.softnodes,
                random_plies=args.random_plies,
                max_plies=args.max_plies,
                seed=args.seed,
                extra_options=extra,
                dump_fens_path=args.dump_fens,
                trace=trace,
                check_hlm=args.hlm,
                audit=audit,
            )
        except RuntimeError:
            if audit.returncode == 3 and len(audit.failures) == 1:
                raise SystemExit(3)
            raise
        if audit.returncode != 0 or audit.failures:
            raise RuntimeError(f"engine exit {audit.returncode}, verification failures {audit.failures}")
    if args.json:
        print(json.dumps(summary))
    else:
        for k, v in summary.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
