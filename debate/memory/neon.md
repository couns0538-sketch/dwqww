# Neon Memory (Server Day Debate)

Updated: 2026-11-23T14:41:30Z (UTC). Stop time: 18:35Z (~3h 54m remaining).
Active branch: `debate/server-plan-20261123`.

## Owner Hand-Over Rule (`212743Z`, `212820Z`)
- Stop stays **`18:35Z` UTC**. Fable stays in the debate for now.
- On `FABLE OUT` (or 15 minutes of Fable silence without it): Astra becomes editor of the final state & `debate/server_day/FINAL_FOR_THE_OWNER.md`, Neon reviews with `AGREE`/`CHANGE` (can read Astra's branch directly via `git fetch`), and Astra hands the owner the final file in her window at stop.

## Current state of the server-day plan & formats
- **`SETUP_PLAN.md` v2.2** (`35b8c34424e4...`): ALL decisions `D1`–`D15`, Section 2, Section 4 settled. Additional agreed requirements queued for `scripts_v2/`: D4 shortfall + 4 boundary cases (`140827Z`, `143323Z`), dual-mode normal vs raw-fallback storage room (`141912Z`, `212259Z` §2), per-ancestor cgroup headroom `min_L(max_L - current_L)` (`143622Z`), D10/N16 identical-binary A/A timing discipline + `completed_opening` (`144008Z`), multi-process home rules throughput (`140908Z`).
- **`FORMATS.md` 2.2** (`02bd23ad...`): Astra `AGREE`, Neon `AGREE` + 4 closures (`143000Z`) ALL accepted by Fable (`213251Z`) and Astra (`143221Z`) for **2.3** (control-file `.zz` order with `offer.json.zz` last + `offer_wire_*`; stage a2 cross-checking all `seal.json` summary fields; exact `binpack + meta.xz -> raw_sha256` lossless reconstruction; `instance` `null != null` fail-closed rule).
- **Independent references (`ref/astra/` + `ref/neon/`, outside paid package):**
  - `ref/astra/` (`c4315a24...`): read by Fable & Neon; 13 native records + `cases/astra/record_v2_vectors.json` (`4fb382d0...`, all 13 positives verified bit-for-bit by Neon `144130Z`).
  - `ref/neon/` (`750eb3c9...`): passed `15/15` + `6/6` on Neon's AND Astra's Linux hosts; left stable at `750eb3c9...` while Fable queues his line-by-line read.

## Approval Ledger State (`scripts_v2/`)
- **Package 1 (`scripts/`, 17 files):** `0` effective `YES` (frozen baseline).
- **`scripts_v2/` batch 1 rev 2 (`94e7518e...`, `42cf67d9...`):** BOTH Astra (`142216Z`) and Neon (`143000Z`) voted `NOT YET`. Fable (`213251Z`, `213501Z`) accepted Astra's 2 + Neon's 4 findings (and all 3 seats agreed `bestmove 0000` stays refused in the paid-day table, `type button` stays allowed, empty lines `""` refused). Driver rev 3 + test running behind PC gate now; `record.py` and `tools/budget.py` follow next.
- **0 effective `YES` in `scripts_v2/` so far.**
- Cached native Linux Forge binary ready at `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`) for instant 2-second live testing of `scripts_v2/` drops.

## Next actions
1. Commit & push `144130Z` ack + memory update.
2. Poll both branches (`AwaitShell`) for Fable's `scripts_v2/` driver v3, `FORMATS.md` 2.3, `record.py`, `tools/budget.py`, `home/`, `worker.py`, `packer.py`, `linux/`.
3. For EVERY `scripts_v2/` file that lands: full line-by-line read + run official test suite on Linux + run targeted adversarial probes on `/tmp/neon_forge_bin/forge_avx2` -> cast exact-byte `YES <sha256> <path>` or `NOT YET <sha256> <path>`.
4. Keep updating `debate/memory/neon.md` ~every 10 minutes; continue until `18:35Z` UTC.
