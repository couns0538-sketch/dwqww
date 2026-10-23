"""Strict data and game-split contracts for the residual training pipeline.

Legacy three-field rows carry no genuine game ID or best move. These tests
deliberately prevent the cleaner from inventing either to qualify validation.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest import mock

import chess
import chess.engine

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))


def sample_record(**changes):
    row = {
        "fen": chess.STARTING_FEN,
        "score_cp_stm": 120,
        "result_white": 1.0,
        "game_id": "test-run:17",
        "ply": 0,
        "bestmove": "e2e4",
        "engine_sha256": "a" * 64,
    }
    row.update(changes)
    return row


class AuthenticatedRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preparation = importlib.import_module("prepare_residual_data")

    def test_valid_quiet_record_keeps_its_authentic_identity_and_input_unchanged(self):
        row = sample_record()
        before = copy.deepcopy(row)
        actual = self.preparation.validate_record(row)
        self.assertEqual(row, before)
        self.assertEqual(actual["game_id"], row["game_id"])
        self.assertEqual(actual["ply"], 0)
        self.assertEqual(actual["score_cp_stm"], 120)
        self.assertEqual(actual["engine_sha256"], "a" * 64)
        self.assertEqual(actual["result_stm"], 1.0)

    def test_black_result_is_reflected_but_an_already_stm_score_is_not(self):
        board = chess.Board()
        board.push_uci("e2e4")
        row = sample_record(fen=board.fen(), ply=1, bestmove="e7e5", score_cp_stm=150)
        actual = self.preparation.validate_record(row)
        self.assertEqual(actual["score_cp_stm"], 150)
        self.assertEqual(actual["result_white"], 1.0)
        self.assertEqual(actual["result_stm"], 0.0)
        row["result_white"] = 0.0
        self.assertEqual(self.preparation.validate_record(row)["result_stm"], 1.0)

    def test_draw_stays_half_from_either_perspective(self):
        white = sample_record(result_white=0.5)
        board = chess.Board()
        board.push_uci("e2e4")
        black = sample_record(fen=board.fen(), ply=1, bestmove="e7e5", result_white=0.5)
        for row in (white, black):
            with self.subTest(fen=row["fen"]):
                self.assertEqual(self.preparation.validate_record(row)["result_stm"], 0.5)

    def test_missing_game_or_move_provenance_cannot_be_replaced_by_a_default(self):
        for key in ("game_id", "ply", "bestmove", "engine_sha256"):
            with self.subTest(key=key):
                row = sample_record()
                del row[key]
                with self.assertRaises(ValueError):
                    self.preparation.validate_record(row)

    def test_a_legacy_three_field_line_cannot_qualify_as_an_authenticated_game_record(self):
        with self.assertRaises(ValueError):
            self.preparation.validate_record(chess.STARTING_FEN + " | 120 | 1.0")

    def test_game_id_and_engine_digest_must_be_real_nonempty_identifiers(self):
        for value in (None, "", "   ", 17, True):
            with self.subTest(game_id=value), self.assertRaises(ValueError):
                self.preparation.validate_record(sample_record(game_id=value))
        for value in (None, "", "a" * 63, "a" * 65, "z" * 64, 123):
            with self.subTest(engine_sha256=value), self.assertRaises(ValueError):
                self.preparation.validate_record(sample_record(engine_sha256=value))

    def test_teacher_scores_are_finite_integer_centipawns_not_mate_or_bound_labels(self):
        for value in (True, "120", 1.5, float("nan"), float("inf"), "#3", "120 lowerbound"):
            with self.subTest(score=value), self.assertRaises(ValueError):
                self.preparation.validate_record(sample_record(score_cp_stm=value))

    def test_score_cap_is_applied_in_both_directions_inclusively(self):
        for score in (-1000, 0, 1000):
            with self.subTest(score=score):
                actual = self.preparation.validate_record(sample_record(score_cp_stm=score), score_cap=1000)
                self.assertEqual(actual["score_cp_stm"], score)
        for score in (-1001, 1001):
            with self.subTest(score=score), self.assertRaises(ValueError):
                self.preparation.validate_record(sample_record(score_cp_stm=score), score_cap=1000)

    def test_result_is_a_finite_white_outcome_not_an_arbitrary_probability(self):
        for value in (True, None, -1.0, 0.1, 0.75, 2.0, float("nan"), float("inf")):
            with self.subTest(result=value), self.assertRaises(ValueError):
                self.preparation.validate_record(sample_record(result_white=value))

    def test_ply_is_the_actual_board_ply_not_an_invented_sample_index(self):
        for value in (-1, 1, 99, True, "0", 0.5):
            with self.subTest(ply=value), self.assertRaises(ValueError):
                self.preparation.validate_record(sample_record(ply=value))

    def test_invalid_and_truncated_fens_are_not_silently_repaired(self):
        for fen in ("", "8/8/8/8/8/8/8/8 w - - 0 1", " ".join(chess.STARTING_FEN.split()[:4])):
            with self.subTest(fen=fen), self.assertRaises(ValueError):
                self.preparation.validate_record(sample_record(fen=fen))

    def test_bestmove_must_be_a_legal_full_move_on_this_board(self):
        for move in (None, "", "0000", "e2e5", "e7e5", "e2e4q"):
            with self.subTest(move=move), self.assertRaises(ValueError):
                self.preparation.validate_record(sample_record(bestmove=move))

    def test_in_check_position_is_filtered_even_for_a_quiet_legal_evasion(self):
        row = sample_record(fen="6k1/8/8/8/8/8/4r3/4K3 w - - 0 1", bestmove="e1d1")
        board = chess.Board(row["fen"])
        self.assertTrue(board.is_valid() and board.is_check())
        self.assertIn(chess.Move.from_uci(row["bestmove"]), board.legal_moves)
        with self.assertRaises(ValueError):
            self.preparation.validate_record(row)

    def test_capture_and_promotion_bestmoves_are_filtered(self):
        fixtures = [
            ("6k1/8/8/8/8/8/p7/R5K1 w - - 0 1", "a1a2"),
            ("6k1/P7/8/8/8/8/8/6K1 w - - 0 1", "a7a8n"),
        ]
        for fen, move in fixtures:
            with self.subTest(fen=fen):
                board = chess.Board(fen)
                self.assertTrue(board.is_valid())
                self.assertIn(chess.Move.from_uci(move), board.legal_moves)
                with self.assertRaises(ValueError):
                    self.preparation.validate_record(sample_record(fen=fen, bestmove=move))

    def test_quiet_checking_bestmove_is_filtered_too(self):
        row = sample_record(fen="6k1/8/8/8/8/8/8/R5K1 w - - 0 1", bestmove="a1a8")
        board = chess.Board(row["fen"])
        move = chess.Move.from_uci(row["bestmove"])
        self.assertTrue(board.is_valid() and move in board.legal_moves)
        self.assertFalse(board.is_capture(move) or bool(move.promotion))
        self.assertTrue(board.gives_check(move))
        with self.assertRaises(ValueError):
            self.preparation.validate_record(row)


class WholeGameSplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preparation = importlib.import_module("prepare_residual_data")

    def test_partition_is_a_stable_function_of_authentic_game_id(self):
        for game_id in ("run-a:0", "run-a:1", "run-a:103", "run-b:0"):
            expected = self.preparation.split_for_game(game_id, seed=20261023, fraction=0.2)
            self.assertIn(expected, ("train", "validation"))
            for _ in range(30):
                self.assertEqual(self.preparation.split_for_game(game_id, seed=20261023, fraction=0.2), expected)

    def test_different_plies_and_positions_of_one_game_share_its_partition(self):
        board = chess.Board()
        partition = self.preparation.split_for_game("run-a:17", seed=20261023, fraction=0.2)
        for move in ("e2e4", "e7e5", "g1f3", "b8c6"):
            board.push_uci(move)
            row = sample_record(fen=board.fen(), ply=board.ply(), game_id="run-a:17")
            self.assertEqual(self.preparation.split_for_game(row["game_id"], seed=20261023, fraction=0.2), partition)

    def test_validation_selection_is_not_every_game_or_a_per_position_coin_flip(self):
        values = [self.preparation.split_for_game(f"run-a:{game}", seed=20261023, fraction=0.2)
                  for game in range(2000)]
        self.assertTrue(set(values) <= {"train", "validation"})
        self.assertGreater(values.count("validation"), 200)
        self.assertLess(values.count("validation"), 600)

    def test_invalid_split_configuration_fails_before_partitioning(self):
        for fraction in (-0.1, 0.0, 1.0, 1.1, float("nan"), float("inf")):
            with self.subTest(fraction=fraction), self.assertRaises(ValueError):
                self.preparation.split_for_game("run-a:0", seed=20261023, fraction=fraction)
        for game_id in (None, "", "  ", 17):
            with self.subTest(game_id=game_id), self.assertRaises(ValueError):
                self.preparation.split_for_game(game_id, seed=20261023, fraction=0.2)


class ValidationLeakageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preparation = importlib.import_module("prepare_residual_data")

    def test_validation_key_ignores_only_move_counters(self):
        first = chess.STARTING_FEN
        changed_counters = " ".join(first.split()[:4]) + " 87 129"
        self.assertEqual(self.preparation.position_key(first),
                         self.preparation.position_key(changed_counters))
        self.assertEqual(self.preparation.position_key(first), " ".join(first.split()[:4]))

    def test_side_castling_and_ep_stay_in_the_declared_position_key(self):
        first = chess.STARTING_FEN
        for index, value in ((1, "b"), (2, "-"), (3, "e3")):
            fields = first.split()
            fields[index] = value
            with self.subTest(index=index):
                self.assertNotEqual(self.preparation.position_key(first),
                                    self.preparation.position_key(" ".join(fields)))

    def test_held_out_positions_are_removed_from_legacy_and_authenticated_training(self):
        validation_key = self.preparation.position_key(chess.STARTING_FEN)
        after_e4 = chess.Board()
        after_e4.push_uci("e2e4")
        legacy = {"fen": " ".join(chess.STARTING_FEN.split()[:4]) + " 20 91",
                  "score_cp_stm": 10, "result_white": 0.5}
        authenticated = sample_record(game_id="different-training-game:2")
        keep = sample_record(fen=after_e4.fen(), ply=1, bestmove="e7e5", game_id="train:3")
        inputs = [legacy, authenticated, keep]
        before = copy.deepcopy(inputs)
        actual = list(self.preparation.exclude_validation_positions(inputs, {validation_key}))
        self.assertEqual(actual, [keep])
        self.assertEqual(inputs, before)
        self.assertNotIn("game_id", legacy)  # Removing leakage does not invent provenance.


class CompletedGamePublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generation = importlib.import_module("generate_residual_data")

    def record(self):
        row = sample_record()
        return {name: row[name] for name in ("fen", "score_cp_stm", "ply", "bestmove")}

    def test_unfinished_game_cannot_publish_result_labels_or_create_a_data_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "games.jsonl"
            count = self.generation.write_completed_game(
                path, game_id="run:1", records=[self.record()], result_white=None,
                engine_sha256="a" * 64,
            )
            self.assertEqual(count, 0)
            self.assertFalse(path.exists())

    def test_completed_game_publishes_real_id_ply_move_score_and_white_result(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "games.jsonl"
            count = self.generation.write_completed_game(
                path, game_id="run:1", records=[self.record()], result_white=0.5,
                engine_sha256="a" * 64,
            )
            self.assertEqual(count, 1)
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(rows, [sample_record(game_id="run:1", result_white=0.5)])

    def test_tactical_record_is_not_mislabelled_as_a_quiet_training_position(self):
        tactical = {"fen": "6k1/8/8/8/8/8/8/R5K1 w - - 0 1",
                    "score_cp_stm": 300, "ply": 0, "bestmove": "a1a8"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "games.jsonl"
            count = self.generation.write_completed_game(
                path, game_id="run:1", records=[self.record(), tactical], result_white=1.0,
                engine_sha256="a" * 64,
            )
            self.assertEqual(count, 1)
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual([row["bestmove"] for row in rows], ["e2e4"])

    def test_generator_manifest_hashes_actual_bytes_and_reports_options_and_completed_games(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            engine, network, positions = root / "forge", root / "nnue_weights.inc", root / "games.jsonl"
            engine.write_bytes(b"inert unit fixture: no executable is run")
            network.write_bytes(b"inert unit network fixture")
            engine_hash = hashlib.sha256(engine.read_bytes()).hexdigest()
            self.generation.write_completed_game(
                positions, game_id="run:1", records=[self.record()], result_white=0.5,
                engine_sha256=engine_hash,
            )
            manifest = self.generation.build_manifest(
                engine_path=engine, network_path=network, positions_path=positions,
                source_commit="b" * 40, completed_game_ids=["run:1"],
                seed=20261023, nodes=5000, workers=2,
            )
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["source_commit"], "b" * 40)
            self.assertEqual(manifest["engine"]["sha256"], engine_hash)
            self.assertEqual(manifest["network"]["sha256"], hashlib.sha256(network.read_bytes()).hexdigest())
            self.assertEqual(manifest["positions"]["sha256"], hashlib.sha256(positions.read_bytes()).hexdigest())
            self.assertEqual(manifest["positions"]["rows"], 1)
            self.assertEqual(manifest["completed_game_ids"], ["run:1"])
            self.assertEqual(manifest["completed_games"], 1)
            self.assertEqual(manifest["options"], {"Threads": 1, "Hash": 16, "OwnBook": False})
            self.assertEqual(manifest["search"]["nodes"], 5000)
            self.assertEqual(manifest["seed"], 20261023)
            self.assertEqual(manifest["workers"], 2)
            self.assertEqual(manifest["termination"]["max_ply"], 300)
            self.assertEqual(manifest["termination"]["max_ply_result"], "adjudicated_draw")


class ExistingGeneratorHookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selfplay = importlib.import_module("forge_selfplay")

    def test_record_hook_preserves_old_return_format_and_exposes_pre_move_identity(self):
        class FakeEngine:
            protocol = SimpleNamespace(score_is_bound=False)

            def play(self, board, limit, **kwargs):
                move = chess.Move.from_uci(("e2e4", "e7e5")[board.ply()])
                return SimpleNamespace(move=move, info={
                    "score": chess.engine.PovScore(chess.engine.Cp(15), board.turn),
                })

        args = SimpleNamespace(opening_plies=0, max_ply=2, depth=None, nodes=1,
                               max_score=3000, adjudicate_cp=2000, adjudicate_plies=4)
        import random
        observed = []
        legacy = self.selfplay.play_game(FakeEngine(), args, random.Random(4), threading.Event())
        actual = self.selfplay.play_game(FakeEngine(), args, random.Random(4), threading.Event(),
                                         record_hook=observed.append)
        self.assertEqual(actual, legacy)
        self.assertEqual(actual[1], 0.5)  # Explicit max-ply adjudication, not a natural draw claim.
        self.assertEqual([row["ply"] for row in observed], [0, 1])
        self.assertEqual([row["bestmove"] for row in observed], ["e2e4", "e7e5"])
        self.assertEqual([(row["fen"], row["score_cp_stm"]) for row in observed], actual[0])
        self.assertEqual(observed[0]["fen"], chess.STARTING_FEN)


class DataToolFailureRetentionTests(unittest.TestCase):
    def test_native_parser_failures_retain_original_streams_even_after_normal_exit(self):
        preparation = importlib.import_module("prepare_residual_data")
        for response in (b"not-json\n", b"", b"{}\n"):
            with self.subTest(response=response), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                producer = root / "inert-producer"
                producer.write_text("#!" + sys.executable + "\nimport sys\nsys.stdin.buffer.read()\n"
                                    + "sys.stdout.buffer.write(" + repr(response) + ")\n")
                producer.chmod(0o700)
                with self.assertRaises(ValueError):
                    preparation.native_labels(producer, [sample_record()], root, 0)
                stem = root / "batch-00000"
                self.assertEqual(stem.with_suffix(".failed.stdin").read_bytes(),
                                 (chess.STARTING_FEN + "\n").encode("ascii"))
                self.assertEqual(stem.with_suffix(".failed.stdout").read_bytes(), response)
                self.assertEqual(stem.with_suffix(".failed.stderr").read_bytes(), b"")

    def test_worker_persistence_failure_does_not_hang_waiting_for_a_lost_done_message(self):
        generation = importlib.import_module("generate_residual_data")
        original_open = Path.open
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            engine, network, output = root / "inert-engine", root / "network", root / "output"
            engine.write_bytes(b"never executed")
            network.write_bytes(b"inert fixture")

            def fail_trace(path, *args, **kwargs):
                if path.name == "worker-0-uci.jsonl":
                    raise OSError("injected worker evidence failure")
                return original_open(path, *args, **kwargs)

            started = time.monotonic()
            with mock.patch.object(Path, "open", fail_trace), mock.patch.object(chess.engine.SimpleEngine, "popen") as spawn:
                result = generation.main([
                    "--engine", str(engine), "--network", str(network), "--out", str(output),
                    "--source-commit", "b" * 40, "--games", "1", "--workers", "1", "--nodes", "1",
                    "--time-limit-seconds", "0.2",
                ])
            self.assertEqual(result, 1)
            self.assertLess(time.monotonic() - started, 3)
            spawn.assert_not_called()
            self.assertEqual((output / "games.jsonl").read_bytes(), b"")
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "FAILED_OR_INCOMPLETE_GENERATION")
            self.assertEqual(manifest["completed_games"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
