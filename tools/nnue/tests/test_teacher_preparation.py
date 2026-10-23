"""Small fail-closed contracts for independent-teacher preparation."""
from __future__ import annotations

import copy
import gzip
import importlib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import chess
import numpy as np


class TeacherPreparationTests(unittest.TestCase):
    def setUp(self):
        self.tool = importlib.import_module("prepare_teacher_data")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def game(self):
        board = chess.Board(); board.push_uci("e2e4")
        sample = {"game_id": "g1", "split": "validation", "result_white": 1.0,
                  "fen": board.fen(en_passant="fen"), "ply": 1, "bestmove": "e7e5",
                  "score_cp_stm": 5, "engine_sha256": "b" * 64}
        original = {"game_id": "g1", "split": "validation", "result_white": 1.0,
                    "moves": ["e2e4", "e7e5"], "samples": [sample],
                    "engine_white_sha256": "a" * 64, "engine_black_sha256": "b" * 64}
        labelled = copy.deepcopy(original)
        labelled["samples"][0].update(source_sample_index=0, forge_score_cp_stm=5,
            score_cp_stm=-37, teacher_cp_stm=-37, teacher_kind="cp", teacher_depth=6,
            teacher_nodes=123, teacher_time_ms=1, teacher_wall_ms=1.2,
            teacher_bestmove="e7e5")
        return original, labelled

    def test_exact_position_priority_and_first_occurrence(self):
        index = self.tool.PositionIndex()
        fen = chess.STARTING_FEN
        key = self.tool.position_key(fen)
        index.add(key, "train", 0); index.add(key, "validation", 1)
        index.add(key, "train", 2); index.add(key, "audit", 3)
        index.add(key, "audit", 4)
        self.assertFalse(index.selected(key, "train", 0))
        self.assertFalse(index.selected(key, "validation", 1))
        self.assertTrue(index.selected(key, "audit", 3))
        self.assertFalse(index.selected(key, "audit", 4))
        self.assertEqual(index.counts(), {"train": 0, "validation": 0, "audit": 1})
        self.assertEqual(key, self.tool.position_key(fen.rsplit(" ", 2)[0] + " 9 20"))

    def test_black_teacher_pov_and_white_result_conversion(self):
        original, labelled = self.game()
        rows = self.tool.validate_labelled_game(original, labelled, {"a"*64,"b"*64}, 6, 1000)
        self.assertEqual(rows[0]["score_cp_stm"], -37)
        self.assertEqual(rows[0]["result_stm"], 0.0)

    def test_wrong_game_result_engine_teacher_or_prefix_is_rejected(self):
        mutations = [lambda g: g.update(game_id="other"),
            lambda g: g["samples"][0].update(game_id="other"),
            lambda g: g["samples"][0].update(result_white=0.0),
            lambda g: g["samples"][0].update(engine_sha256="a"*64),
            lambda g: g["samples"][0].update(teacher_cp_stm=37),
            lambda g: g["samples"][0].update(teacher_depth=5),
            lambda g: g["samples"][0].update(source_sample_index=1),
            lambda g: g["samples"][0].update(fen=chess.STARTING_FEN),
            lambda g: g["samples"][0].update(teacher_bestmove="e7e4")]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                original, labelled = self.game(); mutate(labelled)
                with self.assertRaises(ValueError):
                    self.tool.validate_labelled_game(original, labelled, {"a"*64,"b"*64}, 6, 1000)

    def test_unsampled_null_move_tail_is_rejected(self):
        original, labelled = self.game()
        original["moves"].extend(["g1f3", "0000"])
        labelled["moves"] = list(original["moves"])
        with self.assertRaisesRegex(ValueError, "Illegal complete game move"):
            self.tool.validate_labelled_game(original, labelled, {"a"*64,"b"*64}, 6, 1000)

    def test_legal_move_after_draw_termination_is_rejected(self):
        original, labelled = self.game()
        original["moves"] = ["g1f3", "g8f6", "f3g1", "f6g8"] * 2 + ["g1f3"]
        original["samples"] = []
        labelled = copy.deepcopy(original)
        with self.assertRaisesRegex(ValueError, "terminal"):
            self.tool.validate_labelled_game(original, labelled, {"a"*64,"b"*64}, 6, 1000)

    def test_source_hash_change_is_rejected(self):
        source = self.directory / "source.gz"; source.write_bytes(b"actual")
        digest = self.tool.sha256(source)
        self.tool.check_hash(source, digest)
        source.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "changed"):
            self.tool.check_hash(source, digest)

    def test_explicit_falsey_or_malformed_source_hash_is_rejected(self):
        source = self.directory / "source"; source.write_text("actual")
        sources = self.tool.TeacherSources.__new__(self.tool.TeacherSources)
        sources.bindings = {}
        sources.add(source, "test")  # Only an omitted/None digest is computed.
        for invalid in ("", False, 0, [], "a"*63, "G"*64):
            with self.subTest(declared_sha256=invalid), self.assertRaisesRegex(ValueError, "SHA-256"):
                sources.add(source, "test", invalid)

    def test_native_failure_retains_one_compressed_raw_record(self):
        probe = self.directory / "probe"
        probe.write_text("#!/usr/bin/env python3\nimport sys\nprint('broken')\nprint('failure',file=sys.stderr)\nsys.exit(7)\n")
        probe.chmod(0o700)
        evidence = self.directory / "evidence"
        with self.assertRaises(RuntimeError):
            self.tool.native_labels(probe, [{"fen": chess.STARTING_FEN}], evidence, 0)
        files = list(evidence.glob("*.json.gz")); self.assertEqual(len(files), 1)
        failure = json.load(gzip.open(files[0], "rt"))
        self.assertEqual(failure["returncode"], 7)
        self.assertIn("failure", failure["stderr"])
        self.assertIn(chess.STARTING_FEN, failure["stdin"])

    def test_native_success_exit_with_missing_rows_still_fails_closed(self):
        probe = self.directory / "probe-empty"
        probe.write_text("#!" + sys.executable + "\nimport sys\nsys.stdin.read()\n")
        probe.chmod(0o700)
        evidence = self.directory / "empty-evidence"
        with self.assertRaisesRegex(ValueError, "row count"):
            self.tool.native_labels(probe, [{"fen": chess.STARTING_FEN}], evidence, 3)
        failure = json.load(gzip.open(evidence / "failed-batch-000003.json.gz", "rt"))
        self.assertEqual(failure["returncode"], 0)
        self.assertEqual(failure["stdout"], "")

    @unittest.skipUnless(hasattr(os, "fork"), "Owned POSIX process-group contract")
    def test_native_timeout_kills_descendant_after_parent_exits(self):
        probe = self.directory / "probe-fork"
        probe.write_text("#!/bin/sh\nsleep 2 &\nprintf 'owned child %s\\n' \"$!\"\nexit 0\n")
        probe.chmod(0o700); evidence = self.directory / "timeout-evidence"
        started = time.monotonic()
        with self.assertRaises(subprocess.TimeoutExpired):
            self.tool.native_labels(probe, [{"fen": chess.STARTING_FEN}], evidence, 4, timeout=.15)
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 1.5, "Descendant pipes outlived the requested timeout")
        failure = json.load(gzip.open(evidence / "failed-batch-000004.json.gz", "rt"))
        self.assertEqual(failure["returncode"], 0)
        self.assertIn("owned child", failure["stdout"])

    def fixture(self):
        generated = self.directory / "generated"; (generated / "chunks").mkdir(parents=True)
        labelled = self.directory / "labelled"; (labelled / "chunks").mkdir(parents=True)
        identities = []
        for name in ("shipped", "opponent"):
            binary, network = self.directory / name, self.directory / (name + ".inc")
            binary.write_text(name); network.write_text(name + " network")
            identities.append({"path": str(binary), "sha256": self.tool.sha256(binary),
                "network_path": str(network), "network_sha256": self.tool.sha256(network), "source_commit": "a"*40})
        config = {"split_seed": 17, "validation_fraction": .2, "audit_fraction": .2,
                  "engines": identities, "max_ply": 4}
        config["config_sha256"] = hashlib.sha256(self.tool.encoded(config)).hexdigest()
        selected = {}
        for index in range(100):
            game_id = self.tool.game_identity(config["config_sha256"], index)
            split = self.tool.split_for_game(game_id, 17, .2, .2)
            selected.setdefault(split, index)
        originals, labels = [], []
        sequences = {"train": ["g1f3", "g8f6", "b1c3", "b8c6"],
                     "validation": ["e2e4", "e7e5", "g1f3", "b8c6"],
                     "audit": ["d2d4", "d7d5", "g1f3", "g8f6"]}
        for split, index in sorted(selected.items(), key=lambda pair: pair[1]):
            identity = self.tool.game_identity(config["config_sha256"], index)
            white, black = self.tool.pairing(index); board = chess.Board(); samples = []
            for ply, text in enumerate(sequences[split]):
                if ply in (0, 2):
                    samples.append({"game_id": identity, "game_index": index, "split": split,
                        "result_white": .5, "fen": board.fen(en_passant="fen"), "ply": ply,
                        "bestmove": text, "score_cp_stm": 17,
                        "engine_sha256": identities[white if board.turn else black]["sha256"]})
                board.push_uci(text)
            game = {"game_id": identity, "game_index": index, "split": split, "result_white": .5,
                "moves": sequences[split], "samples": samples, "final_fen": board.fen(en_passant="fen"),
                "termination": "adjudicated_max_ply_draw", "engine_white_sha256": identities[white]["sha256"],
                "engine_black_sha256": identities[black]["sha256"]}
            teacher_game = copy.deepcopy(game)
            for sample_index, sample in enumerate(teacher_game["samples"]):
                sample.update(source_sample_index=sample_index, forge_score_cp_stm=17,
                    score_cp_stm=-37, teacher_cp_stm=-37, teacher_kind="cp", teacher_depth=6,
                    teacher_nodes=123, teacher_time_ms=1, teacher_wall_ms=1.2, teacher_bestmove=sample["bestmove"])
            originals.append(game); labels.append(teacher_game)
        source = generated / "chunks/games-000000.jsonl.gz"
        teacher_source = labelled / "chunks/labels.jsonl.gz"
        for path, rows in ((source, originals), (teacher_source, labels)):
            with gzip.open(path, "wt") as stream:
                stream.writelines(json.dumps(row) + "\n" for row in rows)
        generation_manifest = {"status": "PASS_COMPLETED_GAMES_OWNED_ENGINES_CLOSED", "configuration": config,
            "chunks": [{"path": "chunks/games-000000.jsonl.gz", "sha256": self.tool.sha256(source)}]}
        self.tool.write_json(generated / "manifest.json", generation_manifest)
        teacher = self.directory / "teacher"; teacher.write_text("independent teacher")
        teacher_config = {"teacher_binary": str(teacher), "teacher_sha256": self.tool.sha256(teacher),
            "teacher_network_sha256": "c" * 64, "options": {"Threads": "1", "MultiPV": "1"},
            "input_dir": str(generated), "depth": 6, "policy": {"score_cap_cp": 1000, "score_pov": "side_to_move"}}
        teacher_manifest = {"status": "complete", "configuration": teacher_config, "chunks": [{
            "path": "labels.jsonl.gz", "sha256": self.tool.sha256(teacher_source),
            "source_path": str(source), "source_sha256": self.tool.sha256(source),
            "games": 3, "accepted": 6, "game_ids": [game["game_id"] for game in originals]}]}
        self.tool.write_json(labelled / "manifest.json", teacher_manifest)
        probe = self.directory / "probe"
        probe.write_text("#!" + sys.executable + "\nimport chess,json,sys\nfor index,line in enumerate(sys.stdin):\n b=chess.Board(line.strip()); fs=[]\n for perspective in [b.turn,not b.turn]:\n  fs.append([(0 if p.color==perspective else 384)+(p.piece_type-1)*64+(s if perspective else s^56) for s,p in b.piece_map().items()])\n print(json.dumps(dict(index=index,hce_cp_stm=18,nnue_cp_stm=None,nnue_available=True,residual_mode=True,hidden_size=128,hce_only=True,in_check=False,terminal=False,has_tactical_legal_move=False,features=fs)))\n")
        probe.chmod(0o700)
        receipt = self.directory / "probe-source.json"
        self.tool.write_json(receipt, {"probe_sha256": self.tool.sha256(probe),
            "sources": [{"path": str(probe), "sha256": self.tool.sha256(probe)}]})
        protocol = self.directory / "protocol.json"
        self.tool.write_json(protocol, {"target": {"kind": "teacher_probability_game_result_blend", "result_weight": .4,
            "sigmoid_k": 2.25, "cp_scale": 400.0}, "teacher": {"depth": 6,
            "binary_sha256": teacher_config["teacher_sha256"], "network_sha256": "c"*64,
            "options": teacher_config["options"], "policy": teacher_config["policy"]},
            "dataset": {"whole_game_split_seed": 17, "fractions": {"train": .6, "validation": .2, "audit": .2}}})
        return SimpleNamespace(teacher_manifest=labelled / "manifest.json", generation_manifest=None,
            probe=probe, probe_source=receipt, protocol=protocol, out=self.directory / "prepared-output",
            min_positions=1, batch_size=2)

    def test_streamed_prepare_isolates_audit_and_replays_actual_arrays(self):
        args = self.fixture()
        self.assertEqual(self.tool.prepare(args), 2)  # Five-million qualification cannot be bypassed.
        prepared, audit = args.out / "prepared", args.out / "audit-prepared"
        freeze = json.loads((args.out / "freeze.json").read_text())
        self.assertEqual(freeze["retained"], {"train": 1, "validation": 1, "audit": 2})
        self.assertFalse(freeze["training_permitted"])
        self.assertEqual((prepared / "train.npz").stat().st_ino, (audit / "train.npz").stat().st_ino)
        all_keys = []
        for directory in (prepared, audit):
            manifest = json.loads((directory / "manifest.json").read_text())
            with np.load(directory / "validation.npz") as archive:
                data = {key: archive[key] for key in archive.files}
            result = self.tool.validate_validation_provenance(directory, manifest, data)
            self.assertEqual(result["rows"], len(data["score"]))
            self.assertEqual(result["source_lines_replayed"], 2)
            self.assertEqual(result["heldout_rows_replayed"], len(data["score"]))
            all_keys.append(set(result["position_keys"]))
            data["score"][0] += 1
            with self.assertRaisesRegex(ValueError, "score/result"):
                self.tool.validate_validation_provenance(directory, manifest, data)
            data["score"][0] -= 1
            data["hce"][0] += 1
            with self.assertRaisesRegex(ValueError, "HCE"):
                self.tool.validate_validation_provenance(directory, manifest, data)
            data["hce"][0] -= 1
            data["features"][0, 0, 0] = 767
            with self.assertRaisesRegex(ValueError, "feature indices"):
                self.tool.validate_validation_provenance(directory, manifest, data)
        self.assertFalse(all_keys[0] & all_keys[1])

    def test_changed_frozen_split_seed_fraction_or_teacher_depth_is_rejected(self):
        args = self.fixture()
        sources = self.tool.TeacherSources(args.teacher_manifest)
        protocol = json.loads(args.protocol.read_text())
        mutations = [lambda p: p["dataset"].update(whole_game_split_seed=18),
                     lambda p: p["dataset"]["fractions"].update(audit=.1),
                     lambda p: p["teacher"].update(depth=8)]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                changed = copy.deepcopy(protocol); mutate(changed)
                with self.assertRaisesRegex(ValueError, "protocol"):
                    self.tool.validate_protocol(sources, changed)

    def test_frozen_teacher_binary_network_options_and_policy_are_bound(self):
        args = self.fixture(); sources = self.tool.TeacherSources(args.teacher_manifest)
        protocol = json.loads(args.protocol.read_text())
        mutations = [lambda t: t.update(binary_sha256="f"*64),
                     lambda t: t.update(network_sha256="f"*64),
                     lambda t: t["options"].update(Threads="99"),
                     lambda t: t["policy"].update(score_pov="white"),
                     lambda t: t.pop("options"), lambda t: t.pop("network_sha256")]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                changed = copy.deepcopy(protocol); mutate(changed["teacher"])
                with self.assertRaisesRegex(ValueError, "teacher"):
                    self.tool.validate_protocol(sources, changed)

    def test_native_adapter_lineage_files_are_bound_and_changes_rejected(self):
        args = self.fixture()
        path = self.directory / "generated/manifest.json"
        manifest = json.loads(path.read_text()); config = manifest["configuration"]
        config["native_batch"] = True
        receipts = []
        for index, engine in enumerate(config["engines"]):
            for key in ("frozen_core", "original_uci_reference", "adapter_source"):
                artifact = self.directory / (str(index) + "-" + key); artifact.write_text(key)
                engine[key] = {"path": str(artifact), "sha256": self.tool.sha256(artifact)}
                receipts.append(artifact)
        del config["config_sha256"]
        config["config_sha256"] = hashlib.sha256(self.tool.encoded(config)).hexdigest()
        self.tool.write_json(path, manifest)
        sources = self.tool.TeacherSources(args.teacher_manifest)
        self.assertTrue(set(receipts) <= set(sources.bindings))
        for artifact in receipts:
            artifact.write_text("changed")
            with self.assertRaisesRegex(ValueError, "changed"):
                self.tool.TeacherSources(args.teacher_manifest)
            artifact.write_text(artifact.name.split("-", 1)[1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
