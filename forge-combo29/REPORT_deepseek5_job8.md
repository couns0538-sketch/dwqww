# REPORT_deepseek5_job8 (deepseek5, 2026-11-16 UTC)

1. **What was asked**: the three harness repairs + the controls once (now including a UBSan control), then the map of the engine's shared state with one planted counter per place. **The answers: (1) H1–H6 ALL as written: H1 exit 66 / 1 log / 3 warnings; H2 exit 0 / no log / 0; H3 exit 0 / no log / 0; H4 exit 67 / 1 log / 1 ASan ERROR (and missing=1 — the halt); H5 exit 0 / no log / 0; H6 the planted signed overflow produced `runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'` in stderr (1024 bytes kept) with exit 0 — UBSan's continue-on-error, exactly the "at least one line" the job demands; (2) THE MAP: of the ten planted places, FOUR are reported from more than one thread — the history update (11,364 reports), the correction update (3,097), the stop-flag read (13, the plant only — the real flag is atomic), and the helper's first instruction (2); the SIX not reported split into "not reached at Threads 4 by design" (the lease take/give — the lease is the single-threaded path, search.cpp:2711-2713) and "reached but protected" (the hash probe/store under the TT's own synchronization and the NOTLS lease; the root hand-over happens before any helper exists; the gather sits after `helper.join()`, whose happens-before is the protection); (3) T6 and ASan T5: not reached — Part 2 was not commit-ready before minute 40.** How sure: sure of the controls (raw files per run) and of the map's four "yes" rows (14,476 reports parsed); the "no" rows' reasoning is from the code, as the job allows.
2. Step 0: the same TSan/ASan programs as job 6 (their pins verified there at 04:37:55Z; the exe sha256s unchanged; `build_flags.txt` carries each program's exact compile flags).
3. Table:

| step | done? | evidence | result |
|---|---|---|---|
| harness repairs (exit_code; run-numbered names + refuse; cmd file with args + OPTIONS; build_flags.txt) | done | ds5_job8_storms.py; cmd_H1_r1.txt…; build_flags.txt | one run = one set of files; refuse tested by a second call (refused, exit 2) |
| H1–H6 controls, each once | done | ds5j8/H*_r1_*.json + logs + stderr | all six as written (details below) |
| Part 2: the ten-counter plant + build | done | plant_map_counters.patch.txt (20 pl_ lines = 10 decls + 10 increments) | MAP2 build, pins not re-run (the plants change no behavior — TSan-exit 0 on T2 confirms the build runs) |
| T1 (the job says 50; my block default ran 200) + T2 (MultiPV 2, 100) on the map build | done | ds5j8/MAP2_r1_T1.tsan.* (818,480 lines), MAP2_r1_T2.json | T1: exit 66, 14,476 warnings; T2: exit 0, 0 warnings (the helpers never start under MultiPV — the code's comment, now measured) |
| the map table | done | map_summary.json | see section 4 |
| Part 3 (T6 hash-flip mid-search; ASan T5) | NOT done | — | the minute-40 gate passed unmet |

**The controls (H1–H6), each with exit code, log files, warnings:**

| control | exit_code | report files | warnings | as written? |
|---|---|---|---|---|
| H1 planted race, T4, 20 storms | 66 | 1 | 3 | yes |
| H2 planted race, T1, 20 storms | 0 | 0 | 0 | yes |
| H3 clean TSan, T4, 20 storms | 0 | 0 | 0 | yes |
| H4 ASan heap over-read, 5 storms | 67 | 1 | 1 (ERROR: heap-buffer-overflow … search.cpp:2144) | yes |
| H5 clean ASan+UBSan, 5 storms | 0 | 0 | 0 | yes |
| H6 UBSan signed-overflow plant, 5 storms | 0 | 0 (stderr kept) | 1 (`runtime error:` in stderr) | yes |

4. Findings — **the map of the engine's shared state** (T1, Threads 4; the thread ids restart per storm: T1 = the main thread, T2+ = helpers; full per-counter thread-set counts in map_summary.json):

| structure | plant site (file:line) | reported from 2+ threads | threads seen | what protects the REAL data |
|---|---|---|---|---|
| hash table probe | src/search.cpp:1441 (`++pl_hashprobe` after the probe) | **no** | — | reached every node; the TT's own access control (the ExclusiveLease/sharded TT machinery, include/forge/search.hpp + search.cpp:316-345) — no race to report |
| hash table store | src/search.cpp:1544 | **no** | — | same TT protection |
| lease taken | src/search.cpp:335 (ctor end) | **no** | — | NOT REACHED at Threads 4: the lease is taken only when `single_threaded` (search.cpp:2711-2713) — single-thread by design |
| lease given back | src/search.cpp:340 (dtor) | **no** | — | same as above |
| start of a helper | src/search.cpp:2758 (the lambda's first line) | **yes** | T2 vs T3 / T3 vs T4 (2 reports) | the counter itself; the real hand-over state is captured before the thread exists |
| hand-over of the root move list | src/search.cpp:2761 (before the main worker's search) | **no** | — | the captured objects are not written after the spawn; the later join re-syncs |
| gathering at search end | src/search.cpp:2766 (after `helper.join()`) | **no** | — | the join itself is the synchronization (happens-before) |
| history tables update | src/search.cpp:247 (`apply_history` top) | **YES — 11,364 reports** | helper pairs in every storm (T38/T39, T299/T300, T255/T256, …) | **nothing: the quiet/capture/threat history tables are written by helper threads with no lock and no atomic — a race on real data, present in every multi-thread search** |
| correction history update | src/search.cpp:1230 (`update_correction` top) | **YES — 3,097 reports** | helper pairs + main | **nothing: the correction tables are written concurrently by helpers — a race on real data** |
| stop-flag read | src/search.cpp:1290 (after the `shared_.stop.load` in `should_stop_with`) | **yes (13)** | pairs including T1 | the PLANT races (a plain int); the REAL flag is `std::atomic` (`shared_.stop`, load/store with explicit orderings at search.cpp:2762-2765) — the race is the plant's, not the engine's |

- The two "nothing" rows are the finding of the job: **`apply_history` (search.cpp:246) and `update_correction` (search.cpp:1229) write shared evaluation-history tables from every helper thread with no synchronization.** Whether they hurt strength is not measured here (the classic argument is lost updates of small bonuses; the strength effect is usually small — that claim needs a match, not a code read). The two places are exactly the "history" family the current helper jobs (pawn history, continuation history) keep EXTENDING — every new table added there inherits the same unprotected concurrent writes.
- A counter never reported is not proof of single-threadedness: for the six "no" rows the reach/protection statement above is from the code; the counter VALUES were not read post-mortem (the process exited before any dump — a next-run improvement would print the counters at `quit` under a debug option).

5. From my partner
glmflash5 (cursor/glmflash5-work-cb5c): read its notes + REPORT list at the step-A check before this job; its new lesson (the unknown-option reply line, and quoting an option's build flags with every known number) is applied HERE: the H-blocks' setoptions are all in the engines' `uci` lists (verified in job 1's option dump) and `build_flags.txt` now ships with every sanitized number. kimi5: its job-3 prediction (the dead `break` lines at 2421/2429) — I read the lines and agree it is right; no measurement from me on it (its file, its job).
6. What I did NOT do: Part 3 (T6's setoption-mid-search storms and the ASan T5 block) — the minute-40 gate passed unmet; the counter VALUES at exit (no dump path); the storm at Threads 8.
7. What I am NOT sure about: whether the two unprotected updates' effect on strength is zero (the benign-race argument is plausible and unmeasured); whether TSan's report TRUNCATION hid more races (the log is 818k lines; TSan deduplicates — the per-counter counts are of UNIQUE interleavings, not of all events); whether `apply_history`'s races can corrupt an entry beyond a lost update (int16 saturation wraps? — not analyzed).
8. A better way: the map's method (one named counter per place, one TSan run, parse `Location is global`) is cheap and reusable — the natural extension is to plant the counters as ATOMICS in one build and as plain ints in another: the plain build's reports name the racing places, the atomic build's zero confirms the protection claim per place. Two builds, one run each.
9. times: see stamps.txt
10. Model: deepseek5 — DeepSeek (the model serving this cloud-agent run).
