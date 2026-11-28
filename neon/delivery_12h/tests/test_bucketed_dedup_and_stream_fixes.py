"""CPU-only pytest suite for Stream B (Linux Server-Day kit, bucketed dedup, and stream fixes).

Strict hygiene:
  - CPU-only env vars set at module import time (zero GPU access, zero fastchess).
  - All scratch files isolated under streamB_linux_serverday/_work_test_<uuid> and removed in finally:.
  - Maximum 2 CPU worker processes/threads in all tests.
  - Zero bytecode / pytest cache creation when run with `-B -p no:cacheprovider`.
"""
from __future__ import annotations

import ast
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

os.environ["HIP_VISIBLE_DEVICES"] = ""
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["ROCR_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["FORGE_MIN_FREE_RAM_GB"] = "0"

import numpy as np  # noqa: E402
import pytest  # noqa: E402

STREAM_B_DIR = Path(__file__).resolve().parents[1]
FORGE_FIXES_DIR = STREAM_B_DIR.parents[1]
LAB_ROOT = FORGE_FIXES_DIR.parents[1]
FILTER_QUEST_DIR = LAB_ROOT / "neon" / "filter_quest"
DATAGEN_V2_PATH = FORGE_FIXES_DIR / "teamwork_wave2" / "streamB_nnue" / "gen_cc0_selfgame_fqs_v2.py"
PARTITION_PATH = FILTER_QUEST_DIR / "partition_fqs_buckets.py"
FILTER_PATH = FILTER_QUEST_DIR / "filter_fqs_to_fqs.py"
TRAIN_STREAM_PATH = FORGE_FIXES_DIR / "train_v3p_stream.py"
POST_G3_PATH = FORGE_FIXES_DIR / "run_post_g3_pipeline.py"
MAKE_SWA_PATH = FORGE_FIXES_DIR / "make_swa_v3p.py"
LINUX_GUARDS_PATH = STREAM_B_DIR / "linux_guards.py"

for _p in (str(STREAM_B_DIR), str(FILTER_QUEST_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import filter_fqs_to_fqs as fq  # noqa: E402
import linux_guards as lg  # noqa: E402
import partition_fqs_buckets as pfb  # noqa: E402

FQS_DTYPE = fq.FQS_DTYPE


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
    env["TMP"] = str(scratch)
    env["TEMP"] = str(scratch)
    env["TMPDIR"] = str(scratch)
    if extra:
        env.update(extra)
    return env


def _git_bash_exe() -> str:
    candidates = [
        Path(r"C:\Program Files\Git\bin\bash.exe"),
        Path(r"C:\Program Files\Git\usr\bin\bash.exe"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    found = shutil.which("bash")
    if found and "WindowsApps" not in found:
        return found
    pytest.skip("Git Bash (non-WindowsApps bash) not available")
    return ""


def _make_row(
    tag0: int,
    tag1: int = 0,
    *,
    stm: int = 0,
    score16: int = 0,
    res8: int = 0,
    flags: int = 0,
    weight_u8: int = 128,
) -> np.ndarray:
    r = np.zeros(1, dtype=FQS_DTYPE)
    r[0]["packed"][0] = 0x61
    r[0]["packed"][1] = tag0 & 0xFF
    r[0]["packed"][7] = (tag0 >> 8) & 0xFF
    r[0]["packed"][15] = tag1 & 0xFF
    r[0]["packed"][23] = (tag1 >> 8) & 0xFF
    r[0]["packed"][30] = 0xC0
    r[0]["stm"] = stm
    r[0]["score16"] = score16
    r[0]["res8"] = res8
    r[0]["flags"] = flags
    r[0]["weight_u8"] = weight_u8
    return r


def _load_fqs_map(out_dir: Path) -> dict[bytes, tuple[int, int, int, int]]:
    mp: dict[bytes, tuple[int, int, int, int]] = {}
    for f in sorted(out_dir.glob("fqs_*.fqs.z")):
        arr = fq.read_fqs(f)
        for row in arr:
            key = row["packed"].tobytes() + bytes([int(row["stm"])])
            assert key not in mp, f"Duplicate output key in {f.name}"
            mp[key] = (
                int(row["score16"]),
                int(row["res8"]),
                int(row["flags"]),
                int(row["weight_u8"]),
            )
    return mp


def _extract_argparse_flags(py_path: Path) -> set[str]:
    tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
    flags: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "add_argument":
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.startswith("--"):
                        flags.add(arg.value)
    return flags


# ---------------------------------------------------------------------------
# (a) partition_fqs_buckets.py selftest, multi-shard parity, cleanup, spread
# ---------------------------------------------------------------------------


def test_partition_fqs_buckets_selftest_subprocess(local_tmp: Path) -> None:
    r = subprocess.run(
        [sys.executable, "-B", str(PARTITION_PATH), "--selftest"],
        env=_sub_env(local_tmp),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, f"partition_fqs_buckets --selftest failed:\n{r.stdout}\n{r.stderr}"
    assert "PARTITION_FQS_BUCKETS_SELFTEST_PASS:" in r.stdout


@pytest.mark.parametrize("dedup_mode", ["first", "avg"])
def test_partition_fqs_buckets_multishard_parity_and_cleanup(local_tmp: Path, dedup_mode: str) -> None:
    rng = np.random.default_rng(20261128 + (1 if dedup_mode == "avg" else 0))
    in_dir = local_tmp / "in_shards"
    in_dir.mkdir(parents=True, exist_ok=True)

    # 4 shards with deterministic edge cases + 1,000+ randomized cross-shard rows
    # Edge cases in shard 0 & 1 & 2 & 3:
    # - t1_corrupt: stm=2, res8=2, score16=30001, score16=-30001
    # - t1_in_check: flags bit 1
    # - t2_noisy: flags bit 0 (kept when skip_noisy=False, dropped when True - we test skip_noisy=False & hs800)
    # - t2_draw_conflict: res8=0 & |score16| >= 600
    # - t2_swing: flags bit 2
    # - t2_hs800: |score16| in [800, 1199] and >= 1200
    # - same packed with stm=0 vs stm=1 (must stay distinct)
    # - banker's rounding .5 ties: (1, 2)->2 and (2, 3)->2
    # - res_sum == 0 tie -> res8 = 0
    # - weight_u8 clip at 192 for count >= 3
    s0_edges = np.concatenate([
        _make_row(1, stm=2, score16=10, res8=0),          # corrupt stm
        _make_row(2, stm=0, score16=10, res8=2),          # corrupt res8
        _make_row(3, stm=0, score16=30001, res8=1),       # corrupt score > 30000
        _make_row(4, stm=0, score16=100, res8=0, flags=2),  # in_check
        _make_row(5, stm=0, score16=-650, res8=0, flags=0), # draw conflict
        _make_row(6, stm=0, score16=50, res8=1, flags=4),   # swing
        _make_row(10, stm=0, score16=1, res8=1, flags=0x10),    # tie .5 -> 2
        _make_row(11, stm=1, score16=2, res8=0, flags=0x20),    # tie .5 -> 2
        _make_row(10, stm=1, score16=-44, res8=-1, flags=0x10), # same packed, different stm
        _make_row(12, stm=0, score16=100, res8=1, flags=0x31),  # 3x dup -> clip 192, preserve first flags=0x31
    ])
    s1_edges = np.concatenate([
        _make_row(10, stm=0, score16=2, res8=-1, flags=0x11),   # res_sum=0, flags differs from first
        _make_row(11, stm=1, score16=3, res8=0, flags=0x20),
        _make_row(12, stm=0, score16=140, res8=1, flags=0x30),
        _make_row(13, stm=0, score16=-30001, res8=-1),          # corrupt score < -30000
    ])
    s2_edges = np.concatenate([
        _make_row(12, stm=0, score16=120, res8=-1, flags=0x30), # res_sum = 1+1-1 = 1 -> res8=1
        _make_row(14, stm=0, score16=950, res8=1, flags=0),     # hs800 band1
        _make_row(15, stm=1, score16=-1350, res8=-1, flags=0),  # hs800 band2
    ])

    pool_keys = rng.integers(0, 256, size=(300, 32), dtype=np.uint8)
    shard_paths: list[Path] = []
    extra_blocks = [s0_edges, s1_edges, s2_edges, np.empty(0, dtype=FQS_DTYPE)]
    for si in range(4):
        n = 300
        arr = np.zeros(n, dtype=FQS_DTYPE)
        idx = rng.integers(0, len(pool_keys), size=n)
        arr["packed"] = pool_keys[idx]
        arr["stm"] = rng.integers(0, 2, size=n, dtype=np.uint8)
        arr["score16"] = rng.integers(-1600, 1600, size=n, dtype=np.int16)
        arr["res8"] = rng.choice([-1, 0, 1], size=n).astype(np.int8)
        arr["flags"] = rng.choice([0, 0, 1, 2, 4, 0x10, 0x20], size=n).astype(np.uint8)
        arr["weight_u8"] = 128
        full_arr = np.concatenate([extra_blocks[si], arr]) if len(extra_blocks[si]) else arr
        sp = in_dir / f"shard_{si:02d}.fqs.z"
        fq.write_fqs_atomic(sp, full_arr, level=1)
        shard_paths.append(sp)

    ref_dir = local_tmp / f"ref_{dedup_mode}"
    bkt_dir = local_tmp / f"bkt_{dedup_mode}"

    s_ref = fq.filter_and_dedup(
        shard_paths,
        ref_dir,
        skip_in_check=True,
        skip_noisy=False,
        drop_draw_conflict=600,
        drop_swing=True,
        hs800_p1=65,
        hs800_p2=35,
        dedup_mode=dedup_mode,
        shard_rows=128,
    )
    s_bkt = pfb.partition_and_dedup(
        shard_paths,
        bkt_dir,
        num_buckets=8,
        workers=2,
        skip_in_check=True,
        skip_noisy=False,
        drop_draw_conflict=600,
        drop_swing=True,
        hs800_p1=65,
        hs800_p2=35,
        dedup_mode=dedup_mode,
        shard_rows=64,
        flush_rows_per_bucket=32,
        comp_level=1,
        keep_buckets=False,
    )

    stat_keys = (
        "in_shards",
        "raw_rows",
        "t1_corrupt",
        "t1_in_check",
        "t2_noisy",
        "t2_draw_conflict",
        "t2_swing",
        "t2_hs800",
        "t2_dedup_merged",
        "kept_rows",
    )
    for k in stat_keys:
        assert s_ref[k] == s_bkt[k], f"{dedup_mode} counter mismatch for {k}: ref={s_ref[k]} vs bkt={s_bkt[k]}"

    assert s_bkt["t1_corrupt"] >= 4
    assert s_bkt["t1_in_check"] >= 1
    assert s_bkt["t2_draw_conflict"] >= 1
    assert s_bkt["t2_swing"] >= 1

    m_ref = _load_fqs_map(ref_dir)
    m_bkt = _load_fqs_map(bkt_dir)
    assert m_ref == m_bkt, f"{dedup_mode} map mismatch: len(ref)={len(m_ref)} vs len(bkt)={len(m_bkt)}"

    # Verify zero .part files and no _buckets_tmp leftovers
    assert list(bkt_dir.rglob("*.part")) == []
    assert list(ref_dir.rglob("*.part")) == []
    assert not (bkt_dir / "_buckets_tmp").exists()
    assert (bkt_dir / "summary.json").exists()


def test_vectorized_bucket_ids_uniformity_128_buckets() -> None:
    n_keys = 16384
    num_buckets = 128
    rng = np.random.default_rng(20261128)
    arr = np.zeros(n_keys, dtype=FQS_DTYPE)
    arr["packed"] = rng.integers(0, 256, size=(n_keys, 32), dtype=np.uint8)
    arr["stm"] = rng.integers(0, 2, size=n_keys, dtype=np.uint8)

    bids = pfb._vectorized_bucket_ids(arr, num_buckets)
    assert bids.shape == (n_keys,)
    assert bids.min() >= 0 and bids.max() < num_buckets

    # Identical (packed, stm) keys with different score/res/flags MUST hash identically
    arr_copy = arr.copy()
    arr_copy["score16"] = 123
    arr_copy["res8"] = -1
    arr_copy["flags"] = 7
    assert np.array_equal(bids, pfb._vectorized_bucket_ids(arr_copy, num_buckets))

    counts = np.bincount(bids, minlength=num_buckets)
    mean = n_keys / num_buckets  # 128.0; Poisson std = 11.31
    assert np.all(counts > 0), f"Empty buckets found: min={counts.min()}"
    assert counts.min() >= int(mean * 0.55) and counts.max() <= int(mean * 1.55), (
        f"Bucket spread skewed: min={counts.min()}, max={counts.max()}, mean={mean}"
    )


# ---------------------------------------------------------------------------
# (b) train_v3p_stream.py selftest & AST/source fixes
# ---------------------------------------------------------------------------


def test_train_v3p_stream_selftest_subprocess(local_tmp: Path) -> None:
    r = subprocess.run(
        [sys.executable, "-B", str(TRAIN_STREAM_PATH), "--selftest"],
        env=_sub_env(local_tmp, {"FORGE_LAB_ROOT": str(LAB_ROOT)}),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, f"train_v3p_stream --selftest failed:\n{r.stdout}\n{r.stderr}"
    assert "STREAM_V3P_SELFTEST_PASS:" in r.stdout
    assert "superbatches=2 main_per_sb=32 anc=4 total_per_sb=36" in r.stdout


def test_train_v3p_stream_ast_and_source_fixes() -> None:
    src = TRAIN_STREAM_PATH.read_text(encoding="utf-8")
    assert "compact_records" not in src, "Typo compact_records still present in train_v3p_stream.py"
    assert "FORGE_LAB_ROOT" in src, "FORGE_LAB_ROOT env override missing in train_v3p_stream.py"

    tree = ast.parse(src, filename=str(TRAIN_STREAM_PATH))
    compact_imports = 0
    bad_imports = 0
    uses_env_get_forge_lab_root = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "compact_record":
                    compact_imports += 1
                if alias.name == "compact_records":
                    bad_imports += 1
        elif isinstance(node, ast.ImportFrom):
            if node.module == "compact_record":
                compact_imports += 1
            if node.module == "compact_records":
                bad_imports += 1
        elif isinstance(node, ast.Constant) and node.value == "FORGE_LAB_ROOT":
            uses_env_get_forge_lab_root = True

    assert bad_imports == 0
    assert compact_imports >= 2, f"Expected >=2 `import compact_record` statements, found {compact_imports}"
    assert uses_env_get_forge_lab_root


# ---------------------------------------------------------------------------
# (c) run_post_g3_pipeline.py AST/source checks & make_swa_v3p.py --help
# ---------------------------------------------------------------------------


def test_run_post_g3_pipeline_uses_make_swa_out_dir(local_tmp: Path) -> None:
    src = POST_G3_PATH.read_text(encoding="utf-8")
    assert "--out-pt" not in src, "Stale --out-pt found in run_post_g3_pipeline.py"
    assert "--out-fnn3" not in src, "Stale --out-fnn3 found in run_post_g3_pipeline.py"

    tree = ast.parse(src, filename=str(POST_G3_PATH))
    found_make_swa_call_with_out_dir = False
    for node in ast.walk(tree):
        if isinstance(node, ast.List):
            str_consts = [el.value for el in node.elts if isinstance(el, ast.Constant) and isinstance(el.value, str)]
            if "--out-dir" in str_consts and "--ckpts" in str_consts:
                found_make_swa_call_with_out_dir = True
    assert found_make_swa_call_with_out_dir, "run_post_g3_pipeline.py must invoke make_swa_v3p.py with --ckpts and --out-dir"

    r = subprocess.run(
        [sys.executable, "-B", str(MAKE_SWA_PATH), "--help"],
        env=_sub_env(local_tmp),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, f"make_swa_v3p.py --help failed:\n{r.stderr}"
    assert "--out-dir" in r.stdout
    assert "--ckpts" in r.stdout
    assert "--out-pt" not in r.stdout
    assert "--out-fnn3" not in r.stdout


# ---------------------------------------------------------------------------
# (d) linux_guards.py selftest + unit tests
# ---------------------------------------------------------------------------


def test_linux_guards_selftest_subprocess(local_tmp: Path) -> None:
    r = subprocess.run(
        [sys.executable, "-B", str(LINUX_GUARDS_PATH), "--selftest"],
        env=_sub_env(local_tmp),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, f"linux_guards.py --selftest failed:\n{r.stdout}\n{r.stderr}"
    assert "LINUX_GUARDS_SELFTEST_PASS:" in r.stdout
    assert not list(STREAM_B_DIR.glob("_work_selftest_*"))


def test_linux_guards_ram_parsers_and_room(local_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FORGE_FAKE_FREE_RAM_GB", raising=False)
    sample_avail = "MemTotal:       134217728 kB\nMemFree:        10485760 kB\nMemAvailable:   67108864 kB\n"
    assert abs((lg.parse_meminfo(sample_avail) or 0.0) - 64.0) < 1e-6

    sample_fb = "MemTotal:       16777216 kB\nMemFree:         2097152 kB\nBuffers:         1048576 kB\nCached:          1048576 kB\n"
    assert abs((lg.parse_meminfo(sample_fb) or 0.0) - 4.0) < 1e-6
    assert lg.parse_meminfo("") is None

    mi = local_tmp / "proc_meminfo"
    mi.write_text(sample_avail, encoding="utf-8")
    assert abs((lg.free_ram_gb(mi) or 0.0) - 64.0) < 1e-6

    ok, _ = lg.mem_room_ok(50.0, keep_gb=5.0, meminfo_path=mi)
    low, _ = lg.mem_room_ok(60.0, keep_gb=5.0, meminfo_path=mi)
    assert ok is True
    assert low is False

    live = lg.free_ram_gb()
    assert live is None or live > 0.0

    monkeypatch.setenv("FORGE_FAKE_FREE_RAM_GB", "12.5")
    assert lg.free_ram_gb() == 12.5


def test_linux_guards_gpu_temp_and_guard_classes(local_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NNLOOP_FAKE_GPU_FILE", raising=False)
    monkeypatch.delenv("FORGE_GPU_TEMP_DRY_RUN", raising=False)

    assert lg.gpu_temp_c(dry_run=True) is None
    monkeypatch.setenv("FORGE_GPU_TEMP_DRY_RUN", "1")
    assert lg.gpu_temp_c(dry_run=False) is None
    monkeypatch.delenv("FORGE_GPU_TEMP_DRY_RUN", raising=False)

    assert lg.parse_nvidia_smi_temps("61\n[N/A]\n74.5\n") == 74.5
    assert lg.parse_nvidia_smi_temps("") is None
    assert lg.parse_rocm_smi_temps('{"card0": {"Temperature (Sensor junction) (C)": "91.5", "Temperature (Sensor edge) (C)": 70}}') == 91.5
    assert lg.parse_rocm_smi_temps("GPU[0] : Temperature (Sensor memory) (C): 83.0\n") == 83.0

    # Mocked nvidia-smi subprocess fallback without touching any GPU
    monkeypatch.setattr(lg.shutil, "which", lambda name: "/usr/bin/nvidia-smi" if name == "nvidia-smi" else None)
    monkeypatch.setattr(
        lg.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(a[0], 0, stdout="66\n78.0\n", stderr=""),
    )
    assert lg.gpu_temp_c(dry_run=False) == 78.0

    # NNLOOP_FAKE_GPU_FILE overrides SMI and exercises GpuHeatGuard pause/cool/resume
    fake_gpu = local_tmp / "fake_gpu_c.txt"
    fake_gpu.write_text("99.5\n", encoding="ascii")
    monkeypatch.setenv("NNLOOP_FAKE_GPU_FILE", str(fake_gpu))
    assert lg.gpu_temp_c(dry_run=False) == 99.5

    sleeps = {"count": 0}

    def fake_sleep(_s: float) -> None:
        sleeps["count"] += 1
        fake_gpu.write_text("82.0\n" if sleeps["count"] >= 2 else "95.0\n", encoding="ascii")

    hg = lg.GpuHeatGuard(pause_c=98.0, resume_c=84.0, every_s=0.0, timeout_s=60.0, poll_s=2.0, sleep_fn=fake_sleep)
    hg.tick()
    assert hg.pauses == 1
    assert hg.max_seen == 99.5
    assert hg.paused_s >= 4.0
    assert sleeps["count"] == 2

    # RamGuard: pass, recover, and SystemExit refusal
    rg_pass = lg.RamGuard(floor_gb=2.0, every_s=0.0, timeout_s=0.0, poll_s=0.0, reader=lambda: 8.0)
    rg_pass.tick()
    assert rg_pass.lowest == 8.0

    readings = iter([1.0, 1.2, 3.5])
    rg_recover = lg.RamGuard(
        floor_gb=2.0, every_s=0.0, timeout_s=30.0, poll_s=1.0,
        sleep_fn=lambda _: None, reader=lambda: next(readings),
    )
    rg_recover.tick()
    assert rg_recover.lowest == 1.0

    rg_fail = lg.RamGuard(
        floor_gb=4.0, every_s=0.0, timeout_s=2.0, poll_s=1.0,
        sleep_fn=lambda _: None, reader=lambda: 0.5,
    )
    with pytest.raises(SystemExit):
        rg_fail.tick()


# ---------------------------------------------------------------------------
# (e) Shell scripts LF / Git Bash syntax / CLI flag parity & zero forbidden word
# ---------------------------------------------------------------------------


def test_shell_scripts_lf_syntax_and_cli_flags(local_tmp: Path) -> None:
    bash_exe = _git_bash_exe()
    scripts = {
        "run_datagen_epyc.sh": DATAGEN_V2_PATH,
        "run_dedup_buckets.sh": PARTITION_PATH,
        "run_train_stream_gpu.sh": TRAIN_STREAM_PATH,
    }

    for sh_name, target_py in scripts.items():
        sh_path = STREAM_B_DIR / sh_name
        assert sh_path.exists(), f"Missing {sh_path}"
        raw = sh_path.read_bytes()
        assert b"\r" not in raw, f"CRLF detected in {sh_name}"
        text = raw.decode("utf-8")
        assert text.startswith("#!/usr/bin/env bash\n")
        assert "set -euo pipefail" in text

        r_syn = subprocess.run(
            [bash_exe, "-n", str(sh_path)],
            env=_sub_env(local_tmp),
            capture_output=True,
            text=True,
            timeout=20,
        )
        assert r_syn.returncode == 0, f"bash -n failed for {sh_name}:\n{r_syn.stderr}"

        # Dry-run execution check via Git Bash
        r_dry = subprocess.run(
            [bash_exe, str(sh_path), "--dry-run"],
            env=_sub_env(local_tmp),
            capture_output=True,
            text=True,
            timeout=20,
        )
        assert r_dry.returncode == 0, f"Dry-run failed for {sh_name}:\n{r_dry.stderr}"
        assert target_py.name in r_dry.stdout

        # Cross-check all --flags used inside the .sh against actual argparse flags of target_py
        real_flags = _extract_argparse_flags(target_py)
        used_flags = set(re.findall(r"(?<!\w)(--[a-z][a-z0-9-]+)", text))
        # --dry-run is handled by the shell wrapper itself, not forwarded to Python
        used_flags.discard("--dry-run")
        unknown = sorted(used_flags - real_flags)
        assert not unknown, f"{sh_name} passes unknown CLI flags for {target_py.name}: {unknown}"

    # Specific contract assertions per script
    datagen_txt = (STREAM_B_DIR / "run_datagen_epyc.sh").read_text(encoding="utf-8")
    assert "--startpos-random-plies" not in datagen_txt
    assert "HIP_VISIBLE_DEVICES=\"\"" in datagen_txt

    dedup_txt = (STREAM_B_DIR / "run_dedup_buckets.sh").read_text(encoding="utf-8")
    assert "--buckets 128" in dedup_txt
    assert "--workers 64" in dedup_txt
    assert "--dedup-mode avg" in dedup_txt
    assert "--drop-draw-conflict 600" in dedup_txt
    assert "--shard-rows 500000" in dedup_txt

    train_txt = (STREAM_B_DIR / "run_train_stream_gpu.sh").read_text(encoding="utf-8")
    assert "FORGE_LAB_ROOT" in train_txt
    assert "--shards-per-superbatch" in train_txt
    assert "--distill-net" in train_txt
    assert "G2_v3p_1024_pairwise_psqt/cand.pt" in train_txt
    assert "--save-cycles" in train_txt
    assert "--resume" in train_txt
    for anc in (
        "dead_draws_20k_s5disjoint.fqs.z",
        "won_endings_syzygy_20k.fqs.z",
        "opening_ply012_anchors.fqs.z",
    ):
        assert anc in train_txt, f"Missing anchor {anc} in run_train_stream_gpu.sh"


def test_zero_forbidden_word_across_stream_b_deliverables() -> None:
    forbidden_re = re.compile(r"\b" + "cu" + r"red?\b", re.IGNORECASE)
    checked = 0
    for ext in ("*.py", "*.sh", "*.md"):
        for p in STREAM_B_DIR.rglob(ext):
            checked += 1
            txt = p.read_text(encoding="utf-8")
            m = forbidden_re.search(txt)
            assert m is None, f"Forbidden word {m.group(0)!r} found in {p}"
    assert checked >= 6
