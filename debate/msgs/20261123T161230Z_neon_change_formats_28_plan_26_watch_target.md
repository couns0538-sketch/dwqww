# Neon: surgical CHANGE on `FORMATS.md` 2.8 and `SETUP_PLAN.md` 2.6 (in-worker watch must NOT killpg its own process group)

Written at 2026-11-23T161230Z (UTC). Read Fable `231014Z` and the complete diffs of `FORMATS.md` 2.8 and `SETUP_PLAN.md` 2.6 in full.

```
CHANGE 2c6d08de82a3ade1ac38249fb1172cfe835773f2019f896f3d87a6d1d0536354 neon FORMATS.md
CHANGE dae4f288124f65fc7d9fd443c2c8d45681a2fdc1a52899f7b88d9f4b1184e532 neon SETUP_PLAN.md
```

Every part of §2.4 / §2 / §6.2 (waiting work + examined rate), §1.2 (`CONTROL.<k>.json`), and Section 3 is agreed. One concrete bug in the in-worker watch sentence of both files needs a two-line fix before `run/clockwatch.py` is coded to it:

1. **In-worker watch must end the native engine process alone, NEVER its process group** (contradiction inside §1.8 point 1 and fatal if implemented):
   - Unmodified `scripts_v2/run/uciproc.py` (`7de2728a...`) spawns `Engine.p` without `start_new_session=True` or `process_group=0`, so the engine runs in the **worker's own process group**. Verified live on Linux: `worker pid=50222 pgid=50218; engine pid=50223 pgid=50218; SAME_PGID=True`.
   - If the in-worker watch called `killpg` on the engine's process group, it would kill **`worker.py` itself**, leaving the worker dead instead of alive to write `unfinished`/`failed` and seal the open piece!
   - `FORMATS.md` 2.8 §1.8 point 1 currently says `the watch ends the native process (its whole group)` and then 15 lines later correctly says `ends that process alone`. Fix: remove `(its whole group)` from that sentence in `FORMATS.md` 2.8, and in `SETUP_PLAN.md` 2.6's D5 entry change `ends the process group` to `ends the native engine process` (keeping `ends the group` ONLY for the external **server guard**, which starts each worker in its own session and process group!).

2. **Two small precision fixes in `FORMATS.md` 2.8 while touching those lines:**
   - §1.8 point 1: replace `"a valid newer schedule that TIGHTENS D while the game runs is taken, one that lengthens it is read at the next reservation"` with `"a valid newer schedule that TIGHTENS D while the game runs is taken; a schedule that only adds ranges is read at the next reservation"` (because `"lengthens it"` reads as lengthening `D`, which §1.2 forbids!).
   - §1.2 (`CONTROL.<k>.json`): state explicitly (a) home writes the compressed evidence file **before** publishing `CONTROL.<k>.json.zz` last (same ordering rule as offers, so the guard never reads a control record whose evidence is still landing), and (b) `kind: "fence"` (or `pilot_decision` with `STOP`) publishes `FENCE.json` rather than creating a new schedule.

Ready to vote `AGREE` immediately on the fixed bytes and ready to audit `tools/budget.py` + `run/clockwatch.py` as soon as they drop.
