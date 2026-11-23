# Neon Memory (Server Day Debate)

Updated: 2026-11-23T13:39:45Z (UTC). Stop time: 18:35Z (~4h 55m remaining).
Active branch: `debate/server-plan-20261123`.

## Current state of the server-day plan
- **`SETUP_PLAN.md` v2.2** (`35b8c34424e4...`, Fable `203408Z` / `60c40eee23`):
  - **ALL decisions `D1`–`D15`, Section 2 (5 counts + C2 scope), and Section 4 (machine minimums + both-forms server spool sizing) are SETTLED** on our joint record!
  - Section 7 (45 merged failure rows) has a planted test in EVERY row.
  - PC measurements (`M2`, `M3`, `M5`, `M6`, `M7`) by Opus (2,000 games, recounted by Fable) are in Section 10: 3 home stages = `42,332` raw rows/CPU-s (`0.66` of 1 thread @ `26,456` kept/s); kept `94.78%`; packed `4.568 B/kept row` (`9.14 GB` for 2B, matching Linux `9.00 GB`); raw `75.1 B/row` (`158 GB` for 2B, matching Linux `75.37 B/row` allocated); `lzma-6` raw fallback only `43k` r/s on PC / `37k` on Linux -> switched to `zlib-6` (`431k` r/s); Opus also measured `1,018 B/game` = `15.5 GiB` RAM blowup in v1 home ledger -> removed in `FORMATS.md` v2.
  - Opus ran all 9 of Astra's cases on Windows PC: **all 9 failed with rc=1 identically to Linux**, confirming every fault is in the code, not OS-specific.
- **`FORMATS.md` v2** (`5e6e30e4d447...`):
  - Reviewed line-by-line by Neon (`133945Z`), voted **`CHANGE`** for 5 concrete protocol bugs before coding writers/readers:
    1. §2.1 `epoch` monotonicity must be by piece **`index`** (`i < j => epoch[i] <= epoch[j]`), NOT arrival order — otherwise valid out-of-order `p1(epoch 1)` arriving after `p2(epoch 2)` is falsely rejected as stale!
    2. §2.0 `(slot, counter)` does NOT arithmetically name one piece (short pieces at range boundaries/stops break `(c-1)//piece_games`); use a **per-piece interval table** `(slot, index, first_counter, last_counter)` (`~1–2 MiB` for 2B day) + disjoint round ranges + opening overlapping piece verdict only on interval overlap.
    3. §2.3 `partial` round immutability trap (Stage `b` must wait while pieces/seals are in transit before `TERMINAL.jsonl` closes the day!) + A26 conflict symmetry across immutable per-piece `verdict.json` files.
    4. §1.6 zero-row pieces (`games >= 1, rows == 0`): offer directly as `"raw"` without calling `convert` or counting toward `PACKER_MODE.jsonl` 3-failure fallback breaker; probes run in scratch temp space only.
    5. Exact LF-terminated `.raw` + `bind` byte rule (§7 row 7), explicit `run_fingerprint` on every immutable record (§1.5–§2.5), no raw floats in hashed records, structured `opening_rule` with `plies`, `schedule: 0` for pilot ranges, `TERMINAL.jsonl` full schedule chain / `no_schedule`, `{"t":"ended"}` + crash-after-seal recovery in §1.4, empty-range sentinel in §1.7, dead-slot handling in §1.8.
- **`run/engine_lines.py` (upcoming v2):** Confirmed on Linux across all 8 frozen workloads + 500 self-play games (`65,537` rows) that clean runs print **only 4 `info string` forms** (`NNUE v3 loaded`, `NNUE v3 active`, `bench depth`, `eval hce`), and `0` during `selfgame`. Agreed with Fable's tighter 4-form whitelist (refusing `softnodes`, clock traces, book moves, legacy loader lines).
- **Linux Section 4 `machine_check` kernel probe spec (`133500Z`):** Proved live on this Ubuntu 24.04 host that `/sys/fs/cgroup/memory.max` does NOT exist at root while `/sys/fs/cgroup/<proc/self/cgroup>/memory.max = 14.63 GiB` sits `1.00 GiB` below `/proc/meminfo MemTotal = 15.63 GiB`, and PID 1 is `tini` with `/run/systemd/system` missing (`D15`). Gave Fable exact cgroup v2 ancestor-walk + `statvfs` `ST_RDONLY`/`ST_NOEXEC` + `st_dev` + `RLIMIT_CORE=(0,0)` + `sched_getaffinity` spec.
- **Section 5 (uncommitted first-debate tools):** Answered honestly (`133945Z`): those 3 tools lived only in scratch `/tmp/` on an earlier ephemeral first-debate VM, are not on this VM, should not be treated as branch evidence, and will not be reconstructed during the server-day 6 hours under the owner's single-focus order.

## Approval Ledger State (`debate/server_day/APPROVALS.md`, `d7a57477c19a...`)
- Package 1 (`scripts/`, `MANIFEST.sha256` member digest `9705a787bf51...`): **`0` effective `YES`** across all 17 scripts from all 3 seats (Astra, Neon, Fable all `NOT YET` on confirmed bugs).
- Waiting for Fable's `debate/server_day/scripts_v2/` (starting with `run/engine_lines.py` + `run/uciproc.py`, then `record.py`, `worker.py`, `packer.py`, tools, home, guards, tests).

## Linux scratch & artifacts
- `/tmp/server_day_bench/build_clean_lto/bin/forge` (GCC 13.3 AVX2+PGO+LTO from frozen `loop/source`, matches PC `profile`/`verify`/`startup`/`n12_batch` bit-for-bit).
- `debate/server_day/cases/neon/` (`N1`–`N10` runnable failing cases, verified `0 PASS, 10 FAIL` on v1).

## Next actions
1. Wait for Fable's `FORMATS.md` v3 (or v2.1) and first `debate/server_day/scripts_v2/` drop (`engine_lines.py`, `uciproc.py`, `record.py`, `worker.py`, `packer.py`, etc.) + Astra's `FORMATS.md` v2 vote.
2. Review every `scripts_v2/` file line-by-line, verify SHA-256 against its manifest, port/run `cases/neon/` + `cases/astra/` + `tests/` + adversarial fault tests live on Linux, and post exact `YES <sha256> <path>` or `NOT YET <sha256> <path>: line N: <case>`.
3. Update memory every ~10 minutes; continue until `18:35Z`.
