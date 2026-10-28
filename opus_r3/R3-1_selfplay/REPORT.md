# R3-1 self-play checks (every option and build switch ON alone, all ON together, 500 games each) — DONE

Branch `opus-r3-selfplay` = opus-r3-stack 330237f3 (merged) + the job commits in `opus_r3/R3-1_selfplay/`.
Agent text; the rows that were PARTIAL at hand-back were completed by the main session from the collected
`logs/final_330237f3/matrix_summary.json` (the runners kept going after the agent ended).
Machine exclusive: no (gates, NNUE training and the self-play datagen ran throughout; every process of this job
at nice 19 / idle priority, about 2.7 cores during the final run). No Elo or speed claims.

## Acceptance
| line | result | evidence |
|---|---|---|
| checker: python-chess UCI driver, two processes of one config, random forge-10000.epd openings; legality of every bestmove, ponder, pv and currmove move; exactly one bestmove per go (isready barrier after every position); crash, exit status 0, hang, stderr; well-formed info lines and S08fix profile blocks; isready round trips incl. mid-search; preflight (options advertised, accepted, required activation lines, go depth 5, bench 11 signature) | built | `opus_selfplay_check.py --help`, README.md |
| checker self-test (planted protocol faults via fault_proxy.py) | 20/20 reported with the expected error type, clean control 0 errors (final harness sha256 c2105302 on 330237f3) | logs/final_330237f3/selftest.log |
| base head 2432670b | off: 500 games, 50640 plies, 0 errors. all_on: 500 games, 50980 plies, 0 crashes/illegal/double bestmoves/timeouts, 122 info lines after a HardDeadline watchdog bestmove (defect, reported, fixed in 5792074a). Other base configs stopped on request | logs/base_2432670b/ |
| HardDeadline repro (repro_late_info.py, every other option OFF) | 2432670b: 2 late lines in 200 rounds (134 watchdog answers); 330237f3: 0 in 1100 rounds (480 watchdog answers) | logs/repro_late_info_2432670b.log, logs/final_330237f3/repro_late_info.log |
| final head 330237f3: 36 configs x 500 games (every runtime option ON alone, every build switch ON alone incl. FORGE_NNUE_INT16 + NnueInt16 and FORGE_ATTACKS_INIT_ONCE, 3 all-ON variants) | **PASS**: 36/36 configs x 500, 18000 games, 1869703 plies, 0 errors (0 crashes, illegal moves, double bestmoves, timeouts, malformed output); 3040 HardDeadline watchdog answers, 0 late lines | logs/final_330237f3/MATRIX.md, summaries/ |
| final engine head 064af732 (main session, same harness): the options added after 330237f3, SmpHelpersPastDepth alone (Threads 2) and in all-ON, the 20 R3-4 spins at +10% / -10% | **PASS**: 4/4 configs x 500, 2000 games, 201275 plies, 0 errors; 45 watchdog answers, 0 late lines | logs/final_064af732/MATRIX.md |
| exe sha256 + git head per config | recorded | logs/final_330237f3/build.log, matrix_summary.json |

Final-run budgets (coordinator, 3 h): go nodes 200-2000; mix nodes 58 / clock 8 / movetime 10 / depth 8 /
infinite 6 / ponderhit 5 / pondermiss 5 (clock 0.2-2 s + 0-50 ms inc, movetime 5-30, depth 1-6, infinite/ponder
5-50 ms); 200-ply cap; 2 runners in parallel, 3 games per config (2 for Threads 2). All-ON variants:
all_on (every switch + every option, v2 replica rm8 + 8 heads + zero threat and pawn-pair blocks),
all_on_pure (same with PureNnue + stand-alone net), all_on_v1net (every switch + every non-v2 option, so
NnueLazyAcc and NnueInt16 are active). S-A4 H512 and FORGE_DATAGEN skipped (coordinator).

## Results on 330237f3 (`logs/final_330237f3/MATRIX.md` has the options of every row)
36 of 36 configs ran: 18000 games, 1869703 plies, 0 errors, 3040 HardDeadline watchdog answers (git head 330237f3).

| config | exe (sha256) | thr | games | plies | errors | crashes | illegal | double bm | timeouts | late info | watchdog answers | bench11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all_on | allsw `52f337c864bd` | 2 | 500/500 | 48826 | 0 | 0 | 0 | 0 | 0 | 0 | 1017 | 362031 |
| all_on_pure | allsw `52f337c864bd` | 2 | 500/500 | 52282 | 0 | 0 | 0 | 0 | 0 | 0 | 1054 | 368464 |
| all_on_v1net | allsw `52f337c864bd` | 2 | 500/500 | 50985 | 0 | 0 | 0 | 0 | 0 | 0 | 708 | 332408 |
| hard_deadline10 | base `07eb6fdeb058` | 1 | 500/500 | 48948 | 0 | 0 | 0 | 0 | 0 | 0 | 261 | 312866 |
| sw_nnue_lazy_acc | lazyacc `9ffef77efe05` | 1 | 500/500 | 51620 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| sw_prof | prof `1286cb9c7236` | 1 | 500/500 | 51527 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| sw_nnue_int16 | int16 `f65cb2ce3844` | 1 | 500/500 | 50342 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 330610 |
| sw_attacks_init_once | initonce `feb109601b55` | 1 | 500/500 | 50227 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| off | base `07eb6fdeb058` | 1 | 500/500 | 50323 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| smp_best_thread | base `07eb6fdeb058` | 2 | 500/500 | 40728 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| smp_exact_nodes | base `07eb6fdeb058` | 2 | 500/500 | 49053 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| lockless_tt | base `07eb6fdeb058` | 2 | 500/500 | 41538 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| syzygy | base `07eb6fdeb058` | 1 | 500/500 | 51988 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 313631 |
| corrhistplus7 | base `07eb6fdeb058` | 1 | 500/500 | 49496 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 317529 |
| nnue_king_buckets_rm8 | base `07eb6fdeb058` | 1 | 500/500 | 52239 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| nnue_output_buckets8 | base `07eb6fdeb058` | 1 | 500/500 | 50844 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| nnue_threats | base `07eb6fdeb058` | 1 | 500/500 | 53581 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| nnue_pawn_pairs | base `07eb6fdeb058` | 1 | 500/500 | 53538 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| pure_nnue | base `07eb6fdeb058` | 1 | 500/500 | 55757 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 450072 |
| corr_margins | base `07eb6fdeb058` | 1 | 500/500 | 53495 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 343365 |
| corr_ext | base `07eb6fdeb058` | 1 | 500/500 | 52466 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312961 |
| cuckoo_rep | base `07eb6fdeb058` | 1 | 500/500 | 54526 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 324211 |
| material_key_table | base `07eb6fdeb058` | 1 | 500/500 | 53913 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| netscale90 | base `07eb6fdeb058` | 1 | 500/500 | 52832 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 314443 |
| netscale110 | base `07eb6fdeb058` | 1 | 500/500 | 55596 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 268059 |
| hist_rework1 | base `07eb6fdeb058` | 1 | 500/500 | 54252 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 373261 |
| hist_rework2 | base `07eb6fdeb058` | 1 | 500/500 | 53877 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 320427 |
| hist_rework3 | base `07eb6fdeb058` | 1 | 500/500 | 51783 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 336192 |
| intended_threefold | base `07eb6fdeb058` | 1 | 500/500 | 54165 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| sw_nnue_o2 | o2 `373ae98655a1` | 1 | 500/500 | 52609 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| sw_nozero_move_buffers | nozero `2ab5ba01c222` | 1 | 500/500 | 56021 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| sw_s13_tt_child_prefetch | s13 `d7c61881dfa7` | 1 | 500/500 | 54142 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| sw_speedstack | speedstack `2e6b15b4c101` | 1 | 500/500 | 53399 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| corrhistplus1 | base `07eb6fdeb058` | 1 | 500/500 | 53262 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 318363 |
| corrhistplus2 | base `07eb6fdeb058` | 1 | 500/500 | 54755 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 296553 |
| corrhistplus4 | base `07eb6fdeb058` | 1 | 500/500 | 54768 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 340927 |

## Results on the final engine head 064af732 (4 configs)
4 of 4 configs ran: 2000 games, 201275 plies, 0 errors, 45 HardDeadline watchdog answers (git head 064af732).

| config | exe (sha256) | thr | games | plies | errors | crashes | illegal | double bm | timeouts | late info | watchdog answers | bench11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| smp_helpers_past_depth | base `43938b61608a` | 2 | 500/500 | 41515 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 |
| all_on_final | allsw `3ab215583d0a` | 2 | 500/500 | 52494 | 0 | 0 | 0 | 0 | 0 | 0 | 45 | 362031 |
| spsa_plus10 | base `43938b61608a` | 1 | 500/500 | 52473 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 320444 |
| spsa_minus10 | base `43938b61608a` | 1 | 500/500 | 54793 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 282806 |

## Findings
1. HardDeadline (C3) printed search output after the watchdog's bestmove (2432670b all_on: 122 `info depth`
   lines in 96 of 500 games, each right after one of 2106 watchdog answers, 0-281 ms late, median 18 ms; 97 with
   a PV whose first move was not the bestmove). Cause: the search's emit() (completed iteration and the aborted
   iteration's "revised line") could not see that the go was already answered. Never a double bestmove or an
   illegal move. Reported at once; fixed in the stack (output_closed, 5792074a); 0 late lines on 330237f3 over
   3040 watchdog answers in the matrix and 480 in the repro.
2. NnueLazyAcc and NnueInt16 act on the compiled-in net only. With a v2 net, NnueLazyAcc is silently unused, and
   `info string NnueInt16 active` is still printed when NnueInt16 is set before NNUEFile (all_on bench11 is
   362031 with or without it, while int16 changes the tree). all_on_v1net covers both together.
3. Profile blocks are consistent: one complete block before every search-thread bestmove (none before watchdog
   answers), e.g. all_on 50170 blocks / 51187 bestmoves (1017 watchdog), 0 overflow.
4. Informational: clock overruns under CPU starvation (base off: 43 of 10605 clocked searches, max 455 ms;
   final runs 0-5 per config, max 12.5 ms in all_on; hard_deadline10: 0). Forge prints no tbhits, so syzygy
   activity evidence is the activation line plus the bench signature (313631 vs 312866).

## UNVERIFIED / left
- Timing-dependent defects need the race to happen; 500 games per config on a loaded PC is evidence, not proof.
- A late duplicate bestmove arriving after the next readyok would be reported as an illegal/early bestmove of
  the next search rather than extra_bestmove (still an error); Forge joins the old search before answering
  `position`, so that window does not exist for Forge.
- S-A4 H512 not run (skipped on request; a widened lock net exists: F:/opus_scratch/r3/selfplay/nets/
  h512_widened_lock_split.inc, same weights as S-A4's split net; build_engines.sh builds h512 with it).
- Base head 2432670b: only off and all_on ran (stopped on request after the defect).

Machine exclusive: no.
