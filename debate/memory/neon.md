# Neon Memory (Server Day Debate)

Updated: 2026-11-23T15:28:00Z (UTC). Stop time: 18:35Z (~3h 07m remaining).
Active branch: `debate/server-plan-20261123`.

## Owner Hand-Over Rule (`212743Z`, `212820Z`)
- Stop stays **`18:35Z` UTC**. Fable is active (`222530Z` = `15:25:30Z` UTC; finished reading `worker.py` 1,057 lines -> NOT YET, fixing invalid-date bug + 2.4 updates before publishing `worker.py` + `test_worker.py`, then `packer.py`, then home reader).
- On `FABLE OUT` (or 15 min silence): Astra edits final state & `FINAL_FOR_THE_OWNER.md`, Neon reviews (`AGREE`/`CHANGE`), Astra hands final file to owner at `18:35Z`.

## Plan & Formats State
- **`SETUP_PLAN.md` v2.4** (`be886e29954b8141786eeb8442d1543efdcb7e2330c9c367e518c1f97ce97361`): **AGREE** Neon (`152800Z`), editor Fable (`222530Z`), Astra asked. Aligns Section 2 (`RECEIVED` vs `C1`), Section 6.2 & Section 7 row 32 (piece vs record vs local-outage retry), D2 closing-room budget + `>= 2`-round rolling horizon, and Section 8 vote table.
- **`FORMATS.md` v2.4** (`6a469247c404b4c75965e1806f42ad1a8d1c0ba3e6367c765659b504fb15fd47`): **AGREE** Neon (`152800Z`), editor Fable (`222530Z`), Astra asked. Incorporates all 4 Neon/Astra 2.4 changes (§1.1 instance equality, §1.3 same-boot `RESUME` anchor rule, §1.8.1 pilot fence `hard_cutoff_utc`, §1.8.3 `dispatch_unknown`), §2.3 child-table missing check, §2.1 listing vs confirmation (`152429Z`), and §1.7/§1.9 `never_dispatched_first` interval form (measured by Neon on Linux ext4 for 16.384M IDs: 71.25 MB allocated vs 2,409.44 MB before, 111 KB `TERMINAL.jsonl.zz`, 0.826 s, with 67.11 MB from 16,384 × 4 KiB block rounding).
- **Independent references (`ref/astra/`, `ref/neon/`):** outside paid package. Both tested & verified on Linux.

## Approval Ledger State (`scripts_v2/`) — ALL 5 PUBLISHED FILES 3/3 `YES`!
- **Package 1 (`scripts/`, 17 files):** `0` effective `YES` (frozen baseline).
- **`scripts_v2/` (manifest `8081536d31099a300926e6c95ef85a2c293a65d6a9aeda481e2d422f67842d74`):**
  1. `scripts_v2/run/engine_lines.py` (`a82eb9c85f28f25792a98930b39fc4a4b26ad03639c4fc6ae303adffd32167f1`): **3/3 `YES`**.
  2. `scripts_v2/run/uciproc.py` (`7de2728aef77b686e759b73afedca5fee1f4d7ec68515e3176732690f0aa87a4`): **3/3 `YES`**.
  3. `scripts_v2/tests/test_uciproc.py` (`690b3243764c627d59eb3657c02c74089490e8c86ac658fdc51914dd6f418308`): **3/3 `YES`**.
  4. `scripts_v2/run/record.py` (`bc71fa894bf9fa0966fe39f3c4db0f6bd95a98d8ecbf372b0ce93a964d22ea52`): **3/3 `YES`**.
  5. `scripts_v2/tests/test_record.py` (`a8e16021f829da4c27c79812ac7d87f6cc8b1bb173c51581709003590806abb0`): **3/3 `YES`**.
- **In pipeline on PC (not yet published):** `scripts_v2/run/worker.py` (Fable read 1,057 lines -> NOT YET: updating to FORMATS 2.4 + fixing Nov 31 date bug), `scripts_v2/run/packer.py` (Opus 68/68, queued for Fable's read), `scripts_v2/tools/budget.py`, then home reader, guards, launcher.

## Next actions
1. Commit & push `152800Z` AGREE + measurement + memory update.
2. Poll both branches (`AwaitShell`) for `scripts_v2/run/worker.py` + `tests/test_worker.py`, `packer.py`, `budget.py`, and Astra's 2.4 votes.
3. Audit every line & live-test every new `scripts_v2/` drop on Linux against `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`); keep updating memory ~every 10 minutes until `18:35Z` UTC.
