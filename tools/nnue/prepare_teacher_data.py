#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Stream authenticated independent-teacher games into native residual arrays.

The only corpus-sized Python object is an exact first-four-FEN winner index.
Complete game objects and native output are bounded by one game / one batch;
arrays use temporary disk memmaps. Audit wins cross-split overlaps, followed by
validation, then training; the first occurrence wins within each partition.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import zip_longest
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

import chess
import numpy as np

from generate_teacher_games import encoded, game_identity, pairing, repetition_key, split_for_game, terminal_result
from prepare_residual_data import position_key, sha256

PARTITIONS = ("train", "validation", "audit")
RECIPE_KEYS = {"fen", "game_id", "ply", "source_path", "source_line", "sample_index", "source_sample_index"}


def check_hash(path, expected):
    if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
        raise ValueError("Invalid SHA-256 binding: " + str(path))
    if not Path(path).is_file() or sha256(path) != expected:
        raise ValueError("Missing or changed source: " + str(path))


def write_json(path, value):
    Path(path).write_bytes(json.dumps(value, indent=2, allow_nan=False).encode("ascii") + b"\n")


class SourceResolver:
    """Relocate immutable evidence paths explicitly; never rewrite its bytes."""
    def __init__(self, mappings=None):
        self.mappings = []
        for mapping in mappings or []:
            if not isinstance(mapping, dict) or set(mapping) != {"from", "to"}:
                raise ValueError("Source mappings require exact from/to roots")
            source, target = Path(mapping["from"]), Path(mapping["to"])
            if not source.is_absolute() or not target.is_absolute():
                raise ValueError("Source relocation roots must be absolute")
            self.mappings.append((source, target.resolve()))
        if len({str(source) for source, _ in self.mappings}) != len(self.mappings):
            raise ValueError("Duplicate source relocation root")
        self.mappings.sort(key=lambda item: len(item[0].parts), reverse=True)

    def __call__(self, path):
        path = Path(path)
        # Already relocated paths must not be translated twice when a target
        # lives below its original root.
        if any(path.is_relative_to(target) for _, target in self.mappings):
            return path.resolve()
        for source, target in self.mappings:
            if path.is_relative_to(source):
                return (target / path.relative_to(source)).resolve()
        return path.resolve()


def validate_protocol(sources, protocol):
    target = protocol.get("target", {})
    weight = target.get("result_weight")
    if (target.get("kind") != "teacher_probability_game_result_blend"
            or type(weight) not in (int, float) or not .3 <= weight <= .5
            or target.get("sigmoid_k") != 2.25 or target.get("cp_scale") != 400.0):
        raise ValueError("Frozen teacher/result target differs from the existing residual contract")
    dataset = protocol.get("dataset", {})
    fractions = dataset.get("fractions", {})
    if (dataset.get("whole_game_split_seed") != sources.gconfig["split_seed"]
            or fractions.get("validation") != sources.gconfig["validation_fraction"]
            or fractions.get("audit") != sources.gconfig["audit_fraction"]
            or not np.isclose(fractions.get("train", -1), 1.0 - fractions.get("validation", 0) - fractions.get("audit", 0),
                              rtol=0, atol=1e-15)):
        raise ValueError("Frozen protocol whole-game split seed/fractions differ from generation")
    teacher = protocol.get("teacher", {})
    if teacher.get("depth") != sources.config["depth"]:
        raise ValueError("Frozen protocol teacher depth differs from actual teacher labels")
    for frozen, actual in (("binary_sha256", "teacher_sha256"), ("network_sha256", "teacher_network_sha256")):
        value = teacher.get(frozen)
        if (not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None
                or value != sources.config.get(actual)):
            raise ValueError("Frozen protocol teacher " + frozen + " differs from actual labels")
    for field in ("options", "policy"):
        expected, actual = teacher.get(field), sources.config.get(field)
        if (not isinstance(expected, dict) or not expected or not isinstance(actual, dict)
                or encoded(expected) != encoded(actual)):
            raise ValueError("Frozen protocol teacher " + field + " differs from actual labels")
    for field, index in (("baseline_source_sha", 0), ("secondary_generation_source_sha", 1)):
        if field in protocol and protocol[field] != sources.engines[index].get("source_commit"):
            raise ValueError("Frozen protocol actual generation source commit differs")
    if "generation_seed" in dataset and dataset["generation_seed"] != sources.gconfig.get("seed"):
        raise ValueError("Frozen generation opening seed differs")
    if "max_ply" in dataset and dataset["max_ply"] != sources.gconfig.get("max_ply"):
        raise ValueError("Frozen complete-game adjudication limit differs")


class PositionIndex:
    """Exact strings, with no lossy hash or collision assumptions."""
    def __init__(self):
        self.winners = {}

    def add(self, key, split, ordinal):
        rank = PARTITIONS.index(split)
        current = self.winners.get(key)
        if current is None or rank > (current & 3):
            self.winners[key] = (ordinal << 2) | rank

    def selected(self, key, split, ordinal):
        return self.winners.get(key) == (ordinal << 2) | PARTITIONS.index(split)

    def counts(self):
        counts = Counter(PARTITIONS[value & 3] for value in self.winners.values())
        return {name: counts[name] for name in PARTITIONS}


def _quiet_move(board, text, label):
    if not isinstance(text, str):
        raise ValueError("Invalid " + label + " move")
    try:
        move = chess.Move.from_uci(text)
    except (TypeError, ValueError) as error:
        raise ValueError("Invalid " + label + " move") from error
    if move not in board.legal_moves or board.is_capture(move) or move.promotion or board.gives_check(move):
        raise ValueError("Illegal or tactical " + label + " move")
    return move


def validate_labelled_game(original, labelled, engine_shas, depth, score_cap, max_ply=None):
    """Replay complete legal game history, then authenticate each accepted label."""
    if not isinstance(original, dict) or not isinstance(labelled, dict):
        raise ValueError("A complete game object is required")
    # The teacher may replace only samples and append declared teacher counters.
    for key, value in original.items():
        if key != "samples" and labelled.get(key) != value:
            raise ValueError("Teacher changed original game field: " + key)
    identity, split = original.get("game_id"), original.get("split")
    result = original.get("result_white")
    if (not isinstance(identity, str) or not identity or split not in PARTITIONS
            or isinstance(result, bool) or result not in (0.0, .5, 1.0)):
        raise ValueError("Invalid completed game identity/split/result")
    if any(original.get("engine_" + color + "_sha256") not in engine_shas for color in ("white", "black")):
        raise ValueError("Original game engine identity is not authenticated")
    moves, samples, accepted = original.get("moves"), original.get("samples"), labelled.get("samples")
    if not isinstance(moves, list) or not isinstance(samples, list) or not isinstance(accepted, list):
        raise ValueError("Complete game moves and samples required")
    by_ply = {}
    for source_index, sample in enumerate(samples):
        ply = sample.get("ply")
        if type(ply) is not int or not 0 <= ply < len(moves) or ply in by_ply:
            raise ValueError("Duplicate or invalid original game ply")
        by_ply[ply] = (source_index, sample)
    board = chess.Board(original.get("initial_fen", chess.STARTING_FEN))
    if not board.is_valid() or board.ply() != 0:
        raise ValueError("Require valid fresh start-ply game history")
    repetitions = Counter({repetition_key(board): 1})
    boards = {}
    for ply, move in enumerate(moves):
        try:
            parsed = chess.Move.from_uci(move)
        except (AttributeError, TypeError, ValueError) as error:
            raise ValueError("Illegal complete game move") from error
        if not parsed or not board.is_legal(parsed):
            raise ValueError("Illegal complete game move")
        if terminal_result(board, max_ply if max_ply is not None else 2**63,
                           repetitions[repetition_key(board)]) is not None:
            raise ValueError("Complete game continues after terminal position")
        if ply in by_ply:
            _, sample = by_ply[ply]
            expected_engine = original["engine_" + ("white" if board.turn else "black") + "_sha256"]
            if (sample.get("game_id") != identity or sample.get("split") != split
                    or sample.get("result_white") != result or sample.get("ply") != board.ply()
                    or sample.get("fen") != board.fen(en_passant="fen")
                    or sample.get("bestmove") != move or sample.get("engine_sha256") != expected_engine):
                raise ValueError("Original sample game/ply/FEN/result/engine history differs")
            boards[ply] = board.copy(stack=False)
        board.push(parsed)
        repetitions[repetition_key(board)] += 1
    if "final_fen" in original and original["final_fen"] != board.fen(en_passant="fen"):
        raise ValueError("Complete game final FEN differs")
    if max_ply is not None and terminal_result(board, max_ply) != (result, original.get("termination")):
        raise ValueError("Actual complete game result/termination differs")
    output, seen = [], set()
    for sample in accepted:
        source_index = sample.get("source_sample_index")
        if type(source_index) is not int or not 0 <= source_index < len(samples) or source_index in seen:
            raise ValueError("Invalid or duplicate teacher source sample index")
        seen.add(source_index)
        source = samples[source_index]
        for key, value in source.items():
            if key != "score_cp_stm" and sample.get(key) != value:
                raise ValueError("Teacher changed original sample field: " + key)
        cp = sample.get("teacher_cp_stm")
        if (type(cp) is not int or abs(cp) > score_cap or sample.get("score_cp_stm") != cp
                or sample.get("forge_score_cp_stm") != source.get("score_cp_stm")
                or sample.get("teacher_kind") != "cp" or sample.get("teacher_depth") != depth
                or any(type(sample.get(key)) is not int or sample[key] < 0
                       for key in ("teacher_nodes", "teacher_time_ms"))):
            raise ValueError("Independent teacher score/depth/source provenance differs")
        sample_board = boards[source["ply"]]
        if sample_board.is_check() or sample_board.is_game_over(claim_draw=False) or sample_board.halfmove_clock >= 100:
            raise ValueError("In-check or terminal teacher position")
        _quiet_move(sample_board, sample.get("teacher_bestmove"), "teacher")
        row = dict(sample)
        row["result_stm"] = float(result if sample_board.turn else 1.0 - result)
        output.append(row)
    return output


def native_labels(probe, rows, evidence_dir, batch_index, receipt=None, timeout=120):
    """Use communicate (closes stdin) with bounded batches; retain failed bytes."""
    payload = ("\n".join(row["fen"] for row in rows) + "\n").encode("ascii")
    command = [str(probe), "--hce-only"]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    stdout = stderr = b""
    group_kill_attempted = False
    cleanup_timeout = 2
    def kill_owned_group():
        nonlocal group_kill_attempted
        group_kill_attempted = True
        # The session leader can already be reaped while descendants still own
        # stdout/stderr. Its original PID remains our owned process-group ID.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        try:
            stdout, stderr = process.communicate(payload, timeout=timeout)
        except BaseException as original_error:
            kill_owned_group()
            try:
                stdout, stderr = process.communicate(timeout=cleanup_timeout)
            except subprocess.TimeoutExpired as cleanup_error:
                stdout = cleanup_error.output or getattr(original_error, "output", None) or b""
                stderr = cleanup_error.stderr or getattr(original_error, "stderr", None) or b""
                # Even an unexpectedly inherited descriptor cannot make the
                # second drain unbounded. Retain bytes observed before closure.
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream is not None:
                        stream.close()
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=cleanup_timeout)
            raise
        if process.returncode != 0 or stderr:
            raise RuntimeError("Native HCE probe process failed")
        facts = [json.loads(line) for line in stdout.splitlines()]
        if len(facts) != len(rows):
            raise ValueError("Native HCE row count differs")
        for index, fact in enumerate(facts):
            if (type(fact.get("index")) is not int or fact["index"] != index
                    or fact.get("hidden_size") != 128 or fact.get("hce_only") is not True
                    or fact.get("nnue_cp_stm") is not None or fact.get("residual_mode") is not True
                    or fact.get("nnue_available") is not True or type(fact.get("hce_cp_stm")) is not int
                    or fact.get("in_check") is not False or fact.get("terminal") is not False):
                raise ValueError("Native HCE schema/order/filter contract differs")
            values = fact.get("features")
            if (not isinstance(values, list) or len(values) != 2
                    or any(not isinstance(part, list) or not 2 <= len(part) <= 32
                           or len(set(part)) != len(part)
                           or any(type(v) is not int or not 0 <= v < 768 for v in part) for part in values)
                    or len(values[0]) != len(values[1])):
                raise ValueError("Invalid native perspective feature inventory")
        if receipt is not None:
            receipt["batches"] += 1; receipt["rows"] += len(rows)
            # Framed stream hashes bind exact bytes and batch boundaries.
            for name, value in (("stdin", payload), ("stdout", stdout), ("stderr", stderr)):
                receipt[name + "_digest"].update(len(value).to_bytes(8, "big") + value)
                receipt[name + "_bytes"] += len(value)
        return facts
    except BaseException as error:
        Path(evidence_dir).mkdir(parents=True, exist_ok=True)
        failure = {"command": command, "batch": batch_index, "error": repr(error),
                   "returncode": process.returncode, "rows": len(rows),
                   "stdin": payload.decode("ascii"), "stdout": stdout.decode("utf8", "replace"),
                   "stderr": stderr.decode("utf8", "replace"), "owned_process_reaped": process.poll() is not None,
                   "owned_process_group_kill_attempted": group_kill_attempted,
                   "cleanup_timeout_seconds": cleanup_timeout}
        with gzip.open(Path(evidence_dir) / f"failed-batch-{batch_index:06d}.json.gz", "wt", compresslevel=1) as stream:
            json.dump(failure, stream)
        raise
    finally:
        if process.poll() is None:
            kill_owned_group()
            process.wait(timeout=cleanup_timeout)


class TeacherSources:
    """Immutable bindings plus bounded streaming replay of matched source chunks."""
    def __init__(self, teacher_manifest, generation_manifest=None, source_mappings=None):
        self.resolve = SourceResolver(source_mappings)
        self.teacher_path = Path(teacher_manifest).resolve()
        self.teacher = json.loads(self.teacher_path.read_bytes())
        if self.teacher.get("status") != "complete" or not self.teacher.get("chunks"):
            raise ValueError("Teacher publication is incomplete or empty")
        self.config = self.teacher["configuration"]
        self.generation_path = (Path(generation_manifest).resolve() if generation_manifest else
                                self.resolve(Path(self.config["input_dir"]) / "manifest.json"))
        self.generation = json.loads(self.generation_path.read_bytes())
        self.gconfig = self.generation["configuration"]
        expected = dict(self.gconfig); digest = expected.pop("config_sha256")
        if hashlib.sha256(encoded(expected)).hexdigest() != digest:
            raise ValueError("Generator configuration SHA differs")
        if self.generation.get("status") != "PASS_COMPLETED_GAMES_OWNED_ENGINES_CLOSED":
            raise ValueError("Generation is not a closed completed-game publication")
        self.engines = self.gconfig["engines"]
        if len(self.engines) != 2:
            raise ValueError("Both actual generation engine identities are required")
        self.engine_shas = {entry["sha256"] for entry in self.engines}
        if (self.config.get("teacher_sha256") in self.engine_shas
                or self.config.get("policy", {}).get("score_pov") != "side_to_move"
                or type(self.config.get("depth")) is not int or self.config["depth"] < 1):
            raise ValueError("Require a distinct independent teacher and explicit STM/depth contract")
        self.bindings = {}
        self.add(self.teacher_path, "independent_teacher_manifest")
        self.add(self.generation_path, "generation_manifest")
        self.add(self.config["teacher_binary"], "independent_teacher_binary", self.config["teacher_sha256"])
        for name, config, field in (("generate_teacher_games.py", self.gconfig, "generator_sha256"),
                                    ("label_teacher_games.py", self.config, "tool_sha256")):
            if field in config:
                self.add(Path(__file__).with_name(name), "source_producer_tool", config[field])
        for engine in self.engines:
            self.add(engine["path"], "generation_engine_binary", engine["sha256"])
            self.add(engine["network_path"], "generation_engine_network_source", engine["network_sha256"])
            for field in ("frozen_core", "original_uci_reference", "adapter_source"):
                artifact = engine.get(field)
                if artifact is None and not self.gconfig.get("native_batch"):
                    continue
                if (not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str)
                        or not isinstance(artifact.get("sha256"), str)):
                    raise ValueError("Missing native generation adapter lineage: " + field)
                self.add(artifact["path"], "generation_" + field, artifact["sha256"])
        original_chunks = {(self.generation_path.parent / chunk["path"]).resolve(): chunk
                           for chunk in self.generation["chunks"]}
        self.chunks = []
        for chunk in sorted(self.teacher["chunks"], key=lambda record: record["source_path"]):
            original = self.resolve(chunk["source_path"])
            generation_chunk = original_chunks.get(original)
            if generation_chunk is None or generation_chunk["sha256"] != chunk["source_sha256"]:
                raise ValueError("Teacher source is absent or changed in generator manifest")
            label_path = self.teacher_path.parent / "chunks" / chunk["path"]
            self.add(original, "completed_game_chunk", chunk["source_sha256"])
            self.add(label_path, "independent_teacher_chunk", chunk["sha256"])
            self.chunks.append((chunk, original, label_path.resolve()))

    def validate_identity(self, original):
        identity, index = original.get("game_id"), original.get("game_index")
        if type(index) is not int or index < 0:
            raise ValueError("Invalid actual game index")
        expected_split = split_for_game(identity, self.gconfig["split_seed"],
            self.gconfig["validation_fraction"], self.gconfig["audit_fraction"])
        white, black = pairing(index)
        if (identity != game_identity(self.gconfig["config_sha256"], index)
                or original.get("split") != expected_split
                or original.get("engine_white_sha256") != self.engines[white]["sha256"]
                or original.get("engine_black_sha256") != self.engines[black]["sha256"]):
            raise ValueError("Wrong authentic game identity, split or engine pairing")

    def add(self, path, kind, expected=None):
        path = getattr(self, "resolve", SourceResolver())(path)
        digest = sha256(path) if expected is None else expected
        check_hash(path, digest)
        if path in self.bindings:
            if self.bindings[path]["sha256"] != digest:
                raise ValueError("Conflicting source binding")
            if self.bindings[path]["kind"] != kind:
                roles = self.bindings[path].setdefault("additional_kinds", [])
                if kind not in roles:
                    roles.append(kind)
            return
        self.bindings[path] = {"path": str(path), "sha256": digest, "kind": kind}

    def check(self):
        for path, record in self.bindings.items():
            check_hash(path, record["sha256"])

    def games(self, authenticate=True):
        seen = set()
        for metadata, original_path, label_path in self.chunks:
            count = accepted = 0; actual_ids = []
            with gzip.open(original_path, "rt", encoding="ascii") as originals, gzip.open(label_path, "rt", encoding="ascii") as labels:
                for line_number, pair in enumerate(zip_longest(originals, labels), 1):
                    if None in pair or any(not line.endswith("\n") for line in pair):
                        raise ValueError("Truncated or differently sized original/teacher chunk")
                    original, labelled = map(json.loads, pair)
                    self.validate_identity(original)
                    identity = original["game_id"]
                    if identity in seen:
                        raise ValueError("Duplicate authentic game identity")
                    seen.add(identity); actual_ids.append(identity); count += 1
                    rows = (validate_labelled_game(original, labelled, self.engine_shas,
                            self.config["depth"], self.config["policy"]["score_cap_cp"], self.gconfig["max_ply"])
                            if authenticate else labelled["samples"])
                    accepted += len(rows)
                    yield metadata, label_path, line_number, original, labelled, rows
            if count != metadata["games"] or accepted != metadata["accepted"] or actual_ids != metadata["game_ids"]:
                raise ValueError("Teacher chunk game/accepted counts or ordered identities differ")


def _memmaps(directory, name, count):
    specs = {"features": (np.int16, (count, 2, 32)), "hce": (np.int32, (count,)),
             "score": (np.int32, (count,)), "result_stm": (np.float32, (count,))}
    return {key: np.memmap(directory / f"{name}-{key}.raw", dtype=dtype, mode="w+", shape=shape)
            for key, (dtype, shape) in specs.items()}


def _fill(arrays, index, row, fact):
    arrays["features"][index] = -1
    for perspective, values in enumerate(fact["features"]):
        arrays["features"][index, perspective, :len(values)] = values
    arrays["hce"][index] = fact["hce_cp_stm"]
    arrays["score"][index] = row["score_cp_stm"]
    arrays["result_stm"][index] = row["result_stm"]


def validate_validation_provenance(data_dir, manifest, data, *, _recipe_selection=None):
    """Replay exact recipe rows, both original game streams, and native labels.

    ``source_lines_replayed`` counts decoded original *and* teacher compressed
    game JSONL records, not sampled positions; one game line can contain many
    requested positions. ``heldout_rows_replayed`` records the latter count.
    """
    if manifest.get("provenance_layout") == "multi_shard_v1":
        from merge_teacher_prepared import validate_merged_validation_provenance
        return validate_merged_validation_provenance(data_dir, manifest, data)
    data_dir = Path(data_dir).resolve()
    resolve = SourceResolver(manifest.get("source_mappings"))
    count = len(data["score"])
    binding = manifest.get("artifacts", {}).get("validation-provenance.jsonl", {})
    recipe_path = data_dir / "validation-provenance.jsonl"
    if _recipe_selection is not None:
        binding = _recipe_selection
        recipe_path = Path(binding["path"]).resolve()
    check_hash(recipe_path, binding.get("sha256"))
    if (binding.get("rows") != count or (_recipe_selection is None
            and manifest.get("files", {}).get("validation.npz", {}).get("rows") != count)):
        raise ValueError("Held-out recipe and array row counts differ")
    bindings = {}
    for entry in manifest.get("sources", []):
        path = Path(entry["path"])
        path = resolve(path if path.is_absolute() else data_dir / path)
        if path in bindings:
            if (not manifest.get("source_mappings") or bindings[path]["sha256"] != entry.get("sha256")):
                raise ValueError("Duplicate source identity")
            # An explicit relocation may map a mutable original pathname onto
            # its already-bound immutable exact-byte snapshot.
            continue
        check_hash(path, entry.get("sha256")); bindings[path] = entry
    def one_kind(kind):
        paths = [path for path, entry in bindings.items() if entry.get("kind") == kind]
        if len(paths) != 1:
            raise ValueError("Need one bound " + kind)
        return paths[0]
    sources = TeacherSources(one_kind("independent_teacher_manifest"), one_kind("generation_manifest"),
                             manifest.get("source_mappings"))
    for path, entry in sources.bindings.items():
        if path not in bindings or bindings[path]["sha256"] != entry["sha256"]:
            raise ValueError("Source chunk/engine binding omitted or changed")
    split = manifest["split"]
    known = split.get("validation_game_ids")
    if (not isinstance(known, list) or not known or len(set(known)) != len(known)
            or set(known) & set(split.get("train_game_ids", []))):
        raise ValueError("Invalid or overlapping held-out game membership")
    known = set(known); heldout = split.get("heldout_partition")
    if heldout not in ("validation", "audit"):
        raise ValueError("Explicit held-out source partition required")
    requests, game_ids, keys, identities = {}, [], [], set()
    valid_paths = {label for _, _, label in sources.chunks}
    opener = gzip.open if recipe_path.name.endswith(".gz") else open
    with opener(recipe_path, "rt", encoding="ascii") as stream:
        for row_index, line in enumerate(stream):
            if not line.endswith("\n"):
                raise ValueError("Truncated held-out recipe")
            row = json.loads(line)
            if not isinstance(row, dict) or set(row) != RECIPE_KEYS:
                raise ValueError("Independent-teacher recipe schema differs")
            if (row.get("game_id") not in known or type(row.get("ply")) is not int or row["ply"] < 0
                    or any(type(row.get(key)) is not int or row[key] < (1 if key == "source_line" else 0)
                           for key in ("source_line", "sample_index", "source_sample_index"))):
                raise ValueError("Invalid held-out game/ply/source identity")
            source_path = resolve(row["source_path"])
            if source_path not in valid_paths:
                raise ValueError("Unbound held-out teacher chunk")
            identity = (row["game_id"], row["ply"])
            key = position_key(row["fen"])
            if identity in identities:
                raise ValueError("Duplicate held-out game/ply")
            identities.add(identity)
            requests.setdefault(source_path, {}).setdefault(row["source_line"], []).append((row_index, row))
            game_ids.append(row["game_id"]); keys.append(key)
    if len(game_ids) != count or len(set(keys)) != count:
        raise ValueError("Held-out recipe count differs or duplicate positions remain")
    replayed_rows = replayed_lines = 0; pending = []
    probe = one_kind("native_hce_probe")
    def flush_native():
        if not pending:
            return
        facts = native_labels(probe, [row for _, row in pending], data_dir.parent / "provenance-native-failures",
                              replayed_rows)
        for (row_index, _), fact in zip(pending, facts):
            if int(data["hce"][row_index]) != fact["hce_cp_stm"]:
                raise ValueError("Held-out HCE differs from actual native probe")
            for perspective, expected in enumerate(fact["features"]):
                actual = data["features"][row_index, perspective]
                if sorted(actual[actual >= 0].tolist()) != sorted(expected):
                    raise ValueError("Held-out feature indices differ from native FEN inventory")
        pending.clear()
    for metadata, original_path, label_path in sources.chunks:
        wanted = requests.pop(label_path, None)
        if not wanted:
            continue
        with gzip.open(original_path, "rt", encoding="ascii") as originals, gzip.open(label_path, "rt", encoding="ascii") as labels:
            for line_number, pair in enumerate(zip_longest(originals, labels), 1):
                if line_number not in wanted:
                    continue
                if None in pair or any(not line.endswith("\n") for line in pair):
                    raise ValueError("Missing/truncated requested source game")
                original, labelled = map(json.loads, pair)
                sources.validate_identity(original)
                rows = validate_labelled_game(original, labelled, sources.engine_shas,
                    sources.config["depth"], manifest["filters"]["max_abs_score"], sources.gconfig["max_ply"])
                replayed_lines += 2
                if original.get("split") != heldout:
                    raise ValueError("Requested original game is in the wrong held-out split")
                for row_index, recipe in wanted.pop(line_number):
                    sample_index = recipe["sample_index"]
                    if not 0 <= sample_index < len(rows):
                        raise ValueError("Held-out teacher sample index is absent")
                    sample = rows[sample_index]
                    if (any(sample[key] != recipe[key] for key in ("game_id", "fen", "ply", "source_sample_index"))
                            or sample["score_cp_stm"] != int(data["score"][row_index])
                            or sample["result_stm"] != float(data["result_stm"][row_index])):
                        raise ValueError("Held-out source FEN/game/ply/teacher score/result differs from arrays")
                    pending.append((row_index, sample)); replayed_rows += 1
                    if len(pending) >= 20000:
                        flush_native()
        if wanted:
            raise ValueError("A requested source game line was not observed")
    flush_native()
    if requests or replayed_rows != count:
        raise ValueError("A held-out original source row was not replayed")
    return {"rows": count, "game_ids": game_ids, "position_keys": keys,
        "represented_game_ids": sorted(set(game_ids)), "listed_validation_games": len(known),
        "source_lines_replayed": replayed_lines, "heldout_rows_replayed": replayed_rows,
        "recipe_sha256": binding["sha256"],
        "scope": "Matched original and teacher compressed game records replayed with authentic game/ply/FEN/result, both generating engine SHA identities and independent teacher SHA/depth; STM score/result, native HCE and both feature inventories checked against exact array order. source_lines_replayed counts both decoded original and teacher game JSONL records."}


def prepare(args):
    started = time.monotonic()
    args.out = Path(args.out).resolve(); args.probe = Path(args.probe).resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    inputs = args.out / "inputs"; inputs.mkdir()
    sources = TeacherSources(args.teacher_manifest, args.generation_manifest)
    protocol_path = Path(args.protocol).resolve()
    protocol = json.loads(protocol_path.read_bytes())
    validate_protocol(sources, protocol)
    probe_source_path = Path(args.probe_source).resolve()
    probe_source = json.loads(probe_source_path.read_bytes())
    sources.add(args.probe, "native_hce_probe", probe_source["probe_sha256"])
    sources.add(probe_source_path, "native_hce_probe_source_receipt")
    sources.add(protocol_path, "frozen_training_protocol")
    sources.add(Path(__file__), "preparer_source")
    for source in probe_source.get("sources", []):
        sources.add(source["path"], "native_hce_probe_actual_source", source["sha256"])
    if not probe_source.get("sources"):
        raise ValueError("Actual native probe source bindings are required")
    # These immutable exact-byte snapshots are portable publication artifacts.
    for name, original in (("teacher-manifest.json", sources.teacher_path),
            ("generation-manifest.json", sources.generation_path), ("protocol.json", protocol_path),
            ("probe-source.json", probe_source_path)):
        shutil.copyfile(original, inputs / name)
        sources.add(inputs / name, "frozen_input_snapshot")
    index, assigned, seen_rows = PositionIndex(), {name: [] for name in PARTITIONS}, Counter()
    accepted_by_game = {}
    ordinal = 0
    for _, _, _, original, _, rows in sources.games():
        split = original["split"]; assigned[split].append(original["game_id"])
        accepted_by_game[original["game_id"]] = len(rows)
        for row in rows:
            index.add(position_key(row["fen"]), split, ordinal)
            ordinal += 1; seen_rows[split] += 1
    counts = index.counts(); total = sum(counts.values())
    if any(counts[name] == 0 for name in PARTITIONS):
        raise ValueError("Every split needs at least one eligible unique native position")
    minimum = max(5_000_000, args.min_positions)
    qualified = total >= minimum
    normal, audit = args.out / "prepared", args.out / "audit-prepared"
    normal.mkdir(); audit.mkdir()
    scratch = args.out / ".memmaps"; scratch.mkdir()
    arrays = {name: _memmaps(scratch, name, counts[name]) for name in PARTITIONS}
    recipe_paths = {"train": normal / "train-provenance.jsonl.gz",
                    "validation": normal / "validation-provenance.jsonl",
                    "audit": audit / "validation-provenance.jsonl"}
    recipes = {name: (gzip.open(path, "wt", compresslevel=1, encoding="ascii") if name == "train"
                      else path.open("w", encoding="ascii")) for name, path in recipe_paths.items()}
    receipt = {"batches": 0, "rows": 0}
    for key in ("stdin", "stdout", "stderr"):
        receipt[key + "_digest"] = hashlib.sha256(); receipt[key + "_bytes"] = 0
    offsets = Counter(); retained_by_game = Counter(); pending = []; ordinal = 0
    def flush():
        if not pending:
            return
        facts = native_labels(args.probe, [row for _, row, _ in pending], args.out / "native-failures",
                              receipt["batches"], receipt)
        for (split, row, recipe), fact in zip(pending, facts):
            _fill(arrays[split], offsets[split], row, fact)
            recipes[split].write(json.dumps(recipe, separators=(",", ":")) + "\n")
            offsets[split] += 1
            retained_by_game[row["game_id"]] += 1
        pending.clear()
    try:
        for _, label_path, line_number, original, labelled, rows in sources.games(authenticate=False):
            split = original["split"]
            for sample_index, sample in enumerate(rows):
                if index.selected(position_key(sample["fen"]), split, ordinal):
                    row = dict(sample)
                    result = original["result_white"]
                    row["result_stm"] = float(result if sample["fen"].split()[1] == "w" else 1.0 - result)
                    recipe = {"fen": sample["fen"], "game_id": original["game_id"], "ply": sample["ply"],
                              "source_path": str(label_path), "source_line": line_number, "sample_index": sample_index,
                              "source_sample_index": sample["source_sample_index"]}
                    pending.append((split, row, recipe))
                    if len(pending) >= args.batch_size:
                        flush()
                ordinal += 1
        flush()
    finally:
        for stream in recipes.values():
            stream.close()
    if dict(offsets) != counts:
        raise ValueError("Prepared retained counts changed between passes")
    del index
    for name in PARTITIONS:
        destination = audit / "validation.npz" if name == "audit" else normal / (name + ".npz")
        for array in arrays[name].values():
            array.flush()
        np.savez_compressed(destination, **arrays[name])
        for array in arrays[name].values():
            array._mmap.close()
        del arrays[name]
        for raw in scratch.glob(name + "-*.raw"):
            raw.unlink()
    scratch.rmdir()
    os.link(normal / "train.npz", audit / "train.npz")
    derived = {key: value for key, value in receipt.items() if not key.endswith("_digest")}
    derived.update({key + "_sha256": receipt[key + "_digest"].hexdigest() for key in ("stdin", "stdout", "stderr")})
    derived.update(command=[str(args.probe), "--hce-only"], successful_streams_retained=False,
                   hash_framing="8-byte unsigned big-endian byte-length followed by exact stream, per batch",
                   failed_stream_policy="One gzip JSON raw input/stdout/stderr/returncode record per failed batch")
    write_json(args.out / "native-probe-receipt.json", derived)
    sources.add(args.out / "native-probe-receipt.json", "native_derived_stream_receipt")
    sources.check()
    common = {"schema_version": 1, "hidden_size": 128, "score_pov": "side_to_move", "result_pov": "side_to_move",
        "provenance_format": "independent_teacher_v1", "protocol_sha256": sha256(protocol_path),
        "status": "QUALIFIED_FROZEN" if qualified else "INCOMPLETE_BELOW_MINIMUM_DO_NOT_TRAIN_OR_PROMOTE",
        "training_permitted": qualified, "minimum_positions": minimum, "retained_total_positions": total,
        "target": protocol["target"], "teacher": sources.config,
        "generation_configuration": sources.gconfig, "native_probe_sha256": sha256(args.probe),
        "native_probe_path": str(args.probe), "sources": list(sources.bindings.values()),
        "filters": {"max_abs_score": sources.config["policy"]["score_cap_cp"], "no_in_check": True,
                    "tactical_bestmove_filter": True},
        "position_policy": "Exact first four FEN fields; audit > validation > train; first retained occurrence within winning split",
        "exact_first4fen_crosssplit_overlap": 0,
        "statistics": {"teacher_accepted_by_split": dict(seen_rows), "retained_by_split": counts,
                       "excluded_overlaps_or_duplicates_by_split": {key: seen_rows[key] - counts[key] for key in PARTITIONS},
                       "zero_retained_games": {
                           "all_teacher_samples_filtered": sorted(game for game, rows in accepted_by_game.items() if rows == 0),
                           "all_positions_overlap_or_duplicate": sorted(game for game, rows in accepted_by_game.items()
                                                                        if rows and not retained_by_game[game])}},
        "audit_isolation": {"frozen_before_training": True, "audit_game_ids": assigned["audit"],
                            "audit_used_for_optimization_or_epoch_selection": False},
        "native_evidence": derived, "elapsed_seconds": time.monotonic() - started}
    for directory, heldout in ((normal, "validation"), (audit, "audit")):
        manifest = dict(common)
        manifest["dataset_role"] = "training_and_selection" if heldout == "validation" else "final_audit_only"
        manifest["split"] = {"policy": "game_hash", "seed": sources.gconfig["split_seed"],
            "legacy_training_game_ids_unknown": False, "train_game_ids": assigned["train"],
            "validation_game_ids": assigned[heldout], "heldout_partition": heldout,
            "validation_fraction": sources.gconfig["validation_fraction"], "audit_fraction": sources.gconfig["audit_fraction"]}
        manifest["files"] = {name: {"sha256": sha256(directory / name), "rows": counts["train" if name == "train.npz" else heldout]}
                             for name in ("train.npz", "validation.npz")}
        recipe = directory / "validation-provenance.jsonl"
        manifest["artifacts"] = {recipe.name: {"sha256": sha256(recipe), "rows": counts[heldout]}}
        if heldout == "validation":
            path = directory / "train-provenance.jsonl.gz"
            manifest["artifacts"][path.name] = {"sha256": sha256(path), "rows": counts["train"]}
        write_json(directory / "manifest.json", manifest)
    write_json(args.out / "freeze.json", {"status": common["status"], "training_permitted": qualified,
        "retained": counts, "total": total, "minimum_positions": minimum,
        "protocol_sha256": common["protocol_sha256"],
        "prepared_manifest_sha256": sha256(normal / "manifest.json"),
        "audit_manifest_sha256": sha256(audit / "manifest.json")})
    print(json.dumps({"status": common["status"], "retained": counts, "total": total}), flush=True)
    return 0 if qualified else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--teacher-manifest", type=Path, required=True)
    parser.add_argument("--generation-manifest", type=Path)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--probe-source", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=20000)
    parser.add_argument("--min-positions", type=int, default=5000000)
    args = parser.parse_args(argv)
    if args.batch_size < 1 or args.min_positions < 1:
        parser.error("Positive batch size and minimum required")
    return prepare(args)


if __name__ == "__main__":
    raise SystemExit(main())
