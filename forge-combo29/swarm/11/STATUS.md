# STATUS — Seat 11

## 2026-11-16T21:07:00Z (times from `date -u` in stamps.txt)
seat 11
area 1 — FEN INPUT under ASan + UBSan
branch for-fable-and-opus/swarm-11
seed 1101

- [x] STEP 1 seat claimed (SEAT.txt committed, token echoed back from origin)
- [ ] STEP 2 build 6b98f217 + honesty check
- [ ] THE CYCLE

Next command: `cd /agent/repos/dwqww && git worktree add ../base 6b98f2170a3210e71beed04bbd2553972c253ed7`

- [x] STEP 2 honesty check: 312866 / 862329 / 3024920 / 4865609 ALL MATCH (HONESTY.txt)
- [x] ASan+UBSan build started

## 2026-11-16 (cycle 1)
- job1 DONE: 20k mutated FENs under ASan+UBSan, 0 crashes / 0 san lines (both proofs shown).
- Read Opus FABLE_TO_swarm_1.md: F1 is new; F2 already known (kept only the harmlessness proof);
  S-F3 WITHDRAWN (I wrongly claimed to refute Opus's castling line).
- job1/S-F3_WITHDRAWN.md records both retractions.
- Next: job 2 of area 1 (extreme numbers in FEN fields).

## 2026-11-16 (cycle 1, job 2)
- job2 DONE: 30 extreme-number FEN cases under ASan+UBSan. 0 crashes, 0 san lines, 0 illegal
  bestmoves. All 9 prediction points held (j2-10 was my own malformed 21-digit case).
- perft 2 vs python-chess: 10 comparable cases, 0 differences; engine stricter where they differ.
- S-C2 pushed earlier: CONFIRMS seat 01's S-F2 (impossible double check accepted, perft right).
- Next: job 3 of area 1 (position startpos moves, 1000 legal plies + one illegal move).

## 2026-11-16 (cycle 1, job 3 — area 1 complete)
- job3 DONE: 1000-ply legal list + illegal at ply 1/10/500/end + known case + garbage token.
  7/7 equal python-chess on plain AND ASan builds, 0 san lines. Prefix kept exactly (perft2 identity).
- ALL THREE area-1 jobs are now done.
- Next per brief 2(c): job 1 of area 1 AGAIN with SEED+10 (1111) and a NEW position set (R with SEED+10),
  and say in the report what differs from the first run.

## 2026-11-16 (cycle 2)
- Read FABLE_TO_swarm_2.md. RULE 1 (a zero needs a planted one) applied — and it FOUND A REAL
  DEFECT IN MY OWN RUNNER: readline() had no timeout, so a hung engine hung the harness and my
  "0 crashes/0 hangs" was not shown. Fixed with a queue+thread reader; plant now counted.
  Full 20k re-run with the fixed runner (job1/run_asan_v2) gives identical numbers. See RULE1.md.
- S-C3: CONFIRMS seat 19's 19-F5 (bench is stdin-only, argv ignored) with a control.
- Next: re-run job 1 with SEED+10 = 1111 and a new position set R (brief 2(c)).

## 2026-11-16 (cycle 2, area-1 round 2 = brief 2(c))
- Round 2 DONE: seed 1111, new R set (0 overlap). 20k cases, 0 crashes / 0 san lines / 0 illegal.
  85.44 % refused, 32 py-invalid = 23 F1 (extra token, now reproduced at scale) + 9 adjacent digits.
- PREDICTION 5 WAS WRONG (I said 0 F1 cases; my insert alphabet holds a space). Recorded, not edited.
- Next: cycle 3 board read, then claim the next unconfirmed peer finding (19-F1..F4, 29-F1/F2 remain).

## 2026-11-16 (cycle 3)
- S-C5: 29-F1's DIRECTION reproduced (NNUE off changes bench 13 tree 862329->907205, 1.16x nps).
  Explicitly NOT a reproduction of its profiler shares.
- S-F8 NEW: `setoption name X false` without the `value` word is silently ignored (uci.cpp:265
  name loop swallows the token). This broke my own runner first; fixed, v3 re-run identical numbers.
- Next: area 10 job 2 (recount deepseek6's longK report from its raw files).

## 2026-11-16 (cycle 3, area 10 job 2)
- DONE: recount of deepseek6 long58. The brief's named `REPORT_deepseek6_longK.md` /
  `tests_deepseek6_longK/` DO NOT EXIST on that branch (it has long1..long58); seat 10 had
  long56, so I took long58. All numbers reproduce EXCEPT "best moves changed 6-33", which is
  really 2-33 (FutilityDepth_p 2, FutilityDepth_m 4). S-F9.
- Next: area 10 job 1 (check a NEW unconfirmed peer finding; 19-F2..F4 and 29-F2 remain).

## 2026-11-16 (cycle 4 — HARNESS AUDIT after 19-F12 broadcast)
- 19-F12 (piped `quit` mid-search -> fabricated `bestmove` with 0 nodes) REPRODUCED on my build:
  piped `go depth 12` + quit on startpos -> `bestmove a2a3`, no info lines; with a 3 s wait ->
  `e2e4`, 56,720 nodes, depth 12. Not reported as my finding (seat 19 owns it).
- AUDIT: runner.py (job1, job2, job1r2, all S-F1..S-F9) sends one command at a time and reads to
  `bestmove`/`readyok` before continuing, and sends `quit` only after the last case -> NOT affected.
  Perft-based checks (castle_battery, perft2cmp, check_s01f2, job3) use `go perft`, which completes
  synchronously, and every number equals python-chess's -> not fabricated.
- AFFECTED and INVALID: check_s05f3.py (piped `go depth 10`) — scored nothing. Never recorded as a
  result. Rebuilt on ucio.py (waits for bestmove).
- New file: ucio.py — a waiting UCI driver for all future score-based work.
- Next: verify perft is not fabricated, re-verify a runner.py result with the waiting driver,
  then finish the S-F3 check.
- AUDIT COMPLETE, evidence `checks/verify_runner_not_fabricated.txt`: 12/12 sampled job1r2 cases give
  the same bestmove via runner.py and via the waiting driver, all with real info lines; control
  shows the piped form fabricating `a2a3` with 0 info lines. Perft unaffected (4,865,609 both ways).
- NOT affected: all job1/job2/job1r2 results, S-F1..S-F9, S-C2..S-C6, job3, castle_battery, perft2cmp.
- DISCARDS: one draft of check_s05f3 (piped go depth) — no numbers from it were ever recorded.
- S-C7: CONFIRMS seat 05 S-F3 (draw bites at H=91). Every score positively parsed; a missing
  parse raises MeasurementError and aborts with no verdict (seat 19's NaN warning applied).
  NOTE my cp values differ from theirs (381/271 vs 472/314) — same threshold, different options.
- S-A2 PARSER RE-AUDIT: found one real hole (check_s05f3 treated "no score printed" as "draw
  appeared" -> would have confirmed from nothing). Fixed to raise MeasurementError; live negative
  tests for s19f1/recount/s29f1 all fail loudly. Evidence checks/parser_audit.txt.
- S-C7 re-run AFTER the fix: CONFIRMS S-F3 at H=91, all 11 scores positively parsed.
- S-F10 NEW: the 9-ply-early draw is NOT universal — KRvK and KQvK flip to cp 0 at H=91, but
  KPvK flips only at H=99. Every score positively parsed; KRvKR was refused and gave no verdict.
- S-F11 NEW (goes beyond S-F3): the early draw is a HORIZON effect. Flip H = 96/95/92/91/89 at
  depth 4/6/8/10/12 — moves earlier as depth grows. So "9 plies early" is one point on a curve.
- S-A3 WARM/COLD AUDIT: no Clear Hash used anywhere. My runner pools 500 cases/process so later
  rows are warm: bestmove differs in 4/120 sampled cases warm-vs-cold, BUT illegal bestmoves are
  0 cold AND 0 warm, so the job-1 conclusion holds. Per-position bestmoves/node counts are labelled
  warm-dependent, not cold.
- S-F12 MY PREDICTION FAILED: I predicted the draw flip at depth 14 would be H~87; it is H=89,
  identical to depth 12. So the flip saturates by ~depth 12 — S-F11's "monotone with depth" is
  too strong and is corrected. What survives: flip is depth-dependent (96@d4 vs 89@d12/d14).
- S-F8 strengthened with a positive control: `UseNNUE value false` changes the depth-8 score
  26 -> 10, so the option works when written correctly; only the missing `value` word is silent.

## 2026-11-16 21:58Z CHECKPOINT (deadline 22:30)
Seat 11, area 1 (FEN input under ASan+UBSan). Branch for-fable-and-opus/swarm-11.
DONE (all pushed, raw evidence beside each):
- STEP 1 seat, STEP 2 build + honesty 4/4 (312866/862329/3024920/4865609).
- job1 (20k mutated FENs, ASan+UBSan, 0 crashes / 0 san lines, both sanitizer proofs).
- job2 (30 extreme-number FENs, perft2 vs python-chess 0 diffs), job3 (1000-ply moves list).
- job1 round 2 (seed 1111, new R set).
- Checks: S-C2 (seat 01), S-C3 (19-F5), S-C4 (19-F1 mech), S-C5 (29-F1 direction),
  S-C6 (19-F4 structure), S-C7 (seat 05 S-F3 threshold).
- Findings of mine: S-F1 extra token silently dropped (S-A4 narrows it to reporting only),
  S-F2 adjacent digits (known; proved harmless), S-F8 setoption without `value` word is silent,
  S-F9 deepseek6 long58 "6-33" is really 2-33, S-F10 early draw not universal,
  S-F11/S-F12 early draw is depth-dependent but SATURATES (my d14 prediction failed).
- Audits: S-A1 (19-F12 fabrication, my runner verified unaffected), S-A2 (parser NaN, one real
  hole fixed in check_s05f3), S-A3 (warm/cold: 4/120 bestmoves differ, 0 illegal either way).
- RULE1.md: planted controls for every zero I claim.
NEXT: continue area-1 work; push again by 22:30.
- S-F13 NEW: exhaustive ep-field matrix — 63 of 64 ep squares refused, only the legal `d6`
  accepted (perft 1 = 31 = python-chess). Ep validation is airtight; job 2's sampling generalises.
- S-F14 NEW: all 16 castling-rights subsets on 2 boards, 0 perft differences. Rights rule is
  exactly "king + matching rook on home squares"; accepted masks always match python-chess.
- S-F15 NEW: side-to-move (33 vs 31) and both counters (fullmove, halfmove) leave move generation
  untouched, all matching python-chess, 11/11 probes parsed. My first script had a false "all equal"
  over Nones — fixed to abort with MEASUREMENT FAILED; recorded in the finding.
- S-F16: piece-inventory rule matches board.cpp on 10 generated-FEN boundary cases (no defect).
  Recorded that my first hand-labelled FENs were wrong twice + pawns on rank 8 once — my errors,
  caught by generating FENs from intended counts.
- S-F17: job1's 20k headline replicates identically across 3 full runs incl. the final hardened
  runner (17130/2870/24/0/0), with .meta proving the setoption `value` syntax now takes effect.
- S-C8: CONFIRMS seat 21's 21-F2 — a refused FEN still answers readyok and the next search moves
  for the STALE side (g8f6 Black) vs d2d4 White when accepted. Two of my attempts failed first
  because a 7-field FEN is silently accepted (S-F1), so it never reached the refusal path.
- S-C9 CONFIRMS 21-F9: at halfmove 100 a MATE IN 1 is thrown away (f2f3, cp 0, 0 nodes) in both
  colours and all three go forms; at 99 all find d1d8/d8d1 mate 1. 6/6 vs 6/6. Serious defect.
- S-F18 NEW: mate-throwing boundary is exactly H=100 (mate 140 nodes at 95..99, f2f3 cp 0 at
  100..102). Hard 0-node adjudication — a SEPARATE mechanism from S-F10/S-F11's depth-dependent
  draw threshold.
- S-F19: located the exact cause of 21-F9 — src/search.cpp:2251 root_drawn omits the mate
  exception that is_draw() at :1302 deliberately has ("Checkmate on the hundredth half-move
  still wins"). Root returns score 0 before any search, so the mate is never played.
- S-P1 TEXT PATCH for 21-F9/S-F19: patches/fifty_mate_root.patch.txt applies with `patch -p1`
  without fuzz; honesty 4/4 unchanged; fault gone (6/6 H=100 mate now found); genuine draws and
  the checkmated root still adjudicate at 0 nodes (no regression).
- S-C10 SCOPES 24-F3: G position 90 is 0.04s cold / 0.02s warm on the RELEASE build (no outlier).
  Their 348s figure does not transfer here; likely TSan-specific. I do not claim their numbers are wrong.
- S-C11 CONFIRMS S-F2/24-C1: searchmoves naming no legal root move -> quoted info line +
  bestmove 0000 on a 20-move board; legal names do NOT trigger it (negative control asserted).
- S-C12 CONFIRMS S-F1(12)/24-C2: ucinewgame alone resets to startpos (6/e1f2 -> 20/e2e4 -> 6/e1f2
  after re-sending the position), with python-chess agreeing on both ends.

## 2026-11-16T22:18:45Z CONTINUE: 12 more hours, ends at 2026-11-17T10:18:45Z
- Seat 11 kept (branch for-fable-and-opus/swarm-11, folder forge-combo29/swarm/11). No new seat taken.
- Next: read FABLE_TO_swarm_3/4/5 (1 and 2 already read), then build the PC engine from file 5
  in a separate copy with -DFORGE_MATE_ALPHA_GUARD=1, check its bench numbers, then re-run my
  finds on the PC build under settings PC20 and label every finding with build + settings.

## 2026-11-16T22:21Z PC BUILD READY
- Read FABLE_TO_swarm_3, _4, _5 (1 and 2 read earlier). File 3 confirms my S-F3 withdrawal was RIGHT
  and says a patch for the base tree is NOT needed (so my S-P1 is superseded — see the note I will add).
  File 4: pins are DEFAULT-option numbers, sums are S14 — my honesty check was already correct.
- PC r15 built in /tmp/pcbuild from /tmp/pcbase (separate copy), sha256 of patch matches d6bd72c531f785f4.
  VERIFIED: default 4/4 pins; S14 242796/656517; PC20 278024/587276. All Threads 1.
- THREAD RULE: audited — every result I have recorded used Threads 1 (default or explicit). Nothing to retract.
- NEXT: re-run my finds on the PC build under PC20, labelling each with build + settings.
- RE-RUNS ON PC r15 UNDER PC20 (Threads 1), checks/rerun_pc20.txt:
  * 21-F9 / my S-C9+S-F18: REPAIRED (H=100 mate now found: d1d8, mate 1, 140 nodes; base gave f2f3 cp 0 0 nodes).
    My S-P1 patch is SUPERSEDED — file 3 says no base-tree patch is needed.
  * S-F8: HALF-repaired — now answers `unknown option UseNNUE false` instead of silence.
  * S-F1: STILL PRESENT — extra token still silently dropped on the PC build.
- S-F24: FEN layer on PC r15/PC20 is IDENTICAL to base on every probe (S-F2, S-F13, S-F14, S-F15, S-F16).
  So my FEN findings transfer unchanged to the PC. (Two FEN labels in this run were mislabelled by me again —
  the engine values are right; S-F16 has the correctly generated version.)
- S-F25: closed my own S-F24 mislabel. 8P+2R is LEGAL (2 rooks are original, no promotion needed) and
  8P+2Q is illegal — board.cpp's `promoted > 8-pawns` rule is consistent, engine correct, my labels wrong.
- S-F26: 05-F8/24-C3 NOT repaired on the PC — `go infinite` at a terminal root never volunteers a
  bestmove (6 s window, NO stop sent, ordinary-board control also NEVER). My first probe looked like a
  fix only because my pipeline sent stop; caught and corrected.
- S-F27: the full 20k mutation sweep on PC r15/PC20 gives IDENTICAL numbers to base
  (17130/2870/24/0/0, 99.164 %), all 20 setoptions confirmed in .meta. FEN layer transfers to the PC.
- S-F28: 21-F2 stale-board defect STILL PRESENT on PC r15/PC20 (refused FEN -> readyok -> g8f6, a
  Black move from the old game; accepted form -> h2h3 White). Survives into the owner's engine.
- S-F29: ucinewgame-reset and searchmoves-0000 both UNCHANGED on PC r15/PC20 (same as base).

## 2026-11-16T22:26Z CHECKPOINT (12 h window, ends 10:18Z 17 Nov)
Done since CONTINUE: read files 3/4/5; built PC r15 (sha256 verified) and matched ALL THREE number
regimes (default 4/4 pins, S14 242796/656517, PC20 278024/587276); re-ran my finds on PC20:
- REPAIRED on PC: halfmove-100 mate loss (S-F21) — my S-P1 patch superseded.
- HALF-repaired: S-F8 setoption now reports `unknown option` instead of silence (S-F22).
- STILL PRESENT on PC: S-F1 extra token (S-F23), 05-F8 go-infinite no-volunteer (S-F26),
  21-F2 stale board after refused FEN (S-F28), ucinewgame reset + searchmoves 0000 (S-F29).
- IDENTICAL on PC: whole FEN layer (S-F24/S-F25) and the full 20k sweep (S-F27).
All numbers Threads 1. Next: continue re-running/expanding finds on PC20, STATUS every 25 min.
- S-F30: FORGE_FIX_GO_PARSE proven to FIRE (base reaches depth 1 on `go depth nodes 100`, PC r15
  reaches depth 2; 3/3 runs each). First positive demonstration of a patch switch.
- S-F31: two of the six switches are OFF in the PC patch (BARE_KING_ONE_THREAD 0, ABORT_PUBLISH 0).
- S-F32: FORGE_FIX_ROOT_DRAWN proven to fire — threefold root: base 0 nodes/a2a3, PC r15 26 nodes/d2d4.
  A 2nd occurrence is also searched, matching file 3's "third occurrence" rule.
- S-A5 CRITICAL SELF-AUDIT: my ucio.Engine double-wrapped PC20_LINES, so since the PC build was
  made, every "under PC20" search result actually ran with DEFAULT options (bench proved it: 312866
  vs 278024). Fixed + verified. RETRACTING the PC20 label on S-F21/F26/F28/F29/F30/F32/F33 and
  re-running them all now. S-F20/F24/F25/F27/F34 unaffected.
- S-F33 CORRECTED: with options actually applied, all four PC20 switches change ALL 40 positions'
  nodes and 13-16/40 bestmoves (bench: 253404/308529/287350/271813 vs S14 242796). My earlier
  "0 changed" was the S-A5 bug and is retracted.
- S-F34: re-verified ALL retracted PC20 checks with provably-applying options. Every substantive
  conclusion unchanged (S-F21/F26/F28/F29/F30/F32 stand); only S-F33's result was inverted by the bug
  and is corrected. Options proven applied via bench 278024/242796 through the same Engine.

## 2026-11-16T22:32Z CHECKPOINT
Seat 11 / area 1 / branch swarm-11. PC r15 built + all 3 number regimes matched. Retracted the PC20
label on 7 findings after finding my own harness bug (S-A5), fixed it, re-ran everything (S-F34).
Findings of mine now: S-F1..S-F34 + S-C2..S-C12 + audits S-A1..S-A5 + S-P1(superseded).
Next: continue on PC20 with provably-applied options; STATUS every 25 min.
- PC_SWITCHES.md WRITTEN: all six FORGE_FIX_* with compiled state + measured effect, one line each.
  In his binary: ROOT_DRAWN, GO_PARSE, ISREADY_PENDING, HARD_LIMIT_EMERGENCY, BARE_KING_LMR_CAP.
  NOT in his binary: BARE_KING_ONE_THREAD, ABORT_PUBLISH. Notable: turning BARE_KING_ONE_THREAD on
  changes a lone-king search 106,270 -> 1,431,555 nodes at Threads 1 (13.5x), so its absence matters.
  UNMEASURED (stated as such): ISREADY_PENDING, HARD_LIMIT_EMERGENCY, BARE_KING_LMR_CAP, ABORT_PUBLISH.
  Includes the one-command cross-seat check: bench 11 must read 278024 for PC20, 242796 for S14,
  312866 means NO options were applied.
- Closed the BARE_KING_LMR_CAP gap: it is MEASURED and live — lone-king `6k1/8/8/8/8/8/8/4QK2 w`
  gives e1e7/106,270 nodes with it ON vs f1g1/26,973 with it OFF (bestmove changes); normal
  positions unaffected. PC_SWITCHES.md updated. Remaining UNMEASURED: ISREADY_PENDING,
  HARD_LIMIT_EMERGENCY, ABORT_PUBLISH (stated as such, not inferred).
- S-F37: 553/553 real positions (G+O) accepted on PC20 with 0 perft-1 mismatches vs python-chess.
  Confirms every FEN defect of mine is on synthetic/malformed input only, now on the PC build too.

## 2026-11-16T22:38Z CHECKPOINT
- PC_SWITCHES.md delivered (six switches, state + measured effect, unmeasured ones marked).
- FEN layer on PC20: S-F36 castling field order-independent + duplicates refused; S-F37 553/553
  real positions accepted with 0 perft-1 mismatches.
- Next: continue FEN layer on PC20; STATUS every 25 min.
- S-F38 (systematic S-F28): on PC20 every SHORT FEN (5/4/3/1 fields, and bare `position fen`) is
  refused yet the engine keeps the PREVIOUS board (perft 1 = 26 = old board), while a 7-field FEN is
  silently accepted. Too few = refused-but-stale; too many = accepted-silently.
- S-F40 (most practical FEN finding): a realistic GUI game switch with a TRUNCATED FEN gets
  readyok and then a move from the PREVIOUS game (a7a6, legal in game 1, not in game 2). A silent
  wrong-answer, invisible to anything keying on readyok. Evidence checks/gui_sequence_pc20.txt.

## 2026-11-16T22:44Z FILE 6 APPLIED — two of my verdicts were WRONG
- Read FABLE_TO_swarm_6. Applied its inequality test (2N-1 <= 100-H from counter-0 `go depth 20`).
- S-C9 / S-F18 / S-F19 / S-F10 / S-F11 / S-F12 were NOT defects: withdrawn as defects (numbers stand,
  verdicts do not). At H=100 the budget is 0 so a mate in 1 cannot fit — the engine's draw is correct.
- S-P1 text patch WITHDRAWN (nothing to fix; file 3 already said so).
- S-C7 stands as a measurement only, not as a defect confirmation.
- Re-tested properly: mate-in-1 at every counter on PC r15/PC20 AND base -> 0 defects.
- New standing: file 6 says my finds are worth most on the PC path (PC20, Threads 1, softnodes 2000,
  nodes 20000/50000/250000, 6s+0.06 clock). My FEN work (S-F38/F39/F40) applies there directly.
- S-F41 (file 6's suggested area): `go softnodes N` on PC20/Threads 1/Hash16 is FULLY DETERMINISTIC
  (0/25 differ) and always stops at a finished depth, but overruns N by median 33.6% at N=2000
  (max 220%) and 30.5% at N=20000 (max 135%) across 25 real G positions. One position is not enough
  to characterise it (my single probe had shown 13.4% and 1.5%).
- S-F42: the stale-board defect fires on the PC's REAL path — g8f6 (a GAME-1 move) returned under
  `go softnodes 2000` (self-play), `go nodes 20000` (matches) AND `go movetime 100` (clock) after a
  truncated game-2 FEN. Refusal line IS emitted; a harness must treat it as fatal. This is a live
  wrong-move hazard for the owner's own harness, not a UCI edge case.
- HAZARD_stale_board.md WRITTEN as a standalone doc for the owner (hazard, exact output incl. the
  refusal line, three real search modes, and the one-line rule).
- S-F43: `ucinewgame` DOES clear the stale board but resets to STARTPOS (perft 1 = 20), not to game 2.
  So: invalid FEN is fatal; if continuing in-process, ucinewgame AND re-send a well-formed position;
  safest is a fresh process per game.
- PC_SWITCHES.md updated: explicit "still unmeasured" list = ISREADY_PENDING, HARD_LIMIT_EMERGENCY,
  ABORT_PUBLISH (no probe distinguishes ON from OFF; not evidence of no effect).
- S-F46 (blast radius): the stale-board damage is CONFINED to the one rejected command. game1 -> BAD
  -> game3 gives f3e5 (legal only in game 3) both via `position fen` and `position startpos moves`;
  swept 20 trials: 18 recovered correctly, 0 infected, 2 ambiguous-because-legal-in-both. So a bad FEN
  costs exactly one move, not the session — the rule stands but the radius is one move.
- HAZARD_stale_board.md updated with the blast-radius section: damage is ONE move, not the session
  (18/20 recovered correctly, 0 infected), so the simple defence costs one game.
- S-F47: on the owner's 6s+0.06 clock, PC20/Threads 1 uses only median 238 ms (max 826 ms) over 20
  G positions; 0/20 came near 6000 ms. Startpos 366 ms, 21-piece Italian 149 ms. Not a defect — but
  it means a 6s clock rarely binds, so clock-based match results are effectively "a few hundred ms".
- S-F48: the owner's MATCH setting `go nodes N` is deterministic but stops at a COMPLETED depth and
  so uses LESS than N: median -34% at 20000, -20% at 50000, -22% at 250000 (worst -62%). Example:
  nodes 50000 -> depth 12, 31,779 nodes. Consequence: "nodes 50000" matches are a depth ceiling in
  disguise, not an equal node budget. (Contrast: softnodes OVERSHOOTS by ~33%.)
- S-F51: pathological FENs all refused cleanly on PC20 (3000-char field, 1500 '8/' segments, 70
  ranks, 64-digit rank), each with a specific diagnostic; a 10,000-ply move list is ACCEPTED and
  returns exactly to startpos. Caveat: the 3,000-char control is refused incidentally (pawn-on-
  promotion-rank fires first), not by a length guard.

## 2026-11-16T22:57Z CHECKPOINT
- S-F49/S-F50: node-limited matches are UNEQUAL both across openings and, decisively, between the
  base and PC builds (0/10 same depth at 250k; PC 1-4 plies deeper) -> use fixed depth or the clock.
- S-F46: stale-board blast radius is ONE move (18/20 recovered, 0 infected).
- S-F51: pathological FENs refused cleanly; 10,000-ply list handled correctly.
Next: continue FEN layer on the real path.
- HAZARD_match_protocol.md WRITTEN for the owner: both depth tables (10 openings, 50k and 250k),
  and the one-line rule — do not compare builds at fixed nodes, use fixed depth or the clock.
  Also records why (nodes lands at an iteration boundary, so N buys a depth) and the alternatives.
- S-F52: in-check positions correct on PC20 — 5 hand-built + 15 random all match python-chess's
  evasion counts and every bestmove is legal (0 problems). Check layer is sound on the real path.
- S-F53: `position fen X` and `position startpos moves <path>` are search-identical on PC20 (8/8,
  same bestmove AND same nodes) — a harness rebuilding positions as FENs is not handicapping it.

## 2026-11-16T23:05Z CHECKPOINT
Deliverables for the owner now: HAZARD_stale_board.md (with blast radius) and
HAZARD_match_protocol.md (both depth tables + the rule). PC_SWITCHES.md complete with explicit
unmeasured list. FEN layer on PC20 now covered end to end: acceptance (553/553), in-check (20/20),
pathological input, both position forms, softnodes/nodes/clock behaviour.
Next: continue FEN layer and real-path work.
- S-F55: the hazard DEFENCE is now validated, not asserted. Worst case (the bad FEN IS game 3):
  naive -> g8f6 (game-1 move, WRONG); detect -> aborts, SAFE; fixup (ucinewgame + re-send a good
  position) -> f3e5 (game 3, CORRECT), and 15/15 across different positions. Hazard doc updated.
- S-F57: the SECOND route (illegal move in a move list keeps the legal prefix) verified on PC20 and
  cross-referenced to seat 21's 21-C9/21-C2. HAZARD_stale_board.md REWRITTEN: the real-game
  demonstration is now the opening section, and both routes sit together with the shared shape
  spelled out. The one-line rule now names both `invalid FEN` and `illegal move`.
- S-F58: Route 2 quantified. One illegal token in a 16-ply list silently truncates to the prefix:
  corruption at ply 3 keeps 2 plies and returns a move ILLEGAL in the intended position (3 of 4
  corruption points did). The engine is self-consistent but answering for a board up to 13 plies
  in the past. Every prefix perft matched python-chess (clean, silent, no crash).
- S-F59: the combined `position fen F moves ...` form (worst case for a harness) behaves correctly in
  itself but carries BOTH traps: an illegal move keeps the legal prefix, and a refused FEN inside it
  keeps the PREVIOUS board entirely (perft 1 = 26 = the old 26-move board). Confirms seat 21's 21-C9
  on the PC build.

## 2026-11-17T FINAL (written at 23:07Z; the 12-hour window ends 2026-11-17T10:18:45Z)

**PRIMARY DELIVERABLE: `forge-combo29/swarm/11/HAZARD_stale_board.md`** — the document the owner
should read before his next training or match run. A rejected `position` command leaves the engine
on the WRONG BOARD and it answers `readyok` anyway; two routes (malformed FEN, illegal move in a
list), the real-game demonstration, the one-move blast radius, the `ucinewgame` nuance, and the
three harness protocols tested (naive fails, detect and fixup work, 15/15). Secondary:
`HAZARD_match_protocol.md` (node budgets are not depth-equal) and `PC_SWITCHES.md` (the six
FORGE_FIX_* switches with compiled state and measured effect).

### Every find of mine, with state, build and settings

Builds: **base** = 6b98f217, g++ Release, x86-64-v4 (Threads 1 unless stated); **PC r15** = base +
the FABLE_TO_swarm_5 patch, `-DFORGE_MATE_ALPHA_GUARD=1`, verified against all three number regimes.
Settings: **none** (no setoption), **S14** (the 14 settings), **PC20** (S14 + the six).

| id | state | one-line | build / settings |
|---|---|---|---|
| S-F1 | open (harmless, S-F44) | extra token after the sixth FEN field silently dropped; board identical | base none; PC20 |
| S-F2 | confirmed-known (Opus file 1) | adjacent digits accepted; proven cosmetic (S-F45) | base none; PC20 |
| S-F3 | WITHDRAWN by me | I wrongly claimed to refute Opus's castling line | — |
| S-F4 | open | 20k mutated FENs: 0 crashes, 0 san lines, both sanitizer proofs | base ASan+UBSan |
| S-F5 | open | extreme FEN numbers: bounds correct, stricter than python-chess | base ASan |
| S-F6 | open | 1,000-ply list + illegal move keeps legal prefix | base, ASan |
| S-F7 | open | F1 reproduced at scale (23/20,000) | base ASan |
| S-F8 | open, HALF-repaired on PC (S-F22) | `setoption` without the `value` word silently ignored on base; now reports `unknown option` on PC | base none; PC20 |
| S-F9 | open | deepseek6 long58 says "6-33" changed moves, really 2-33 | n/a (raw files) |
| S-F10 | WITHDRAWN as defect (S-A6) | "early draw" — file 6: correct behaviour | PC20, base |
| S-F11 | WITHDRAWN as defect (S-A6) | same | PC20 |
| S-F12 | WITHDRAWN as defect (S-A6) | my own prediction failed anyway | PC20 |
| S-F13 | open | ep field: 63/64 refused, the legal one correct | base none; PC20 |
| S-F14 | open | all 16 castling subsets, 0 perft differences | base; PC20 |
| S-F15 | open | side/fullmove/halfmove independent of movegen | base; PC20 |
| S-F16 | open (no defect) | inventory rule matches board.cpp on 10 generated cases | base |
| S-F17 | open | job1 headline replicates across 3 full runs | base ASan |
| S-F18 | WITHDRAWN as defect (S-A6) | mate at H=100 — correct per file 6 | PC20 |
| S-F19 | WITHDRAWN as defect (S-A6) | root adjudication — no defect | source read |
| S-P1 | **WITHDRAWN** | text patch for a non-existent defect; marked DO NOT APPLY | — |
| S-F20 | open | PC r15 build verified: all 3 number regimes match | PC r15 |
| S-F21 | open (repaired on PC) | halfmove-100 mate loss gone on PC | base vs PC20 |
| S-F22 | open | setoption now reports `unknown option` on PC | PC20 |
| S-F23 | open | extra token still accepted on PC (still harmless, S-F44) | PC20 |
| S-F24 | open | whole FEN layer identical on PC20 vs base | both |
| S-F25 | correction (mine) | 8P+2R legal, 8P+2Q illegal — engine right, my labels wrong | both |
| S-F26 | open | `go infinite` at terminal root never volunteers a bestmove on EITHER build | both |
| S-F27 | open | 20k sweep on PC20 = base exactly (17130/2870/24/0/0) | PC20 |
| S-F28 | open — HAZARD | refused FEN leaves stale board (wrong side to move) on PC | PC20 |
| S-F29 | open | ucinewgame resets to startpos; searchmoves-no-legal -> 0000 | both |
| S-F30 | open | `FORGE_FIX_GO_PARSE` demonstrably fires (depth 1 vs 2) | base vs PC20 |
| S-F31 | open | two of six switches compiled OFF (BARE_KING_ONE_THREAD, ABORT_PUBLISH) | source |
| S-F32 | open | `FORGE_FIX_ROOT_DRAWN` demonstrably fires (threefold searched) | base vs PC20 |
| S-F33 | corrected | all four PC20 switches materially change the search | PC20 |
| S-F34 | open | all retracted PC20 labels re-verified; conclusions stand | both |
| S-F35 | open | movetime = T - ~9.4 ms fixed, unchanged on PC | PC20 |
| S-F36 | open | castling field is an unordered set; duplicates refused | PC20 |
| S-F37 | open | 553/553 real positions accepted, 0 perft mismatches | PC20 |
| S-F38 | open — HAZARD | every SHORT FEN refused but stale board kept | PC20 |
| S-F39 | open | same on base — not a PC regression | both |
| S-F40 | open — HAZARD | GUI game-switch with truncated FEN gets previous game's move | PC20 |
| S-F41 | open | softnodes deterministic, stops at finished depth, overruns 30-34% median | PC20 |
| S-F42 | open — HAZARD | hazard fires under softnodes/nodes/movetime | PC20 |
| S-F43 | open | ucinewgame clears to STARTPOS, not your position | PC20 |
| S-F44 | open | extra token harmless: 60/60 real-path searches identical | PC20 |
| S-F45 | open | adjacent-digit cosmetic: 25/25 identical | PC20 |
| S-F46 | open | blast radius ONE move: 18/20 recovered, 0 infected | PC20 |
| S-F47 | open | 6s clock uses only median 238 ms; clock rarely binds | PC20 |
| S-F48 | open | `go nodes N` undershoots N by 20-34% (depth-boundary) | PC20 |
| S-F49 | open | depth spread across 10 openings is 3-4 plies (unequal) | PC20 |
| S-F50 | open — MATCH PROTOCOL | paired depth: same on 4/10 at 50k, 0/10 at 250k | base vs PC20 |
| S-F51 | open | pathological inputs refused cleanly; 10k-ply list correct | PC20 |
| S-F52 | open | in-check positions correct, 20/20 | PC20 |
| S-F53 | open | `position fen X` vs `position startpos moves` identical, 8/8 | PC20 |
| S-F54 | open — HAZARD demo | hazard reproduced end-to-end in a real self-play game | PC20 |
| S-F55 | open — DEFENCE VALIDATED | naive fails, detect and fixup work; fixup 15/15 | PC20 |
| S-F56 | open | accepted-unreachable boards generate correct moves | PC20 |
| S-F57 | open | Route 2 (illegal move in a list) verified + cross-ref 21-C9/21-C2 | PC20 |
| S-F58 | open | corrupted list silently drops up to 13 plies | PC20 |
| S-F59 | open | combined `fen ... moves` carries both traps | PC20 |
| S-F60 | open | fresh process + bad first command leaves STARTPOS, not a stale game | PC20 |
| S-F61 | open | en-passant capture actually generated and counted | PC20 |
| S-C2 | CONFIRMS seat 01 S-F2 | impossible double check accepted, perft right | base |
| S-C3 | CONFIRMS 19-F5 | bench is stdin-only, argv ignored | base |
| S-C4 | CONFIRMS 19-F1 mechanism (not %) | residual net: eval reports hce+nnue | base |
| S-C5 | consistent with 29-F1 (direction only) | NNUE off changes the bench tree | base |
| S-C6 | consistent-with 19-F4 (structure only) | one see_ge symbol vs 3 generator instances | nm |
| S-C7 | measurement only (defect withdrawn, S-A6) | fifty-move threshold at H=91 | base, PC20 |
| S-C8 | CONFIRMS 21-F2 | refused FEN -> stale board, wrong side to move | base |
| S-C9 | WITHDRAWN as defect (S-A6) | = 21-F9, correct per file 6 | PC20 |
| S-C10 | SCOPES 24-F3 | G position 90 is 0.04 s cold on release (no outlier) | base release |
| S-C11 | CONFIRMS 02 S-F2 / 24-C1 | searchmoves with no legal move -> 0000 | base; PC20 |
| S-C12 | CONFIRMS 12 S-F1 / 24-C2 | ucinewgame resets the board | base; PC20 |
| S-A1 | audit | 19-F12 fabrication; my runner verified unaffected | base |
| S-A2 | audit | parser NaN: one real hole found and fixed | all |
| S-A3 | audit | warm/cold: 4/120 bestmoves differ, 0 illegal either way | base |
| S-A4 | audit | S-F1 narrowed to a reporting defect | base |
| S-A5 | audit — RETRACTION | my ucio double-wrapped PC20 options; labels retracted | all |
| S-A6 | reverdict | mate/draw "defects" are NOT defects per file 6 | both |

### What is still UNMEASURED or open, stated plainly
- Three of the six `FORGE_FIX_*` switches: `ISREADY_PENDING`, `HARD_LIMIT_EMERGENCY`,
  `ABORT_PUBLISH` — no probe I built distinguishes ON from OFF, so I claim nothing about them.
- The brief's `REPORT_deepseek6_longK.md` does not exist; I recounted long58 instead (S-F9).
- I never ran anything above Threads 1 for a score claim; every number here is Threads 1.
- S-F62: after a refused FEN, ONLY `ucinewgame` clears the stale board. `isready`, `eval`, `stop` and
  `go perft` all leave it in place (the go still returns a game-1 move). So "resync with isready" —
  exactly what a GUI does — does NOT defend. The defence is to DISCARD the game, not to resync.
- S-F63: a refused FEN does NOT contaminate the transposition table — `go depth 12` on a later target
  gives identical results (e4d5, 60,955 nodes, cp 83) with or without a preceding refused FEN. So the
  blast radius is one command / one answer / no residue. Blast-radius picture now complete.

## 2026-11-16T23:10Z progress (window still open to 10:18Z)
- Move generation on PC20 now VERIFIED: perft 1-4 x 12 G positions = 48/48 match (incl. a 6,040,815
  node perft 4), perft 5 x 4 sparse positions = 4/4 match. Feature divides all correct: ep capture
  generated (S-F61), castling transit in all four edge cases (S-F64), all four promotion kinds incl.
  push+capture eight-way (S-F65).
- Hazard note: rule line now "Fatal on invalid FEN or illegal move: resync only with ucinewgame plus
  a well-formed position, never isready." S-F62 proved isready/eval/stop do NOT clear it. S-F63 proved
  no hash residue (identical 60,955-node search), so blast radius = one command, one answer, no residue.
- PROBES_THAT_LIED.md WRITTEN and linked from the hazard note: the promotion probe whose FEN put the
  pawn on the king's square (looked like missing promotions; python-chess agreeing 5=5 was the tell),
  the go-infinite probe whose own shell sent the stop (looked like a fix), plus the tuple-unpacking
  false-defect and the mislabelled-FEN cases. Each with the tell, the control, and the corrected result.
- S-F70: full 49-ply game on the 6s+0.06 clock, clocks tracked honestly: NO flag fall (white 2,021 ms
  / black 1,669 ms left), 0 illegal, slowest move 841 ms. Clock path is safe for real play.
- S-F69: self-play at softnodes 2000 is deterministic and terminating — two games each exactly 212
  plies ending by insufficient material, 424 moves 0 illegal; each passed 9 threefold positions
  without the engine ending it (correct: that is the match program's job, per file 6).
- S-F71: ponder is sound on PC20 — `go ponder` alone waits (emits nothing in 3 s), +ponderhit gives a
  real searched move (g1f3, legal), +stop gives the shallow first-legal move (a2a3, correct UCI
  semantics). A pondering match program will not hang.
- S-F72: match decisions are REPRODUCIBLE at Threads 1 — 0/12 unstable at nodes 20000/50000/250000
  (bestmove+nodes+score all identical across fresh processes). The S-F49/S-F50 unequal-depth problem
  is cross-build fairness, NOT within-build randomness: two separate issues, only one needs a fix.
- S-F75: as the node budget grows the search SETTLES — depth monotone up every time, 7/8 positions
  keep the same bestmove across 20k/50k/250k, the 8th changes once then holds. Combined with S-F72
  (reproducible), node-limited matches are converged as well as stable.
- S-F78: `go wtime 6000` WITHOUT btime does not hang but searches ~12 s instead of 136 ms — the time
  manager needs BOTH clocks; the side to move's budget is effectively unbounded if omitted. My first
  probe read the 30 s cutoff as a hang; the full output showed depth 31 at 18.9 M nodes. Protocol
  requirement, not a defect: always send both wtime and btime.
- S-F79 (rest of the clock matrix): movestogo 1 = 2,020 ms vs movestogo 40 = 98 ms; wtime 0 answers in
  1 ms; movetime 0/5 answer in 1 ms; wtime 999999999 searches >45 s which is CORRECT (eleven days of
  requested thinking time), not a hang — and I did not read it as one, per trap 2b.
- S-F80: uci_guard.py — a guard harness implementing both documented defences, SELF-TESTED against
  the real engine: refusal raises + resyncs to startpos (next search gives d2d4, no leak), and a
  one-sided clock is refused before it can cost 12 s. Real queue deadline, sanitizer check, and the
  trap-2b warning in its timeout message.
- S-F81: uci_guard.py verified against ROUTE 2 as well — an illegal move in a list raises
  PositionRejected and the next search gives d2d4 (startpos), not the truncated-prefix answer; a
  one-sided clock raises ValueError before any search. The guard covers both routes and the clock rule.

### FINAL ADDENDUM (23:31Z) — deliverables and findings since the FINAL block above
Four documents are the record, in reading order:
1. **HAZARD_stale_board.md** — PRIMARY. Two routes into a stale board, the real-game demonstration,
   one-move blast radius, the `ucinewgame`-vs-`isready` table, three protocols tested, the
   one-sentence rule, and a pointer to the guard harness.
2. **HAZARD_match_protocol.md** — node budgets are not depth-equal (paired 0/10 at 250k), always send
   both clocks (136 ms vs 12 s), the engine relies on your program to end games (9 threefolds passed).
3. **PROBES_THAT_LIED.md** — five harness traps incl. trap 2b, each with the control that killed it.
4. **uci_guard.py** — the guard harness; self-tested against both routes and the clock rule.

Additional findings since the FINAL block, all PC r15 / PC20 / Threads 1, all open (no defects):
S-F68 (probes note), S-F69 (self-play deterministic, 212 plies), S-F70 (full clock game, no flag
fall), S-F71 (ponder sound), S-F72 (match decisions reproducible, 0/12 unstable), S-F73 (searchmoves
restricts correctly), S-F74 (MultiPV correct; MultiPV 1 omits the field), S-F75 (search settles across
20k/50k/250k), S-F76 (mid-search interrupts never hang, both bestmoves attributed), S-F77 (extreme
`go depth` clamps safely; depth 40 found mate 9 at 172.6 M nodes), S-F78 (missing `btime` = 12 s not
136 ms), S-F79 (movestogo/zero/huge clocks all safe), S-F80 (guard self-test), S-F81 (guard vs Route 2), S-F82 (a ~1,000 M-node search is stable: depth 64
reached 978,487,626 nodes with the same `mate 9`/`f4f5` as depth 40, and depth 100 reproduced it
exactly — no overflow at 10^9 nodes, no illegal move, which bounds the engine's top-end risk), and
S-F83 (all seven classic endings score correctly: KQvK mate 7, KRvK +571, K/KN/KB v K all exactly
cp 0, KNNvK +327 without a false mate, KQvKR +260).

Withdrawn or corrected, retained rather than deleted: S-F3, S-F10, S-F11, S-F12, S-F18, S-F19, S-C9
(not defects under file 6), S-P1 (patch withdrawn, marked DO NOT APPLY), S-A5 (my PC20 labels
retracted after the uci double-wrap bug), S-F25/S-F33/S-F25 corrections of my own errors.
- S-F82: a ~1,000 M-node search is stable — depth 40 = 172.6 M nodes (mate 9), depth 64 = 978,487,626
  nodes (mate 9), depth 100 identical to depth 64 (converged). No overflow at 10^9 nodes.
- uci_guard.py usage rewritten as a runnable example: the three calls in order (position, bestmove,
  exception handler) plus a context-manager form; syntax-checked and the self-test still passes.
- S-F86: no gross blunders at match budget — playing the engine's own move and re-searching the reply
  at the same budget, the largest score swing one ply later is 48 cp (median ~13) over 10 positions.
  Its evaluation is self-consistent under its own best reply.
- S-F87: the guard's deadline is PROVEN against a planted hang — a fake engine that never sends
  bestmove produces a GuardError after exactly the 3.0 s timeout, with the trap-2b note attached.
  This is the specific failure my own first runner.py had, so the guard is shown to fix it.
