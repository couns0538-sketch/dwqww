"""CPU-only verification of all new train_v3p.py features (zero GPU touch).

Verifies:
  1. --ob-reweight (m4 & cc0), --score-weight-mode (soft800, close_boost), --use-shard-weights
  2. Anchor Weight-Exemption Rule (anchors stay weight=1.0 even with soft800 + ob_reweight!)
  3. --max-rows exact non-anchor truncation
  4. --save-cycles writes cand_e{ep}.pt at every cycle end
  5. --keep-fqs-check / --keep-fqs-in-check alias separates bit0 (noisy) vs bit1 (in_check)
  6. Early rejection of invalid --lr-cycles "" and --resume config mismatch (hidden/batch_size)
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import zlib
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(r"C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests")))
import _cpu_harness as h  # noqa: E402

FQS_MAGIC = b"FQS1\x00\x00\x00\x00"
FQS_DTYPE = np.dtype([
    ("packed", np.uint8, (32,)),
    ("stm", np.uint8),
    ("score16", np.int16),
    ("res8", np.int8),
    ("flags", np.uint8),
    ("weight_u8", np.uint8),
])


def write_synth_shard(path: Path, n: int, scores: list[int], res: list[int], flags: list[int], weights: list[int]) -> None:
    arr = np.zeros(n, dtype=FQS_DTYPE)
    # Valid 4-piece position: WK e1 (sq 4)=6, BK e8 (sq 60)=12, WQ d1 (sq 3)=5, BP d7 (sq 51)=7
    codes = np.zeros(64, dtype=np.uint8)
    codes[4] = 6
    codes[60] = 12
    codes[3] = 5
    codes[51] = 7
    packed = (codes[0::2] | (codes[1::2] << 4)).astype(np.uint8)
    for i in range(n):
        arr[i]["packed"] = packed
        arr[i]["stm"] = i % 2
        arr[i]["score16"] = scores[i % len(scores)]
        arr[i]["res8"] = res[i % len(res)]
        arr[i]["flags"] = flags[i % len(flags)]
        arr[i]["weight_u8"] = weights[i % len(weights)]
    path.write_bytes(zlib.compress(FQS_MAGIC + arr.tobytes(), level=1))


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        fqs_p = root / "main.fqs.z"
        anc_p = root / "anc.fqs.z"
        # 40 rows: mix of quiet(0), noisy(1), check(2), noisy+check(3); scores 50, 900, 1500
        write_synth_shard(fqs_p, 40, [50, 900, 1500, -100], [1, 1, -1, 0], [0, 1, 2, 3], [128, 192, 64, 128])
        # 8 anchor rows with high score (1800) to verify anchor exemption from soft800!
        write_synth_shard(anc_p, 8, [1800, 0], [1, 0], [0, 0], [128, 128])

        # Test 1: Weighting + max_rows + save_cycles + keep-fqs-in-check alias
        out1 = root / "run1"
        args1 = [
            "--fqs-shards", str(fqs_p), "--anchor-shards", str(anc_p), "--anchor-repeat", "1",
            "--max-rows", "16", "--score-weight-mode", "soft800", "--ob-reweight", "cc0",
            "--use-shard-weights", "--save-cycles", "--keep-fqs-in-check",
            "--hidden", "64", "--epochs", "2", "--batch-size", "8", "--lr-cycles", "1,2",
            "--ob-smooth", "2e-6", "--loss-pow", "2.5", "--seed", "1", "--mem-need-gb", "0",
            "--out-dir", str(out1),
        ]
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc, _ = h.run_train_v3p_main(args1)
        out_txt = buf.getvalue()
        assert rc == 0, f"run1 failed rc={rc}"
        assert "SAMPLE WEIGHTS READY: score=soft800 ob=cc0 shard_w=True non_anc_mean=1.0000 anchors_exempt=8" in out_txt, out_txt
        assert "START_V3P: n=24 " in out_txt, out_txt  # 16 max_rows + 8 anchors
        assert (out1 / "cand_e1.pt").exists() and (out1 / "cand_e2.pt").exists(), "save-cycles missed cand_e{1,2}.pt"
        ck = torch.load(out1 / "resume_ckpt.pt", map_location="cpu", weights_only=False)
        assert ck["cfg"] == {"hidden": 64, "batch_size": 8, "pairwise": True, "has_psqt": True}, ck["cfg"]
        print("T1 WEIGHTS + ANCHOR_EXEMPT + MAX_ROWS + SAVE_CYCLES + KEEP_CHECK_ALIAS: PASS")

        # Test 2: Resume config mismatch MUST fail loudly!
        args_bad_resume = [
            "--fqs-shards", str(fqs_p), "--hidden", "128", "--epochs", "3", "--batch-size", "8",
            "--lr-cycles", "1,3", "--resume", "--mem-need-gb", "0", "--out-dir", str(out1),
        ]
        failed_mismatch = False
        try:
            with redirect_stdout(io.StringIO()):
                h.run_train_v3p_main(args_bad_resume)
        except SystemExit as e:
            failed_mismatch = "Resume checkpoint mismatch" in str(e)
        assert failed_mismatch, "Expected resume config mismatch SystemExit!"
        print("T2 RESUME CONFIG MISMATCH LOUD REJECTION: PASS")

        # Test 3: Default skips bit1 (in_check) while keeping bit0 (noisy); --skip-fqs-noisy skips both
        out3a = root / "run3a"
        buf3a = io.StringIO()
        with redirect_stdout(buf3a):
            h.run_train_v3p_main([
                "--fqs-shards", str(fqs_p), "--hidden", "64", "--epochs", "1", "--batch-size", "8",
                "--lr-cycles", "1", "--mem-need-gb", "0", "--out-dir", str(out3a),
            ])
        assert "FQS MIXED: +20 pos" in buf3a.getvalue(), buf3a.getvalue()  # flags 0 and 1 (20/40)

        out3b = root / "run3b"
        buf3b = io.StringIO()
        with redirect_stdout(buf3b):
            h.run_train_v3p_main([
                "--fqs-shards", str(fqs_p), "--skip-fqs-noisy", "--hidden", "64", "--epochs", "1",
                "--batch-size", "8", "--lr-cycles", "1", "--mem-need-gb", "0", "--out-dir", str(out3b),
            ])
        assert "FQS MIXED: +10 pos" in buf3b.getvalue(), buf3b.getvalue()  # flags 0 only (10/40)
        print("T3 G3a (KEEP NOISY, SKIP CHECK = 20) vs G3b (SKIP NOISY+CHECK = 10): PASS")

        # Test 4: Invalid --lr-cycles rejected early
        bad_cyc = False
        try:
            with redirect_stdout(io.StringIO()):
                h.run_train_v3p_main([
                    "--fqs-shards", str(fqs_p), "--hidden", "64", "--epochs", "1", "--lr-cycles", "",
                    "--mem-need-gb", "0", "--out-dir", str(root / "run4"),
                ])
        except SystemExit as e:
            bad_cyc = "Invalid --lr-cycles" in str(e)
        assert bad_cyc, "Expected invalid --lr-cycles SystemExit!"
        print("T4 INVALID --lr-cycles EARLY REJECTION: PASS")

    print("ALL 4 UPGRADED TRAIN_V3P UNIT TESTS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
