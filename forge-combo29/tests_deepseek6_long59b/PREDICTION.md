# deepseek6 long 59b — PREDICTION (written before the first run of this redo)

Item (file 21): redo long 59's S14 thread runs, which were **invalid**: my harness sent `Threads N` and then the
S14 option block, and that block still contained `Threads 1` — so all three "S14 at 2/4/8 threads" runs searched
with **one** thread. File 21 also corrects my claim about the build switch.

Model: DeepSeek V4.1 Flash 1017, chat 1794862262. Time: `stamps.txt`.

## What I got wrong in long 59, verified in my own committed files before this redo

1. **The S14 thread runs were 1-thread runs.** `runs/S14_t4.rows.meta` line 12 is `setoption name Threads value 2`
   and line 14 is `setoption name Threads value 1`. The last `Threads` line wins. So long 59's F1 ("S14 is
   thread-count invariant") is **withdrawn**, and the "0 ThreadSanitizer reports at 4 and 8 threads" half of F2 is
   a 1-thread result. The **defaults** half of F2 stands: `DEF_t8.rows.meta` has only `Threads value 8`.
2. **I misread the build switch.** `include/forge/search.hpp:23` documents `FORGE_SPD_TT_NOTLS` as "the Worker that
   runs on the thread holding the table's ExclusiveLease calls TT probe / store without lock_stripe", and
   `src/search.cpp:383` says owner calls "skip lock_stripe: under the lease it only hands back a deferred (unlocked)
   lock, after a thread_local lookup per call". So it is **not** a thread-local table; `=1` saves a `thread_local`
   lookup per call. **CMakeLists.txt:32 sets it to 1**, so my `=0` build tested the path the lock build does not
   take. Both builds are needed for this item, which is exactly what file 21 asks for.

## Fixed now

- **Harness Step 0, unskippable**: after assembling the setoption list, assert the **LAST** `Threads` line equals
  the run's thread count and the LAST `Hash` line is 16; otherwise stop before the first `go`. Plant: feed it long
  59's old ordering (S14 block after `Threads 4`) and it must refuse; the refusal is committed.
- **Run matrix**: S14 on all of G at depth 10, S14 block FIRST and `Threads` LAST:
  | build | threads | purpose |
  |---|---|---|
  | `FORGE_SPD_TT_NOTLS=1` (the lock's build) | 1 | control, must be **7,290,580** |
  | `=1` | 2, 4, 8 | the real thread runs |
  | `=0` (my long-59 build) | 1 | control, same sum expected |
  | `=0` | 2, 4, 8 | the same thread runs on the other build |
  **8 runs** over 353 positions, plus **the planted race once through each build** (2 more).
- Everything else as long 59: `TSAN_OPTIONS="halt_on_error=0 second_deadlock_stack=1"` set explicitly, one engine
  process per position, `ucinewgame` + `isready` before every `go`, legality of every bestmove with python-chess.

## Predictions, each with the range that kills it

**P1 — the planter refuses long 59's old ordering.** Feeding the list `[..., Threads 4, S14 block containing
Threads 1]` must exit with a refusal and no search. Kill range: it proceeds → the guard is not working.

**P2 — the threads really arrive this time.** At 2, 4 and 8 threads on BOTH builds, the S14 G sums **differ from
7,290,580** and differ from each other. File 21 states this as the thing to check against "the threads did not
arrive". Kill range: any of the six runs equal to 7,290,580 → stop and report that the threads did not arrive.

**P3 — the two builds give the SAME sums at the same thread count.** They differ only in a `thread_local` lookup
per TT call, which changes speed, not the search. Kill range: any thread count where `=0` and `=1` differ → that
would mean the lookup changes the tree, which is a finding.

**P4 — still zero ThreadSanitizer reports in all eight runs, and the planted race is reported through BOTH
builds.** Kill range: any report (headline), or a plant that is not reported through one of the builds (then that
build's clean run means nothing).

**P5 — the 1-thread controls both equal 7,290,580.** Kill range: either differing → the two builds are not the same
engine, and P3 cannot be interpreted.

**P6 — budget.** Eight runs over 353 positions at depth 10 under TSAN: about 25–50 minutes, 4 at a time where the
machine allows. Kill range: over 70 minutes I report the runs done and name the rest.

## What would make me report "not done"
A control that does not equal 7,290,580, a plant not reported on either build, or the runs not finishing. In each
case the report says which half is missing and quotes no number that depends on it.
