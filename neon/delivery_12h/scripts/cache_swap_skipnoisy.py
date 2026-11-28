"""DRAFT ONLY: One-time cache swap for switching live Forge training from --keep-noisy to skip-noisy.

Per OPUS-2811-CACHE-SWAP-DRAFT-REQUEST (2026-11-28 08:00 PC):
  - DRAFT in C:\\nnue-lab\\neon\\forge_fixes\\loop_place\\; NEVER run on C:\\nnue-lab\\runs\\ until reviewed
    line-by-line by Opus and second-read by Fable.
  - Dry-run by default. Acts ONLY when the final two CLI arguments are literally: GO LIVE
  - Selects window rounds using pipeline/run.py's own training_window() function (zero copied logic).
  - Processes rounds OLDEST FIRST:
      1. Checks free space on the target drive before each round; stops if building this round's
         cache could drop free space below --floor-gb (default 30.0 GiB).
      2. Builds filtered.plain.cache.npz using pipeline/forge_train.py's own _load_one() function
         (zero copied parsing/serialization code), intercepting its final atomic replace so the
         built artifact stays under a temporary name (.swap.tmp.npz) until verified by reload and
         a second parse.
      3. Verifies the temporary cache loads cleanly with np.load(allow_pickle=False), matches the
         exact expected size:mtime:11:v1 key and required arrays, and matches a second-parse row
         count from forge_parse.parse_file() (proving the written cache file is whole, not the filter).
      4. Atomically renames .swap.tmp.npz -> filtered.plain.cache.npz, and ONLY THEN deletes
         that round's filtered.plain.cache-n0c1.npz.
      5. Refuses GO LIVE unless stop_file (default C:\\nnue-lab\\pipeline\\STOP) exists, so a running
         loop trainer can never lose a cache underneath it.
      6. Emits one concise log line per round.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import sys
import tomllib
from pathlib import Path
from typing import Callable

import numpy as np

LAB = Path(r"C:\nnue-lab")
PIPELINE = LAB / "pipeline"
if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))

import forge_parse  # noqa: E402
import forge_train as ft  # noqa: E402
import run as loop_run  # noqa: E402

REQUIRED_CACHE_KEYS = ("key", "codes", "stm", "score", "res", "hce")
PLAIN_FALLBACK_MULT = 1.50  # fallback peak multiplier if old_cache is absent (temp cache + parse slices)
DEFAULT_STOP_FILE = LAB / "pipeline/STOP"


def _free_gb(path: Path) -> float:
    return shutil.disk_usage(str(path)).free / float(1 << 30)


def _fresh_skipnoisy_count(plain_path: Path, hce_exe: str) -> int:
    """Second parse with forge_parse.parse_file(skip_noisy=True, skip_check=True).

    Uses the same parser as _load_one, so matching this count proves the written cache file is
    whole and uncorrupted (not an independent validation of the filter logic itself).
    """
    procs = int(os.environ.get("FORGE_PARSE_PROCS", "0") or 0) or min(8, os.cpu_count() or 1)
    parsed = forge_parse.parse_file(str(plain_path), hce_exe, True, True, procs)
    return int(parsed["stm"].shape[0])


def _expected_default_key(plain_path: Path) -> str:
    st = os.stat(plain_path)
    return f"{st.st_size}:{int(st.st_mtime)}:11:v1"


def _verify_cache_file(cache_path: Path, expected_key: str, fresh_count: int) -> int:
    """Load cache_path cleanly, verify key/arrays/shapes, and verify row count == fresh_count."""
    if not cache_path.exists():
        raise RuntimeError(f"temp cache missing: {cache_path}")
    with np.load(cache_path, allow_pickle=False) as z:
        for k in REQUIRED_CACHE_KEYS:
            if k not in z.files:
                raise RuntimeError(f"missing key '{k}' in {cache_path}")
        got_key = str(z["key"])
        if got_key != expected_key:
            raise RuntimeError(f"cache key mismatch: got {got_key!r}, expected {expected_key!r}")
        n = int(z["stm"].shape[0])
        if n <= 0:
            raise RuntimeError(f"empty cache (n={n}) in {cache_path}")
        for k in ("codes", "score", "res", "hce"):
            if int(z[k].shape[0]) != n:
                raise RuntimeError(f"array length mismatch for '{k}': {z[k].shape[0]} != {n}")
        # Force actual decompression/read of boundary slices to prove the archive is intact.
        _ = (int(z["stm"][0]), int(z["stm"][-1]), float(z["score"][0]), float(z["score"][-1]))
    if n != fresh_count:
        raise RuntimeError(f"row count mismatch: cache={n} != fresh={fresh_count}")
    return n


@contextlib.contextmanager
def _capture_load_one_to_temp(target_cache: Path, swap_tmp: Path):
    """Redirect forge_train._load_one's final os.replace(tmp, cache) so output lands at swap_tmp."""
    orig_replace = ft.os.replace

    def _guarded_replace(src, dst):
        if Path(dst).resolve() == target_cache.resolve():
            return orig_replace(src, swap_tmp)
        return orig_replace(src, dst)

    ft.os.replace = _guarded_replace
    try:
        yield
    finally:
        ft.os.replace = orig_replace


def select_window_rounds(
    state_d: dict,
    cfg: dict,
    target_round: int | None = None,
) -> tuple[list[tuple[int, int, str]], list[int], int]:
    """Select the training window using pipeline/run.py's exact training_window()."""
    rounds = state_d.get("rounds") or {}
    if target_round is None:
        nums = [int(k) for k in rounds.keys() if str(k).isdigit()]
        if not nums:
            raise RuntimeError("state.json has no rounds")
        target_round = max(nums)
    t = cfg.get("train") or {}
    window = int(t.get("window_rounds", 1000))
    cap = int(t.get("max_window_positions", 0) or 0)
    return loop_run.training_window(state_d, target_round, window, cap)


def swap_caches(
    config_path: Path,
    state_path: Path,
    go_live: bool = False,
    floor_gb: float = 30.0,
    stop_file: Path = DEFAULT_STOP_FILE,
    target_round: int | None = None,
    hce_exe_override: str | None = None,
    free_gb_fn: Callable[[Path], float] = _free_gb,
    fresh_count_fn: Callable[[Path, str], int] = _fresh_skipnoisy_count,
    post_build_hook: Callable[[Path], None] | None = None,
) -> dict:
    """Execute dry-run or GO LIVE oldest-first cache swap across the selected training window."""
    cfg = tomllib.loads(config_path.read_text(encoding="utf-8"))
    state_d = json.loads(state_path.read_text(encoding="utf-8"))
    hce_exe = hce_exe_override or str(LAB / "forge/build/hce_dump.exe")

    per_round, dropped, kept_total = select_window_rounds(state_d, cfg, target_round=target_round)
    # per_round is already ordered oldest -> newest by training_window().
    mode = "GO_LIVE" if go_live else "DRY_RUN"
    rng = f"r{per_round[0][0]:04d}..r{per_round[-1][0]:04d}" if per_round else "EMPTY"
    print(
        f"CACHE_SWAP mode={mode} rounds={len(per_round)} range={rng} "
        f"kept_recorded={kept_total} dropped={len(dropped)} floor_gb={floor_gb:.2f} stop_file={stop_file}",
        flush=True,
    )

    report = {
        "mode": mode,
        "floor_gb": floor_gb,
        "stop_file": str(stop_file),
        "selected_rounds": [rr for rr, _, _ in per_round],
        "swapped": [],
        "already_clean": [],
        "skipped_missing_plain": [],
        "stopped_reason": None,
    }

    if go_live and not stop_file.exists():
        msg = f"stop_file_missing: {stop_file} (loop must be stopped before GO LIVE)"
        print(f"REFUSE_GO_LIVE {msg}", flush=True)
        report["stopped_reason"] = msg
        return report

    for rr, recorded_kept, filtered_str in per_round:
        plain = Path(filtered_str)
        if not plain.exists():
            print(f"r{rr:04d} SKIP_MISSING_PLAIN path={plain}", flush=True)
            report["skipped_missing_plain"].append(rr)
            continue

        default_cache = Path(str(plain) + ".cache.npz")
        old_cache = Path(str(plain) + ".cache-n0c1.npz")
        swap_tmp = Path(str(plain) + ".cache.npz.swap.tmp.npz")
        expected_key = _expected_default_key(plain)

        plain_gb = plain.stat().st_size / float(1 << 30)
        old_gb = (old_cache.stat().st_size / float(1 << 30)) if old_cache.exists() else 0.0
        # Peak coexistence: swap_tmp (~0.81 GiB) + second-parse slice files beside plain (~0.81 GiB)
        # <= 2.0 * old_gb (old keep-noisy cache ~0.995 GiB > new skip-noisy cache ~0.81 GiB).
        est_need_gb = max(2.0 * old_gb, plain_gb * PLAIN_FALLBACK_MULT) if old_gb == 0.0 else (2.0 * old_gb)
        cur_free_gb = free_gb_fn(plain.parent)

        # Already swapped & valid?
        default_valid = False
        if default_cache.exists():
            try:
                with np.load(default_cache, allow_pickle=False) as z:
                    default_valid = (str(z["key"]) == expected_key and int(z["stm"].shape[0]) > 0)
            except Exception:
                default_valid = False

        if default_valid and not old_cache.exists():
            print(f"r{rr:04d} ALREADY_CLEAN default_cache={default_cache.name} free_gb={cur_free_gb:.2f}", flush=True)
            report["already_clean"].append(rr)
            continue

        if default_valid:
            est_need_gb = 0.0
        if cur_free_gb - est_need_gb < floor_gb:
            msg = f"low_disk free_gb={cur_free_gb:.2f} est_need_gb={est_need_gb:.2f} floor_gb={floor_gb:.2f}"
            print(f"r{rr:04d} STOP_LOW_DISK {msg}", flush=True)
            report["stopped_reason"] = f"r{rr:04d}: {msg}"
            return report

        if not go_live:
            action = "WOULD_DELETE_OLD_ONLY" if default_valid else "WOULD_BUILD_VERIFY_SWAP"
            print(
                f"r{rr:04d} DRY_RUN {action} plain_gb={plain_gb:.3f} old_gb={old_gb:.3f} "
                f"est_need_gb={est_need_gb:.3f} free_gb={cur_free_gb:.2f}",
                flush=True,
            )
            continue

        # GO LIVE execution for this single round:
        try:
            if not default_valid:
                if swap_tmp.exists():
                    swap_tmp.unlink()
                # Remove stale unreadable default_cache only if it was corrupt, never touch old_cache yet!
                if default_cache.exists():
                    default_cache.unlink()
                with _capture_load_one_to_temp(default_cache, swap_tmp):
                    ft._load_one(str(plain), hce_exe, True, True)
                if post_build_hook is not None:
                    post_build_hook(swap_tmp)
                # Re-check free space right before the second parse (swap_tmp + parse slices coexist).
                tmp_gb = (swap_tmp.stat().st_size / float(1 << 30)) if swap_tmp.exists() else est_need_gb
                pre_parse_free_gb = free_gb_fn(plain.parent)
                if pre_parse_free_gb - tmp_gb < floor_gb:
                    raise RuntimeError(
                        f"low_disk_before_second_parse free_gb={pre_parse_free_gb:.2f} "
                        f"slice_est_gb={tmp_gb:.2f} floor_gb={floor_gb:.2f}"
                    )
                fresh_n = fresh_count_fn(plain, hce_exe)
                verified_n = _verify_cache_file(swap_tmp, expected_key, fresh_n)
                os.replace(swap_tmp, default_cache)
            else:
                # Re-check free space before the second parse for an existing default_cache too.
                def_gb = default_cache.stat().st_size / float(1 << 30)
                pre_parse_free_gb = free_gb_fn(plain.parent)
                if pre_parse_free_gb - def_gb < floor_gb:
                    raise RuntimeError(
                        f"low_disk_before_second_parse free_gb={pre_parse_free_gb:.2f} "
                        f"slice_est_gb={def_gb:.2f} floor_gb={floor_gb:.2f}"
                    )
                fresh_n = fresh_count_fn(plain, hce_exe)
                verified_n = _verify_cache_file(default_cache, expected_key, fresh_n)

            deleted_old = False
            if old_cache.exists():
                old_cache.unlink()
                deleted_old = True
            after_free_gb = free_gb_fn(plain.parent)
            new_gb = default_cache.stat().st_size / float(1 << 30)
            print(
                f"r{rr:04d} SWAP_OK rows={verified_n} new_gb={new_gb:.3f} deleted_old={deleted_old} "
                f"free_gb={after_free_gb:.2f}",
                flush=True,
            )
            report["swapped"].append({"round": rr, "rows": verified_n, "deleted_old": deleted_old})
        except Exception as e:
            if swap_tmp.exists():
                try:
                    swap_tmp.unlink()
                except OSError:
                    pass
            print(f"r{rr:04d} FAIL_VERIFY error={type(e).__name__}: {e} (old_cache preserved={old_cache.exists()})", flush=True)
            report["stopped_reason"] = f"r{rr:04d}: {type(e).__name__}: {e}"
            return report

    return report


def parse_cli(argv: list[str]) -> tuple[argparse.Namespace, bool]:
    go_live = len(argv) >= 2 and argv[-2] == "GO" and argv[-1] == "LIVE"
    clean_argv = argv[:-2] if go_live else list(argv)
    ap = argparse.ArgumentParser(description="Dry-run by default; pass trailing 'GO LIVE' to execute.")
    ap.add_argument("--config", default=str(LAB / "pipeline/config.forge.toml"))
    ap.add_argument("--state", default=str(LAB / "runs/forge/state.json"))
    ap.add_argument("--floor-gb", type=float, default=30.0)
    ap.add_argument("--stop-file", default=str(DEFAULT_STOP_FILE))
    ap.add_argument("--target-round", type=int, default=None)
    ap.add_argument("--hce-exe", default=None)
    args = ap.parse_args(clean_argv)
    return args, go_live


def main(argv: list[str] | None = None) -> int:
    raw = sys.argv[1:] if argv is None else list(argv)
    args, go_live = parse_cli(raw)
    rep = swap_caches(
        config_path=Path(args.config),
        state_path=Path(args.state),
        go_live=go_live,
        floor_gb=args.floor_gb,
        stop_file=Path(args.stop_file),
        target_round=args.target_round,
        hce_exe_override=args.hce_exe,
    )
    return 0 if rep["stopped_reason"] is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
