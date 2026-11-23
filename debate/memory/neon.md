# Neon Memory (Server Day Debate)

Updated: 2026-11-23T15:44:10Z (UTC). Stop time: 18:35Z (~2h 50m remaining).
Active branch: `debate/server-plan-20261123`.

## Owner Hand-Over Rule (`212743Z`, `212820Z`)
- Stop stays **`18:35Z` UTC**. Fable is active (`224234Z` = `15:42:34Z` UTC; `worker.py` and `packer.py` being updated by Opus to FORMATS 2.7 + Neon's packer repair conditions).
- On `FABLE OUT` (or 15 min silence): Astra edits final state & `FINAL_FOR_THE_OWNER.md`, Neon reviews (`AGREE`/`CHANGE`), Astra hands final file to owner at `18:35Z`.

## Plan & Formats State
- **`SETUP_PLAN.md` v2.4** (`be886e29954b8141786eeb8442d1543efdcb7e2330c9c367e518c1f97ce97361`): **AGREE** by all three (Astra `152716Z`, Neon `152800Z`/`153120Z`, editor Fable `222530Z`).
- **`FORMATS.md` v2.7** (`58debbd34fc951fc9a4ba49b5cd2d197fae8f0c9a3d490902a01f4dae5626f4b`): **AGREE** Neon (`154410Z`), editor Fable (`224234Z`), Astra asked. Adds `mode: "play"|"seal_only"` on `epoch` line, consecutive schedule chase in §1.2, three-clock bound (`UTC`, `CLOCK_MONOTONIC`, `CLOCK_BOOTTIME`) with 10 s forward-UTC hold (`failed`/`clock`), serial-order `unreconciled` check, and per-member last-byte progress + independent as-of-expiry reporting.
- **Independent references (`ref/astra/`, `ref/neon/`):** outside paid package. Both tested & verified on Linux.

## Approval Ledger State (`APPROVALS_V2.md`, `scripts_v2/`) — ALL 5 PUBLISHED FILES 3/3 `YES`!
- **`scripts_v2/` (manifest `8081536d31099a300926e6c95ef85a2c293a65d6a9aeda481e2d422f67842d74`):**
  1. `scripts_v2/run/engine_lines.py` (`a82eb9c8...`): **3/3 `YES`**.
  2. `scripts_v2/run/uciproc.py` (`7de2728a...`): **3/3 `YES`**.
  3. `scripts_v2/tests/test_uciproc.py` (`690b3243...`): **3/3 `YES`**.
  4. `scripts_v2/run/record.py` (`bc71fa89...`): **3/3 `YES`**.
  5. `scripts_v2/tests/test_record.py` (`a8e16021...`): **3/3 `YES`**.
- **In pipeline on PC:** `worker.py` (updating to 2.7: epoch `mode`, 3 clocks + hold, consecutive schedule chase, serial order, strict calendar date), `packer.py` (updating to finish existing offer + verify members + ignore leftover other-form member), `budget.py`, then home reader, guards, launcher.

## Next actions
1. Commit & push `154410Z` `FORMATS.md` 2.7 `AGREE` + memory update.
2. Poll both branches (`AwaitShell`) for Astra's `FORMATS.md` 2.7 vote and Fable's `worker.py`, `packer.py`, `budget.py` drops.
3. Audit every line & live-test every new `scripts_v2/` drop on Linux against `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`); keep updating memory ~every 10 minutes until `18:35Z` UTC.
