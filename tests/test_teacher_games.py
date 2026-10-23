"""Integrity tests for fresh, completed-game teacher-data generation."""
import gzip
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest

import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "nnue"))
import generate_teacher_games as gen


class GameContractTests(unittest.TestCase):
    def test_split_opening_and_pairing_are_reproducible(self):
        seen = set()
        for index in range(100):
            first = gen.opening_for_game(777, index, 8, 24)
            self.assertEqual(first, gen.opening_for_game(777, index, 8, 24))
            seed, moves = first
            self.assertGreaterEqual(len(moves), 8)
            self.assertLessEqual(len(moves), 24)
            board = chess.Board()
            for move in moves:
                board.push_uci(move)
            seen.add(tuple(moves))
            game_id = gen.game_identity("a" * 64, index)
            self.assertEqual(gen.split_for_game(game_id, 777, .1, .1),
                             gen.split_for_game(game_id, 777, .1, .1))
        self.assertGreater(len(seen), 95)
        self.assertEqual([gen.pairing(i) for i in range(4)], [(0, 0), (0, 1), (0, 0), (1, 0)])

    def test_quiet_filter_rejects_checks_captures_promotions_and_bounds(self):
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        self.assertTrue(gen.eligible(board, move, {"cp": 1000, "bound": False}, 1000))
        self.assertFalse(gen.eligible(board, move, {"cp": 1001, "bound": False}, 1000))
        self.assertFalse(gen.eligible(board, move, {"cp": -1001, "bound": False}, 1000))
        self.assertFalse(gen.eligible(board, move, {"cp": 0, "bound": True}, 1000))
        self.assertFalse(gen.eligible(board, move, {"mate": 3, "bound": False}, 1000))
        board = chess.Board("4k3/8/8/8/8/8/8/R3K3 w Q - 0 1")
        self.assertTrue(board.gives_check(chess.Move.from_uci("a1a8")))
        self.assertFalse(gen.eligible(board, chess.Move.from_uci("a1a8"), {"cp": 5}, 1000))
        board = chess.Board("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
        self.assertFalse(gen.eligible(board, chess.Move.from_uci("a7a8n"), {"cp": 5}, 1000))
        board = chess.Board("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1")
        self.assertFalse(gen.eligible(board, chess.Move.from_uci("e5d6"), {"cp": 5}, 1000))

    def test_score_parser_replaces_bound_and_score_kind(self):
        score = gen.parse_score("info depth 2 score cp 3 lowerbound nodes 64")
        self.assertEqual(score, {"cp": 3, "bound": True})
        self.assertEqual(gen.parse_score("info depth 3 score cp 7 nodes 66"), {"cp": 7, "bound": False})
        self.assertEqual(gen.parse_score("info depth 4 score mate -2 upperbound"), {"mate": -2, "bound": True})
        self.assertIsNone(gen.parse_score("info nodes 64 nps 1000"))
        self.assertIsNone(gen.parse_score("info string prior score cp 99"))

    def test_search_without_fresh_score_never_inherits_prior_score(self):
        class Transcript:
            def send(self, line):
                pass
            def until(self, terminal):
                return ["bestmove e2e4"]
        move, score = gen.UciEngine.search(Transcript(), [], 64)
        self.assertEqual(move, "e2e4")
        self.assertEqual(score, {})
        # Generator scores are diagnostics. Independent teacher labels this
        # quiet position later; absence of Forge info must not bias sampling.
        self.assertTrue(gen.eligible(chess.Board(), chess.Move.from_uci(move), score, 1000))

    def test_checkmate_precedes_draw_limit(self):
        board = chess.Board()
        for move in ("f2f3", "e7e5", "g2g4", "d8h4"):
            board.push_uci(move)
        self.assertEqual(gen.terminal_result(board, 4), (0.0, "checkmate"))
        self.assertEqual(gen.terminal_result(chess.Board(), 0), (0.5, "adjudicated_max_ply_draw"))

    def test_zeroing_history_window_preserves_fen_and_repetition(self):
        board = chess.Board()
        window = gen.HistoryWindow()
        all_moves = ["e2e4", "e7e5", "g1f3", "b8c6", "f3g1", "c6b8", "g1f3", "b8c6"]
        for text in all_moves:
            move = chess.Move.from_uci(text)
            zeroing = board.is_zeroing(move)
            board.push(move)
            window.after_move(board, zeroing)
        self.assertEqual(window.start_ply, 2)
        rebuilt = chess.Board(window.fen)
        for text in all_moves[window.start_ply:]:
            rebuilt.push_uci(text)
        self.assertEqual(rebuilt.fen(en_passant="fen"), board.fen(en_passant="fen"))
        self.assertEqual(rebuilt.is_repetition(2), board.is_repetition(2))
        self.assertEqual(rebuilt.is_repetition(3), board.is_repetition(3))

    def test_zeroing_window_on_random_walk_ep_promotion_and_castling(self):
        walks = [(chess.Board(), ["e2e4", "a7a6", "e4e5", "d7d5", "e5d6"]),
                 (chess.Board(), ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "e1g1"]),
                 (chess.Board("4k3/P7/8/8/8/8/8/4K3 w - - 0 1"), ["a7a8n"])]
        import random
        rng = random.Random(527)
        board, random_moves = chess.Board(), []
        for _ in range(500):
            legal = list(board.legal_moves)
            if not legal:
                break
            move = rng.choice(legal)
            random_moves.append(move.uci())
            board.push(move)
        walks.append((chess.Board(), random_moves))
        checked = 0
        for board, moves in walks:
            initial_fen, window, prefix = board.fen(en_passant="fen"), gen.HistoryWindow(), []
            initial_ply = board.ply()
            for text in moves:
                move = chess.Move.from_uci(text)
                zeroing = board.is_zeroing(move)
                board.push(move)
                prefix.append(text)
                window.after_move(board, zeroing)
                rebuilt = chess.Board(window.fen or initial_fen)
                for prior in prefix[max(0, window.start_ply - initial_ply):]:
                    rebuilt.push_uci(prior)
                self.assertEqual(rebuilt.fen(en_passant="fen"), board.fen(en_passant="fen"))
                self.assertEqual(gen.repetition_key(rebuilt), gen.repetition_key(board))
                for repeats in (2, 3):
                    self.assertEqual(rebuilt.is_repetition(repeats), board.is_repetition(repeats))
                checked += 1
        self.assertGreater(checked, 100)

    def test_store_freezes_config_and_hashes_and_excludes_partial_tails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = {"seed": 3, "engines": [{"sha256": "a" * 64}]}
            store = gen.ChunkStore(root, config, chunk_games=2)
            for index in range(2):
                store.append({"game_id": str(index), "game_index": index, "split": "train",
                              "result_white": .5, "samples": [{"game_id": str(index), "split": "train"}]})
            store.close()
            checkpoint = json.loads((root / "manifest.json").read_text())
            self.assertEqual(checkpoint["completed_games"], 2)
            self.assertEqual(checkpoint["eligible_positions"], 2)
            chunk = root / checkpoint["chunks"][0]["path"]
            with gzip.open(chunk, "rt") as stream:
                self.assertEqual(len(list(stream)), 2)
            (root / "chunks" / "ignored.jsonl.gz.part").write_text("incomplete")
            resumed = gen.ChunkStore(root, config, chunk_games=2, resume=True)
            self.assertEqual(resumed.next_index, 2)
            resumed.close()
            with self.assertRaisesRegex(ValueError, "configuration"):
                gen.ChunkStore(root, {"seed": 4}, chunk_games=2, resume=True)
            chunk.write_bytes(chunk.read_bytes() + b"tampered")
            with self.assertRaisesRegex(ValueError, "hash"):
                gen.ChunkStore(root, config, chunk_games=2, resume=True)

    def test_incomplete_or_duplicate_game_is_rejected_before_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            store = gen.ChunkStore(Path(temp), {"seed": 1}, chunk_games=2)
            with self.assertRaises(ValueError):
                store.append({"game_id": "x", "game_index": 0, "split": "train", "result_white": None, "samples": []})
            valid = {"game_id": "x", "game_index": 0, "split": "train", "result_white": .5, "samples": []}
            store.append(valid)
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                store.append(valid)
            store.close()
            self.assertEqual(json.loads((Path(temp) / "manifest.json").read_text())["completed_games"], 1)

    def test_resume_recovers_only_authenticated_trace_prefix(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = gen.ChunkStore(root, {"seed": 1}, chunk_games=2)
            store.close()
            trace = root / "process-trace.jsonl.gz"
            committed = gzip.compress(b'{"complete":true}\n', mtime=0)
            trace.write_bytes(committed)
            manifest = json.loads((root / "manifest.json").read_text())
            manifest["process_trace"] = {"path": trace.name, "sha256": gen.sha256(trace), "bytes": len(committed)}
            (root / "manifest.json").write_text(json.dumps(manifest))
            tail = gzip.compress(b'{"uncommitted":true}\n', mtime=0)
            trace.write_bytes(committed + tail)
            resumed = gen.ChunkStore(root, {"seed": 1}, chunk_games=2, resume=True)
            self.assertEqual(trace.read_bytes(), committed)
            self.assertEqual((root / "process-trace.uncommitted.jsonl.gz").read_bytes(), tail)
            resumed.close()


class OwnedProcessTests(unittest.TestCase):
    def fake_engine(self, root, mode):
        path = root / ("fake-" + mode)
        path.write_text("#!" + sys.executable + "\n" + '''
import sys,time
for line in sys.stdin:
    command=line.strip()
    if command=='uci':
        print('id name test-only fake UCI')
        for name,typ,val in [('Threads','spin','1'),('Hash','spin','16'),('OwnBook','check','false')]:
            print('option name '+name+' type '+typ+' default '+val)
        print('uciok',flush=True)
    elif command=='isready': print('readyok',flush=True)
    elif command.startswith('go '):
        if MODE=='eof': sys.exit(7)
        if MODE=='hang': time.sleep(30)
        print('info depth 1 score cp 10 nodes 1')
        print('bestmove e2e4',flush=True)
    elif command=='quit': sys.exit(0)
'''.replace("MODE", repr(mode)))
        path.chmod(0o755)
        return path

    def test_eof_is_failure_and_owned_process_is_reaped(self):
        with tempfile.TemporaryDirectory() as temp:
            engine = gen.UciEngine(self.fake_engine(Path(temp), "eof"), timeout=1)
            with self.assertRaisesRegex(RuntimeError, "EOF"):
                engine.search([], 64)
            receipt = engine.close()
            self.assertTrue(receipt["reaped"])
            self.assertEqual(receipt["returncode"], 7)

    def test_hung_search_times_out_and_cleanup_kills_owned_group(self):
        with tempfile.TemporaryDirectory() as temp:
            engine = gen.UciEngine(self.fake_engine(Path(temp), "hang"), timeout=2)
            engine.timeout = .1
            with self.assertRaisesRegex(RuntimeError, "timeout"):
                engine.search([], 64)
            receipt = engine.close()
            self.assertTrue(receipt["reaped"])
            self.assertTrue(receipt["forced_kill"])

    def test_illegal_moves_publish_no_game_and_all_engines_close(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            engine, network, out = self.fake_engine(root, "illegal"), root / "network", root / "output"
            network.write_text("test-only identity")
            command = [sys.executable, str(Path(gen.__file__)), "--engine", str(engine),
                       "--opponent", str(engine), "--source-commit", "a" * 40,
                       "--opponent-source-commit", "b" * 40, "--network", str(network),
                       "--opponent-network", str(network), "--out", str(out),
                       "--workers", "2", "--games", "2", "--target-positions", "0",
                       "--opening-min", "0", "--opening-max", "0", "--time-limit-seconds", "10"]
            process = subprocess.run(command, capture_output=True, text=True, timeout=20)
            self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
            manifest = json.loads((out / "manifest.json").read_text())
            self.assertEqual(manifest["completed_games"], 0)
            self.assertEqual(manifest["eligible_positions"], 0)
            self.assertEqual(manifest["status"], "INCOMPLETE_OR_FAILED")
            self.assertTrue(manifest["sessions"][-1]["owned_workers_reaped"])
            for worker in manifest["sessions"][-1]["workers_observed"].values():
                for receipt in worker["engines"]:
                    self.assertTrue(receipt["reaped"])
                    self.assertEqual(receipt["returncode"], 0)


if __name__ == "__main__":
    unittest.main()
