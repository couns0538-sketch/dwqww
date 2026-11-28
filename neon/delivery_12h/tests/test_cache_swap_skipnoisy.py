"""Planted-fault & end-to-end tests on small COPIES for cache_swap_skipnoisy.py.

Strictly operates inside a temporary directory under C:\\nnue-lab\\neon\\forge_fixes\\loop_place\\;
NEVER writes to or modifies C:\\nnue-lab\\runs\\.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
LAB = Path(r"C:\nnue-lab")
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(LAB / "pipeline") not in sys.path:
    sys.path.insert(0, str(LAB / "pipeline"))

import cache_swap_skipnoisy as cs  # noqa: E402
import forge_train as ft  # noqa: E402

SOURCE_PLAIN = LAB / "runs/forge/val/val.plain"
HCE_EXE = str(LAB / "forge/build/hce_dump.exe")


def _extract_n_records(src: Path, dst: Path, n_records: int) -> None:
    """Extract the first n_records complete .plain records (terminated by 'e')."""
    lines_out: list[str] = []
    recs = 0
    with src.open("r", encoding="utf-8") as f:
        for ln in f:
            lines_out.append(ln)
            if ln.strip() == "e":
                recs += 1
                if recs >= n_records:
                    break
    assert recs == n_records, f"Only found {recs} records in {src}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("".join(lines_out), encoding="utf-8", newline="\n")


def _build_fixture_sandbox(tmp_path: Path, n_rounds: int = 3, cap: int = 250) -> tuple[Path, Path, list[Path]]:
    """Create a mini sandbox with n_rounds small copied .plain files + pre-existing cache-n0c1.npz."""
    os.environ["FORGE_PARSE_PROCS"] = "1"
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        f"[train]\nwindow_rounds = 1000\nmax_window_positions = {cap}\n",
        encoding="utf-8",
    )
    rounds_meta = {}
    plains: list[Path] = []
    for idx in range(1, n_rounds + 1):
        p = tmp_path / f"r{idx:04d}/data/filtered.plain"
        _extract_n_records(SOURCE_PLAIN, p, 100)
        # Build genuine pre-existing keep-noisy cache (.cache-n0c1.npz) using forge_train._load_one
        ft._load_one(str(p), HCE_EXE, False, True)
        old_c = Path(str(p) + ".cache-n0c1.npz")
        assert old_c.exists(), f"Failed to seed {old_c}"
        rounds_meta[str(idx)] = {"stages": {"filter": {"out": {"kept": 100, "filtered": str(p)}}}}
        plains.append(p)
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps({"rounds": rounds_meta}, indent=2), encoding="utf-8")
    return cfg_path, state_path, plains


def test_dry_run_makes_zero_changes(tmp_path: Path):
    cfg_p, state_p, plains = _build_fixture_sandbox(tmp_path, n_rounds=3, cap=250)
    # cap=250 with 100 kept/round selects rounds [2, 3] (drops round 1), matching run.py!
    rep = cs.swap_caches(cfg_p, state_p, go_live=False, floor_gb=30.0, hce_exe_override=HCE_EXE, free_gb_fn=lambda _: 40.0)
    assert rep["mode"] == "DRY_RUN"
    assert rep["selected_rounds"] == [2, 3]
    assert rep["stopped_reason"] is None
    assert rep["swapped"] == []
    for p in plains:
        assert not Path(str(p) + ".cache.npz").exists()
        assert Path(str(p) + ".cache-n0c1.npz").exists()


def test_cli_requires_exact_trailing_go_live():
    _, gl1 = cs.parse_cli(["--floor-gb", "30"])
    assert gl1 is False
    with pytest.raises(SystemExit):
        cs.parse_cli(["--floor-gb", "30", "GO"])
    with pytest.raises(SystemExit):
        cs.parse_cli(["GO", "LIVE", "--floor-gb", "30"])
    args4, gl4 = cs.parse_cli(["--floor-gb", "31.5", "GO", "LIVE"])
    assert gl4 is True and args4.floor_gb == 31.5


def test_go_live_swaps_oldest_first_and_verifies_load(tmp_path: Path):
    cfg_p, state_p, plains = _build_fixture_sandbox(tmp_path, n_rounds=3, cap=250)
    stop_p = tmp_path / "STOP"
    stop_p.write_text("stopped\n", encoding="utf-8")
    rep = cs.swap_caches(cfg_p, state_p, go_live=True, floor_gb=30.0, stop_file=stop_p, hce_exe_override=HCE_EXE, free_gb_fn=lambda _: 40.0)
    assert rep["stopped_reason"] is None
    assert [x["round"] for x in rep["swapped"]] == [2, 3]
    # Round 1 was outside cap -> completely untouched
    assert not Path(str(plains[0]) + ".cache.npz").exists()
    assert Path(str(plains[0]) + ".cache-n0c1.npz").exists()
    # Rounds 2 and 3 swapped cleanly: default cache loads, old cache deleted, no swap tmp left
    for p in plains[1:]:
        new_c = Path(str(p) + ".cache.npz")
        old_c = Path(str(p) + ".cache-n0c1.npz")
        tmp_c = Path(str(p) + ".cache.npz.swap.tmp.npz")
        assert new_c.exists() and not old_c.exists() and not tmp_c.exists()
        with np.load(new_c, allow_pickle=False) as z:
            assert int(z["stm"].shape[0]) > 0
            assert str(z["key"]) == cs._expected_default_key(p)


def test_planted_fault_missing_stop_file_refuses_go_live(tmp_path: Path):
    cfg_p, state_p, plains = _build_fixture_sandbox(tmp_path, n_rounds=2, cap=300)
    missing_stop = tmp_path / "STOP_MISSING"
    assert not missing_stop.exists()
    rep = cs.swap_caches(
        cfg_p, state_p, go_live=True, floor_gb=30.0, stop_file=missing_stop,
        hce_exe_override=HCE_EXE, free_gb_fn=lambda _: 40.0,
    )
    assert rep["stopped_reason"] is not None
    assert "stop_file_missing" in rep["stopped_reason"]
    assert rep["swapped"] == []
    for p in plains:
        assert not Path(str(p) + ".cache.npz").exists()
        assert Path(str(p) + ".cache-n0c1.npz").exists()


def test_planted_fault_wrong_row_count_aborts_and_preserves_old_cache(tmp_path: Path):
    cfg_p, state_p, plains = _build_fixture_sandbox(tmp_path, n_rounds=2, cap=300)
    stop_p = tmp_path / "STOP"
    stop_p.write_text("stopped\n", encoding="utf-8")
    # Plant a wrong fresh row count (+7 off)
    rep = cs.swap_caches(
        cfg_p, state_p, go_live=True, floor_gb=30.0, stop_file=stop_p, hce_exe_override=HCE_EXE,
        free_gb_fn=lambda _: 40.0,
        fresh_count_fn=lambda p, h: cs._fresh_skipnoisy_count(p, h) + 7,
    )
    assert rep["stopped_reason"] is not None
    assert "row count mismatch" in rep["stopped_reason"]
    assert rep["swapped"] == []
    # CRITICAL: neither round renamed, temp cleaned, old cache-n0c1.npz 100% preserved!
    for p in plains:
        assert not Path(str(p) + ".cache.npz").exists()
        assert not Path(str(p) + ".cache.npz.swap.tmp.npz").exists()
        assert Path(str(p) + ".cache-n0c1.npz").exists()


def test_planted_fault_low_disk_floor_stops_before_build_and_preserves_old_cache(tmp_path: Path):
    cfg_p, state_p, plains = _build_fixture_sandbox(tmp_path, n_rounds=2, cap=300)
    stop_p = tmp_path / "STOP"
    stop_p.write_text("stopped\n", encoding="utf-8")
    # Plant free space just below the 30.0 GiB floor
    rep = cs.swap_caches(
        cfg_p, state_p, go_live=True, floor_gb=30.0, stop_file=stop_p, hce_exe_override=HCE_EXE,
        free_gb_fn=lambda _: 29.95,
    )
    assert rep["stopped_reason"] is not None
    assert "low_disk" in rep["stopped_reason"]
    assert rep["swapped"] == []
    for p in plains:
        assert not Path(str(p) + ".cache.npz").exists()
        assert Path(str(p) + ".cache-n0c1.npz").exists()


def test_planted_fault_corrupt_temp_cache_aborts_and_preserves_old_cache(tmp_path: Path):
    cfg_p, state_p, plains = _build_fixture_sandbox(tmp_path, n_rounds=2, cap=300)
    stop_p = tmp_path / "STOP"
    stop_p.write_text("stopped\n", encoding="utf-8")

    def _corrupt_temp(swap_tmp: Path) -> None:
        swap_tmp.write_bytes(b"NOT_A_VALID_NPZ_ARCHIVE")

    rep = cs.swap_caches(
        cfg_p, state_p, go_live=True, floor_gb=30.0, stop_file=stop_p, hce_exe_override=HCE_EXE,
        free_gb_fn=lambda _: 40.0,
        post_build_hook=_corrupt_temp,
    )
    assert rep["stopped_reason"] is not None
    assert rep["swapped"] == []
    for p in plains:
        assert not Path(str(p) + ".cache.npz").exists()
        assert not Path(str(p) + ".cache.npz.swap.tmp.npz").exists()
        assert Path(str(p) + ".cache-n0c1.npz").exists()


def test_planted_fault_low_disk_before_second_parse_aborts_and_preserves_old_cache(tmp_path: Path):
    """Positive control for the pre-second-parse peak disk guard (OPUS-2811-SWAP-V2-AND-FORENSIC-READ).

    First free_gb_fn call returns 40.0 GiB (clears the pre-build check so swap_tmp is built).
    Second free_gb_fn call returns strictly above the 30.0 GiB floor (30.0 + 0.5 * tmp_gb,
    mirroring 30.5 GiB against a 0.81 GiB real cache), yet below 30.0 + tmp_gb once slice files
    would coexist with swap_tmp. Must abort BEFORE calling fresh_count_fn, delete swap_tmp, and
    preserve old_cache untouched.
    """
    cfg_p, state_p, plains = _build_fixture_sandbox(tmp_path, n_rounds=2, cap=300)
    stop_p = tmp_path / "STOP"
    stop_p.write_text("stopped\n", encoding="utf-8")
    free_calls = {"n": 0}
    second_parse_calls = {"n": 0}

    def _dropping_free_gb(parent: Path) -> float:
        free_calls["n"] += 1
        if free_calls["n"] == 1:
            return 40.0
        swap_tmp = parent / "filtered.plain.cache.npz.swap.tmp.npz"
        assert swap_tmp.exists(), "Expected swap_tmp to exist before second disk check"
        tmp_gb = swap_tmp.stat().st_size / float(1 << 30)
        assert tmp_gb > 0.0
        # Strictly above 30.0 GiB floor, yet reserving tmp_gb for second-parse slices drops below 30.0 GiB.
        return 30.0 + 0.5 * tmp_gb

    def _counting_fresh(p: Path, h: str) -> int:
        second_parse_calls["n"] += 1
        return cs._fresh_skipnoisy_count(p, h)

    rep = cs.swap_caches(
        cfg_p, state_p, go_live=True, floor_gb=30.0, stop_file=stop_p, hce_exe_override=HCE_EXE,
        free_gb_fn=_dropping_free_gb,
        fresh_count_fn=_counting_fresh,
    )
    assert free_calls["n"] == 2
    assert second_parse_calls["n"] == 0, "Guard must stop BEFORE the second parse runs"
    assert rep["stopped_reason"] is not None
    assert "low_disk_before_second_parse" in rep["stopped_reason"]
    assert rep["swapped"] == []
    for p in plains:
        assert not Path(str(p) + ".cache.npz").exists()
        assert not Path(str(p) + ".cache.npz.swap.tmp.npz").exists()
        assert Path(str(p) + ".cache-n0c1.npz").exists()
