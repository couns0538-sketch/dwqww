# HANDOFF - fast npt data loader (R14-B item 1), for Engine NNUE / QA

State: **CPU-verified, UNPROVEN on the GPU** (the GPU window in GPU_REQUEST.md was not granted: the npt queue holds the
GPU until 2026-11-08). Nothing here is a strength claim; switching is Engine NNUE's decision. Off by default.

## What it is
`--fast-loader` makes the npt trainer (`F:\opus_scratch\r6\nnue-pytorch-amd`, b2614500 + patches) read its binpack with
`forge_fastloader.dll` (own code, C++20, MinGW g++ 15.2) instead of the default loader DLL. It produces **the same
batches, byte for byte, as the default loader with `--num-workers 1`** (same skip filter, same random numbers, same
window shuffles, same SparseBatch layout), but filters the ~90 % skipped records from three stem fields without
decoding a board and builds features in parallel. Evidence and numbers: RESULTS.md; design: LOADER_SPEC.md.

| file | sha256 | where |
|---|---|---|
| `forge_fastloader.dll` (candidate b5) | `9eb29b7d134a73eb58d47b2ced38587ed450ffaf11fdfcb108898652cefcd935` | `D:\o14b\fl\b5_install\`; rebuild: `fastloader/build_fastloader.sh` (pc1 = pc2 byte-identical) |
| `forge_fastloader.py` (Dataset wrapper) | `39af47b0f347963c9f3ad470c7a90c2652b4ae361f18b71adfeeb3cbdf3a9605` | `fastloader/` on this branch, copy in `D:\o14b\fl\b5_install\` |
| trainer switch | - | `patches/0005-fast-loader-switch.patch` = what `tools/install_fast_loader.py` applies |

The DLL is built with `-march=znver5` for this PC's CPU (Ryzen 7 9850X3D); it imports only Windows DLLs (KERNEL32 +
the UCRT API sets). On another CPU, rebuild with that CPU's `-march` and re-run the equality checks before use.

## Verified on the CPU (details in RESULTS.md)
- Batches identical to the default loader's `--num-workers 1` stream: 1,000 / 1,000 training batches + the validation
  batches, a 24-configuration matrix, 3,100 batches past a file wrap, and every tensor on the trainer's own Dataset path.
- One epoch of CPU training (L1 256, 16 batches, seeded before the model is built, 1 thread, deterministic
  algorithms): the printed losses of old and fast are identical in all 5 values.
- Speed (loader only, palindromic ABBA, 10 pairs, CPUs 2-3, BelowNormal): per-arm medians 468,494 vs 4,035,567 kept positions / s;
  median of the 10 pair ratios **8.65x** (mean 8.64, 95% CI 8.58-8.69); a full 152.5M-position epoch through the fast loader alone: 29.8 s, peak 166 MB.
- ASan + UBSan and TSan self-tests in GitHub CI: PASS.

## Not verified (needs the GPU window)
GPU utilisation and it/s of a real epoch, and the adapter path below (the adapter starts a GPU run).

## Adopting it in the queue (Engine NNUE decides; never edit the live trainer folder in place)
1. Make a trainer copy (e.g. `robocopy F:\opus_scratch\r6\nnue-pytorch-amd <COPY> /E` from cmd / PowerShell; from
   Git Bash prefix `MSYS_NO_PATHCONV=1`, else Git Bash turns `/E` into `E:/` and robocopy copies nothing, exit 16)
   and check it against the installer's base: `cd <COPY> && sha256sum -c <branch>/opus_r14b/item1/trainer_manifest_b2614500.sha256` (264 files,
   all OK = the trainer version the installer's anchors were written for). `D:\o14b\npt` is such a copy, already
   switched - but the loader files next to its train.py are the superseded **b4** (12:43, DLL a4f965aa...): use a fresh
   copy (steps 1-3), or give the b5 folder to the acceptance check (3b). Checked 2026-11-02 16:04 and again 20:41
   (adoption rehearsal from a fresh clone): the live tree still matched (264 / 264).
2. Build the DLL from this branch (`bash fastloader/build_fastloader.sh <new dir>`, ~1 minute; prints sha256, which
   must be 9eb29b7d...) or use `D:\o14b\fl\b5_install\forge_fastloader.dll`.
3. `python -I -B tools/install_fast_loader.py <COPY> --check --loader-dll <DLL>`, then the same without `--check`: it
   patches config.py + train.py (exact anchors; refuses a trainer that differs or is already patched, exit 2) and
   copies the DLL and this branch's `fastloader/forge_fastloader.py` next to `<COPY>\train.py` (never over an existing
   file; prints both sha256). (Without `--loader-dll`, copy the two files yourself, or set `FORGE_FAST_LOADER_DIR`; the
   adapter passes the queue's environment through.) Unknown or misspelt arguments are exit 2 (since 22:2x a typo can
   no longer turn `--check` into an install), and a real install into the live folder
   `F:\opus_scratch\r6\nnue-pytorch-amd` is refused; `--check` there is allowed (read-only).
3b. Acceptance check, CPU only, GPU hidden (about 1 minute): `bash tools/fl_acceptance.sh <COPY> <new out dir>` runs
   the trainer's own Dataset -> FixedNumBatchesDataset -> DataLoader path with the old loader (w1; default: the copy's
   own `build\libtraining_data_loader.dll`) and the fast loader (w4; default: the files next to its train.py) and
   compares every tensor of 200 training + 61 validation batches; exit 0 = identical. It prints the fast DLL's sha256
   and a note when that is not b5 (9eb29b7d...); a b4-era forge_fastloader.py stops it with a clear message. Another
   old loader goes in as the 3rd argument (the DLL file itself) and another fast loader as the 4th (the folder that
   holds forge_fastloader.dll + .py); `''` keeps a default, e.g. on `D:\o14b\npt` (b4 files):
   `bash tools/fl_acceptance.sh /d/o14b/npt <out> '' 'D:\o14b\fl\b5_install'` - 2026-11-02 18:46: old 36 s, fast 6 s,
   **261 / 261 batches identical** with b5 (logs/acceptance/: the log names the b5 DLL); again 21:42 into a folder
   whose name has spaces: 261 / 261. On the fresh-copy rehearsal (20:42) the defaults found the installed b5 files.
4. Queue line (adapter `F:\forge_nnue_train\tools\train_resid_nnuepytorch_v2.py`): add `--npt-repo <COPY>` and, as the
   LAST arguments, `--npt-extra --fast-loader` (`--npt-extra` takes the rest of the command line). Everything else
   stays as it is. `--num-workers N` sets the fast loader's feature-builder threads to N - 2 (at least 1; plus one
   reader and one filter thread); the batches are the same at any N (the w1 stream).
   Thread count: the measured layout (reader + filter + 1 builder = `--num-workers 3`) delivered 4,035,567 kept
   positions / s on 2 CPUs at BelowNormal, about 24x what the live line consumes (7.4-10.3 it/s x 16,384 = 121k-169k
   kept positions / s in its epoch logs). So `--num-workers 3` is enough even for a GPU-bound epoch; with the live
   line's `--num-workers 4` (the `_w4_` in its name) the fast loader would run 2 builders, one thread more than needed.
   CPU cost (one logical CPU, live thread setting, 2026-11-02): old 2.45 vs fast 0.34 CPU-us per kept position, i.e.
   feeding the live line takes 0.30-0.41 of a CPU with the default loader and 0.04-0.06 with the fast one. The Idle
   trainer process used 0.4-0.6 cores (21:19-21:22) on CPUs that were 86-90 % busy, mostly with heavier-class work;
   some idle time was left, so it was not purely CPU-bound (RESULTS.md). The GPU window decides.
5. Check the run log's first lines: `Fast loader: ON (<version>, <path>, sha256 9eb29b7d...)`. A trainer without the
   flag prints `Fast loader: off`.
6. Roll back: remove `--npt-extra --fast-loader` (or `--npt-repo`); nothing else changes.

## Scope (fails closed with a clear error outside it)
Unchained binpack records only (the J1 binpacks are unchained, 34 B / record; every chunk of both J1 files holds whole
records - a damaged chunk's partial tail would be skipped, not reported), exactly one file per stream,
`--no-filtered --no-wld-filtered` without simple-eval skipping, loader feature set K32H3 (what the trainer hands the
loader for `--features K32H3^`; the CPU loss match ran train.py with `--features K32H3^`), no DDP (world size 1).
Anything else raises instead of silently differing from the default loader; each refusal and its message is tested by
`tools/test_scope.py` (20 cases, standard library + the DLL, no GPU: bug hunt #7). The equality, distribution and
speed tools refuse wrong arguments, damaged or empty dumps and existing outputs before any work, and their compare
commands never pass two empty or junk files: `tools/test_cli.py` (34 cases, no DLL loaded: bug hunt #16). Damaged files (bug hunt #4, 371 fuzz
runs incl. a bounds-checked build): clean errors, no crash, no hang. One shared limit: a cyclic stream over a file in
which the skip filter keeps nothing (e.g. every score VALUE_NONE) waits forever - the default loader does the same.

## What changes for training
The live line runs the default loader with `--num-workers 4`: several decode workers, each with its own adaptive
filter state, mixed by thread timing (not reproducible run to run). The fast loader gives the deterministic
`--num-workers 1` stream: same filter rules, a different sample of the same data. Loss values of a fast-loader epoch
are therefore comparable to the live epochs only as a sanity check, not bit for bit. Measured (RESULTS.md,
2026-11-02 18:25): over 32.8M positions each, old loader w4 vs fast loader differ by less than 0.001 total-variation
distance in piece count, side to move, outcome, queen bucket and score histograms (mean score -1.17 SE).

## Optional trainer fix found on the way
`train.py` builds the model before `torch.manual_seed`, and torch 2.11.0+rocm7.13.0 seeds from the clock per process:
the same `--seed` does not give the same initial weights. `patches/0006-seed-before-model-OPTIONAL.patch` fixes that
(not needed for the loader; Engine NNUE decides).
