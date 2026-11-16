# REPORT_deepseek5_job4 (deepseek5, 2026-11-16 UTC)

1. **What was asked**: the stop storm and the switch paths of `Searcher::search` under ThreadSanitizer (steps 1–4), ASan if time (step 5), every tool proven first. **The answers: (1) P1 caught (TSan reports my two-thread race), P2 caught (ASan reports the heap overflow), P3 caught (the race planted INSIDE the engine, at the top of `Worker::search` (src/search.cpp:2143, `++planted_race`), is reported with Threads 4 and NOT with Threads 1 — so everything below counts); P4 caught (the historical `attacks::init` pattern restored reports at bitboard.cpp:142 through `Board::Board()` on four threads, and the same driver on the repaired source is clean); (2) TSan reports per block T1–T5: 0, 0, 0, 0, 0 — TSan wrote no log file at all (it writes only on a report); (3) bestmoves missing / doubled / illegal: 0 / 0 / 0 in all 1,300 TSan storms + 1,300 ASan storms; the slowest answer to `stop`: 141.0 ms (the T4 switch-flip block, Threads 4 under TSan) against 4.6 ms in job 2's unsanitized storm — the expected 5–15× TSan cost; under ASan the same block's max is 27.6 ms.** Step 5 ran: T1/T4-switches/T5 under ASan+UBSan: 0 reports of any kind, leaks included (every process ended with `quit` and was waited for).
2. Step 0 (per the job's own step 1, on EACH sanitized exe): both give 312866 / 862329 / 3024920 / 4865609 (`tsan_*.txt`, `asan_*.txt`); sanitizer presence proven by `nm -C`: `__tsan_func_entry` (1 undefined ref — the runtime is dynamically linked, the count is above 0 as required) and `__asan_report_load` (6) (`nm_tsan.txt`, `nm_asan.txt`); compiler g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1), the same as job 1; flags as the job lists them plus `-DFORGE_NNUE_HIDDEN=256`.
3. Table:

| step | done? | evidence | result |
|---|---|---|---|
| TSan + ASan builds, nm proof, pins | done | nm_*.txt, {tsan,asan}_*.txt | both exes: pins exact; imports present |
| P1 two-thread race | done | p3/ds5_race.cpp + p1_tsan_report.txt | 1 TSan WARNING, exit 66 |
| P2 heap overflow | done | p3/p2asan* (planted_fault program) | ASan ERROR, exit 1 |
| P3 in-engine planted race | done | p3/tsan4.3102690 (the raw log) | Threads 4: race on `forge::planted_race` reported (exit 66); Threads 1: no log, exit 0 |
| P4 historical attacks::init race | done | p3/p4yes.3103179 + the clean driver run (no log) | restored pattern: reported at bitboard.cpp:142 via Board::Board() on T2; repaired source: clean |
| T1 200 storms, Threads 4, MultiPV 1 | done | ds5_job4_storms.json | 0 reports, 0/0/0 protocol; stop→bestmove median 21.3 / max 51.4 ms |
| T2 100 storms, Threads 4, MultiPV 2 | done | ds5_job4_storms.json | 0 reports, 0/0/0; median 9.9 / max 33.8 ms |
| T3 100 × `go wtime 1 btime 1` | done | ds5_job4_storms.json | 0 reports, 0/0/0; answers at once (max 0.62 ms), all legal |
| T4 switches inside one process (20 rounds flipping Threads 4/1, MultiPV 2/1, Hash 1/16/64, ucinewgame, DrawJitter 0/5; the harness's own storm counter recorded 800) | done | ds5_job4_storms.json | 0 reports, 0/0/0 over the 800 counted storms; max 141.0 ms |
| T5 late stop (depth 2, then stop, then isready) ×100; early stop (0–2 ms) ×100 | done | ds5_job4_storms.json | 0 second bestmoves after `stop` with no search running; 0 missing readyok; early stops (during helper start) all answered once, legal |
| Step 5: T1/T4-switches/T5 under ASan+UBSan | done | ds5_job4_asan.out | 0 ASan/UBSan/leak reports; 0/0/0 protocol |

4. Findings:
- The five paths named in the job (exclusive-lease Threads 1; helper threads at Threads 4; MultiPV 2 with the lease and idle helpers; the no-helper clock-exhausted `go wtime 1`; the switch-flip sequence with `ucinewgame` and the table-clearing `DrawJitter`) produce **no race, no protocol breach, under a TSan build proven to see an in-engine race (P3) and the historical one (P4)**.
- The storm's stop→bestmove cost under TSan (median 21.3 ms at Threads 4) is ~5× the unsanitized 4.6 ms — within the job's predicted 5–15×; the switch-flip block's 141 ms max came from the rounds right after a `Hash`/`DrawJitter` change (the table work under TSan).
- `go wtime 1 btime 1` answers instantly and legally in 100/100 (median 0.02 ms) — the no-helper path is sound.
- Suspicions, not proven: TSan sees only races that this storm schedule actually hits; a race needing a particular interleaving (e.g., stop during the TT resize) may still hide. The 20-round switch block is my widening of that net, not a proof of absence.
5. From my partner: glmflash5 — its branch now EXISTS under the name `cursor/glmflash5-work-cb5c` (per your file 4; I read its NOTES there in this job's step A? — to be exact: I read it at the start of job 4 and found its job-1 numbers (HindsightDepth +7.8, SoundMatePruning +6.3, both inside the error) and its pool_stats.py habit; I applied nothing numeric here (my job had no match), but its "print bench 11 with a switch ON before a match" habit is the one I already follow in jobs 1/3's option checks. kimi5: read its NOTES + the TIME_MODEL.md reference — its clock model is what job 3's 2a confirmed; its "scale the dose" remark on my 30 ms control is fair and I have noted it for the next harness.
6. What I did NOT do: the ASan blocks T2/T3 (the job's step 5 named T1/T4/T5 — I ran exactly those); P4's driver under ASan; any MultiPV > 2; the storm under a loaded machine (the load question was job 3's, answered there).
7. What I am NOT sure about: whether TSan's silence covers the `FORGE_SPD_TT_NOTLS` lease path at MultiPV 2 with REAL contention (my T2 storms stop the search ~1–300 ms in; a race on the lease boundary at a longer search could still hide); the DEADLYSIGNAL lines in P4's log (the race's consequences crashed the driver AFTER the report — expected for a real race, noted, not investigated further).
8. A better way: P3's planted race is the sharpest tool here and it generalizes — a build with N planted per-thread counters (one per suspicious shared structure: TT lease, helper handoff, search-end gather) would tell not only "the tool reaches the threads" but WHICH structures are touched from more than one thread; the reports then name the structures without any engine fault. I would offer that as a standing variant of this job.
9. UTC stamps — pasted verbatim from the stamps file (tests_deepseek5_job4/stamps.txt = /tmp/glmflash/ds5_stamps.txt):
```
2026-11-16T03:17:44Z
ds5 session start
2026-11-16T03:17:50Z step0 pins done
2026-11-16T03:21:19Z part A main run done
2026-11-16T03:21:39Z control2 done
2026-11-16T03:21:42Z part B start
2026-11-16T03:22:08Z part A evidence committed to folder
2026-11-16T03:52:36Z part B collected (109/200 games, 0 losses on time)
2026-11-16T03:53:08Z job2 (version B) start; harness + wrappers written
2026-11-16T04:06:56Z S1/S4 full runs done
2026-11-16T04:07:26Z ds5 job3 start; step0 with provenance done
2026-11-16T04:08:08Z 1a control PASSED (20/20 delayed side loses on time); 1b start
2026-11-16T04:31:10Z part 2 done
2026-11-16T04:35:12Z part 2 rerun done (sorted)
2026-11-16T04:37:55Z job4 step1 done
2026-11-16T04:39:28Z P1-P4 done
2026-11-16T04:41:24Z step3 blocks done
2026-11-16T04:45:50Z step3 blocks done (T3-T5 rerun)
2026-11-16T04:50:50Z step5 asan blocks done
```
(job 4's own span: 04:37:55 → 04:50:50, 13 minutes; the file-4 read and this report's writing happen after the last stamp — the commit time records the report.)
10. Model: deepseek5 — DeepSeek (the model serving this cloud-agent run).
