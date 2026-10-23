#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Merge authenticated native prepared shards without repeating preparation.

Original manifests, recipes and source bytes remain immutable. Exact position
priority is audit > validation > train. Source arrays are copied, never scored.
The merged training and audit data remain ineligible below five million rows.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np

from prepare_teacher_data import (PARTITIONS, RECIPE_KEYS, PositionIndex, SourceResolver,
    _memmaps, check_hash, encoded, position_key, sha256, split_for_game, write_json)

ARRAY_NAMES = {"features", "hce", "score", "result_stm"}
MERGED_RECIPE_KEYS = RECIPE_KEYS | {"shard_id", "source_row"}


def _read(path):
    raw = Path(path).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _stream(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="ascii") as stream:
        for line in stream:
            if not line.endswith("\n"):
                raise ValueError("Truncated source recipe: " + str(path))
            row = json.loads(line)
            if not isinstance(row, dict) or set(row) != RECIPE_KEYS:
                raise ValueError("Original independent-teacher recipe schema differs")
            yield row


def _bind(bindings, path, digest, kind):
    path = Path(path).resolve()
    previous = bindings.get(str(path))
    if previous is not None and previous["sha256"] != digest:
        raise ValueError("Conflicting source SHA binding: " + str(path))
    if previous is None:
        check_hash(path, digest)
        bindings[str(path)] = {"path": str(path), "sha256": digest, "kind": kind}


def _arrays(path, count, score_cap):
    with np.load(path, allow_pickle=False) as archive:
        if set(archive.files) != ARRAY_NAMES:
            raise ValueError("Source NPZ names differ")
        arrays = {key: archive[key] for key in archive.files}
    f = arrays["features"]
    if f.dtype != np.int16 or f.shape != (count, 2, 32):
        raise ValueError("Source features must be int16[N,2,32]")
    if any(arrays[key].dtype != np.int32 or arrays[key].shape != (count,) for key in ("hce", "score")):
        raise ValueError("Source native HCE/teacher scores must be int32[N]")
    if arrays["result_stm"].dtype != np.float32 or arrays["result_stm"].shape != (count,):
        raise ValueError("Source outcomes must be float32[N]")
    for begin in range(0, count, 20000):
        values = f[begin:begin + 20000]
        ordered = np.sort(values, axis=2)
        if (((values < -1) | (values >= 768)).any()
                or ((ordered[:, :, 1:] == ordered[:, :, :-1]) & (ordered[:, :, 1:] >= 0)).any()
                or not np.array_equal((values[:, 0] >= 0).sum(1), (values[:, 1] >= 0).sum(1))):
            raise ValueError("Invalid source native feature inventories")
    if (np.abs(arrays["score"].astype(np.int64)) > score_cap).any() or not np.isin(arrays["result_stm"], [0, .5, 1]).all():
        raise ValueError("Source scores/outcomes differ from the declared filters")
    return arrays


class Shard:
    def __init__(self, identifier, directory, mappings, bindings):
        self.id = int(identifier); self.directory = Path(directory).resolve()
        self.mappings = mappings; self.resolve = SourceResolver(mappings)
        self.manifests = {}; self.manifest_records = {}
        for partition, role in (("validation", "prepared"), ("audit", "audit-prepared")):
            path = self.directory / role / "manifest.json"
            manifest, digest = _read(path)
            if (manifest.get("schema_version") != 1 or manifest.get("provenance_format") != "independent_teacher_v1"
                    or manifest.get("provenance_layout") is not None or manifest.get("hidden_size") != 128
                    or manifest.get("score_pov") != "side_to_move" or manifest.get("result_pov") != "side_to_move"
                    or manifest.get("split", {}).get("heldout_partition") != partition
                    or manifest.get("split", {}).get("legacy_training_game_ids_unknown") is not False):
                raise ValueError("Unsupported original prepared shard provenance")
            _bind(bindings, path, digest, "original_prepared_shard_manifest")
            for source in manifest["sources"]:
                raw = Path(source["path"])
                actual = self.resolve(raw if raw.is_absolute() else path.parent / raw)
                _bind(bindings, actual, source["sha256"], "original_shard_" + source["kind"])
            for name, record in {**manifest["files"], **manifest["artifacts"]}.items():
                _bind(bindings, path.parent / name, record["sha256"], "original_prepared_shard_artifact")
            self.manifests[partition] = manifest
            self.manifest_records[partition] = {"path": str(path), "sha256": digest}
        normal, audit = self.manifests["validation"], self.manifests["audit"]
        if (normal["files"]["train.npz"] != audit["files"]["train.npz"]
                or normal["split"]["train_game_ids"] != audit["split"]["train_game_ids"]
                or normal["teacher"] != audit["teacher"]
                or normal["generation_configuration"] != audit["generation_configuration"]):
            raise ValueError("Original training/audit shard identities differ")
        self.generation = normal["generation_configuration"]
        self.teacher = normal["teacher"]
        self.assigned = {"train": normal["split"]["train_game_ids"],
            "validation": normal["split"]["validation_game_ids"], "audit": audit["split"]["validation_game_ids"]}
        self.counts = {"train": normal["files"]["train.npz"]["rows"],
            "validation": normal["files"]["validation.npz"]["rows"], "audit": audit["files"]["validation.npz"]["rows"]}
        if any(type(count) is not int or count <= 0 for count in self.counts.values()):
            raise ValueError("Positive source shard row counts required")
        known = set()
        for partition, ids in self.assigned.items():
            if not isinstance(ids, list) or len(set(ids)) != len(ids) or known.intersection(ids):
                raise ValueError("Invalid/overlapping authentic source game IDs")
            known.update(ids)
            for game in ids:
                if (not isinstance(game, str) or not game.startswith(self.generation["config_sha256"][:24] + ":")
                        or split_for_game(game, self.generation["split_seed"], self.generation["validation_fraction"],
                                          self.generation["audit_fraction"]) != partition):
                    raise ValueError("Original whole-game hash assignment differs")
        def source_entry(kind):
            matches = [entry for entry in normal["sources"] if entry["kind"] == kind]
            if len(matches) != 1:
                raise ValueError("Missing singleton native/source proof: " + kind)
            return matches[0]
        def source_json(kind):
            raw = Path(source_entry(kind)["path"])
            return _read(self.resolve(raw if raw.is_absolute() else self.role("validation") / raw))[0]
        generation_source = source_json("generation_manifest")
        teacher_source = source_json("independent_teacher_manifest")
        config = dict(self.generation); config_digest = config.pop("config_sha256")
        if (hashlib.sha256(encoded(config)).hexdigest() != config_digest
                or generation_source.get("status") != "PASS_COMPLETED_GAMES_OWNED_ENGINES_CLOSED"
                or teacher_source.get("status") != "complete"
                or generation_source.get("configuration") != self.generation
                or teacher_source.get("configuration") != self.teacher):
            raise ValueError("Prepared shard original source configurations differ")
        native = source_json("native_derived_stream_receipt")
        probe = source_json("native_hce_probe_source_receipt")
        if (native.get("rows") != sum(self.counts.values()) or type(native.get("batches")) is not int
                or native["batches"] < 1 or native.get("command", [])[1:] != ["--hce-only"]
                or probe.get("probe_sha256") != normal.get("native_probe_sha256")
                or source_entry("native_hce_probe")["sha256"] != normal.get("native_probe_sha256")
                or self.resolve(native["command"][0]) != self.resolve(source_entry("native_hce_probe")["path"])):
            raise ValueError("Native HCE/features source receipt differs")
        if (not probe.get("sources") or any(str(self.resolve(entry["path"])) not in bindings
                or bindings[str(self.resolve(entry["path"]))]["sha256"] != entry["sha256"] for entry in probe["sources"])):
            raise ValueError("Original native probe source identity is not authenticated")
        original_protocol = source_json("frozen_training_protocol")
        self.original_protocol = original_protocol
        if (normal.get("protocol_sha256") != source_entry("frozen_training_protocol")["sha256"]
                or audit.get("protocol_sha256") != normal.get("protocol_sha256")
                or normal["target"] != original_protocol.get("target")
                or normal["filters"].get("no_in_check") is not True
                or normal["filters"].get("tactical_bestmove_filter") is not True
                or normal["filters"].get("max_abs_score") != self.teacher["policy"]["score_cap_cp"]):
            raise ValueError("Original shard target differs from its protocol")

    def role(self, partition):
        return self.directory / ("audit-prepared" if partition == "audit" else "prepared")

    def recipe_path(self, partition):
        return self.role(partition) / ("train-provenance.jsonl.gz" if partition == "train" else "validation-provenance.jsonl")

    def array_path(self, partition):
        return self.role(partition) / ("train.npz" if partition == "train" else "validation.npz")

    def recipes(self, partition):
        known = set(self.assigned[partition]); count = 0
        for row in _stream(self.recipe_path(partition)):
            if row.get("game_id") not in known:
                raise ValueError("Original recipe has wrong whole-game membership")
            count += 1
            yield row
        if count != self.counts[partition]:
            raise ValueError("Source recipe/NPZ row counts differ")


def _specifications(args, bindings):
    mappings = {}
    for item in args.source_map:
        identifier, name = item.split("=", 1)
        if int(identifier) in mappings:
            raise ValueError("Duplicate source-map shard ID")
        value, digest = _read(name); SourceResolver(value)
        mappings[int(identifier)] = value
        _bind(bindings, name, digest, "frozen_source_relocation_map")
    shards = []; seen = set()
    for item in args.shard:
        identifier, directory = item.split("=", 1); identifier = int(identifier)
        if identifier < 0 or identifier in seen:
            raise ValueError("Invalid or duplicate source shard ID")
        seen.add(identifier); shards.append(Shard(identifier, directory, mappings.get(identifier, []), bindings))
    if not shards or set(mappings) - seen:
        raise ValueError("Require source shards and matching relocation maps")
    return sorted(shards, key=lambda shard: shard.id)


def _science(shards, protocol):
    base_seed = protocol.get("dataset", {}).get("generation_seed")
    if type(base_seed) is not int:
        raise ValueError("Global protocol must predeclare the generation seed base")
    teacher = protocol["teacher"]; dataset = protocol["dataset"]
    seen = set(); reference = None
    for shard in shards:
        g, t, manifest = shard.generation, shard.teacher, shard.manifests["validation"]
        if g.get("seed") != base_seed + shard.id:
            raise ValueError("Source shard generation seed is not the predeclared base + shard ID")
        if (t.get("teacher_sha256") != teacher.get("binary_sha256")
                or t.get("teacher_network_sha256") != teacher.get("network_sha256")
                or t.get("depth") != teacher.get("depth") or t.get("options") != teacher.get("options")
                or t.get("policy") != teacher.get("policy") or manifest["target"] != protocol["target"]
                or g["split_seed"] != dataset["whole_game_split_seed"]
                or g["validation_fraction"] != dataset["fractions"]["validation"]
                or g["audit_fraction"] != dataset["fractions"]["audit"]):
            raise ValueError("Source shard scientific teacher/target/split settings differ")
        for key in ("nodes", "max_ply", "opening_plies"):
            if key in dataset and g.get(key) != dataset[key]:
                raise ValueError("Source shard generation settings differ: " + key)
        for field, index in (("baseline_source_sha", 0), ("secondary_generation_source_sha", 1)):
            if field in protocol and g["engines"][index]["source_commit"] != protocol[field]:
                raise ValueError("Frozen global protocol engine source commit differs")
        signature = {"engines": [(engine["source_commit"], engine["network_sha256"]) for engine in g["engines"]],
                     "filters": manifest["filters"], "generation_options": g.get("options")}
        if reference is not None and signature != reference:
            raise ValueError("Source shard native engine/evaluation/filter identity differs")
        reference = signature
        ids = {game for games in shard.assigned.values() for game in games}
        if seen.intersection(ids):
            raise ValueError("Duplicate game identity across source shards")
        seen.update(ids)


def merge(args):
    started = time.monotonic(); bindings = {}
    protocol_path = Path(args.protocol).resolve(); protocol, protocol_sha = _read(protocol_path)
    _bind(bindings, protocol_path, protocol_sha, "frozen_global_training_protocol")
    shards = _specifications(args, bindings); _science(shards, protocol)
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=False)
    plan = {"schema": "native_prepared_shards_v1", "protocol_sha256": protocol_sha,
        "shards": [{"id": s.id, "directory": str(s.directory), "manifests": s.manifest_records,
                    "source_mappings": s.mappings, "generation_seed": s.generation["seed"]} for s in shards],
        "position_policy": "Exact first four FEN fields; audit > validation > train; first occurrence by shard ID then original array order"}
    write_json(out / "merge-plan.json", plan)
    _bind(bindings, out / "merge-plan.json", sha256(out / "merge-plan.json"), "frozen_merge_plan")
    _bind(bindings, Path(__file__), sha256(Path(__file__)), "merger_source")
    index = PositionIndex(); ordinal = 0; original_counts = Counter()
    for shard in shards:
        for partition in PARTITIONS:
            for row in shard.recipes(partition):
                index.add(position_key(row["fen"]), partition, ordinal); ordinal += 1
                original_counts[partition] += 1
    counts = index.counts(); total = sum(counts.values())
    if any(count == 0 for count in counts.values()):
        raise ValueError("Every globally filtered partition needs native rows")
    minimum = max(5000000, args.min_positions); qualified = total >= minimum
    normal, audit = out / "prepared", out / "audit-prepared"; normal.mkdir(); audit.mkdir()
    scratch = out / ".memmaps"; scratch.mkdir()
    arrays = {partition: _memmaps(scratch, partition, counts[partition]) for partition in PARTITIONS}
    output_recipe = {"train": gzip.open(normal / "train-provenance.jsonl.gz", "wt", encoding="ascii", compresslevel=1),
        "validation": (normal / "validation-provenance.jsonl").open("w", encoding="ascii"),
        "audit": (audit / "validation-provenance.jsonl").open("w", encoding="ascii")}
    offsets = Counter(); retained_games = Counter(); selections = {"validation": [], "audit": []}; ordinal = 0
    try:
        for shard in shards:
            for partition in PARTITIONS:
                source = _arrays(shard.array_path(partition), shard.counts[partition],
                                 shard.manifests["validation"]["filters"]["max_abs_score"])
                selection_path = out / "recipe-selections" / partition / (str(shard.id) + ".jsonl.gz")
                selection_path.parent.mkdir(parents=True, exist_ok=True)
                selected_count = 0; pending = []
                with gzip.open(selection_path, "wt", encoding="ascii", compresslevel=1) as selected_recipe:
                    def flush():
                        if not pending:
                            return
                        rows = np.asarray(pending, dtype=np.int64); begin = offsets[partition]
                        for key in ARRAY_NAMES:
                            arrays[partition][key][begin:begin + len(rows)] = source[key][rows]
                        offsets[partition] += len(rows); pending.clear()
                    for row_index, row in enumerate(shard.recipes(partition)):
                        if index.selected(position_key(row["fen"]), partition, ordinal):
                            pending.append(row_index); selected_count += 1; retained_games[row["game_id"]] += 1
                            output_recipe[partition].write(json.dumps({**row, "shard_id": shard.id, "source_row": row_index}, separators=(",", ":")) + "\n")
                            selected_recipe.write(json.dumps(row, separators=(",", ":")) + "\n")
                            if len(pending) >= 20000:
                                flush()
                        ordinal += 1
                    flush()
                del source
                if partition in selections:
                    selections[partition].append({"shard_id": shard.id, "path": str(selection_path),
                        "rows": selected_count, "sha256": sha256(selection_path)})
                _bind(bindings, selection_path, sha256(selection_path), "derived_original_recipe_selection")
    finally:
        for stream in output_recipe.values():
            stream.close()
    del index
    if dict(offsets) != counts:
        raise ValueError("Selected native rows changed between passes")
    for partition in PARTITIONS:
        destination = audit / "validation.npz" if partition == "audit" else normal / (partition + ".npz")
        for array in arrays[partition].values():
            array.flush()
        np.savez_compressed(destination, **arrays[partition])
        for array in arrays[partition].values():
            array._mmap.close()
        del arrays[partition]
        for raw in scratch.glob(partition + "-*.raw"):
            raw.unlink()
    scratch.rmdir(); os.link(normal / "train.npz", audit / "train.npz")
    for binding in bindings.values():
        check_hash(binding["path"], binding["sha256"])
    assigned = {partition: [game for shard in shards for game in shard.assigned[partition]] for partition in PARTITIONS}
    common = {"schema_version": 1, "hidden_size": 128, "score_pov": "side_to_move", "result_pov": "side_to_move",
        "provenance_format": "independent_teacher_v1", "provenance_layout": "multi_shard_v1",
        "protocol_sha256": protocol_sha, "target": protocol["target"], "teacher": protocol["teacher"],
        "status": "QUALIFIED_FROZEN" if qualified else "INCOMPLETE_BELOW_MINIMUM_DO_NOT_TRAIN_OR_PROMOTE",
        "training_permitted": qualified, "minimum_positions": minimum, "retained_total_positions": total,
        "filters": shards[0].manifests["validation"]["filters"], "sources": list(bindings.values()),
        "merge": {**plan, "native_arrays_recomputed": False, "native_proof": "Original prepared array, source and native HCE receipt SHA bindings retained per shard; selected rows copied without numerical changes"},
        "statistics": {"original_rows": dict(original_counts), "retained_by_split": counts,
            "excluded_by_split": {key: original_counts[key] - counts[key] for key in PARTITIONS},
            "zero_retained_games": sorted(game for games in assigned.values() for game in games if not retained_games[game])},
        "exact_first4fen_crosssplit_overlap": 0,
        "audit_isolation": {"frozen_before_training": True, "audit_game_ids": assigned["audit"],
                            "audit_used_for_optimization_or_epoch_selection": False},
        "elapsed_seconds": time.monotonic() - started}
    for directory, heldout in ((normal, "validation"), (audit, "audit")):
        manifest = copy.deepcopy(common)
        manifest["dataset_role"] = "training_and_selection" if heldout == "validation" else "final_audit_only"
        manifest["split"] = {"policy": "game_hash", "seed": protocol["dataset"]["whole_game_split_seed"],
            "legacy_training_game_ids_unknown": False, "train_game_ids": assigned["train"],
            "validation_game_ids": assigned[heldout], "heldout_partition": heldout}
        manifest["recipe_selections"] = selections[heldout]
        manifest["files"] = {name: {"rows": counts["train" if name == "train.npz" else heldout],
                                   "sha256": sha256(directory / name)} for name in ("train.npz", "validation.npz")}
        manifest["artifacts"] = {"validation-provenance.jsonl": {"rows": counts[heldout],
                                   "sha256": sha256(directory / "validation-provenance.jsonl")}}
        if heldout == "validation":
            manifest["artifacts"]["train-provenance.jsonl.gz"] = {"rows": counts["train"],
                "sha256": sha256(directory / "train-provenance.jsonl.gz")}
        write_json(directory / "manifest.json", manifest)
    write_json(out / "freeze.json", {"status": common["status"], "training_permitted": qualified,
        "retained": counts, "total": total, "minimum_positions": minimum, "protocol_sha256": protocol_sha,
        "prepared_manifest_sha256": sha256(normal / "manifest.json"), "audit_manifest_sha256": sha256(audit / "manifest.json")})
    print(json.dumps({"status": common["status"], "retained": counts, "total": total}), flush=True)
    return 0 if qualified else 2


def validate_merged_validation_provenance(data_dir, manifest, data):
    from prepare_teacher_data import validate_validation_provenance
    data_dir = Path(data_dir).resolve(); count = len(data["score"])
    binding = manifest["artifacts"]["validation-provenance.jsonl"]
    check_hash(data_dir / "validation-provenance.jsonl", binding["sha256"])
    if binding["rows"] != count or manifest["files"]["validation.npz"]["rows"] != count:
        raise ValueError("Merged recipe/array row counts differ")
    for entry in manifest["sources"]:
        check_hash(entry["path"], entry["sha256"])
    records = {record["id"]: record for record in manifest["merge"]["shards"]}
    requested = {}; game_ids = []; keys = []
    with (data_dir / "validation-provenance.jsonl").open(encoding="ascii") as stream:
        for array_index, line in enumerate(stream):
            if not line.endswith("\n"):
                raise ValueError("Truncated merged held-out recipe")
            recipe = json.loads(line)
            if (set(recipe) != MERGED_RECIPE_KEYS or type(recipe["shard_id"]) is not int
                    or recipe["shard_id"] not in records or type(recipe["source_row"]) is not int or recipe["source_row"] < 0):
                raise ValueError("Invalid merged original shard/row identity")
            original = {key: recipe[key] for key in RECIPE_KEYS}
            wanted = requested.setdefault(recipe["shard_id"], {})
            if recipe["source_row"] in wanted:
                raise ValueError("Duplicate original held-out array row")
            wanted[recipe["source_row"]] = (array_index, original)
            game_ids.append(recipe["game_id"]); keys.append(position_key(recipe["fen"]))
    known = set(manifest["split"]["validation_game_ids"])
    if (len(game_ids) != count or len(set(keys)) != count or not set(game_ids) <= known
            or known.intersection(manifest["split"]["train_game_ids"])):
        raise ValueError("Merged held-out count, unique positions or assigned games differ")
    partition = manifest["split"]["heldout_partition"]
    if partition not in ("validation", "audit"):
        raise ValueError("Wrong merged held-out partition")
    selections = {entry["shard_id"]: entry for entry in manifest["recipe_selections"]}
    source_lines = replayed = 0
    for identifier, wanted in requested.items():
        record = records[identifier]; original_binding = record["manifests"][partition]
        check_hash(original_binding["path"], original_binding["sha256"])
        original_manifest = _read(original_binding["path"])[0]
        original_manifest = copy.deepcopy(original_manifest)
        original_manifest["source_mappings"] = record["source_mappings"]
        directory = Path(original_binding["path"]).parent
        source_binding = original_manifest["files"]["validation.npz"]
        check_hash(directory / "validation.npz", source_binding["sha256"])
        source = _arrays(directory / "validation.npz", source_binding["rows"], original_manifest["filters"]["max_abs_score"])
        recipe_binding = original_manifest["artifacts"]["validation-provenance.jsonl"]
        check_hash(directory / "validation-provenance.jsonl", recipe_binding["sha256"])
        indices = []; original_rows = []; observed = set()
        for source_row, recipe in enumerate(_stream(directory / "validation-provenance.jsonl")):
            if source_row not in wanted:
                continue
            array_index, expected = wanted[source_row]
            if expected != recipe:
                raise ValueError("Merged recipe differs from original authenticated recipe")
            for key in ARRAY_NAMES:
                if not np.array_equal(source[key][source_row], data[key][array_index]):
                    raise ValueError("Merged native arrays differ from original prepared shard row")
            indices.append(array_index); original_rows.append(source_row); observed.add(source_row)
        if observed != set(wanted):
            raise ValueError("An original held-out shard row was not observed")
        selection = selections[identifier]
        if selection["rows"] != len(indices):
            raise ValueError("Frozen original-recipe selection count differs")
        selected_data = {key: data[key][indices] for key in ARRAY_NAMES}
        proof = validate_validation_provenance(directory, original_manifest, selected_data, _recipe_selection=selection)
        if proof["game_ids"] != [game_ids[index] for index in indices] or proof["position_keys"] != [keys[index] for index in indices]:
            raise ValueError("Native per-shard replay order differs from merged arrays")
        source_lines += proof["source_lines_replayed"]; replayed += proof["rows"]
        del source, selected_data
    if replayed != count:
        raise ValueError("Merged held-out source replay count differs")
    return {"rows": count, "game_ids": game_ids, "position_keys": keys,
        "represented_game_ids": sorted(set(game_ids)), "listed_validation_games": len(known),
        "source_lines_replayed": source_lines, "heldout_rows_replayed": replayed,
        "recipe_sha256": binding["sha256"],
        "scope": "All original immutable shard manifests/native arrays/recipes authenticated; selected source rows compared exactly; original compressed game/teacher rows and actual per-shard native HCE/features replayed. No native training arrays recomputed by merger."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard", action="append", required=True, help="ID=path to dataset root containing prepared/ and audit-prepared/")
    parser.add_argument("--source-map", action="append", default=[], help="ID=JSON list of absolute {from,to} evidence-root mappings")
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--min-positions", type=int, default=5000000)
    args = parser.parse_args(argv)
    if args.min_positions < 1:
        parser.error("Positive minimum required")
    return merge(args)


if __name__ == "__main__":
    raise SystemExit(main())
