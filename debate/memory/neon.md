# Neon Memory (Server Day + 8h Continuation Debate)

Updated: 2026-11-23T17:12:40Z (UTC).
Active branch: `debate/server-plan-20261123` (fetch `origin/debate/server-plan-20261123-astra` too; Astra edits after `17:25Z`).

## Owner-Confirmed 8h Continuation Schedule (`232555Z`, confirmed directly by owner to Astra `162834Z`)
- **Now – `17:25Z` (~12m remaining with Fable):** Fable leaves at `17:25Z` (`FABLE OUT`). Watching for Fable's patched `clockwatch.py` + `budget.py` v6 drops and `FABLE OUT` ledger.
- **Hours 1–4 (`17:25Z` – `21:25Z`): Engine plan & later stages.** Astra edits, Neon reviews/verifies with evidence & `forge6.5` branch measurements. Deliverable: `debate/engine_plan/ENGINE_PLAN_8H.md` + `AGREE <sha256> neon ENGINE_PLAN_8H.md` (Fable checks once at `21:55Z`).
- **Hours 5–8 (`21:25Z` – `01:25Z` Nov 24): Server-day plan.** Vote (`YES`/`NOT YET`) on Opus's `scripts_v2/` drops (`<stamp>_opus_<subject>.md`), write/verify exact specs + hand-computed test cases under `debate/server_day/specs/`, write ordered rehearsal & measurements, and finalize plain-words `debate/server_day/FINAL_FOR_THE_OWNER.md` + exact-byte `AGREE` (Fable checks once at `01:55Z`). Deliver final plain-words summary to user at `01:25Z`.
- **Strict rules:** Only touch files under `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Current Agreed Documents & `scripts_v2/` Ledger (Manifest `583a289d...`)
- **`FORMATS.md` 2.9** (`ac566296`): **3/3 AGREED**. **`SETUP_PLAN.md` 2.7** (`4100b2a5`): **3/3 AGREED**.
- **5 files with 3/3 `YES`:** `run/engine_lines.py` (`a82eb9c8`), `run/uciproc.py` (`7de2728a`), `tests/test_uciproc.py` (`690b3243`), `run/record.py` (`bc71fa89`), `tests/test_record.py` (`a8e16021`).
- **4 files voted `NOT YET` by BOTH Astra (`165352Z`–`170243Z`, `170921Z`) and Neon (`170114Z`):**
  - `run/clockwatch.py` (`15e76daf`) & `tests/test_clockwatch.py` (`20458abd`): native Linux `pidfd` + `CLOCK_BOOTTIME` + zombie readability + Forge integration + 68/68 + 7/7 mutations PASS. Blocking fixes needed: (1) `by_clock = reason == "cutoff" and vd == OPEN` (hold at `dispatch_end` hung up to `D`), (2) late exit inside `h.gone(0.02)` after `D` must still alarm + bound wait to time left, (3) `select.poll()` for `pidfd >= 1024`, (4) judge existing bounds before non-blocking `refresh` + accepted cross-thread tightening wakes sleeping `Watch` without lost wakeup (`170921Z`), (5) `late` flag on tightened trigger (`left_t < 0`), (6) `math.isfinite` checks on `Bounds.set` / `Watch.__init__`.
  - `tools/budget.py` v5 (`24b6aded`) & `tests/test_budget.py` v5 (`b419d5bb`): 379/379 PASS, 9 prior defects fixed. Blocking fixes needed: (1) compute action windows (`left`, `new_s`) from `cutoff_floor_s`/`dispatch_end_floor_s` (exact fractional kept in `bounds_exact`), (2) omit local paths from `UNQUALIFIED` `reason`, (3) source check for nonzero `exclusive_s`, (4) deduplicate `F2`/`T1` test labels.
  - **Builder spec note (`171134Z` confirmed by Neon arithmetic):** On `OWNER_CHOICE` (exit 3), `budget.py` prints `self_play_s = left` even if policy is `stop` or uncovered reduced target (`r=20000`, `left=80000` -> `n=25000`, `forecast=1.6B`; `1.5B -> n=18750 covered`, `1.7B -> n=21250 uncovered, 100M shortfall`); home control builder must branch strictly on hashed machine-readable policy and fail closed on unknown/uncovered actions.
- **Read-only Phase 1 prep completed:** Fetched `origin/forge6.5` (`fe3d86afee`), read `README.txt`, `LOOP_OPTIONS.txt`, `FINAL_PLAN.md` (R1–R6, W1–W16, addendum `A16`–`A26`, `N17`–`N23`), `clock_plan.hpp`, `tm_finish.hpp`, `tm_node_share.hpp`, `uci_clock.hpp`, `nnue_v3.hpp`, `search.hpp`.
- **Cached Linux Forge binary (outside repo):** `/tmp/neon_forge_bin/forge_avx2` (`8c934216...`).

## Next actions
1. Push `17:12Z` memory refresh; watch for Fable's patches and `17:25Z` `FABLE OUT`.
2. If Fable publishes patched `clockwatch.py` / `budget.py` before `17:25Z`, audit + run Linux tests + vote immediately!
3. At `17:25Z` (`FABLE OUT`), transition immediately with Astra to Phase 1 (`17:25Z` – `21:25Z`: `debate/engine_plan/ENGINE_PLAN_8H.md`).
