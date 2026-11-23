# Neon Memory (Server Day Debate)

Updated: 2026-11-23T15:35:30Z (UTC). Stop time: 18:35Z (~3h 00m remaining).
Active branch: `debate/server-plan-20261123`.

## Owner Hand-Over Rule (`212743Z`, `212820Z`)
- Stop stays **`18:35Z` UTC**. Fable is active (`223416Z` = `15:34:16Z` UTC; finished reading `packer.py` 460 lines -> found crash-window bug between `p.offer.json` and `p.offer.json.zz`; Opus repairing both `worker.py` and `packer.py`).
- On `FABLE OUT` (or 15 min silence): Astra edits final state & `FINAL_FOR_THE_OWNER.md`, Neon reviews (`AGREE`/`CHANGE`), Astra hands final file to owner at `18:35Z`.

## Plan & Formats State
- **`SETUP_PLAN.md` v2.4** (`be886e29954b8141786eeb8442d1543efdcb7e2330c9c367e518c1f97ce97361`): **AGREE** by all three (Astra `152716Z`, Neon `152800Z`/`153120Z`, editor Fable `222530Z`).
- **`FORMATS.md` v2.6** (`4c97d0838da3c11bb247e1dbaf2b3990580ebdd07e35814475ed64135eb6ed80`): **AGREE** Neon (`153530Z`), editor Fable (`223416Z`), Astra asked. Fixes §1.8.3 advancing-only frontier (`{done, noselfgame, refused}` skipped; durable `unfinished` and unresolved `failed`/torn are dispatch barriers, 100% finalizer-restart idempotent) and adds §1.2 rolling schedule history allocation + incremental `SCHEDULE.<n+1>` verification.
- **Independent references (`ref/astra/`, `ref/neon/`):** outside paid package. Both tested & verified on Linux.

## Approval Ledger State (`APPROVALS_V2.md`, `scripts_v2/`) — ALL 5 PUBLISHED FILES 3/3 `YES`!
- **Package 1 (`scripts/`, 17 files):** `0` effective `YES` (frozen baseline, closed).
- **`scripts_v2/` (manifest `8081536d31099a300926e6c95ef85a2c293a65d6a9aeda481e2d422f67842d74`):**
  1. `scripts_v2/run/engine_lines.py` (`a82eb9c85f28f25792a98930b39fc4a4b26ad03639c4fc6ae303adffd32167f1`): **3/3 `YES`**.
  2. `scripts_v2/run/uciproc.py` (`7de2728aef77b686e759b73afedca5fee1f4d7ec68515e3176732690f0aa87a4`): **3/3 `YES`**.
  3. `scripts_v2/tests/test_uciproc.py` (`690b3243764c627d59eb3657c02c74089490e8c86ac658fdc51914dd6f418308`): **3/3 `YES`**.
  4. `scripts_v2/run/record.py` (`bc71fa894bf9fa0966fe39f3c4db0f6bd95a98d8ecbf372b0ce93a964d22ea52`): **3/3 `YES`**.
  5. `scripts_v2/tests/test_record.py` (`a8e16021f829da4c27c79812ac7d87f6cc8b1bb173c51581709003590806abb0`): **3/3 `YES`**.
- **In pipeline on PC:** `scripts_v2/run/worker.py` (updating to 2.6 + strict calendar dates + incremental schedule check), `scripts_v2/run/packer.py` (fixing `p.offer.json` -> `p.offer.json.zz` crash window), `scripts_v2/tools/budget.py`, then home reader, guards, launcher.

## Next actions
1. Commit & push `153530Z` `FORMATS.md` 2.6 `AGREE` + memory update.
2. Poll both branches (`AwaitShell`) for Astra's `FORMATS.md` 2.6 `AGREE` and Fable's `worker.py` / `packer.py` / `budget.py` drops.
3. Audit every line & live-test every new `scripts_v2/` drop on Linux against `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`); keep updating memory ~every 10 minutes until `18:35Z` UTC.
