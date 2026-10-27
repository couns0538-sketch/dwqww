"""S-A3 tests for train_resid_v3d.py: the 27 opus-sol-S50 tests (fixed-size epochs + warm start, re-run on v3d) + lr schedule
tests (defaults = v3b, per-step lr traces against a reference formula, resume/extend, records, errors). Runs on the staged copies:
F:\\opus_scratch\\sol_SA3\\opus_nnue_smoke_sa3_v3d.py (must be byte-identical to train_resid_v3d.py in this folder) and
opus_nnue_smoke_sa3_v3b.py (the lock archive's v3b), loaded with importlib (no train_resid* name on any command line).
The module under test keeps the name C from the S39/S50 tests.

  <venv python> -I -B test_v3d_sa3.py -v        (after opus_nnue_smoke_sa3.py --stage; CPU, 1 thread, Idle priority)
  <venv python> -I -B test_v3d_sa3.py --v3c <copy> -v   (mutation check: test another copy; test_copies then fails by design)
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
ROOT = Path(r"F:\opus_scratch\sol_SA3")
V3C_SRC = HERE / ("train_resid" + "_v3d.py")
V3C_COPY = ROOT / "opus_nnue_smoke_sa3_v3d.py"
if "--v3c" in sys.argv:  # mutation check only
    _i = sys.argv.index("--v3c")
    V3C_COPY = Path(sys.argv[_i + 1])
    del sys.argv[_i:_i + 2]
V3B_COPY = ROOT / "opus_nnue_smoke_sa3_v3b.py"
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
        self.assertIsNone(nc["init_weights"])
        self.assertEqual(C.V3C_OFF, {"epoch_positions": 0, "recent_weight": 1.0, "init_weights": None})
        self.assertEqual(C.V3D_LR, {"lr_schedule": "cosine", "lr_schedule_epochs": 0, "lr_decay_frac": 0.2})
        self.assertEqual({key: nc[key] for key in C.V3D_LR}, C.V3D_LR)
        self.assertEqual({k: v for k, v in nc.items() if k not in C.V3C_OFF and k not in C.V3D_LR}, nb)
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


def run_main(module, extra, tag, stub=True, drop=()):
    """module.main() in-process (stub=True: the train feed yields no batches, holdout evaluation stays real).
    Returns (rc, stdout, run dir). drop = flags removed from the base argv (e.g. --residual, --init-check)."""
    orig = module.Prefetcher

    def feed(d, order, batch, k, depth=6):
        if d["n"] == 200000:
            return EmptyFeed()
        return orig(d, order, batch, k, depth)
    if stub:
        module.Prefetcher = feed
    argv = [x for x in base_argv(UNIT / tag, extra) if x not in drop]
    old = sys.argv
    sys.argv = ["trainer", *argv]
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            rc = module.main()
    finally:
        module.Prefetcher = orig
        sys.argv = old
    return rc, out.getvalue(), UNIT / tag


def settings_of(run):
    head, body = next(run.glob("settings_*.txt")).read_text(encoding="utf-8").split("\n", 1)
    return head.replace(str(run), "<run>"), json.loads(body)


def same_state(a, b):
    return list(a) == list(b) and all(a[k].dtype == b[k].dtype and a[k].shape == b[k].shape
                                      and a[k].numpy().tobytes() == b[k].numpy().tobytes() for k in a)


class TestWarmStart(unittest.TestCase):
    """--init-weights on the v3c copy. Source: a real 10-step run (seed 7, lr 0.01, H16), so its weights and holdout val
    differ from a fresh seed-99 init (a load that does nothing is visible)."""

    @classmethod
    def setUpClass(cls):
        rc, out, run = run_main(C, ["--seed", "7", "--epochs", "1", "--steps-per-epoch", "10", "--lr", "0.01", "--warmup-steps", "1"],
                                "warm_src", stub=False)
        assert rc == 0, out
        cls.src = next(run.glob("epoch001-*.pt"))
        cls.src_md5 = hashlib.md5(cls.src.read_bytes()).hexdigest()
        cls.ck = torch.load(cls.src, map_location="cpu", weights_only=True)
        cls.src_json = json.loads(next(run.glob("epoch001-*.json")).read_text(encoding="utf-8"))

    def test_source_is_not_a_fresh_net(self):
        self.assertEqual(self.ck["step"], 10)
        self.assertGreater(abs(self.src_json["val"]["1.0"] - self.src_json["baseline"]["1.0"]), 1e-6)
        self.assertGreater(float(self.ck["model"]["out.weight"].abs().max()), 0.0)

    def test_loads_weights_only_and_logs_md5(self):
        rc, out, run = run_main(C, ["--init-weights", str(self.src), "--epochs", "1"], "warm_load")
        self.assertEqual(rc, 0, out)
        self.assertIn("INIT CHECK OK (warm start == checkpoint val)", out)
        self.assertIn(f"init-weights: model weights from {self.src} (md5 {self.src_md5}; checkpoint hidden=16 residual=True "
                      f"next_epoch=1 step=10); optimizer, lr and blend schedules start fresh", out)
        saved = torch.load(next(run.glob("epoch001-*.pt")), map_location="cpu", weights_only=True)
        self.assertTrue(same_state(saved["model"], self.ck["model"]), "weights equal the checkpoint (no steps were run)")
        self.assertEqual(saved["optimizer"]["state"], {}, "no optimizer state taken from the checkpoint")
        self.assertEqual(saved["step"], 0)
        _, js = settings_of(run)
        self.assertEqual(js["init_weights_md5"], self.src_md5)
        self.assertEqual(js["init_weights"], str(self.src))
        self.assertEqual(json.loads(next(run.glob("epoch001-*.json")).read_text(encoding="utf-8"))["init_weights_md5"], self.src_md5)

    def test_init_check_needs_the_same_val_subset(self):
        rc, out, _ = run_main(C, ["--init-weights", str(self.src), "--val-positions", "2048"], "warm_badval")
        self.assertEqual(rc, 3)
        self.assertIn("INIT CHECK FAILED (warm start != checkpoint val", out)

    def test_resume_does_not_load_init(self):
        missing = UNIT / "no_such_init.pt"
        rc, out, run = run_main(C, ["--init-weights", str(missing), "--resume", str(self.src)], "warm_resume")
        self.assertEqual(rc, 0, out)
        self.assertIn(f"init-weights {missing} (md5 missing): not loaded, --resume restores model and optimizer", out)
        self.assertEqual(settings_of(run)[1]["init_weights_md5"], "missing")
        saved = torch.load(next(run.glob("epoch002-*.pt")), map_location="cpu", weights_only=True)
        self.assertTrue(same_state(saved["model"], self.ck["model"]))
        self.assertEqual(saved["step"], 10, "step counter continues from --resume")

    def test_missing_file_rejected_before_run_dir(self):
        run = UNIT / "warm_missing"
        old = sys.argv
        sys.argv = ["trainer", *base_argv(run, ["--init-weights", str(UNIT / "no_such_init.pt")])]
        try:
            with contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit) as cm:
                C.main()
        finally:
            sys.argv = old
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("no such file", err.getvalue())
        self.assertFalse(run.exists())

    def test_hidden_and_residual_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "checkpoint hidden=16 but this run has hidden=32"):
            run_main(C, ["--init-weights", str(self.src), "--shape", "32"], "warm_h32")
        with self.assertRaisesRegex(ValueError, "checkpoint residual=True but this run has residual=False"):
            run_main(C, ["--init-weights", str(self.src)], "warm_nores", drop=("--residual",))

    def test_bare_state_dict(self):
        bare = UNIT / "bare_state_dict.pt"
        torch.save(self.ck["model"], bare)
        rc, out, run = run_main(C, ["--init-weights", str(bare), "--epochs", "1"], "warm_bare")
        self.assertEqual(rc, 0, out)
        self.assertIn("bare state_dict", out)
        self.assertIn("(checkpoint has no val: check skipped)", out)
        saved = torch.load(next(run.glob("epoch001-*.pt")), map_location="cpu", weights_only=True)
        self.assertTrue(same_state(saved["model"], self.ck["model"]))

    def test_qat_mismatch_warns(self):
        rc, out, _ = run_main(C, ["--init-weights", str(self.src), "--no-qat", "--epochs", "1"], "warm_noqat", drop=("--init-check",))
        self.assertEqual(rc, 0, out)
        self.assertIn("WARNING: --init-weights checkpoint qat=True but this run has qat=False", out)

    def test_non_finite_rejected(self):
        bad = {k: v.clone() for k, v in self.ck["model"].items()}
        bad["ft.bias"][0] = float("nan")
        path = UNIT / "nan_init.pt"
        torch.save({**self.ck, "model": bad}, path)
        with self.assertRaisesRegex(ValueError, "non-finite weights"):
            run_main(C, ["--init-weights", str(path)], "warm_nan")

    def test_off_settings_dump_equals_v3b(self):
        rc_c, _, run_c = run_main(C, [], "set_off_c")
        rc_b, _, run_b = run_main(B, [], "set_off_b")
        self.assertEqual((rc_c, rc_b), (0, 0))
        (hc, jc), (hb, jb) = settings_of(run_c), settings_of(run_b)
        self.assertEqual(hc, hb)
        jc["run_dir"] = jb["run_dir"] = "<run>"
        self.assertEqual(list(jc.items()), list(jb.items()))


def record_lr(module, extra, tag, stub=False, drop=()):
    """run_main with Adam wrapped to record param_groups[0]['lr'] at every optimizer step (the lr the step really used).
    Returns (rc, stdout, run dir, [lr per step])."""
    lrs = []
    orig = module.make_adam_devscalars

    def make(base):
        cls = orig(base)

        class Recording(cls):
            def step(self, closure=None):
                lrs.append(self.param_groups[0]["lr"])
                return super().step(closure)
        return Recording
    module.make_adam_devscalars = make
    try:
        rc, out, run = run_main(module, extra, tag, stub=stub, drop=drop)
    finally:
        module.make_adam_devscalars = orig
    return rc, out, run, lrs


def ref_lrs(kind, n, lr, warmup, total, floor, decay_frac=0.2):
    """Independent reference for the per-step lr, written from the schedule definitions with numpy (another operation order
    than the trainer): linear warmup lr*(s+1)/W; then lr*floor + lr*(1-floor)*shape with shape = half-cosine (cosine), straight
    line (linear) over the post-warmup horizon, or 1 then a straight line over the last round-half-up(decay_frac*T) steps (wsd,
    never before the warmup end); shape 0 after the horizon."""
    s = np.arange(n, dtype=np.float64)
    out = np.empty(n)
    warm = s < warmup
    out[warm] = lr * (s[warm] + 1.0) / warmup
    if kind in ("cosine", "linear"):
        x = np.clip((s - warmup) / max(1, total - warmup), 0.0, 1.0)
        shape = (1.0 + np.cos(np.pi * x)) / 2.0 if kind == "cosine" else 1.0 - x
    else:
        start = max(warmup, total - max(1, math.floor(decay_frac * total + 0.5)))
        x = np.clip((s - start) / max(1, total - start), 0.0, 1.0)
        shape = np.where(s < start, 1.0, 1.0 - x)
    out[~warm] = lr * floor + lr * (1.0 - floor) * shape[~warm]
    return out


LR_FAST = ["--shape", "8", "--batch-size", "4096", "--val-positions", "4096"]  # 48 steps/epoch on the 200,000-row sample


class TestLrSchedule(unittest.TestCase):
    """v3d lr schedules, checked on the lr Adam used at every step of real in-process runs (H8, 48 steps/epoch, lr 1e-3,
    warmup 20, floor 0.01 = the base argv defaults)."""
    SPE, LR, W, F = 48, 1e-3, 20, 0.01

    def trace(self, extra, tag, module=None):
        rc, out, run, lrs = record_lr(module or C, [*LR_FAST, *extra], tag)
        self.assertEqual(rc, 0, out)
        return out, run, lrs

    def check_ref(self, lrs, kind, total, decay_frac=0.2, warmup=None):
        warmup = self.W if warmup is None else warmup
        np.testing.assert_allclose(np.array(lrs), ref_lrs(kind, len(lrs), self.LR, warmup, total, self.F, decay_frac), rtol=1e-12, atol=0)
        self.assertEqual(lrs[0], self.LR * 1 / warmup)  # first warmup step
        if total <= len(lrs):
            self.assertGreater(lrs[total - 1], self.LR * self.F)  # last step of the horizon: just above the floor
            self.assertTrue(all(x == self.LR * self.F for x in lrs[total:]), "after the horizon: exactly the floor")

    def test_default_is_v3b_bit_for_bit(self):
        _, _, lb = self.trace([], "lr_v3b", module=B)
        _, _, lc = self.trace([], "lr_v3d_default")
        _, _, lh = self.trace(["--lr-schedule", "cosine", "--lr-schedule-epochs", "2"], "lr_v3d_h2")
        self.assertEqual(len(lb), 96)
        self.assertEqual([x.hex() for x in lc], [x.hex() for x in lb])
        self.assertEqual([x.hex() for x in lh], [x.hex() for x in lb])
        self.check_ref(lc, "cosine", 96)

    def test_linear(self):
        out, _, lrs = self.trace(["--lr-schedule", "linear"], "lr_linear")
        self.assertEqual(len(lrs), 96)
        self.check_ref(lrs, "linear", 96)
        self.assertIn("lr schedule: linear over 96 steps (2 epochs x 48), warmup 20, floor 0.01 x lr", out)

    def test_wsd_rounding_and_stable_phase(self):
        out, _, lrs = self.trace(["--lr-schedule", "wsd", "--lr-decay-frac", "0.3"], "lr_wsd")
        self.check_ref(lrs, "wsd", 96, decay_frac=0.3)
        start = 96 - 29  # round-half-up(0.3 * 96 = 28.8) = 29 decay steps
        self.assertTrue(all(x == self.LR for x in lrs[self.W:start]), "stable phase: exactly the peak lr")
        self.assertLess(lrs[start + 1], self.LR)
        self.assertIn(f"lr schedule: wsd over 96 steps (2 epochs x 48), lr 0.001 until step {start}, then linear decay, warmup 20, floor 0.01 x lr", out)

    def test_wsd_decay_never_inside_warmup(self):
        _, _, lrs = self.trace(["--lr-schedule", "wsd", "--lr-decay-frac", "0.5", "--warmup-steps", "70"], "lr_wsd_clamp")
        self.check_ref(lrs, "wsd", 96, decay_frac=0.5, warmup=70)
        self.assertLess(lrs[71], lrs[70])  # decay starts right after the warmup (no stable phase)

    def test_past_the_horizon_stays_at_the_floor(self):
        for kind in ("cosine", "linear", "wsd"):
            out, _, lrs = self.trace(["--lr-schedule", kind, "--lr-schedule-epochs", "1"], f"lr_past_{kind}")
            self.check_ref(lrs, kind, 48)
            self.assertIn("; the run goes 48 steps past the horizon at the floor", out)

    def test_long_horizon_stops_early(self):
        out, _, lrs = self.trace(["--lr-schedule-epochs", "6"], "lr_long")
        self.check_ref(lrs, "cosine", 288)
        self.assertGreater(lrs[-1], 0.8 * self.LR)
        self.assertIn("lr schedule: cosine over 288 steps (6 epochs x 48), warmup 20, floor 0.01 x lr; the run stops at step 96 of the horizon", out)

    def test_resume_gives_the_same_lr_at_every_later_step(self):
        args = ["--lr-schedule", "wsd", "--lr-decay-frac", "0.3", "--epochs", "3"]
        _, run, full = self.trace(args, "lr_res_full")
        _, _, resumed = self.trace([*args, "--resume", str(next(run.glob("epoch001-*.pt")))], "lr_res_cont")
        self.assertEqual(len(full), 144)
        self.assertEqual([x.hex() for x in resumed], [x.hex() for x in full[48:]])
        self.check_ref(full, "wsd", 144, decay_frac=0.3)

    def test_extend_a_run_with_a_fixed_horizon(self):
        args = ["--lr-schedule", "wsd", "--lr-schedule-epochs", "3"]
        out1, run1, part = self.trace([*args, "--epochs", "1"], "lr_ext_part")
        _, _, full = self.trace([*args, "--epochs", "3"], "lr_ext_full")
        _, _, cont = self.trace([*args, "--epochs", "3", "--resume", str(next(run1.glob("epoch001-*.pt")))], "lr_ext_cont")
        self.assertEqual([x.hex() for x in part], [x.hex() for x in full[:48]])
        self.assertEqual([x.hex() for x in cont], [x.hex() for x in full[48:]])
        self.check_ref(full, "wsd", 144)
        self.assertIn("; the run stops at step 48 of the horizon", out1)

    def test_settings_dump_and_config_record_the_schedule(self):
        rc, out, run = run_main(C, ["--lr-schedule", "wsd", "--lr-decay-frac", "0.3", "--lr-schedule-epochs", "3"], "lr_record")
        self.assertEqual(rc, 0, out)
        _, js = settings_of(run)
        self.assertEqual((js["lr_schedule"], js["lr_schedule_epochs"], js["lr_decay_frac"]), ("wsd", 3, 0.3))
        cfg = json.loads(next(run.glob("epoch002-*.json")).read_text(encoding="utf-8"))
        total = 3 * 195
        start = total - int(0.3 * total + 0.5)
        self.assertEqual((cfg["lr_schedule"], cfg["lr_schedule_steps"], cfg["lr_decay_frac"], cfg["lr_decay_start_step"]),
                         ("wsd", total, 0.3, start))
        self.assertIn(f"lr schedule: wsd over {total:,} steps (3 epochs x 195), lr 0.001 until step {start:,}, then linear decay", out)

    def test_off_json_and_stdout_equal_v3b(self):
        rc_c, out_c, run_c = run_main(C, [], "lr_off_c")
        rc_b, out_b, run_b = run_main(B, [], "lr_off_b")
        self.assertEqual((rc_c, rc_b), (0, 0))
        for ep in ("epoch001", "epoch002"):
            self.assertEqual(next(run_c.glob(ep + "-*.json")).read_bytes(), next(run_b.glob(ep + "-*.json")).read_bytes())
        strip = lambda t: [x for x in t.splitlines() if not x.startswith(("MEM ", "holdout:", "train:", "EPOCH", "Finished"))]
        self.assertEqual(strip(out_c), strip(out_b))
        self.assertNotIn("lr schedule:", out_c)

    def test_lr_options_rejected_before_the_run_dir(self):
        bad = [["--lr-schedule", "bogus"], ["--lr-schedule-epochs", "-1"], ["--lr-schedule", "wsd", "--lr-decay-frac", "0"],
               ["--lr-schedule", "wsd", "--lr-decay-frac", "1.5"], ["--lr-schedule", "wsd", "--lr-decay-frac", "nan"],
               ["--lr-decay-frac", "0.3"]]
        for i, extra in enumerate(bad):
            run = UNIT / f"lr_bad{i}"
            old = sys.argv
            sys.argv = ["trainer", *base_argv(run, extra)]
            try:
                with contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit) as cm:
                    C.main()
            finally:
                sys.argv = old
            self.assertEqual(cm.exception.code, 2, extra)
            self.assertIn("error:", err.getvalue())
            self.assertFalse(run.exists(), extra)


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
