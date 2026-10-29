#!/usr/bin/env python3
"""R5D smoke: the fixed exe (ON) vs the base exe (OFF), both sides at --threads (default 2), plus a go/stop stress.

R5D copy of opus_r5/r5c/smoke_n3.py (branch opus-r5c-netv4) with four changes: `--threads N` sets Threads for both
sides (default 2; `--concurrency 1` keeps at most N search threads busy, the idle side blocks on stdin); the stop
stress builds its legality board from the opening FEN when there is one (the R5C runner used the start position,
which reported legal moves of FEN openings as illegal); every move records whether the mover's last score line was
a mate score (summary: `moves_with_mate_score` per side, and `mate_finishes`: games won by mate, per side); `--epd`
openings may be any FEN set (e.g. bare-king endings, where the attacker must convert).

R5C text follows (M2 smoke stability: ON vs OFF games from FEN openings with tablebase-hit counts, plus a go/stop stress).

R5C copy of opus_r5/r5b/smoke_ab.py (R5A smoke.py + --exe-off) with three changes: `--epd FILE` takes the openings
from a FEN/EPD file (first four or six fields per line; `position fen ... moves ...` is sent), every move's last
`tbhits N` of the side to move is recorded (summary: TB-hit totals and moves with hits, per side; the OFF side must
report none when it has no tables), and the PGN carries the FEN header.

R5B copy of opus_r5/r5a/smoke.py (branch opus-r5a-singles, R5A M3) with one change: `--exe-off` makes the OFF side
a second exe (default: the ON exe at its defaults, as in R5A), so a build-switch exe (N2) plays the OFF build of the
same tree. Use `--expect-echo none` for exes without the R5A option echo (forge-bundle-int has none).

Crash, legality and clock checks only -- NOT a strength test (no Elo is computed or claimed).

Games: `--games` (default 200) at `--tc` (default 5+0.05) between the exe with the option set (ON) and the same exe
at its defaults (OFF); both sides Threads 1, Hash 16, OwnBook false. Openings: `--games / 2` openings drawn with
`--seed` from the 8-move book (default 8moves_v3.pgn, read-only), each played twice with colours swapped.
`--concurrency` games run at once (default 3): every game has one engine searching at a time (no pondering), so
at most `--concurrency` engine threads compute; the idle side blocks on stdin. Engines start at BelowNormal and
are reused across games (`ucinewgame` between games), as a match runner does; a crashed or hung engine is
recorded, restarted, and its game scored as a loss for it.
Per move the runner checks: a `bestmove` arrives (timeout = the side's clock + 3 s), the move is legal
(python-chess), the side's clock (wall time from `go` to `bestmove`, Fischer increment) stays >= 0, and no line
contains "ERROR". It also checks the R5A echo: every `go` of the ON engine prints exactly one
`info string active: <expected>` line, the OFF engine none (`--expect-echo ''` disables this for an exe without it).
Games end by mate, stalemate, insufficient material, threefold or 50-move claim (python-chess), or at `--max-plies`
(draw by adjudication).

Stop stress: `--stop-iterations` (default 50) times on the ON engine: position (an opening), `go infinite`, a random
10-150 ms wait, `stop` -> exactly one legal bestmove within 3 s; then `go movetime 300`, a random wait, `stop` ->
the same; then `isready` -> readyok with no extra bestmove.

Output (in --out): games.pgn, summary.json (counts, per-failure details, exe sha256, options, seeds, timings).
Exit 0 only when every check passed (0 illegal, 0 crashes, 0 time losses, 0 missing bestmoves, 0 errors, echo OK,
stop stress OK). A STOP file in --out (or --stop-file) ends the run cooperatively between games (verdict PARTIAL,
exit 2, when nothing failed before the stop; the stress part is skipped).

usage: smoke_ab.py <exe> --name <label> [--exe-off <exe>] [--opt Name=Value ...] --out <dir> [--expect-echo none]
                [--games 200] [--tc 5+0.05] [--concurrency 3] [--seed 1] [--max-plies 400] [--book <pgn>]
"""
import argparse
import datetime
import hashlib
import io
import json
import os
import queue
import random
import re
import subprocess
import sys
import threading
import time

import chess
import chess.pgn

BELOW_NORMAL = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
DEFAULT_BOOK = "C:/Users/Administrator/grok-pc/coder-fuzz/8moves_v3.pgn"
BASE_OPTIONS = [("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")]   # R5D: Threads set from --threads in main()


def vienna_now():
    # PC clock runs 9 h ahead of real UTC (see REPORT.md time base); Vienna (CET) = real UTC + 1 h.
    return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=8)).strftime("%H:%M:%S Vienna")


class EngineDied(Exception):
    pass


class Engine:
    def __init__(self, exe, label, options):
        self.exe, self.label, self.options = exe, label, list(options)
        self.restarts = 0
        self.start()

    def start(self):
        self.lines = queue.Queue()
        self.p = subprocess.Popen([self.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1, creationflags=BELOW_NORMAL)
        threading.Thread(target=self._read, args=(self.p, self.lines), daemon=True).start()
        self.send("uci")
        if self.expect("uciok", 20)[0] is None:
            raise EngineDied(f"{self.label}: no uciok")
        for name, value in BASE_OPTIONS + self.options:
            self.send(f"setoption name {name} value {value}")
        self.sync()

    @staticmethod
    def _read(p, lines):
        for line in p.stdout:
            lines.put(line.rstrip("\n"))
        lines.put(None)

    def send(self, s):
        try:
            self.p.stdin.write(s + "\n")
            self.p.stdin.flush()
        except (BrokenPipeError, OSError, ValueError) as e:
            raise EngineDied(f"{self.label}: write failed ({e}); exit code {self.p.poll()}")

    def expect(self, prefix, timeout):
        """Lines until one starts with prefix: (line or None on timeout, all lines seen)."""
        deadline = time.monotonic() + timeout
        seen = []
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None, seen
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty:
                return None, seen
            if line is None:
                raise EngineDied(f"{self.label}: process exited (code {self.p.poll()}); last lines {seen[-3:]}")
            seen.append(line)
            if line.startswith(prefix):
                return line, seen

    def sync(self, timeout=20):
        self.send("isready")
        line, seen = self.expect("readyok", timeout)
        if line is None:
            raise EngineDied(f"{self.label}: no readyok within {timeout} s")
        return seen

    def restart(self):
        self.restarts += 1
        try:
            if self.p.poll() is None:
                self.p.kill()   # only this runner's own hung child engine
                self.p.wait(timeout=10)
        except Exception:
            pass
        self.start()

    def quit(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            try:
                self.p.kill()
            except Exception:
                pass


def load_epd(path, count, seed):
    fens = []
    for line in open(path, encoding="utf-8"):
        line = line.split("|")[0].strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        fen = " ".join(fields[:6]) if len(fields) >= 6 and fields[4].isdigit() else " ".join(fields[:4]) + " 0 1"
        chess.Board(fen)  # raises on a bad FEN
        fens.append(fen)
    rng = random.Random(seed)
    picks = rng.sample(range(len(fens)), min(count, len(fens)))
    return [{"index": i, "fen": fens[i], "moves": []} for i in picks], len(fens)


def position_command(opening, moves):
    base = f"position fen {opening['fen']}" if opening.get("fen") else "position startpos"
    return base + (" moves " + " ".join(moves) if moves else "")


def load_openings(path, count, seed):
    text = open(path, encoding="utf-8", errors="replace").read()
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip() and not b.lstrip().startswith("[")]
    rng = random.Random(seed)
    picks = rng.sample(range(len(blocks)), count)
    openings = []
    for i in picks:
        game = chess.pgn.read_game(io.StringIO(blocks[i]))
        board = game.board()
        moves = []
        for move in game.mainline_moves():
            moves.append(move.uci())
            board.push(move)
        openings.append({"index": i, "moves": moves})
    return openings, len(blocks)


class Stats:
    def __init__(self):
        self.lock = threading.Lock()
        self.games = []
        self.failures = {"illegal": [], "crash": [], "time_loss": [], "missing_bestmove": [], "error_line": [],
                         "echo": []}
        self.near_flags = 0
        self.moves = 0
        self.tbhits = {"on": 0, "off": 0}    # R5C: sum over moves of the last tbhits value of the mover
        self.tb_moves = {"on": 0, "off": 0}  # R5C: moves whose search reported tbhits > 0
        self.mate_moves = {"on": 0, "off": 0}  # R5D: moves whose last score line was "score mate N"
        self.mate_finishes = {"on": 0, "off": 0}  # R5D: games won by mate

    def fail(self, kind, detail):
        with self.lock:
            self.failures[kind].append(detail)


def play_game(gid, opening, on, off, on_white, args, stats, expect_echo):
    white, black = (on, off) if on_white else (off, on)
    base_ms, inc_ms = args.base_ms, args.inc_ms
    board = chess.Board(opening["fen"]) if opening.get("fen") else chess.Board()
    for m in opening["moves"]:
        board.push_uci(m)
    moves = list(opening["moves"])
    clocks = {chess.WHITE: float(base_ms), chess.BLACK: float(base_ms)}
    result, termination = None, None
    for eng in (white, black):
        try:
            eng.send("ucinewgame")
            eng.sync()
        except EngineDied as e:
            stats.fail("crash", {"game": gid, "engine": eng.label, "where": "ucinewgame", "detail": str(e)})
            eng.restart()
    while result is None:
        side = board.turn
        eng = white if side == chess.WHITE else black
        try:
            eng.send(position_command(opening, moves))
            eng.send(f"go wtime {int(clocks[chess.WHITE])} btime {int(clocks[chess.BLACK])} winc {inc_ms} binc {inc_ms}")
            t0 = time.perf_counter()
            line, seen = eng.expect("bestmove", clocks[side] / 1000.0 + 3.0)
            elapsed = (time.perf_counter() - t0) * 1000.0
        except EngineDied as e:
            stats.fail("crash", {"game": gid, "engine": eng.label, "ply": board.ply(), "detail": str(e)})
            eng.restart()
            result, termination = ("0-1" if side == chess.WHITE else "1-0"), f"crash {eng.label}"
            break
        scores = [l for l in seen if l.startswith("info") and " score " in l]
        if scores and " score mate " in scores[-1]:
            with stats.lock:
                stats.mate_moves["on" if eng is on else "off"] += 1
        hits = [int(m.group(1)) for m in (re.search(r" tbhits (\d+)", l) for l in seen) if m]
        if hits:
            with stats.lock:
                side_key = "on" if eng is on else "off"
                stats.tbhits[side_key] += hits[-1]
                stats.tb_moves[side_key] += 1 if hits[-1] > 0 else 0
        for l in seen:
            if "ERROR" in l:
                stats.fail("error_line", {"game": gid, "engine": eng.label, "ply": board.ply(), "line": l})
        if expect_echo is not None:
            echoes = [l for l in seen if l.startswith("info string active:")]
            want = [f"info string active: {expect_echo}"] if (eng is on and expect_echo) else []
            if echoes != want:
                stats.fail("echo", {"game": gid, "engine": eng.label, "ply": board.ply(), "got": echoes, "want": want})
        if line is None:
            stats.fail("missing_bestmove", {"game": gid, "engine": eng.label, "ply": board.ply(),
                                            "clock_ms": int(clocks[side]), "last": seen[-3:]})
            try:
                eng.send("stop")
                late, _ = eng.expect("bestmove", 3.0)
            except EngineDied:
                late = None
            eng.restart()
            result, termination = ("0-1" if side == chess.WHITE else "1-0"), f"no bestmove {eng.label}"
            break
        token = line.split()[1] if len(line.split()) > 1 else ""
        try:
            move = chess.Move.from_uci(token)
        except ValueError:
            move = None
        if move is None or move not in board.legal_moves:
            stats.fail("illegal", {"game": gid, "engine": eng.label, "ply": board.ply(), "move": token,
                                   "fen": board.fen()})
            result, termination = ("0-1" if side == chess.WHITE else "1-0"), f"illegal move {token} by {eng.label}"
            break
        clocks[side] -= elapsed
        if clocks[side] < 0:
            stats.fail("time_loss", {"game": gid, "engine": eng.label, "ply": board.ply(),
                                     "overshoot_ms": round(-clocks[side], 1)})
            result, termination = ("0-1" if side == chess.WHITE else "1-0"), f"time loss {eng.label}"
            break
        if clocks[side] < 20:
            with stats.lock:
                stats.near_flags += 1
        clocks[side] += inc_ms
        board.push(move)
        moves.append(move.uci())
        with stats.lock:
            stats.moves += 1
        outcome = board.outcome(claim_draw=True)
        if outcome is not None:
            result, termination = outcome.result(), outcome.termination.name.lower()
            if outcome.termination == chess.Termination.CHECKMATE:
                with stats.lock:
                    stats.mate_finishes["on" if eng is on else "off"] += 1
        elif board.ply() >= args.max_plies:
            result, termination = "1/2-1/2", f"adjudicated draw at ply {args.max_plies}"
    game = chess.pgn.Game()
    game.headers["Event"] = f"r5d smoke {args.name}"
    game.headers["Round"] = str(gid + 1)
    game.headers["White"] = white.label
    game.headers["Black"] = black.label
    game.headers["Result"] = result
    game.headers["Termination"] = termination
    game.headers["Opening"] = f"{os.path.basename(args.epd or args.book)} #{opening['index']}"
    if opening.get("fen"):
        game.headers["FEN"] = opening["fen"]
        game.headers["SetUp"] = "1"
    game.headers["TimeControl"] = f"{base_ms / 1000:g}+{inc_ms / 1000:g}"
    node = game
    if opening.get("fen"):
        game.setup(chess.Board(opening["fen"]))
        node = game
    for m in moves:
        node = node.add_variation(chess.Move.from_uci(m))
    on_score = {"1-0": 1.0, "0-1": 0.0, "1/2-1/2": 0.5}[result]
    if not on_white:
        on_score = 1.0 - on_score
    with stats.lock:
        stats.games.append({"game": gid, "on_white": on_white, "result": result, "termination": termination,
                            "plies": len(moves), "on_score": on_score, "pgn": str(game)})


def stop_stress(exe, options, expect_echo, openings, iterations, seed):
    rng = random.Random(seed)
    eng = Engine(exe, "ON-stop", options)
    problems = []
    done = 0
    for i in range(iterations):
        opening = openings[i % len(openings)]
        moves = opening["moves"]
        board = chess.Board(opening["fen"]) if opening.get("fen") else chess.Board()
        for m in moves:
            board.push_uci(m)
        try:
            for kind, go in (("infinite", "go infinite"), ("movetime", "go movetime 300")):
                eng.send(position_command(opening, moves))
                eng.send(go)
                time.sleep(rng.uniform(0.010, 0.150))
                eng.send("stop")
                line, seen = eng.expect("bestmove", 3.0)
                if line is None:
                    problems.append({"iteration": i, "kind": kind, "problem": "no bestmove within 3 s after stop"})
                    eng.restart()
                    continue
                token = line.split()[1] if len(line.split()) > 1 else ""
                if chess.Move.from_uci(token) not in board.legal_moves if re.fullmatch(r"[a-h][1-8][a-h][1-8][qrbn]?", token) else True:
                    problems.append({"iteration": i, "kind": kind, "problem": f"illegal bestmove {token}"})
                if any("ERROR" in l for l in seen):
                    problems.append({"iteration": i, "kind": kind, "problem": "ERROR line", "lines": seen[-3:]})
                if expect_echo is not None:
                    echoes = [l for l in seen if l.startswith("info string active:")]
                    want = [f"info string active: {expect_echo}"] if expect_echo else []
                    if echoes != want:
                        problems.append({"iteration": i, "kind": kind, "problem": "echo", "got": echoes})
            extra = [l for l in eng.sync(10) if l.startswith("bestmove")]
            if extra:
                problems.append({"iteration": i, "problem": f"extra bestmove after stop: {extra}"})
            done += 1
        except EngineDied as e:
            problems.append({"iteration": i, "problem": f"engine died: {e}"})
            eng.restart()
    eng.quit()
    return {"iterations": iterations, "completed": done, "problems": problems, "restarts": eng.restarts}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--name", required=True)
    ap.add_argument("--opt", action="append", default=[], help="Name=Value for the ON side")
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect-echo", default=None,
                    help="expected 'info string active:' payload of the ON side (default: the --opt list)")
    ap.add_argument("--games", type=int, default=200)
    ap.add_argument("--tc", default="5+0.05")
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--max-plies", type=int, default=400)
    ap.add_argument("--book", default=DEFAULT_BOOK)
    ap.add_argument("--stop-iterations", type=int, default=50)
    ap.add_argument("--stop-file", default=None)
    ap.add_argument("--exe-off", default=None, help="R5B: exe of the OFF side (default: the ON exe)")
    ap.add_argument("--epd", default=None, help="R5C: FEN/EPD openings instead of the PGN book")
    ap.add_argument("--threads", type=int, default=2, help="R5D: Threads of both sides")
    args = ap.parse_args()
    BASE_OPTIONS[0] = ("Threads", str(args.threads))
    exe_off = args.exe_off or args.exe
    base, _, inc = args.tc.partition("+")
    args.base_ms, args.inc_ms = int(float(base) * 1000), int(float(inc or 0) * 1000)
    options = [tuple(o.split("=", 1)) for o in args.opt]
    expect_echo = " ".join(f"{k}={v}" for k, v in options) if args.expect_echo is None else args.expect_echo
    if args.expect_echo == "none":
        expect_echo = None
    os.makedirs(args.out, exist_ok=True)
    stop_file = args.stop_file or os.path.join(args.out, "STOP")
    sha = hashlib.sha256(open(args.exe, "rb").read()).hexdigest()
    sha_off = hashlib.sha256(open(exe_off, "rb").read()).hexdigest()
    if args.epd:
        openings, book_size = load_epd(args.epd, (args.games + 1) // 2, args.seed)
    else:
        openings, book_size = load_openings(args.book, (args.games + 1) // 2, args.seed)
    stats = Stats()
    started, t_start = vienna_now(), time.monotonic()
    print(f"[{started}] {args.name}: {args.games} games {args.tc} conc {args.concurrency}, ON = {options}", flush=True)

    jobs = queue.Queue()
    for gid in range(args.games):
        jobs.put(gid)

    def worker(w):
        on = Engine(args.exe, f"ON {' '.join(args.opt)}", options)
        off = Engine(exe_off, "OFF", [])
        while not os.path.exists(stop_file):
            try:
                gid = jobs.get_nowait()
            except queue.Empty:
                break
            play_game(gid, openings[gid // 2], on, off, gid % 2 == 0, args, stats, expect_echo)
            n = len(stats.games)
            if n % 20 == 0:
                print(f"[{vienna_now()}] {args.name}: {n}/{args.games} games, failures "
                      f"{ {k: len(v) for k, v in stats.failures.items()} }", flush=True)
        with stats.lock:
            stats.restarts = getattr(stats, "restarts", 0) + on.restarts + off.restarts
        on.quit()
        off.quit()

    threads = [threading.Thread(target=worker, args=(w,)) for w in range(args.concurrency)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    games_s = time.monotonic() - t_start
    stopped_early = os.path.exists(stop_file)
    stress = None if stopped_early else stop_stress(args.exe, options, expect_echo, openings, args.stop_iterations,
                                                    args.seed + 1)

    stats.games.sort(key=lambda g: g["game"])
    with open(os.path.join(args.out, "games.pgn"), "w", newline="\n") as f:
        for g in stats.games:
            f.write(g["pgn"] + "\n\n")
    terminations = {}
    for g in stats.games:
        key = re.sub(r" (ON|OFF).*$", "", g["termination"])
        terminations[key] = terminations.get(key, 0) + 1
    counts = {k: len(v) for k, v in stats.failures.items()}
    ok = (len(stats.games) == args.games and all(v == 0 for v in counts.values())
          and stress is not None and not stress["problems"])
    # A run ended by the STOP file with no failure so far is PARTIAL (fewer games, no stress run), not FAIL.
    clean = all(v == 0 for v in counts.values()) and (stress is None or not stress["problems"])
    verdict = "PASS" if ok else ("PARTIAL" if stopped_early and clean else "FAIL")
    summary = {
        "name": args.name, "exe": args.exe, "exe_sha256": sha, "exe_off": exe_off, "exe_off_sha256": sha_off,
        "on_options": args.opt, "expect_echo": expect_echo,
        "tc": args.tc, "concurrency": args.concurrency, "threads_per_engine": args.threads, "hash_mb": 16,
        "own_book": False, "moves_with_mate_score": stats.mate_moves, "mate_finishes": stats.mate_finishes,
        "priority": "BelowNormal", "book": args.book, "book_games": book_size, "seed": args.seed,
        "opening_indices": [o["index"] for o in openings], "max_plies": args.max_plies,
        "games_planned": args.games, "games_played": len(stats.games), "moves": stats.moves,
        "avg_plies": round(sum(g["plies"] for g in stats.games) / max(1, len(stats.games)), 1),
        "terminations": terminations,
        "on_score_not_elo": {"points": sum(g["on_score"] for g in stats.games), "games": len(stats.games),
                             "note": f"crash smoke at {args.tc}; not a strength measurement"},
        "failure_counts": counts, "failures": stats.failures, "near_flags_under_20ms": stats.near_flags,
        "tbhits": stats.tbhits, "moves_with_tbhits": stats.tb_moves, "epd": args.epd,
        "engine_restarts": getattr(stats, "restarts", 0), "stop_stress": stress,
        "started": started, "finished": vienna_now(), "games_wall_s": round(games_s, 1),
        "stopped_early": stopped_early, "verdict": verdict,
    }
    with open(os.path.join(args.out, "summary.json"), "w", newline="\n") as f:
        json.dump(summary, f, indent=1)
    print(f"[{vienna_now()}] {args.name}: {summary['verdict']} games {len(stats.games)}/{args.games} "
          f"failures {counts} stop-stress "
          f"{'skipped' if stress is None else str(stress['completed']) + '/' + str(stress['iterations']) + ' problems ' + str(len(stress['problems']))} "
          f"avg plies {summary['avg_plies']} wall {games_s:.0f} s", flush=True)
    sys.exit(0 if ok else (2 if verdict == "PARTIAL" else 1))


main()
