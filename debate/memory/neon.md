# Neon Memory (8h Continuation — Phase 1: Engine Plan & Later Stages)

Updated: 2026-11-23T17:25:17Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra edits on `origin/debate/server-plan-20261123-astra`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** Fable left at `001806Z` (`FABLE OUT`).
  - **`FORMATS.md` 2.9** (`ac566296`) & **`SETUP_PLAN.md` 2.7** (`4100b2a5`): **3/3 AGREED**.
  - **7 of 9 published `scripts_v2/` files now have 3/3 `YES`:** `run/engine_lines.py` (`a82eb9c8`), `run/uciproc.py` (`7de2728a`), `tests/test_uciproc.py` (`690b3243`), `run/record.py` (`bc71fa89`), `tests/test_record.py` (`a8e16021`), **`tools/budget.py` v7 (`76817bad`)**, **`tests/test_budget.py` (`52ef5a14`)**.
  - **2 files `NOT YET` (routed to Opus):** `run/clockwatch.py` v4 (`d21930a1`) & `tests/test_clockwatch.py` (`507883ba`) — 102/102 + 13/13 plants + Linux `pidfd=1200/2048` `select.poll()` PASS, but `Watch._run` lines 305–315 exception path drops `stop()` error and never verifies `gone()`, leaving child live past `D` (`alarm=None`).
- **ACTIVE NOW — Phase 1 (Hours 1–4, `17:25Z` – `21:25Z`): ENGINE PLAN + LATER STAGES.**
  - Deliverable by `21:25Z` on Astra's branch: `debate/engine_plan/ENGINE_PLAN_8H.md` + `AGREE <sha256> neon ENGINE_PLAN_8H.md` (Fable checks once at `21:55Z`).
  - Required contents: (1) agreed addendum entries in addendum form, (2) "Later stages" with **MEASURED triggers** vs wishes, exact work, judging rules, machine-time costs, (3) open items with both sides.
  - Sources: `debate/FINAL_PLAN.md`, `debate/PLAN.md`, `debate/BOARD.md`, `debate/evidence/`, `origin/forge6.5` (`fe3d86afee`).
- **UP NEXT — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN.**
  - Audit/vote Opus `scripts_v2/` drops, write/verify `debate/server_day/specs/` (including `171134Z`, `171332Z`, `172109Z`), ordered rehearsal + measurements (`171712Z`, `172415Z`), plain-words `debate/server_day/FINAL_FOR_THE_OWNER.md` + `AGREE` (Fable checks once at `01:55Z`). Deliver final plain-words summary to user at `01:25Z`.
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Next actions (Phase 1, `17:25Z` – `21:25Z`)
1. Push `172517Z` votes & Phase 1 start message.
2. Coordinate with Astra on Phase 1 scope & structure for `debate/engine_plan/ENGINE_PLAN_8H.md`.
3. Deep-audit `origin/forge6.5` + `FINAL_PLAN.md` / `PLAN.md` / `BOARD.md` + run live compiled Linux `forge6.5` measurements (outside repo, under `/tmp/`) on every later-stage bottleneck:
   - Single-opponent gate leveling off / opponent cycling -> pool/gauntlet/SPRT gate replacement & measured triggers
   - Fixed-depth 2,000-node self-play saturation (draw rate, opening diversity, ply/score distributions, mixed/staged depth, adjudication)
   - Yardstick ceiling (SF ladder beyond SF11, UHO saturation, clock/hash scaling)
   - Labels & teacher ceiling (what happens once Forge beats its teacher net, WDL/score blend, 6-piece TB rescoring, stale vs fresh data mix)
   - Window outgrowing a single card (4B–10B+ positions, replay-window mixing/forgetting, multi-GPU DDP / gradient-accumulation equivalence, storage/IO throughput)
   - Time management (deep audit of `forge6.5` `search.cpp` / `clock_plan.hpp` / `tm_finish.hpp` / `tm_node_share.hpp` beyond `N19`: sudden death, `movestogo`, `ponderhit`, `TmNodeShare` bugs/interactions)
   - Tablebases (5-piece vs 6-piece Syzygy at tournament clocks, root vs in-search probe depth/limit, SMP NVMe contention, TB relabelling)
   - Deeper tuner & dormant `forge6.5` search switches (`search.hpp` has ~18 dormant flags!) + SPSA variance/cost at 60k–250k nodes + SMP scaling beyond 4 threads.
