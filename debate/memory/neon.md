# Neon Server-Plan Memory (2026-11-23 — Branch `debate/server-plan-20261123`)

## 0. ACTIVE OWNER ORDER (`debate/server_day/START_HERE.md` & `20261123T193346Z`)
- **Branch:** `debate/server-plan-20261123` (plain push, never forced; fallback branch `debate/server-plan-20261123-neon` if push refused). Only files under `debate/`; NEVER touch `source/`; nothing personal (public repo).
- **Stop time:** **`18:35Z`** UTC (do not stop earlier; update memory every ~10 minutes; at `18:35Z` deliver final plain-words summary to owner).
- **Single focus:** **`debate/server_day/SETUP_PLAN.md`** + **`debate/server_day/FORMATS.md`** + line-by-line review and explicit **`YES <sha256>`** from all 3 seats (`astra`, `neon`, `fable`) for every script under `debate/server_day/scripts/` (or `NOT YET` with line + failing test; any changed byte invalidates all 3 approvals). Nothing else opened.

## 1. Current Server-Plan State (`2026-11-23T13:24Z`, ~5h 11m remaining until `18:35Z`)
- **`SETUP_PLAN.md` v2.1 (`0151a133`, SHA-256 `69693c6b09b4...`):**
  - **ALL 15 DECISIONS (`D1`–`D15`), SECTION 2, AND SECTION 4 NOW HAVE TWO-SEAT JOINT AGREEMENT** (Astra `132125Z` + Neon `131930Z` + earlier `130332Z`):
    - Already marked SETTLED: `D2`, `D4`, `D12`, `D3` sentence 1.
    - Jointly agreed on v2.1 ready for Fable to mark SETTLED: `Section 2`, `Section 4` (with total allocated server spool sizing: raw + offers + seals + logs), `D1`, `D3` (K >= 1 whole rounds end-to-end vs stage capacities, lower decides), `D5`, `D6` (latest review per `(path, sha256, seat)` wins; `python3 -I -B` + `chmod -R a-w`), `D7`, `D8`, `D9` (independent per-ID seeded 8-ply draw mode declared for day 1), `D10`, `D11`, `D13` (same-day forecast labeled empirical lower scenario; only durable C4 unconditional), `D14`, `D15`.
- **`FORMATS.md` v1 (`ce24899cc866...`, Fable `201222Z`):**
  - Both Astra (`131547Z`) and Neon (`132000Z`) voted **`CHANGE`** while agreeing on all 3 architectural choices (canonical ASCII JSONL, zero upstream ACKs to server, 1 piece never spans 2 rounds).
  - Key changes pending `FORMATS.md` v2: split `completed_zero_rows` vs `opening_ended_nomoves` (proven critical by 5/500 real Linux games = 1.00% `matescore` at ply 8 with legal moves!), non-circular pilot/production schedule, per-slot range endpoints, `<run>-wNNN-gNNNNNNNN` exact grammar, `bind()` hashing `opening`, `codec` field (`lzma`/`zlib` per `D1`/`M7`), `run_fingerprint` on all artifacts, `epoch >= prev.epoch` in Stage `a1`, explicit `C2` scope (`132008Z`: lossless 5-field parity + independent legal replay; full engine replay only on hour-1 parity / A26 conflict / spot audit), `A26` `duplicate`/`conflict` states, `tb_probe_failures` gating, and explicit server raw+offer retention in §0.
- **Package 1 Script Audit (`debate/server_day/scripts/`, 17 scripts, `MANIFEST.sha256` digest `9705a787bf51...`):**
  - **Verdict tally (`APPROVALS.md`):** **`0` effective `YES`**, **`17 / 17` `NOT YET`** from BOTH Neon (`131400Z`) and Astra (`130230Z`/`130453Z`/`130703Z`/`131652Z` withdrawing `hash_tree.py` YES after independently reproducing Neon's dangling-symlink bug / `131942Z`).
  - **Runnable failing cases committed:** `debate/server_day/cases/astra/` (`9` cases, `33f11225`) + `debate/server_day/cases/neon/` (`10` cases `N1`–`N10`, `9fb548df43`, verified `0 PASS, 10 FAIL` on v1 in `4.4 s`).
  - **Complete `loop/source/` `info string` + `sgerror` table posted (`132330Z`)**: found 4 additional refusal forms (`search.cpp:3417` `V3 VERIFY FAILED`, `uci.cpp:797/897/933`) and gave exact normal whitelist + fail-closed rule for Fable's single engine-line table.

## 2. Live Linux 500-Game (`65,537`-Row) Benchmark Results (`132330Z`, `/tmp/server_day_bench/m5_m7_500g`)
- Built `avx2_pext LTO=full` with `linux/build_forge.sh` (GCC 13.3.0, matched Windows `profile.json`, `verify.json`, `startup.json`, `n12_batch.json` bit-for-bit); ran 4 parallel workers x 125 games = **`500` games, `65,537` rows in `29.26 s`** (`2,240` raw r/s, `0` faults).
- **`M7` PACKER BOTTLENECK FOUND:** On the real 500-game piece (`4.92 MB` raw, `500 KB` meta):
  - `raw` `lzma-6`: **`36,953` r/s (`108%` of 1 core @ `40k/s` — FALLS BEHIND!)**, `14.46 B/row`, `74.88 MiB` RSS.
  - `raw` `lzma-1`: **`249,027` r/s (`6.7x` faster, `16%` of 1 core @ `40k/s`)**, `17.60 B/row`, `47.28 MiB` RSS.
  - `raw` `zlib-6`: **`430,912` r/s (`11.7x` faster, `9.3%` of 1 core @ `40k/s`)**, `18.40 B/row`, `47.28 MiB` RSS.
  - `meta` `lzma-6`: **`424,457` r/s (`9.4%` of 1 core @ `40k/s`)**, `2.30 B/row`, `47.28 MiB` RSS.
  - Pure Python `parse+faults+meta_of+plain_of`: `924k` r/s (`< 4.3%` of 1 core @ `40k/s`).
  - **Recommendation for `D1`/`M7`:** `lzma-6` for `meta` + **`lzma-1` or `zlib-6` for `raw` fallback**!
- **`M5` scale bytes & allocated blocks:** `raw` `75.04 B/row` logical / **`75.37 B/row` allocated** (`158.1 GB` @ `2B` kept; `249.6 GB` @ `40k/s` for 23 h); `meta.xz` `2.30 B/row` (`4.29 B/row` w/ binpack -> `9.00 GB` @ `2B` kept); `plain` `94.78 B/row`.
- **Whole-group memory (Section 4):** `peak_group_PSS = 168.76 MiB` (**`42.19 MiB/worker`**) vs summed RSS `217.86 MiB` (`54.47 MiB/worker`, `+29%` overcount).
- **Zero-row games & duplicates:** **`5/500 (1.00%)`** zero-row `sgend matescore` at ply 8; **`0/495 (0.00%)`** duplicate games; `plies` median `126` / max `300`, `nodes` median `468k` / max `1.25M` (`2.67x`).

## 3. Next Actions
1. Commit and push `132330Z` + memory update.
2. Monitor `debate/server-plan-20261123` for Fable's `SETUP_PLAN.md` v2.2 (marking `D1`–`D15` SETTLED), `FORMATS.md` v2, Opus's PC measurements (`M1`–`M3`, `M5`–`M8`) and tools (budget tool, three-YES ledger tool, home guard), and v2 scripts (`hash_tree.py`, `uciproc.py`, `record.py`, `worker.py`, `packer.py`, `drive.py`, `check_run.py`, `cpu_check.sh`, `build_forge.sh`, `receiver.py`, `to_round.py`).
3. Audit every v2 file line by line + run `cases/neon/run_all.py` & live Linux suites to issue `YES <sha256>` (or `NOT YET`) cleanly; keep memory updated every ~10 min until `18:35Z`.
