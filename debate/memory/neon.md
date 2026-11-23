# Neon Memory (Server Day Debate)

Updated: 2026-11-23T15:53:30Z (UTC). Stop time: 18:35Z (~2h 41m remaining).
Active branch: `debate/server-plan-20261123`.

## Owner Hand-Over Rule (`212743Z`, `212820Z`)
- Stop stays **`18:35Z` UTC**. Fable is active (`225123Z` = `15:51:23Z` UTC).
- On `FABLE OUT` (or 15 min silence): Astra edits final state & `FINAL_FOR_THE_OWNER.md`, Neon reviews (`AGREE`/`CHANGE`), Astra hands final file to owner at `18:35Z`.

## Plan & Formats State
- **`FORMATS.md` v2.7** (`58debbd34fc951fc9a4ba49b5cd2d197fae8f0c9a3d490902a01f4dae5626f4b`): **AGREE BY ALL THREE** (Astra `154359Z`, Neon `154410Z`, editor Fable `224234Z`).
- **`SETUP_PLAN.md` v2.5** (`cd63421ba4203b98ac7c43e695cbaaa8d28c120f79423686eda98b21049eb91c`): **AGREE** Neon (`155330Z`), editor Fable (`225123Z`), Astra asked (both seats voted `AGREE D4-surplus-above-the-margin` at `154854Z` & `154910Z` and agreed on `SELF_PLAY` when 0 whole pairs fit). Verified all 3 hand-worked `budget.py` cases in `225123Z` with `fractions.Fraction`.
- **Accepted controls after agreement (`APPROVALS_V2.md`):** Astra `154415Z` simultaneous claims on one volume (volume-wide atomic disk accounting for future server disk guard).

## Approval Ledger State (`APPROVALS_V2.md`, `scripts_v2/`) — ALL 5 PUBLISHED FILES 3/3 `YES`
- **`scripts_v2/` (manifest `8081536d31099a300926e6c95ef85a2c293a65d6a9aeda481e2d422f67842d74`):**
  1. `scripts_v2/run/engine_lines.py` (`a82eb9c8...`): **3/3 `YES`**.
  2. `scripts_v2/run/uciproc.py` (`7de2728a...`): **3/3 `YES`**.
  3. `scripts_v2/tests/test_uciproc.py` (`690b3243...`): **3/3 `YES`**.
  4. `scripts_v2/run/record.py` (`bc71fa89...`): **3/3 `YES`**.
  5. `scripts_v2/tests/test_record.py` (`a8e16021...`): **3/3 `YES`**.
- **In pipeline on PC (not yet published):** `tools/budget.py` + test (applying D4 2.5 + whole-number/non-bool input check), `run/worker.py` + test (updating to FORMATS 2.7), `run/packer.py` + test (repairing finished-offer crash window per Neon `153530Z`).
- **Cached Linux Forge binary (outside repo):** `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`).

## Next actions
1. Commit & push `155330Z` `SETUP_PLAN.md` 2.5 `AGREE` + memory update.
2. Poll both branches (`AwaitShell`) for Astra's `SETUP_PLAN.md` 2.5 vote and Fable's `budget.py`, `worker.py`, `packer.py` drops.
3. Line-by-line audit + live Linux test (with `/tmp/neon_forge_bin/forge_avx2` and fault injection) every `scripts_v2/` drop; update memory ~every 10 minutes until `18:35Z` UTC.
