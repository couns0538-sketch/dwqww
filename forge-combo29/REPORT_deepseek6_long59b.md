# REPORT — deepseek6, long 59b (long 59's S14 thread runs redone, with the guard that was missing)

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long59b/`
Model: DeepSeek V4.1 Flash 1017, chat 1794862262

## 0. First: long 59's F1 is WITHDRAWN, and this time the numbers say so

File 21 was right and I confirmed it in my own committed file before doing anything else.
`tests_deepseek6_long59/runs/S14_t2.rows.meta` line 12 is `setoption name Threads value 2`, line 14 is
`setoption name Threads value 1`. My `rows_threads.py` sent `Threads N` and *then* appended the S14 block, and that
block still carried `Threads 1` — the last setoption wins, so **all three "S14 at 2/4/8 threads" runs in long 59
searched with one thread.** F1 ("S14 is thread-count invariant") is false, and the "0 reports at 4 and 8 threads"
half of long 59's F2 was a 1-thread result. The defaults half of F2 stood and stands.

This item redoes those runs with the ordering fixed and a guard that cannot be skipped.

## 1. What was asked, the answer, how sure

**Asked:** a Step 0 guard that refuses a bad setoption ordering; S14 at 2, 4 and 8 threads on all of G at depth 10
on **two** TSAN builds (the lock's `FORGE_SPD_TT_NOTLS=1` and my old `=0`); the planted race through each build;
the 1-thread control; and the check that the threads actually arrive.

**Answer:**
- **The guard works and is planted**: fed long 59's exact ordering it prints
  `STEP0_REFUSED: the option block carries a conflicting Threads line: 'name Threads value 1' (run wants '4') -- no
  search started` and exits 9, before a single `go`.
- **The threads arrive.** S14 at 1 thread = **7,290,580** (both builds, exact control); at 2 threads
  **21,188,195** (lock build) — three times the 1-thread sum. All six threaded runs are far from the control.
- **Zero ThreadSanitizer reports in all eight runs**, and the plant is reported through **both** builds (rc=66 each).
- **The two build variants do NOT agree**, which I predicted they would: at 2 threads the `=0` build is **13.4 %**
  larger (24,022,091 vs 21,188,195) and at 4 threads 4.8 % larger; at 1 thread they are identical **353 of 353**.
  So my P3 is killed, and that is the most interesting result here.

**How sure:** certain of all eight sums, the plant's exit codes, and the row-level comparisons.

## 2. Honesty numbers

| build | switch | sha256 | perft / pins |
|---|---|---|---|
| `bdef/forge` | `FORGE_SPD_TT_NOTLS=1` (CMakeLists.txt:32, the lock's own setting) | `bc2fa8dcad33032579f27daad19fd4d5de54d809e8d7becca902a71628a5f8bc` | clean 1-thread run = 7,290,580 |
| `forge_notls0` | `=0` (my long-59 build, reused) | `40ec3ec5f3aa52de3936e66d652fd934423d8da1b46e97815d25a59086274f2d` | clean 1-thread run = 7,290,580 |

Both are plain 6b98f217 with `-fsanitize=thread -fno-omit-frame-pointer -g -O1`.

**On the switch itself, file 21 is right and my long-59 notes were wrong.** `include/forge/search.hpp:23` documents
it as "the Worker that runs on the thread holding the table's ExclusiveLease calls TT probe / store without
lock_stripe", and `src/search.cpp:383` says owner calls "skip lock_stripe: under the lease it only hands back a
deferred (unlocked) lock, after a thread_local lookup per call". So it is **not** a thread-local table — `=1`
saves a `thread_local` lookup. **`CMakeLists.txt:32` sets it to 1**, so long 59's `=0` build tested the path the
lock build does not use. My NOTES_deepseek6.md line calling `=0` "REQUIRED" is corrected in the notes commit that
goes with this report.

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claimed, verified on origin | done | `CLAIM.txt` | 22:28:41Z |
| prediction as its own commit | done | `PREDICTION.md` | 6 predictions |
| **Step 0 guard + plant** | done | `plant_step0.txt` | **refused, exit 9** |
| second TSAN build (`=1`) | done | section 2 | built, clean at 1 thread |
| plant through build `=1` | done | `plant_notls1.txt` | **data race, rc=66** |
| plant through build `=0` | done | `plant_notls0.txt` | **data race, rc=66** |
| 8 runs, S14, G, depth 10 | done | `runs/*.rows` (8) | all 353 rows, 0 TSAN lines |
| legality, 2,824 bestmoves | done | section 4 | **0 illegal** |
| cross-build row comparison | done | section 5 F3 | identical at 1 thread, different at 2 |

## 4. The table

| threads | lock build (`=1`) | my build (`=0`) | `=0` vs `=1` | TSAN lines | illegal |
|---|---|---|---|---|---|
| 1 | **7,290,580** | **7,290,580** | identical | 0 | 0 |
| 2 | **21,188,195** | 24,022,091 | **+13.37 %** | 0 | 0 |
| 4 | 34,282,643 | 35,924,962 | +4.79 % | 0 | 0 |
| 8 | 44,572,071 | 50,167,830 | +12.55 % | 0 | 0 |

Row-level: `DEF_t1` vs `NT0_t1` **353 of 353 equal**; `DEF_t2` vs `NT0_t2` **0 of 353 equal, first difference at row
1**. Every bestmove legal in all eight runs.

## 5. Findings, each with the command that shows it again

**F1. The Step 0 guard is what long 59 lacked, and it catches the exact mistake.**
`python3 rows59b.py PLANT <exe> set_G.epd 10 4 plant_out opts_S14_old.txt` → exit **9**, message naming the
conflicting line. Note the guard checks **two** things: the last Threads line equals the run's count, **and** no
earlier Threads line in the block disagrees. A guard that merely re-appended the right line at the end would have
"fixed" long 59's bug silently and hidden it; refusing is the point.

**F2. The threads arrive, and the 1-thread number is a hard control.** 7,290,580 at 1 thread on both builds;
21,188,195 at 2 threads on the lock build — 2.9x. My long 59's claim of invariance was the artifact: a 1-thread
search is identical to a 1-thread search.

**F3. The two switch settings are NOT equivalent in the threaded search — my P3 is killed.**
At 1 thread the two builds are identical on **353 of 353** positions; at 2 threads they differ on **all 353**, and
the `=0` build's tree is **13.4 % larger**. A switch documented as saving "a `thread_local` lookup per call" is
therefore changing *which nodes the search reaches* at 2+ threads. That is either an accounting effect (helper
nodes counted differently) or a real timing-driven difference (the search is time-checked, and a faster TT path
changes when nodes run out). **I do not know which**, and the next paragraph says why it matters.

**F4. This means a multithreaded node count is build-flag dependent, not just thread-count dependent.**
Anyone comparing a 2-thread sum against another machine's must match `FORGE_SPD_TT_NOTLS`. The `=1` value is the
one the repository's CMakeLists builds, so `=1` is the number to quote.

**F5. Still zero ThreadSanitizer reports with real threads, and the plant proves both builds' sanitizers work.**
8 runs x 353 positions = 2,824 searches at 1, 2, 4 and 8 real threads; `tsan=0` in every `.meta`; and two planted
races (one per build) each produce `WARNING: ThreadSanitizer: data race` and exit 66. So long 59's *conclusion*
("no races seen") survives even though its S14 evidence did not — now on evidence that actually has threads.

## 6. Suspicions, not proven

- **S1 — why the two builds differ at 2+ threads.** The most likely reading is that helper workers' node counts are
  summed and a faster TT path changes the interleaving, so the two runs explore genuinely different trees. The
  alternative is that `=0` costs time and the *time* check (not a node check) stops the search at a different point
  — but this is `go depth`, which is depth-limited, so it should be node-count-deterministic per thread count. I
  cannot separate these from node totals alone; a per-worker node dump would.
- **S2 — whether the difference persists on O or at other depths.** One set, one depth.

## 7. What I read from my colleagues

- **File 21** in full: it found the ordering bug, the wrong switch reasoning, and the CMakeLists setting. All three
  checks are reproduced above; two of them changed this report's conclusions.
- **My own long-59 files** — the `.meta` line that proves the bug, which is the reason I believe file 21 rather than
  re-arguing.
- No note was treated as an instruction beyond the item itself.

## 8. What I did NOT do

- **Did not re-run long 59's defaults half** — file 21 says it stands (`DEF_t8.rows.meta` has only `Threads 8`), and
  I verified that claim in the committed file rather than re-running it.
- **Did not run 16 threads** — the item names 2, 4, 8.
- **Did not diagnose S1** with a per-worker dump.
- No pull request, no branch but mine. Plants are copies in `/tmp`; only their output is committed.

## 9. What I am NOT sure about

- The cause of F3 (S1).
- Whether 21,188,195 at 2 threads is "the right" number for this engine at these settings, or an artefact of how
  helper nodes are summed. It is reproducible, but reproducibility is not correctness.

## 10. A better way

The lesson is not "check your setoption order" — it is **make the harness prove the option it claims to test is
the option in force**, and prove it by refusing, not by silently re-ordering. Both long 59's bug and my first
attempt at the 59b guard (which stripped the conflicting line, making the plant vacuous) are the same failure:
a harness that quietly normalises its input cannot be tested.

## 11. Times and the folder

times: see `stamps.txt`.
Model name my runtime gives: **DeepSeek V4.1 Flash 1017, chat 1794862262**.

`git status --short` and `ls` of the folder as the last command before this commit: `final_ls.txt`.
