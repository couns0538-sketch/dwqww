"""CPU-only end-to-end integration & regression suite for Stream B (Server-Day v2).

Strict hygiene:
  - 100% CPU-only env vars set before importing torch and propagated to all subprocesses.
  - Zero GPU access, zero fastchess launches, workers <= 2 everywhere.
  - All temporary artifacts isolated under streamB_serverday_v2/_work_test_<uuid> and removed in finally:.
  - Zero bytecode / pytest cache creation when run with `-B -p no:cacheprovider`.
"""
from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import uuid
import zlib
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Must be set before importing torch.
os.environ["HIP_VISIBLE_DEVICES"] = ""
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["ROCR_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["FORGE_MIN_FREE_RAM_GB"] = "0"

import chess  # noqa: E402
import chess.syzygy  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402
import torch  # noqa: E402

STREAM_B_DIR = Path(__file__).resolve().parents[1]
FORGE_FIXES_DIR = STREAM_B_DIR.parents[1]
LAB_ROOT = FORGE_FIXES_DIR.parents[1]
PIPELINE_DIR = LAB_ROOT / "pipeline"
FT_TRITON_DIR = PIPELINE_DIR / "ft_triton"
FILTER_QUEST_DIR = LAB_ROOT / "neon" / "filter_quest"

GEN_CC0_PATH = FORGE_FIXES_DIR / "gen_cc0_selfgame_fqs.py"
RESCORE_PATH = FORGE_FIXES_DIR / "rescore_fqs_selective.py"
PARTITION_PATH = FILTER_QUEST_DIR / "partition_fqs_buckets.py"
TRAIN_STREAM_PATH = FORGE_FIXES_DIR / "train_v3p_stream.py"
LINUX_GUARDS_PATH = FORGE_FIXES_DIR / "teamwork_wave4" / "streamB_linux_serverday" / "linux_guards.py"

BASE_EXE = FORGE_FIXES_DIR / "builds" / "base_r15dsg.exe"
FUSED_V3_EXE = FORGE_FIXES_DIR / "builds" / "v3p_fused_v3_engine.exe"
R0067_NET = LAB_ROOT / "runs" / "forge" / "r0067" / "train" / "cand.fnn3"
CONFIG_TOML = PIPELINE_DIR / "config.forge.toml"
BOOK_CC0_EPD = FORGE_FIXES_DIR / "book_cc0_clean.epd"
SYZYGY_DIR = LAB_ROOT / "tablebases" / "syzygy345"
PARITY_FENS_JSON = FORGE_FIXES_DIR / "teamwork_wave2" / "streamC_gates" / "parity_fens_8ob.json"

for _p in (str(FT_TRITON_DIR), str(PIPELINE_DIR), str(FORGE_FIXES_DIR), str(FILTER_QUEST_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import forge_train as ft  # noqa: E402
import forge_v3  # noqa: E402
import forge_v3p  # noqa: E402
import gen_cc0_selfgame_fqs as gen_mod  # noqa: E402
import rescore_fqs_selective as rescore_mod  # noqa: E402
import train_v3p as tv3p  # noqa: E402
import batch_kernel_c as bc  # noqa: E402  # requires ft.triton_kernels() path from train_v3p
import train_v3p_stream as stream_mod  # noqa: E402

FQS_MAGIC = gen_mod.FQS_MAGIC
FQS_DTYPE = gen_mod.FQS_DTYPE
CMAP = gen_mod.CMAP


@pytest.fixture
def local_tmp() -> Path:
    d = STREAM_B_DIR / f"_work_test_{uuid.uuid4().hex[:10]}"
    d.mkdir(parents=True, exist_ok=True)
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _sub_env(scratch: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    env["HIP_VISIBLE_DEVICES"] = ""
    env["CUDA_VISIBLE_DEVICES"] = ""
    env["ROCR_VISIBLE_DEVICES"] = ""
    env["OMP_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["FORGE_MIN_FREE_RAM_GB"] = "0"
    env["TMP"] = str(scratch)
    env["TEMP"] = str(scratch)
    env["TMPDIR"] = str(scratch)
    if extra:
        env.update(extra)
    return env


def _git_bash_exe() -> str:
    for c in (
        Path(r"C:\Program Files\Git\bin\bash.exe"),
        Path(r"C:\Program Files\Git\usr\bin\bash.exe"),
    ):
        if c.exists():
            return str(c)
    found = shutil.which("bash")
    if found and "WindowsApps" not in found:
        return found
    pytest.skip("Git Bash (non-WindowsApps bash) not available")
    return ""


def _extract_argparse_flags(py_path: Path) -> set[str]:
    tree = ast.parse(py_path.read_text(encoding="utf-8"))
    flags: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_argument"
        ):
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.startswith("--"):
                    flags.add(arg.value)
    return flags


def _read_fqs_shard(path: Path) -> np.ndarray:
    raw = path.read_bytes()
    if path.name.endswith(".z"):
        raw = zlib.decompress(raw)
    assert len(raw) >= 8 and raw[:8] == FQS_MAGIC, f"Invalid FQS1 header in {path}"
    assert (len(raw) - 8) % FQS_DTYPE.itemsize == 0, f"Unaligned FQS1 payload in {path}"
    return np.frombuffer(raw, dtype=FQS_DTYPE, offset=8).copy()


def _fen_to_codes(fen: str) -> tuple[np.ndarray, bool]:
    parts = fen.split()
    codes = np.zeros(64, dtype=np.uint8)
    r = 7
    for row in parts[0].split("/"):
        c = 0
        for ch in row:
            if ch.isdigit():
                c += int(ch)
            else:
                codes[r * 8 + c] = CMAP[ch]
                c += 1
        r -= 1
    return codes, (parts[1] == "w")


class _CpuSparseRowsRaw:
    @staticmethod
    def apply(table: torch.Tensor, bias: torch.Tensor, idx: torch.Tensor) -> torch.Tensor:
        assert table.device.type == "cpu"
        assert bias.device.type == "cpu"
        assert idx.device.type == "cpu"
        safe_idx = idx.long().clamp(min=0)
        gathered = table[safe_idx]
        mask = (idx >= 0).unsqueeze(-1)
        return bias.unsqueeze(0) + (gathered * mask).sum(dim=1)


def _cpu_make_batch_c(
    idx: torch.Tensor,
    packed: torch.Tensor,
    stm: torch.Tensor,
    score16: torch.Tensor,
    res8: torch.Tensor,
    teacher_p: torch.Tensor | None,
    king_map: torch.Tensor,
    output_map: torch.Tensor,
    mirror: bool,
    k400: float,
    blend: float,
    t_weight: float,
):
    b = int(idx.shape[0])
    dev = packed.device
    assert dev.type == "cpu"
    ix = idx.long()
    pk = packed[ix]
    codes = torch.stack((pk & 15, pk >> 4), dim=2).view(b, 64)
    feat = tv3p.fk.stm_features(codes, stm[ix])
    rows = tv3p.fk.king_bucket_rows(feat, king_map, bool(mirror))
    pieces = (codes > 0).sum(dim=1).clamp(max=32).long()
    bucket = output_map[pieces].to(torch.int32)

    s = torch.clamp(score16[ix].to(torch.float32) * float(k400), -40.0, 40.0)
    teacher = 1.0 / (1.0 + torch.exp(-s))
    target = float(blend) * teacher + (1.0 - float(blend)) * (res8[ix].to(torch.float32) + 1.0) * 0.5
    if teacher_p is not None:
        target = (1.0 - float(t_weight)) * target + float(t_weight) * teacher_p[ix]
    hcel = torch.zeros(b, dtype=torch.float32, device=dev)
    return rows, target, hcel, bucket


@dataclass
class _StreamCpuHandle:
    losses: list[float] = field(default_factory=list)


@contextlib.contextmanager
def _cpu_stream_env(*, capture_losses: bool = False):
    handle = _StreamCpuHandle()
    orig_device = torch.device
    orig_empty_cache = torch.cuda.empty_cache
    orig_sparse_raw = tv3p.SparseRowsRaw
    orig_make_batch_c = bc.make_batch_c
    orig_subprocess_run = stream_mod.subprocess.run
    orig_backward = torch.Tensor.backward
    orig_heat_guard = ft.GpuHeatGuard
    orig_ram_guard = ft.RamGuard

    class _CpuDeviceMeta(type):
        def __instancecheck__(cls, instance: Any) -> bool:
            return isinstance(instance, orig_device)

        def __subclasscheck__(cls, subclass: type) -> bool:
            return issubclass(subclass, orig_device)

    class _CpuDeviceProxy(metaclass=_CpuDeviceMeta):
        def __new__(cls, *args, **kwargs):
            if args:
                a0 = args[0]
                if isinstance(a0, orig_device) and a0.type == "cuda":
                    return orig_device("cpu")
                if isinstance(a0, str) and a0.startswith("cuda"):
                    return orig_device("cpu")
            if isinstance(kwargs.get("device"), str) and kwargs["device"].startswith("cuda"):
                kwargs = dict(kwargs, device="cpu")
            return orig_device(*args, **kwargs)

    class _NoopGuard:
        def __init__(self, *args, **kwargs):
            self.paused_s = 0.0
            self.pauses = 0
            self.max_seen = 0.0

        def tick(self) -> None:
            return None

    def stub_subprocess_run(cmd, *args, **kwargs):
        cmd_s = " ".join(str(x) for x in cmd) if isinstance(cmd, (list, tuple)) else str(cmd)
        if "mem_room.py" in cmd_s:
            return subprocess.CompletedProcess(cmd, 0, stdout="mem_room: CPU_TEST_OK\n", stderr="")
        return orig_subprocess_run(cmd, *args, **kwargs)

    def wrapped_backward(self, *args, **kwargs):
        assert self.device.type == "cpu"
        if capture_losses and self.numel() == 1:
            handle.losses.append(float(self.detach().item()))
        return orig_backward(self, *args, **kwargs)

    try:
        torch.device = _CpuDeviceProxy
        torch.cuda.empty_cache = lambda: None
        tv3p.SparseRowsRaw = _CpuSparseRowsRaw
        bc.make_batch_c = _cpu_make_batch_c
        stream_mod.subprocess.run = stub_subprocess_run
        ft.GpuHeatGuard = _NoopGuard
        ft.RamGuard = _NoopGuard
        if capture_losses:
            torch.Tensor.backward = wrapped_backward
        yield handle
    finally:
        torch.device = orig_device
        torch.cuda.empty_cache = orig_empty_cache
        tv3p.SparseRowsRaw = orig_sparse_raw
        bc.make_batch_c = orig_make_batch_c
        stream_mod.subprocess.run = orig_subprocess_run
        ft.GpuHeatGuard = orig_heat_guard
        ft.RamGuard = orig_ram_guard
        torch.Tensor.backward = orig_backward


def _run_stream_main(argv: list[str], *, capture_losses: bool = False) -> tuple[int, _StreamCpuHandle, str]:
    old_argv = sys.argv
    buf = io.StringIO()
    with _cpu_stream_env(capture_losses=capture_losses) as handle:
        with redirect_stdout(buf):
            try:
                sys.argv = ["train_v3p_stream.py", *argv]
                rc = stream_mod.main()
            finally:
                sys.argv = old_argv
    return int(rc), handle, buf.getvalue()


def _make_synthetic_fqs_shard(path: Path, n: int, seed: int = 7) -> Path:
    rng = np.random.default_rng(seed)
    arr = np.zeros(n, dtype=FQS_DTYPE)
    non_king = np.array([1, 2, 3, 4, 5, 7, 8, 9, 10, 11], dtype=np.uint8)
    for i in range(n):
        codes = np.zeros(64, dtype=np.uint8)
        npcs = int(rng.integers(4, 24))
        sqs = rng.choice(64, size=npcs, replace=False)
        codes[sqs[0]] = 6
        codes[sqs[1]] = 12
        for sq in sqs[2:]:
            codes[sq] = int(rng.choice(non_king))
        arr[i]["packed"] = (codes[0::2] | (codes[1::2] << 4)).astype(np.uint8)
        arr[i]["stm"] = i % 2
        arr[i]["score16"] = int(rng.integers(-500, 501))
        arr[i]["res8"] = int(rng.choice([-1, 0, 1]))
        ob = min(7, max(0, (npcs - 2) // 4))
        arr[i]["flags"] = (ob << 4)
        arr[i]["weight_u8"] = 128 if (i % 3) else 192
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(zlib.compress(FQS_MAGIC + arr.tobytes(), level=1))
    return path


# ---------------------------------------------------------------------------
# 1. gen_cc0_selfgame_fqs.py unit parity & AST flags
# ---------------------------------------------------------------------------


def test_gen_cc0_target_stm_parity_logic_and_flags_unit() -> None:
    pk_b, stm, ob = gen_mod.pack_fen_fast(chess.STARTING_FEN)
    assert len(pk_b) == 32 and stm == 0 and ob == 7

    assert gen_mod._should_skip_plylimit(
        "plylimit", [(i, 320, "a2a3", "8/8/8/8/8/8/8/8 w - - 0 1") for i in range(6)]
    )
    assert not gen_mod._should_skip_plylimit(
        "rule", [(i, 320, "a2a3", "8/8/8/8/8/8/8/8 w - - 0 1") for i in range(6)]
    )

    assert SYZYGY_DIR.exists(), f"Missing Syzygy TB dir {SYZYGY_DIR}"
    with chess.syzygy.open_tablebase(str(SYZYGY_DIR)) as tb:
        assert gen_mod._adjudicate_tb_result(tb, 0, "7k/8/5K2/8/8/8/8/6Q1 w - - 0 1") == 1
        assert gen_mod._adjudicate_tb_result(tb, 0, "7k/8/5K2/8/8/8/6NN/8 w - - 0 1") == 0

    # Sample 200 skewed openings from book_cc0_clean.epd (skewed toward White) and verify exact 50/50 post-random STM
    lines: list[str] = []
    with BOOK_CC0_EPD.open("r", encoding="utf-8") as fh:
        for i, ln in enumerate(fh):
            s = ln.strip()
            if s and i % 100 == 0:
                lines.append(s)
            if len(lines) >= 240:
                break
    assert len(lines) >= 200

    import random

    rng = random.Random(20261128)
    for use_wide in (False, True):
        post_stm = []
        idx = 0
        games = 0
        while len(post_stm) < 200:
            fen0 = lines[idx % len(lines)]
            idx += 1
            b0 = chess.Board(fen0)
            target_turn = chess.WHITE if (games % 2 == 0) else chess.BLACK
            rp = (4 if b0.turn == target_turn else 5) if use_wide else (2 if b0.turn == target_turn else 1)
            ok = True
            for _ in range(rp):
                leg = list(b0.legal_moves)
                if not leg:
                    ok = False
                    break
                b0.push(rng.choice(leg))
            if not ok or not any(b0.legal_moves):
                continue
            assert b0.turn == target_turn
            post_stm.append(b0.turn)
            games += 1
        w_cnt = sum(1 for t in post_stm if t == chess.WHITE)
        b_cnt = sum(1 for t in post_stm if t == chess.BLACK)
        assert w_cnt == 100 and b_cnt == 100, (use_wide, w_cnt, b_cnt)

    gen_flags = _extract_argparse_flags(GEN_CC0_PATH)
    for expected in ("--wide-div-frac", "--tablebase-dir", "--shard-size", "--resume", "--drop-draw-conflicts"):
        assert expected in gen_flags, f"Missing {expected} in {GEN_CC0_PATH}"


# ---------------------------------------------------------------------------
# 2. gen_cc0_selfgame_fqs.py mini 20-game run & --resume verification
# ---------------------------------------------------------------------------


def test_gen_cc0_selfgame_mini_20games_and_resume(local_tmp: Path) -> None:
    out1 = local_tmp / "cc0_mini"
    cmd = [
        sys.executable, "-B", str(GEN_CC0_PATH),
        "--out-dir", str(out1),
        "--book", str(BOOK_CC0_EPD),
        "--config", str(CONFIG_TOML),
        "--tablebase-dir", str(SYZYGY_DIR),
        "--exe", str(BASE_EXE),
        "--net", str(R0067_NET),
        "--positions", "2400",
        "--shard-size", "600",
        "--soft-nodes", "200",
        "--wide-div-frac", "0.15",
        "--startpos-frac", "0.0",
        "--workers", "2",
        "--max-temp-c", "0",
        "--seed", "20261128",
    ]
    r = subprocess.run(cmd, env=_sub_env(local_tmp), capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"gen_cc0 failed:\n{r.stdout}\n{r.stderr}"
    assert not list(out1.glob("*.part")), "Leftover .part files after gen_cc0"

    summary_p = out1 / "summary.json"
    assert summary_p.is_file()
    summary = json.loads(summary_p.read_text(encoding="utf-8"))
    assert summary["games"] >= 20, summary
    assert summary["positions"] >= 2400, summary

    shards = sorted(out1.glob("cc0_w*_s*.fqs.z"))
    assert len(shards) >= 4
    arrs = [_read_fqs_shard(sp) for sp in shards]
    all_arr = np.concatenate(arrs, axis=0)
    assert len(all_arr) == summary["positions"]

    stm = all_arr["stm"]
    res8 = all_arr["res8"]
    sc16 = all_arr["score16"]
    flags = all_arr["flags"]
    w8 = all_arr["weight_u8"]

    assert np.all((stm == 0) | (stm == 1))
    assert np.all((res8 == -1) | (res8 == 0) | (res8 == 1))
    assert np.all(np.abs(sc16) <= 1500)
    assert np.all(w8 == 128)

    white_stm = float((stm == 0).mean())
    assert 0.40 <= white_stm <= 0.60, f"Imbalanced white_stm={white_stm:.4f}"

    # Bit flags 0..3 and OB bits 4..6
    assert int((flags & 2).sum()) == 0, "in_check bit1 must be filtered"
    assert int((flags & 8).sum()) == 0, "draw_conf bit3 must be dropped under default --drop-draw-conflicts"
    assert not ((res8 == 0) & (np.abs(sc16) >= 600)).any(), "draw conflict leaked"
    assert int(((flags & 1) != 0).sum()) > 0, "expected some noisy positions (bit0)"
    assert int((flags & 0x80).sum()) == 0, "bit7 must remain 0"
    obs = (flags >> 4) & 7
    assert np.all((obs >= 0) & (obs <= 7))

    # --resume test on 1 worker with a small book slice
    mini_book = local_tmp / "mini_book.epd"
    with BOOK_CC0_EPD.open("r", encoding="utf-8") as fh:
        mini_book.write_text("".join(fh.readline() for _ in range(40)), encoding="utf-8")

    out_res = local_tmp / "cc0_resume"
    base_resume_cmd = [
        sys.executable, "-B", str(GEN_CC0_PATH),
        "--out-dir", str(out_res),
        "--book", str(mini_book),
        "--config", str(CONFIG_TOML),
        "--tablebase-dir", str(SYZYGY_DIR),
        "--exe", str(BASE_EXE),
        "--net", str(R0067_NET),
        "--shard-size", "200",
        "--soft-nodes", "200",
        "--wide-div-frac", "0.15",
        "--workers", "1",
        "--max-temp-c", "0",
        "--seed", "20261129",
    ]
    r1 = subprocess.run([*base_resume_cmd, "--positions", "100"], env=_sub_env(local_tmp), capture_output=True, text=True, timeout=60)
    assert r1.returncode == 0, r1.stderr
    s0 = out_res / "cc0_w00_s000.fqs.z"
    assert s0.is_file()
    assert sorted(out_res.glob("cc0_w00_s*.fqs.z")) == [s0]
    sha_s0 = hashlib.sha256(s0.read_bytes()).hexdigest()
    n1 = len(_read_fqs_shard(s0))
    assert n1 >= 100

    # Pass 2: --resume at exact existing count -> zero new shards, s0 untouched
    r2 = subprocess.run([*base_resume_cmd, "--positions", str(n1), "--resume"], env=_sub_env(local_tmp), capture_output=True, text=True, timeout=60)
    assert r2.returncode == 0, r2.stderr
    assert sorted(out_res.glob("cc0_w00_s*.fqs.z")) == [s0]
    assert hashlib.sha256(s0.read_bytes()).hexdigest() == sha_s0

    # Pass 3: --resume beyond N1 -> s0 byte-identical, s001 written
    r3 = subprocess.run([*base_resume_cmd, "--positions", str(n1 + 80), "--resume"], env=_sub_env(local_tmp), capture_output=True, text=True, timeout=60)
    assert r3.returncode == 0, r3.stderr
    shards_p3 = sorted(out_res.glob("cc0_w00_s*.fqs.z"))
    assert len(shards_p3) == 2
    assert hashlib.sha256(s0.read_bytes()).hexdigest() == sha_s0
    tot_p3 = sum(len(_read_fqs_shard(p)) for p in shards_p3)
    assert tot_p3 >= n1 + 80


# ---------------------------------------------------------------------------
# 3. rescore_fqs_selective.py --prioritize-opp-castle & atomic output
# ---------------------------------------------------------------------------


def test_rescore_fqs_selective_opp_castle_and_atomic(local_tmp: Path) -> None:
    assert Path(rescore_mod.__file__).resolve() == RESCORE_PATH.resolve()

    in_dir = local_tmp / "rescore_in"
    out_dir = local_tmp / "rescore_out"
    in_dir.mkdir(parents=True, exist_ok=True)

    opp_fens = [
        "r4rk1/pppq1ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPPQ1PPP/2KR3R w - - 0 1",
        "r4rk1/pp1q1ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPPQ1PPP/1K1R3R b - - 0 1",
        "2kr3r/pppq1ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPPQ1PPP/R4RK1 w - - 0 1",
    ]
    endgame_fen = "8/5pk1/6p1/8/8/5NP1/5P1P/6K1 w - - 0 1"  # 7 pieces -> ob=1
    noisy_fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1"
    same_side_fen = "r1bq1rk1/pppp1ppp/2n2n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 1"

    arr = np.zeros(20, dtype=FQS_DTYPE)
    for i in range(20):
        if i in (0, 1):
            fen = chess.STARTING_FEN
            sc, res, lf = 500, 0, 8  # p1: draw conflict bit3
        elif i in (2, 3, 4):
            fen = opp_fens[i - 2]
            sc, res, lf = 30, 0, 0  # p_opp: opposite-side castled middlegame
        elif i in (5, 6):
            fen = endgame_fen
            sc, res, lf = 200, 1, 0  # p3: OB <= 1 non-trivial score
        elif i in (7, 8):
            fen = noisy_fen
            sc, res, lf = 100, 0, 1  # p4: noisy bit0
        else:
            fen = same_side_fen
            sc, res, lf = 10, 0, 0  # neutral control

        pk_b, stm, ob = gen_mod.pack_fen_fast(fen)
        arr[i]["packed"] = np.frombuffer(pk_b, dtype=np.uint8)
        arr[i]["stm"] = stm
        arr[i]["score16"] = sc
        arr[i]["res8"] = res
        arr[i]["flags"] = (ob << 4) | lf
        arr[i]["weight_u8"] = 128

    in_shard = in_dir / "synth_opp.fqs.z"
    in_shard.write_bytes(zlib.compress(FQS_MAGIC + arr.tobytes(), level=1))

    opp_mask = rescore_mod._opp_side_castle_mask(arr["packed"])
    assert opp_mask.tolist() == [i in (2, 3, 4) for i in range(20)]

    mask_no_opp = rescore_mod.select_rescore_mask(arr, max_frac=0.25, prioritize_opp_castle=False)
    mask_with_opp = rescore_mod.select_rescore_mask(arr, max_frac=0.25, prioritize_opp_castle=True)
    assert np.flatnonzero(mask_no_opp).tolist() == [0, 1, 5, 6, 7]
    assert np.flatnonzero(mask_with_opp).tolist() == [0, 1, 2, 3, 4]

    r = subprocess.run(
        [
            sys.executable, "-B", str(RESCORE_PATH),
            "--in-dir", str(in_dir),
            "--out-dir", str(out_dir),
            "--soft-nodes", "200",
            "--max-frac", "0.25",
            "--workers", "2",
            "--exe", str(BASE_EXE),
            "--net", str(R0067_NET),
            "--config", str(CONFIG_TOML),
            "--prioritize-opp-castle",
        ],
        env=_sub_env(local_tmp),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, f"rescore failed:\n{r.stdout}\n{r.stderr}"
    assert not list(out_dir.glob("*.part")), "Leftover .part file after rescore"

    summary_p = out_dir / "rescore_summary.json"
    assert summary_p.is_file()
    reports = json.loads(summary_p.read_text(encoding="utf-8"))
    assert len(reports) == 1
    assert reports[0]["selected"] == 5 and reports[0]["rescored"] == 5

    out_arr = _read_fqs_shard(out_dir / "synth_opp.fqs.z")
    assert len(out_arr) == 20
    assert np.all(np.abs(out_arr[:5]["score16"]) <= 1500)
    assert not np.array_equal(out_arr[2:5]["score16"], arr[2:5]["score16"]), "Selected opp-castle rows must be rescored"
    assert np.array_equal(out_arr[5:], arr[5:]), "Unselected rows must remain bit-identical"


# ---------------------------------------------------------------------------
# 4. forge_v3p.king_layout(16) symmetry/bijection + 1024w kb=16 parity
# ---------------------------------------------------------------------------


def test_forge_v3p_kb16_layout_and_1024w_parity(local_tmp: Path) -> None:
    kmap = forge_v3p.king_layout(16)
    assert len(kmap) == 64
    assert set(kmap) == set(range(16))
    for sq in range(64):
        assert kmap[sq] == kmap[sq ^ 7], f"Mirror symmetry failed at sq={sq}"

    # Verify rank-group disjointness & expected granularity
    r0 = set(kmap[0:8])
    r1 = set(kmap[8:16])
    r2 = set(kmap[16:24])
    r3 = set(kmap[24:32])
    r45 = set(kmap[32:48])
    r67 = set(kmap[48:64])
    assert (r0, r1, r2, r3, r45, r67) == (
        {0, 1, 2, 3}, {4, 5, 6, 7}, {8, 9}, {10, 11}, {12, 13}, {14, 15}
    )

    fens_data = json.loads(PARITY_FENS_JSON.read_text(encoding="utf-8"))
    fens = [item["fen"] if isinstance(item, dict) else item for item in (fens_data["fens"] if isinstance(fens_data, dict) else fens_data)][:60]
    assert len(fens) == 60

    # Check fk.king_bucket_rows matches forge_v3.feature_rows on CPU for kb=16
    test_fens = [
        chess.STARTING_FEN,
        "r4rk1/pppq1ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPPQ1PPP/2KR3R w - - 0 1",
        "7k/8/5K2/8/8/8/8/6Q1 b - - 0 1",
        *fens[:5],
    ]
    t_kmap = torch.tensor(kmap, dtype=torch.int64)
    ref_net = forge_v3p.NetP(hidden=64, king_buckets=16, output_buckets=8, mirror=True, pairwise=True, has_psqt=True)
    for f in test_fens:
        codes_np, is_w = _fen_to_codes(f)
        t_codes = torch.from_numpy(codes_np).unsqueeze(0)
        t_stm = torch.tensor([0 if is_w else 1], dtype=torch.uint8)
        rows_torch = tv3p.fk.king_bucket_rows(tv3p.fk.stm_features(t_codes, t_stm), t_kmap, True)
        ours_ref, theirs_ref = forge_v3.feature_rows(ref_net, codes_np, is_w)
        got_ours = sorted(int(x) for x in rows_torch[0].tolist() if x >= 0)
        got_theirs = sorted(int(x) for x in rows_torch[1].tolist() if x >= 0)
        assert got_ours == sorted(ours_ref) and got_theirs == sorted(theirs_ref)
        assert all(0 <= x < 16 * 768 for x in got_ours + got_theirs)

    # Synthesize 1024w kb=16 ForgeNetV3P -> NetP -> write_net/read_net -> C++ 0-cp parity + PyTorch <=1-cp parity
    with _cpu_stream_env():
        torch.manual_seed(161024)
        model = tv3p.ForgeNetV3P(hidden=1024, king_buckets=16, out_buckets=8, mirror=True, pairwise=True, has_psqt=True)
        with torch.no_grad():
            model.w1.normal_(0.0, 0.08)
            model.fac.normal_(0.0, 0.05)
            model.b1.normal_(0.0, 0.04)
            model.out.weight.normal_(0.0, 0.25)
            model.out.bias.normal_(0.0, 0.08)
            model.psqt_w.normal_(0.0, 0.15)
        model.project()
        net_p = tv3p.to_file_net_p(model)

        net_path = local_tmp / "kb16_1024w.fnn3"
        forge_v3p.write_net(str(net_path), net_p)
        assert net_path.stat().st_size == 25_577_704
        read_back = forge_v3p.read_net(str(net_path))
        assert read_back.king_buckets == 16 and read_back.hidden == 1024 and read_back.king_map == kmap

        # Color-flip symmetry on reference_eval
        for f in test_fens[:4]:
            c_np, is_w = _fen_to_codes(f)
            b_orig = chess.Board(f)
            c_flip, is_w_flip = _fen_to_codes(b_orig.mirror().fen())
            assert forge_v3p.reference_eval(read_back, c_np, is_w) == forge_v3p.reference_eval(read_back, c_flip, is_w_flip)

        # C++ v3p_fused_v3_engine.exe eval vs reference_eval -> exact 0 cp across 60 FENs
        uci_lines = [
            "uci",
            f"setoption name NNUEArchFile value {str(net_path).replace(chr(92), '/')}",
            "setoption name NNUEArch value true",
            "isready",
        ]
        for f in fens:
            uci_lines += [f"position fen {f}", "eval"]
        uci_lines.append("quit")
        r_eng = subprocess.run(
            [str(FUSED_V3_EXE)],
            input="\n".join(uci_lines) + "\n",
            env=_sub_env(local_tmp),
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert r_eng.returncode == 0 and "king_buckets 16" in r_eng.stdout, r_eng.stdout[:400]
        cpp_vals = [int(ln.split()[ln.split().index("nnue") + 1]) for ln in r_eng.stdout.splitlines() if ln.startswith("info string eval")]
        assert len(cpp_vals) == len(fens)

        codes_batch = np.stack([_fen_to_codes(f)[0] for f in fens], axis=0)
        stm_batch = np.array([0 if _fen_to_codes(f)[1] else 1 for f in fens], dtype=np.uint8)
        ref_vals = [forge_v3p.reference_eval(read_back, codes_batch[i], stm_batch[i] == 0) for i in range(len(fens))]
        assert max(abs(a - b) for a, b in zip(ref_vals, cpp_vals)) == 0

        # PyTorch float32 forward on CPU vs reference_eval -> <= 1 cp (and >= 55/60 exact 0 cp)
        model.eval()
        with torch.no_grad():
            logits = model(
                torch.from_numpy(codes_batch),
                torch.from_numpy(stm_batch),
                torch.zeros(len(fens), dtype=torch.float32),
            ).numpy()
        py_vals = np.clip(np.trunc(logits / float(ft.K) * 400.0), -30000, 30000).astype(np.int32)
        diffs = np.abs(py_vals - np.array(ref_vals, dtype=np.int32))
        assert int(diffs.max()) <= 1, f"ForgeNetV3P float32 parity > 1 cp: max={diffs.max()}"
        assert int((diffs == 0).sum()) >= 55, f"Expected >=55/60 exact 0 cp, got {(diffs == 0).sum()}"


# ---------------------------------------------------------------------------
# 5. train_v3p_stream.py --king-buckets 16 CPU smoke & CLI validation
# ---------------------------------------------------------------------------


def test_train_v3p_stream_kb16_cpu_smoke_and_cli(local_tmp: Path) -> None:
    stream_flags = _extract_argparse_flags(TRAIN_STREAM_PATH)
    for req in (
        "--hidden", "--king-buckets", "--use-shard-weights", "--save-cycles",
        "--resume", "--shards-per-superbatch", "--anchor-shards", "--anchor-repeat-per-sb",
        "--distill-net", "--distill-weight",
    ):
        assert req in stream_flags, f"Missing {req} in {TRAIN_STREAM_PATH}"
    assert "--save-ckpt-every" not in stream_flags

    r_bad = subprocess.run(
        [sys.executable, "-B", str(TRAIN_STREAM_PATH), "--save-ckpt-every", "1"],
        env=_sub_env(local_tmp),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r_bad.returncode == 2
    assert "unrecognized arguments: --save-ckpt-every" in r_bad.stderr

    s0 = _make_synthetic_fqs_shard(local_tmp / "shards/s0.fqs.z", 16, seed=101)
    s1 = _make_synthetic_fqs_shard(local_tmp / "shards/s1.fqs.z", 16, seed=102)
    anc = _make_synthetic_fqs_shard(local_tmp / "anc.fqs.z", 4, seed=103)
    out_dir = local_tmp / "train_kb16_out"

    rc, handle, out_txt = _run_stream_main(
        [
            "--fqs-shards", str(s0), str(s1),
            "--anchor-shards", str(anc),
            "--anchor-repeat-per-sb", "1",
            "--shards-per-superbatch", "1",
            "--out-dir", str(out_dir),
            "--hidden", "64",
            "--king-buckets", "16",
            "--epochs", "1",
            "--batch-size", "18",
            "--use-shard-weights",
            "--save-cycles",
            "--lr-cycles", "1",
            "--mem-need-gb", "0",
        ],
        capture_losses=True,
    )
    assert rc == 0, out_txt
    assert handle.losses and all(np.isfinite(x) for x in handle.losses)

    net_p = out_dir / "cand.fnn3"
    ckpt_e1 = out_dir / "cand_e1.pt"
    res_ckpt = out_dir / "resume_ckpt.pt"
    assert net_p.is_file() and ckpt_e1.is_file() and res_ckpt.is_file()

    net_read = forge_v3p.read_net(str(net_p))
    assert net_read.king_buckets == 16 and net_read.hidden == 64
    assert net_read.king_map == forge_v3p.king_layout(16)

    meta_e1 = torch.load(ckpt_e1, map_location="cpu", weights_only=True)
    assert meta_e1["king_buckets"] == 16


# ---------------------------------------------------------------------------
# 6. End-to-end mini pipeline: gen -> partition -> rescore -> FQS1 validation
# ---------------------------------------------------------------------------


def test_e2e_mini_pipeline_gen_partition_rescore_fqs1(local_tmp: Path) -> None:
    d_gen = local_tmp / "step1_gen"
    d_part = local_tmp / "step2_part"
    d_rescore = local_tmp / "step3_rescore"

    r1 = subprocess.run(
        [
            sys.executable, "-B", str(GEN_CC0_PATH),
            "--out-dir", str(d_gen),
            "--book", str(BOOK_CC0_EPD),
            "--config", str(CONFIG_TOML),
            "--tablebase-dir", str(SYZYGY_DIR),
            "--exe", str(BASE_EXE),
            "--net", str(R0067_NET),
            "--positions", "1600",
            "--shard-size", "400",
            "--soft-nodes", "200",
            "--wide-div-frac", "0.15",
            "--workers", "2",
            "--max-temp-c", "0",
            "--seed", "20261130",
        ],
        env=_sub_env(local_tmp),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r1.returncode == 0, r1.stderr

    r2 = subprocess.run(
        [
            sys.executable, "-B", str(PARTITION_PATH),
            "--in-dir", str(d_gen),
            "--out-dir", str(d_part),
            "--buckets", "4",
            "--dedup-mode", "avg",
            "--workers", "2",
        ],
        env=_sub_env(local_tmp),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r2.returncode == 0, r2.stderr
    assert not (d_part / "_buckets_tmp").exists()
    assert not list(d_part.glob("*.part"))
    part_summary = json.loads((d_part / "summary.json").read_text(encoding="utf-8"))
    assert part_summary["kept_rows"] > 0

    part_shards = sorted(d_part.glob("fqs_b*_s*.fqs.z"))
    assert len(part_shards) >= 4
    seen_keys: set[tuple[bytes, int]] = set()
    total_part_rows = 0
    for sp in part_shards:
        arr = _read_fqs_shard(sp)
        total_part_rows += len(arr)
        for row in arr:
            key = (bytes(row["packed"]), int(row["stm"]))
            assert key not in seen_keys, "Duplicate (packed, stm) after avg dedup!"
            seen_keys.add(key)
    assert total_part_rows == part_summary["kept_rows"]

    r3 = subprocess.run(
        [
            sys.executable, "-B", str(RESCORE_PATH),
            "--in-dir", str(d_part),
            "--out-dir", str(d_rescore),
            "--prioritize-opp-castle",
            "--max-frac", "0.10",
            "--soft-nodes", "200",
            "--workers", "2",
            "--exe", str(BASE_EXE),
            "--net", str(R0067_NET),
            "--config", str(CONFIG_TOML),
        ],
        env=_sub_env(local_tmp),
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert r3.returncode == 0, r3.stderr
    assert not list(d_rescore.glob("*.part"))
    res_reports = json.loads((d_rescore / "rescore_summary.json").read_text(encoding="utf-8"))
    tot_sel = sum(x["selected"] for x in res_reports)
    tot_res = sum(x["rescored"] for x in res_reports)
    assert tot_sel > 0 and tot_res == tot_sel

    final_shards = sorted(d_rescore.glob("fqs_b*_s*.fqs.z"))
    assert len(final_shards) == len(part_shards)
    final_rows = 0
    for sp in final_shards:
        arr = _read_fqs_shard(sp)
        final_rows += len(arr)
        assert np.all((arr["stm"] == 0) | (arr["stm"] == 1))
        assert np.all((arr["res8"] == -1) | (arr["res8"] == 0) | (arr["res8"] == 1))
        assert np.all(np.abs(arr["score16"]) <= 1500)
        assert np.all((arr["weight_u8"] >= 128) & (arr["weight_u8"] <= 192))
    assert final_rows == total_part_rows


# ---------------------------------------------------------------------------
# 7. v2 shell scripts, AST flag parity, & Stream B hygiene
# ---------------------------------------------------------------------------


def test_v2_shell_scripts_and_hygiene(local_tmp: Path) -> None:
    bash_exe = _git_bash_exe()
    datagen_sh = STREAM_B_DIR / "run_datagen_epyc_v2.sh"
    train_sh = STREAM_B_DIR / "run_train_stream_gpu_v2.sh"
    runbook_md = STREAM_B_DIR / "SERVER_DAY_V2_RUNBOOK.md"
    assert datagen_sh.is_file() and train_sh.is_file() and runbook_md.is_file()

    gen_real_flags = _extract_argparse_flags(GEN_CC0_PATH)
    train_real_flags = _extract_argparse_flags(TRAIN_STREAM_PATH)
    guard_real_flags = _extract_argparse_flags(LINUX_GUARDS_PATH)

    for sh_path, target_py, real_flags in (
        (datagen_sh, GEN_CC0_PATH, gen_real_flags),
        (train_sh, TRAIN_STREAM_PATH, train_real_flags),
    ):
        raw = sh_path.read_bytes()
        assert b"\r" not in raw, f"CRLF found in {sh_path.name}"
        assert not raw.startswith(b"\xef\xbb\xbf"), f"BOM found in {sh_path.name}"
        txt = raw.decode("utf-8")
        assert txt.startswith("#!/usr/bin/env bash\n")
        assert "set -euo pipefail" in txt

        r_syn = subprocess.run([bash_exe, "-n", str(sh_path)], env=_sub_env(local_tmp), capture_output=True, text=True, timeout=20)
        assert r_syn.returncode == 0, f"bash -n failed for {sh_path.name}:\n{r_syn.stderr}"

        r_dry = subprocess.run([bash_exe, str(sh_path), "--dry-run"], env=_sub_env(local_tmp), capture_output=True, text=True, timeout=20)
        assert r_dry.returncode == 0, f"--dry-run failed for {sh_path.name}:\n{r_dry.stderr}"
        assert target_py.name in r_dry.stdout

        # Validate every emitted --flag on every command line against target script AST
        matched_target = False
        for line in r_dry.stdout.splitlines():
            toks = shlex.split(line)
            if not toks:
                continue
            flags_in_line = {t.split("=", 1)[0] for t in toks if t.startswith("--")}
            if target_py.name in line:
                matched_target = True
                unknown = sorted(flags_in_line - real_flags)
                assert not unknown, f"{sh_path.name} emitted unknown flags for {target_py.name}: {unknown}"
            elif LINUX_GUARDS_PATH.name in line:
                unknown_g = sorted(flags_in_line - guard_real_flags)
                assert not unknown_g, f"{sh_path.name} emitted unknown flags for linux_guards.py: {unknown_g}"
        assert matched_target

        # Static CMD=( ... ) non-comment check
        non_comment = "\n".join(ln for ln in txt.splitlines() if not ln.lstrip().startswith("#"))
        m_cmd = re.search(r"(?<![A-Z0-9_])CMD=\((.*?)\n\)", non_comment, flags=re.DOTALL)
        assert m_cmd is not None, f"Missing CMD=(...) block in {sh_path.name}"
        static_flags = set(re.findall(r"(?<!\w)(--[a-z][a-z0-9-]+)", m_cmd.group(1)))
        assert not (static_flags - real_flags), f"Static unknown flags in {sh_path.name} CMD: {sorted(static_flags - real_flags)}"

    # Datagen v2 contracts
    r_dg_default = subprocess.run([bash_exe, str(datagen_sh), "--dry-run"], env=_sub_env(local_tmp), capture_output=True, text=True, timeout=20)
    assert r_dg_default.returncode == 0
    dg_toks = shlex.split(r_dg_default.stdout.strip())
    for flag in ("--wide-div-frac", "--resume", "--shard-size", "--tablebase-dir"):
        assert flag in dg_toks
    assert dg_toks[dg_toks.index("--wide-div-frac") + 1] == "0.15"

    r_dg_syz = subprocess.run(
        [bash_exe, str(datagen_sh), "--dry-run", "--syzygy-dir", "/tmp/tb_test"],
        env=_sub_env(local_tmp),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r_dg_syz.returncode == 0
    dg_syz_toks = shlex.split(r_dg_syz.stdout.strip())
    assert "--syzygy-dir" not in dg_syz_toks
    assert dg_syz_toks[dg_syz_toks.index("--tablebase-dir") + 1] == "/tmp/tb_test"

    r_dg_syz_eq = subprocess.run(
        [bash_exe, str(datagen_sh), "--dry-run", "--syzygy-dir=/tmp/tb_eq"],
        env=_sub_env(local_tmp),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r_dg_syz_eq.returncode == 0
    dg_syz_eq_toks = shlex.split(r_dg_syz_eq.stdout.strip())
    assert "--syzygy-dir" not in dg_syz_eq_toks
    assert dg_syz_eq_toks[dg_syz_eq_toks.index("--tablebase-dir") + 1] == "/tmp/tb_eq"

    r_dg_syz_env = subprocess.run(
        [bash_exe, str(datagen_sh), "--dry-run"],
        env=_sub_env(local_tmp, {"SYZYGY_DIR": "/tmp/tb_env"}),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r_dg_syz_env.returncode == 0
    dg_syz_env_toks = shlex.split(r_dg_syz_env.stdout.strip())
    assert dg_syz_env_toks[dg_syz_env_toks.index("--tablebase-dir") + 1] == "/tmp/tb_env"

    r_dg_syz_miss = subprocess.run(
        [bash_exe, str(datagen_sh), "--syzygy-dir"],
        env=_sub_env(local_tmp),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r_dg_syz_miss.returncode == 2

    r_dg_out = subprocess.run(
        [bash_exe, str(datagen_sh), "--dry-run", "--out-dir", "/tmp/dg_custom"],
        env=_sub_env(local_tmp),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r_dg_out.returncode == 0
    dg_out_toks = shlex.split(r_dg_out.stdout.strip())
    assert dg_out_toks.count("--out-dir") == 1
    assert dg_out_toks[dg_out_toks.index("--out-dir") + 1] == "/tmp/dg_custom"

    r_dg_out_miss = subprocess.run(
        [bash_exe, str(datagen_sh), "--out-dir"],
        env=_sub_env(local_tmp),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r_dg_out_miss.returncode == 2

    r_dg_nores = subprocess.run(
        [bash_exe, str(datagen_sh), "--dry-run"],
        env=_sub_env(local_tmp, {"RESUME": "0"}),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r_dg_nores.returncode == 0
    assert "--resume" not in shlex.split(r_dg_nores.stdout.strip())

    dg_txt = datagen_sh.read_text(encoding="utf-8")
    assert "exec " not in dg_txt
    assert "47.0" in dg_txt and "53.0" in dg_txt

    # Execute the actual inline Python post-run parity snippet from run_datagen_epyc_v2.sh
    m_parity = re.search(r"<<'PY'\r?\n(.*?)\r?\nPY\s*$", dg_txt, flags=re.DOTALL)
    assert m_parity is not None, "Could not extract inline Python parity check from run_datagen_epyc_v2.sh"
    parity_code = m_parity.group(1)

    for label, n_white, expect_ok in (("parity_pass", 10, True), ("parity_fail", 12, False)):
        p_dir = local_tmp / label
        p_dir.mkdir(parents=True, exist_ok=True)
        arr_p = np.zeros(20, dtype=FQS_DTYPE)
        arr_p["stm"] = np.array([0] * n_white + [1] * (20 - n_white), dtype=np.uint8)
        (p_dir / "cc0_w00_s000.fqs.z").write_bytes(zlib.compress(FQS_MAGIC + arr_p.tobytes(), level=1))
        (p_dir / "summary.json").write_text(json.dumps({"positions": 20}), encoding="utf-8")
        r_par = subprocess.run(
            [sys.executable, "-B", "-", str(p_dir)],
            input=parity_code,
            env=_sub_env(local_tmp),
            capture_output=True,
            text=True,
            timeout=20,
        )
        if expect_ok:
            assert r_par.returncode == 0, f"Expected parity pass, got rc={r_par.returncode}: {r_par.stderr}"
            assert "PARITY_CHECK_PASS:" in r_par.stdout
        else:
            assert r_par.returncode != 0, "Expected parity failure for 60% white_stm"
            assert "PARITY_CHECK_PASS:" not in r_par.stdout, f"Failed parity check leaked pass line: {r_par.stdout!r}"

    # Train v2 contracts
    r_tr_def = subprocess.run([bash_exe, str(train_sh), "--dry-run"], env=_sub_env(local_tmp), capture_output=True, text=True, timeout=20)
    assert r_tr_def.returncode == 0
    assert LINUX_GUARDS_PATH.name in r_tr_def.stdout
    train_line = [ln for ln in r_tr_def.stdout.splitlines() if TRAIN_STREAM_PATH.name in ln][0]
    tr_toks = shlex.split(train_line)
    for flag in ("--hidden", "--king-buckets", "--use-shard-weights", "--save-cycles", "--resume", "--distill-net", "--distill-weight"):
        assert flag in tr_toks
    assert "--save-ckpt-every" not in tr_toks

    r_tr_nodist = subprocess.run(
        [bash_exe, str(train_sh), "--dry-run"],
        env=_sub_env(local_tmp, {"DISTILL_NET": ""}),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r_tr_nodist.returncode == 0
    nodist_line = [ln for ln in r_tr_nodist.stdout.splitlines() if TRAIN_STREAM_PATH.name in ln][0]
    nodist_toks = shlex.split(nodist_line)
    assert "--distill-net" not in nodist_toks
    assert "--distill-weight" not in nodist_toks

    r_tr_noguard_nores = subprocess.run(
        [bash_exe, str(train_sh), "--dry-run"],
        env=_sub_env(local_tmp, {"RESUME": "0", "SKIP_GUARDS": "1"}),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r_tr_noguard_nores.returncode == 0
    assert LINUX_GUARDS_PATH.name not in r_tr_noguard_nores.stdout
    noguard_toks = shlex.split(r_tr_noguard_nores.stdout.strip())
    assert "--resume" not in noguard_toks

    r_tr_ovr = subprocess.run(
        [bash_exe, str(train_sh), "--dry-run"],
        env=_sub_env(local_tmp, {"HIDDEN": "1536", "KING_BUCKETS": "16"}),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r_tr_ovr.returncode == 0
    ovr_line = [ln for ln in r_tr_ovr.stdout.splitlines() if TRAIN_STREAM_PATH.name in ln][0]
    ovr_toks = shlex.split(ovr_line)
    assert ovr_toks[ovr_toks.index("--hidden") + 1] == "1536"
    assert ovr_toks[ovr_toks.index("--king-buckets") + 1] == "16"

    r_tr_eq_flags = subprocess.run(
        [bash_exe, str(train_sh), "--dry-run", "--hidden=1536", "--king-buckets=16", "--out-dir", "/tmp/tr_custom"],
        env=_sub_env(local_tmp),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r_tr_eq_flags.returncode == 0
    eq_line = [ln for ln in r_tr_eq_flags.stdout.splitlines() if TRAIN_STREAM_PATH.name in ln][0]
    eq_toks = shlex.split(eq_line)
    assert eq_toks[eq_toks.index("--hidden") + 1] == "1536"
    assert eq_toks[eq_toks.index("--king-buckets") + 1] == "16"
    assert eq_toks.count("--out-dir") == 1
    assert eq_toks[eq_toks.index("--out-dir") + 1] == "/tmp/tr_custom"

    env_lab_fb = _sub_env(local_tmp, {"LAB_ROOT": "/tmp/lab_fb"})
    env_lab_fb.pop("FORGE_LAB_ROOT", None)
    r_tr_lab = subprocess.run(
        [bash_exe, str(train_sh), "--dry-run"],
        env=env_lab_fb,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert r_tr_lab.returncode == 0
    assert "/tmp/lab_fb/neon/forge_fixes/train_v3p_stream.py" in r_tr_lab.stdout

    r_tr_bad = subprocess.run([bash_exe, str(train_sh), "--hidden", "768", "--dry-run"], env=_sub_env(local_tmp), capture_output=True, text=True, timeout=20)
    assert r_tr_bad.returncode == 2

    r_tr_bad_kb = subprocess.run([bash_exe, str(train_sh), "--king-buckets", "32", "--dry-run"], env=_sub_env(local_tmp), capture_output=True, text=True, timeout=20)
    assert r_tr_bad_kb.returncode == 2

    r_tr_out_miss = subprocess.run([bash_exe, str(train_sh), "--out-dir"], env=_sub_env(local_tmp), capture_output=True, text=True, timeout=20)
    assert r_tr_out_miss.returncode == 2

    # Forbidden-word check across all *.py, *.sh, *.md in streamB_serverday_v2/
    forbidden_re = re.compile(r"\b" + "cu" + r"red?\b", re.IGNORECASE)
    checked = 0
    for ext in ("*.py", "*.sh", "*.md"):
        for p in STREAM_B_DIR.rglob(ext):
            checked += 1
            m = forbidden_re.search(p.read_text(encoding="utf-8"))
            assert m is None, f"Forbidden word {m.group(0)!r} found in {p}"
    assert checked >= 4
