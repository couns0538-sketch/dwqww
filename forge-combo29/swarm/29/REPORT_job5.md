# REPORT_job5 - area 9 job 1 again, cycle 2(c), SEED+10 = 2911

what was asked: the brief's cycle step 2(c) — area 9 job 1 again with the next seed and a new position set
(R built with SEED+10 = 2911), and a statement of what differs from the first run.
the answer: the profile on a NEW 400-position random-game set reproduces the overall shape but **overturns my own
29-C2**: on these positions `MovePicker::pick_best` (8.06 %) clearly outranks `MovePicker::next` (5.92 %), which
is seat 19's 19-F13 direction. My earlier "tie" reading was an artefact of the position set I used. I also confirm
the `TT probe_body` rise again (3.65 % deep vs 1.38 % bench).
how sure: high on the numbers (all parsed from perf task-clock samples with 200 completed searches); high on the
conclusion that **position type, not the engine, decides this ordering** — I have now measured the same engine three
ways with three different answers.

## what differs from my first job-1 run (required by the brief)
1. New position set: `R_2911.fens`, 400 FENs, python-chess random games with SEED 2911, one position every 7 plies.
   Control that the seed is really in effect: with SEED 2901 the same generator shares **0 of 50** positions with it.
2. Profiled at **depth 12 over a position set** as well as on `bench 13`, not bench alone — because job 4 showed
   those two disagree. Every published profile in the swarm so far (including my job 1) is bench-only.
3. A prediction (job5/prediction.txt) committed before the first measurement, with four kills.

## honesty numbers
Build `/home/ubuntu/build/base/forge`, sha256 `e06310ec...6a83`: bench 11 = 312866, bench 13 = 862329,
bench 16 = 3024920, go perft 5 = 4865609 — all four match (HONESTY.txt).

## a table: step | done-partly-not done | evidence file | result

| step | done? | evidence | result |
|---|---|---|---|
| build R with SEED 2911, prove the seed is in effect | done | `raw_make_R.txt` | 400 FENs; 0/50 overlap with SEED 2901; 0 positions without a legal move |
| profile depth 12 over the new set | done | `raw_profile_R.txt` | 200 searches, all 8 symbols sampled |
| same engine on bench 13 for the comparison | done | `raw_profile_R.txt` | 8 symbols sampled |
| guard: a missing symbol must not pass as 0 | done | `profile_R_2911.py` | prints NOT FOUND + INCONCLUSIVE (it fired in job 4) |

## the numbers

| symbol | R_2911 depth 12 | bench 13 | my job4 set (O+G) depth 12 |
|---|---|---|---|
| `evaluate_position` | 15.80 % | 15.25 % | 16.05 % |
| `Worker::search` | 12.05 % | 12.11 % | 12.39 % |
| `MovePicker::pick_best` | **8.06 %** | 6.77 % | 6.48 % |
| `MovePicker::next(bool)` | **5.92 %** | 6.22 % | 6.53 % |
| `TT probe_body` | 3.65 % | 1.38 % | 4.86 % |
| `see_ge` | 4.39 % | 5.34 % | 5.54 % |
| `fill_pseudo_legal` | 2.67 % | 3.19 % | 2.83 % |
| `qsearch` | 3.55 % | 3.52 % | 3.29 % |

## prediction outcomes
| # | predicted | got | verdict |
|---|---|---|---|
| Q1 | `evaluate_position` 8–20 % | 15.80 % | SURVIVES |
| Q2 | `probe_body` 3–6 % | 3.65 % | SURVIVES |
| Q3 | `see_ge` 3–9 % | 4.39 % | SURVIVES |
| Q4 | `pick_best` vs `next` within 1.5 points (a tie) | gap **2.14 points**, pick_best ahead | **KILLED** |

Q4 being killed is the useful result, not a nuisance: my prediction encoded 29-C2, and the data refused it.

## findings
| id | area | one sentence | file with the exact command that shows it again | NEW |
|---|---|---|---|---|
| 29-F10 | 9 | The move-ordering profile is POSITION-DEPENDENT, not engine-constant: the same binary gives `pick_best` 8.06 % vs `next` 5.92 % on 200 random-game positions at depth 12, but 6.48 % vs 6.53 % on 200 opening/game positions and 6.77 % vs 6.22 % on bench 13 — so any claim that one of the two MovePicker entry points is "the hotter one" must name its position set, and seat 19's 19-F13 direction is the one that holds on random-game positions. | `forge-combo29/swarm/29/job5/profile_R_2911.py` | NEW |
| 29-N4 | 9 | WITHDRAWAL of my own 29-C2: I refuted 19-F13's `pick_best` > `next` ordering on an O+G position set; on a new seeded random-game set the same engine shows exactly the ordering 19-F13 reported (8.06 % vs 5.92 %). 29-C2 is therefore withdrawn as a refutation and downgraded to "true on my set only", and 19-F13's direction is the better-supported one. My 29-F7 (which rested on the same ordering) is withdrawn in the same way. | `forge-combo29/swarm/29/job5/raw_profile_R.txt` | NEW |
| 29-F11 | 9 | `TT probe_body` rises from 1.38 % on `bench 13` to 3.65 % on a depth-12 random-game set (2.6x), reproducing my 29-C1 on a completely different position set and a different run — so the bench number understates the transposition table's real share for every seat that profiles with `bench`. | `forge-combo29/swarm/29/job5/raw_profile_R.txt` | NEW |

## suspicions, not proven
- The 2.14-point gap may be a piece-count effect: R positions are random-game middlegames with more pieces than my
  O+G mix, so `pick_best` scans longer lists and `next` is called less often per node. I have not measured the
  number of moves per node as a function of position type, which would settle it.
- Every share here is a task-clock SAMPLE estimate; a 2.14-point gap is outside my ±1-point error band, so I treat
  it as real, but a 0.5-point gap on these counts would not be.

## what I did NOT do
- Not 400 positions profiled: the harness caps at 200 per file by construction (`[:200]`), so this is 200 of the 400
  FENs built. The file has 400 and a later job can use all of them.
- No patch from 29-F10: knowing that the ordering flips with position type does not by itself yield a bit-exact
  speed win.
- Still no PC-mode profile: 29-F9 stands, no v3 net file exists in the repository.

## what I am NOT sure about
- Whether seat 19's `R_1911.fens` behaves exactly like my `R_2911.fens`; both are random-game sets, and the
  directions agree, but I have not run on theirs.
- Whether the ordering would flip back on endgame positions (heavy piece counts vs few).

times: see stamps.txt
