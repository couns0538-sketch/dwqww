#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Fresh external-UCI games, immutable compressed chunks, whole-game partitions.

Scores here describe the generators, not the independent training teacher.
Every gzip JSONL line is one complete game; each retained sample explicitly
contains its game ID and partition. No interrupted game is ever published.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import gzip
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import queue
import random
import re
import signal
import subprocess
import sys
import threading
import time

import chess


SCHEMA = "forge-independent-teacher-games-v1"
OPTIONS = {"Threads": 1, "Hash": 16, "OwnBook": False}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def atomic_json(path, value):
    temp = path.with_name(path.name + ".part")
    with temp.open("wb") as stream:
        stream.write(encoded(value) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)
    if os.name != "nt":
        descriptor = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def game_identity(config_hash, index):
    return config_hash[:24] + ":" + str(index)


def split_for_game(game_id, seed, validation_fraction, audit_fraction):
    if not (0 < validation_fraction < 1 and 0 < audit_fraction < 1
            and validation_fraction + audit_fraction < 1):
        raise ValueError("Invalid whole-game partition fractions")
    value = int.from_bytes(hashlib.sha256(encoded([seed, game_id])).digest()[:8], "big") / 2**64
    return "audit" if value < audit_fraction else (
        "validation" if value < audit_fraction + validation_fraction else "train")


def pairing(index):
    # Half are shipped/shipped; half shipped/5101, with both cross-game colors.
    return (1, 0) if index % 4 == 3 else ((0, 1) if index % 4 == 1 else (0, 0))


def opening_for_game(seed, index, min_plies=8, max_plies=24):
    opening_seed = int.from_bytes(hashlib.sha256(encoded([seed, index, "opening-v1"])).digest()[:8], "big")
    rng, board, moves = random.Random(opening_seed), chess.Board(), []
    target = rng.randint(min_plies, max_plies)
    for _ in range(target):
        legal = list(board.legal_moves)
        if not legal or board.is_insufficient_material():
            break
        move = rng.choice(legal)
        moves.append(move.uci())
        board.push(move)
    return opening_seed, moves


def parse_score(line):
    if not line.startswith("info ") or line.startswith("info string "):
        return None
    match = re.search(r"(?:^| )score (cp|mate) (-?\d+)(?= |$)", line)
    if match is None:
        return None
    return {match[1]: int(match[2]), "bound": bool(re.search(r"\b(?:lowerbound|upperbound)\b", line))}


def eligible(board, move, score, score_cap):
    return ((not score or ("cp" in score and not score.get("bound", False) and abs(score["cp"]) <= score_cap))
            and not board.is_check()
            and not board.is_capture(move) and not move.promotion and not board.gives_check(move)
            and board.halfmove_clock < 100)


def repetition_key(board):
    return (board.pawns, board.knights, board.bishops, board.rooks, board.queens,
            board.kings, board.occupied_co[0], board.occupied_co[1], board.turn,
            board.castling_rights, board.ep_square if board.has_legal_en_passant() else None)


def terminal_result(board, max_ply, repetitions=None):
    # Natural mate has precedence even when the mating move meets a draw limit.
    if not any(board.generate_legal_moves()):
        return (0.0 if board.turn == chess.WHITE else 1.0, "checkmate") if board.is_check() else (.5, "stalemate")
    if board.is_insufficient_material():
        return .5, "insufficient_material"
    if (board.is_repetition(3) if repetitions is None else repetitions >= 3):
        return .5, "threefold_repetition"
    if board.halfmove_clock >= 100:
        return .5, "fifty_move_rule"
    if board.ply() >= max_ply:
        return .5, "adjudicated_max_ply_draw"
    return None


class HistoryWindow:
    """Discard only history made repetition-impossible by a pawn move/capture."""
    def __init__(self):
        self.fen, self.start_ply = None, 0

    def after_move(self, board, zeroing):
        if zeroing:
            self.fen, self.start_ply = board.fen(en_passant="fen"), board.ply()


class UciEngine:
    """One owned, persistent process. Bounded diagnostic tail, per-go fresh scores."""
    def __init__(self, path, timeout=15, on_spawn=None, extra_args=()):
        self.path, self.timeout, self.tail = str(path), timeout, deque(maxlen=128)
        self.lines = queue.Queue()
        self.process = subprocess.Popen([self.path, *extra_args], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True, encoding="ascii", errors="replace",
                                        bufsize=1, cwd=str(Path(path).parent), start_new_session=(os.name != "nt"))
        if on_spawn is not None:
            on_spawn(self.process.pid)
        self.reader = threading.Thread(target=self._read, args=(self.process.stdout, False), daemon=True)
        self.stderr_reader = threading.Thread(target=self._read, args=(self.process.stderr, True), daemon=True)
        self.reader.start()
        self.stderr_reader.start()
        try:
            self.send("uci")
            response = self.until("uciok")
            self.identity = [line for line in response if line.startswith("id ")]
            self.nested_pid = next((int(line.split()[-1]) for line in response
                                    if line.startswith("info string opponent_pid ")), None)
            advertised = {match[1] for line in response
                          if (match := re.match(r"option name (.*?) type ", line))}
            if not set(OPTIONS) <= advertised:
                raise RuntimeError("Generator engine lacks required Threads/Hash/OwnBook options")
            for name, value in OPTIONS.items():
                self.send(f"setoption name {name} value {str(value).lower()}")
            self.send("isready")
            self.until("readyok")
        except BaseException:
            self.close()
            raise

    def _read(self, stream, stderr):
        try:
            for line in stream:
                line = line.rstrip("\r\n")
                if stderr:
                    self.tail.append(["stderr", line])
                else:
                    self.lines.put(line)
        finally:
            if not stderr:
                self.lines.put(None)

    def send(self, line):
        self.tail.append(["send", line])
        self.process.stdin.write(line + "\n")
        self.process.stdin.flush()

    def until(self, terminal):
        deadline, output = time.monotonic() + self.timeout, []
        while True:
            try:
                line = self.lines.get(timeout=max(.001, deadline - time.monotonic()))
            except queue.Empty as error:
                raise RuntimeError("UCI timeout waiting for " + terminal) from error
            if line is None:
                raise RuntimeError(f"UCI EOF waiting for {terminal}; exit={self.process.poll()}")
            self.tail.append(["receive", (f"gamejson bytes={len(line)} sha256=" + hashlib.sha256(line.encode()).hexdigest())
                              if line.startswith("gamejson ") else line])
            output.append(line)
            if line == terminal or line.startswith(terminal + " "):
                return output
            if time.monotonic() >= deadline:
                raise RuntimeError("UCI deadline waiting for " + terminal)

    def new_game(self):
        self.send("ucinewgame")
        self.send("isready")
        self.until("readyok")

    def search(self, moves, nodes, history=None):
        history = history or HistoryWindow()
        suffix = moves[history.start_ply:]
        self.send(("position fen " + history.fen if history.fen else "position startpos")
                  + (" moves " + " ".join(suffix) if suffix else ""))
        self.send(f"go nodes {nodes}")
        score = None  # Never reuse a previous go's score or bound state.
        for line in self.until("bestmove"):
            parsed = parse_score(line) if line.startswith("info ") else None
            if parsed is not None:
                score = parsed
            if line.startswith("bestmove "):
                bestmove = line.split()[1]
        # Tiny generation budgets may finish before an iteration emits info.
        # Preserve absence explicitly; only the independent teacher labels it.
        return bestmove, score or {}

    def close(self):
        forced = False
        try:
            if self.process.poll() is None:
                try:
                    self.send("quit")
                    self.process.wait(timeout=3)
                except (BrokenPipeError, OSError, subprocess.TimeoutExpired):
                    forced = True
                    if os.name != "nt":
                        os.killpg(self.process.pid, signal.SIGKILL)
                    else:
                        self.process.kill()
                    self.process.wait(timeout=3)
        finally:
            self.reader.join(timeout=1)
            self.stderr_reader.join(timeout=1)
            nested_receipt = None
            while True:
                try:
                    line = self.lines.get_nowait()
                except queue.Empty:
                    break
                if line and line.startswith("info string opponent_closed "):
                    fields = line.split()
                    nested_receipt = {"pid": int(fields[3]), "returncode": int(fields[5]), "reaped": True}
            for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                stream.close()
        return {"pid": self.process.pid, "returncode": self.process.returncode,
                "reaped": self.process.poll() is not None, "forced_kill": forced,
                "engine_id": getattr(self, "identity", []), "nested_opponent": nested_receipt}


def play_native_game(index, config, engine, stop):
    opening_seed, opening = opening_for_game(config["seed"], index, *config["opening_plies"])
    white, black = pairing(index)
    command = (f"game {config['nodes']} {config['max_ply']} {config['score_cap']} {white} {black} {len(opening)}"
               + (" " + " ".join(opening) if opening else ""))
    engine.send(command)
    response = engine.until("gamejson")
    if stop.is_set():
        return None
    game = json.loads(response[-1][len("gamejson "):])
    if game["moves"][:len(opening)] != opening:
        raise RuntimeError("Native game altered the deterministic opening")
    identity = game_identity(config["config_sha256"], index)
    split = split_for_game(identity, config["split_seed"], config["validation_fraction"], config["audit_fraction"])
    game.update(game_id=identity, game_index=index, split=split, opening_seed=opening_seed,
                opening_plies=len(opening), engine_white_sha256=config["engines"][white]["sha256"],
                engine_black_sha256=config["engines"][black]["sha256"])
    for row in game["samples"]:
        if type(row["ply"]) is not int or not 0 <= row["ply"] < len(game["moves"]) or game["moves"][row["ply"]] != row["bestmove"]:
            raise RuntimeError("Native sample is not its recorded actual game move")
        engine_index = row.pop("engine_index")
        if engine_index not in (white, black):
            raise RuntimeError("Native sample engine identity differs")
        row.update(game_id=identity, game_index=index, split=split, result_white=game["result_white"],
                   engine_sha256=config["engines"][engine_index]["sha256"])
    return game


def play_game(index, config, engines, stop):
    opening_seed, moves = opening_for_game(config["seed"], index, *config["opening_plies"])
    board, repetitions, history = chess.Board(), Counter(), HistoryWindow()
    repetitions[repetition_key(board)] += 1
    for text in moves:
        move = chess.Move.from_uci(text)
        zeroing = board.is_zeroing(move)
        board.push(move)
        history.after_move(board, zeroing)
        repetitions[repetition_key(board)] += 1
    white, black = pairing(index)
    for engine in {engines[white], engines[black]}:
        engine.new_game()
    identity = game_identity(config["config_sha256"], index)
    split = split_for_game(identity, config["split_seed"], config["validation_fraction"], config["audit_fraction"])
    game = {"game_id": identity, "game_index": index, "split": split, "opening_seed": opening_seed,
            "opening_plies": len(moves), "moves": list(moves), "samples": [], "missing_score_positions": 0,
            "engine_white_sha256": config["engines"][white]["sha256"],
            "engine_black_sha256": config["engines"][black]["sha256"]}
    while True:
        terminal = terminal_result(board, config["max_ply"], repetitions[repetition_key(board)])
        if terminal is not None:
            game["result_white"], game["termination"] = terminal
            game["final_fen"] = board.fen(en_passant="fen")
            for row in game["samples"]:
                row["result_white"] = game["result_white"]
            return game
        if stop.is_set():
            return None
        engine_index = white if board.turn == chess.WHITE else black
        text, score = engines[engine_index].search(game["moves"], config["nodes"], history)
        if stop.is_set():
            return None
        try:
            move = chess.Move.from_uci(text)
        except ValueError as error:
            raise RuntimeError("Malformed engine bestmove: " + text) from error
        if not board.is_legal(move):
            raise RuntimeError("Illegal engine bestmove: " + text + " at " + board.fen())
        if not score:
            game["missing_score_positions"] += 1
        if eligible(board, move, score, config["score_cap"]):
            game["samples"].append({"game_id": identity, "game_index": index, "split": split,
                                    "fen": board.fen(en_passant="fen"), "ply": board.ply(),
                                    "bestmove": text, "score_cp_stm": score.get("cp"),
                                    "forge_score_missing": not bool(score),
                                    "engine_sha256": config["engines"][engine_index]["sha256"]})
        game["moves"].append(text)
        zeroing = board.is_zeroing(move)
        board.push(move)
        history.after_move(board, zeroing)
        repetitions[repetition_key(board)] += 1


class ChunkStore:
    """One writer; a manifest is the sole authoritative commit boundary."""
    def __init__(self, directory, config, chunk_games=256, resume=False):
        self.directory, self.config, self.chunk_games = Path(directory), config, chunk_games
        self.buffer, self.seen, self.next_index = [], set(), 0
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "manifest.json"
        if self.path.exists():
            if not resume:
                raise ValueError("Existing output requires explicit --resume")
            self.manifest = json.loads(self.path.read_text())
            if self.manifest["configuration"] != config or self.manifest["chunk_games"] != chunk_games:
                raise ValueError("Resume configuration differs from frozen configuration")
            trace = self.manifest.get("process_trace")
            if trace:
                path = self.directory / trace["path"]
                if sha256(path) != trace["sha256"]:
                    prefix_size = trace.get("bytes")
                    if type(prefix_size) is not int or path.stat().st_size < prefix_size:
                        raise ValueError("Committed process trace hash mismatch")
                    # Complete gzip members are appended per process event.
                    # Only the prefix bound by the manifest is committed.
                    with path.open("r+b") as stream:
                        prefix = stream.read(prefix_size)
                        if hashlib.sha256(prefix).hexdigest() != trace["sha256"]:
                            raise ValueError("Committed process trace hash mismatch")
                        tail = stream.read()
                        orphan = self.directory / "process-trace.uncommitted.jsonl.gz"
                        with orphan.open("ab") as preserved:
                            preserved.write(tail)
                            preserved.flush()
                            os.fsync(preserved.fileno())
                        stream.truncate(prefix_size)
                        stream.flush()
                        os.fsync(stream.fileno())
            games = rows = 0
            for chunk in self.manifest["chunks"]:
                path = self.directory / chunk["path"]
                if not path.is_file() or sha256(path) != chunk["sha256"]:
                    raise ValueError("Committed chunk hash mismatch: " + str(path))
                games += chunk["games"]
                rows += chunk["eligible_positions"]
                for index in chunk["game_indices"]:
                    if index in self.seen:
                        raise ValueError("Duplicate committed game index")
                    self.seen.add(index)
            if games != self.manifest["completed_games"] or rows != self.manifest["eligible_positions"]:
                raise ValueError("Checkpoint counts disagree with chunks")
            self.next_index = max(self.seen, default=-1) + 1
        else:
            if resume:
                raise ValueError("Cannot resume without a frozen manifest")
            if any(path.name != ".writer.lock" for path in self.directory.iterdir()):
                raise ValueError("New output directory must be empty")
            self.manifest = {"schema": SCHEMA, "configuration": config, "chunk_games": chunk_games,
                             "chunks": [], "completed_games": 0, "eligible_positions": 0,
                             "split_games": {key: 0 for key in ("train", "validation", "audit")},
                             "split_positions": {key: 0 for key in ("train", "validation", "audit")},
                             "status": "FROZEN_READY", "sessions": []}
            (self.directory / "chunks").mkdir()
            atomic_json(self.path, self.manifest)

    def append(self, game):
        if (not isinstance(game.get("game_id"), str) or not game["game_id"]
                or game.get("result_white") not in (0.0, .5, 1.0)
                or isinstance(game.get("result_white"), bool) or game.get("split") not in self.manifest["split_games"]
                or type(game.get("game_index")) is not int):
            raise ValueError("Incomplete or malformed game")
        index = game["game_index"]
        if index in self.seen:
            raise ValueError("Duplicate game index")
        if any(row.get("game_id") != game["game_id"] or row.get("split") != game["split"] for row in game["samples"]):
            raise ValueError("Sample game identity or partition mismatch")
        self.seen.add(index)
        self.next_index = max(self.next_index, index + 1)
        self.buffer.append(game)
        if len(self.buffer) >= self.chunk_games:
            self.commit()

    def commit(self):
        if not self.buffer:
            return
        name = f"chunks/games-{len(self.manifest['chunks']):06d}.jsonl.gz"
        path, games = self.directory / name, sorted(self.buffer, key=lambda row: row["game_index"])
        temp = path.with_name(path.name + ".part")
        # Recover only the manifest boundary. An orphan final/part chunk has no
        # committed games and may be overwritten with deterministic fresh work.
        with temp.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=1, mtime=0) as stream:
                for game in games:
                    stream.write(encoded(game) + b"\n")
            raw.flush()
            os.fsync(raw.fileno())
        os.replace(temp, path)
        if os.name != "nt":
            descriptor = os.open(str(path.parent), os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        positions = sum(len(game["samples"]) for game in games)
        chunk = {"path": name, "sha256": sha256(path), "bytes": path.stat().st_size,
                 "games": len(games), "eligible_positions": positions,
                 "missing_score_positions": sum(game.get("missing_score_positions", 0) for game in games),
                 "game_indices": [game["game_index"] for game in games]}
        self.manifest["chunks"].append(chunk)
        self.manifest["completed_games"] += len(games)
        self.manifest["eligible_positions"] += positions
        for game in games:
            self.manifest["split_games"][game["split"]] += 1
            self.manifest["split_positions"][game["split"]] += len(game["samples"])
        self.manifest["status"] = "GENERATION_IN_PROGRESS"
        if hasattr(self, "trace_path"):
            self.manifest["process_trace"] = trace_metadata(self.trace_path)
        atomic_json(self.path, self.manifest)
        self.buffer.clear()

    def close(self):
        self.commit()


def worker(worker_id, config, tasks, output, stop):
    engines, receipts, error = [], [], None
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        # Keep independent engine instances even when both paths are equal.
        identities = config["engines"][:1] if config.get("native_batch") else config["engines"]
        for identity in identities:
            engines.append(UciEngine(identity["path"], config["engine_timeout"],
                                     lambda pid: output.put(("spawned", worker_id, {"pid": pid})),
                                     ["--coordinator", config["engines"][1]["path"]] if config.get("native_batch") else []))
        output.put(("ready", worker_id, [{"pid": engine.process.pid, "engine_id": engine.identity} for engine in engines]))
        while not stop.is_set():
            try:
                index = tasks.get(timeout=.25)
            except queue.Empty:
                continue
            if index is None:
                break
            game = (play_native_game(index, config, engines[0], stop) if config.get("native_batch")
                    else play_game(index, config, engines, stop))
            if game is not None:
                output.put(("game", worker_id, game))
    except BaseException as exception:
        error = repr(exception)
        stop.set()
        output.put(("error", worker_id, {"error": error, "uci_tail": [list(engine.tail) for engine in engines]}))
    finally:
        for engine in engines:
            try:
                receipts.append(engine.close())
            except BaseException as exception:
                receipts.append({"error": repr(exception), "reaped": False})
        output.put(("done", worker_id, {"engines": receipts, "error": error}))


def file_identity(path, source_commit, network):
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("Exact forty-digit engine source commit required")
    return {"path": str(path.resolve()), "sha256": sha256(path), "source_commit": source_commit,
            "network_path": str(network.resolve()), "network_sha256": sha256(network)}


def trace_metadata(path):
    return {"path": path.name, "sha256": sha256(path), "bytes": path.stat().st_size,
            "policy": "Complete gzip members: process identities/cleanup and exact bounded UCI tails on failure"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--opponent", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--opponent-source-commit", required=True)
    parser.add_argument("--network", type=Path, required=True)
    parser.add_argument("--opponent-network", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--games", type=int, default=1000000)
    parser.add_argument("--target-positions", type=int, default=5000000)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--nodes", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--split-seed", type=int, default=2026102301)
    parser.add_argument("--validation-fraction", type=float, default=.1)
    parser.add_argument("--audit-fraction", type=float, default=.1)
    parser.add_argument("--opening-min", type=int, default=8)
    parser.add_argument("--opening-max", type=int, default=24)
    parser.add_argument("--max-ply", type=int, default=320)
    parser.add_argument("--score-cap", type=int, default=1000)
    parser.add_argument("--chunk-games", type=int, default=256)
    parser.add_argument("--engine-timeout", type=float, default=15)
    parser.add_argument("--time-limit-seconds", type=float, default=14400)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--native-batch", action="store_true", help="One native controller handles each complete game")
    parser.add_argument("--engine-core", type=Path)
    parser.add_argument("--opponent-core", type=Path)
    parser.add_argument("--engine-reference", type=Path)
    parser.add_argument("--opponent-reference", type=Path)
    parser.add_argument("--build-provenance", type=Path, help="Frozen compact adapter build commands and header identities")
    parser.add_argument("--stop-file", type=Path, help="Stop scheduling at completed games when this file exists")
    args = parser.parse_args(argv)
    if (min(args.games, args.workers, args.nodes, args.score_cap, args.chunk_games) <= 0
            or args.target_positions < 0 or args.opening_min < 0
            or not args.opening_min <= args.opening_max < args.max_ply
            or args.engine_timeout <= 0 or args.time_limit_seconds <= 0):
        parser.error("Require positive finite budgets and valid opening/max-ply limits")
    split_for_game("check", args.split_seed, args.validation_fraction, args.audit_fraction)
    identities = [file_identity(args.engine, args.source_commit, args.network),
                  file_identity(args.opponent, args.opponent_source_commit, args.opponent_network)]
    if any((args.engine_core, args.opponent_core, args.engine_reference, args.opponent_reference)):
        if not all((args.engine_core, args.opponent_core, args.engine_reference, args.opponent_reference)):
            parser.error("Adapter provenance requires both cores and both original reference binaries")
        for identity, core, reference in zip(identities, (args.engine_core, args.opponent_core),
                                             (args.engine_reference, args.opponent_reference)):
            identity["frozen_core"] = {"path": str(core.resolve()), "sha256": sha256(core)}
            identity["original_uci_reference"] = {"path": str(reference.resolve()), "sha256": sha256(reference)}
            driver = Path(__file__).with_name("native_game_driver.cpp")
            identity["adapter_source"] = {"path": str(driver.resolve()), "sha256": sha256(driver)}
            identity["implementation"] = "Original synchronous adapter linked to unchanged frozen Forge core; process SHA identifies adapter"
    config = {"schema": SCHEMA, "engines": identities, "options": OPTIONS, "nodes": args.nodes,
              "seed": args.seed, "split_seed": args.split_seed, "validation_fraction": args.validation_fraction,
              "audit_fraction": args.audit_fraction, "opening_plies": [args.opening_min, args.opening_max],
              "max_ply": args.max_ply, "score_cap": args.score_cap, "max_games": args.games,
              "target_positions": args.target_positions, "workers": args.workers,
              "native_batch": args.native_batch,
              "engine_timeout": args.engine_timeout, "time_limit_seconds": args.time_limit_seconds,
              "generator_sha256": sha256(Path(__file__)), "python_chess_version": chess.__version__,
              "filter": "not in check; bestmove quiet/nonpromotion/nonchecking; exact Forge cp within cap or explicitly missing nullable diagnostic; independent teacher alone supplies training labels",
              "termination": "mate/stalemate/actual-threefold/50move/insufficient; max-ply explicitly adjudicated draw",
              "partition_rule": "SHA256([split_seed,game_id]) first64bits; audit then validation then train",
              "uci_history_policy": ("Native complete game Board history; original 5101 core via cached full startpos UCI history" if args.native_batch
                                     else "FEN immediately after latest pawn move/capture plus complete following reversible suffix; full actual game archived"),
              "pairing_rule": "index mod4: shipped/shipped, shipped/5101, shipped/shipped, 5101/shipped",
              "purpose": "Fresh independent-teacher inputs; generation scores are not training teacher labels; no strength claim"}
    config["config_sha256"] = hashlib.sha256(encoded(config)).hexdigest()
    if args.build_provenance:
        config["build_provenance"] = {"path": str(args.build_provenance.resolve()), "sha256": sha256(args.build_provenance)}
        config["config_sha256"] = hashlib.sha256(encoded({key: value for key, value in config.items() if key != "config_sha256"})).hexdigest()
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    lock_stream = (args.out / ".writer.lock").open("a+b")
    if os.name != "nt":
        import fcntl
        fcntl.flock(lock_stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
    store = ChunkStore(args.out, config, args.chunk_games, args.resume)
    ctx, started = mp.get_context("spawn"), time.monotonic()
    stop, output = ctx.Event(), ctx.Queue()
    task_queues = [ctx.Queue(maxsize=2) for _ in range(args.workers)]
    processes = [ctx.Process(target=worker, args=(index, config, task_queues[index], output, stop))
                 for index in range(args.workers)]
    prior_handlers = {sig: signal.signal(sig, lambda *_: stop.set()) for sig in (signal.SIGINT, signal.SIGTERM)}
    errors, facts, done, ready, owned_engine_pids = [], {}, set(), set(), set()
    next_index, pending_rows, received_games = store.next_index, 0, 0
    stop_file = args.stop_file.resolve() if args.stop_file else args.out / "STOP_GENERATION"
    graceful_stop = False
    last_progress, budget_done = started, False
    trace_path = args.out / "process-trace.jsonl.gz"
    trace = trace_path.open("ab")
    store.trace_path = trace_path
    initial_rows = store.manifest["eligible_positions"]
    def event(kind, worker_id, payload):
        trace.write(gzip.compress(encoded({"event": kind, "worker": worker_id, "elapsed": time.monotonic() - started, "data": payload}) + b"\n",
                                  compresslevel=1, mtime=0))
        trace.flush()
        os.fsync(trace.fileno())
    def dispatch(worker_id):
        nonlocal next_index, budget_done, graceful_stop
        rows = initial_rows + pending_rows
        graceful_stop = graceful_stop or stop_file.exists()
        if stop.is_set() or graceful_stop or next_index >= args.games or (args.target_positions and rows >= args.target_positions):
            budget_done = True
            task_queues[worker_id].put(None)
        else:
            task_queues[worker_id].put(next_index)
            next_index += 1
    try:
        for process in processes:
            process.start()
        while len(done) < args.workers:
            if time.monotonic() - started >= args.time_limit_seconds and not stop.is_set():
                errors.append("Generation time budget reached")
                stop.set()
            try:
                kind, worker_id, payload = output.get(timeout=.25)
            except queue.Empty:
                for index, process in enumerate(processes):
                    if process.exitcode is not None and index not in done:
                        # The done queue message may still be in transit.
                        if process.exitcode != 0:
                            errors.append(f"Worker {index} exited with {process.exitcode}")
                            done.add(index)
                            stop.set()
                continue
            if kind == "game":
                store.append(payload)
                pending_rows += len(payload["samples"])
                received_games += 1
                dispatch(worker_id)
            elif kind == "ready":
                ready.add(worker_id)
                event(kind, worker_id, payload)
                dispatch(worker_id)
            elif kind == "spawned":
                owned_engine_pids.add(payload["pid"])
                event(kind, worker_id, payload)
            elif kind == "error":
                errors.append(payload["error"])
                event(kind, worker_id, payload)
            elif kind == "done":
                facts[worker_id] = payload
                done.add(worker_id)
                event(kind, worker_id, payload)
            if time.monotonic() - last_progress >= 30:
                print(json.dumps({"completed_games": store.manifest["completed_games"] + len(store.buffer),
                                  "eligible_positions": initial_rows + pending_rows,
                                  "positions_per_second": pending_rows / max(.001, time.monotonic() - started),
                                  "elapsed_seconds": time.monotonic() - started}), flush=True)
                last_progress = time.monotonic()
    except BaseException as exception:
        errors.append(repr(exception))
        stop.set()
        event("parent_error", None, {"error": repr(exception)})
    finally:
        stop.set()
        for tasks in task_queues:
            try:
                tasks.put_nowait(None)
            except queue.Full:
                pass
        # Continue servicing Queue feeder pipes while workers finish. Joining
        # without draining can deadlock a worker that just sent a full game.
        shutdown_deadline = time.monotonic() + args.engine_timeout + 10
        while len(done) < args.workers and time.monotonic() < shutdown_deadline:
            try:
                kind, worker_id, payload = output.get(timeout=.1)
            except queue.Empty:
                if all(process.exitcode is not None for process in processes):
                    break
                continue
            if kind == "game":
                if payload["game_index"] not in store.seen:
                    store.append(payload)
                    pending_rows += len(payload["samples"])
                    received_games += 1
            elif kind == "spawned":
                owned_engine_pids.add(payload["pid"])
                event(kind, worker_id, payload)
            elif kind == "done":
                facts[worker_id] = payload
                done.add(worker_id)
                event(kind, worker_id, payload)
            elif kind == "error":
                errors.append(payload["error"])
                event(kind, worker_id, payload)
        # Kill still-owned detached engine groups before their owner worker.
        reaped_pids = {engine.get("pid") for fact in facts.values() for engine in fact["engines"]
                       if engine.get("reaped")}
        for pid in owned_engine_pids - reaped_pids:
            try:
                if os.name != "nt":
                    os.killpg(pid, signal.SIGKILL)
                else:
                    os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        for process in processes:
            process.join(timeout=3)
            if process.is_alive():
                process.kill()
                process.join(timeout=3)
                errors.append("Worker required forced kill")
        store.close()
        for sig, previous in prior_handlers.items():
            signal.signal(sig, previous)
        for identity in identities:
            if sha256(identity["path"]) != identity["sha256"] or sha256(identity["network_path"]) != identity["network_sha256"]:
                errors.append("Frozen engine or compiled-network source changed during generation")
            for artifact in (identity.get(key) for key in ("frozen_core", "original_uci_reference", "adapter_source")):
                if artifact and sha256(artifact["path"]) != artifact["sha256"]:
                    errors.append("Frozen adapter/core/reference source changed during generation")
        if sha256(Path(__file__)) != config["generator_sha256"]:
            errors.append("Frozen generator source changed during generation")
        if args.build_provenance and sha256(args.build_provenance) != config["build_provenance"]["sha256"]:
            errors.append("Frozen native build provenance changed during generation")
        closed = (len(facts) == args.workers and all(len(fact["engines"]) == (1 if args.native_batch else 2) and fact["error"] is None
                  and all(engine.get("reaped") and engine.get("returncode") == 0 and not engine.get("forced_kill")
                          and (not args.native_batch or (engine.get("nested_opponent") or {}).get("returncode") == 0)
                          for engine in fact["engines"]) for fact in facts.values()))
        reached = (store.manifest["eligible_positions"] >= args.target_positions if args.target_positions
                   else store.manifest["completed_games"] >= args.games)
        status = "PASS_COMPLETED_GAMES_OWNED_ENGINES_CLOSED" if (reached or graceful_stop) and closed and not errors else "INCOMPLETE_OR_FAILED"
        trace.close()
        store.manifest["status"] = status
        store.manifest["target_reached"] = reached
        store.manifest["stop_reason"] = "stop_file_at_completed_game" if graceful_stop else ("target_reached" if reached else "incomplete_or_failure")
        store.manifest["process_trace"] = trace_metadata(trace_path)
        store.manifest["sessions"].append({"elapsed_seconds": time.monotonic() - started, "new_games": received_games,
                                            "new_eligible_positions": pending_rows, "errors": errors,
                                            "workers_observed": facts, "owned_workers_reaped": all(p.exitcode is not None for p in processes)})
        atomic_json(store.path, store.manifest)
        lock_stream.close()
    print(json.dumps({"status": status, "completed_games": store.manifest["completed_games"],
                      "eligible_positions": store.manifest["eligible_positions"],
                      "elapsed_seconds": time.monotonic() - started,
                      "positions_per_second": pending_rows / max(.001, time.monotonic() - started), "errors": errors}), flush=True)
    return 0 if status.startswith("PASS") else 1


if __name__ == "__main__":
    sys.exit(main())
