# Phase 2 closeout delta (50-file package at `b5244639`) for Fable's `01:55Z` check

Written by: Neon (`2026-11-24T01:22:00Z`, branch `debate/server-plan-20261123`).
Context: Phase 2 (`21:25Z` – `01:25Z` Nov 24) closes now. `debate/server_day/FINAL_FOR_THE_OWNER.md` (`b7f0018287d4f30a5953e69128e9ab0949631d6d89e0750c1246d074c145e35b`) is intentionally left untouched so Astra's and Neon's 2/2 exact-hash `AGREE` on the 48-file snapshot (`8a7c0eb8`) remains intact while Astra has been silent since `23:00Z`. This note records the exact post-report delta (`8a7c0eb8` -> `b5244639`) and Neon's complete 50/50 exact-hash tally for Fable's `01:55Z` review.

## 1. Signed artifacts standing unchanged at Phase 2 close

| Artifact | SHA-256 | Exact votes |
|---|---|---|
| `debate/server_day/SETUP_PLAN.md` (2.7) | `4100b2a5cdc6d44dab1e38816ad317d23f8dd96618ed1facfd70c6a80c3eb374` | 3/3 `AGREE` (Fable, Astra, Neon) |
| `debate/server_day/FORMATS.md` (2.9) | `ac566296e27b8acfe08e83c3afb27866e2b99f256c878a66c6a96519fed6b8e8` | 3/3 `AGREE` (Fable, Astra, Neon) |
| `debate/engine_plan/ENGINE_PLAN_8H.md` (`dfc0a0c2`) | `f8fb81979f803c587b76a44a2d374f04a37c16797ad8b493a61f8b56d6655867` | 2/2 `AGREE` (Astra, Neon) |
| `debate/server_day/specs/` (all 14 files, sorted set hash) | `430a52d62a9cb0655cdbf4f6b1d8e2bdb9faa12125474a499dfc87ca86fe82c0` | 2/2 `AGREE` (Astra, Neon) |
| `debate/server_day/FINAL_FOR_THE_OWNER.md` (48-file snapshot) | `b7f0018287d4f30a5953e69128e9ab0949631d6d89e0750c1246d074c145e35b` | 2/2 `AGREE` (Astra, Neon) |

## 2. Post-report Opus drops audited on Linux (`8a7c0eb8` -> `b5244639`)

Package manifest at close: `debate/server_day/scripts_v2/MANIFEST.sha256`
- Manifest file SHA-256: `6a0b3c92c873e3441789881257e7088f03ff759313a814411511fd5ea28d65ec`
- Internal manifest digest line: `f884e9cf3cd08dff9dae247a48ecc60164c46fe2eaba8a145d258ecb8f99fcf5`
- File count: **50 files** (`50/50` verified with `sha256sum -c`)

1. **`home/credit.py` + `tests/test_credit.py` (Opus `6500e34a`, added files #49–#50) — Neon `NOT YET`**
   - `home/credit.py`: `85f07d53d10defd69450a2b389ab12a7cb3295b112e1b0cd82004d16a96fa275`
   - `tests/test_credit.py`: `ea2a32a4ae3802ae2c9ac99e52ee097c957d1c86f479e22ea5a462814a02d8e5`
   - Details in `debate/msgs/20261123T231800Z_neon_phase2_credit_audit_and_votes.md`: Linux K1/K5 baseline matched (`7` games, `462` rows); `AGREE` on Opus Q1/Q2/Q5/F1–F4; 6 live-reproduced defects (overlapping `not_done`/`never_dispatched_first` producing false `complete`/`done=-1`/unsorted `not_done`; unvalidated `v["piece"]`/`g["state"]`/missing `rows_digest`; confirmed fork/C1 break yielding silent `WAITS` exit 0; corrupt receipt/verdict JSON crashing exit 1; corrupt `SCHEDULE.1.json.zz` dropped via `Home.ranges()`; `first_index=-2` / empty range ignoring C1 pieces / schema-only DB mutating `meta`).

2. **`home/custody.py` v2 + `tests/test_custody.py` v2 (Opus `4e4cc09c`) — Neon `YES` (awaiting Astra + Fable)**
   - `home/custody.py`: `1079a8a6c268cefa938e62e92e5e156929ddffb540ecb06a5e239d71e7d823f9`
   - `tests/test_custody.py`: `f6b446692515c41ef06c57ba3dd0a189002bb941a86248c12a6c0eb653aa7593`
   - Details in `debate/msgs/20261124T004000Z_neon_phase2_custody_v2_yes_content_v2_not_yet.md`: all prior defects + R-C8 verified fixed live on Linux; 36/36 planted mutations killed uniquely (non-blocking note: `check_records()` scans only `self.h["slots"]`).

3. **`home/content.py` v2 + `tests/test_content.py` v2 (Opus `4e4cc09c`) — Neon `NOT YET`**
   - `home/content.py`: `2cc1fb9f440bebfcd9be37c2ddc7979821ef742124c945ec33dc888c7c4fd7a6`
   - `tests/test_content.py`: `4535c79d086950563c2691a3bfda8ac6ff6d0c93b354b8d2456fd99c6cb739ba`
   - Details in `debate/msgs/20261124T004000Z_neon_phase2_custody_v2_yes_content_v2_not_yet.md`: R-T1..R-T7 verified fixed (including confirming Opus on R-T4 `uci.cpp` `drawcount == 0`, 37/37 plants unique), EXCEPT `check_index()` (`content.py:387`) checks `if run is not None and run[0] != self.fp:` and misses `run is None` when `entries` or `judged` already contains rows (K21b gap -> silently stamps Run B onto a populated no-`meta` Run A `equal.sqlite`).

## 3. Post-report Linux empirical measurements (`231830Z`)

Recorded in `debate/msgs/20261123T231830Z_neon_linux_hardstop_pdeathsig_and_avx512_measurements.md`:
- **4-worker full-CPU `clockwatch` kill latency (real Linux Forge binary):** `20/20` normal hard stops dead before `D` in `1.69–3.23 ms`; `12/12` tightened-`D` stops in `1.70–3.53 ms`; double-loss (`SIGKILL` worker + supervisor) left `12/12` orphans running without `PR_SET_PDEATHSIG` vs `0/12` orphans (`2.76–4.86 ms`) with `PR_SET_PDEATHSIG(SIGKILL)` (with spawning-thread and fork-race notes).
- **4-variant SIMD + compiler benchmark (`gcc 13.3` vs `clang 18.1` x `AVX2` vs `AVX-512`):** `36/36` bit-exact matches against `known/profile.json` (`85ac8e75...`); AVX-512 beats AVX2 by `+9.13%` (GCC) / `+8.22%` (Clang); Clang ThinLTO beats GCC LTO by `+3.48%` / `+2.62%` (noting `--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13` on Ubuntu 24.04).

## 4. Complete Neon exact-hash vote tally across all 50 manifest files (`32 YES`, `18 NOT YET`)

- **7 executable/test files — 3/3 `YES`** (Phase 0: `engine_lines`, `uciproc`, `record`, `budget` + tests).
- **4 executable/service/test files — 2/2 `YES`** (`clockwatch`, `forgeday.service` + tests; awaiting Fable).
- **19 static inputs — 2/2 `YES`** (all 9 `known/*` + all 10 `workloads/*`; Astra + Neon).
- **2 executable/test files — 1/3 `YES`** (`home/custody.py` v2, `tests/test_custody.py` v2; Neon `YES`, awaiting Astra + Fable).
- **4 post-report executable/test files — Neon `NOT YET`** (`home/credit.py`, `tests/test_credit.py`, `home/content.py` v2, `tests/test_content.py` v2; awaiting Astra + Fable and repairs).
- **14 un-repaired v1 executable/test files — 2/2 `NOT YET`** (`guard`, `worker`, `packer`, `terminal`, `bootguard`, `launcher`, `make_control` + tests; Opus announced `guard` v2 and `worker` v2 next).

## 5. Bottom line for the owner

**Wait before renting.** Both plans (`ENGINE_PLAN_8H.md`, `SETUP_PLAN.md` 2.7 / `FORMATS.md` 2.9, all 14 `specs/`) and the owner report (`FINAL_FOR_THE_OWNER.md`) stand agreed. Before paying for a server: finish and re-vote (`3/3 YES`) the remaining 18 `NOT YET` files plus any newly added programs, resolve the Linux normal-format converter and open owner policy choices, and pass the full unpaid end-to-end rehearsal.
