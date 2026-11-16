## 2026-11-16T21:07Z (block 1)

- seat: 17
- branch: for-fable-and-opus/swarm-17
- area: 7 (READING THE CODE for faults)
- seed: 1701

Done: STEP 1 seat claimed (SEAT.txt pushed), repository check passed (couns0538-sketch/dwqww).
Running: STEP 2 engine build at 6b98f217 in ../base worktree.
Next: release build, then the honesty check (bench 11/13/16, go perft 5).

## 2026-11-16T21:34Z (block 4)

seat 17 | area 7 (READING THE CODE for faults) | branch for-fable-and-opus/swarm-17 | seed 1701

DONE
- STEP 1 seat, STEP 2 build + honesty (all four pins match: 312866 / 862329 / 3024920 / 4865609).
- ASan+UBSan builds of engine + planted-fault copies; sanitizer proof both ways (planted heap over-read
  2 lines, planted signed overflow 1 line, both counted by the SAME runner; real build 0 lines).
- valgrind memcheck harness (portable build; AVX-512 exe cannot run under valgrind).
- S-F1 / S-F2: `go ... searchmoves <no legal match>` answers `bestmove 0000` on a position with legal
  moves; source `src/search.cpp:2640` reads `front()` of an empty MoveList.
- Harness check vs broadcast 19-F12: CONFIRMED on my engine; the one pipelined runner I had
  (proof_runner.py) was fixed, its proof re-run, FINDINGS records which results were affected.

RUNNING
- 218-legal-move position under release + ASan (perft 1 and depth 6): checks the unclamped
  `root_effort_moves_[256]` / `assert`-compiled-out suspicion. Not finished yet.

NEXT COMMAND
cd /agent/repos/dwqww/forge-combo29/swarm/17/job1 && python3 run_asan.py /agent/repos/base/forge-combo29/build-asan/forge G.epd 21 20 16 asan_G_21_40
## 2026-11-16T21:43Z (block 5) — checkpoint push

seat 17 | area 7 (READING THE CODE for faults) | branch for-fable-and-opus/swarm-17 | seed 1701

DONE (all pushed)
- Step 1 seat, Step 2 build + honesty: 312866 / 862329 / 3024920 / 4865609 all match.
- Sanitizer proofs with planted faults, re-run through a de-pipelined runner after 19-F12.
- Measurement-integrity audit after the seat 19 warning: three guards added and each shown failing.
- ASan+UBSan sweeps: G 1-12 depth 14, G 21-40 depth 16, and MultiPV 3 / MultiPV 8 / mate 2 / Threads 4
  (24 searches). Every search measured (not_measured 0), 0 sanitizer lines in all of them.
- Checks of other seats: S-C0 (CONFIRMS 19-F12), S-C1 (CONFIRMS 07-R1), S-C2 (CONFIRMS 07-F1),
  S-C4 (CONFIRMS 27-F2), S-C5/S-C6 (CONFIRMS + strengthens 27-F4).
- Own findings: S-F1 (`bestmove 0000` on a position with 20 legal moves); S-F2 WITHDRAWN (my stated
  source was wrong - line 2640 is unreachable with an empty list, proved with control-flow markers);
  S-F3 negative control (bench 13 pin is immune to the history drift).

RUNNING
- max_moves.py: the 218-legal-move record position under release+ASan. Slow; time-boxed, may be abandoned.

NEXT COMMAND
cd /agent/repos/dwqww/forge-combo29/swarm/17/job1 && python3 run_asan.py /agent/repos/base/forge-combo29/build-asan/forge G.epd 41 20 16 asan_G_41_60
## 2026-11-16T21:57Z (block 6)

seat 17 | area 7 | branch for-fable-and-opus/swarm-17 | seed 1701

DONE since block 5
- REPORT_job1.md pushed; job 2 (move picker + histories) done, REPORT_job2.md pushed with it.
- NEW: S-F7 (history tunables at both advertised extremes under ASan: 0 lines, 40x node spread proves applied),
  S-F8 (no-legal-match searchmoves ignores node/movetime budgets: 64 depth lines all nodes 0), S-F4 (OwnBook
  default true voided my first clock run - methodological trap), S-F3/S-F5/S-F6 negatives.
- CONFIRMS: 10 (warm/cold rule, all four parts reproduced exactly), 07-R1, 07-F1, 27-F2, 27-F4 (re-labelled),
  19-F12. My own S-F2 WITHDRAWN (my source attribution was wrong; the observable S-F1 stands).

CORRECTION on record
- After seat 10's rule: my S-C6 baseline was a fresh process vs a post-Clear-Hash search, which conflates warm
  drift with a TT clear. FINDINGS now says so and keeps only the narrower surviving claim (hashfull -> 0, so
  the residual drift is the histories). All my ASan sweeps are one-search-per-process, so they are unaffected.

NEXT
- Check remaining seat findings; finish area 7 job 3 (transposition table) as far as time allows.
## 2026-11-16T22:05Z (block 7) — checkpoint

seat 17 | area 7 | branch for-fable-and-opus/swarm-17 | seed 1701

DONE since block 6
- NOTE_select_readline_artifact.md: standalone note on the select+readline artefact (failure signature,
  the rule for harness authors, both working patterns, evidence table).
- S-F8 follow-up, corrected: the no-legal-match searchmoves root does NOT hang and is NOT unbounded -
  bestmove 0000 in 18-19 ms on both `go movetime 100` and `go wtime 1000 btime 1000`, confirmed 3 ways
  including a plain shell pipe. What survives is narrower: 64 info depth lines all reporting nodes 0 time 0,
  i.e. a search report for a search that never ran. S-F11 records the harness root cause.
- S-C9 CONFIRMS 21-F2 (refused FEN still answers readyok, old board stays), S-C10 CONFIRMS 21-F8
  (fullmove 0 refused while python-chess accepts it: 5 legal moves -> engine plays the old board with 20).
- ASan sweep G 61-90 depth 14: 30 measured, 0 sanitizer lines. Running total 106 measured ASan searches.
- TT resize verified (S-F9): Hash 1/8/32/512/2048 -> hashfull 440/58/10/0/0, nodes converge, same bestmove.

NEXT
- Final STATUS + FINDINGS push at 22:30, then stop. Area 7 job 3 report if time remains.
## 2026-11-16T22:10Z (block 8) — FINAL

seat 17 | area 7 (READING THE CODE for faults) | branch for-fable-and-opus/swarm-17 | seed 1701

FINAL STATE — everything is pushed. Stopping here per the 22:30 deadline.

Deliverables in this folder
- HONESTY.txt (+ honesty/): all four pins match (312866 / 862329 / 3024920 / 4865609).
- REPORT_job1.md, REPORT_job2.md, REPORT_job3.md (each: asked / answer / how sure, honesty numbers,
  step table, findings with a re-run command, suspicions separate, what I did not do, uncertainties, times).
- NOTE_select_readline_artifact.md: standalone note on the select+readline artefact with the one-line rule.
- FINDINGS.md: 12 lines of my own (S-F*) and 12 checks of other seats (S-C*).

Findings of my own still standing
- S-F1  `bestmove 0000` returned on a position with 20 legal moves (no legal `searchmoves` match).
- S-F4  `OwnBook` defaults TRUE, so clock measurements from the initial position measure nothing.
- S-F7  history/LMR tunables at both advertised extremes: 0 sanitizer lines, 40x node spread proves applied.
- S-F8  no-match `searchmoves` prints 64 depth lines of `nodes 0 time 0` - a search report for a search that
        never ran. NOT a hang and NOT unbounded (bestmove 0000 in 18-19 ms; my first harness was wrong).
- S-F11 the select()+buffered readline() artefact that produced that wrong first answer.
- S-F3/S-F5/S-F6/S-F9 negatives; S-F2 WITHDRAWN by me (wrong source attribution).

Best result of the session (a check, not my own finding)
- S-C12: independently confirmed and severity-assessed seat 21's 21-F9 - at halfmove 100 the engine returns
  `f2f3` with `cp 0 nodes 0` and MISSES a mate in 1 that it finds at halfmove 99. Mechanism at
  src/search.cpp:2251 (>= 100 treated as a drawn root, no claim modelled, no search performed).

Measurement totals
- 106 measured ASan+UBSan searches, 0 sanitizer lines, every one asserted to have actually searched.
- Sanitizer proof both ways with planted faults, counted by the same runner.

NEXT COMMAND (if resumed)
cd /agent/repos/dwqww/forge-combo29/swarm/17 && gh_absent=$? ; git fetch -q --depth 1 origin handoff/fable-opus-combo29-all-20261114 && git show FETCH_HEAD:forge-combo29/soak_all/FABLE_TO_swarm_1.md | head -5

## 2026-11-16T22:19Z CONTINUE: 12 more hours, ends at 2026-11-17T10:19Z

seat 17 | area 7 | branch for-fable-and-opus/swarm-17 | seed 1701
Kept the same seat (from ~/swarm_seat.txt, verified against SEAT.txt). Doing next: read FABLE_TO_swarm_2..5 in order, build the PC source from file 5 in a separate copy with -DFORGE_MATE_ALPHA_GUARD=1, check its bench numbers, then THE CYCLE with BOTH builds (PC build under PC20 settings).
## 2026-11-16T22:22Z (block 9)

seat 17 | area 7 | Threads 1 for every score | branch for-fable-and-opus/swarm-17

DONE
- Read FABLE_TO_swarm_2..5 in order. File 3 corrects file 1's castling line; file 4 separates
  default-option pins from S14 sums; file 5 is the PC source patch.
- PC r15 build: patch sha256 matches d6bd72c531f785f4..., 11 files, zero fuzz, built with
  -DFORGE_MATE_ALPHA_GUARD=1 in a separate copy. All 8 honesty numbers match file 5's table
  (none 312866/862329/3024920/4865609, S14 242796/656517, PC20 278024/587276). See PC_BUILD.txt.
- PC vs base on my own finds (Threads 1 both sides): S-F1 bestmove 0000 STILL PRESENT on the PC build;
  S-F8 zero-node depth lines STILL PRESENT; S-C10 fullmove 0 STILL PRESENT; S-C11 missed mate at
  halfmove 100 REPAIRED on the PC build (a1a8 "mate 1", 84/105 nodes vs f2f3 "cp 0 nodes 0").
- Threads audit: only the job1 threads4 sweep used >1 thread (6 records, no scores, never cited).
  Every other result was Threads 1 (default; my ASan runner sends no Threads option).

NEXT
- Continue area 7 on BOTH builds: re-read the PC-side source for the new switches (b4.hpp, HistRework,
  CorrHistV2, TtPruneV2) for the same fault classes, and re-run the S-F7 history-extremes stress under PC20.
## 2026-11-16T22:37Z (block 10)

seat 17 | area 7 | every score Threads 1 | branch for-fable-and-opus/swarm-17

ANSWERED the two follow-up questions

Q2 (pawn-move mate at halfmove 100). YES, the PC build covers it, on a DECISIVE board:
  `r7/1P6/8/8/8/8/8/k1K5 w - - 100 1`, only mate `b7a8q` (capture-promotion), and the engine's own
  generation order puts `b7b8q` first and `b7a8q` fifth.
  base S14, hm100 -> `b7b8q`, `cp 0 nodes 0`, MATE MISSED
  base S14, hm99  -> `b7a8q`, `mate 1`, 60 nodes
  PC20,    hm100 -> `b7a8q`, `mate 1`, 60 nodes  (REPAIRED)
  PC20,    hm99  -> `b7a8q`, `mate 1`, 60 nodes
  My first three pawn-mate boards were NOT decisive (`a7a8q` is the engine's first move there, so base
  plays it by luck with a 0-node score); they are listed in the evidence so nobody reuses them.

Q1 (are S-F1 and 19-F12 the same missing guard?). NO - two separate defects, with markers:
  S-F1 / S-F8 / S-F1b fire PATH_EARLY_ROOTDRAWN count=0 and answer 0000.
  19-F28's catch-all at search.cpp:3017 never fired in any of my six cases.
  S-F1's 0000 is an EMPTY bestmove (`root_candidates` empty -> the guarded assignment is skipped), not a
  fabricated one. Fixing 19-F12 will not fix S-F1, and vice versa.

NEXT
- Re-run the S-F7 history-extremes stress under PC20 on the PC build, and test the four new PC switches
  (CuckooRep / HistRework / TtPruneV2 / CorrHistV2) at their extremes for the same fault classes.
## 2026-11-16T22:41Z (block 11)

seat 17 | area 7 + new softnodes area | every score Threads 1 | branch for-fable-and-opus/swarm-17

DONE
- Read FABLE_TO_swarm_6. Two of my verdicts changed and I corrected them:
  * S-C11 and S-C12 WITHDRAWN as defects. File 6's inequality (defect only if 2N-1 <= 100-counter) is
    satisfied correctly by the BASE tree: counter 98 and 99 -> a1a8 "mate 1", counter 100 -> cp 0, which is
    correct because the mating move would be the 101st half-move. My earlier "mate MISSED / REPAIRED"
    framing for the pawn-promotion board is withdrawn for the same reason.
- NEW AREA softnodes, PC r15 / PC20 / Threads 1, 3 runs per cell, 12 cells:
  deterministic 12/12 (every field identical), depth sequences complete 1..D, overshoot 1.02x-2.06x,
  worst cell G2 at softnodes 250000 = 514,117 nodes for a 250,000 budget.
- Switch extremes on the PC build (between searches): 35 searches, 0 problems; HistRework 9 correctly
  refused (`invalid value`) and clamped to 3 (node counts identical to rework3).

RUNNING
- Mid-search setoption stress (13 switches x 2 go forms) on the PC ASan build; the first 8 logs are clean
  (bestmove present, readyok present, 0 sanitizer lines). Hash 2048 under ASan is slow.

NEXT
- Finish mid-search stress; write the findings table with a GUI-reachability column.
## 2026-11-16T22:54Z (block 12)

seat 17 | area 7 + softnodes + budget sensitivity | Threads 1 | branch for-fable-and-opus/swarm-17

DONE
- Budget sensitivity (independent check of the other seat's 100-position run): 10 G positions, PC r15/PC20,
  Threads 1, at go nodes 20000 / 50000 / 250000: 9 of 10 keep the same bestmove, 1 changes
  (position 6 `2r4r/pp4k1/...` : c8c3 at 20000, d6e6 at 50000 and 250000; score cp 7 -> cp 16 -> cp 37).
  So the three budgets are mostly the same player and the exception is real.
- Mid-search setoption stress, 13 switches x 2 go forms = 26 cases on the PC ASan build: all legal bestmove,
  readyok, 0 sanitizer lines, including Threads 256. HistRework 9 correctly refused and clamped.
  Observation: setoption mid-search emits bestmove BEFORE readyok in 12/12 cases.
- My 4th harness bug recorded: the first version swallowed the bestmove while waiting for readyok and
  reported 12 false hangs. Fixed by inspecting every line consumed during the wait; false run kept in
  pc/midsetopt2/ so the error is visible.
- FINDINGS_TABLE.md updated with the two new rows (budget sensitivity, mid-search setoption).

NEXT
- Keep the table current; next area work on the PC path (clock 6s+0.06, go nodes 20000) as file 6 ranks it.
## 2026-11-16T22:55Z (block 13)

seat 17 | area 7 + PC-path measurements | Threads 1 | branch for-fable-and-opus/swarm-17

DONE
- Depth vs selection on position 6: PURE DEPTH EFFECT, proven by identical nodes. `go nodes 20000` ==
  `go depth 8` (13,628 nodes, cp 7, c8c3); `go nodes 50000` == `go depth 10` (45,673, cp 16, d6e6).
  No selection effect. The move is non-monotone in depth (d6 h8f8, d7 d6e6, d8 c8c3, d9 f5h6, d10 d6e6)
  -> recorded as a method rule: any fixed-node A/B on a tactical position must log the depth reached.
- Node-tier sweep, 10 real positions, tiers 2000/20000/50000/250000 with depths: only 6 of 10 keep one move;
  depth spans 5-17 on the same board; position 6 gives three different moves across four budgets.
- Match clock 6s+0.06 on a real middlegame: 60 moves, 0 forfeits, 0 illegal moves, clocks left 1715/1599 ms,
  median 153 ms, max 866 ms. All three rows are in FINDINGS_TABLE.md.

NEXT
- More match-clock games (one game is a thin sample for a forfeit claim), then keep the table current.
## 2026-11-16T23:05Z (block 14)

seat 17 | PC path measurements | Threads 1 | branch for-fable-and-opus/swarm-17

DONE — the forfeit question is answered
- 30 match-clock games at 6 s + 0.06 from 30 real middlegames: 1,416 plies, **0 forfeits**,
  0 engine-caused illegal moves, clock dipping to **194 ms** without a forfeit (5 games under 600 ms).
  So a forfeit was not observed even at a quarter-second of clock. Evidence pc/manygames/.
- Node-path health, 100 lines (20 positions x 2000/20000/50000/250000/softnodes 2000): 0 illegal moves,
  0 bestmove 0000, 0 mate PVs that fail to mate, depths 5-20.
- CORRECTION of my own alarm: the "illegal move" I found mid-run was MY invalid FEN (Black to move with White
  in check); the engine refused it correctly and played a legal startpos move - exactly S-C9. 2 of my 30 start
  FENs were bad, 28 good; both games re-run from valid positions, clean. I now validate every FEN with
  python-chess before use.

NEXT
- Keep the table current; continue the cycle on anything on the PC path that could lose a game.
## 2026-11-16T23:06Z (block 15)

seat 17 | PC path measurements | Threads 1 | branch for-fable-and-opus/swarm-17

DONE
- S-C9 confirmed end-to-end in ONE GUI-like session: load a real middlegame, search (b6b5); load an INVALID
  FEN (side to move left its own king in check); engine refuses with an info string, answers readyok, and
  then returns b6b5 again - the FIRST position's move, legal there and illegal in startpos. So in a GUI
  session the engine hands out the previous board's move with no error state. Highest-exposure item found.
  And it is a typo-class trigger: 2 of my 30 hand-written FENs hit it.
- Table row strengthened with that confirmation.

NEXT
- Keep cycling: look for the same silent-continuation hazard on the `position startpos moves` path, which a
  GUI uses for every game, and push STATUS at the 25-minute mark.
## 2026-11-16T23:07Z (block 16)

seat 17 | PC path measurements | Threads 1 | branch for-fable-and-opus/swarm-17

DONE
- Three-line FEN guard added to FINDINGS_TABLE.md and VERIFIED: refuses both FENs that fooled me, an empty
  board, a checkmated position and a stalemate; accepts good ones. pc/guardcheck/guard.json.
- Moves-path silent continuation measured: `position startpos moves e2e4 e7e5 e1e3` -> `illegal move e1e3`,
  `readyok`, then `g1f3` (legal in the retained PREFIX only). That is the call a GUI makes on every move, so
  the exposure is far larger than the hand-written-FEN route; recorded as exposure, not a new fault.

NEXT
- Continue the cycle: the remaining question on the owner's path is whether the engine ever disagrees with
  python-chess about legality at the match budgets on a larger position sample (a wrong move is the other way
  to lose a game outright). Then keep the table current and push STATUS every 25 minutes.
## 2026-11-16T23:22Z (block 17)

seat 17 | PC path | Threads 1 | branch for-fable-and-opus/swarm-17

DONE
- NOTE_moves_path_hazard.md: standalone GUI-author note on `info string illegal move` — command, exact output
  for four cases, what the engine plays, and the rule that a harness must treat that line as FATAL for the
  game. Linked from the table row.
- Legality at the match budgets: 60 real game positions x 20000/50000/250000 = 180 lines, 0 illegal moves,
  0 unmeasured. Also 0 of the 60 real game FENs were rejected by the guard — my 2 bad FENs came from a
  hand-written list, so the FEN hazard is a hand-written-input hazard, not a real-data one.

DELIVERABLES (the three to hand the owner first)
- FINDINGS_TABLE.md   — every finding with build, settings, Threads 1 and GUI-reachability.
- NOTE_moves_path_hazard.md — the per-move hazard and the fatal-on-illegal-move rule.
- NOTE_select_readline_artifact.md — the harness artefact that fabricates a hang.

NEXT
- Keep the table current to the close at 2026-11-17T10:19Z; continue the cycle on the PC path.
