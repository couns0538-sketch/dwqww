# Neon Memory (Server Day Debate)

Updated: 2026-11-23T14:50:00Z (UTC). Stop time: 18:35Z (~3h 45m remaining).
Active branch: `debate/server-plan-20261123`.

## Owner Hand-Over Rule (`212743Z`, `212820Z`)
- Stop stays **`18:35Z` UTC**. Fable is active (`214118Z` = `1441Z` UTC).
- On `FABLE OUT` (or 15 minutes of Fable silence): Astra edits final state & `FINAL_FOR_THE_OWNER.md`, Neon reviews with `AGREE`/`CHANGE`, Astra hands final file to owner at `18:35Z`.

## Current state of the server-day plan & formats
- **`SETUP_PLAN.md` v2.2** (`35b8c34424e4...`): ALL decisions `D1`–`D15`, Section 2, Section 4 settled. Additional agreed controls queued for `scripts_v2/`: D4 shortfall + 4 boundaries (`140827Z`, `143323Z`), dual-mode normal/raw-fallback storage (`141912Z`, `212259Z`), per-ancestor cgroup headroom `min_L(max_L - current_L)` (`143622Z`, `214118Z`), D10/N16 self-spread same-binary A/A rule (symmetrical faster/slower) + `completed_opening` (`edge3146` ply-7 vs `edge4013` ply-8, `144008Z`, `214118Z`), Stage `b` local prerequisite outage retry before single publication (`144620Z`, `145000Z`).
- **`FORMATS.md` 2.2** (`02bd23ad...`): 2.3 queued with Neon's 4 closures (`143000Z`, accepted by Fable `213251Z` & Astra `143221Z`) + worker-writing questions + Stage `b` local retry wording.
- **Independent references (`ref/astra/`, `ref/neon/`):** outside paid package. `ref/neon/` (`750eb3c9...`) passed `15/15` + `6/6` on both Linux hosts. `cases/astra/record_v2_vectors.json` (`4fb382d0...`, 13 positives + 10 negatives) independently verified by Neon and accepted by Fable.

## Approval Ledger State (`scripts_v2/`)
- **Package 1 (`scripts/`, 17 files):** `0` effective `YES` (frozen baseline).
- **`scripts_v2/` driver v3 (`e68d9ef50e`, manifest `28b68c8f...`):**
  - `scripts_v2/run/engine_lines.py` (`a82eb9c85f28f25792a98930b39fc4a4b26ad03639c4fc6ae303adffd32167f1`): **Astra `YES` (`144526Z`) + Neon `YES` (`145000Z`)** — awaiting Fable's formal `YES` line for first 3-seat `YES`!
  - `scripts_v2/tests/test_uciproc.py` (`4c8cef0910a616265309de0f530707a4f7709c98998e7cc8d7134a0273194774`): **Astra `YES` (`144526Z`) + Neon `YES` (`145000Z`)** (58/58 on v3, 48/58 on v2, 15/53 on v1 on native Linux; will re-vote when 2 new `uciproc.py` checks are added).
  - `scripts_v2/run/uciproc.py` (`ab4e7ec8d3e48dcf5d26cd63b6dc0f1f1672bc60e46dec705c5e2319a7030a8c`): **Astra `NOT YET` (`144526Z`) + Neon `NOT YET` (`145000Z`)** — both live-reproduced on Linux (`_note()` unguarded `ENOSPC` -> `nodes 29` with `gone == ''`; `secs = TIMEOUT_MAX + 1000` -> `OverflowError` -> `nodes 20` with `gone == ''`).

## Next actions
1. Commit & push `145000Z` votes + memory update.
2. Watch both branches (`AwaitShell`) for:
   - `scripts_v2/run/uciproc.py` v4 + updated `test_uciproc.py` -> immediate Linux verification & `YES`!
   - `FORMATS.md` 2.3 -> fast `AGREE`!
   - `scripts_v2/run/record.py`, `scripts_v2/run/worker.py` (95/95 on PC!), `scripts_v2/tools/budget.py` (177 checks on PC!), `packer.py`, `linux/`, `home/` -> immediate line-by-line review + live Linux fault tests on `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`)!
3. Keep updating `debate/memory/neon.md` ~every 10 minutes; continue until `18:35Z` UTC.
