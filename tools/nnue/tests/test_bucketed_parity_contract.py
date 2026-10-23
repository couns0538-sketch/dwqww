"""Regression checks for the parity corpus and informative-head acceptance gate."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

import chess
import numpy as np

SPEC = importlib.util.spec_from_file_location(
    'bucket_parity', Path(__file__).with_name('test_bucketed_engine_parity.py'))
parity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parity)


class BucketParityContract(unittest.TestCase):
    def test_piece_count_boundaries_and_clamping(self):
        for count in range(2, 33):
            self.assertEqual(parity.bucket_for_piece_count(count), min(7, (count - 1) // 4))
        self.assertEqual(parity.bucket_for_piece_count(0), 0)
        self.assertEqual(parity.bucket_for_piece_count(64), 7)
        with self.assertRaises(ValueError):
            parity.bucket_for_piece_count(8.5)

    def test_corpus_is_unique_deterministic_and_covers_both_turns_of_every_bucket(self):
        with tempfile.TemporaryDirectory() as directory:
            sample = Path(directory) / 'empty.txt'; sample.write_text('')
            first = parity.corpus(sample, 1024, 20261023)
            self.assertEqual(first, parity.corpus(sample, 1024, 20261023))
        records, _, special = first
        self.assertEqual(len(records), 1024)
        self.assertEqual(len({' '.join(fen.split()[:4]) for fen in records}), 1024)
        coverage = set()
        for fen in records:
            board = chess.Board(fen)
            self.assertTrue(board.is_valid())
            coverage.add((parity.bucket_for_piece_count(len(board.piece_map())), board.turn))
        self.assertEqual(coverage, {(bucket, turn) for bucket in range(8) for turn in (False, True)})
        self.assertTrue(all(special.values()))

    def test_distinct_head_gate_rejects_an_uninformative_fixture(self):
        weights = {'output_buckets': 8, 'bucket_w2': np.zeros((8, 256), dtype=np.float32),
                   'bucket_b2': np.zeros(8, dtype=np.float32)}
        self.assertEqual(parity.validate_head_layout(weights, False)['distinct_head_count'], 1)
        with self.assertRaises(ValueError):
            parity.validate_head_layout(weights, True)
        weights['bucket_b2'] = np.arange(8, dtype=np.float32)
        self.assertEqual(parity.validate_head_layout(weights, True)['distinct_head_count'], 8)
        weights['output_buckets'] = 1
        with self.assertRaises(ValueError):
            parity.validate_head_layout(weights, False)

    def test_forced_zero_head_control_must_distinguish_each_nonzero_head(self):
        rows = {bucket: 10 for bucket in range(8)}
        changes = {bucket: (0 if bucket == 0 else 1) for bucket in range(8)}
        self.assertTrue(parity.informative_head_zero_control(rows, changes))
        changes[6] = 0
        self.assertFalse(parity.informative_head_zero_control(rows, changes))
        changes[6] = 1; rows[7] = 0
        self.assertFalse(parity.informative_head_zero_control(rows, changes))


if __name__ == '__main__':
    unittest.main()
