#!/usr/bin/env python3
"""Finite Forge self-play with authentic game IDs, moves and source identities.

Original three-field self-play output remains supported by forge_selfplay.py.
This separate format saves only complete games and is intended for game-held-out
residual-network validation, not a playing-strength match.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import queue
import random
import re
import signal
import threading
import time
from types import SimpleNamespace
import uuid

import chess
import chess.engine

import forge_selfplay
from prepare_residual_data import sha256, validate_record


def write_completed_game(path, *, game_id, records, result_white, engine_sha256):
    if result_white is None:
        return 0
    if isinstance(result_white, bool) or result_white not in (0.0, 0.5, 1.0):
        raise ValueError("A complete game needs an actual White result")
    if not isinstance(game_id, str) or not game_id.strip():
        raise ValueError("A complete game needs an authentic ID")
    if not isinstance(engine_sha256, str) or re.fullmatch("[0-9a-f]{64}", engine_sha256) is None:
        raise ValueError("A complete game needs its engine digest")
    rows = []
    for record in records:
        row = dict(record, game_id=game_id, result_white=result_white, engine_sha256=engine_sha256)
        try:
            normalized = validate_record(row, score_cap=3000)
        except ValueError as error:
            if str(error) in ("In-check position", "Tactical best move", "Terminal position"):
                continue
            raise
        normalized.pop("result_stm")
        rows.append(normalized)
    if rows:
        # Serialize the entire validated game before publishing its first row.
        # A malformed tail cannot leave a valid-looking prefix on disk.
        payload = "".join(json.dumps(row, separators=(",", ":"), allow_nan=False) + "\n" for row in rows)
        with Path(path).open("a", encoding="ascii", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    return len(rows)


def build_manifest(*, engine_path, network_path, positions_path, source_commit,
                   completed_game_ids, seed, nodes, workers):
    if not isinstance(source_commit, str) or re.fullmatch("[0-9a-f]{40}", source_commit) is None:
        raise ValueError("An explicit frozen engine source commit is required")
    if len(set(completed_game_ids)) != len(completed_game_ids):
        raise ValueError("Duplicate completed-game identities")
    paths = {"engine": Path(engine_path).resolve(), "network": Path(network_path).resolve(),
             "positions": Path(positions_path).resolve()}
    with paths["positions"].open("rb") as stream:
        counts = sum(1 for _ in stream)
    build_files = [paths["engine"].parent / name for name in (
        "CMakeCache.txt", "compile_commands.json", "CMakeFiles/forge_core.dir/flags.make",
        "CMakeFiles/forge.dir/flags.make", "CMakeFiles/forge.dir/link.txt")]
    return {"schema_version": 1, "source_commit": source_commit,
            **{name: {"path": str(path), "sha256": sha256(path)} for name, path in paths.items()},
            "options": {"Threads": 1, "Hash": 16, "OwnBook": False},
            "search": {"nodes": nodes}, "seed": seed, "workers": workers,
            "completed_game_ids": list(completed_game_ids), "completed_games": len(completed_game_ids),
            "termination": {"opening_plies": 8, "max_ply": 300, "max_ply_result": "adjudicated_draw",
                            "adjudicate_cp": 2000, "adjudicate_plies": 4,
                            "natural_terminal_rules": "Original play_game: checkmate precedence, actual repetition/50move/insufficient material"},
            "build_files": {str(path): sha256(path) for path in build_files if path.is_file()},
            "positions": {"path": str(paths["positions"]), "sha256": sha256(paths["positions"]), "rows": counts},
            "purpose": "Search-score training labels and game-held-out validation only; not Elo evidence"}


class TracedProtocol(forge_selfplay.MeteredUCI):
    def __init__(self):
        super().__init__()
        self.trace = None

    def send_line(self, line):
        if self.trace is not None:
            self.trace.write(json.dumps({"direction": "send", "line": line}) + "\n")
        super().send_line(line)

    def line_received(self, line):
        if self.trace is not None:
            self.trace.write(json.dumps({"direction": "receive", "line": line}) + "\n")
        super().line_received(line)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--games", type=int, default=256)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--nodes", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--network", type=Path, default=Path(__file__).resolve().parents[2] / "src/nnue_weights.inc")
    parser.add_argument("--time-limit-seconds", type=float, default=3600)
    args = parser.parse_args(argv)
    if min(args.games, args.workers, args.nodes) <= 0 or args.time_limit_seconds <= 0:
        parser.error("Positive finite games/workers/nodes/time budget required")
    args.engine, args.network, args.out = (path.resolve() for path in (args.engine, args.network, args.out))
    if not args.engine.is_file() or not args.network.is_file():
        parser.error("Existing engine and compiled-network source required")
    if re.fullmatch("[0-9a-f]{40}", args.source_commit) is None:
        parser.error("Exact forty-digit frozen engine source commit required")
    args.out.mkdir(parents=True, exist_ok=False)
    positions = args.out / "games.jsonl"
    positions.touch(exist_ok=False)
    engine_hash, network_hash = sha256(args.engine), sha256(args.network)
    run_id = uuid.uuid4().hex
    stop = threading.Event()
    # A failed parent writer must never strand workers in a bounded queue.put
    # while executor shutdown waits for them. The finite game budget bounds it.
    messages = queue.Queue()
    old_handler = signal.signal(signal.SIGINT, lambda *_: stop.set())
    started = time.monotonic()
    game_args = SimpleNamespace(opening_plies=8, max_ply=300, depth=None, nodes=args.nodes,
                                max_score=3000, adjudicate_cp=2000, adjudicate_plies=4)

    def worker(worker_id):
        engine = None
        facts = {"worker": worker_id, "engine_sha256": engine_hash, "engine_pid": None,
                 "returncode": None, "closed": False, "error": None}
        trace = (args.out / f"worker-{worker_id}-uci.jsonl").open("x", buffering=1)
        try:
            engine = chess.engine.SimpleEngine.popen(TracedProtocol, [str(args.engine)], timeout=60,
                                                     setpgrp=True, cwd=str(args.engine.parent))
            engine.protocol.trace = trace
            facts["engine_pid"] = engine.transport.get_pid()
            facts["engine_id"] = engine.id
            required = {"Threads": 1, "Hash": 16, "OwnBook": False}
            if not set(required) <= set(engine.options):
                raise RuntimeError("Forge lacks a required UCI option")
            engine.configure(required)
            facts["configured_options"] = required
            for index in range(worker_id, args.games, args.workers):
                if stop.is_set():
                    break
                for attempt in range(10):
                    records = []
                    completed = forge_selfplay.play_game(
                        engine, game_args, random.Random(args.seed + index + attempt * args.games),
                        stop, record_hook=records.append)
                    if completed is not None:
                        break
                    if stop.is_set():
                        return
                else:
                    raise RuntimeError("Ten random openings produced no complete game")
                if stop.is_set():
                    break
                legacy, result = completed
                if [(row["fen"], row["score_cp_stm"]) for row in records] != legacy:
                    raise RuntimeError("Record hook changed legacy sample identity")
                messages.put(("game", index, records, result))
        except BaseException as error:
            facts["error"] = repr(error)
            stop.set()
            messages.put(("error", worker_id, repr(error)))
        finally:
            try:
                forge_selfplay.stop_engine(engine)
                if engine is not None:
                    facts["returncode"] = engine.returncode.result(timeout=3)
                    facts["closed"] = engine.returncode.done()
            except BaseException as error:
                facts["cleanup_error"] = repr(error)
            trace.close()
            (args.out / f"worker-{worker_id}-process.json").write_text(json.dumps(facts, indent=2) + "\n")
            messages.put(("done", worker_id, facts))

    completed, worker_facts, errors = {}, [], []
    rows_written = 0
    source_hashes = {str(path): sha256(path) for path in (
        Path(__file__), Path(forge_selfplay.__file__), Path(validate_record.__code__.co_filename))}
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = [executor.submit(worker, index) for index in range(args.workers)]
            try:
                while len(worker_facts) < args.workers:
                    if time.monotonic() - started >= args.time_limit_seconds and not stop.is_set():
                        stop.set()
                        errors.append("Finite generation time budget reached")
                    try:
                        message = messages.get(timeout=0.25)
                    except queue.Empty:
                        continue
                    if message[0] == "game":
                        _, index, records, result = message
                        game_id = run_id + ":" + str(index)
                        if index in completed:
                            raise RuntimeError("Repeated completed game index")
                        kept = write_completed_game(positions, game_id=game_id, records=records,
                                                    result_white=result, engine_sha256=engine_hash)
                        completed[index] = game_id
                        rows_written += kept
                        print(json.dumps({"completed_games": len(completed), "retained_positions": rows_written}), flush=True)
                    elif message[0] == "error":
                        errors.append(message[2])
                    else:
                        worker_facts.append(message[2])
                for future in futures:
                    future.result()
            finally:
                stop.set()
    finally:
        stop.set()
        signal.signal(signal.SIGINT, old_handler)
    manifest = build_manifest(engine_path=args.engine, network_path=args.network, positions_path=positions,
                              source_commit=args.source_commit, completed_game_ids=[completed[key] for key in sorted(completed)],
                              seed=args.seed, nodes=args.nodes, workers=args.workers)
    manifest.update(run_id=run_id, workers_observed=worker_facts, errors=errors,
                    elapsed_seconds=time.monotonic() - started, requested_games=args.games,
                    generator_sha256=sha256(Path(__file__)), original_selfplay_sha256=sha256(Path(forge_selfplay.__file__)),
                    generator_source_files_before=source_hashes,
                    generator_source_files_after={path: sha256(Path(path)) for path in source_hashes})
    passed = (len(completed) == args.games and not errors and all(
        facts["closed"] and facts["returncode"] == 0 and facts["error"] is None for facts in worker_facts)
        and sha256(args.engine) == engine_hash and sha256(args.network) == network_hash
        and manifest["generator_source_files_before"] == manifest["generator_source_files_after"])
    manifest["status"] = "PASS_COMPLETED_GAMES_OWNED_ENGINES_CLOSED" if passed else "FAILED_OR_INCOMPLETE_GENERATION"
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"status": manifest["status"], "completed_games": len(completed), "positions": rows_written}), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
