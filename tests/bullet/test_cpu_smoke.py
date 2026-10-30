"""Small independent contracts for the supplemental AL1 CPU smoke trainer."""
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'bullet'))
import train_lock_cpu_smoke as smoke


class CpuSmokeTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        torch.manual_seed(7)

    def test_piece_square_perspectives_and_empty_squares(self):
        codes = np.zeros((1, 64), dtype=np.int64)
        codes[0, 8], codes[0, 63] = 1, 12  # White pawn a2, Black king h8.
        ours, theirs = smoke.dense_features(codes, np.array([0]))
        self.assertEqual(torch.nonzero(ours[0]).flatten().tolist(), [8, 767])
        self.assertEqual(torch.nonzero(theirs[0]).flatten().tolist(), [327, 432])
        black_ours, black_theirs = smoke.dense_features(codes, np.array([1]))
        self.assertTrue(torch.equal(ours, black_theirs))
        self.assertTrue(torch.equal(theirs, black_ours))
        self.assertEqual(float(ours.sum()), 2.0)

    def test_quantization_half_away_and_straight_through_gradient(self):
        original = torch.tensor([-1.5, -.5, .5, 1.5]) / 4096
        original.requires_grad_()
        quantized = smoke.quantized_ste(original)
        self.assertEqual((quantized * 4096).tolist(), [-2, -1, 1, 2])
        quantized.sum().backward()
        self.assertEqual(original.grad.tolist(), [1, 1, 1, 1])

    def test_ste_is_bit_exact_across_projected_range_and_rounding_boundaries(self):
        generator = torch.Generator().manual_seed(29643)
        bound = 32767 / 4096
        random_values = (torch.rand(250000, generator=generator) * 2 - 1) * bound
        # Visit every in-range half-LSB threshold and its adjacent float32s.
        boundaries = (torch.arange(-32767, 32767, dtype=torch.float32) + .5) / 4096
        lower = torch.nextafter(boundaries, torch.full_like(boundaries, -float('inf')))
        upper = torch.nextafter(boundaries, torch.full_like(boundaries, float('inf')))
        # Include signed zero, subnormals, smallest normals, and projection ends.
        tiny = torch.tensor([0., -0., np.nextafter(np.float32(0), np.float32(1)),
                             np.finfo(np.float32).tiny, 1e-30, 1e-20, 1e-10, bound])
        values = torch.cat([random_values, boundaries, lower, upper, tiny, -tiny])
        scaled = values.double() * 4096
        expected = ((torch.sign(scaled) * torch.floor(scaled.abs() + .5))
                    .to(torch.int16).to(torch.float32) / 4096)
        actual = smoke.quantized_ste(values)
        self.assertEqual(int(torch.count_nonzero(actual.view(torch.int32) != expected.view(torch.int32))), 0)

    def test_residual_starts_at_hce_and_both_perspectives_contribute(self):
        model = smoke.LockNet()
        ours = torch.zeros((2, 768))
        theirs = torch.zeros_like(ours)
        ours[:, 0], theirs[:, 1] = 1, 1
        hce = torch.tensor([100., -100.])
        self.assertTrue(torch.equal(model(ours, theirs, hce), hce * (2.25 / 400)))
        with torch.no_grad():
            model.ftw.zero_()
            model.ftb.zero_()
            model.ftw[0, 0], model.ftw[1, 0] = .5, 2
            model.outw[0, 0], model.outw[1, 0] = 2, -1
        expected = hce * (2.25 / 400) - .5  # .5**2 * 2 + clamp(2)**2 * -1
        self.assertTrue(torch.equal(model(ours, theirs, hce), expected))

    def test_one_epoch_visits_tail_once_and_is_reproducible(self):
        ours = torch.zeros((7, 768))
        theirs = torch.zeros_like(ours)
        ours[:, 0], theirs[:, 1] = 1, 1
        hce, score = torch.zeros(7), torch.full((7,), 70.)
        first = smoke.LockNet()
        second = smoke.LockNet()
        second.load_state_dict(first.state_dict())
        before = smoke.measure(first, ours, theirs, hce, score, 4)
        first_receipt = smoke.train_epoch(first, ours, theirs, hce, score, batch_size=4, seed=3, learning_rate=.003)
        second_receipt = smoke.train_epoch(second, ours, theirs, hce, score, batch_size=4, seed=3, learning_rate=.003)
        self.assertEqual(sorted(first_receipt['row_order']), list(range(7)))
        self.assertEqual(first_receipt['batch_sizes'], [4, 3])
        self.assertEqual(first_receipt['row_order'], second_receipt['row_order'])
        for key, value in first.state_dict().items():
            self.assertTrue(torch.equal(value, second.state_dict()[key]))
        self.assertLess(smoke.measure(first, ours, theirs, hce, score, 4)['mse'], before['mse'])

    def test_selected_rows_keep_original_score_hce_and_full_fen(self):
        from forge_pos import PosReader, PosWriter, Record, fen_record
        fen = '4k3/8/8/8/8/8/P7/4K3 b - - 7 12'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with PosWriter(root / 'source', 'sample', True, with_fen=True) as writer:
                for score in (10, 20, 30):
                    row = fen_record(fen, score, .5)
                    writer.append(Record(row.board, row.score, row.meta, score - 7), fen)
            out = root / 'selected'
            out.mkdir()
            result = smoke.select_rows(root / 'source/sample.pos', root / 'source/sample.hce',
                                       root / 'source/sample.fen', out, start=1, count=2)
            with PosReader(out / 'subset.pos', out / 'subset.hce') as reader:
                self.assertEqual([(r.score, r.hce) for r in reader], [(20, 13), (30, 23)])
            self.assertEqual((out / 'subset.fen').read_text().splitlines(), [fen, fen])
            self.assertEqual(result['source_indices'], [1, 2])
            self.assertEqual(result['codes'].shape, (2, 64))

    def test_forward_bits_match_independent_export_oracle(self):
        from forge_pos import fen_record
        model = smoke.LockNet()
        with torch.no_grad():
            model.outw.normal_(0, .1)
            model.outb.fill_(.125)
        q = {role: smoke.lock_export.common.quantize(values.reshape(-1), 4096,
             'nearest_ties_away', '<i2') for role, values in model.arrays().items()}
        for side in ('w', 'b'):
            fen = 'r1bqkbnr/pppp2p1/2n1pp1p/8/3P1P2/N1P5/PP2P1PP/R1BQKBNR ' + side + ' KQkq - 0 5'
            row = fen_record(fen, 0, .5)
            packed = np.frombuffer(row.board, dtype=np.uint8)
            codes = np.empty((1, 64), dtype=np.int64)
            codes[0, 0::2], codes[0, 1::2] = packed & 15, packed >> 4
            ours, theirs = smoke.dense_features(codes, np.array([int(side == 'b')]))
            with torch.no_grad():
                value = model.residual(ours, theirs).numpy()
            _, expected_bits = smoke.lock_export.evaluate(q, fen)
            self.assertEqual(int(value.view(np.uint32)[0]), expected_bits)


if __name__ == '__main__':
    unittest.main()
