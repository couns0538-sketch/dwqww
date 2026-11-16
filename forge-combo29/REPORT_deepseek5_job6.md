# REPORT_deepseek5_job6 (deepseek5, 2026-11-16 UTC)

1. **What was asked**: job 4's storm again, through a harness that can SEE a sanitizer report — per-block files, harness-set sanitizer options, exit codes, stderr kept, and the controls run THROUGH the same pipe. **The answers: (1) H1–H5 all as expected THROUGH the new harness — H1 (the planted in-engine race, Threads 4): exit via TSan, 6 WARNING lines in 2 tsan log files; H2 (same plant, Threads 1): 0; H3 (clean TSan, Threads 4): 0, exit 0; H4 (the planted heap over-read, ASan): 2 ERROR lines in 2 asan logs, the engine died mid-block (missing=1) exactly as a first-report halt behaves; H5 (clean ASan): 0; (2) the storm, both programs: TSan T1(200)/T2(100)/T3(100)/T4sw(800)/T5(100+100) — warnings 0 in every block, no report file created, 0 missing / 0 doubled / 0 illegal everywhere; ASan T1/T2/T3/T4sw — the same zeros; (3) job 4's "0 reports" is now CONFIRMED by a harness that provably sees: the same harness lights up on H1/H4 and stays silent on the clean engine over 1,300 TSan storms and 1,200 ASan storms.** Cut: ASan's T5 block (the driver's guard fired first); Part 4 (the shared-state map) not reached.
2. Step 0: the same builds as job 4 (TSan exe and ASan exe, pins verified there at 04:37:55Z; sha256s of the trees unchanged — the plants live in separate copies /tmp/ds5_tsan_p3 and /tmp/ds5_asan_p3, each committed as a text diff: `plant_race.patch.txt` (the P3 counter at the top of `Worker::search`, src/search.cpp:2143-2145) and `plant_heaporead.patch.txt` (the H4 over-read, src/search.cpp:2144-2145); nothing of the engine is committed as source).
3. Table:

| step | done? | evidence | result |
|---|---|---|---|
| harness `ds5_job6_storms.py` | done | the file; cmd_H1..cmd_STORM_ASAN.txt | tag+block-named outputs; harness-set TSAN/ASAN/UBSAN_OPTIONS; stderr to a file; quit + wait 60 s; drain 500 ms |
| H1 plant-race T4, 20 storms | done | H1_T1x20.json + H1_T1x20.tsan.* | warnings 6, report_files 2 — DETECTED |
| H2 plant-race T1, 20 storms | done | H2_T1x20.json | warnings 0 — correct silence |
| H3 clean TSan, T4, 20 storms | done | H3_T1x20.json | warnings 0, exit 0 |
| H4 ASan heap plant, 5 storms | done | H4_T1x5.json + H4_T1x5.asan.* | warnings 2 (ERROR: AddressSanitizer), missing 1 (the halt), DETECTED |
| H5 clean ASan, 5 storms | done | H5_T1x5.json | warnings 0 |
| TSan storm T1/T2/T3/T4sw/T5 | done | STORM_TSAN_*.json (+ .out) | 0 reports, 0/0/0 in 1,300 storms; stop-answer max 50.7 (T1) / 148.4 ms (T4sw) |
| ASan storm T1/T2/T3/T4sw | done | STORM_ASAN_*.json | 0 reports, 0/0/0 in 1,200 storms; max 29.7 ms (T4sw) |
| ASan storm T5 | NOT done (driver guard) | — | cut |
| Part 4 shared-state map | NOT done | — | the stop fell first; proposed as the next job |

4. Findings:
- The five switch paths of `Searcher::search` (exclusive-lease Threads 1; helper threads; MultiPV 2 with the lease; the clock-exhausted no-helper path; the flip sequence with ucinewgame + the table-clearing DrawJitter) produced **no race and no protocol breach under a TSan build whose in-engine detection is proven by H1 (6 warnings, threads named) and by job 4's P4** — the silence is now a measured fact with files, not a sentence.
- The exit_code field is recorded for T4sw/T5 (0 = clean exits with LeakSanitizer active, so also **no leaks**) but still `null` for T1/T2/T3 (a leftover assignment in my block() — the warnings/stderr evidence stands; the exit-code gap is named here rather than hidden).
- The ASan run's T5 block was cut by my driver's guard at ~15 min; T1–T4sw completed.
- Suspicions, not proven: TSan's silence covers the interleavings this storm schedule produces; a race needing a rarer interleaving (e.g. stop during a Hash resize mid-search — my T4 flips options only BETWEEN searches) could still hide. Part 4's map is the systematic answer.
5. From my partner: glmflash5 (`cursor/glmflash5-work-cb5c`): read its NOTES tail and REPORT list at the step-A check before this job — its job-2 numbers (TmFinishIteration −10.7 [−26.2, +4.8] at 2+0.02, 0 losses in 986 games) were recounted by Fable and match; its warning "resolve the real fastchess PID at kill time, never a stored wrapper PID" is applied in my harness (I never kill by stored PID; I wait(60) after quit). kimi5: its job-2 prediction is pushed and it measures now — I did not read its measurement files (your instruction) and wrote nothing to it.
6. What I did NOT do: Part 4 (the shared-state map with per-structure planted counters — my own proposal, cut by the clock); ASan T5; a rerun of the H4 block with a slower plant (its engine died at the FIRST report — the "warnings 2" counts the first search's reports only).
7. What I am NOT sure about: whether the T4sw block's option-flip sequence exercises the TT-resize race surface (a Hash CHANGE mid-SEARCH is impossible in my protocol — the flips are between searches; a race there would need a different storm); whether TSan's exitcode=66 was ever actually triggered (no report → no exit 66 anywhere in the storm — consistent, but the field's null for T1–T3 leaves the exit unrecorded, which I regret).
8. A better way: the exit-code bug and the env-setting belong in the harness ONCE — done; the remaining gap is Part 4, which I would run next with the nine plants named in the job text (hash probe/store, the lease's take/give, helper start, root-move hand-over, result gather, history/correction updates, the stop-flag read), each behind its own `plant_<name>.patch.txt`, then ONE harness run names which structures are touched from more than one thread — the map you asked for.
9. times: see stamps.txt
10. Model: deepseek5 — DeepSeek (the model serving this cloud-agent run).
