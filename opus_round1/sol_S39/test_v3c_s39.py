"""S39 unit + order-capture tests for train_resid_v3c.py (fixed-size epochs). Runs on the staged copies only:
F:\\opus_scratch\\sol_S39\\opus_nnue_smoke_s39_v3c.py (must be byte-identical to train_resid_v3c.py in this folder) and
opus_nnue_smoke_s39_v3b.py (the lock archive's v3b), loaded with importlib (no train_resid* name on any command line).

  <venv python> -I -B test_v3c_s39.py -v        (after opus_nnue_smoke_s39.py --stage; CPU, 1 thread, Idle priority)
  <venv python> -I -B test_v3c_s39.py --v3c <copy> -v   (mutation check: test another copy; test_copies then fails by design)
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import inspect
import io
import json
import math
import os
import random
import sys
import threading
import time
import unittest
from fractions import Fraction
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = Path(r"F:\opus_scratch\sol_S39")
V3C_SRC = HERE / ("train_resid" + "_v3c.py")
V3C_COPY = ROOT / "opus_nnue_smoke_s39_v3c.py"
if "--v3c" in sys.argv:  # mutation check only
    _i = sys.argv.index("--v3c")
    V3C_COPY = Path(sys.argv[_i + 1])
    del sys.argv[_i:_i + 2]
V3B_COPY = ROOT / "opus_nnue_smoke_s39_v3b.py"
PIN_V3B = "5cebba4d44133630e247d9ab4c0085fa6301dde8db1dfe1389452ac19d92313f"
SAMPLE = ROOT / "inputs" / "data32_sample_50k"
SHARDS = ("t00000", "t01000", "t02000", "t03000")
UNIT = ROOT / "tmp" / f"unit_{time.strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"


def load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


import torch  # noqa: E402

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
C = load(V3C_COPY)
B = load(V3B_COPY)


class Captured(Exception):
    pass


def parsed(module, argv):
    """Run module.main() only up to parse_args and return the namespace (no side effects)."""
    orig = argparse.ArgumentParser.parse_args

    def fake(self, *a, **k):
        raise Captured(orig(self, *a, **k))
    argparse.ArgumentParser.parse_args = fake
    old = sys.argv
    sys.argv = ["trainer", *argv]
    try:
        module.main()
    except Captured as e:
        return e.args[0]
    finally:
        argparse.ArgumentParser.parse_args = orig
        sys.argv = old
    raise AssertionError("parse_args not reached")


def base_argv(run_dir, extra=()):
    return ["--train", *[str(SAMPLE / f"{s}.pos") for s in SHARDS], "--holdout", str(SAMPLE / "h000.pos"),
            "--hce-dir", str(SAMPLE), "--device", "cpu", "--residual", "--init-check", "--log-every", "1e9", "--shape", "16",
            "--epochs", "2", "--seed", "99", "--batch-size", "1024", "--warmup-steps", "20", "--val-positions", "4096",
            "--run-dir", str(run_dir), *extra]


class EmptyFeed:
    """Train feed stand-in: yields no batches (the epoch does no steps); joinable like a Prefetcher."""
    def __init__(self):
        self.t = threading.Thread(target=lambda: None)
        self.t.start()

    def close(self):
        self.t.join()

    def __iter__(self):
        return iter(())


def captured_orders(module, extra, tag):
    """Run module.main() with the train-set Prefetcher replaced by a recorder (holdout evaluation stays real).
    Returns (stdout, [the train index order handed to the feed, per epoch])."""
    calls = []
    orig = module.Prefetcher

    def feed(d, order, batch, k, depth=6):
        if d["n"] == 200000:  # the train set (holdout = 50,000)
            calls.append(np.array(order, copy=True))
            return EmptyFeed()
        return orig(d, order, batch, k, depth)
    module.Prefetcher = feed
    old = sys.argv
    sys.argv = ["trainer", *base_argv(UNIT / tag, extra)]
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            rc = module.main()
    finally:
        module.Prefetcher = orig
        sys.argv = old
    assert rc == 0, out.getvalue()
    return out.getvalue(), calls


def ref_quotas(sizes, weights, total):
    """Independent reference for epoch_quotas: the cap set is found from the weight breakpoints (lambda * w >= 1 <=> capped,
    lambda = what is left / sum(rows * weight) of the free files), then largest remainder, ties -> lower index."""
    W = [Fraction(w) for w in weights]
    files = [f for f in range(len(sizes)) if sizes[f] > 0]
    levels = sorted({W[f] for f in files}, reverse=True)
    for m in range(len(levels) + 1):
        capped = [f for f in files if m and W[f] >= levels[m - 1]]
        free = [f for f in files if f not in capped]
        rest = total - sum(sizes[f] for f in capped)
        if not free:
            if rest == 0:
                lam = None
                break
            continue
        lam = Fraction(rest) / sum(sizes[f] * W[f] for f in free)
        if rest >= 0 and all(lam * W[f] >= 1 for f in capped) and all(lam * W[f] < 1 for f in free):
            break
    else:
        raise AssertionError("no consistent split")
    q = [0] * len(sizes)
    for f in capped:
        q[f] = sizes[f]
    if free and rest:
        share = {f: lam * sizes[f] * W[f] for f in free}
        for f in free:
            q[f] = math.floor(share[f])
        for f in sorted(free, key=lambda f: (-(share[f] - q[f]), f))[:rest - sum(q[f] for f in free)]:
            q[f] += 1
    return q


def v3b_order(n, seed, e):
    buf = np.arange(n, dtype=np.int32)
    np.random.default_rng(seed * 1000 + e).shuffle(buf)
    return buf


class TestInputs(unittest.TestCase):
    def test_copies(self):
        self.assertEqual(hashlib.sha256(V3C_COPY.read_bytes()).hexdigest(), hashlib.sha256(V3C_SRC.read_bytes()).hexdigest(),
                         "staged v3c copy differs from the deliverable")
        self.assertEqual(hashlib.sha256(V3B_COPY.read_bytes()).hexdigest(), PIN_V3B)


class TestOptions(unittest.TestCase):
    def test_defaults_off_and_v3b_defaults_unchanged(self):
        req = ["--holdout", "h.pos", "--hce-dir", "d"]
        nc, nb = vars(parsed(C, req)), vars(parsed(B, req))
        self.assertEqual(nc["epoch_positions"], 0)
        self.assertEqual(nc["recent_weight"], 1.0)
        self.assertEqual(C.V3C_OFF, {"epoch_positions": 0, "recent_weight": 1.0})
        self.assertEqual({k: v for k, v in nc.items() if k not in C.V3C_OFF}, nb)
        self.assertEqual(list(nc)[:len(nb)], list(nb), "v3b options keep their order (settings dump)")

    def test_validation_before_any_output(self):
        bad = [["--recent-weight", "2"], ["--epoch-positions", "-1"], ["--epoch-positions", "100"],
               ["--epoch-positions", "5000", "--recent-weight", "0"], ["--epoch-positions", "5000", "--recent-weight", "-1"],
               ["--epoch-positions", "5000", "--recent-weight", "nan"], ["--epoch-positions", "5000", "--recent-weight", "inf"]]
        for i, extra in enumerate(bad):
            run = UNIT / f"bad{i}"
            old = sys.argv
            sys.argv = ["trainer", *base_argv(run, extra)]
            try:
                with contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit) as cm:
                    C.main()
            finally:
                sys.argv = old
            self.assertEqual(cm.exception.code, 2, extra)
            self.assertIn("error:", err.getvalue())
            self.assertFalse(run.exists(), f"run dir created for {extra}")


class TestQuotas(unittest.TestCase):
    def test_recent_weights(self):
        self.assertEqual(C.recent_weights(0, 3.0), [])
        self.assertEqual(C.recent_weights(1, 3.0), [1.0])
        self.assertEqual(C.recent_weights(5, 1.0), [1.0] * 5)
        w = C.recent_weights(4, 3.0)
        self.assertEqual((w[0], w[-1]), (1.0, 3.0))
        self.assertTrue(all(abs(a - b) < 1e-12 for a, b in zip(w, [1.0, 5 / 3, 7 / 3, 3.0])))
        self.assertEqual(C.recent_weights(3, 0.5), [1.0, 0.75, 0.5])

    def test_known_cases(self):
        self.assertEqual(C.epoch_quotas([50000] * 4, C.recent_weights(4, 3.0), 100000), [12500, 20833, 29167, 37500])
        self.assertEqual(C.epoch_quotas([50000] * 4, C.recent_weights(4, 10.0), 150000), [10000, 40000, 50000, 50000])  # 2 capped
        self.assertEqual(C.epoch_quotas([10, 20, 30, 40], [1.0] * 4, 50), [5, 10, 15, 20])
        self.assertEqual(C.epoch_quotas([3, 3, 3], [1.0] * 3, 4), [2, 1, 1])  # tie -> lower index
        self.assertEqual(C.epoch_quotas([5, 0, 5], [1.0, 9.0, 1.0], 6), [3, 0, 3])
        self.assertEqual(C.epoch_quotas([7, 9], [1.0, 2.0], 0), [0, 0])
        self.assertEqual(C.epoch_quotas([7, 9], [1.0, 2.0], 16), [7, 9])
        with self.assertRaises(ValueError):
            C.epoch_quotas([7, 9], [1.0, 2.0], 17)

    def test_fuzz_invariants(self):
        rnd = random.Random(39)
        for _ in range(3000):
            nf = rnd.randint(1, 12)
            sizes = [rnd.choice([0, rnd.randint(1, 50), rnd.randint(1, 5000)]) for _ in range(nf)]
            weights = [rnd.choice([1.0, rnd.uniform(0.05, 20.0)]) for _ in range(nf)]
            total = rnd.randint(0, sum(sizes))
            q = C.epoch_quotas(sizes, weights, total)
            self.assertEqual(sum(q), total)
            self.assertTrue(all(0 <= x <= n for x, n in zip(q, sizes)))
            self.assertEqual(q, ref_quotas(sizes, weights, total), (sizes, weights, total))
            if len(set(weights)) == 1 and sum(sizes):  # uniform: every file within 1 of total * n / N
                for f in range(nf):
                    self.assertLess(abs(q[f] - Fraction(total * sizes[f], sum(sizes))), 1)


class TestDraw(unittest.TestCase):
    sizes = [1000, 3000, 2000, 4000]

    def draw(self, seed, quotas, chunk=1 << 24):
        offs = [int(o) for o in np.cumsum([0] + self.sizes[:-1])]
        buf = np.arange(sum(self.sizes), dtype=np.int32)
        w = C.draw_weighted(buf, np.random.default_rng(seed), offs, self.sizes, quotas, chunk=chunk)
        return buf, w, offs

    def test_no_repeats_and_quotas(self):
        quotas = C.epoch_quotas(self.sizes, C.recent_weights(4, 3.0), 5000)
        buf, w, offs = self.draw(99000, quotas)
        sel = buf[:w]
        self.assertEqual(w, 5000)
        self.assertEqual(len(np.unique(sel)), 5000)
        self.assertTrue(((sel >= 0) & (sel < sum(self.sizes))).all())
        fid = np.searchsorted(np.array(offs), sel, side="right") - 1
        self.assertEqual(np.bincount(fid, minlength=4).tolist(), quotas)
        self.assertFalse((np.diff(sel) > 0).all(), "epoch order is shuffled")
        self.assertFalse((np.diff(fid) >= 0).all(), "files interleaved (one shuffle after the per-file draws), not file by file")
        self.assertEqual(len(set(fid[:500].tolist())), 4, "the first 10% of the epoch already mixes all files")

    def test_deterministic_and_seeded(self):
        quotas = C.epoch_quotas(self.sizes, C.recent_weights(4, 3.0), 5000)
        a, _, _ = self.draw(99000, quotas)
        b, _, _ = self.draw(99000, quotas)
        c, _, _ = self.draw(99001, quotas)
        self.assertTrue((a[:5000] == b[:5000]).all())
        self.assertFalse((a[:5000] == c[:5000]).all())

    def test_chunked_copy_overlap(self):
        quotas = C.epoch_quotas(self.sizes, C.recent_weights(4, 0.25), 7000)
        ref, w, _ = self.draw(5, quotas)
        for chunk in (1, 7, 64, 999, 4000):
            got, w2, _ = self.draw(5, quotas, chunk=chunk)
            self.assertEqual(w2, w)
            self.assertTrue((got[:w] == ref[:w]).all(), chunk)

    def test_uniform_within_file(self):
        quotas = C.epoch_quotas(self.sizes, C.recent_weights(4, 3.0), 5000)
        hits = np.zeros(sum(self.sizes), np.int64)
        epochs = 400
        for e in range(epochs):
            buf, w, _ = self.draw(1000 + e, quotas)
            hits[buf[:w]] += 1
        o = 0
        for n, q in zip(self.sizes, quotas):
            p = q / n
            seg = hits[o:o + n]
            sd = math.sqrt(epochs * p * (1 - p))
            self.assertLess(abs(seg.mean() - epochs * p), 1e-9 + 6 * sd / math.sqrt(n))  # exact per epoch: mean == E*p
            self.assertLess(np.abs(seg - epochs * p).max(), 6 * sd)
            o += n


class TestOrderCapture(unittest.TestCase):
    """Runs the real main() of the v3c copy with a recording Prefetcher: the train orders handed to it per epoch."""

    def test_off_equals_v3b_full_permutation(self):
        out_c, oc = captured_orders(C, [], "cap_off_c")
        out_b, ob = captured_orders(B, [], "cap_off_b")
        self.assertEqual(len(oc), 2)
        for e in range(2):
            self.assertTrue((oc[e] == ob[e]).all())
            self.assertTrue((oc[e] == v3b_order(200000, 99, e)[:195 * 1024]).all())
        self.assertNotIn("epoch-positions", out_c)

    def test_uniform_is_prefix_of_v3b_order(self):
        out, oc = captured_orders(C, ["--epoch-positions", "100000"], "cap_u")
        self.assertIn("steps/epoch=97 total=194 ", out)
        for e in range(2):
            self.assertEqual(len(oc[e]), 97 * 1024)
            self.assertTrue((oc[e] == v3b_order(200000, 99, e)[:97 * 1024]).all())
            self.assertEqual(len(np.unique(oc[e])), 97 * 1024)
        self.assertFalse((np.sort(oc[0]) == np.sort(oc[1])).all(), "epochs draw different subsets")

    def test_weighted_plan(self):
        out, oc = captured_orders(C, ["--epoch-positions", "100000", "--recent-weight", "3"], "cap_w")
        quotas = [12500, 20833, 29167, 37500]
        self.assertIn("t03000.pos 3.0000 37,500/50,000", out)
        for e in range(2):
            buf = np.arange(200000, dtype=np.int32)
            w = C.draw_weighted(buf, np.random.default_rng(99 * 1000 + e), [0, 50000, 100000, 150000], [50000] * 4, quotas)
            self.assertEqual(w, 100000)
            self.assertTrue((oc[e] == buf[:97 * 1024]).all())
            self.assertEqual(len(np.unique(oc[e])), 97 * 1024)
        full = np.arange(200000, dtype=np.int32)
        C.draw_weighted(full, np.random.default_rng(99000), [0, 50000, 100000, 150000], [50000] * 4, quotas)
        self.assertEqual(np.bincount(full[:100000] // 50000, minlength=4).tolist(), quotas)

    def test_n_at_least_data_size_is_v3b(self):
        for tag, extra in (("cap_eq", ["--epoch-positions", "200000"]), ("cap_gt", ["--epoch-positions", "999999", "--recent-weight", "3"])):
            out, oc = captured_orders(C, extra, tag)
            self.assertIn("full epochs (v3b order", out)
            for e in range(2):
                self.assertTrue((oc[e] == v3b_order(200000, 99, e)[:195 * 1024]).all())

    def test_order_buffers_2(self):
        _, o1 = captured_orders(C, ["--epoch-positions", "100000", "--recent-weight", "3"], "cap_ob1")
        _, o2 = captured_orders(C, ["--epoch-positions", "100000", "--recent-weight", "3", "--order-buffers", "2"], "cap_ob2")
        for e in range(2):
            self.assertTrue((o1[e] == o2[e]).all())


class TestSharedCode(unittest.TestCase):
    """Everything outside the epoch draw is v3b's code: shared functions/classes and the whole training loop are source-identical."""

    def test_shared_definitions_identical(self):
        names = [n for n, v in vars(B).items() if (inspect.isfunction(v) or inspect.isclass(v)) and getattr(v, "__module__", "") == B.__name__]
        self.assertGreaterEqual(len(names), 20)
        for n in names:
            if n == "main":
                continue
            self.assertEqual(inspect.getsource(getattr(C, n)), inspect.getsource(getattr(B, n)), n)

    def test_training_loop_identical(self):
        def loop(module):
            src = inspect.getsource(module.main)
            start = src.index("    sc_dev = torch.zeros(2, device=dev)")
            return src[start:]
        self.assertEqual(loop(C), loop(B), "training loop / save / final eval differ")
        self.assertIn("for bt in pf:", loop(C))


if __name__ == "__main__":
    UNIT.mkdir(parents=True, exist_ok=True)
    unittest.main(verbosity=2)
