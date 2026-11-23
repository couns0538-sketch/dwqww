# Neon Server-Plan Memory (2026-11-23 — Branch `debate/server-plan-20261123`)

## 0. ACTIVE OWNER ORDER (`debate/server_day/START_HERE.md` & `20261123T193346Z`)
- **Branch:** `debate/server-plan-20261123` (plain push, never forced; fallback branch `debate/server-plan-20261123-neon` if push refused). Only files under `debate/`; NEVER touch `source/`; nothing personal (public repo).
- **Stop time:** **`18:35Z`** UTC (do not stop earlier; update memory every ~10 minutes; at `18:35Z` deliver final plain-words summary to owner).
- **Single focus:** **`debate/server_day/SETUP_PLAN.md`** + line-by-line review and explicit **`YES <sha256>`** from all 3 seats (`astra`, `neon`, `fable`) for every script under `debate/server_day/scripts/` (or `NOT YET` with line + failing test; any changed byte invalidates all 3 approvals). Nothing else opened.

## 1. Current Server-Plan State (`2026-11-23T13:15Z`, ~5h 20m remaining until `18:35Z`)
- **`SETUP_PLAN.md` v2 (`d81a3165`, Fable `200551Z`):**
  - **Already SETTLED:** `D2`, `D4`, `D12`, plus first sentence of `D3` (joint record Astra `130332Z` + Neon `130210Z`).
  - **Neon v2 votes posted (`131430Z`):** `AGREE` on **Section 2, Section 4, and `D1, D3, D5, D6, D7, D8, D9, D10, D11, D13, D14, D15`** (withdrew `C4_1 / t_1` on `D3` after proving the 9% single-round drain-latency bias; added `D6` `python3 -I -B` + `chmod -R a-w`, `D14` `slot_meta.json`, and `D15` non-systemd check notes). Ready to form joint records with Astra as soon as Astra confirms v2 text + `D13` terminal inventory / `D14` chain schemas.
  - **Section 7 (45 merged failure rows):** Proposed concrete planted tests for all six `-` rows (**9, 23, 35, 40, 41, 45**) plus tightenings for **5, 11, 14, 16, 26, 27, 32, 33, 34** (`131430Z`).
- **Complete line-by-line audit of all 17 scripts in `debate/server_day/scripts/` posted (`131400Z`):**
  - Verified `MANIFEST.sha256` (`35` files, member digest `9705a787bf51...`, manifest SHA-256 `c8a30ad9095f...`) using `python3 -I -B`.
  - **Live Linux proofs executed on Ubuntu 24.04 (`g++ 13.3.0`, `Python 3.12.3`):**
    - `linux/build_forge.sh` (`avx2_pext`, `LTO=full`, `PLANT=none`) ran end-to-end against `loop/source` (`SOURCE.sha256` EQUAL) and matched Windows `known/profile.json`, `verify.json`, `startup.json`, and `n12_batch.json` bit-for-bit! `PLANT=other_source` WAS caught by GCC 13.3 `-Werror=coverage-mismatch` (`rc=1`).
    - `tests/test_worker.py`: `93/94` passed (only T8 failed loudly due to no `python-chess`); `tests/mutants.py`: control + `6/6` mutants caught (`rc=0`).
    - Reproduced bugs live: `cpu_check.sh` line 25 (`rc=1` silent on missing `flags`), `build_forge.sh` unquoted `$extra` on `$WORK` with space + `CXX=clang++` failure + `LTO=none` default + Step 7 skipping `n12_batch.uci` + `python3` without `-I -B`, `uciproc.py` line 66 & `drive.py` line 66 infinite-hang on 20 ms spam (`4.04s`/`2.55s` under `0.3s` limit; confirms Astra), `record.py` `bind()` omitting `opening` on `openingend` + unvalidated `gid` format, `packer.py` 0-byte `.sha256` `IndexError` `rc=1` (+ Astra's `rebuild()` dropped fifth-field `result` & `.packed`/`PIECES.txt` crash gap & `D2` removal mode), `receiver.py` unvalidated `gid[-8:]` `ValueError` + zero-row `gid` re-credit + `A26`/uncompressed/missing-fsync (+ Astra's re-ACK without `state/raw` & same-key overwrite & non-terminal `nomoves`), `to_round.py` step-1 loop & missing `sha256(raw)` re-check & partial `out/` dir, `check_run.py` unanchored `ERROR` false positive + bare `sgerror` miss, `hash_tree.py` dangling symlink ignored + duplicate `subs`, `make_workloads.py` missing arg check & `games <= 0`, and test files needing `D2`/regression updates.
  - Answered Fable `scripts/README.md` #3 (piece chain YES), #4 (single stop + ordered drain), #5 (Linux dir `fsync` YES + Windows `os.replace` retry), #7 (`uciproc.py` pipes drain stderr, line 66 breaks deadline).
  - **Verdict tally at `13:15Z`:** `0` scripts `YES`, `17/17` scripts `NOT YET` with exact hashes, line numbers, and reproducible failing cases.
- **Next actions:**
  1. Commit and push `131400Z`, `131430Z`, and memory update to `debate/server-plan-20261123`.
  2. Monitor branch for Astra's `D13` terminal inventory / `D14` chain specs, Astra's Linux build/worker audit, Fable's `SETUP_PLAN.md` v3, Opus's measurements (`M1`–`M3`, `M5`–`M8`) & upcoming scripts (budget tool, three-YES ledger tool, home guard, revised scripts).
  3. Co-sign joint settlement records with Astra as decisions stabilize, audit every new/revised script line-by-line with live Linux execution, and keep memory updated every ~10 min until `18:35Z`.

## 2. Verified Technical Baseline (Carried From First Debate & Server-Plan Proofs)
- **Toolchain on this Ubuntu 24.04 host:** `g++ 13.3.0`, `clang++ 18.1.3` (missing `libstdc++` match/no `llvm-profdata`), `Python 3.12.3` (no `zstd`, no `python-chess`).
- **Codec benchmarks on `60` real `r67` games (`7,512` rows, `/tmp/server_day_bench/r67_60g.txt`):**
  - Game records (`6.64 B/row` raw): `lzma-6` -> `2.13 B/row`, `1.73M` rows/s (`0.015` cores @ `26.5k/s`); `zlib-6` -> `2.45 B/row`, `2.55M` rows/s.
  - Raw `sg` fallback (`66.56 B/row`): `lzma-6` -> `11.94 B/row`, `82.9k` rows/s (`0.320` cores); `zlib-6` -> `15.55 B/row`, `480.2k` rows/s.
  - **Peak RSS at 10 MB payload (`19.05 MiB` base):** `zlib-6` = `+0.32 MiB`, `lzma-1` = `+8.52 MiB`, `lzma-6` = `+90.26 MiB` (`109.31 MiB`) -> compression stays inside the single packer process, never per worker.
- **Compiler findings:** GCC PGO without `-flto` regressed `-9.5%` to `-20.0%` vs `-O3`; GCC PGO+LTO recovered `+4.6%` to `+7.5%`; `loop/build_recipe/pgo_selfgame.py` lines 69–71 bug confirmed on PC by Fable (`200551Z`).
- **First-debate plan count (`debate/FINAL_PLAN.md`):** `10` changes (`A16, A17, N17, A18, A20, A22, A23, N23, A24, A26`) + `8` for later (`A19, N18..N22, A21, A25`) + owner's server-day direction. `source/` 100% untouched.
