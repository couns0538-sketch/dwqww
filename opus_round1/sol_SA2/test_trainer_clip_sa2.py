"""S-A2 tests for trainer_v3c_clip.py (--weight-clip). Runs on the staged copies only:
F:\\opus_scratch\\sol_SA2\\opus_nnue_smoke_sa2_clip.py (must be byte-identical to trainer_v3c_clip.py in this folder) and
opus_nnue_smoke_sa2_v3c.py (the S50 v3c), loaded with importlib (no train_resid* name on any command line).

  <venv python> -I -B test_trainer_clip_sa2.py -v                 (after opus_nnue_smoke_sa2.py --stage; CPU, 1 thread, Idle)
  <venv python> -I -B test_trainer_clip_sa2.py --clip <copy> -v   (mutation check: test another copy; test_copy_matches fails by design)
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib.util
import io
import math
import os
import sys
import time
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = Path(r"F:\opus_scratch\sol_SA2")
CLIP_SRC = HERE / "trainer_v3c_clip.py"
CLIP_COPY = ROOT / "opus_nnue_smoke_sa2_clip.py"
if "--clip" in sys.argv:  # mutation check only
    _i = sys.argv.index("--clip")
    CLIP_COPY = Path(sys.argv[_i + 1])
    del sys.argv[_i:_i + 2]
V3C_COPY = ROOT / "opus_nnue_smoke_sa2_v3c.py"
PIN_V3C = "ddff28bb6801421793e1767cec8271fe3406a263b0c0dfec03ac0cd97dcadef8"
SAMPLE = ROOT / "inputs" / "data32_sample_50k"
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
C = load(CLIP_COPY)
V = load(V3C_COPY)


class Captured(Exception):
    pass


def parsed(module, argv):
    """module.main() up to parse_args (+ the S-A2 validation right after it): (namespace, clip_units) or SystemExit."""
    orig = argparse.ArgumentParser.parse_args
    holder = {}

    def fake(self, *a, **k):
        ns = orig(self, *a, **k)
        holder["ns"] = ns
        return ns
    argparse.ArgumentParser.parse_args = fake
    old = sys.argv
    sys.argv = ["trainer", *argv, "--holdout", "x.pos", "--hce-dir", "x", "--epoch-positions", "-1"]  # stops at the v3c check
    try:
        with contextlib.redirect_stderr(io.StringIO()) as err:
            try:
                module.main()
            except SystemExit as e:
                holder["exit"] = (e.code, err.getvalue())
    finally:
        argparse.ArgumentParser.parse_args = orig
        sys.argv = old
    return holder


def model(hidden=8, seed=3):
    torch.manual_seed(seed)
    m = C.NNUE(hidden, qat=True, residual=True)
    with torch.no_grad():
        for p in m.parameters():
            p.normal_(0.0, 0.2)
    return m


class Tests(unittest.TestCase):
    def test_copy_matches(self):
        self.assertEqual(hashlib.sha256(CLIP_COPY.read_bytes()).digest(), hashlib.sha256(CLIP_SRC.read_bytes()).digest())
        self.assertEqual(hashlib.sha256(V3C_COPY.read_bytes()).hexdigest(), PIN_V3C)

    def test_off_default_and_settings_dump(self):
        h = parsed(C, [])
        self.assertEqual(h["ns"].weight_clip, 0.0)
        self.assertIn("weight_clip", C.V3C_OFF)
        self.assertEqual(C.V3C_OFF["weight_clip"], 0.0)
        settings = {k: v for k, v in vars(h["ns"]).items() if not (k in C.V3C_OFF and v == C.V3C_OFF[k])}
        hv = parsed(V, [])
        settings_v3c = {k: v for k, v in vars(hv["ns"]).items() if not (k in V.V3C_OFF and v == V.V3C_OFF[k])}
        self.assertEqual(settings, settings_v3c)  # the off settings dump == v3c's

    def test_bare_flag_is_the_largest_2_24_bound(self):
        h = parsed(C, ["--weight-clip"])
        self.assertEqual(h["ns"].weight_clip, 21704 / 4096)
        self.assertEqual(C.CLIP_UNITS_DEFAULT, 21704)
        self.assertLess(773 * 21704, 2**24)
        self.assertGreaterEqual(773 * 21705, 2**24)
        self.assertEqual(math.floor(h["ns"].weight_clip * 4096), 21704)

    def test_validation(self):
        def error_line(h):
            return h["exit"][1].strip().splitlines()[-1]
        for bad in ("0.0001", "8.0", str(32767 / 4096), "nan", "-1", "inf"):
            h = parsed(C, ["--weight-clip", bad])
            self.assertIn("exit", h, bad)
            self.assertEqual(h["exit"][0], 2, bad)
            self.assertIn("error: --weight-clip C needs 1 <= floor(C*4096) <= 32766", error_line(h), bad)
        for good in ("0.05", str(32766 / 4096), str(1 / 4096)):
            h = parsed(C, ["--weight-clip", good])
            self.assertIn("error: --epoch-positions must be", error_line(h), good)  # passed the clip check, stops at v3c's

    def test_clip_weights_exact(self):
        m = model()
        before = {k: v.clone() for k, v in m.state_dict().items()}
        m.clip_weights(204)
        bound = 204 / 4096
        for k, v in m.state_dict().items():
            self.assertLessEqual(float(v.abs().max()), bound, k)
            inside = before[k].abs() <= bound
            self.assertTrue(torch.equal(v[inside], before[k][inside]), k)   # untouched inside the bound
            self.assertTrue(bool((v[~inside].abs() == bound).all()), k)      # exactly on the bound outside
        self.assertGreater(int((m.ft.weight.abs() == bound).sum()), 0)

    def test_int16_check(self):
        rng = np.random.default_rng(5)
        H = 16
        w1 = rng.integers(-204, 205, 768 * H).astype(np.int16)
        b1 = rng.integers(-204, 205, H).astype(np.int16)
        w2 = rng.integers(-204, 205, 2 * H).astype(np.int16)
        b2 = np.array([204], np.int16)
        rep = C.int16_check([w1, b1, w2, b2], 204)
        a1 = np.abs(w1.astype(np.int64)).reshape(768, H)
        self.assertEqual(rep["lane_bound"], int((np.abs(b1.astype(np.int64)) + a1.sum(axis=0)).max() + 4 * a1.max()))
        self.assertEqual(rep["max_abs"]["B2"], 204)
        self.assertEqual(rep["at_int16_rail"], 0)
        self.assertTrue(rep["lane_bound_below_2^24"])
        for i in range(4):
            arrays = [w1.copy(), b1.copy(), w2.copy(), b2.copy()]
            arrays[i][0] = 205
            with self.assertRaises(ValueError):
                C.int16_check(arrays, 204)

    def test_export_refuses_before_writing(self):
        UNIT.mkdir(parents=True, exist_ok=True)
        m = model()  # |w| up to ~0.8 >> 204/4096, not clipped
        stem = UNIT / "refuse"
        with self.assertRaises(ValueError):
            C.export_forge(m, stem, 2.25, True, 204)
        self.assertFalse(stem.with_suffix(".inc").exists() or stem.with_suffix(".bin").exists())

    def test_export_off_and_on_byte_identical_to_v3c(self):
        UNIT.mkdir(parents=True, exist_ok=True)
        m = model()
        m.clip_weights(21704)
        V.export_forge(m, UNIT / "v3c", 2.25, True)
        C.export_forge(m, UNIT / "off", 2.25, True)
        rep = C.export_forge(m, UNIT / "on", 2.25, True, 21704)
        for ext in (".inc", ".bin"):
            ref = (UNIT / ("v3c" + ext)).read_bytes()
            self.assertEqual((UNIT / ("off" + ext)).read_bytes(), ref, ext)
            self.assertEqual((UNIT / ("on" + ext)).read_bytes(), ref, ext)   # the check never changes the export
        self.assertIsNotNone(rep)

    def test_unchanged_functions_equal_v3c(self):
        def funcs(path):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            out = {}
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    out[node.name] = ast.dump(node)
            return out
        a, b = funcs(V3C_COPY), funcs(CLIP_COPY)
        changed = sorted(k for k in a if a[k] != b.get(k))
        self.assertEqual(changed, ["NNUE", "export_forge", "main"])
        self.assertEqual(sorted(set(b) - set(a)), ["int16_check"])

    def test_training_loop_clips(self):
        if not (SAMPLE / "t00000.pos").exists():
            self.skipTest("staged sample missing")
        UNIT.mkdir(parents=True, exist_ok=True)
        run = UNIT / "loop"
        argv = ["--train", str(SAMPLE / "t00000.pos"), "--holdout", str(SAMPLE / "h000.pos"), "--hce-dir", str(SAMPLE),
                "--device", "cpu", "--residual", "--log-every", "1e9", "--shape", "16", "--epochs", "1", "--steps-per-epoch", "4",
                "--batch-size", "256", "--val-positions", "1024", "--seed", "7", "--adam-impl", "torch", "--lr", "0.01",
                "--weight-clip", str(8 / 4096), "--run-dir", str(run)]
        old = sys.argv
        sys.argv = ["trainer", *argv]
        try:
            with contextlib.redirect_stdout(io.StringIO()) as out:
                rc = C.main()
        finally:
            sys.argv = old
        self.assertEqual(rc, 0)
        text = out.getvalue()
        self.assertIn("weight-clip: W1 B1 W2 B2 clamped to +-8/4096", text)
        self.assertIn("INT16 CHECK epoch001", text)
        ck = torch.load(sorted(run.glob("*.pt"))[0], map_location="cpu", weights_only=True)
        self.assertEqual(ck["config"]["weight_clip_units"], 8)
        bound = 8 / 4096
        for k, v in ck["model"].items():
            self.assertLessEqual(float(v.abs().max()), bound, k)
        self.assertGreater(int((ck["model"]["ft.weight"].abs() == bound).sum()), 0)


if __name__ == "__main__":
    unittest.main()
