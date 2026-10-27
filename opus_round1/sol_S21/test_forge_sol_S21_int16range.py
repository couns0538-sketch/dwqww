"""Tests for forge_sol_S21_int16range.py (numpy; run with OPENBLAS/OMP/MKL threads = 1).
S21_NETS_DIR = the lock archive's 5_nnue/nets/history_all_CR_passed (for the CR-table cross-check; skipped if absent).
Temporary files go to TMP. Run: python -I -B test_forge_sol_S21_int16range.py"""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("s21", HERE / "forge_sol_S21_int16range.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
NETS = Path(os.environ.get("S21_NETS_DIR", r"D:\grok-pc-data\dwqww\.claude\worktrees\b\pkg\forge_LOCK_AL1_s198_FULL_20261026_1039\5_nnue\nets\history_all_CR_passed"))
CR = {  # CR_HOLD_sol_nnueint16_b425207a_overflow_table.txt: md5 prefix -> (max|w1|, top32 bound, full-768 bound, max|w2|)
    "resid_h256_e12_e_ep12.inc": ("6d22f612", 10323, 262551, 1635680, 14727),
    "resid_h256_e32_f003_b06_ep32.inc": ("80a35e2f", 14055, 383755, 1940536, 14662),
    "resid_h256_e16_f004_b06_sol_ep16.inc": ("4c8ba6dd", 9688, 259245, 1498988, 17403),
    "resid_h256_e24_f005_b06_ep24.inc": ("0ae059d1", 10128, 258309, 1415036, 15270),
    "resid_h256_e48_f006_b06_ep48.inc": ("0fae54a4", 12011, 327268, 2177169, 16778),
    "resid_h256_e16_f007_b06_ep16.inc": ("eaf55cb9", 9964, 267511, 1501156, 14415),
    "resid_h256_e20_f008_b06_sol_ep20.inc": ("1a2ea398", 10673, 251600, 1569811, 15397),
    "resid_h256_e16_f009_b06_ep16.inc": ("eee839ba", 10979, 254787, 1529476, 14323),
    "resid_h256_e16_f010_b06_ep16.inc": ("d8e332e9", 9115, 249454, 1448510, 15485),
    "resid_h256_e20_f011_b06_ep20.inc": ("2623b434", 13735, 331731, 1531680, 13795),
    "resid_h256_e16_f012_b06_sol_ep16.inc": ("1f0bca9a", 10109, 245561, 1512252, 13843),
    "resid_h256_e20_f013_b06_ep20.inc": ("6d0ede66", 8738, 229760, 1494818, 14886),
    "resid_h256_e20_f014_b06_ep20.inc": ("4eb57893", 9292, 237793, 1506055, 15155),
}


def random_net(seed, big=False):
    rng = np.random.default_rng(seed)
    w1 = rng.integers(-3000 if not big else -12000, 3000 if not big else 12000, (768, 256))
    return {"w1": w1, "b1": rng.integers(-500, 500, 256), "w2": rng.integers(-15000, 15000, 512), "b2": 123, "residual": True,
            "md5": "x", "path": "random"}


def board_codes(placement, stm):
    codes = np.zeros(64, np.int64)
    pieces = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6, "p": 7, "n": 8, "b": 9, "r": 10, "q": 11, "k": 12}
    for r, rank in enumerate(placement.split("/")):
        f = 0
        for ch in rank:
            if ch.isdigit():
                f += int(ch)
            else:
                codes[(7 - r) * 8 + f] = pieces[ch]
                f += 1
    return codes, 0 if stm == "w" else 1


class Forward(unittest.TestCase):
    def test_features_match_the_trainer_formula(self):
        codes, _ = board_codes("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR", "w")
        fw = tool.feature_lists(codes[None, :], np.array([0]))[0]
        fb = tool.feature_lists(codes[None, :], np.array([1]))[0]
        self.assertEqual(fw[0], (0 * 6 + 3) * 64 + 0)        # white rook a1, white perspective: own rook, sq 0
        self.assertEqual(fb[0], (1 * 6 + 3) * 64 + 56)       # same rook, black perspective: enemy rook, sq ^ 56
        self.assertEqual(fw[63], (1 * 6 + 3) * 64 + 63)      # black rook h8, white perspective
        self.assertEqual(fb[63], (0 * 6 + 3) * 64 + 7)       # black rook h8, black perspective: own, 63 ^ 56
        self.assertEqual(int((fw == 768).sum()), 32)

    def test_accumulator_and_cp_against_a_direct_loop(self):
        net = random_net(1)
        codes, stm = board_codes("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R", "w")
        acc_s = tool.accumulators(net, codes[None, :], np.array([stm]))[0]
        acc_o = tool.accumulators(net, codes[None, :], np.array([1 - stm]))[0]
        direct_s, direct_o = net["b1"].copy(), net["b1"].copy()
        for sq in range(64):
            c = codes[sq]
            if c == 0:
                continue
            color, typ = (c - 1) // 6, (c - 1) % 6
            direct_s = direct_s + net["w1"][((color != stm) * 6 + typ) * 64 + (sq ^ 56 if stm else sq)]
            direct_o = direct_o + net["w1"][((color != 1 - stm) * 6 + typ) * 64 + (sq ^ 56 if 1 - stm else sq)]
        self.assertTrue(np.array_equal(acc_s, direct_s) and np.array_equal(acc_o, direct_o))
        cp = tool.network_cp(net, acc_s[None, :], acc_o[None, :])[0]
        act_s = np.clip(direct_s / 4096, 0, 1) ** 2
        act_o = np.clip(direct_o / 4096, 0, 1) ** 2
        ref = (act_s @ net["w2"][:256] + act_o @ net["w2"][256:] + net["b2"]) / 4096 * 400 / 2.25
        self.assertAlmostEqual(cp, ref, places=9)

    def test_wrap16(self):
        self.assertEqual(list(tool.wrap16(np.array([32767, 32768, -32769, 65536 + 5]))), [32767, -32768, 32767, 5])


class Export(unittest.TestCase):
    def test_bound_export_fits_int16_and_cannot_build(self):
        net = random_net(2, big=True)
        rng = np.random.default_rng(3)
        codes = np.zeros((300, 64), np.int64)
        for i in range(300):
            squares = rng.choice(64, 20, replace=False)
            codes[i, squares] = rng.integers(1, 13, 20)
        stm = rng.integers(0, 2, 300)
        clipped, parity = tool.export(net, codes, stm, "bound")
        self.assertLessEqual(parity["max_abs_acc_after"], 32767)
        self.assertTrue(parity["fits_int16_on_positions"])
        self.assertLess(parity["alpha"], 1.0)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "x.inc"
            tool.write_inc(out, clipped, parity, net)
            first = out.read_text(encoding="ascii").splitlines()[0]
            self.assertTrue(first.startswith("#error"))
            again = tool.read_inc(out)
            self.assertTrue(np.array_equal(again["w1"], clipped["w1"]))
        clipped_o, parity_o = tool.export(net, codes, stm, "observed")
        self.assertTrue(parity_o["fits_int16_on_positions"])        # rounding headroom keeps the observed max in range
        self.assertLessEqual(parity_o["max_abs_acc_after"], 32767)
        self.assertLessEqual(parity_o["parity_net_cp"]["mean_abs"], parity["parity_net_cp"]["mean_abs"] + 1e-9)


@unittest.skipUnless(NETS.is_dir(), "no nets dir")
class CrTable(unittest.TestCase):
    def test_weight_bounds_equal_cr_table(self):
        for name, (md5, maxw, top32, full, maxw2) in CR.items():
            net = tool.read_inc(NETS / name)
            b = tool.bounds(net)
            self.assertEqual(net["md5"][:8], md5, name)
            self.assertEqual((b["max_abs_w1"], b["top32_bound"], b["full768_bound"], b["max_abs_w2"]), (maxw, top32, full, maxw2), name)
            self.assertGreater(b["top32_bound"], 32767, name)   # CR: a true int16 accumulator would overflow for every net


if __name__ == "__main__":
    unittest.main(verbosity=2)
