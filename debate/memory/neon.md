# Neon Memory (Server Day Debate)

Updated: 2026-11-23T16:03:45Z (UTC). Stop time: 18:35Z (~2h 31m remaining).
Active branch: `debate/server-plan-20261123`.

## Owner Hand-Over Rule (`212743Z`, `212820Z`)
- Stop stays **`18:35Z` UTC**. Fable is active (`225604Z` = `15:56:04Z` UTC).
- On `FABLE OUT` (or 15 min silence): Astra edits final state & `FINAL_FOR_THE_OWNER.md`, Neon reviews (`AGREE`/`CHANGE`), Astra hands final file to owner at `18:35Z`.

## Plan & Formats State
- **`FORMATS.md` v2.7** (`58debbd34fc951fc9a4ba49b5cd2d197fae8f0c9a3d490902a01f4dae5626f4b`): **AGREE BY ALL THREE** (Astra `154359Z`, Neon `154410Z`, editor Fable `224234Z`).
- **`SETUP_PLAN.md` v2.5** (`cd63421ba4203b98ac7c43e695cbaaa8d28c120f79423686eda98b21049eb91c`): **AGREE BY ALL THREE** (Astra `155309Z`, Neon `155330Z`, editor Fable `225123Z`).
- **Open items after agreement:**
  1. Fable `225604Z` §3 (`worker-clocks-read-at-game-boundaries`): **CHANGE Astra (`155748Z`)**, **CHANGE Neon (`160345Z`, superseding `155820Z`)** — Neon proved live on Linux against unmodified `uciproc.py` (`7de2728a...`) + native Forge (`/tmp/neon_forge_bin/forge_avx2`) that a ~20-line watchdog thread inside `worker.py` using `os.pidfd_open` + `signal.pidfd_send_signal(..., SIGKILL)` (and `eng.p.kill()` Win32 handle on Windows) kills mid-search Forge in **1.49–1.93 ms** across all three cases (ordinary D, same-boot wake past D, forward UTC clock-hold) with **ZERO edits to `uciproc.py`** and **ZERO 600 s overrun**!
  2. Astra `155631Z` (pending backlogs by unprocessed identities/units, not literal `C1-C2`/`C2-C4`, consistent short snapshot) & `155704Z` (stage-b capacity counts examined games/raw rows, separate from `C3` changed labels): supported by Neon (`155820Z`).
  3. Astra `154415Z` (volume-wide atomic disk accounting) & `155407Z` (16.4M SQLite WAL index + no held reporting snapshot): recorded in `APPROVALS_V2.md`.

## Approval Ledger State (`APPROVALS_V2.md`, `scripts_v2/`) — ALL 5 PUBLISHED FILES 3/3 `YES`
- **`scripts_v2/` (manifest `8081536d31099a300926e6c95ef85a2c293a65d6a9aeda481e2d422f67842d74`):**
  1. `scripts_v2/run/engine_lines.py` (`a82eb9c8...`): **3/3 `YES`**.
  2. `scripts_v2/run/uciproc.py` (`7de2728a...`): **3/3 `YES`**.
  3. `scripts_v2/tests/test_uciproc.py` (`690b3243...`): **3/3 `YES`**.
  4. `scripts_v2/run/record.py` (`bc71fa89...`): **3/3 `YES`**.
  5. `scripts_v2/tests/test_record.py` (`a8e16021...`): **3/3 `YES`**.
- **In pipeline on PC (Fable ETA ~`16:40Z` for `budget.py`, then `worker.py`, `packer.py`):** `tools/budget.py`, `run/worker.py`, `run/packer.py` + their tests.
- **Cached Linux Forge binary (outside repo):** `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`).

## Next actions
1. Commit & push `160345Z` watchdog proof + memory update.
2. Poll both branches (`AwaitShell`) for Fable's reply and `budget.py` / `worker.py` / `packer.py` drops.
3. Audit every line & live-test every new `scripts_v2/` drop on Linux; keep updating memory ~every 10 minutes until `18:35Z` UTC.
