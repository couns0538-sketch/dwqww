# Neon Memory (Server Day Debate)

Updated: 2026-11-23T16:20:55Z (UTC). Stop time: 18:35Z (~2h 14m remaining).
Active branch: `debate/server-plan-20261123`.

## Owner Hand-Over Rule (`212743Z`, `212820Z`)
- Stop stays **`18:35Z` UTC**. Fable is active (`231527Z` = `16:15:27Z` UTC).
- On `FABLE OUT` (or 15 min silence): Astra edits final state & `FINAL_FOR_THE_OWNER.md`, Neon reviews (`AGREE`/`CHANGE`), Astra hands final file to owner at `18:35Z`.

## Plan & Formats State
- **`FORMATS.md` v2.9** (`ac566296e27b8acfe08e83c3afb27866e2b99f256c878a66c6a96519fed6b8e8`): **AGREE** Neon (`162055Z`), editor Fable (`231527Z`), Astra asked. Fixes in-worker watch target (engine process alone, never group), full stop allowance + deadline-aware wake, `only adds ranges`, evidence-before-control, and `STOP`/`fence` -> `FENCE.json`.
- **`SETUP_PLAN.md` v2.7** (`4100b2a5cdc6d44dab1e38816ad317d23f8dd96618ed1facfd70c6a80c3eb374`): **AGREE** Neon (`162055Z`), editor Fable (`231527Z`), Astra asked.

## Approval Ledger State (`APPROVALS_V2.md`, `scripts_v2/`) — manifest `63180c68...`
- **5 files with 3/3 `YES`:**
  1. `scripts_v2/run/engine_lines.py` (`a82eb9c8...`): **3/3 `YES`**.
  2. `scripts_v2/run/uciproc.py` (`7de2728a...`): **3/3 `YES`**.
  3. `scripts_v2/tests/test_uciproc.py` (`690b3243...`): **3/3 `YES`**.
  4. `scripts_v2/run/record.py` (`bc71fa89...`): **3/3 `YES`**.
  5. `scripts_v2/tests/test_record.py` (`a8e16021...`): **3/3 `YES`**.
- **2 newly published files (audited line-by-line & probed on Linux `162055Z`):**
  6. `scripts_v2/tools/budget.py` (`c7aab952...`): **NOT YET** Neon (`162055Z`) — 278/278 pass & 12/12 mutations caught, but 4 real defects reproduced live: (1) module-global `_SHA` stale cache across in-process `decide()` calls bypasses Failure Row 3 after raw file tamper; (2) duplicate JSON keys (`c4_rows` twice -> `REACHED`) & `NaN`/`1e500` in extra state key emit invalid JSON (`NaN`/`Infinity`) into stdout evidence; (3) `longest_game_s = 0` qualifies as `SELF_PLAY_AND_MATCHES` with unmeasured D5 stop margin; (4) minor hardening (`PermissionError` -> `UNQUALIFIED`, empty match name `""`).
  7. `scripts_v2/tests/test_budget.py` (`2c0fc9f6...`): **NOT YET** Neon (`162055Z`) — add regression cases for the 4 items above.
- **In pipeline on PC:** `run/clockwatch.py` + test (Fable writing now), then `run/worker.py` + test, `run/packer.py` + test.
- **Cached Linux Forge binary (outside repo):** `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`).

## Next actions
1. Commit & push `162055Z` votes + memory update.
2. Poll both branches (`AwaitShell`) for Astra's `FORMATS 2.9` / `SETUP_PLAN 2.7` / `budget.py` review, patched `budget.py`, and `run/clockwatch.py`, `run/worker.py`, `run/packer.py` drops.
3. Line-by-line audit & live Linux test every new `scripts_v2/` drop; keep updating memory ~every 10 minutes until `18:35Z` UTC.
