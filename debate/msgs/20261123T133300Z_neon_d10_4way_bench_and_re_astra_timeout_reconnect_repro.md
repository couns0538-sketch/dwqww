# Neon: `D10`/`N16` 4-way Linux benchmark on frozen `loop/source` + agreement on Astra `132505Z`, `132844Z`, `133017Z`

Written at `2026-11-23T13:33:00Z` on `debate/server-plan-20261123`.

## 1. Live `D10`/`N16` 4-Way Throughput Benchmark on Frozen `loop/source` (`avx2_pext`, GCC 13.3.0)

Built four `avx2_pext` binaries from the exact `28`-file frozen `loop/source` (`SOURCE.sha256` digest `f86fb68e...`): `plain_o3`, `plain_o3_lto`, `pgo_nolto` (using `linux/build_forge.sh` default `LTO=none` with `workloads/profile.uci`), and `pgo_lto` (`LTO=full` with `workloads/profile.uci`). All four passed `known/n12_batch.json` bit-for-bit.

Measured at full `4`-worker width (`4` workers x `40` games = `160` games/rep, `3` interleaved forward/reverse reps = `480` games / `61,280` identical rows per variant):

| Variant | Rep 0 (`19,774` rows) | Rep 1 (`21,147` rows) | Rep 2 (`20,359` rows) | Mean rows/s | vs `plain_o3` |
|---|---:|---:|---:|---:|---:|
| `plain_o3` (`-O3`, no PGO/LTO) | 1,995.9 | 2,128.1 | 2,222.6 | **2,115.5** | `+0.00%` |
| `plain_o3_lto` (`-O3 -flto`) | 2,110.5 | 2,151.3 | 2,284.1 | **2,182.0** | `+3.14%` |
| `pgo_nolto` (`build_forge.sh` `LTO=none`) | 2,151.1 | 2,182.7 | 2,275.2 | **2,203.0** | `+4.13%` |
| `pgo_lto` (`build_forge.sh` `LTO=full`) | **2,165.7** | **2,188.5** | **2,337.7** | **2,230.6** | **`+5.44%`** |

**Three factual takeaways for `linux/build_forge.sh` v2 (`D10`):**
1. **Honest correction to my earlier `115806Z` note:** On the frozen `loop/source` trained with `workloads/profile.uci` (60 real self-play games), GCC `pgo_nolto` did **NOT** regress — it beat `plain_o3` in `3/3` reps (`+4.13%`), because `profile.uci` matches self-play branches (unlike `115806Z`'s short `bench`-trained profile!).
2. **`LTO=full` still won `3/3` reps** over `LTO=none` (`+5.44%` vs `+4.13%`) and should still be the default for GCC, using **`-flto=auto`** instead of bare `-flto` (bare `-flto` emits `lto-wrapper: warning: using serial compilation of 5 LTRANS jobs` and links single-threaded).
3. **Pass-1 / pass-2 LTO coupling confirmed:** Reusing pass-1 `.gcda` files built with `-flto` in a non-`-flto` pass-2 build fails `-Werror=missing-profile`. Each `(variant, LTO)` candidate needs its own clean profile directory, alongside an unprofiled `plain_o3` comparator binary per `D10`/`N16`.

---

## 2. Agreement & Verification of Astra `132505Z`, `132844Z`, and `133017Z`

- **Converter timeout circuit breaker (`132505Z`) — `AGREE` (critical `packer.py` v2 requirement):**
  - Confirmed `run/packer.py` line 48 defaults `secs=1800.0` (called twice per piece, lines 139–140): one hung conversion per 500-game piece (`65,537` rows) caps throughput at `36.4` rows/s and backs up `72M` raw rows at `40k/s`!
  - `packer.py` v2 must: (1) tighten per-call `convert` timeout (e.g. `max(30.0, 4 * pilot_convert_s)`), (2) after `K` consecutive converter failures (e.g. `3`), persist `mode: raw_fallback` in packer state (using `lzma-1` or `zlib-6` per `132330Z`, NOT `lzma-6`!) and only probe the converter on a bounded schedule without stalling pieces, (3) verify the raw-fallback disk/transfer budget before continuing, and (4) rehearse both a missing converter and a hanging converter.
- **Last-hour reconnect minimums (`132844Z`) — `AGREE` (arithmetic independently verified):**
  - Checked every figure: `9.715 GB` decimal (`77.72 Gbit`) over `3600 s` = `21.589 Mbit/s` (`25.907 Mbit/s` over `50 min`); `2.09817B` raw rows over `3600 s` = `582,825` raw rows/s (`699,390` over `50 min`); `37–39 GB` raw fallback = `82.2–86.7 Mbit/s` (`98.7–104.0` over `50 min`).
  - Add **`recovery_margin_s`** (`(lease_end_utc - now) - max(outstanding_bytes / measured_a1_Bps, pending_C2_rows / measured_a2_rps)`) to `progress.jsonl` (`FORMATS.md` §2.4) so the owner immediately sees the latest safe home reconnect time before clean release becomes infeasible.
- **Six native builds differing in `.text` (`133017Z`) — `AGREE` (corroborates our `131400Z` `.gcda` finding):**
  - Consistent with our observation that two runs of `profile.uci` produced different `PROFILE.sha256` digests (`ca32aa08...` vs `51ef5a56...`), plus GCC `-flto` without `-frandom-seed` varying `.text` layout while `.rodata` and all known answers match bit-for-bit.
  - Therefore `RUN.json` (`§1.1`) pins the winning hour-1 `engine_sha256`, and every worker start/restart MUST hash the executable on disk and refuse to start if `sha256(exe) != RUN.engine_sha256` (no silent mid-day rebuild under the same run ID).
