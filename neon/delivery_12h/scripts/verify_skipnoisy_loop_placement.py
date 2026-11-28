"""Strictly read-only verification for skip-noisy loop placement DRAFT artifacts.

Verifies:
  (a) config_forge_skipnoisy_DRAFT.patch cleanly applies in memory to a copy of
      C:\\nnue-lab\\pipeline\\config.forge.toml and parses valid TOML without `--keep-noisy`
      in `[train] train_cmd` (while preserving `max_window_positions == 388000000`).
  (b) cache_swap_skipnoisy.py imports cleanly and its DRY_RUN selects the exact same rounds
      as C:\\nnue-lab\\pipeline\\run.py:training_window().
  (c) All required source/model/patch/script SHA-256 hashes exist and match.

Zero files are written anywhere during execution.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import sys
import tomllib
from contextlib import redirect_stdout
from pathlib import Path

sys.dont_write_bytecode = True

LAB = Path(r"C:\nnue-lab")
PIPELINE = LAB / "pipeline"
LOOP_PLACE = Path(__file__).resolve().parent
FIX = LOOP_PLACE.parent

CONFIG_TOML = PIPELINE / "config.forge.toml"
STATE_JSON = LAB / "runs" / "forge" / "state.json"
PATCH_PATH = LOOP_PLACE / "config_forge_skipnoisy_DRAFT.patch"

if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))
if str(LOOP_PLACE) not in sys.path:
    sys.path.insert(0, str(LOOP_PLACE))

import cache_swap_skipnoisy as css  # noqa: E402
import run as loop_run  # noqa: E402

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

EXPECTED_SHA256 = {
    "config.forge.toml": (
        CONFIG_TOML,
        "d3c4f4eec16eeda71318476cb4d031c252529f77e491e294ddc49fc79c2fd488",
    ),
    "pipeline/run.py": (
        PIPELINE / "run.py",
        "3b992502f0a3e497e0eb4f612effe2d2516d8d10c40e0a68e4a1f4879c78f20b",
    ),
    "pipeline/forge_train_v3.py": (
        PIPELINE / "forge_train_v3.py",
        "62d63f1b72d798634610f8aa8483e7b83c7448328accf55e768c29d0b00fec61",
    ),
    "cache_swap_skipnoisy.py": (
        LOOP_PLACE / "cache_swap_skipnoisy.py",
        "7a19c65efd4b72771495dbcb541ed4be4cd054ef4da86c0110ad075ebaa0ce68",
    ),
    "test_cache_swap_skipnoisy.py": (
        LOOP_PLACE / "test_cache_swap_skipnoisy.py",
        "e082131ae02a4d55ea905ba18ee17910eb65adb535c899300eccc52f10a41b3c",
    ),
    "r0067_cand.fnn3": (
        LAB / "runs/forge/r0067/train/cand.fnn3",
        "737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28",
    ),
    "r0202_cand.fnn3": (
        LAB / "runs/forge/r0202/train/cand.fnn3",
        "42fd34526c3126096b33c34776184246ed0a01bb542febcc6942f584afad5fbd",
    ),
    "R1_skip_cand.fnn3": (
        FIX / "gpu_runs/OPUS_R1_live768_skipnoisy/cand.fnn3",
        "4902fe653e575c0c73ab78aed18fb6d2a10c8f33c895160cb5b68b1bdb9b21ec",
    ),
    "R1_keep_cand.fnn3": (
        FIX / "gpu_runs/OPUS_R1_live768_keepnoisy_twin/cand.fnn3",
        "8b1158aad16d882063da6673efa1584ac0cb4382cb3358964bdb03bb487b02e7",
    ),
    "teachers/b_full.pt": (
        LAB / "runs/forge/teachers/b_full.pt",
        "52be981d04cc92cadbabb12d84b82c19b0ac3299557a9179968dc7d872039430",
    ),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def apply_unified_diff_in_memory(original_text: str, patch_text: str) -> str:
    """Strictly apply a single-file unified diff in memory, checking every context and '-' line."""
    patch_lines = patch_text.splitlines()
    idx = 0
    while idx < len(patch_lines) and not patch_lines[idx].startswith("--- "):
        idx += 1
    if idx + 1 >= len(patch_lines) or not patch_lines[idx + 1].startswith("+++ "):
        raise ValueError("Unified diff missing --- / +++ headers")
    idx += 2

    orig_lines = original_text.splitlines(keepends=True)
    out_lines: list[str] = []
    orig_pos = 0
    hunks_applied = 0

    while idx < len(patch_lines):
        line = patch_lines[idx]
        if line.startswith("#") or line == "":
            idx += 1
            continue
        m = HUNK_RE.match(line)
        if not m:
            raise ValueError(f"Expected @@ hunk header, got: {line!r}")
        old_start = int(m.group(1)) - 1
        old_count = int(m.group(2) or "1")
        new_count = int(m.group(4) or "1")
        idx += 1

        if old_start < orig_pos:
            raise ValueError("Overlapping hunk")
        out_lines.extend(orig_lines[orig_pos:old_start])
        orig_pos = old_start

        seen_old = 0
        seen_new = 0
        while idx < len(patch_lines) and (seen_old < old_count or seen_new < new_count):
            pl = patch_lines[idx]
            if pl.startswith(" "):
                expected = pl[1:]
                actual = orig_lines[orig_pos].rstrip("\r\n")
                if actual != expected:
                    raise ValueError(f"Context mismatch at line {orig_pos + 1}: {actual!r} != {expected!r}")
                out_lines.append(orig_lines[orig_pos])
                orig_pos += 1
                seen_old += 1
                seen_new += 1
            elif pl.startswith("-"):
                expected = pl[1:]
                actual = orig_lines[orig_pos].rstrip("\r\n")
                if actual != expected:
                    raise ValueError(f"Delete mismatch at line {orig_pos + 1}: {actual!r} != {expected!r}")
                orig_pos += 1
                seen_old += 1
            elif pl.startswith("+"):
                eol = "\r\n" if (orig_pos < len(orig_lines) and orig_lines[orig_pos].endswith("\r\n")) else "\n"
                out_lines.append(pl[1:] + eol)
                seen_new += 1
            else:
                raise ValueError(f"Unexpected diff line: {pl!r}")
            idx += 1

        if seen_old != old_count or seen_new != new_count:
            raise ValueError(f"Hunk length mismatch: old={seen_old}/{old_count} new={seen_new}/{new_count}")
        hunks_applied += 1

    if hunks_applied == 0:
        raise ValueError("No hunks found in patch")
    out_lines.extend(orig_lines[orig_pos:])
    return "".join(out_lines)


def verify_all() -> dict:
    # (a) Apply DRAFT patch in-memory and validate TOML
    orig_text = CONFIG_TOML.read_text(encoding="utf-8")
    patch_text = PATCH_PATH.read_text(encoding="utf-8")
    orig_cfg = tomllib.loads(orig_text)
    assert "--keep-noisy" in orig_cfg["train"]["train_cmd"], "Original config.forge.toml missing --keep-noisy"

    patched_text = apply_unified_diff_in_memory(orig_text, patch_text)
    patched_cfg = tomllib.loads(patched_text)
    assert "--keep-noisy" not in patched_cfg["train"]["train_cmd"], "Patched train_cmd still has --keep-noisy!"
    assert patched_cfg["train"]["max_window_positions"] == 388_000_000
    assert orig_cfg["train"]["env"] == patched_cfg["train"]["env"]

    # (b) Import cache_swap_skipnoisy cleanly and verify DRY_RUN == run.py:training_window()
    state_d = json.loads(STATE_JSON.read_text(encoding="utf-8"))
    nums = [int(k) for k in (state_d.get("rounds") or {}).keys() if str(k).isdigit()]
    target_round = max(nums)
    per_round, dropped, kept_total = loop_run.training_window(
        state_d,
        target_round,
        int(orig_cfg["train"]["window_rounds"]),
        int(orig_cfg["train"]["max_window_positions"]),
    )
    expected_rounds = [rr for rr, _, _ in per_round]

    buf = io.StringIO()
    with redirect_stdout(buf):
        rep = css.swap_caches(CONFIG_TOML, STATE_JSON, go_live=False)
    assert rep["mode"] == "DRY_RUN"
    assert rep["stopped_reason"] is None
    assert rep["selected_rounds"] == expected_rounds, f"{rep['selected_rounds']} != {expected_rounds}"
    assert rep["swapped"] == []

    # (c) Verify all required SHA-256 hashes exist and match
    verified_hashes: dict[str, str] = {}
    for label, (path, expected_sha) in EXPECTED_SHA256.items():
        assert path.is_file(), f"Missing required artifact: {path}"
        actual = sha256_file(path)
        assert actual == expected_sha, f"SHA-256 mismatch for {label}: {actual} != {expected_sha}"
        verified_hashes[label] = actual

    return {
        "status": "PASS",
        "patch_applies_in_memory": True,
        "patched_toml_valid": True,
        "keep_noisy_removed_from_train_cmd": True,
        "max_window_positions": patched_cfg["train"]["max_window_positions"],
        "target_round": target_round,
        "selected_rounds_count": len(expected_rounds),
        "selected_rounds_range": f"r{expected_rounds[0]:04d}..r{expected_rounds[-1]:04d}",
        "kept_recorded_total": kept_total,
        "dropped_rounds_count": len(dropped),
        "verified_hashes_count": len(verified_hashes),
    }


def main() -> int:
    res = verify_all()
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
