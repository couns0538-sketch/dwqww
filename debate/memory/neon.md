# Neon Memory (Server Day + 8h Continuation Debate)

Updated: 2026-11-23T17:01:14Z (UTC).
Active branch: `debate/server-plan-20261123` (fetch `origin/debate/server-plan-20261123-astra` too; Astra edits after `17:25Z`).

## Owner-Confirmed 8h Continuation Schedule (`232555Z`, confirmed directly by owner to Astra `162834Z`)
- **Now – `17:25Z` (~24m remaining with Fable):** Fable leaves at `17:25Z` (`FABLE OUT`). Priority: re-verify & vote on Fable's patched `clockwatch.py` and `budget.py` v6 before `17:25Z` if published in time!
- **Hours 1–4 (`17:25Z` – `21:25Z`): Engine plan & later stages.** Astra edits, Neon reviews/verifies with evidence & `forge6.5` branch measurements. Deliverable: `debate/engine_plan/ENGINE_PLAN_8H.md` + `AGREE <sha256> neon ENGINE_PLAN_8H.md` (Fable checks once at `21:55Z`).
- **Hours 5–8 (`21:25Z` – `01:25Z` Nov 24): Server-day plan.** Vote (`YES`/`NOT YET`) on Opus's `scripts_v2/` drops (`<stamp>_opus_<subject>.md`), write/verify exact specs + hand-computed test cases under `debate/server_day/specs/`, write ordered rehearsal & measurements, and finalize plain-words `debate/server_day/FINAL_FOR_THE_OWNER.md` + exact-byte `AGREE` (Fable checks once at `01:55Z`). Deliver final plain-words summary to user at `01:25Z`.
- **Strict rules:** Only touch files under `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Current Agreed Documents & `scripts_v2/` Ledger (Manifest `583a289d...`)
- **`FORMATS.md` 2.9** (`ac566296e27b8acfe08e83c3afb27866e2b99f256c878a66c6a96519fed6b8e8`): **3/3 AGREED**.
- **`SETUP_PLAN.md` 2.7** (`4100b2a5cdc6d44dab1e38816ad317d23f8dd96618ed1facfd70c6a80c3eb374`): **3/3 AGREED**.
- **5 files with 3/3 `YES`:** `run/engine_lines.py` (`a82eb9c8`), `run/uciproc.py` (`7de2728a`), `tests/test_uciproc.py` (`690b3243`), `run/record.py` (`bc71fa89`), `tests/test_record.py` (`a8e16021`).
- **4 files audited & voted `NOT YET` by BOTH Astra (`165352Z`–`165715Z`) and Neon (`170114Z`):**
  - `run/clockwatch.py` (`15e76daf`) & `tests/test_clockwatch.py` (`20458abd`): native Linux `pidfd` + `CLOCK_BOOTTIME` + zombie readability + Forge integration + 68/68 + 7/7 mutations PASS, BUT blocking bugs found:
    1. `_fire()` line 263 `by_clock = vd == OPEN` misses `reason == "cutoff"` -> clock hold at `dispatch_end` hangs up to `D` (hours!) instead of alarming after `allowance_s` (and UTC jump into `[D - allowance, D)` alarms early).
    2. `_fire()` lines 266–270 return with `alarm = None` when process exits after `D` inside `h.gone(0.02)`.
    3. `ProcHandle.gone()` line 165 `select.select` crashes for `pidfd >= 1024` (use `select.poll`).
    4. Synchronous `refresh()` before judging existing `D` + `late` flag misses newly tightened trigger (`left_t < 0`, `D` ahead).
    5. Non-finite `NaN`/`inf` bounds/params accepted silently in `Bounds.set` / `Watch.__init__`.
  - `tools/budget.py` v5 (`24b6aded`) & `tests/test_budget.py` v5 (`b419d5bb`): 379/379 PASS, all 9 prior defects fixed, BUT blocking bugs found:
    1. Action windows (`left`, `new_s`) use fractional `D`/`stop_new` instead of published `cutoff_floor_s`/`dispatch_end_floor_s` (assigns match pair at `dispatch_end_floor_s=82199`, returns `SELF_PLAY` instead of `SHORT` at `cutoff_floor_s=82799`).
    2. `unsourced()` leaks local absolute paths in `res["reason"]`.
    3. Nonzero `exclusive_s` lacks source validation under failure row 3.
    4. Duplicate test case labels `F2` and `T1` in `test_budget.py`.
- **Cached Linux Forge binary (outside repo):** `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`).

## Next actions
1. Commit & push `170114Z` review + memory refresh immediately so Fable sees all findings well before `17:25Z`.
2. Watch for Fable's patched `clockwatch.py` v2 + `budget.py` v6 drops and re-audit/vote immediately before `17:25Z`.
3. While waiting (before `17:25Z`), fetch `origin/forge6.5` (read-only exploration) and prepare for Phase 1 (`17:25Z` – `21:25Z` `ENGINE_PLAN_8H.md`).
