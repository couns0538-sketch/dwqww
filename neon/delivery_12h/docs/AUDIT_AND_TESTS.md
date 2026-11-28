# Stream B Milestone 1 Audit & CPU Verification Report (`train_v3p.py`, `forge_v3p.py`, Syzygy Anchors)

**Date:** `2026-11-28T04:04:30Z` (`2026-11-27 20:04` PC; synced to live `751`-line `train_v3p.py`)  
**Deliverable Root:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\`  
**Audited Target Versions (Read-Only):**
- `C:\nnue-lab\neon\forge_fixes\train_v3p.py`: `751` lines, `36,262` B, mtime `2026-11-28T03:18:14Z` (`2026-11-27 19:18:14` PC), sha256 prefix `5c7878178aa1cb08` (prior audited snapshots: `18:57:55` `648` lines / `29,994` B / `b959ad2e287d4cdf`, `18:18:45` `589` lines / `26,353` B / `36c82263...`)
- `C:\nnue-lab\neon\forge_fixes\forge_v3p.py`: `199` lines, `9,090` B, mtime `2026-11-27 18:18:46`, sha256 prefix `0fb9726170c4d948`
- `C:\nnue-lab\neon\forge_fixes\make_dead_draw_shard.py`: `113` lines, `4,363` B, mtime `2026-11-27 19:00:35`, sha256 prefix `85cd7eb7c44c94d9`
- `C:\nnue-lab\neon\forge_fixes\anchors\dead_draws_20k.fqs.z`: `125,399` B, mtime `2026-11-27 19:00:46`, sha256 prefix `a75a72de6169894d`
- `C:\nnue-lab\neon\forge_fixes\anchors\won_endings_syzygy_20k.fqs.z`: `154,309` B, mtime `2026-11-27 18:44:57`, sha256 prefix `c2f51696b886c6ca`

---

## 1. `train_v3p.py` Delta Audit (`18:18:45` -> `18:54:51` -> `18:57:55` -> `2026-11-28T03:18:14Z`)

### 1.1 Evolution Across Snapshots
1. **`18:18:45` (`589` lines, `26,353` B, sha256 `36c82263...`) -> `18:54:51` (`644` lines):**
   - Added `.fqs`/`.fqs.z` shard loading and anchor mixing (`--fqs-shards`, `--fqs-repeat`, `--skip-fqs-noisy`, `--anchor-shards`, `--anchor-repeat`, `load_fqs_numpy()`).
   - Replaced `torch.cat` loading with zero-VRAM-spike single GPU preallocation, eliminating the `~11.7 GiB` concatenation spike.
   - Added exact-WDL anchor `teacher_p` assignment inside `if t_path is not None:`.
   - Added `--lr-cycles auto` (`{0.15, 0.30, 0.60, 1.00} * epochs`) and atomic per-epoch checkpointing (`--save-ckpt-every`, `--resume`, `tmp_resume_ckpt.pt` -> `os.replace` to `resume_ckpt.pt`).
2. **`18:54:51` (`644` lines) -> `18:57:55` (`648` lines, `29,994` B, sha256 `b959ad2e287d4cdf`):**
   - Added `--loss-pow` (`type=float, default=2.0`, help `"WDL error exponent (2.0=MSE, 2.5/2.6=Bullet/Stockfish)"`).
   - Replaced fixed `.pow(2).mean()` with `loss_pow == 2.0` vs `.abs().clamp(min=1e-7).pow(args.loss_pow)` (`L661-664` in live `751`-line file).
   - `args.loss_pow` is automatically persisted in `metrics["args"]` (`L729`).
3. **`18:57:55` (`648` lines) -> `2026-11-28T03:18:14Z` (`751` lines, `36,262` B, sha256 `5c7878178aa1cb08...`):**
   - **Py2 FIXED (`L358-363`):** Early `--lr-cycles` parsing/validation before data load; rejects `""`, `"0"`, negative, duplicate, or non-increasing cycles with `SystemExit("Invalid --lr-cycles=...")`.
   - **Py3 FIXED (`L323, 610-615, 693-694, 701-702`):** Persists `"cfg": {"hidden", "batch_size", "pairwise", "has_psqt"}` in `resume_ckpt.pt` and validates on `--resume` (`SystemExit("Resume checkpoint mismatch: ...")` on `hidden`/`batch_size`/arch mismatch); adds `--save-cycles` (`cand_e{ep}.pt` at LR cycle boundaries).
   - **Py5 FIXED (`L312-314, 408, 436, 657-659` + `--use-shard-weights`):** Merged §2 exact-WDL anchor override for `--distill-net ""` (`L657-659`), separated `--skip-fqs-noisy` (bit 0) from `--keep-fqs-check` / `--keep-fqs-in-check` (bit 1), and added `--max-rows`, `--score-weight-mode`, `--ob-reweight`, and `--use-shard-weights`.

### 1.2 Full `Py1..Py13` Audit Table (`train_v3p.py` `751` lines & `forge_v3p.py` `199` lines)

| ID | Status (`18:57:55`) | Status (`03:18:14Z`) | Exact Location | Verified Findings & Residual Gaps |
|---|---|---|---|---|
| **Py1** | FIXED | **FIXED** | `train_v3p.py:169-182` | `ob_smooth_penalty()` guards `out_buckets < 2` (returns `w2.new_zeros(())`), divides only by `ob_pairs = float(self.out_buckets - 1)` (NOT `H` or `KB*768`), and sums `w2`, `b2`, and `psqt_w + psqt_fac.unsqueeze(0)`. Verified algebraically & via CPU autograd (`test_ob_smooth.py`). |
| **Py2** | PARTIAL | **FIXED** | `train_v3p.py:356-367` | `--epochs >= 1`, `--hidden` bounds, and `--lr-cycles` are all validated early before data load (`L356-367`). `--lr-cycles ""`, `"0"`, and `"2,1"` now raise `SystemExit("Invalid --lr-cycles=...")` (`L363`), verified in `test_resume_parity.py`. |
| **Py3** | PARTIAL | **FIXED** | `train_v3p.py:210-222, 323, 608-622, 693-706` | `resume_ckpt.pt` saves `"cfg": {"hidden", "batch_size", "pairwise", "has_psqt"}` (`L701-702`) and validates it on `--resume` (`L610-615`, raising `SystemExit("Resume checkpoint mismatch: ...")` on `hidden` or `batch_size` mismatch, verified in `test_resume_parity.py`); `--save-cycles` added (`L323, 693-694`). Minor non-blocking items: absent `resume_ckpt.pt` starts from epoch `0`, `guard`/`t_train` start fresh on resume, and no `--init-model`/standalone `export`. |
| **Py4** | OPEN | **OPEN** | `train_v3p.py:387-390` | Unconditionally calls `torch.load(t_path, ...)` before checking `t_path.suffix`, crashing on `.inc` residual teachers. |
| **Py5** | PARTIAL | **FIXED** | `train_v3p.py:312-314, 393-427, 432-523, 553-555, 657-659` | **Fixed in `03:18:14Z`:** (1) `--distill-net ""` exact-WDL anchor override merged at `L657-659` (see §2); (2) separated `--skip-fqs-noisy` (bit `1`) and `--keep-fqs-check`/`--keep-fqs-in-check` (bit `2`) at `L312-314, 408, 436`; (3) `weight_u8` used via `--use-shard-weights` (`L322, 478-479, 508-509, 564-565`). Remaining minor item: per-row `stm`/`res8`/piece-code/`<=32`-pieces domain validation on load. |
| **Py6** | OPEN | **OPEN** | `train_v3p.py:228, 266-273, 719-725` | Unused `import chess` (`L228`); `verify_int_parity` (`L719`) not asserted (`<= 1 cp`) and hardcodes `val.plain`; `score_plain_eval` (`L266-273, 722-725`) lacks `.exists()` guards. |
| **Py7** | OPEN | **OPEN** | `train_v3p.py:89-92` | `SparseRowsRaw.forward` lacks `idx.dtype == int16`, `idx.is_contiguous()`, `table.dtype == float32`, `table.shape[0] <= 32767` assertions (enforced in `CpuSparseRowsRaw`). |
| **Py8** | CLEAN | **CLEAN** | `train_v3p.py:137-207, 661-664` | Quantization, STE, `project()`, `to_file_net_p()`, and `--loss-pow` (`clamp(min=1e-7)`) are sound. |
| **Py9** | PARTIAL | **PARTIAL** | `forge_v3p.py:56-75` | `check_bounds()` validates `kb`, `ob`, `eval_scale`, and casts to `int64` before `np.abs`; `king_map` (`len==64, <kb`) and `output_map` (`len==33, <ob`) range checks remain open. |
| **Py10** | OPEN | **OPEN** | `forge_v3p.py:107-133` | `read_net()` lacks `len >= 192+8`, unknown flags, `reserved == 0`, map bounds, and `FLAG_RESIDUAL` attribute on `NetP`. |
| **Py11** | OPEN | **OPEN** | `forge_v3p.py:167, 181` | `selftest()` writes `_tmp_test_v3*.fnn3` directly in `C:\nnue-lab\neon\forge_fixes\`. |
| **Py12** | OPEN | **OPEN (minor)** | `train_v3p.py:603` | Passes `fused=True` to `torch.optim.Adam` unconditionally (works on CPU in both `venv` and `venv101`, unlike `forge_train.py:768-773` fallback guard). |
| **Py13** | OPEN | **OPEN (minor)** | `train_v3p.py:354-355` | Missing-input `SystemExit` message omits `--anchor-shards` even though `L354` accepts it. |

---

## 2. `--distill-net ""` Anchor Exact-WDL Fix (Merged into Live `train_v3p.py:657-659`)

- **Historical Root Cause (`648`-line snapshot & `batch_kernel_c.py:88-94`):**
  - Previously, exact-WDL anchor `teacher_p` assignment sat solely inside `if t_path is not None:`. When `--distill-net ""` (`t_path is None`), `bc.make_batch_c` (`batch_kernel_c.py:88-94`) computed `target = blend * sigmoid(score16 * K / 400) + (1 - blend) * 0.5 * (res8 + 1)`, yielding `0.575 != 1.0` on an anchor row with `(score16=0, res8=+1)` at `mix=0.85` (raw pre-override `make_batch_c` behavior still verified in `test_anchor_wdl.py`).
- **Merged Live Fix (`train_v3p.py:657-659` in `751`-line `03:18:14Z`):**
  ```python
  if t_path is None and n_before_anchors < d["n"]:
      anc_wdl = 0.5 * (d["res8"][idx.long()].float() + 1.0)
      target = torch.where(idx >= n_before_anchors, anc_wdl, target)
  ```
  Verified both in `test_anchor_wdl.py` (unit/spy proof) and live `train_v3p.py` in `test_g3_flags.py`:
  1. `res8=0 -> 0.5`, `res8=+1 -> 1.0`, `res8=-1 -> 0.0` regardless of `score16` (`0`, `+300`, `+1200`, `-1200`).
  2. Non-anchor rows (`idx < n_before_anchors`) retain `mix * sigmoid(score16 * K / 400) + (1 - mix) * 0.5 * (res8 + 1)`.
  3. Distilled runs (`t_path is not None`) are 100% unaltered.

---

## 3. Syzygy 3-4-5 Anchor Audit & `dead_draws_20k_clean.fqs.z`

- **Timeline of `anchors\dead_draws_20k.fqs.z`:**
  1. Prior to `2026-11-28T03:00:35Z`, `make_dead_draw_shard.py` (`4,025` B) lacked `is_stalemate()` and `tb.get_wdl(b) != 0`, which caused Survey 2's `row 8563` mate-in-1 (`8/8/8/8/8/6KN/8/3N3k w - - 0 1`, `tb.get_wdl == +2`, `d1f2#`) and `3` stalemates.
  2. At `2026-11-28T03:00:35Z–03:00:46Z`, `make_dead_draw_shard.py` (`4,363` B) was updated and `dead_draws_20k.fqs.z` (`125,399` B) regenerated. Full 20,000-row validation against `C:\nnue-lab\tablebases\syzygy345` confirms `0` WDL/check/stalemate/checkmate/legality errors (`20,000/20,000` `wdl == 0`).
  3. **Remaining defects in `anchors\dead_draws_20k.fqs.z`:** `303` duplicate FENs (`unique_fens = 19,697`, from sampling with replacement), non-atomic file writes, and sparse `meta.json`.
  4. **Important `python-chess` note:** `b.is_game_over()` returns `True` for all `12,000` insufficient-material rows (`K-K`, `KN-K`, `KB-K`), so validators must check `not b.is_checkmate()`, `not b.is_stalemate()`, `any(b.generate_legal_moves())`, and `not b.is_game_over()` when `not b.is_insufficient_material()`.
- **`anchors\won_endings_syzygy_20k.fqs.z` (`154,309` B):**
  - Full 20,000-row validation passes with `0` WDL/check/stalemate/checkmate/legality errors (`20,000/20,000` `tb.get_wdl(b) == ±2`, `insuff_mat = 0`, `game_over = 0`, `stm = {0: 10041, 1: 9959}`, `res8 = {-1: 9365, 1: 10635}`, `34` duplicate FENs).
- **Clean Replacement (`make_dead_draw_shard_v2.py` -> `dead_draws_20k_clean.fqs.z` + `dead_draws_20k_clean_meta.json`):**
  - Enforces pawn-rank guard, `b.is_valid()`, `not b.is_check()`, `not b.is_stalemate()`, `not b.is_checkmate()`, `any(b.generate_legal_moves())`, `(b.is_insufficient_material() or not b.is_game_over())`, `tb.get_wdl(b) == 0`, strict `(pk.tobytes(), stm)` deduplication (`0` duplicates), balanced `stm` (`10,000` White / `10,000` Black), `--include-5pc` (default `True`: `19,000` 2–4pc FIDE draws + `1,000` 5-piece Syzygy `wdl == 0` draws across `KBB-KB`, `KNN-KN`, `KBN-KN`, `KBN-KB` x `250`), atomic `.part -> os.replace`, and SHA-256 metadata (`127,484` B, `sha256: f2073b88b95d109c5b130fce503f8f9126baf852c47db4af4e31f9c5e0976716`).

---

## 4. `ob_smooth_penalty()` Math (`train_v3p.py:169-182`)

- Guard: `if self.out_buckets < 2: return w2.new_zeros(())`.
- Formula: $\text{pen} = \frac{1}{\text{OB}-1}\left(\|w_2[1:]-w_2[:-1]\|_F^2 + \|b_2[1:]-b_2[:-1]\|_2^2 + \|(p_w + p_{\text{fac}})[:,:,1:] - (p_w + p_{\text{fac}})[:,:,:-1]\|_F^2\right)$.
- For a single adjacent-bucket jump $\Delta$ at `OB = 8` (`ob_pairs = 7`), $|\nabla(\lambda \cdot \text{pen})| = \frac{2\lambda \Delta}{7}$, strictly independent of `hidden` (`H=64` vs `1024` verified identical) and `king_buckets`.
- At $\Delta = 0.25$: `lam = 1e-4` -> `7.1429e-6` (`714x` Adam `eps = 1e-8`); `lam = 2e-6` -> `1.4286e-7` (`14.3x` Adam `eps = 1e-8`).
- Verified in `test_ob_smooth.py`: `psqt_w` + `psqt_fac` exact cancellation, `out_buckets = 1` exact zero gradient contribution, and real CPU MSE + `ob_smooth` comparison across all `8` buckets (`< 5%` of dense-bucket MSE `b2` grad at `1e-4`, `< 0.1%` at `2e-6`, while actively regularizing unvisited `psqt` coordinates where `grad_mse == 0.0`).

---

## 5. Deliverables & CPU Verification Results (Raw Output)

### 5.1 Deliverable Files (all under `C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\`)
- `AUDIT_AND_TESTS.md` (this report)
- `make_dead_draw_shard_v2.py`
- `dead_draws_20k_clean.fqs.z` (`127,484` B)
- `dead_draws_20k_clean_meta.json`
- `tests\_cpu_harness.py` (Note: both `venv` and `venv101` report `torch.cuda.is_available() == True` under Windows ROCm even with blanked `HIP/CUDA/ROCR_VISIBLE_DEVICES`, so `_cpu_harness.py` patches `torch.device("cuda" -> "cpu")` via a `type`-compatible proxy metaclass, `torch.cuda.empty_cache`, `SparseRowsRaw`, `bc.make_batch_c`, `fk.SparseRowsAct`, `subprocess.run`, `score_plain_eval`, and asserts `.device.type == "cpu"` on all tensors.)
- `tests\test_resume_parity.py`
- `tests\test_anchor_wdl.py`
- `tests\test_ob_smooth.py`
- `tests\test_anchors_syzygy.py`

### 5.2 Clean Shard Generation Command & Raw Output
```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
C:\nnue-lab\venv\Scripts\python.exe -B C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\make_dead_draw_shard_v2.py
```
```text
DEAD_DRAWS_CLEAN_DONE: {"path": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave2\\streamB_nnue\\dead_draws_20k_clean.fqs.z", "positions": 20000, "unique_positions": 20000, "duplicates": 0, "bytes": 127484, "kb": 124.5, "raw_bytes": 760008, "sha256": "f2073b88b95d109c5b130fce503f8f9126baf852c47db4af4e31f9c5e0976716", "raw_sha256": "3b28094c972e300dde5da4642512c41193a10f6cd222163d5a6ed9f0e2a6519a", "seed": 20261127, "include_5pc": true, "tb_dir": "C:\\nnue-lab\\tablebases\\syzygy345", "syzygy_verified": true, "spec_counts": {"K-K": 2000, "KN-K": 2350, "K-KN": 2350, "KB-K": 2350, "K-KB": 2350, "KNN-K": 2800, "K-KNN": 2800, "KN-KN": 1000, "KB-KN": 500, "KB-KB_ocb": 500, "KBB-KB": 250, "KNN-KN": 250, "KBN-KN": 250, "KBN-KB": 250}, "stm_counts": {"0": 10000, "1": 10000}, "ob_counts": {"0": 20000}, "created_utc": "2026-11-28T03:08:20Z"}
```

### 5.3 Full CPU Test Suite — `pytest` (`venv101`, PyTorch `2.14.0+rocm10.1.0`, post-fix `751`-line `train_v3p.py`)
```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
C:\nnue-lab\venv\Scripts\python.exe -B C:\nnue-lab\tmp\fable_scratch\tools\mem_room.py 2
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_resume_parity.py C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_anchor_wdl.py C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_ob_smooth.py C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_anchors_syzygy.py
```
```text
mem_room: GO: commit limit 68.5 GiB, committed 45.9, room 22.6; physical free 15.8 of 31.6; need 2.0, keep 5.0
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0 -- C:\nnue-lab\venv101\Scripts\python.exe
rootdir: C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests
plugins: typeguard-4.6.0
collecting ... collected 14 items

..\..\..\..\..\..\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_resume_parity.py::TestResumeParity::test_continuous_2ep_vs_1ep_plus_resume PASSED [  7%]
..\..\..\..\..\..\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_resume_parity.py::TestResumeParity::test_midrun_crash_4ep_auto_cycles_with_v3p_distill_and_anchors PASSED [ 14%]
..\..\..\..\..\..\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_resume_parity.py::TestResumeParity::test_resume_edge_cases_and_documented_gaps PASSED [ 21%]
..\..\..\..\..\..\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_anchor_wdl.py::TestAnchorWdl::test_distilled_run_anchor_exact_wdl_teacher_p PASSED [ 28%]
..\..\..\..\..\..\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_anchor_wdl.py::TestAnchorWdl::test_minimal_branchless_fix_exact_wdl_and_nonanchor_preservation PASSED [ 35%]
..\..\..\..\..\..\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_anchor_wdl.py::TestAnchorWdl::test_undistilled_unmodified_bug_yields_0575_for_zero_score_win_anchor PASSED [ 42%]
..\..\..\..\..\..\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_ob_smooth.py::TestObSmooth::test_analytical_gradient_h_invariance_and_psqt_cancellation PASSED [ 50%]
..\..\..\..\..\..\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_ob_smooth.py::TestObSmooth::test_out_buckets_one_zero_guard PASSED [ 57%]
..\..\..\..\..\..\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_ob_smooth.py::TestObSmooth::test_real_cpu_mse_vs_ob_smooth_across_all_8_buckets PASSED [ 64%]
..\..\..\..\..\..\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_ob_smooth.py::TestObSmooth::test_shapes_and_variants PASSED [ 71%]
..\..\..\..\..\..\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_anchors_syzygy.py::TestAnchorsSyzygy::test_dead_draws_20k_clean PASSED [ 78%]
..\..\..\..\..\..\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_anchors_syzygy.py::TestAnchorsSyzygy::test_dead_draws_20k_live PASSED [ 85%]
..\..\..\..\..\..\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_anchors_syzygy.py::TestAnchorsSyzygy::test_validator_catches_mate_in_1_and_stalemate PASSED [ 92%]
..\..\..\..\..\..\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_anchors_syzygy.py::TestAnchorsSyzygy::test_won_endings_20k_live PASSED [100%]

============================= 14 passed in 11.05s =============================
```

### 5.4 Full CPU Test Suite — `unittest` (`venv`, PyTorch `2.9.1+rocmsdk20260116`, post-fix `751`-line `train_v3p.py`)
```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
C:\nnue-lab\venv\Scripts\python.exe -B -m unittest discover -s C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests -p "test_*.py" -v
```
```text
Failed to get device count
test_distilled_run_anchor_exact_wdl_teacher_p (test_anchor_wdl.TestAnchorWdl.test_distilled_run_anchor_exact_wdl_teacher_p) ... ok
test_minimal_branchless_fix_exact_wdl_and_nonanchor_preservation (test_anchor_wdl.TestAnchorWdl.test_minimal_branchless_fix_exact_wdl_and_nonanchor_preservation) ... ok
test_undistilled_unmodified_bug_yields_0575_for_zero_score_win_anchor (test_anchor_wdl.TestAnchorWdl.test_undistilled_unmodified_bug_yields_0575_for_zero_score_win_anchor)
Verify raw pre-override `make_batch_c` output (0.575) before live `train_v3p.py:657-659` exact-WDL `torch.where`. ... ok
test_dead_draws_20k_clean (test_anchors_syzygy.TestAnchorsSyzygy.test_dead_draws_20k_clean) ... CLEAN_DEAD_DRAWS_STATS: {'positions': 20000, 'unique_fens': 20000, 'dup_count': 0, 'insuff_mat': 11473, 'game_over': 11473, 'stm_counts': {0: 10000, 1: 10000}, 'res8_counts': {0: 20000}}
ok
test_dead_draws_20k_live (test_anchors_syzygy.TestAnchorsSyzygy.test_dead_draws_20k_live) ... LIVE_DEAD_DRAWS_STATS: {'positions': 20000, 'unique_fens': 19697, 'dup_count': 303, 'insuff_mat': 12000, 'game_over': 12000, 'stm_counts': {0: 10020, 1: 9980}, 'res8_counts': {0: 20000}}
ok
test_validator_catches_mate_in_1_and_stalemate (test_anchors_syzygy.TestAnchorsSyzygy.test_validator_catches_mate_in_1_and_stalemate) ... ok
test_won_endings_20k_live (test_anchors_syzygy.TestAnchorsSyzygy.test_won_endings_20k_live) ... LIVE_WON_ENDINGS_STATS: {'positions': 20000, 'unique_fens': 19966, 'dup_count': 34, 'insuff_mat': 0, 'game_over': 0, 'stm_counts': {0: 10041, 1: 9959}, 'res8_counts': {-1: 9365, 1: 10635}}
ok
test_analytical_gradient_h_invariance_and_psqt_cancellation (test_ob_smooth.TestObSmooth.test_analytical_gradient_h_invariance_and_psqt_cancellation) ... ok
test_out_buckets_one_zero_guard (test_ob_smooth.TestObSmooth.test_out_buckets_one_zero_guard) ... ok
test_real_cpu_mse_vs_ob_smooth_across_all_8_buckets (test_ob_smooth.TestObSmooth.test_real_cpu_mse_vs_ob_smooth_across_all_8_buckets) ... ok
test_shapes_and_variants (test_ob_smooth.TestObSmooth.test_shapes_and_variants) ... ok
test_continuous_2ep_vs_1ep_plus_resume (test_resume_parity.TestResumeParity.test_continuous_2ep_vs_1ep_plus_resume) ... ok
test_midrun_crash_4ep_auto_cycles_with_v3p_distill_and_anchors (test_resume_parity.TestResumeParity.test_midrun_crash_4ep_auto_cycles_with_v3p_distill_and_anchors) ... ok
test_resume_edge_cases_and_documented_gaps (test_resume_parity.TestResumeParity.test_resume_edge_cases_and_documented_gaps) ... ok

----------------------------------------------------------------------
Ran 14 tests in 9.440s

OK
```

### 5.5 M2 G3 Flag Suite (`test_g3_flags.py`) & Patch Check (`venv101`, post-fix `751`-line `train_v3p.py`)
```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
C:\nnue-lab\venv101\Scripts\python.exe -B C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamB_nnue\tests\test_g3_flags.py
```
```text
=== TEST 1: gen_cc0_selfgame_fqs_v2 protocol, parity, 4 flags, atomicity, meta.json ===
[PASS] Test 1: rows=56, flags=(q=16, n=32, chk=16, n&chk=8), drops=(16,16,8), book_parity=[1, 2, 1, 2, 1, 2], start_parity=[0, 1]
...
[PASS] live_g3a_default: seen score16 tags=[101, 102, 201, 202], loss=0.049733, sha=dd5a6ebb3c39
...
[PASS] Test 3a (--distill-net ''): all 8/8 anchors immune to noisy+check filter & forced to exact WDL 0.0/0.5/1.0
...
[PASS] Test 3b (--distill-net <v3p.pt>): distilled data + exact-WDL anchor mix verified within 1e-6

ALL M2 G3 FLAG TESTS PASSED (3/3)
```
(`train_v3p_g3_flags.patch` also passed `git apply --check` with `rc=0` against a temp copy of the `751`-line `train_v3p.py`.)
