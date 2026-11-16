# REPORT job 1 — seat 17, area 7 (READING THE CODE for faults)

## What was asked / the answer / how sure

**What was asked.** Area 7 job 1: read `src/search.cpp` (2753 lines at base `6b98f217`) for faults —
overflow, uninitialised value, off-by-one, index out of range, a race, undefined behaviour, a value read
before it is set — and for every suspicious line give file, line, why, and a TEST that shows it; anything
without a test goes under "suspicions, not proven". A repair only as a text patch.

**The answer.** One engine fault shown end to end (S-F1: `bestmove 0000` returned on a position with 20
legal moves, via the `searchmoves` path), one wrong claim of mine withdrawn after my own test refuted it
(S-F2), one methodological trap that voided five of my own measurements (S-F4), and five negatives that
are worth having on record. No sanitizer line in any of the 76 measured ASan+UBSan searches.

**How sure.** S-F1 is certain (raw output, reproduced on three builds, python-chess cross-check).
S-F2 is certainly wrong and I withdrew it myself. The negatives are certain within their scope; I say
below what that scope is.

## Honesty numbers (base `6b98f217`, release, GCC 13.3.0, no FORGE_PORTABLE; host has AVX-512F + BMI2)

| req | expected | got | verdict |
|---|---|---|---|
| bench 11 | 312866 | 312866 | MATCH |
| bench 13 | 862329 | 862329 | MATCH |
| bench 16 | 3024920 | 3024920 | MATCH |
| go perft 5 | 4865609 | 4865609 | MATCH |

Evidence: `HONESTY.txt` and `honesty/*.raw` + `honesty/*.meta` (exe path, sha256
`e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`, `id name Chess Engine Forge 6.4.24
candidate`, no options sent). Build is USED.

## Step / done-partly-not done / evidence table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| Build base + honesty check | done | `HONESTY.txt`, `honesty/` | all four pins match |
| Read src/search.cpp in full | done | `job1/` notes folded into this report | structure, TT, move picker, search, qsearch, driver read |
| ASan+UBSan build of the engine | done | `build-asan` (outside the repo), `proof/real_normal_search.meta` | 50 sanitizer symbols |
| Sanitizer proof: planted heap over-read | done | `job1/proof/planted_heap_overread.*` | runner counted 2 lines |
| Sanitizer proof: planted signed overflow | done | `job1/proof/planted_signed_overflow.*` | runner counted 1 line |
| ASan sweep G 1-12 depth 14 | done | `job1/asan_G_1_12/` | 12 searches, 0 sanitizer lines |
| ASan sweep G 21-40 depth 16 | done | `job1/asan_G_21_40/run.meta` | 20 measured / 20, 0 sanitizer lines |
| ASan sweep G 41-60 depth 16 | done | `job1/asan_G_41_60/run.meta` | 20 measured / 20, 0 sanitizer lines |
| ASan MultiPV 3 / 8, mate 2, Threads 4 | done | `job1/mpv/mpv.json` | 24 measured / 24, 0 sanitizer lines |
| Deep search (seldepth 48-64) under ASan | done | `job1/maxply/maxply2.json` | 0 sanitizer lines |
| 400-ply game + long key history under ASan | done | `job1/bench_repeat/long_game.json` | identical answer for move-list and FEN, 0 lines |
| Clock extremes under UBSan | done | `job1/clock/clock_extreme_nobook.json` | 0 sanitizer lines at max int64 |
| valgrind memcheck (uninitialised values) | partly | `job1/vg/plain_depth6.valgrind.log` | 0 errors on a real depth-6 search; the edge-path run hit my own 600 s shell timeout and proved nothing, so it is NOT counted |
| 218-legal-move record position | not done | `job1/max_moves.py` | run repeatedly overran its window on this 4-core box under ASan; abandoned rather than left ambiguous. Not evidence of anything |
| Repair as a text patch | not attempted | — | S-F1's fix (`restricted_root_empty` is already computed at search.cpp:2210 and carried nowhere) is a design decision for Opus, not a mechanical repair; I did not touch engine source |

## Findings, each with a command that shows it again

**S-F1 — `bestmove 0000` on a position that has 20 legal moves.**
`go depth 5 searchmoves e7e5` on startpos (e7e5 is Black's move, so nothing matches) answers
`info string searchmoves restriction has no legal root moves` and then `bestmove 0000`. UCI defines `0000`
as "no legal move exists"; python-chess says this position has 20. A GUI receiving 0000 from the side to move
has been handed an illegal move. Control: `searchmoves e2e4` answers `e2e4`; a checkmated position correctly
answers 0000.
Command: `cd forge-combo29/swarm/17/job1 && python3 finding_searchmoves.py /agent/repos/base/forge-combo29/build/forge sm`

**S-F2 — WITHDRAWN.** I attributed S-F1 to `src/search.cpp:2640` reading `front()` of an empty `MoveList`.
It does not: every empty-`root_candidates` path returns at the early block on line 2253, so 2640 never sees
an empty list. Refuted by my own control-flow marker test, and independently by seat 07's 07-R1.
Command: `cd forge-combo29/swarm/17/job1 && cat reach_check/flow.json`

**S-F4 — methodological trap: `OwnBook` defaults TRUE.**
Every clock or time measurement that starts from the initial position is answered by the book in ~0 ms with
no `info depth` line. My first clock run produced five "results" that measured nothing. With the book off,
the same searches scale properly (1000 -> 55 ms/d14, 10000 -> 374 ms/d18, 100000 -> 5234 ms/d25).
Command: `cd forge-combo29/swarm/17/job1 && python3 -c "import json;print(json.load(open('clock/clock.json'))[0]);print(json.load(open('clock/clock_nobook.json'))[0])"`
(Seat 08's 08-F3 records the same trap independently; I did not see it before I hit it.)

**Checks of other seats (each with my own harness, not theirs).**
- S-C0 CONFIRMS 19-F12 — pipelined `quit` fabricates `bestmove a2a3` at 0 nodes; my harness gets e2e4/56,720.
  Command: `python3 harness_check.py /agent/repos/base/forge-combo29/build/forge harness_ok`
- S-C1 CONFIRMS 07-R1 — my own S-F2 source claim was wrong (see above).
- S-C2 CONFIRMS 07-F1 — the info lines are literally `score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv`.
  Evidence: `job1/reach_check/case07f1.log`
- S-C4 CONFIRMS 27-F2 — `go nodes` 1/5/10/20/25 -> a2a3 with zero info lines; 26 -> d2d4 with 26 nodes.
  Evidence: `job1/check27/nodes.json`
- S-C5/S-C6 CONFIRMS + strengthens 27-F4 — `setoption name Clear Hash` changes the depth-10 node count in
  20/20 positions (e.g. 23448 -> 40313) while the bestmove changes in only 1/20. Node count is the sensitive
  detector for the surviving histories.
  Evidence: `job1/check27clear/D_A_*.log`, `D_B_*.log`

## Suspicions, not proven

- `MovePicker::moves_` is `std::array<Scored,256>` with `push_scored` writing `moves_[count_++]` and no
  runtime bound; `MoveList::Capacity` is also 256 and `push_back` asserts only. `NDEBUG` is set in this
  build, so the assert is gone. The known maximum number of legal moves in a chess position is 218, so I
  could not construct an overflow, and I am NOT claiming one exists — only that nothing clamps it.
- `Worker::search` line 2377 `std::copy(root_candidates.begin(), root_candidates.end(), root_effort_moves_.begin())`
  is guarded by `assert(root_effort_count_ <= root_effort_moves_.size())`, which `NDEBUG` removes.
- `setoption` on a spin outside its range reports `info string invalid value` AND assigns the clamped value
  (`apply_spin` calls `assign` after `note_invalid`). That is deliberate per the comment at src/uci.cpp:275,
  so I list it as behaviour, not a fault.

## What I did NOT do

- Did not read the other six files area 7 job 1 lists (move picker/histories as a separate pass, position and
  move making, TT as a separate pass, UCI loop, time manager, evaluation, move generator) to the same depth
  as `src/search.cpp`; the TT and the time manager got a focused read, the rest did not.
- Did not finish the 218-legal-move position.
- Did not complete the valgrind edge-path run (MultiPV/ponder/searchmoves in one process); the one clean
  valgrind result is a plain depth-6 search.
- Did not write any patch or change any engine source.
- Did not attempt TSAN or the threads area.

## What I am NOT sure about

- The exact rate at which Clear Hash changes answers depends heavily on position set and depth; my 1/20
  bestmove rate versus seat 27's 9/20 is not a contradiction but I have not explained the difference.
- Whether the 256-slot move picker is reachable in some position I did not find. I searched for the record
  maximum (218) and stopped there.
- My ASan sweeps cover positions from set G only (60 of 353) plus a handful of special ones; O and R are not
  covered in job 1.

## Times

see `job1/…/run.meta` (`date`, `date_end`) and `STATUS.md` blocks; every run records its own UTC stamps.

## Last commands' output

```
=== git status --short
(clean at the commit that adds this report)

=== ls job1
asan_G_1_12      asan_G_21_40    asan_G_41_60    bench_repeat    check27
check27clear     clock           explore_asp     explore_asp.py  finding_searchmoves.py
G.epd            harness_check.py harness_ok     max_moves.py    maxply
mpv              plant_fault.py  prediction.txt  proof           proof_runner.py
reach_check      run_asan.py     run_asan.sh     sm              smove_over
uci_driver.py    vg              vg_run.py
```
