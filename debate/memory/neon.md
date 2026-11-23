# Neon Memory (Server Day Debate)

Updated: 2026-11-23T15:38:30Z (UTC). Stop time: 18:35Z (~2h 56m remaining).
Active branch: `debate/server-plan-20261123`.

## Owner Hand-Over Rule (`212743Z`, `212820Z`)
- Stop stays **`18:35Z` UTC**. Fable is active (`223416Z` = `15:34:16Z` UTC; repairing `worker.py` and `packer.py`).
- On `FABLE OUT` (or 15 min silence): Astra edits final state & `FINAL_FOR_THE_OWNER.md`, Neon reviews (`AGREE`/`CHANGE`), Astra hands final file to owner at `18:35Z`.

## Plan & Formats State
- **`SETUP_PLAN.md` v2.4** (`be886e29954b8141786eeb8442d1543efdcb7e2330c9c367e518c1f97ce97361`): **AGREE** by all three (Astra `152716Z`, Neon `152800Z`/`153120Z`, editor Fable `222530Z`).
- **`FORMATS.md` v2.6** (`4c97d0838da3c11bb247e1dbaf2b3990580ebdd07e35814475ed64135eb6ed80`): **CHANGE** by both Astra (`153602Z`) and Neon (`153830Z`) for v2.7:
  1. §1.4 & §1.8.3: add `"mode":"play"|"seal_only"` to existing `epoch` line (zero extra appends per game); infer `dispatch_unknown` ONLY from a prior `"mode":"play"` epoch so restarting a first-ever finalizer stays 100% invariant (`never_dispatched`).
  2. §1.2: loop `n+1, n+2, ...` until next schedule file is absent before each reservation (never stop after only one step when `n+2` tightened `dispatch_end_utc`).
- **Additional concurred controls for forthcoming v2 scripts (`153451Z`, `153725Z`, `153830Z`):**
  - Linux `CLOCK_BOOTTIME` (suspend-inclusive) beside `CLOCK_MONOTONIC` and trusted UTC inside one boot (earliest bound, never lengthen on backward wall jump).
  - Per-member byte-progress idle timeout at home + independent as-of-expiry reporting without blocking on hung transfers or backdating late completions.
- **Independent references (`ref/astra/`, `ref/neon/`):** outside paid package. Both tested & verified on Linux.

## Approval Ledger State (`APPROVALS_V2.md`, `scripts_v2/`) — ALL 5 PUBLISHED FILES 3/3 `YES`!
- **`scripts_v2/` (manifest `8081536d31099a300926e6c95ef85a2c293a65d6a9aeda481e2d422f67842d74`):**
  1. `scripts_v2/run/engine_lines.py` (`a82eb9c8...`): **3/3 `YES`**.
  2. `scripts_v2/run/uciproc.py` (`7de2728a...`): **3/3 `YES`**.
  3. `scripts_v2/tests/test_uciproc.py` (`690b3243...`): **3/3 `YES`**.
  4. `scripts_v2/run/record.py` (`bc71fa89...`): **3/3 `YES`**.
  5. `scripts_v2/tests/test_record.py` (`a8e16021...`): **3/3 `YES`**.
- **In pipeline on PC:** `worker.py`, `packer.py`, `budget.py`, then home reader, guards, launcher.

## Next actions
1. Commit & push `153830Z` `FORMATS.md` 2.6 `CHANGE` + memory update.
2. Poll both branches (`AwaitShell`) for `FORMATS.md` 2.7 and Fable's `scripts_v2/run/worker.py`, `packer.py`, `budget.py` drops.
3. Audit every line & live-test every new `scripts_v2/` drop on Linux against `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`); keep updating memory ~every 10 minutes until `18:35Z` UTC.
