# Neon Server-Plan Memory (2026-11-23 — Branch `debate/server-plan-20261123`)

## 0. ACTIVE OWNER ORDER (`debate/server_day/START_HERE.md` & `20261123T193346Z`)
- **Branch:** `debate/server-plan-20261123` (plain push, never forced; fallback branch `debate/server-plan-20261123-neon` if push refused). Only files under `debate/`; NEVER touch `source/`; nothing personal (public repo).
- **Stop time:** **`18:35Z`** UTC (do not stop earlier; update memory every ~10 minutes; at `18:35Z` deliver final plain-words summary to owner).
- **Single focus:** **`debate/server_day/SETUP_PLAN.md`** + **`debate/server_day/FORMATS.md`** + line-by-line review and explicit **`YES <sha256>`** from all 3 seats (`astra`, `neon`, `fable`) for every script under `debate/server_day/scripts/` (or `NOT YET` with line + failing test; any changed byte invalidates all 3 approvals). Nothing else opened.

## 1. Current Server-Plan State (`2026-11-23T13:33Z`, ~5h 02m remaining until `18:35Z`)
- **`SETUP_PLAN.md` v2.1 (`0151a133`, SHA-256 `69693c6b09b4...`):**
  - **ALL 15 DECISIONS (`D1`–`D15`), SECTION 2, AND SECTION 4 HAVE TWO-SEAT JOINT AGREEMENT** (Astra `132125Z` + Neon `131930Z` + earlier `130332Z`), awaiting Fable's v2.2 settlement mark + spool-sizing update (`158–282 GB` total retained server bytes, not `9.7–16 GB`).
- **`FORMATS.md` v1 (`ce24899cc866...`):** Both Astra (`131547Z`) and Neon (`132000Z`) voted `CHANGE` (agreeing on all 3 architecture choices), awaiting Fable's `FORMATS.md` v2 incorporating: split `completed_zero_rows` vs `opening_ended_nomoves`, non-circular pilot/production schedule, per-slot range endpoints, `<run>-wNNN-gNNNNNNNN`, `bind()` hashing `opening`, `codec` field (`lzma`/`zlib`), `run_fingerprint` on all artifacts, `epoch >= prev.epoch`, `C2` scope (`132008Z`), W5 independent-opening mode (`132138Z`), converter timeout circuit breaker (`132505Z`), `recovery_margin_s` in `progress.jsonl` (`132844Z`), and `engine_sha256` enforcement on every worker restart (`133017Z`).
- **Package 1 Script Audit (`debate/server_day/scripts/`, 17 scripts, `MANIFEST.sha256` digest `9705a787bf51...`):**
  - **`0` effective `YES`**, **`17 / 17` `NOT YET`** from BOTH Neon and Astra (Astra withdrew `hash_tree.py` YES in `131652Z`).
  - Runnable failing suites committed: `debate/server_day/cases/astra/` (`9` cases) + `debate/server_day/cases/neon/` (`10` cases `N1`–`N10`, verified `0 PASS, 10 FAIL` on v1 in `4.4 s`).

## 2. Verified Linux Benchmarks (All Executed Live on Frozen `loop/source` + `loop/forge65_r0067.fnn3`)
- **500-game 4-worker run (`65,537` rows, `29.26 s`, `2,240` r/s, `132330Z`):**
  - **`M7` packer ceiling:** `raw` `lzma-6` = `36,953` r/s (`108%` of 1 core @ `40k/s` — **TOO SLOW!**), `74.88 MiB` RSS; `raw` **`lzma-1`** = `249,027` r/s (`17.60 B/row`, `47.28 MiB`); `raw` **`zlib-6`** = `430,912` r/s (`18.40 B/row`, `47.28 MiB`); `meta` **`lzma-6`** = `424,457` r/s (`2.30 B/row`, `47.28 MiB`); pure Python `parse+faults+meta_of+plain_of` = `924k` r/s.
  - **`M5` scale bytes:** `raw` `75.04 B/row` logical / **`75.37 B/row` allocated** (`158.1 GB` @ `2B` kept; `249.6 GB` @ `40k/s` for 23 h); `meta.xz` `2.30 B/row` (`4.29 B/row` w/ binpack -> `9.00 GB` @ `2B` kept); `plain` `94.78 B/row`.
  - **Whole-group memory:** `peak_group_PSS = 168.76 MiB` (`42.19 MiB/worker`) vs summed RSS `217.86 MiB` (`54.47 MiB/worker`, `+29%` overcount).
  - **Zero-row & duplicates:** `5/500 (1.00%)` zero-row `sgend matescore` at ply 8 (legal moves left!); `0/495 (0.00%)` duplicates; `plies` med `126`/max `300`, `nodes` med `468k`/max `1.25M` (`2.67x`).
- **`D10`/`N16` 4-way interleaved benchmark on frozen `loop/source` (`avx2_pext`, GCC 13.3.0, `480` games / `61,280` rows each, `133300Z`):**
  - `plain_o3`: `2,115.5` r/s (`+0.00%`); `plain_o3_lto`: `2,182.0` r/s (`+3.14%`); `pgo_nolto` (`profile.uci`): `2,203.0` r/s (`+4.13%`, fixed `115806Z`'s `bench`-profile regression!); `pgo_lto` (`LTO=full`): **`2,230.6` r/s (`+5.44%`, won 3/3 reps)**; use `-flto=auto` instead of serial `-flto`.
- **Complete `info string` + `sgerror` inventory (`132330Z`):** Audited all `loop/source/src/{uci,search}.cpp` emissions; found 4 more refusal forms (`search.cpp:3417` `V3 VERIFY FAILED`, `uci.cpp:797/897/933`) and proposed normal whitelist + fail-closed default.

## 3. Next Actions
1. Commit & push `133300Z` + memory update.
2. Wait/poll cleanly for Fable's next drop (`SETUP_PLAN.md` v2.2, `FORMATS.md` v2, Opus's measurements `M1`–`M3`/`M5`–`M8`, Opus's budget/ledger/home-guard tools, and v2 scripts for three-YES read).
3. Audit every v2 script line-by-line + run `cases/neon/run_all.py` & live Linux suites to issue `YES <sha256>` (or `NOT YET`) until `18:35Z`.
