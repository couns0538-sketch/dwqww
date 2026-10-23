#!/usr/bin/env python3
"""Forge NNUE self-play. Python 3.10+; pip install python-chess psutil.

Scores are side-to-move cp; results are WHITE's result. Only completed games
are exported. UCI uses a growing `position startpos moves ...` history.
The persistent SQLite hash set and output directory must be kept together.
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import multiprocessing as mp
import os
from pathlib import Path
import queue
import random
import re
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import uuid

import chess
import chess.engine
import psutil

DEFAULT_ENGINE = r"C:\Users\Administrator\grok-pc\forge.exe"
WINDOWS = sys.platform == "win32"
# Shared statistics: completed games, eligible candidates, accumulated search
# seconds, active go timestamp, attempts, worker start timestamp.
GAMES, CANDIDATES, SEARCH, ACTIVE, ATTEMPTS, STARTED = range(6)
FILE_RE = re.compile(r"^forge_selfplay_(\d+)\.txt(?:\..*)?$")


def position_hash(fen):
    """128-bit identity: piece placement, turn, castling and EP; no counters."""
    return hashlib.blake2b(" ".join(fen.split()[:4]).encode("ascii"),
                           digest_size=16).digest()


def publish_new(temp, target):
    """Publish without replacing an existing target."""
    if WINDOWS:
        os.rename(temp, target)  # Windows rename fails if target already exists.
    else:
        os.link(temp, target)  # POSIX rename would replace; link does not.
        Path(temp).unlink()


def checksum_file(path):
    digest = hashlib.md5()
    with open(path, "rb") as src:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def seal_checksum(path, digest=None):
    target = path.with_suffix(path.suffix + ".md5")
    if target.exists():
        return
    temp = target.with_name(target.name + ".tmp-" + uuid.uuid4().hex)
    try:
        with open(temp, "xb") as dst:
            dst.write(f"{digest or checksum_file(path)}  {path.name}\n".encode("ascii"))
            dst.flush()
            os.fsync(dst.fileno())
        publish_new(temp, target)
    finally:
        temp.unlink(missing_ok=True)


class DirectoryLock:
    """OS lock is automatically released even after a process crash."""
    def __init__(self, directory):
        self.file = open(directory / "forge_selfplay.lock", "a+b")
        self.file.seek(0, os.SEEK_END)
        if not self.file.tell():
            self.file.write(b"0")
            self.file.flush()
        self.file.seek(0)
        try:
            if WINDOWS:
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.file.close()
            raise RuntimeError("Another writer is using this output directory.")

    def close(self):
        self.file.close()


class OutputStore:
    """Single writer, persistent on-disk hash set, recoverable active files.

    A transaction inserts hashes, writes/fsyncs data, then commits its offset.
    On crash, only an uncommitted .part tail is rolled back. Finished .txt
    files are never changed. Keeping the DB avoids rescanning old data.
    """
    def __init__(self, directory, lines_per_file=10_000_000):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = DirectoryLock(self.directory)
        self.file = None
        self.failed = False
        self.limit = lines_per_file
        self.db = None
        try:
            self.db = sqlite3.connect(self.directory / "forge_seen_hashes.sqlite3")
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
            self.db.execute("PRAGMA cache_size=-16384")
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS hashes
                  (hash BLOB PRIMARY KEY) WITHOUT ROWID;
                CREATE TABLE IF NOT EXISTS files
                  (name TEXT PRIMARY KEY, bytes INTEGER NOT NULL,
                   lines INTEGER NOT NULL);
            """)
            self.recover()
            indices = [int(m.group(1)) for p in self.directory.iterdir()
                       if (m := FILE_RE.match(p.name))]
            indices += [int(FILE_RE.match(row[0]).group(1))
                        for row in self.db.execute("SELECT name FROM files")]
            self.next_number = max(indices, default=0) + 1
        except BaseException:
            if self.db is not None:
                self.db.close()
            self.lock.close()
            raise

    def recover(self):
        # Restore the last durable transaction boundary of active temporary data.
        for part in sorted(self.directory.glob("forge_selfplay_*.txt.part")):
            final = part.with_suffix("")
            row = self.db.execute("SELECT bytes, lines FROM files WHERE name=?",
                                  (final.name,)).fetchone()
            if final.exists():
                # Crash between hard-link publication and removal of .part.
                if not os.path.samefile(part, final):
                    raise RuntimeError(f"Conflicting temporary file: {part}")
                part.unlink()
            elif row is not None:
                if part.stat().st_size < row[0]:
                    raise RuntimeError(f"Data shorter than committed offset: {part}")
                with open(part, "r+b") as dst:
                    dst.truncate(row[0])
                    dst.flush()
                    os.fsync(dst.fileno())
                publish_new(part, final)
            else:
                # Created before its first DB transaction committed: no data is
                # durable yet. Preserve it, reserving its original number.
                abandoned = part.with_name(part.name + ".uncommitted-" + uuid.uuid4().hex)
                part.rename(abandoned)
        known = dict((name, (size, lines)) for name, size, lines in
                     self.db.execute("SELECT name, bytes, lines FROM files"))
        for name in known:
            if not (self.directory / name).exists():
                raise RuntimeError(f"Missing indexed data file: {name}; restore it with its DB.")
        # Also import pre-existing finished files, e.g. data made before the DB
        # existed. This is a one-time streaming scan, not an in-memory FEN set.
        for path in sorted(self.directory.glob("forge_selfplay_*.txt")):
            if not re.fullmatch(r"forge_selfplay_\d+\.txt", path.name):
                continue
            size = path.stat().st_size
            if path.name in known:
                if size != known[path.name][0]:
                    raise RuntimeError(f"Indexed data was modified: {path}")
            else:
                count = 0
                with self.db:
                    with open(path, "rb") as src:
                        for raw in src:
                            if not raw.endswith(b"\n"):
                                raise RuntimeError(f"Unterminated line in existing file: {path}")
                            fen, score, result = raw.decode("ascii").strip().split(" | ")
                            if len(fen.split()) != 6 or result not in ("0.0", "0.5", "1.0"):
                                raise RuntimeError(f"Invalid existing record in {path}")
                            int(score)
                            self.db.execute("INSERT OR IGNORE INTO hashes VALUES (?)",
                                            (position_hash(fen),))
                            count += 1
                    self.db.execute("INSERT INTO files VALUES (?,?,?)", (path.name, size, count))
            seal_checksum(path)

    def _open(self):
        while True:
            self.path = self.directory / f"forge_selfplay_{self.next_number:03d}.txt"
            self.next_number += 1
            if self.path.exists() or self.path.with_suffix(".txt.md5").exists():
                continue
            self.part = self.path.with_suffix(".txt.part")
            try:
                self.file = open(self.part, "xb")
                break
            except FileExistsError:
                continue
        self.size = self.lines = 0
        self.digest = hashlib.md5()

    def finish_file(self):
        if self.file is None:
            return
        self.file.flush()
        os.fsync(self.file.fileno())
        self.file.close()
        self.file = None
        publish_new(self.part, self.path)
        seal_checksum(self.path, self.digest.hexdigest())
        print(f"Finished {self.path.name}: {self.lines:,} lines", flush=True)

    def append(self, records):
        """records = iterable of (full FEN, STM cp, White result); return kept."""
        kept = 0
        iterator = iter(records)
        exhausted = False
        try:
            while not exhausted:
                payload = bytearray()
                added = 0
                with self.db:
                    for fen, cp, result in iterator:
                        inserted = self.db.execute(
                            "INSERT OR IGNORE INTO hashes VALUES (?)",
                            (position_hash(fen),)).rowcount
                        if not inserted:
                            continue
                        if self.file is None:
                            self._open()
                        payload.extend(f"{fen} | {int(cp)} | {result:.1f}\n".encode("ascii"))
                        added += 1
                        if self.lines + added == self.limit:
                            break
                    else:
                        exhausted = True
                    if added:
                        self.file.write(payload)
                        self.file.flush()
                        os.fsync(self.file.fileno())  # Data must precede DB commit.
                        new_size, new_lines = self.size + len(payload), self.lines + added
                        self.db.execute("INSERT OR REPLACE INTO files VALUES (?,?,?)",
                                        (self.path.name, new_size, new_lines))
                if added:
                    self.digest.update(payload)
                    self.size, self.lines = new_size, new_lines
                    kept += added
                    if self.lines == self.limit:
                        self.finish_file()
        except BaseException:
            self.failed = True
            raise
        return kept

    def close(self):
        try:
            if not self.failed:
                self.finish_file()
            elif self.file is not None:
                self.file.close()  # Leave .part for transaction recovery.
            self.db.close()
        finally:
            self.lock.close()


def parse_cpus(value):
    cpus = set()
    try:
        for part in value.split(","):
            ends = part.split("-")
            if len(ends) == 1:
                cpus.add(int(part))
            elif len(ends) == 2:
                a, b = map(int, ends)
                if a > b:
                    raise ValueError
                cpus.update(range(a, b + 1))
            else:
                raise ValueError
        if not cpus or min(cpus) < 0:
            raise ValueError
    except ValueError:
        raise argparse.ArgumentTypeError("Use logical CPU IDs such as 12-15 or 0,2,4,6")
    return sorted(cpus)


def constrain_process(process, cpus):
    process.cpu_affinity(cpus)
    process.nice(psutil.IDLE_PRIORITY_CLASS if WINDOWS else 19)
    if sorted(process.cpu_affinity()) != sorted(cpus):
        raise RuntimeError(f"Could not set affinity to {cpus} for PID {process.pid}")
    if WINDOWS and process.nice() != psutil.IDLE_PRIORITY_CLASS:
        raise RuntimeError(f"Could not set IDLE priority for PID {process.pid}")


class MeteredUCI(chess.engine.UciProtocol):
    """Measure go-to-bestmove wall time, excluding position setup and disk I/O."""
    def __init__(self):
        super().__init__()
        self.stats = None
        self.score_is_bound = False

    def send_line(self, line):
        if line == "go" or line.startswith("go "):
            self.score_is_bound = False
            if self.stats is not None:
                with self.stats.get_lock():
                    self.stats[ACTIVE] = time.monotonic()
        super().send_line(line)

    def line_received(self, line):
        # python-chess merges info dictionaries; an old aspiration bound flag
        # can survive a later exact score. Track the LAST score line ourselves.
        words = line.split()
        if words[:1] == ["info"] and "score" in words and words[1:2] != ["string"]:
            self.score_is_bound = "lowerbound" in words or "upperbound" in words
        if self.stats is not None and line.startswith("bestmove "):
            with self.stats.get_lock():
                if self.stats[ACTIVE]:
                    self.stats[SEARCH] += time.monotonic() - self.stats[ACTIVE]
                    self.stats[ACTIVE] = 0.0
        super().line_received(line)


def stop_engine(engine):
    if engine is None:
        return
    try:
        process = psutil.Process(engine.transport.get_pid())
    except psutil.NoSuchProcess:
        process = None
    try:
        engine.timeout = 3.0
        engine.quit()
    except Exception:
        engine.close()
    finally:
        if process is not None:
            try:
                process.wait(timeout=3)
            except psutil.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
            except psutil.NoSuchProcess:
                pass


def terminal_result(board, max_ply):
    # Actual repetition/halfmove thresholds, not a claim based on a future move.
    if board.is_checkmate():
        return 0.0 if board.turn == chess.WHITE else 1.0
    if (board.is_stalemate() or board.is_insufficient_material()
            or board.is_repetition(3) or board.is_fifty_moves()
            or board.ply() >= max_ply):
        return 0.5
    return None


def decisive_side(score, turn, threshold):
    """Return a winning COLOR, so alternating STM scores don't break streaks."""
    white = score if turn == chess.WHITE else -score
    if white >= chess.engine.Cp(threshold):
        return chess.WHITE
    if white <= chess.engine.Cp(-threshold):
        return chess.BLACK
    return None


def eligible_score(board, move, score, max_cp=3000):
    if (board.is_check() or board.is_capture(move) or move.promotion
            or score.is_mate()):
        return None
    cp = score.score()
    return cp if cp is not None and abs(cp) <= max_cp else None


def play_game(engine, args, rng, stop, record_hook=None):
    board = chess.Board()  # Keep the complete stack; never replace by FEN.
    for _ in range(args.opening_plies):
        if terminal_result(board, args.max_ply) is not None or stop.is_set():
            return None
        board.push(rng.choice(list(board.legal_moves)))
    game_token = object()  # python-chess sends ucinewgame once for this game.
    if terminal_result(board, args.max_ply) is not None:
        return None  # An opening that ended the game produces no samples.
    limit = (chess.engine.Limit(depth=args.depth) if args.depth is not None
             else chess.engine.Limit(nodes=args.nodes))
    records, winner, streak = [], None, 0
    while True:
        result = terminal_result(board, args.max_ply)
        if result is not None:
            return records, result
        if stop.is_set():
            return None
        reply = engine.play(board, limit, game=game_token,
                            info=chess.engine.INFO_SCORE, ponder=False)
        if stop.is_set():
            return None  # A stopped search must not label even its final move.
        if reply.move is None or reply.move not in board.legal_moves:
            raise RuntimeError("Engine did not return a legal best move.")
        if "score" not in reply.info:
            raise RuntimeError("Engine returned no score; cannot label this game.")
        score = reply.info["score"].pov(board.turn)
        bounded = getattr(getattr(engine, "protocol", None), "score_is_bound", False)
        cp = None if bounded else eligible_score(board, reply.move, score, args.max_score)
        if cp is not None:
            records.append((board.fen(en_passant="fen"), cp))
            if record_hook is not None:
                record_hook({"fen": board.fen(en_passant="fen"), "score_cp_stm": cp,
                             "ply": board.ply(), "bestmove": reply.move.uci()})
        side = None if bounded else decisive_side(score, board.turn, args.adjudicate_cp)
        streak = streak + 1 if side is not None and side == winner else (1 if side is not None else 0)
        winner = side
        board.push(reply.move)
        result = terminal_result(board, args.max_ply)
        if result is not None:
            return records, result
        if streak >= args.adjudicate_plies:
            return records, 1.0 if winner == chess.WHITE else 0.0


def worker(worker_id, args, stop, output, stats):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    logging.getLogger("chess.engine").setLevel(logging.ERROR)
    engine = None
    watcher = None
    worker_done = threading.Event()
    with stats.get_lock():
        stats[STARTED] = time.monotonic()
    try:
        constrain_process(psutil.Process(), args.cpus)
        extra = {"creationflags": subprocess.IDLE_PRIORITY_CLASS} if WINDOWS else {}
        engine = chess.engine.SimpleEngine.popen(
            MeteredUCI, [args.engine], timeout=args.engine_timeout,
            setpgrp=True, cwd=str(Path(args.engine).parent), **extra)
        engine.protocol.stats = stats
        constrain_process(psutil.Process(engine.transport.get_pid()), args.cpus)
        for option in ("Threads", "Hash"):
            if option not in engine.options:
                raise RuntimeError(f"Engine lacks required UCI option {option}")
        engine.configure({"Threads": 1, "Hash": 16})
        def interrupt_search():
            # Never leave a dead process waiting inside multiprocessing.Event:
            # its Condition notification handshake could block the parent.
            while not worker_done.wait(0.05):
                if stop.is_set():
                    break
            else:
                return
            def send_stop():
                try:
                    if not engine.returncode.done():
                        engine.protocol.send_line("stop")
                except (chess.engine.EngineError, RuntimeError):
                    pass  # The transport can close while the callback is queued.
            try:
                engine.protocol.loop.call_soon_threadsafe(send_stop)
            except RuntimeError:
                pass  # Already shut down after reaching a finite game limit.

        watcher = threading.Thread(target=interrupt_search, daemon=True)
        watcher.start()
        output.put(("ready", worker_id, engine.transport.get_pid()))
        rng = random.Random(None if args.seed is None else args.seed + worker_id)
        while not stop.is_set():
            with stats.get_lock():
                if args.games_per_worker and stats[GAMES] >= args.games_per_worker:
                    break
                stats[ATTEMPTS] += 1
            completed = play_game(engine, args, rng, stop)
            if completed is None:
                continue
            records, result = completed
            with stats.get_lock():
                stats[GAMES] += 1
                stats[CANDIDATES] += len(records)
            output.put(("game", worker_id, (records, result)))
    except BaseException as exc:
        output.put(("error", worker_id, f"{type(exc).__name__}: {exc}"))
        stop.set()
    finally:
        worker_done.set()
        if watcher is not None:
            watcher.join(timeout=1)
        try:
            stop_engine(engine)
        except Exception as exc:
            output.put(("error", worker_id, f"Engine shutdown: {exc}"))
        with stats.get_lock():
            if stats[ACTIVE]:
                stats[SEARCH] += time.monotonic() - stats[ACTIVE]
                stats[ACTIVE] = 0
        output.put(("done", worker_id, None))
        output.close()
        output.join_thread()


def progress(stats, written, started):
    now = time.monotonic()
    elapsed = max(now - started, 0.001)
    games = candidates = 0
    search = 0.0
    print(f"\nElapsed {elapsed / 3600:.3f} h; positions below are saved after deduplication.", flush=True)
    for i, item in enumerate(stats):
        with item.get_lock():
            values = list(item)
        searching = values[SEARCH] + (now - values[ACTIVE] if values[ACTIVE] else 0)
        games += int(values[GAMES])
        candidates += int(values[CANDIDATES])
        search += searching
        print(f"Worker {i + 1}: games={int(values[GAMES]):,} "
              f"positions={written[i]:,} positions/h={written[i] * 3600 / elapsed:,.0f} "
              f"search={100 * searching / elapsed:.1f}%", flush=True)
    print(f"TOTAL: games={games:,} positions={sum(written):,} "
          f"positions/h={sum(written) * 3600 / elapsed:,.0f} "
          f"search={100 * search / (len(stats) * elapsed):.1f}% "
          f"eligible={candidates:,}; search is go-to-bestmove wall-time duty cycle.", flush=True)


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", default=DEFAULT_ENGINE)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--cpus", type=parse_cpus, default=parse_cpus("12-15"))
    budget = parser.add_mutually_exclusive_group()
    budget.add_argument("--nodes", type=int, default=5000)
    budget.add_argument("--depth", type=int)
    parser.add_argument("--out", default="out")
    parser.add_argument("--lines-per-file", type=int, default=10_000_000)
    parser.add_argument("--opening-plies", type=int, default=8)
    parser.add_argument("--max-ply", type=int, default=300)
    parser.add_argument("--adjudicate-cp", type=int, default=2000)
    parser.add_argument("--adjudicate-plies", type=int, default=4)
    parser.add_argument("--max-score", type=int, default=3000)
    parser.add_argument("--progress-seconds", type=float, default=60)
    parser.add_argument("--engine-timeout", type=float, default=60)
    parser.add_argument("--games-per-worker", type=int, default=0,
                        help="0 = continuous; useful for a finite smoke test")
    parser.add_argument("--seed", type=int)
    args = parser.parse_args(argv)
    for name in ("workers", "nodes", "lines_per_file", "adjudicate_cp", "adjudicate_plies",
                 "max_score", "progress_seconds", "engine_timeout"):
        if getattr(args, name) <= 0:
            parser.error(f"--{name.replace('_', '-')} must be positive")
    if args.depth is not None and args.depth <= 0:
        parser.error("--depth must be positive")
    if args.opening_plies < 0 or args.max_ply <= args.opening_plies or args.games_per_worker < 0:
        parser.error("Require 0 <= opening-plies < max-ply and games-per-worker >= 0")
    args.engine = str(Path(args.engine).expanduser().resolve())
    if not Path(args.engine).is_file():
        parser.error(f"Engine not found: {args.engine}")
    available = psutil.Process().cpu_affinity()
    if not set(args.cpus) <= set(available):
        parser.error(f"Requested CPUs {args.cpus}; available logical CPU IDs are {available}")
    return args


def main(argv=None):
    args = arguments(argv)
    store = OutputStore(args.out, args.lines_per_file)
    ctx = mp.get_context("spawn")
    stop = ctx.Event()
    output = ctx.Queue(maxsize=max(4, args.workers * 2))
    stats = [ctx.Array("d", 6) for _ in range(args.workers)]
    processes, engines, done = [], {}, set()
    written = [0] * args.workers
    started, last_progress = time.monotonic(), time.monotonic()
    stopping_at, failed, interrupted = None, False, False

    def interrupt(signum, frame):
        nonlocal interrupted
        interrupted = True
        stop.set()

    old_handler = signal.signal(signal.SIGINT, interrupt)
    print(f"Forge: {args.workers} worker(s), CPUs {args.cpus}, Threads=1, Hash=16; "
          f"{'depth ' + str(args.depth) if args.depth else str(args.nodes) + ' nodes/move'}", flush=True)
    try:
        for i in range(args.workers):
            process = ctx.Process(target=worker, args=(i, args, stop, output, stats[i]),
                                  name=f"ForgeSelfplay-{i + 1}")
            process.start()
            processes.append(process)
        while len(done) < len(processes):
            try:
                kind, worker_id, payload = output.get(timeout=0.25)
                if kind == "game":
                    if not store.failed:
                        records, result = payload
                        try:
                            written[worker_id] += store.append((fen, cp, result) for fen, cp in records)
                        except Exception as exc:
                            print(f"Output error: {exc}", file=sys.stderr, flush=True)
                            failed = True
                            stop.set()
                elif kind == "ready":
                    try:
                        engines[worker_id] = psutil.Process(payload)
                    except psutil.NoSuchProcess:
                        pass  # An immediate engine crash will also send error/done.
                    print(f"Worker {worker_id + 1}: engine PID {payload}, affinity/priority set.", flush=True)
                elif kind == "error":
                    print(f"Worker {worker_id + 1} error: {payload}", file=sys.stderr, flush=True)
                    failed = True
                    stop.set()
                elif kind == "done":
                    done.add(worker_id)
            except queue.Empty:
                # A process that dies without its done message must not hang us.
                for i, process in enumerate(processes):
                    if process.exitcode is not None and i not in done:
                        done.add(i)
                        print(f"Worker {i + 1} exited unexpectedly ({process.exitcode}).", file=sys.stderr)
                        failed = True
                        stop.set()
            now = time.monotonic()
            if now - last_progress >= args.progress_seconds:
                progress(stats, written, started)
                last_progress = now
            if stop.is_set():
                if stopping_at is None:
                    stopping_at = now
                    print("Stopping: draining completed games and quitting engines...", flush=True)
                if now - stopping_at > args.engine_timeout + 15:
                    print("Shutdown timeout; stopping unresponsive children.", file=sys.stderr)
                    failed = True
                    break
    finally:
        stop.set()
        # Close only our own engine processes; psutil guards against PID reuse.
        for process in processes:
            process.join(timeout=0.1)
        for engine in engines.values():
            try:
                if engine.is_running():
                    engine.kill()
            except psutil.NoSuchProcess:
                pass
        for process in processes:
            if process.is_alive():
                process.terminate()
            process.join(timeout=5)
        output.close()
        output.join_thread()
        try:
            store.close()
        finally:
            signal.signal(signal.SIGINT, old_handler)
        progress(stats, written, started)
    print("Stopped cleanly." if not failed else "Stopped with errors; see messages above.", flush=True)
    return 1 if failed else (130 if interrupted else 0)


if __name__ == "__main__":
    mp.freeze_support()
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, sqlite3.Error, psutil.Error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
