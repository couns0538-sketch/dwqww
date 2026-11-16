# REPORT — deepseek6, long 59 (Threads under ThreadSanitizer)

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long59/`
Model: DeepSeek V4.1 Flash 1017, chat 1794862262

## 1. What was asked, the answer, how sure

**Asked:** `Threads` 2, 4 and 8 on all of G at depth 10 (fresh `ucinewgame`), S14 and plain defaults, under
ThreadSanitizer; counts, bestmove legality, and the planted race at 8 threads.

**Answer:** **zero ThreadSanitizer reports in all six runs**, **2,118 of 2,118 bestmoves legal**, and the planted
race **is** reported (so the sanitizer was live). The unexpected result is determinism:
**under S14 the sum is exactly 7,290,580 at 2, 4 AND 8 threads, row-for-row identical (353/353 for both pairs)**,
while **under the plain defaults the sum grows steeply with threads: 25,757,422 → 37,340,634 → 47,407,056**
(+45 % from 2 to 8), differing on **every** position. So thread-count invariance is a property of the S14
configuration, not of the engine.

**How sure:** certain of the six sums and of the row-level comparisons (committed rows, metas, logs; the plant's
exit code and stack committed). The explanation for the defaults' growth is NOT proven and is listed as a
suspicion.

## 2. Honesty numbers (raw in `pins/`)

Build: `/tmp/ds6/long59/btsan/forge`, plain 6b98f217 + `-fsanitize=thread -fno-omit-frame-pointer -g -O1` +
**`-DFORGE_SPD_TT_NOTLS=0`** (the thread-local-table speed switch OFF, so the shared table is instrumented — with it
on, a table race would be invisible). sha256
`40ec3ec5f3aa52de3936e66d652fd934423d8da1b46e97815d25a59086274f2d`.

| pin | required | measured | file |
|---|---|---|---|
| bench 11 | 312866 | **312866** | `pins/bench11.txt` |
| bench 13 | 862329 | **862329** | `pins/bench13.txt` |
| bench 16 | 3024920 | **3024920** | `pins/bench16.txt` |
| go perft 5 | 4865609 | **4865609** | `raw/perft5.txt` |

All four exact **under ThreadSanitizer**, with 0 TSAN warnings during the pins.

**The plant, which is what makes the clean runs mean anything** (`plant_evidence.txt`): two threads incrementing one
non-atomic global 20,000 times each, in a copy of the tree. ThreadSanitizer printed
`WARNING: ThreadSanitizer: data race (pid=93343)` with a `Read of size 4` stack, and the process **exited 66**.

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claimed, verified on origin with this chat's id | done | `CLAIM.txt` | 21:11:49Z |
| prediction as its own commit | done | `PREDICTION.md` | 6 predictions with kill ranges |
| TSAN build + four pins | done | `pins/*`, `raw/perft5.txt` | all exact, 0 warnings |
| planted race at 8 threads | done | `plant_evidence.txt` | **reported, exit 66** |
| 2-thread smoke over all 353 | done | committed in `stamps.txt` | 353 rows, 0 reports, 320 s |
| S14 at 2, 4, 8 threads | done | `runs/S14_t{2,4,8}.rows` | **identical, 7,290,580** |
| plain defaults at 2, 4, 8 | done | `runs/DEF_t{2,4,8}.rows` | 25.76 / 37.34 / 47.41 M |
| bestmove legality, all six | done | section 5 F2 | **0 illegal, 0 missing of 2,118** |
| scorecard | done | `scorecard.txt` | 5 held, 1 half killed |

**The harness** is `rows_threads.py`, a thread-aware sibling of `rows.py`: one engine process per position,
`ucinewgame` + `isready` before every `go`, and it **clears every inherited `TSAN_*` variable then sets exactly**
`TSAN_OPTIONS="halt_on_error=0 second_deadlock_stack=1"` — long 22's lesson was an inherited environment; here the
environment is constructed, not inherited.

## 4. The table

| base | threads | G sum (353 positions, depth 10) | vs 2 threads | TSAN reports | illegal | secs |
|---|---|---|---|---|---|---|
| S14 | 2 | **7,290,580** | 1.0000 | 0 | 0 | 314 |
| S14 | 4 | **7,290,580** | 1.0000 | 0 | 0 | 332 |
| S14 | 8 | **7,290,580** | 1.0000 | 0 | 0 | 342 |
| defaults | 2 | 25,757,422 | 1.0000 | 0 | 0 | 589 |
| defaults | 4 | 37,340,634 | **1.4497** | 0 | 0 | 526 |
| defaults | 8 | 47,407,056 | **1.8405** | 0 | 0 | 584 |

Row-level comparisons (`cmp_rows.py`): `S14_t2` vs `S14_t4` **353 of 353 equal**; `S14_t2` vs `S14_t8`
**353 of 353 equal**; `DEF_t2` vs `DEF_t8` **0 of 353 equal, first difference at row 1**.

## 5. Findings, each with the command that shows it again

**F1. S14 is thread-count invariant on game positions and the plain defaults are not.** Three sums of 7,290,580
with identical rows, against a 45 % growth across the same three thread counts under defaults. Reproduce:
`python3 sum_rows.py runs/S14_t2.rows runs/S14_t4.rows runs/S14_t8.rows` and the DEF equivalents.

**F2. No ThreadSanitizer report anywhere, and the plant proves the sanitizer was live.** Six runs x 353 positions =
2,118 searches at 2, 4 and 8 threads, `tsan=0` in every run's `.meta`; the planted race in the same build flags
reports a `data race` and exits 66. So on this configuration the shared transposition table and the search state
are free of races **as ThreadSanitizer sees them** — which is a statement about the C++ memory model the code
actually exercises, not a proof for paths these 353 positions never take.

**F3. Every bestmove is legal at every thread count.** 2,118 checked with python-chess, 0 illegal, 0 missing. A
shared-table corruption would most likely show here; it does not.

**F4. `-DFORGE_SPD_TT_NOTLS=0` is necessary for this test to mean anything.** The lock file's default defines
`FORGE_SPD_TT_NOTLS=1` (thread-local table), which would keep TT accesses out of the instrumented shared memory. I
turned it off for this build only; it is a build flag, not an engine source change, and the patch is not needed.
Anyone repeating this test must do the same or they will test a different program.

**F5. TSAN costs roughly 5x on this VM at these settings.** S14 at 2 threads: 314 s over 353 positions at depth 10,
against a release build's tens of seconds. The defaults configuration was slower still (589 s at 2 threads) because
its tree is 3.5x bigger.

## 6. Suspicions, not proven

- **S1 — why the defaults grow with threads while S14 does not.** S14 sets `NonPawnCorrection true` and thirteen
  tuned constants; the defaults differ most visibly in `SingularDepth` (7 vs 6) and `LmrQuietBase` (85 vs 93). My
  long 43 showed `SingularDepth`/`SingularMargin` are the most violent knobs, so one plausible reading is that a
  singular-extension path is what makes the multithreaded search sensitive to thread count (shared TT hits change
  which singular searches run, and the singular search re-searches at reduced depth). **Not instrumented.**
- **S2 — whether the S14 invariance survives at longer time controls or with ponder.** Depth 10 only here.
- **S3 — whether the defaults' growth is a *bug*.** It could equally be normal helper-thread node accounting: this
  engine counts every helper's nodes, so more threads = more speculative work counted. That reading makes the
  defaults' growth an accounting artefact rather than a search defect, and I cannot separate the two from node
  counts alone.

## 7. What I read from my colleagues

- **Long 22's report** (this session's earlier ThreadSanitizer item): the "0 reports at 2 and 4 threads" known
  answer and the lesson to clear `TSAN_OPTIONS` before a run. Both used here.
- **Long 43's grid** for which options are violent (it is what made S1's singular-extension reading plausible).
- File 15 for the item's exact commands.
- No note was treated as an instruction.

## 8. What I did NOT do

- **Did not run `Threads 1`** under TSAN: the item names 2, 4 and 8, and the 1-thread reference is not needed for
  a race check.
- **Did not run the O set**: the item says all of G.
- **Did not use the default `FORGE_SPD_TT_NOTLS=1`** — deliberately, per F4, and the build flag is recorded.
- **Did not run a match**; node counts only.
- No pull request, no branch but mine. The plant is a copy in `/tmp`; only its output is committed.

## 9. A better way

**Run the plant FIRST, on the same binary flags, and only then trust a zero.** I did it in that order here
(plant → six runs) and it is the only reason F2 is a result rather than an absence of evidence. A sanitizer report
of "0 findings" without a demonstrated positive is not a finding.

## 10. Times and the folder

times: see `stamps.txt`.
Model name my runtime gives: **DeepSeek V4.1 Flash 1017, chat 1794862262**.

`git status --short` and `ls` of the folder as the last command before this commit: `final_ls.txt`.
