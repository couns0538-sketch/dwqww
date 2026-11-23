# Neon Memory (Server Day Debate)

Updated: 2026-11-23T16:12:30Z (UTC). Stop time: 18:35Z (~2h 22m remaining).
Active branch: `debate/server-plan-20261123`.

## Owner Hand-Over Rule (`212743Z`, `212820Z`)
- Stop stays **`18:35Z` UTC**. Fable is active (`231014Z` = `16:10:14Z` UTC).
- On `FABLE OUT` (or 15 min silence): Astra edits final state & `FINAL_FOR_THE_OWNER.md`, Neon reviews (`AGREE`/`CHANGE`), Astra hands final file to owner at `18:35Z`.

## Plan & Formats State
- **Agreed baselines:** `FORMATS.md` v2.7 (`58debbd3...`) and `SETUP_PLAN.md` v2.5 (`cd63421b...`) — both 3/3 agreed.
- **Proposed updates (`231014Z`):**
  - `FORMATS.md` v2.8 (`2c6d08de82a3ade1ac38249fb1172cfe835773f2019f896f3d87a6d1d0536354`) & `SETUP_PLAN.md` v2.6 (`dae4f288124f65fc7d9fd443c2c8d45681a2fdc1a52899f7b88d9f4b1184e532`): Fable withdrew boundary-only clocks and folded in all three joint CHANGEs (in-worker watch + external guard process group, waiting-work / examined-rate progress line, narrow compressed `CONTROL.<k>.json`).
  - **Neon `161230Z` surgical `CHANGE` on both:** verified live on Linux that unmodified `uciproc.py` spawns Forge in `worker.py`'s **own** process group (`worker pgid == engine pgid == 50218`), so the in-worker watch MUST end **that native engine process alone** via `pidfd`/handle (NEVER `(its whole group)` / `killpg`, which would kill `worker.py` itself!), reserving `killpg` strictly for the external server guard. Also flagged two small precisions (`"lengthens it"` -> `"only adds ranges"`, evidence uploaded before `CONTROL.<k>.json.zz` and `kind: "fence"` -> `FENCE.json`).

## Approval Ledger State (`APPROVALS_V2.md`, `scripts_v2/`) — ALL 5 PUBLISHED FILES 3/3 `YES`
- **`scripts_v2/` (manifest `8081536d31099a300926e6c95ef85a2c293a65d6a9aeda481e2d422f67842d74`):**
  1. `scripts_v2/run/engine_lines.py` (`a82eb9c8...`): **3/3 `YES`**.
  2. `scripts_v2/run/uciproc.py` (`7de2728a...`): **3/3 `YES`**.
  3. `scripts_v2/tests/test_uciproc.py` (`690b3243...`): **3/3 `YES`**.
  4. `scripts_v2/run/record.py` (`bc71fa89...`): **3/3 `YES`**.
  5. `scripts_v2/tests/test_record.py` (`a8e16021...`): **3/3 `YES`**.
- **In pipeline on PC (next drops):**
  - `tools/budget.py` + test (`c7aab952d886`, Fable reading changed lines next, then publishing!).
  - `run/clockwatch.py` + test (Fable writing), wired into `run/worker.py` + test.
  - `run/packer.py` + test (repaired finished-offer crash window).
- **Cached Linux Forge binary (outside repo):** `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`).

## Next actions
1. Commit & push `161230Z` surgical `CHANGE` + memory update.
2. Poll both branches (`AwaitShell`) for Astra's review of 2.8/2.6, Fable's `2.9`/`2.7` fix, and **`tools/budget.py` + test** (imminent!).
3. Line-by-line audit & live Linux test every published `scripts_v2/` drop; keep updating memory ~every 10 minutes until `18:35Z` UTC.
