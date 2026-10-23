#!/usr/bin/env python3
"""Prepare residual data with held-out real games and native Forge HCE labels.

Legacy FEN | STM score | White result records are training-only. Their game
identities are unknown and are never synthesized from row numbers or counters.
"""
from __future__ import annotations

import argparse
from collections import Counter
import glob
import hashlib
import json
import math
from pathlib import Path
import re
import os
import random
import signal
import subprocess
import time

import chess
import numpy as np


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def position_key(fen):
    if not isinstance(fen, str) or len(fen.split()) != 6:
        raise ValueError("A complete six-field FEN is required")
    return " ".join(fen.split()[:4])


def split_for_game(game_id, seed, fraction):
    if not isinstance(game_id, str) or not game_id.strip():
        raise ValueError("An authentic nonempty game_id is required")
    if type(seed) is not int or not isinstance(fraction, (int, float)) or not math.isfinite(fraction) or not 0 < fraction < 1:
        raise ValueError("Require an integer seed and 0 < validation fraction < 1")
    token = json.dumps([seed, game_id], ensure_ascii=True, separators=(",", ":")).encode("ascii")
    value = int.from_bytes(hashlib.sha256(token).digest(), "big")
    return "validation" if value < int(fraction * (1 << 256)) else "train"


def validate_record(row, score_cap=1000):
    if not isinstance(row, dict):
        raise ValueError("Authenticated records must be JSON objects, not legacy lines")
    required = {"fen", "score_cp_stm", "result_white", "game_id", "ply", "bestmove", "engine_sha256"}
    if not required <= set(row):
        raise ValueError("Missing authenticated fields: " + ",".join(sorted(required - set(row))))
    if type(score_cap) is not int or score_cap <= 0:
        raise ValueError("score_cap must be a positive integer")
    if not isinstance(row["game_id"], str) or not row["game_id"].strip():
        raise ValueError("Invalid authentic game_id")
    if not isinstance(row["engine_sha256"], str) or re.fullmatch("[0-9a-f]{64}", row["engine_sha256"]) is None:
        raise ValueError("Invalid engine SHA-256")
    score = row["score_cp_stm"]
    if type(score) is not int or abs(score) > score_cap:
        raise ValueError("Teacher score must be integer STM cp within the configured score cap")
    result = row["result_white"]
    if isinstance(result, bool) or not isinstance(result, (int, float)) or result not in (0.0, 0.5, 1.0):
        raise ValueError("White result must be 0, 0.5 or 1")
    position_key(row["fen"])
    try:
        board = chess.Board(row["fen"])
    except (TypeError, ValueError) as error:
        raise ValueError("Invalid FEN") from error
    if not board.is_valid():
        raise ValueError("Invalid board")
    if type(row["ply"]) is not int or row["ply"] < 0 or row["ply"] != board.ply():
        raise ValueError("Recorded ply must equal the actual FEN ply")
    if not isinstance(row["bestmove"], str):
        raise ValueError("A legal best move is required")
    try:
        move = chess.Move.from_uci(row["bestmove"])
    except ValueError as error:
        raise ValueError("Invalid best move") from error
    if move not in board.legal_moves:
        raise ValueError("Illegal best move")
    if board.is_check():
        raise ValueError("In-check position")
    if board.is_capture(move) or move.promotion or board.gives_check(move):
        raise ValueError("Tactical best move")
    if board.is_game_over(claim_draw=False) or board.halfmove_clock >= 100:
        raise ValueError("Terminal position")
    normalized = dict(row)
    normalized["result_stm"] = float(result if board.turn == chess.WHITE else 1.0 - result)
    return normalized


def exclude_validation_positions(records, validation_keys):
    for row in records:
        if position_key(row["fen"]) not in validation_keys:
            yield row


def native_labels(probe, rows, evidence_dir, batch_index):
    fens = ("\n".join(row["fen"] for row in rows) + "\n").encode("ascii")
    command = [str(probe), "--hce-only"]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    try:
        # communicate services stdin/stdout concurrently; writing a whole batch
        # before reading this buffered producer can otherwise deadlock its pipes.
        stdout, stderr = process.communicate(fens, timeout=120)
    except BaseException:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        (evidence_dir / f"batch-{batch_index:05}.failed.stdout").write_bytes(stdout)
        (evidence_dir / f"batch-{batch_index:05}.failed.stderr").write_bytes(stderr)
        (evidence_dir / f"batch-{batch_index:05}.failed.stdin").write_bytes(fens)
        raise
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
    # Successful full-corpus derived JSON can exceed the workspace disk quota.
    # Keep exact stream digests/status/counts and retained arrays + source-line
    # recipes, while retaining original streams on every observed failure.
    stem = evidence_dir / f"batch-{batch_index:05}"
    receipt = {"command": command, "returncode": process.returncode, "input_rows": len(rows),
               "stdin_sha256": hashlib.sha256(fens).hexdigest(), "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
               "stderr_sha256": hashlib.sha256(stderr).hexdigest(), "stdin_bytes": len(fens),
               "stdout_bytes": len(stdout), "stderr_bytes": len(stderr),
               "owned_process_reaped": process.poll() is not None,
               "successful_derived_streams_retained": False}
    stem.with_suffix(".json").write_text(json.dumps(receipt) + "\n")
    if process.returncode != 0 or stderr:
        stem.with_suffix(".failed.stdin").write_bytes(fens)
        stem.with_suffix(".failed.stdout").write_bytes(stdout)
        stem.with_suffix(".failed.stderr").write_bytes(stderr)
        raise RuntimeError("Native HCE probe failed; original batch evidence retained at " + str(stem))
    facts = [json.loads(line) for line in stdout.splitlines()]
    if len(facts) != len(rows):
        raise ValueError("Native probe row count differs")
    required = {"index", "hce_cp_stm", "nnue_cp_stm", "nnue_available", "residual_mode", "hidden_size",
                "hce_only", "in_check", "terminal", "has_tactical_legal_move", "features"}
    for index, fact in enumerate(facts):
        if set(fact) != required or type(fact["index"]) is not int or fact["index"] != index:
            raise ValueError("Native probe schema or row order differs")
        if (fact["hidden_size"] != 128 or fact["hce_only"] is not True or fact["nnue_cp_stm"] is not None
                or fact["residual_mode"] is not True or fact["nnue_available"] is not True):
            raise ValueError("Native probe is not the authenticated Forge H128 residual HCE-only contract")
        if type(fact["hce_cp_stm"]) is not int:
            raise ValueError("Native HCE is not integer STM centipawns")
        for key in ("in_check", "terminal", "has_tactical_legal_move"):
            if type(fact[key]) is not bool:
                raise ValueError("Native filter fact has wrong type")
        features = fact["features"]
        if not isinstance(features, list) or len(features) != 2 or len(features[0]) != len(features[1]):
            raise ValueError("Native feature perspectives differ")
        for values in features:
            if (not isinstance(values, list) or not 2 <= len(values) <= 32 or len(set(values)) != len(values)
                    or any(type(value) is not int or not 0 <= value < 768 for value in values)):
                raise ValueError("Native feature inventory is invalid")
    return facts


def prepared_arrays(rows):
    features = np.full((len(rows), 2, 32), -1, dtype=np.int16)
    hce = np.empty(len(rows), dtype=np.int32)
    score = np.empty(len(rows), dtype=np.int32)
    results = np.empty(len(rows), dtype=np.float32)
    for index, (row, fact) in enumerate(rows):
        for perspective in (0, 1):
            values = fact["features"][perspective]
            features[index, perspective, :len(values)] = values
        hce[index] = fact["hce_cp_stm"]
        score[index] = row["score_cp_stm"]
        results[index] = row["result_stm"]
    return {"features": features, "hce": hce, "score": score, "result_stm": results}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy", action="append", default=[], help="Glob of legacy training-only files; never validation")
    parser.add_argument("--games-jsonl", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-train", type=int, default=1_000_000)
    parser.add_argument("--score-cap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--batch-size", type=int, default=4096)
    args = parser.parse_args(argv)
    if args.max_train <= 0 or args.score_cap <= 0 or args.batch_size <= 0:
        parser.error("Positive max-train, score-cap and batch-size required")
    split_for_game("configuration-check", args.seed, args.val_fraction)
    args.games_jsonl, args.probe, args.out = (path.resolve() for path in (args.games_jsonl, args.probe, args.out))
    if not args.probe.is_file() or not args.games_jsonl.is_file():
        parser.error("Existing native probe and completed-game input required")
    args.out.mkdir(parents=True, exist_ok=False)
    evidence = args.out / "native-probe-evidence"
    evidence.mkdir()
    generation_manifest_path = args.games_jsonl.parent / "manifest.json"
    generation = json.loads(generation_manifest_path.read_text())
    if (generation.get("status") != "PASS_COMPLETED_GAMES_OWNED_ENGINES_CLOSED"
            or generation["positions"]["sha256"] != sha256(args.games_jsonl)):
        raise ValueError("Fresh authentic generation manifest is absent or changed")
    if (generation.get("options") != {"Threads": 1, "Hash": 16, "OwnBook": False}
            or generation.get("requested_games") != generation.get("completed_games")
            or len(generation.get("workers_observed", [])) != generation.get("workers")
            or any(fact.get("closed") is not True or fact.get("returncode") != 0
                   or fact.get("configured_options") != generation["options"]
                   for fact in generation.get("workers_observed", []))):
        raise ValueError("Actual complete-game/engine-closure/options evidence differs")
    completed_ids = generation["completed_game_ids"]
    if (not isinstance(completed_ids, list) or len(set(completed_ids)) != len(completed_ids)
            or generation["completed_games"] != len(completed_ids)):
        raise ValueError("Completed-game manifest IDs differ")
    train_ids = [game_id for game_id in completed_ids
                 if split_for_game(game_id, args.seed, args.val_fraction) == "train"]
    validation_ids = [game_id for game_id in completed_ids
                      if split_for_game(game_id, args.seed, args.val_fraction) == "validation"]
    if not train_ids or not validation_ids:
        raise ValueError("Both authentic game partitions must be nonempty")
    validation_set, completed_set = set(validation_ids), set(completed_ids)
    stats = Counter()
    game_rows = []
    seen_game_plies = set()
    original_game_rows = 0
    with args.games_jsonl.open() as stream:
        for line_number, line in enumerate(stream, 1):
            original_game_rows += 1
            row = json.loads(line)
            if row.get("game_id") not in completed_set or row.get("engine_sha256") != generation["engine"]["sha256"]:
                raise ValueError("Unlisted game ID or source engine at input line " + str(line_number))
            identity = (row["game_id"], row["ply"])
            if identity in seen_game_plies:
                raise ValueError("Duplicate game/ply record")
            seen_game_plies.add(identity)
            try:
                row = validate_record(row, args.score_cap)
            except ValueError as error:
                if str(error) not in ("In-check position", "Tactical best move", "Terminal position",
                                      "Teacher score must be integer STM cp within the configured score cap"):
                    raise
                stats["fresh_filtered:" + str(error)] += 1
                continue
            row.update(source_path=str(args.games_jsonl), source_line=line_number)
            game_rows.append(row)
    if original_game_rows != generation["positions"]["rows"]:
        raise ValueError("Completed-game row count differs from the frozen generator manifest")
    validation_keys = {position_key(row["fen"]) for row in game_rows if row["game_id"] in validation_set}
    if not validation_keys:
        raise ValueError("No eligible positions in the actual held-out games")
    val_source = [row for row in game_rows if row["game_id"] in validation_set]
    fresh_train = list(exclude_validation_positions(
        (row for row in game_rows if row["game_id"] not in validation_set), validation_keys))
    stats["fresh_validation_overlap_excluded"] = sum(row["game_id"] not in validation_set for row in game_rows) - len(fresh_train)
    legacy_paths = sorted({Path(name).resolve() for pattern in args.legacy for name in glob.glob(pattern)})
    if args.legacy and not legacy_paths:
        raise ValueError("Legacy glob matched no files")
    source_paths = [args.games_jsonl, generation_manifest_path, args.probe, *legacy_paths]
    initial_hashes = {str(path): sha256(path) for path in source_paths}
    (args.out / "INPUTS.json").write_text(json.dumps(initial_hashes, indent=2) + "\n")
    started = time.monotonic()
    train_output, validation_output, legacy_reservoir = [], [], []
    seen_train = set()
    batch_index = 0
    rng = random.Random(args.seed)
    legacy_eligible = 0
    legacy_capacity = None
    per_source = {str(path): Counter() for path in legacy_paths}

    def append_batch(batch, destination, legacy=False):
        nonlocal batch_index, legacy_eligible
        if not batch:
            return
        facts = native_labels(args.probe, batch, evidence, batch_index)
        batch_index += 1
        for row, fact in zip(batch, facts):
            if fact["in_check"] or fact["terminal"] or (legacy and fact["has_tactical_legal_move"]):
                stats["native_filtered_legacy" if legacy else "native_filtered_fresh"] += 1
                continue
            if destination is train_output:
                key = position_key(row["fen"])
                if key in validation_keys:
                    stats["training_validation_overlap_excluded"] += 1
                    continue
                if key in seen_train:
                    stats["training_duplicate_position_excluded"] += 1
                    continue
                seen_train.add(key)
            if legacy:
                legacy_eligible += 1
                per_source[row["source_path"]]["eligible_unique_after_filters"] += 1
                if len(legacy_reservoir) < legacy_capacity:
                    legacy_reservoir.append((row, fact))
                else:
                    slot = rng.randrange(legacy_eligible)
                    if slot < legacy_capacity:
                        legacy_reservoir[slot] = (row, fact)
            elif destination is validation_output or len(destination) < args.max_train:
                destination.append((row, fact))

    for destination, source in ((validation_output, val_source), (train_output, fresh_train)):
        for begin in range(0, len(source), args.batch_size):
            append_batch(source[begin:begin + args.batch_size], destination)
    legacy_capacity = args.max_train - len(train_output)
    for path in legacy_paths:
        batch = []
        with path.open("r", encoding="ascii") as stream:
            for line_number, line in enumerate(stream, 1):
                stats["legacy_rows_examined"] += 1
                per_source[str(path)]["examined"] += 1
                fields = [field.strip() for field in line.split("|")]
                if len(fields) != 3:
                    raise ValueError(f"Malformed legacy row {path}:{line_number}")
                fen, cp_text, result_text = fields
                try:
                    cp, result = int(cp_text), float(result_text)
                except ValueError as error:
                    raise ValueError(f"Malformed legacy labels {path}:{line_number}") from error
                if result not in (0.0, 0.5, 1.0):
                    raise ValueError("Invalid legacy White result")
                if abs(cp) > args.score_cap:
                    stats["legacy_score_cap_excluded"] += 1
                    per_source[str(path)]["score_cap_excluded"] += 1
                    continue
                key = position_key(fen)
                if key in validation_keys:
                    stats["legacy_validation_overlap_excluded"] += 1
                    per_source[str(path)]["validation_overlap_excluded"] += 1
                    continue
                if key in seen_train:
                    stats["legacy_duplicate_position_excluded"] += 1
                    per_source[str(path)]["duplicate_position_excluded"] += 1
                    continue
                board = chess.Board(fen)
                if not board.is_valid():
                    raise ValueError(f"Illegal legacy board {path}:{line_number}")
                batch.append({"fen": fen, "score_cp_stm": cp, "source_path": str(path), "source_line": line_number,
                              "result_stm": float(result if board.turn else 1.0 - result)})
                if len(batch) == args.batch_size:
                    append_batch(batch, train_output, legacy=True)
                    batch = []
        append_batch(batch, train_output, legacy=True)
        print(json.dumps({"file": str(path), "retained_train": len(train_output) + len(legacy_reservoir),
                          "retained_validation": len(validation_output), "legacy_rows_examined": stats["legacy_rows_examined"],
                          "eligible_unique_legacy": legacy_eligible}), flush=True)
    for row, _ in legacy_reservoir:
        per_source[row["source_path"]]["selected"] += 1
    train_output.extend(legacy_reservoir)
    if not train_output or not validation_output:
        raise ValueError("Both prepared datasets must contain retained positions")
    if {position_key(row["fen"]) for row, _ in train_output} & validation_keys:
        raise ValueError("Training/validation position leakage")
    for label, rows in (("train", train_output), ("validation", validation_output)):
        np.savez(args.out / (label + ".npz"), **prepared_arrays(rows))
        with (args.out / (label + "-provenance.jsonl")).open("x") as stream:
            for row, _ in rows:
                stream.write(json.dumps({"fen": row["fen"], "game_id": row.get("game_id"), "ply": row.get("ply"),
                                         "source_path": row["source_path"], "source_line": row["source_line"],
                                         "legacy_game_identity_unknown": "game_id" not in row}, separators=(",", ":")) + "\n")
    if any(sha256(Path(path)) != digest for path, digest in initial_hashes.items()):
        raise ValueError("Input changed during preparation")
    manifest = {
        "schema_version": 1, "hidden_size": 128, "score_pov": "side_to_move", "result_pov": "side_to_move",
        "split": {"policy": "legacy_train_only_with_new_heldout_games" if legacy_paths else "game_hash",
                  "seed": args.seed, "train_game_ids": train_ids, "validation_game_ids": validation_ids,
                  "legacy_training_game_ids_unknown": bool(legacy_paths), "validation_fraction": args.val_fraction},
        "files": {label + ".npz": {"sha256": sha256(args.out / (label + ".npz")), "rows": len(rows)}
                  for label, rows in (("train", train_output), ("validation", validation_output))},
        "filters": {"max_abs_score": args.score_cap, "no_in_check": True, "tactical_bestmove_filter": True,
                    "legacy_without_move": "Conservative rejection of every position having any legal capture, promotion or checking move"},
        "sources": [{"path": str(path), "sha256": initial_hashes[str(path)],
                     "kind": "legacy_training_only" if path in legacy_paths else
                     ("native_hce_probe" if path == args.probe else "authenticated_game_data_or_manifest")}
                    for path in source_paths],
        "generation_engine_sha256": generation["engine"]["sha256"],
        "native_probe_sha256": initial_hashes[str(args.probe)], "statistics": dict(stats),
        "exact_first4fen_training_validation_overlap": 0,
        "native_probe_batches": batch_index, "elapsed_seconds": time.monotonic() - started,
        "selection": "All eligible fresh held-out rows; eligible fresh training rows; seeded Algorithm R reservoir of eligible unique legacy positions across all source files",
        "legacy_reservoir_seed": args.seed, "eligible_unique_legacy": legacy_eligible,
        "legacy_per_source": {path: dict(counts) for path, counts in per_source.items()},
        "native_derived_evidence": "Successful full-corpus derived streams are hashed, not retained. Arrays and source-line recipes retained; original failed native streams retained on failure. Raw inference parity evidence is separate.",
        "legacy_teacher_engine_source_identity": "Unknown: original three-field input has no authenticated engine metadata",
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"status": "PASS_PREPARED_DATA", "train": len(train_output), "validation": len(validation_output),
                      "manifest_sha256": sha256(args.out / "manifest.json")}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
