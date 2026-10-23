"""Prepared shards preserve original evidence and cannot bypass qualification."""
import copy
import gzip
import importlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

import numpy as np
import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import prepare_teacher_data as preparation
import test_teacher_preparation as original_tests


class MergeTests(unittest.TestCase):
    def setUp(self):
        self.tool = importlib.import_module("merge_teacher_prepared")
        self.temporary = tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def shard(self, index):
        case = original_tests.TeacherPreparationTests(); case.tool = preparation
        case.directory = self.root / ("shard" + str(index)); case.directory.mkdir()
        args = case.fixture()
        generation_path = case.directory / "generated/manifest.json"
        generation = json.loads(generation_path.read_bytes()); config = generation["configuration"]
        config["seed"] = 100 + index; config.pop("config_sha256")
        config["config_sha256"] = __import__("hashlib").sha256(preparation.encoded(config)).hexdigest()
        originals_path = case.directory / "generated/chunks/games-000000.jsonl.gz"
        labels_path = case.directory / "labelled/chunks/labels.jsonl.gz"
        originals = [json.loads(line) for line in gzip.open(originals_path, "rt")]
        labels = [json.loads(line) for line in gzip.open(labels_path, "rt")]
        for original, labelled in zip(originals, labels):
            if index == 1:
                # A train key from shard0 becomes audit in shard1. Keep other
                # unique rows in every partition and both held-out sources.
                sequences = {"train": ["e2e3", "d7d5", "g1f3", "g8f6"],
                    "validation": ["c2c4", "e7e5", "g1f3", "b8c6"],
                    "audit": ["g1f3", "g8f6", "b1c3", "b8c6"]}
                moves = sequences[original["split"]]; board = chess.Board(); fens = []
                for move in moves:
                    fens.append(board.fen(en_passant="fen")); board.push_uci(move)
                for game in (original, labelled):
                    game["moves"] = moves; game["final_fen"] = board.fen(en_passant="fen")
                    for sample in game["samples"]:
                        sample["fen"] = fens[sample["ply"]]; sample["bestmove"] = moves[sample["ply"]]
                        if "teacher_bestmove" in sample:
                            sample["teacher_bestmove"] = sample["bestmove"]
            for game_index in range(1000):
                identity = preparation.game_identity(config["config_sha256"], game_index)
                if preparation.split_for_game(identity, 17, .2, .2) == original["split"]:
                    break
            white, black = preparation.pairing(game_index)
            for game in (original, labelled):
                game.update(game_id=identity, game_index=game_index,
                    engine_white_sha256=config["engines"][white]["sha256"],
                    engine_black_sha256=config["engines"][black]["sha256"])
                for sample in game["samples"]:
                    sample.update(game_id=identity, game_index=game_index,
                        engine_sha256=config["engines"][white if sample["fen"].split()[1] == "w" else black]["sha256"])
        for path, games in ((originals_path, originals), (labels_path, labels)):
            with gzip.open(path, "wt") as stream:
                stream.writelines(json.dumps(game) + "\n" for game in games)
        generation["chunks"][0]["sha256"] = preparation.sha256(originals_path)
        preparation.write_json(generation_path, generation)
        teacher = json.loads(args.teacher_manifest.read_bytes())
        teacher["chunks"][0].update(sha256=preparation.sha256(labels_path),
            source_sha256=preparation.sha256(originals_path), game_ids=[g["game_id"] for g in originals])
        preparation.write_json(args.teacher_manifest, teacher)
        protocol = json.loads(args.protocol.read_bytes()); protocol["dataset"]["generation_seed"] = 100 + index
        preparation.write_json(args.protocol, protocol)
        self.assertEqual(preparation.prepare(args), 2)
        return args

    def merger(self, shards):
        protocol = json.loads(shards[0].protocol.read_bytes())
        protocol["dataset"]["generation_seed"] = 100
        protocol_path = self.root / "merge-protocol.json"; preparation.write_json(protocol_path, protocol)
        return SimpleNamespace(shard=[str(i) + "=" + str(s.out) for i, s in enumerate(shards)],
            source_map=[], protocol=protocol_path, out=self.root / "merged", min_positions=1)

    def test_merge_deduplicates_and_keeps_five_million_gate(self):
        args = self.merger([self.shard(0), self.shard(1)])
        self.assertEqual(self.tool.merge(args), 2)
        freeze = json.loads((args.out / "freeze.json").read_bytes())
        self.assertFalse(freeze["training_permitted"])
        self.assertEqual(freeze["retained"], {"train": 1, "validation": 2, "audit": 3})
        knight = chess.Board(); knight.push_uci("g1f3"); knight.push_uci("g8f6")
        knight_key = preparation.position_key(knight.fen())
        train_keys = {preparation.position_key(row["fen"]) for row in self.tool._stream(args.out / "recipe-selections/train/0.jsonl.gz")}
        self.assertNotIn(knight_key, train_keys)
        for role in ("prepared", "audit-prepared"):
            directory = args.out / role; manifest = json.loads((directory / "manifest.json").read_bytes())
            with np.load(directory / "validation.npz") as archive:
                data = {key: archive[key] for key in archive.files}
            replay = preparation.validate_validation_provenance(directory, manifest, data)
            self.assertEqual(replay["rows"], len(data["score"]))
            self.assertEqual(replay["represented_game_ids"], sorted(set(replay["game_ids"])))
            if role == "audit-prepared":
                self.assertEqual(len(replay["represented_game_ids"]), 2)
                self.assertIn(knight_key, replay["position_keys"])
            data["hce"][0] += 1
            with self.assertRaises(ValueError):
                preparation.validate_validation_provenance(directory, manifest, data)

    def test_wrong_predeclared_seed_and_changed_source_are_rejected(self):
        shards = [self.shard(0), self.shard(1)]; args = self.merger(shards)
        args.shard[1] = "2=" + str(shards[1].out)
        with self.assertRaisesRegex(ValueError, "seed"):
            self.tool.merge(args)
        args.out = self.root / "changed"; args.shard[1] = "1=" + str(shards[1].out)
        (self.root / "shard1/teacher").write_text("changed source")
        with self.assertRaisesRegex(ValueError, "changed"):
            self.tool.merge(args)

    def test_relocation_resolver_keeps_original_bytes(self):
        original = self.root / "original"; original.mkdir(); path = original / "a.txt"; path.write_text("same bytes")
        relocated = self.root / "relocated"; original.rename(relocated)
        resolver = preparation.SourceResolver([{"from": str(original), "to": str(relocated)}])
        self.assertEqual(resolver(path), relocated / "a.txt")
        preparation.check_hash(resolver(path), preparation.sha256(relocated / "a.txt"))

    def test_relocated_original_shards_merge_and_native_replay(self):
        shards = [self.shard(0), self.shard(1)]; args = self.merger(shards)
        for index, shard in enumerate(shards):
            old = self.root / ("shard" + str(index)); moved = self.root / ("moved" + str(index))
            old.rename(moved)
            mapping = self.root / (str(index) + "-mapping.json")
            preparation.write_json(mapping, [{"from": str(old / "protocol.json"),
                "to": str(moved / "prepared-output/inputs/protocol.json")},
                {"from": str(old), "to": str(moved)}])
            args.shard[index] = str(index) + "=" + str(moved / "prepared-output")
            args.source_map.append(str(index) + "=" + str(mapping))
        self.assertEqual(self.tool.merge(args), 2)
        directory = args.out / "audit-prepared"
        manifest = json.loads((directory / "manifest.json").read_bytes())
        with np.load(directory / "validation.npz") as archive:
            data = {key: archive[key] for key in archive.files}
        proof = preparation.validate_validation_provenance(directory, manifest, data)
        self.assertEqual(proof["rows"], 3)
        self.assertEqual(len(proof["represented_game_ids"]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
