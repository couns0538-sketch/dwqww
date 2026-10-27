#!/usr/bin/env python3
"""Unit tests for the S09 v2 files (trainer defaults/recipe, export, 8-head selection, validation helpers).
Run: python -I -B test_forge_sol_S09_v2.py   (CPU torch + numpy; one thread; nothing is trained).
Optional: S09_CURRENT_TRAINER=<renamed copy of the current v3b trainer> also compares defaults and export bytes
against it (the copy must not carry a train_resid* name)."""
from __future__ import annotations
import argparse, hashlib, io, json, os, struct, sys, tempfile, unittest
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import torch  # noqa: E402

torch.set_num_threads(1)
import forge_sol_S09_export_identity_v2 as ei  # noqa: E402
import forge_sol_S09_holdout_validate_v2 as hv  # noqa: E402
import opus_s09_patch_one_file as po  # noqa: E402
import opus_s09_split_pos as sp  # noqa: E402

V2 = ei.load_trainer(HERE / "forge_sol_S09_trainer_buckets_v2.py", "s09_v2_under_test")
CUR_PATH = os.environ.get("S09_CURRENT_TRAINER")
CUR = ei.load_trainer(CUR_PATH, "s09_current_under_test") if CUR_PATH else None

V3B_DEFAULTS = {"shape": 128, "residual": False, "epochs": 8, "batch_size": 4096, "lr": 1e-3, "seed": 1,
                "final_full_val": False, "warmup_steps": 300, "blend_start": 1.0, "blend_end": 0.6,
                "val_positions": 4_000_000, "min_lr_frac": 0.01, "device": "directml", "adam_impl": "dml",
                "dev_scalars": 1, "loss_sync_every": 128, "sigmoid_k": 2.25}


class _Captured(Exception):
    pass


def parser_of(mod):
    """Run mod.main() only up to parse_args and return the parser (nothing else executes)."""
    box = {}
    orig = argparse.ArgumentParser.parse_args

    def grab(self, *a, **k):
        box["p"] = self
        raise _Captured
    argparse.ArgumentParser.parse_args = grab
    try:
        mod.main()
    except _Captured:
        pass
    finally:
        argparse.ArgumentParser.parse_args = orig
    return box["p"]


def defaults(mod):
    return {a.dest: a.default for a in parser_of(mod)._actions if a.dest != "help"}


class Defaults(unittest.TestCase):
    def test_v3b_defaults_restored(self):
        d = defaults(V2)
        for k, v in V3B_DEFAULTS.items():
            self.assertEqual(d[k], v, k)
        self.assertEqual(d["buckets"], 1)
        flags = {s for a in parser_of(V2)._actions for s in a.option_strings}
        self.assertNotIn("--standalone", flags)

    def test_recipe_args_give_f006(self):
        args = (HERE / "forge_sol_S09_f006_recipe_args_v2.txt").read_text().split()
        a = parser_of(V2).parse_args(["--holdout", "h.pos", "--hce-dir", "."] + args)
        got = {k: getattr(a, k) for k in ("shape", "residual", "epochs", "batch_size", "lr", "seed", "final_full_val",
                                           "warmup_steps", "blend_end", "val_positions", "init_check", "buckets")}
        self.assertEqual(got, {"shape": 256, "residual": True, "epochs": 48, "batch_size": 8192, "lr": 7.07e-4,
                               "seed": 25, "final_full_val": True, "warmup_steps": 300, "blend_end": 0.6,
                               "val_positions": 1_000_000, "init_check": True, "buckets": 1})
        rec = json.loads((HERE / "forge_sol_S09_f006_recipe_v2.json").read_text())
        self.assertEqual(rec["recipe_args"], args)

    @unittest.skipUnless(CUR, "S09_CURRENT_TRAINER not set")
    def test_defaults_equal_current(self):
        d2, dc = defaults(V2), defaults(CUR)
        self.assertEqual(d2.pop("buckets"), 1)
        self.assertEqual(d2, dc)


def tiny_model(mod, hidden=8, buckets=None, seed=3):
    torch.manual_seed(seed)
    kw = {} if buckets is None else {"buckets": buckets}
    m = mod.NNUE(hidden, residual=True, **kw)
    with torch.no_grad():
        for p in m.parameters():
            p.copy_(torch.round(torch.randn_like(p) * 300) / 4096)
    return m


class Export(unittest.TestCase):
    def test_one_head_layout(self):
        with tempfile.TemporaryDirectory() as t:
            V2.export_forge(tiny_model(V2, buckets=1), Path(t) / "n", 2.25, True)
            net = ei.parse_inc(Path(t) / "n.inc")
            self.assertEqual((net["heads"], net["hidden"], net["head_macro"]), (1, 8, []))
            self.assertIn("static const std::int16_t NnueB2 = ", (Path(t) / "n.inc").read_text())

    def test_eight_head_layout_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as t:
            m = tiny_model(V2, buckets=8)
            V2.export_forge(m, Path(t) / "a", 2.25, True)
            net = ei.parse_inc(Path(t) / "a.inc")
            self.assertEqual((net["heads"], net["head_macro"]), (8, [("FORGE_NNUE_OUTPUT_HEADS", "8")]))
            V2.export_forge(ei.model_from_net(V2, net, buckets=8), Path(t) / "b", 2.25, True)
            self.assertEqual((Path(t) / "a.inc").read_bytes(), (Path(t) / "b.inc").read_bytes())

    @unittest.skipUnless(CUR, "S09_CURRENT_TRAINER not set")
    def test_one_head_bytes_equal_current(self):
        with tempfile.TemporaryDirectory() as t:
            V2.export_forge(tiny_model(V2, buckets=1), Path(t) / "v2", 2.25, True)
            CUR.export_forge(tiny_model(CUR), Path(t) / "cur", 2.25, True)
            for ext in ("inc", "bin"):
                self.assertEqual((Path(t) / f"v2.{ext}").read_bytes(), (Path(t) / f"cur.{ext}").read_bytes(), ext)


def codes_with(pieces):
    """One board row (64 codes) with exactly `pieces` pieces: two kings plus pawns/knights."""
    c = torch.zeros(64, dtype=torch.long)
    c[4], c[60] = 6, 12
    sq = [s for s in range(8, 56)] + [0, 1, 2, 3, 5, 6, 7, 56, 57, 58, 59, 61, 62, 63]
    for i in range(pieces - 2):
        c[sq[i]] = 2 if i % 2 else 7 + 1
    return c


class Heads(unittest.TestCase):
    def test_forward_picks_head_by_piece_count(self):
        m = V2.NNUE(8, residual=True, buckets=8)
        with torch.no_grad():
            m.out.weight.zero_()
            m.out.bias.copy_(torch.arange(8, dtype=torch.float32) / 64)
        counts = [2, 4, 5, 8, 9, 16, 17, 24, 25, 28, 29, 32]
        codes = torch.stack([codes_with(p) for p in counts])
        out = m(codes, torch.zeros(len(counts), dtype=torch.long), torch.zeros(len(counts)))
        want = [min(max((p - 1) // 4, 0), 7) / 64 for p in counts]
        self.assertEqual(out.tolist(), want)

    def test_nibble_counter_matches(self):
        boards = []
        for p in (2, 3, 4, 5, 12, 13, 31, 32):
            c = codes_with(p).numpy().astype(np.uint8)
            boards.append(c[0::2] | (c[1::2] << 4))
        pieces, heads = hv.heads_from_boards(np.asarray(boards, dtype=np.uint8))
        self.assertEqual(pieces.tolist(), [2, 3, 4, 5, 12, 13, 31, 32])
        self.assertEqual(heads.tolist(), [0, 0, 0, 1, 2, 3, 7, 7])

    def test_replicate8_keeps_logits(self):
        torch.manual_seed(1)
        with tempfile.TemporaryDirectory() as t:
            V2.export_forge(tiny_model(V2, buckets=1), Path(t) / "n", 2.25, True)
            net = ei.parse_inc(Path(t) / "n.inc")
        one = ei.model_from_net(V2, net, buckets=1)
        eight = ei.model_from_net(V2, hv.replicate8(net), buckets=8)
        codes = torch.stack([codes_with(p) for p in range(2, 33)])
        stm = torch.zeros(len(codes), dtype=torch.long)
        hce = torch.linspace(-1, 1, len(codes))
        self.assertLessEqual((one(codes, stm, hce) - eight(codes, stm, hce)).abs().max().item(), 1e-6)


class Helpers(unittest.TestCase):
    def test_patch_one_file(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / "base.txt").write_bytes(b"a\nb\nc\nd\n")  # LF bytes, like the git blob the tool is used on
            (t / "p.diff").write_bytes(b"--- x/other\n+++ other\n@@ -1,1 +1,1 @@\n-q\n+r\n"
                                       b"--- /old/src/f.inc\n+++ src/f.inc\n@@ -2,2 +2,3 @@\n b\n-c\n+C\n+C2\n")
            want = b"a\nb\nC\nC2\nd\n"
            md5 = hashlib.md5(want).hexdigest()
            with redirect_stdout(io.StringIO()):
                self.assertEqual(po.main([str(t / "p.diff"), "src/f.inc", str(t / "base.txt"), str(t / "o.txt"), "--md5", md5]), 0)
                self.assertEqual((t / "o.txt").read_bytes(), want)
                self.assertEqual(po.main([str(t / "p.diff"), "src/f.inc", str(t / "base.txt"), str(t / "o2.txt"), "--md5", "0" * 32]), 1)

    def test_split_pos(self):
        n = 5
        boards = (np.arange(n * 32) % 251).astype(np.uint8)
        score = np.arange(n, dtype="<i2") * 7
        meta = np.arange(n, dtype=np.uint8)
        hce = np.arange(n, dtype="<i2") * -3
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / "x.pos").write_bytes(b"FPOS" + struct.pack("<IQ", 1, n) + boards.tobytes() + score.tobytes() + meta.tobytes())
            (t / "x.hce").write_bytes(b"FHCE" + struct.pack("<IQ", 1, n) + hce.tobytes())
            with redirect_stdout(io.StringIO()):
                sp.main([str(t / "x.pos"), str(t / "x.hce"), "1", "4", str(t / "y")])
            d = V2.load_set([str(t / "y.pos")], str(t))
            self.assertEqual(d["n"], 3)
            self.assertEqual(d["boards"].tobytes(), boards.reshape(n, 32)[1:4].tobytes())
            self.assertEqual(d["score"].tolist(), score[1:4].tolist())
            self.assertEqual(d["meta"].tolist(), meta[1:4].tolist())
            self.assertEqual(d["hce"].tolist(), hce[1:4].tolist())


if __name__ == "__main__":
    unittest.main(verbosity=2)
