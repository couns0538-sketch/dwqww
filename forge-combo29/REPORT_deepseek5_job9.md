# REPORT_deepseek5_job9 (deepseek5, 2026-11-16 UTC)

1. **What was asked**: the two notes corrections first (Part 0), then the four-build test that decides job 8's headline (A), then T6 + the ASan T5 (B), then job 7's Part C (C). **The answers: (1) Part 0 done — commit aaa6aaa4e ("deepseek5 notes corrected") carries both CORRECTION lines, each with the recount beside it (FI lower-depth 127/126/117 of 300, NS 90/59/57, OFF2 7/3/6; bestmove diffs FI 7/4/17, NS 3/1/5, OFF2 2/0/2 — the recount command and its output are committed as tests_deepseek5_job9/recount_job7.py/.out); (2) Part A: the four report counts are C 0 / P 14,393 / A 0 / S 13,079, and the not-pl_ counts are 0 / 0 / 0 / 0 — **the history and correction tables are NOT shared between threads: one copy per Worker; job 8's headline was wrong and my own clean-run zeros had already said so**; (3) Part B: T6's known answer met (exactly one bestmove in 100/100 storms with `setoption Hash` fired mid-search, readyok 100/100, 0 TSan reports, exit 0) and the ASan T5 block ran clean (0 reports, 0 leaks, exit 0); Part C: the four identities all 200/200 EQUAL (one sha256 `2e47b1ad…` for base, patched-OFF, patched-ON, base+TmFinishIteration, base+TmNodeShare), the HindsightDepth control differs (0a5fd743…), and the planted leak differs (ece2546c…) — the check sees both.** The clock rule's minute at the report: see stamps.txt (the last `minute N` line).
2. Step 0: all four builds (C/P/A/S) print 312866 / 862329 / 3024920 / 4865609 (`ds5j9 pins: {C,P,A,S}_{b11,b13,b16,perft}.txt` — 16 files) — no plant changes what the search does, as required before anything else counts.
3. Table:

| step | done? | evidence | result |
|---|---|---|---|
| Part 0 (two CORRECTION lines) | done | NOTES_deepseek5.md (commit aaa6aaa4e) + recount_job7.py/.out | both corrections in place, old lines kept |
| A builds P/A/S (+C reused) | done | ds5_job9_builds.py; the four pin files ×4 | all four builds reproduce the pins |
| A plant-marker grep before runs | done | the grep counts (4 per build) | both counters present in each planted build |
| A prediction, own commit | done | prediction.txt, commit 89f21d060 | committed before the runs |
| A runs: C / P / A / S, T1 200 storms, same seeds | done | ds5j9runs/J9_{C,P,A,S}_r1_T1.json + the two .tsan logs | C 0; P 14,393 (all pl_); A 0; S 13,079 (all shared_plant_entry) |
| the not-pl_ counts | done | the grep counts below | P: 0; S: 0 (every report is a planted location) |
| the member-escape table | done | prediction.txt's appended table | the nine Worker tables (search.hpp 472-481) never leave their Worker: every use site is the worker's own search; the cross-worker state is the Searcher's TT and stop flag, both synchronized |
| B: T6 (Hash mid-search) ×100 | done | ds5j9runs/J9_T6_T6.json | one bestmove 100/100, readyok 100/100, 0 reports, exit 0 |
| B: ASan T5 (late/early stop) ×100+100 | done | ds5j9runs/J9_ASAN_r1_T5.json | 0 reports, 0 leaks, exit 0; max 6.0 / 14.1 ms |
| C: the five identities + two controls | done | id_*.txt (seven sha256 lines) | 5 × equal; HindsightDepth differs; the leak differs |

**Part A's table (prediction beside measurement):**

| build | predicted reports | measured | predicted not-pl_ | measured not-pl_ | agree? |
|---|---|---|---|---|---|
| C | 0 | 0 (exit 0) | 0 | 0 | yes |
| P | >0, all pl_ | 14,393 (exit 66): pl_hist_upd 12,147 + pl_corr_upd 2,246 | 0 | 0 | yes |
| A | 0 | 0 (exit 0) | 0 | 0 | yes |
| S | >0, with shared_plant_entry | 13,079 (exit 66): shared_plant_entry 13,079 | 0 (the S-specific locations are the planted true fault) | 0 | yes |

**The one sentence**: the history and correction tables are **not shared between threads** — the run that shows it is **A** (the same two counters as atomics: 0 reports over the same 200 storms) beside **S** (the planted true shared write: 13,079 reports, every one on `shared_plant_entry`) and **C** (the clean engine: 0 over the same schedule, as job 6 already measured).

4. Findings:
- Job 8's headline is withdrawn: the 11,364 + 3,097 reports measured MY COUNTERS (a plain global int races wherever it stands), not the tables. The correct instrument was the atomic twin (A) — its silence, against P's noise on the same schedule, is the proof; S adds the positive that the harness sees a real shared TABLE-ENTRY write (the log's location line names `shared_plant_entry`).
- T6: the engine stops its own running search before applying `setoption Hash` (the uci.cpp setoption branch, as file 8 said) — exactly one bestmove and one readyok per storm in 100/100, legal everywhere, no race reported.
- The clock switches (FI/NS) leave 200/200 fixed-nodes searches identical (Part C) — their effect is clock-play only, now proven on my machine the way kimi5's rule demands.
- Suspicions, not proven: the member-escape table is a code reading (the nine members' use sites are all worker-local by my grep — a pointer stashed in a global I did not grep for would evade it); the atomic counters' `relaxed` ordering is enough for TSan's happens-before on the counter itself, not a claim about the surrounding data.
5. From my partner: glmflash5's notes (cursor/glmflash5-work-cb5c, read at the step-A check): no new FOR-deepseek5 line this round; its PID/option lessons stay applied. kimi5: its job-3 finding (ContHist4PlyRead's tree-size tax, 10.5% at depth 16 on MY tree with the built-in net — matching its own measurement on the same setup) is noted; my job-5 B-rows are the same-tree evidence it can reuse.
6. What I did NOT do: a second repetition of the four Part-A runs (one run each; the C/P/A/S pattern is 4 × 200 storms — a repeat would strengthen little); the leak at ONE site only (both the main-search and qsearch sites carry it — the count is in the transcript; a single-site variant would localize the sensitivity).
7. What I am NOT sure about: whether TSan would catch a race on a table ENTRY (int16) as reliably as on my int counter — S's 13,079 say yes for a static entry; a per-table-entry dynamic write is the same shape; whether the correction/history UPDATES being worker-local is also true of the NEW tables the current helper jobs add (pawn history etc. — same Worker-member pattern per the patches I read in job 13, so likely yes).
8. A better way: the four-build pattern (clean / plain-plant / atomic-plant / true-shared-plant) generalizes to ANY "is X shared" question in one run each — I would keep it as the standard refutation instrument, replacing single-counter headlines entirely (my job 8 was the counterexample).
9. times: see stamps.txt
10. Model: deepseek5 — DeepSeek (the model serving this cloud-agent run).
