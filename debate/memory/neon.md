# Neon Memory (Server Day + 8h Continuation Debate)

Updated: 2026-11-23T16:27:35Z (UTC).
Active branch: `debate/server-plan-20261123` (fetch `origin/debate/server-plan-20261123-astra` too; Astra edits after `17:25Z`).

## Updated Owner Schedule (`232555Z`, replaces earlier `18:35Z` stop!)
- **Now – `17:25Z` (~57m remaining with Fable):** Fable leaves at `17:25Z` (`FABLE OUT`). Priority: audit + get 3/3 `YES` on `run/clockwatch.py`, repaired `tools/budget.py` (9 points), and any `scripts_v2/` drops published before `17:25Z`.
- **Hours 1–4 (`17:25Z` – `21:25Z`): Engine plan & later stages.** Astra edits, Neon reviews/verifies with evidence & `forge6.5` branch measurements. Deliverable: `debate/engine_plan/ENGINE_PLAN_8H.md` + `AGREE <sha256> neon ENGINE_PLAN_8H.md` (Fable checks once at `21:55Z`).
- **Hours 5–8 (`21:25Z` – `01:25Z` Nov 24): Server-day plan.** Vote (`YES`/`NOT YET`) on Opus's `scripts_v2/` drops (`<stamp>_opus_<subject>.md`), write/verify exact specs + hand-computed test cases under `debate/server_day/specs/`, write ordered rehearsal & measurements, and finalize plain-words `debate/server_day/FINAL_FOR_THE_OWNER.md` + exact-byte `AGREE` (Fable checks once at `01:55Z`). Deliver final plain-words summary to user at `01:25Z`.
- **Strict rules:** Only touch files under `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Current Agreed Documents & `scripts_v2/` Ledger (Manifest `63180c68...`)
- **`FORMATS.md` 2.9** (`ac566296e27b8acfe08e83c3afb27866e2b99f256c878a66c6a96519fed6b8e8`): **3/3 AGREED** (Astra `161757Z`, Neon `162055Z`, Fable `231527Z`).
- **`SETUP_PLAN.md` 2.7** (`4100b2a5cdc6d44dab1e38816ad317d23f8dd96618ed1facfd70c6a80c3eb374`): **3/3 AGREED** (Astra `161757Z`, Neon `162055Z`, Fable `231527Z`).
- **5 files with 3/3 `YES`:** `run/engine_lines.py` (`a82eb9c8`), `run/uciproc.py` (`7de2728a`), `tests/test_uciproc.py` (`690b3243`), `run/record.py` (`bc71fa89`), `tests/test_record.py` (`a8e16021`).
- **2 files with `NOT YET` from both seats (Fable repairing all 9 points now):** `tools/budget.py` (`c7aab952`), `tests/test_budget.py` (`2c0fc9f6`).
- **Imminent drops before `17:25Z`:** `run/clockwatch.py` + test, repaired `tools/budget.py` + test; Opus working on `run/worker.py` (with `clockwatch.py`) and `run/packer.py`.
- **Cached Linux Forge binary (outside repo):** `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`).

## Next actions
1. Commit & push `162735Z` acknowledgement + memory update.
2. Poll both branches (`AwaitShell`) for `run/clockwatch.py` + test and repaired `tools/budget.py` + test; audit line-by-line & live-test on Linux immediately!
3. At `17:25Z` (`FABLE OUT`), transition cleanly with Astra to Hours 1–4 (`ENGINE_PLAN_8H.md`, `forge6.5`).
