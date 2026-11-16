## 2026-11-16T23:25Z FINAL (continuing to work; this block is the complete inventory as it stands)

**A pattern worth recording, with a progression: TEN times tonight the real finding was a CONTROL error in my own test, not the engine - and the tenth was caught AT THE DESK, before publishing, rather than in review.** The earlier nine: a different-depth comparison (S-C27), a regex match compared to the wrong string (check_05F14), a PV retyped from memory (S-F27), a 13-board sample standing in for a recommendation (S-C17), a single Hash axis (S-C22), a one-clock answer read as a constant (27-F12), two false mismatches from `audit_final.py`'s own matcher, and a false FAIL from `final_selfcheck.py`'s own assertion. **When a result looks surprising, check the harness before the engine.** The mechanical forms of the habit are `compliance_check.sh` (the brief's rules), `audit_final.py` (no withdrawn finding left live in this document) and `final_selfcheck.py` (the live headline claims re-run, 4/4 PASS). Two of those checkers produced false failures on their own first run, which is the best illustration the line could have - and the tenth error being caught before publication is the progression worth noting.

**A second pattern, and a better self-description than a list of corrections: my findings tend to be right about the mechanism and NARROW about the scope.** Four times tonight another seat's formulation was one axis wider than mine - seat 05's boundary (position-dependent, not one rule), seat 19's budget ratio (both limit types, not just softnodes), seat 30's MultiPV (which needed the Hash axis), seat 20's S-F53 (any report-without-search path, not just resolved roots). Each time my statement was true and theirs was truer. So when a finding looks clean, the question to ask is **"what else is this an instance of?"** before publishing it.

**Read this first:** across every command tested, the **MOVE** the engine returns is stable run to run; **scores from a clock-based search are approximate** (a few centipawns of run-to-run variation, because the stop is wall-clock dependent - 6 runs gave cp 55 and cp 67 at depths 16 and 18); **scores from `go nodes` and `go softnodes` are exact** (fully deterministic in score, nodes, depth and move). So a training pipeline may label moves freely from any command, but must treat clock-derived scores as approximate and only node-limit-derived scores as exact.

**GUARD RESULTS (all three re-run at 2026-11-16T23:55Z, and re-run again at the close):**
`compliance_check.sh` -> **PASS** (0 tracked binaries, 0 files outside my folder, 0 non-text, 0 engine source, nothing uncommitted) |
`audit_final.py` -> **0 mismatches** (no finding marked dead in FINDINGS.md is left live in this document) |
`final_selfcheck.py` -> **4/4 PASS** (S-F29 depth-18 threshold, S-C26 terminal ladder, S-C27 burst + correct answer, S-C22 Hash-16 ladder above Hash-256). The self-check names what it does NOT cover, so a 4/4 is not whole-document verification: full games, regime sweeps, and the variant-build and seat-27-binary checks carry their own evidence files. Note that the Hash-256 depth in that cell reads 4 or 2 depending on the run - which is S-C15 itself (a clock search varies in depth), and the assertion tests only Hash16 > Hash256, so it is correct either way.

Seat 25, area 5 (principal variations and scores). Branch for-fable-and-opus/swarm-25, folder
forge-combo29/swarm/25/. Build used for everything PC: PC r15 from FABLE_TO_swarm_5 (patch sha256
d6bd72c531f785f4... matches), PC20, Threads 1, Hash 16 unless a line says otherwise. Base-tree findings used
build 6b98f217, S14. All four honesty pins hold on every build I used: 312866 / 862329 / 3024920 / 4865609.

### REASSURANCE FIRST: the owner's real match setting is clean end-to-end (S-F30)

A full **90-ply self-play game** at the owner's exact match configuration - PC r15, PC20, Threads 1, Hash 16,
`go nodes 20000`, one fresh process per move - came out clean:

| check | result |
|---|---|
| illegal moves / no legal move | **0** |
| moves whose final `info` line was missing | **0** |
| moves chosen from a COMPLETED iteration (non-empty PV) | **90 / 90** |
| game termination | normal (threefold repetition) |
| nodes actually spent / 20000 | median **0.75** (0.34-1.00) |

So at the setting his matches actually use, over a whole game, **none of the defects in this report fires**.
The 0.75 figure independently reproduces the budget ratio I confirmed against seat 19 (S-C12).
Evidence: `pcpath/match_game.py`, `pcpath/match_game.txt`.

**Both game endings are now covered.** A second self-play game forced to end in mate (S-F31) reached CHECKMATE
at ply 3 with 0 illegal moves, 0 missing info lines, 3/3 completed-iteration moves and **3 mate scores of which
none had a PV that fails to play out** (every PV sliced from the engine line and replayed). So repetition and
checkmate - the two ways a match actually ends - are both clean at the owner's setting.

### THE HEADLINE FINDING FOR THE OWNER (file 6's half-move test needs depth)

**File 6's test for whether a high-counter `cp 0` is a defect requires a deep search, and the real threshold is
depth 18, not 20. Applying the rule at depth 10-16 produces a FALSE "no forced mate" and would wrongly dismiss a
real defect.** Six mate-rich boards x depths 8/12/14/16/18/20/22/24 on PC r15/PC20/Threads 1/Hash 16:
- QR vs K, Q+R vs K and my S-F1 board report their mate from **depth 8**.
- The KQ-vs-K board (`8/8/8/8/3k4/8/8/K1Q5 w`) needs **depth 18**: `cp 1359` at depth 16, `mate 9` at 18,
  `mate 8` at 20. So depth 16 is already wrong on a board that has a mate.
- **Two boards never resolve a mate within depth 24** and report ordinary scores: KQ vs K in the centre
  (`cp 18-25`) and KR vs K (`cp 534`). Read those as **no mate inside the horizon**, NOT as a broken engine.
  Use depth 20+ as file 6 says, and try 24 before concluding anything.
Evidence: `check_file6/depth_requirement.py`, `check_file6/depth_requirement.txt` (8x6 table, rows copied from
engine output), written up in `check_file6/HOW_TO_APPLY_FILE6.md`.

### FINDINGS THAT STAND

| id | one line | build + settings |
|---|---|---|
| S-F1 | Base tree: `8/8/1p6/8/p3p3/8/2Kpk3/8 w` says `mate -12` at depth 12-16; plain minimax and the engine's own depth-24 PV (8 plies, verified checkmate) both give **mate -4**, so the shallow score is wrong by 8 moves. **REPAIRED on the PC build** (`mate -4` at depth 12 under PC20). | base/S14; PC/PC20 |
| S-F2 | That root's mate score wanders -12/-9/-6/-5/-4 with depth. | base/S14 |
| S-F6 | **WITHDRAWN as a defect (S-C26).** A checkmated root answers `mate 0` / `0000` / 0 nodes, and I had filed that as an undefined token. Seat 11 showed why it is not, and I verified the ladder myself on PC20: checkmated -> `mate 0`/`0000`/0 nodes; **mate in 1 -> `mate 1`/`a1a8`/105 nodes** (a real move); stalemated -> `cp 0`/`0000`; dead draw -> `cp 0`; KQvK -> `cp 1107`/2,779 nodes. `mate 0` and `mate 1` are DIFFERENT signals: 1 = mate available (with a move), 0 = already mated (with 0000). Under UCI's `score mate y` = mate in y moves, y = 0 is the natural encoding of "mated now". Seat 21's 21-F11 was withdrawn for the same reason. Surviving consumer note only: a reader assuming \|y\| >= 1 must handle 0. | base and PC/PC20 |
| S-F7 | **COSMETIC - and SCOPE SUPERSEDED by seat 20's S-F53 (S-C29).** The correct statement is broader: **any path that reports WITHOUT SEARCHING emits one info-depth line per depth, capped at the requested depth or at 64.** Verified on three such paths on PC20: terminal root, resolved mate root, and empty-`searchmoves` (`go depth 5 searchmoves a7a8` -> bestmove 0000 plus `info string searchmoves restriction has no legal root moves`) - all give 5 lines at `go depth 5` and 64 at `go nodes 50000`. The answer a consumer reads is still correct (S-C27: identical to `go depth 10`), so it remains cosmetic. Consumer advice: take the last line or the bestmove, not iteration counts. | base and PC/PC20 |
| S-F8 | Middlegame `2b2knr/...` says `mate -9` at depth 12 where depth 24 gives `mate -7` with a verified 14-ply mate. **REPAIRED on the PC build** (`mate -8`). | base/S14; PC/PC20 |
| S-F9 | Wrong-mate-score rate across three independent sets: 2 of 28 mate scores (~7%), and in both cases the SCORE was wrong, never merely the PV. | base/S14 |
| S-F10 | The wrong mate score is not state: a fresh process reproduces it, and a correct deeper search followed by `ucinewgame` returns to the wrong number in the same process. | base/S14 |
| S-F25 | `go softnodes` is deterministic (identical score/nodes/move), always stops at a FINISHED depth, and overshoots N by 1.06-1.55x. Independently reproduced by seats **08, 19 and 29**. | PC/PC20 |
| S-F26 | **NEAR-MISS, NOT A DEFECT - DO NOT "FIX".** The match path uses only 2.4-8.7% of its clock (178 ms of 6 s), which is `plan_clock_budget`'s soft limit working (TmSoftDivisor 22 -> 317 ms at 6 s); `go movetime` differs because it is a hard instruction. Corroborated by four seats; raising time usage would lose on time. **Caveat added (S-C15): a clock search is deterministic in the MOVE only** - at 6 runs the score took 2 distinct values (cp 55 / cp 67), nodes 2 (172,312 / 309,981) and depth 2 (16 / 18), while the move never varied. `go nodes` and `go softnodes` are fully deterministic. So a pipeline recording SCORES from clock searches must treat them as approximate; the moves are trustworthy. | PC/PC20 |
| S-F29 | The depth-20 threshold finding above. | PC/PC20 |
| S-F35 | **WITHDRAWN - refuted by my own wider sample (S-C17).** I reported that `go softnodes 20000` fixes both label faults completely, based on 13 boards. On 40 mate-rich boards the opposite holds: `softnodes 2000` -> 0 undeliverable / 1 differing, while `softnodes 20000` -> **2 undeliverable / 3 differing**. So 20000 is WORSE on the wider set and the 13-board result was a coincidence. Likely reason: at 2000 only 7 of 40 boards emit a mate score at all, at 20000 19 do, so a higher budget moves the engine INTO the depth range where premature mate claims appear. **Revised recommendation: do not rely on a budget - validate mate PVs in the label pipeline**, because both 2000 and 20000 emit undeliverable mate claims on worst-case boards. | PC/PC20 |
| S-F36 | **MECHANISM: a bigger softnodes budget creates MORE mate claims, so no budget fixes this.** At `softnodes 2000` only **7 of 40** mate-rich boards emit a mate score at all; at `softnodes 20000`, **19 of 40** do. An undeliverable mate claim is a function of how often claims are made, not of budget quality - so raising the budget moves the engine into the depth range where premature claims appear, and the count of bad claims rises with the count of claims. That is why S-F35's "use 20000" could not work in principle, and why the fix is **PV validation in the pipeline**, not a budget choice. | PC/PC20 |
| S-C31 | **The label rule, measured - and it is a FILTER, not a budget: reject any mate score whose PV length != 2\|N\|-1 (or 2\|N\| for negative N).** On the three boards that exhibit the defect (softnodes 500..20000) the classes are **SHORT 4, ok 8, right-length-not-mate 0** - so every failure is a PV that stops short of its own claimed distance, i.e. the score is not broken and the report is premature, and the filter **catches every observed failure** - which is all it is shown to do; it does **NOT validate a passing score**, since a right-length PV that ends in checkmate could still be a longer mate and I did not test that. A filter for the measured failure shape, not a correctness proof. **And the near-miss is the practical warning: both rejected cases were only ONE MOVE long** (`mate 4` with 6 plies where 7 were needed; `mate 5` with 8 where 9 were needed), so they came within a single ply of passing the filter while being wrong about the distance. Anyone relying on it should expect that a barely-failing score is the common case, not a distant one. It also explains S-F34's "one move pessimistic": a still-converging mate reports one move too long (4Q3/8/r2K4/ -> mate 4/SHORT at softnodes 1000-2000, mate 3/ok from 5000). **Positive result kept: 12 of 12 mate scores correct on a random 40-board sample at softnodes 2000** - the failure is board-specific (it needs a mate converging at that exact budget), which is a sampling fact, not a contradiction. |
| S-F34 | **THE TWO MEASURED REASONS TO RAISE THE SELF-PLAY BUDGET FROM 2000** (13 mate-scored endgame boards, PC20/Threads 1/Hash 16): **(1) label validity** - at `go softnodes 2000`, **1 of 13** mate scores has a PV that does not play out (6 plies claimed as mate 4, which needs 7), versus **0 of 13** at `go nodes 20000`; **(2) label magnitude** - **3 of 13** boards report a mate number ONE MOVE LONGER than the match setting reports (mate 4 where the match setting correctly says mate 3). So self-play mate labels at 2000 nodes can be both pessimistic by a move and undeliverable by their own line, while the match budget is clean on the same boards. Middlegame caveat: 2000-node searches rarely emit mate scores at all (1 in 100), so real-corpus rates are far lower - these are the worst cases. | PC/PC20 |
| S-F33 | **At `go softnodes 2000` (self-play, depth 6) a mate PV can be one ply short of its own claim.** Board `4Q3/8/r2K4/8/2B5/5R2/1k6/8 w` reports `mate 4` with a 6-ply non-mate (needs 7) at softnodes 2000, and the correct `mate 3` with a verified 5-ply checkmate at `go nodes 20000`. Horizon truncation at shallow depth, not a wrong number - but it means a self-play label can carry a PV that does not play out AND a mate distance one move pessimistic. 0 illegal PVs at either setting over 100 positions. | PC/PC20 |
| S-F32 | **Every degenerate clock regime returns a legal, stable move** - `movestogo 10`, increment-only (`wtime 0 winc 1000`), `wtime 50`, and even `wtime 0 btime 0 winc 0 binc 0`: all legal, no hang, no crash, move identical across 3 runs each. `movestogo` correctly spends far more (depth 19, 312 ms) than the no-movestogo case, per `plan_clock_budget`'s 1/(mtg+1) branch. | PC/PC20 |
| S-F31 | **Both game endings are clean at the match setting.** A forced-mate self-play game (start `4k3/8/8/8/8/8/8/K1QR4 w`, `go nodes 20000`, one fresh process per move) ends in CHECKMATE at ply 3 with 0 illegal moves, 0 missing info lines, 3/3 completed-iteration moves, and **3 mate scores of which 0 had a PV that fails to play out** (PVs sliced from the engine line and replayed, never typed). With S-F30 (90-ply, repetition) both endings are covered. Node spend median 0.13x N because a decided mate is found quickly - the "search resolved early" behaviour, not a fault. | PC/PC20 |

### CONFIRMATIONS / CHECKS OF OTHERS

| id | what | result |
|---|---|---|
| S-C1 | seat 06 S-F10 | confirms the depth-10 depth-10 mate result, with the correction that "mate machinery sound" does not generalise to depth 12 |
| S-C3 | seat 06 S-F21 | **exact** reproduction: 101/353 bestmoves not the mirror (28.6%), 334/353 scores unequal (94.6%), with a 180-rotation plant caught 5/5 |
| S-C4 | FABLE_TO_swarm_5's honesty table | **all six numbers exact** on my own build (312866/862329/3024920/4865609; 242796/656517; 278024/587276) |
| S-C5 | file 6 applied to my own boards | **0 of 8 survive** as defects (budget at counter 99 is 1 half-move; no board has a forced mate) |
| S-C6 | file 6 positive control | the rule is **not vacuous**: one board fires at counter 91 (mate 8 at counter 0, cp 0 at the real counter, 15 > 9), and the engine reports the mate whenever the budget allows |
| S-C7 | seat 05 S-F14 | **partly confirms, partly refutes**: my 21-piece board is flat `cp 0` at counter 99 for depths 6-12 (confirmed); the pawnless variant scores +63..+87 at counter 100, not a draw (refuted on PC r15; they used the base tree) |
| S-C12 | seat 19 19-F46 | **numerically confirms**: `go nodes` ratio median 0.67 vs their 0.68, `go softnodes` 1.21 vs 1.219, softnodes deeper in 18/18 |
| S-C18/19/20 | **27-F12 ("clock ignored when Black is to move") - SETTLED, closed.** Refuted independently by me on BOTH builds and by seat 30 (30-C40, matching numbers plus a 12-of-12 side-to-move check), **and the origin of its number identified**: the "constant" 286,156 nodes is the BASE build's answer at `wtime 3000`, read as if invariant across wtime 0..3000. Three lines of evidence plus a mechanism for the error. |
**THREAD ORDER (the superseded first statement is part of why the last one is trustworthy):** S-C21 my too-narrow "clock x MultiPV" measured at one Hash -> **S-C22** three conditions with the Hash-16 control ladder -> **S-C23** the mechanism and the falsifiable patch threshold -> **S-C24** what to actually do. Each step is a correction of the one before it, kept in place rather than tidied away.
| S-C21 | **Superseded by S-C22/S-C23** - I first reported the MultiPV instability as "the clock x MultiPV pair", measured at Hash 256 only, and generalised one axis too far. |
| S-C22 | **Three conditions, corrected: clock + MultiPV>1 + LARGE HASH.** Hash 16 gives a clean, stable ladder (MPV1/2/3/4 -> depth 16/15/13/11, every cell exact) - that ladder is the CONTROL proving MultiPV itself is sound. Hash 256 collapses (MPV2 [4,5], MPV3 [4], MPV4 [2,4], with run-to-run spread) while MPV1 stays exactly depth 16 / 172,312. `go depth 12` is exact at both Hashes for every MPV. **Match path (MPV1) unaffected at every Hash.** |
| S-C23 | **MECHANISM: the between-line TT clear eats the clock budget.** At MPV3, nodes searched per ms falls **559 (Hash 16) -> 183 (64) -> 2 (256)** while depth falls 13 -> 9 -> 4; at Hash 256 the engine spends **290 ms to search 622 nodes** (2 nodes/ms) against **1,566 nodes/ms** at MPV1. MPV1 is unaffected by Hash (depth 16 / 172,312 at Hash 16 through 1024). **Falsifiable prediction: a patch that removes the redundant clear should bring MPV3+Hash256 to ~1,500 nodes/ms, not ~0.** |
| S-C24 | **PRACTICAL ADVICE, measured.** On a CLOCK (`wtime 5000`) at MPV3 depth falls monotonically with Hash: **16 -> 13 (fine), 32 -> 10, 64 -> 10, 128 -> 7, 256 -> 4, 512 -> 1**; with a DEPTH LIMIT Hash is free (`go depth 20` reaches depth 20 at Hash 16, 64 and 256). **On a clock with MultiPV > 1 keep Hash 16; for deep analysis under a depth or node limit, Hash is free.** |
| S-C33/S-C34 | **`movestogo 0` is NOT an engine bug - it means "one move to go" after the clamp, and last-move budgeting correctly spends about half the clock. The error is a CALLER that sends 0 meaning "unknown".** At the match clock, field omitted -> 179/161/381 ms (3.0-6.3% of 6,060) at depth 18; `movestogo 0` -> 1,514/1,804/1,892 ms (25.0-31.2%) at depth 22-26, i.e. **4-11x the time for 4-8 plies**. Mechanism, read not guessed: `search.hpp:42` `moves_to_go = 0` is the ABSENT sentinel, `uci.cpp:172/241` clamp a supplied value with `std::max(1, value)`, and `clock_plan.hpp:37` branches on `moves_to_go > 0` - so absent -> 317 ms soft, 0 -> clamped to 1 -> 3040 ms, predicted 9.6x inside the measured 4.2-11.2x. **Practical: omit `movestogo` or send a large value, never 0.** The owner's matches omit it, so they are unaffected. |

**FOUR-WAY AGREEMENT on `go softnodes` - about as settled as anything in this run.** My S-F25 (softnodes
deterministic, finished-depth stop, bounded overshoot) was independently reproduced by seats **08 (08-F26)**,
**19 (19-F44)** and **29 (29-F22/23/24)** on their own harnesses; I then reproduced seat 19's budget-ratio
numbers (19-F46) to within a hundredth on mine. Four independent arrivals at the same numbers mean the
soft-node path can be treated as characterised. The practical consequence, agreed by all four:
**a cost model keyed to N must assume 1.3x-2.1x N for `go softnodes`, and about 0.5x-0.7x N for `go nodes`** -
a hard node limit discards the iteration it interrupts, a soft one finishes it. Neither is a fault; both are
budget-modelling facts for anyone reading match or self-play labels.

### WITHDRAWN / NOT A DEFECT (with the reason)

| id | status |
|---|---|
| S-F3, S-F4, S-F5, S-F11..S-F18, S-F20 | **NOT A DEFECT under file 6.** Measurements all reproduce; the judgement was wrong because the owner's match program ends the game at the 100th half-move, so `cp 0` is correct. My "the opponent can decline" premise was the human FIDE claiming rule. |
| S-F19 | **withdrawn by my own A/B**: removing the fifty-move test from `is_draw` moves scores by 323 cp mean and costs a median 408x nodes |
| S-F22, S-F23 | **not to be pursued**: the refusable-aware repair fixes a non-defect and costs 11-20 plies of depth at every clock tried (depth 22->12, 32->14, 36->15) |
| S-F27, S-F28, S-C9, S-C10 | **withdrawn entirely**: there is no `go nodes 20000` defect. The final answer is correct; my "illegal move in the PV" was my own typo (`b2a2` for `b1a2`) replayed back at me. Exposure on 100 real game positions: 0. |
| merge question | the repair must be applied on its own and **never layered inside `FORGE_FIX_ROOT_DRAWN`** (root-only flag vs a per-node test), but it should not be applied at all |

### ERRORS OF MINE, ALL RECORDED, NONE EDITED AWAY

Written up in `COPYING_RULE.md` (the transferable artifact) and `pcpath/S-F27_WITHDRAWN.md`:
1. concluded the clock-99 zero was correct - withdrawn (`debug/CORRECTION.md`)
2. typed `h6h5` as a pawn push when it is a capture (`debug/COST_FINAL.md`)
3. a check compared a regex match to `"cp 0"` when it returns `"score cp 0"` (`check_05F14/`)
4. headlined S-F27 as a match-path defect when the final answer was correct (`pcpath/EXPOSURE_FINAL.md`)
5. claimed an illegal PV move that was my own typo (`pcpath/S-F27_WITHDRAWN.md`)
6. scoped S-F7's 64-line artifact to terminal roots when a non-terminal mate root produces it too (S-C14)
7. claimed the clock path was 3/3 reproducible in score and nodes when only the MOVE is deterministic - at 6 runs
   the score, node count and depth each take 2 distinct values (S-C15)
One cause for 1-5: reconstructing data instead of copying it from raw output. 6 and 7 are the same fault in
another form - a conclusion drawn from too small a sample instead of from a sweep.

### FILES THAT MATTER MOST
`COPYING_RULE.md` (the rule for the next swarm), `check_file6/HOW_TO_APPLY_FILE6.md` (the depth line),
`check_file6/depth_requirement.txt` (the 8x6 table), `pcbuild/HONESTY_PC.txt` (file 5 table reproduced),
`debug/CLOCK99_ANALYSIS.md` and `debug/MECHANISM.md` (the full clock thread, for the record),
`debug/RISK_MEASURED.md` (why the repair was refused), `pcpath/EXPOSURE_FINAL.md` (the withdrawal).

Running now: nothing. Next: continue the cycle on the PC path and confirm other seats where my PC20 harness helps.



































## 2026-11-16T23:58Z - S-F37 minimum-one floor is its own finding; pattern paragraph carries the caught-at-desk progression

S-F37 (PC r15/PC20/Threads 1/Hash 16): `go depth 0` behaves as **depth 1**; `go movetime 0` reaches **depth 5**; only
`go nodes 0` honours 0 literally (immediate answer at depth 0, move g1e2 vs the normal f1e2). So three of four limit
fields clamp 0 to a minimum and only `nodes` treats 0 as "no search" - a trap for any harness passing 0 to mean
"unset". The movestogo asymmetry stays a separate, movestogo-specific case of the same habit.

FINAL pattern paragraph now reads TEN errors with the progression: the tenth was caught AT THE DESK before
publishing rather than in review. Lists the nine earlier ones compactly (incl. the two checker false-failures) and
closes with "when a result looks surprising, check the harness before the engine".

Scope probe keeps both states visible: labelled SCOPE PROBE, control caveat stated, no conclusion read off it.

State: 80 findings, compliance PASS, audit 0 mismatches, working tree clean, local = remote. Continuing at cadence.

## 2026-11-16T23:58Z - movestogo "NOT a bug" leads its FINAL row; scope probe caught my own control error pre-publication

FINAL row now opens: "movestogo 0 is NOT an engine bug - it means 'one move to go' after the clamp, and last-move
budgeting correctly spends about half the clock. The error is a CALLER that sends 0 meaning 'unknown'." Then the
4-11x table with depth, the three code citations, the 9.6x-predicted-inside-4.2-11.2x-measured arithmetic, and the
advice.

S-C35 scope probe: std::max(1,...) appears ONLY on movestogo (uci.cpp:172/241), so the time-formula asymmetry is
movestogo-specific. My probe compared "supplied" vs "zero" - the WRONG control for a 0-vs-absent question - so I
labelled it a scope probe only and read no conclusion off it. Tenth control error, first caught before publishing.
What it legitimately shows: the "minimum one" shape recurs (depth 0 -> depth 1; movetime 0 -> depth 5) while
nodes 0 answers immediately at depth 0 (documented zero-budget path).

State: 79 findings, guards green, working tree clean, local = remote. Continuing at cadence.

## 2026-11-16T23:57Z - S-C34: movestogo disagreement RESOLVED into a diagnosis (three code facts, read)

1. include/forge/search.hpp:42   int moves_to_go = 0;                      <- ABSENT sentinel IS 0
2. src/uci.cpp:172 and :241      = std::max(1, value);                      <- supplied value clamped to >= 1
3. include/forge/clock_plan.hpp:37  if (moves_to_go > 0) { ... } else { ... } <- two formulas

absent -> 0 -> else -> soft = 5990/22 + 45 = 317 ms
movestogo 0 -> clamped 1 -> if -> soft = 5990/2 + 45 = 3040 ms
Predicted ratio 9.6x sits inside the measured 4.2-11.2x, so the arithmetic closes it.

**It is NOT a bug**: movestogo 0 legitimately means "one move to go", and last-move budgeting correctly spends about
half the clock. The error is a caller sending 0 meaning "unknown". My earlier flag was right about the layer and the
sentinel's existence, wrong only about the sentinel's value (it is 0, and the clamp on the write side breaks the
symmetry). ADVICE: omit movestogo or send a large value, never 0.

The 4-11x table with depth figures stays beside it in check_30F55/results.txt.
State: 78 findings, guards green, working tree clean, local = remote. Continuing at cadence.

## 2026-11-16T23:57Z - S-C33: CONFIRMS 30-F55 (movestogo 0 costs 4-11x the time) and flags where the cause is NOT

Match clock 6s+0.06, PC20, Threads 1, Hash 16, 3 runs x 3 positions:
  field omitted : 179/161/381 ms (3.0-6.3% of 6,060) at depth 18
  movestogo 0   : 1,514/1,804/1,892 ms (25.0-31.2%) at depth 22-26
  movestogo 1   : 1,503/1,812/1,894 ms - essentially identical to 0
So 0 costs 4-11x the time and buys 4-8 plies. PRACTICAL: a match program must OMIT movestogo (or send a large
value), never 0; the owner's own setting omits it, so his matches are unaffected.

CODE/MEASUREMENT DISAGREEMENT worth someone's time: include/forge/clock_plan.hpp:37 branches on `moves_to_go > 0`,
so 0 and absent should take the SAME else-branch and behave identically - yet they differ by 4x. So the cause is NOT
in plan_clock_budget; it must be the UCI layer treating a PRESENT movestogo 0 differently from an absent field. I
did not read the UCI parser, so this is a report of the disagreement, not a diagnosis.

State: 77 findings, guards green, working tree clean, local = remote. Continuing at cadence.

## 2026-11-16T23:55Z - near-miss detail beside the filter caveat

Both files now pair the caveat with the practical warning: the filter catches every observed failure but does NOT
validate a pass, AND both rejected cases were only ONE MOVE long (mate 4 with 6 plies where 7 were needed; mate 5
with 8 where 9 were needed) - so they came within a single ply of passing while being wrong about the distance.
Anyone relying on the filter should expect a barely-failing score to be the common case, not a distant one.

Sentence to keep: the filter removes scores I have measured to be bad; it does not certify the ones it keeps.

State: 76 findings, guards green (compliance PASS / audit 0 mismatches / self-check 4/4), working tree clean,
local = remote. Continuing at cadence; guards re-run once more at the close.

## 2026-11-16T23:55Z - S-C32: tried to demonstrate the PV-length filter's blind spot, could not (null result)

Five boards, softnodes 1000 vs 100000: the two failures (mate 4/SHORT, mate 5/SHORT) are correctly REJECTED; the two
passes (mate 3, mate 2) had the SAME distance at the large budget, so those passes were right; one board gave no mate
at 1000. So the accept condition coincided with correctness every time on this sample - which does NOT show the filter
is sound, only that no counter-example was found here.

The caveat therefore stands as a caveat: a PASS means "not rejected", NOT "verified". The claim is now bounded from
both sides. A demonstration would need a short-budget search reporting a right-length checkmate-ending PV whose
distance exceeds the truth - plausible (the rejected cases were only one move long) but not found in five boards.

State: 76 findings, guards green, working tree clean, local = remote. Continuing at cadence; three guards re-run
near the close as promised.

## 2026-11-16T23:54Z - the PV-length filter now states its LIMIT (catches every observed failure; does not validate a pass)

Both FINDINGS and the FINAL now say: the filter **catches every observed failure - which is all it is shown to do; it
does NOT validate a passing score**, because a right-length PV ending in checkmate could still be a longer mate than
necessary, and I did not test for that. A filter for the measured failure shape, not a correctness proof.
(My earlier "a correct mate score always passes" implied validation the data does not support.)

The CONVERGENCE explanation stays beside the rule: a still-converging mate reports one move longer than the truth -
which is why the PV is short, why the failure is budget-dependent on one board (mate 4/SHORT at softnodes 1000-2000,
mate 3/ok from 5000), and why a random 40-board sample missed it (the converging window is narrow per board).

State: guards green (audit 0 mismatches, self-check 4/4, compliance PASS), working tree clean, local = remote.
Continuing at cadence; three guards re-run once more near the close.

## 2026-11-16T23:54Z - S-C31: the label rule MEASURED on a non-empty set (filter, not a budget)

After the empty-set error (S-C30), the same question asked on boards that DO fail: classes SHORT 4, ok 8,
right-length-not-mate 0 across 3 boards x softnodes 500..20000. So every failure is a PV that stops short of its
own claimed distance - the score is not broken, the report is premature.

LABEL RULE (measured, actionable): **reject any mate score whose PV length != 2|N|-1 (or 2|N| for negative N).**
Catches every observed failure at zero cost, since a correct mate score always passes. Better than the withdrawn
"use 20000" because it needs no budget decision.

EXPLAINS S-F34's "one move pessimistic" instead of describing it: budget-dependent on the same board
(4Q3/8/r2K4/... mate 4/SHORT at 1000-2000, mate 3/ok from 5000; 7Q/8/8/4K3/... mate 5/SHORT at 500-1000, mate 4/ok
at 2000) - a converging mate reports one move too long. And it explains why the random 40-board sample missed it:
the failure needs a mate converging at that exact budget, a narrow window.

POSITIVE RESULT in FINAL beside it: 12/12 mate scores correct on those 40 boards at softnodes 2000.
State: guards green (audit 0, self-check 4/4, compliance PASS), working tree clean, local = remote.

## 2026-11-16T23:52Z - NINTH control error: an EMPTY failure set produced a claim (inside the checker itself)

label_check.py asked whether the self-play mate-PV failure is always a SHORT PV. 40 mate-rich boards at
softnodes 2000 gave 12 mate scores, 12 ok, ZERO failures - and the script then printed "Every failure is a SHORT
PV - the SCORE is not broken": a characterisation of an EMPTY SET, asserting what the data cannot support. My own
rule (a description needs a non-empty set, as a zero needs a plant) would have caught it.

FIXED: the conclusion branch now requires >=1 failure, else prints an explicit UNMEASURED line. Re-run says
"NO FAILURES IN SAMPLE - the character of failures and their rate are UNMEASURED here. Do not conclude 'every
failure is short' from an empty set."

SURVIVES as a positive result: 12/12 mate scores correct on these 40 boards - about those boards only. The S-F34
failure is real but BOARD-SPECIFIC (4Q3/8/r2K4/...), which is why a random 40-board sample missed it: sampling, not
contradiction.

FINAL pattern line now says NINE instances and names this one as happening inside the checker itself.
State: working tree clean, local = remote. Continuing at cadence; three guards re-run near the close.

## 2026-11-16T23:50Z - FINAL now names BOTH patterns; wider rule carried; all three guards green

PATTERN 1 (control errors): six times the real finding was a fault in my own test - different-depth comparison,
regex-vs-wrong-string, PV retyped, 13-board sample for a recommendation, single Hash axis, one-clock-answer-as-
constant. Mechanical forms: compliance_check.sh, audit_final.py, final_selfcheck.py. Two of those checkers produced
false failures on their own first run, which is the best illustration the line could have.

PATTERN 2 (scope narrowness, new): "my findings tend to be right about the mechanism and NARROW about the scope" -
four times another seat's formulation was one axis wider (seat 05 boundary, seat 19 budget ratio, seat 30 MultiPV,
seat 20 S-F53). Question implied: "what else is this an instance of?" before publishing.

WIDER RULE CARRIED: S-F7's FINAL row now carries seat 20's S-F53 - any report-without-search path emits one
info-depth line per depth, capped at the requested depth or 64 - with empty-searchmoves as the proving member; my
S-C27 scope noted as a special case.

GUARDS: audit_final.py 0 mismatches | final_selfcheck.py 4/4 PASS | compliance_check.sh PASS.
State: working tree clean, local = remote. Continuing at cadence; guards re-run once more near the close.

## 2026-11-16T23:49Z - S-C29: seat 20's S-F53 CONFIRMED and it supersedes my S-C27 scope

One reporting habit, not a terminal quirk: any path that reports WITHOUT SEARCHING emits one info-depth line per
depth, capped at the requested depth or at 64. Verified on three such paths (PC r15/PC20):
  terminal (checkmated) root : go depth 5 -> 5 lines/depth 5 ; go nodes 50000 -> 64/64
  resolved mate root         : 5/5 ; 64/64
  empty searchmoves          : go depth 5 searchmoves a7a8 -> 5/5, bestmove 0000, + info string about no legal
                               root moves
My S-C27 ("a root that resolves before the limit") is a special case; the empty-searchmoves member is what proves
the rule is about the report-without-search path, not about resolution. FINAL's S-F7 row now carries seat 20's
broader rule with mine noted as a special case.

FOURTH time tonight another seat's formulation was one axis wider than mine (seat 05 boundary, seat 19 budget
ratio, seat 30 MultiPV, seat 20 S-F53). Pattern alongside the control-error line: my findings tend to be right
about mechanism and narrow about SCOPE.

State: compliance PASS, 0 audit mismatches, 4/4 self-check, working tree clean, local = remote. Continuing.

## 2026-11-16T23:49Z - third guard (final_selfcheck.py, 4/4 PASS) and the EIGHTH control error, again inside a checker

New final_selfcheck.py re-runs the four cheap live headline claims: S-F29 (cp 1359 at depth 16, mate 8 at 20),
S-C26 (mate 0/0000/0n vs mate 1/a1a8/105n), S-C27 (64-line burst, answer == go depth 10), S-C22 (MPV3 clock:
Hash16 depth 13 > Hash256 depth 4). **4/4 PASS.**
Its FIRST run reported S-F29 as FAIL while printing exactly the numbers S-F29 claims - my assertion tested
`startswith("cp")` against "score cp 1359". Eighth instance of the control pattern, and the SECOND inside a checker
I wrote to prevent them.

FINAL pattern line now names all three guards (compliance_check.sh, audit_final.py, final_selfcheck.py) and says
plainly that two of them exhibited the pattern on their own first run - the best illustration the line could have.

State: compliance PASS, 0 audit mismatches, 4/4 self-check, working tree clean, local = remote.
Next: re-run audit_final.py near the close (FINDINGS keeps growing), and keep cycling.

## 2026-11-16T23:48Z - control-error pattern line in the FINAL + audit_final.py guard

FINAL now opens with the pattern: "six times tonight the real finding was a CONTROL error in my own test, not the
engine" - different-depth comparison (S-C27), regex-vs-wrong-string (check_05F14), PV retyped (S-F27), 13-board
sample for a recommendation (S-C17), single Hash axis (S-C22), one-clock-answer-as-constant (27-F12 refutation).
Lesson: when a result looks surprising, check the harness before the engine.

NEW audit_final.py: cross-checks every finding marked WITHDRAWN/NOT A DEFECT/REFUTED/COSMETIC in FINDINGS.md
against its FINAL row. Result 0 mismatches. The FIRST run flagged S-C5 and S-C6 falsely - my matcher scanned the
whole row, so "NOT A DEFECT" inside S-C5's subject matter and "is NOT vacuous" in S-C6 read as statuses. Tightened
to the status cell only. Seventh instance of the pattern, inside the audit itself.

State: compliance PASS, 0 audit mismatches, working tree clean, local = remote. Continuing at cadence.

## 2026-11-16T23:48Z - terminal-root family CLOSED: S-F6 withdrawn, S-F7 reclassified cosmetic (S-C26/S-C27)

S-F6 WITHDRAWN as a defect: verified seat 11's ladder myself (checkmated -> mate 0/0000/0 nodes; mate in 1 ->
mate 1/a1a8/105 nodes; stalemated -> cp 0/0000; dead draw -> cp 0; KQvK -> cp 1107/2,779). mate 0 and mate 1 are
different signals in one encoding; UCI's y=0 naturally encodes "mated now". Consumer note kept, labelled as advice.

S-F7 RECLASSIFIED cosmetic: the answer on a resolved root is identical in score and move to go depth 10; the burst
is bounded at exactly 64 (the depth cap); and go movetime bursts identically, so it is not a node-limit fault but
what the loop does when a root resolves. Consumer advice: read the last line or the bestmove, not iteration counts.
Also recorded: my first comparison used different depths (nodes 50000 stopped at 13 vs depth 10) and reported a
false mismatch; the correct control is "same depth". Caught and noted rather than dropped.

State: 71 findings, compliance PASS, working tree clean, local = remote. Continuing at cadence.

## 2026-11-16T23:47Z - S-C26: S-F6 WITHDRAWN as a defect (seat 11 was right; ladder verified on my build)

Verified seat 11's ladder myself on PC r15/PC20, go depth 5, Threads 1, Hash 16:
  checkmated root     -> mate 0 / 0000 / 0 nodes
  mate in 1 available -> mate 1 / a1a8 / 105 nodes    <- a REAL move and non-zero nodes
  stalemated root     -> cp 0 / 0000 / 0 nodes
  dead draw KvK       -> cp 0 / e3d2
  KQ vs K             -> cp 1107 / c1c2 / 2,779 nodes
The distinction I missed: mate 0 and mate 1 are DIFFERENT signals in one encoding - 1 = mate available in one move
(with a move), 0 = already mated (with 0000). Under UCI `score mate y` = mate in y moves, y = 0 naturally encodes
"mated now". So the terminal case is not a fault. Withdrawn, with seat 21's 21-F11 noted as withdrawn for the same
reason. Surviving note is consumer-side only: a reader assuming |y| >= 1 must handle 0.

Eleventh correction tonight. S-F6's FINAL row is now the withdrawal with the ladder.

State: 69 findings, compliance PASS, working tree clean, local = remote. Continuing at cadence.

## 2026-11-16T23:45Z - TESTED MY OWN S-C23 PREDICTION: direction right, magnitude wrong (S-C25)

Applied seat 30's ttclear_no_alt_clear patch to the PC r15 tree (pins unchanged - a clean controlled change) and
ran my S-C23 command, go wtime 5000, MPV3:
  Hash  16: 13 / 559 -> 13 / 677 nodes/ms
  Hash  64:  9 / 183 -> 13 / 583   (3.2x, full depth restored)
  Hash 256:  4 /   2 ->  7 /  29   (14x, 3 plies recovered)
  Hash1024:        ->  1 /   0
  MPV1 control: ~1,500 flat at every Hash, unchanged between builds
So the redundant clear WAS a large part of the cost - seat 30's diagnosis of the clear is vindicated - but it does
NOT reach MPV1's ~1,500, which is what I predicted. A SECOND cost at large Hash remains; its shape (583 -> 29 -> 0)
points at the still-present alt_worker->clear() per line or the alt table's per-line touch. HYPOTHESIS, not measured.
VERDICT: seat 30's patch is necessary and not sufficient - a genuine 14x improvement that should go in, but the
collapse survives in reduced form. S-C24 advice unchanged and better grounded: on a clock with MPV>1 keep Hash 16.

State: 72 findings, working tree clean, local = remote. Next: keep cycling.

## 2026-11-16T23:45Z - compliance_check.sh: the binary gate is now mechanical and plant-tested

Added forge-combo29/swarm/25/compliance_check.sh, run before every push, exit 1 on violation:
  (1) tracked binaries in my folder (extension list)   (2) files touched outside my folder
  (3) non-text files by `file` content                 (4) engine source committed
  (5) uncommitted changes -> WARN so nothing is forgotten at a push boundary
PLANT TESTED: staged a fake .pyc -> caught two independent ways (extension + content, reported as `data`),
exit 1; after removal, exit 0. So a green run means something.
CURRENT: COMPLIANCE PASS on all four hard checks.

Cause noted by the coordinator and fixed at the class level: a .pyc can only come from a script run next to
itself, so the gate catches the failure mode rather than the instance.

State: 71 findings, working tree clean, local = remote. Next: keep cycling.

## 2026-11-16T23:44Z - COMPLIANCE AUDIT of my own folder, and the four-step thread order in the FINAL

COMPLIANCE (checked against the brief's rules):
  * text files only: PASS after a fix - I had committed ONE .pyc binary
    (job1c/__pycache__/classify_mates...pyc); removed from the index, deleted, and a .gitignore added.
    Remaining non-ASCII files are all valid UTF-8 TEXT (em-dashes in prose), not binaries: `file` reports
    "Unicode text, UTF-8 text" for every one.
  * only my own folder: PASS - `git log --name-only ae78bd1c2..HEAD` filtered to outside
    forge-combo29/swarm/25/ returns 0 files.
  * no binaries in the index: PASS (0 files matching .pyc/.so/.a/.o).
  * no pull request, no engine source committed (patch files are .patch.txt only), branch is mine alone.

FINAL now carries the FOUR-STEP THREAD ORDER for the MultiPV work, with the superseded first statement kept in
place: S-C21 (my too-narrow "clock x MultiPV", measured at one Hash) -> S-C22 (three conditions + the Hash-16
control ladder) -> S-C23 (mechanism, nodes/ms 559->183->2 vs MPV1 flat ~1,500, plus the falsifiable patch
threshold) -> S-C24 (Hash 16 on a clock with multiple lines; Hash free under a depth/node limit).

State: 70 findings, working tree clean, local = remote. Next: keep cycling.

## 2026-11-16T23:43Z - S-C24: the MultiPV thread ends with a measured recommendation

On a CLOCK (go wtime 5000, MPV3) depth falls monotonically with Hash: 16 -> 13 (fine), 32 -> 10, 64 -> 10,
128 -> 7, 256 -> 4, 512 -> 1 (collapsed). With a DEPTH LIMIT Hash is free: go depth 20 at MPV3 reaches depth 20 at
Hash 16, 64 AND 256 alike. So the collapse is a clock-budget effect only, not a search-quality effect.
ADVICE: on a clock with MultiPV>1 keep Hash 16; for deep analysis with a depth/node limit, Hash is free.

Thread order in FINDINGS: S-C21 (mine, too narrow, superseded) -> S-C22 (three conditions + Hash-16 control
ladder) -> S-C23 (mechanism with nodes/ms 559->183->2 vs MPV1 flat ~1,500, and the falsifiable patch threshold)
-> S-C24 (what to do).

State: 69 findings, working tree clean, local = remote. Next: keep cycling.

## 2026-11-16T23:43Z - S-C23 MECHANISM MEASURED: the between-line TT clear eats the clock budget

go wtime 5000, MPV3, nodes searched per ms of wall time:
  Hash  16 -> depth 13, 118,566 nodes, 559 nodes/ms
  Hash  64 -> depth  9,  20,518 nodes, 183 nodes/ms
  Hash 256 -> depth  4,     622 nodes,   2 nodes/ms   (290 ms spent to search 622 nodes)
  MPV1 at every Hash 16..1024 -> depth 16 / 172,312 nodes / ~1,500 nodes/ms (completely unaffected by Hash)
So a large Hash alone is harmless; the clock budget at MPV3 is consumed WITHOUT searching - the clear's cost,
monotone in Hash. The clean Hash-16 ladder (MPV1/2/3/4 -> 16/15/13/11, all exact) is the control proving MultiPV
itself is sound and only the clear is at fault.

FALSIFIABLE PREDICTION recorded: a patch removing the redundant clear should bring MPV3+Hash256 to ~1,500 nodes/ms,
not ~0. That distinguishes "removes the clear" from "changes MultiPV behaviour".

S-C21 marked superseded in the FINAL; S-C22 (three conditions + control ladder) and S-C23 (mechanism) are in it.
Match path (MPV1) unaffected at every Hash.

State: 68 findings, working tree clean, local = remote. Next: keep cycling.

## 2026-11-16T23:42Z - S-C22 CORRECTS my S-C21: the MultiPV collapse needs a LARGE HASH too

Same position, go wtime 5000, 4 fresh runs per cell:
  Hash  16: MPV1 16 | MPV2 15 | MPV3 13 | MPV4 11   - clean and STABLE ladder (1-2 plies per extra line)
  Hash 256: MPV1 16 (exact) | MPV2 [4,5] 2.5x spread | MPV3 [4] | MPV4 [2,4] 5.4x spread   - COLLAPSE
  go depth 12 at Hash 256: exact at every MPV -> deterministic limits unaffected
So the defect needs ALL THREE: clock, MultiPV > 1, large Hash. My S-C21 said "clock x MultiPV" from a single Hash
and generalised one factor too far. Plausible cause: MultiPV>1 clears the TT between lines (seat 12 measured it),
a large Hash makes that clear expensive, so the time manager stops at a shallow depth.

PRACTICAL: the owner's matches use MultiPV 1 - exact at both Hashes, so the MATCH PATH IS UNTOUCHED. The exposure is
analysis at MPV3-4 with a large Hash, where the engine silently returns depth 2-5 instead of ~13-16.

State: 66 findings, working tree clean, local = remote. Next: keep cycling.

## 2026-11-16T23:41Z - 27-F12 SETTLED/closed; S-C21 finds the clock x MultiPV pair

27-F12 now reads SETTLED/closed in S-C18/S-C19/S-C20 and in the FINAL: two independent refutations (mine on both
builds, seat 30's 30-C40 with matching numbers and a 12-of-12 side-to-move check) plus the origin of the number -
286,156 nodes is the BASE build's wtime-3000 answer, read as invariant.

S-C21 (new): checked seat 30's 30-F50 and it holds, with a narrower cause. 6 fresh runs per cell:
  wtime 5000 + MPV3 -> depths [1,4], nodes 73-622, 8.5x spread      (their instability reproduced)
  wtime 5000 + MPV1 -> depth 16, 172,312 nodes every run, 1.0x      (clock alone exact)
  nodes 50000 + MPV3 -> depth 10, 6,386, 1.0x ; depth 12 + MPV3 -> 12, 94,994, 1.0x  (MultiPV alone exact)
So the CLOCK x MULTIPV pair starves the search: depth 1-4 where MPV1 reaches 16 on the same clock - a 12-15 ply
loss that also varies run to run. Neither factor alone causes it. Numbers are position-dependent (they saw {7,11}
at Hash 256, I saw {1,4}); the structure reproduces.

State: 65 findings, working tree clean, local = remote. Next: keep cycling.

## 2026-11-16T23:41Z - S-C20: 27-F12 SETTLED - the 286,156 "constant" is the base build's wtime-3000 answer

Verified the origin of the number myself: on seat 27's own FEN, base 6b98f217 at `go wtime 3000` gives
`info depth 20 seldepth 38 score cp 0 nodes 286156` - exactly the value they reported as invariant across
wtime 0..3000. The PC build at the same command gives 121,768. So one large-budget answer was read as a constant;
that single misreading explains the whole finding.

Two independent refutations with matching numbers: mine (depth 1/39 at wtime<=10, 6/918 at 50, 10/11,488 at 200,
22/178,324 at 3000) and seat 30's 30-C40 (same ladder, 3000 -> 22/178,324/91 ms identical to mine; plus no
side-to-move asymmetry in 12 of 12 positions across both builds). Settled.

State: 63 findings, working tree clean, local = remote. Next: keep cycling.

## 2026-11-16T23:40Z - S-C19: 27-F12 does not reproduce on the base build either

Base tree 6b98f217 / S14, same four tests as S-C18:
  go wtime 3000 -> depth 20 / 122,327 nodes (clock scales; their claim needs it frozen for every wtime)
  white wtime 0 -> depth 1 / 21 nodes ; black -> depth 1 / 39 ; startpos 26 vs 26 (no side asymmetry)
  go movetime 5 -> depth 5 / 588 nodes (not depth 1)
So both builds I can test behave identically and agree with my S-F32. Caveat upgraded: "builds may differ" is now
"behaviour is consistent across both builds I can test; their named binary 068f0927 remains untested by me."

State: 62 findings, working tree clean, local = remote. Next: keep cycling.

## 2026-11-16T23:40Z - S-C18: 27-F12 (clock ignored for black) does not reproduce on my build

Seat 27's most striking claim was that `go wtime N` is ignored entirely when BLACK is to move. On my PC build
(file-5 patch, PC20, Threads 1, Hash 16) it does not reproduce at any part:
  their FEN, wtime 0/1/3/10/50/200/1000/3000 -> depth 1/1/1/1/5/10/17/22, nodes 39..178,324, move changes
  side-to-move: white at wtime 0 -> depth 1/21 nodes; black -> depth 1/39; startpos 26 vs 26 (no asymmetry)
  their "0 info lines with w" -> 1 line for me; their "movetime 5 stops at depth 1" -> depth 6/918 for me
Recorded as NOT REPRODUCED, with the caveat that they name a different binary (PC r15 068f0927), so the builds may
differ. This agrees with my S-F32 (every clock regime well behaved, both colours).

State: 61 findings, working tree clean, local = remote. Next: keep cycling.

## 2026-11-16T23:39Z - S-F36 mechanism (no budget fixes this) + COPYING_RULE extended to eight cases

S-F36: a bigger softnodes budget CREATES more mate claims rather than fewer - 7 of 40 mate-rich boards emit a mate
score at 2000, 19 of 40 at 20000. An undeliverable claim is a function of how often claims are made, so raising the
budget moves the engine into the range where premature claims appear. That is why "use 20000" could not work in
principle, and why the fix is PV VALIDATION in the pipeline, not a budget number. It sits directly under the S-F35
withdrawal in the FINAL.

COPYING_RULE.md now has eight cases and a four-part rule; the new part is "size the sample to the claim, not to the
first convenient run", with cases 1-5 grouped as "reconstructed data" and 6-8 as "sample too small for the claim".

State: 60 findings, working tree clean, local = remote. Next: keep cycling - the remaining useful work is other
seats' unconfirmed finds against the PC20 harness.

## 2026-11-16T23:37Z - NINTH self-correction: my own wider sample REFUTED the S-F35 remedy

I recommended "run self-play at softnodes 20000" based on 13 boards. On 40 mate-rich boards the opposite holds:
   softnodes 2000  : 0 undeliverable, 1 differing
   softnodes 20000 : 2 undeliverable, 3 differing
So 20000 is WORSE on the wider set; the 13-board result was a coincidence. Reason: at 2000 only 7 of 40 boards emit
a mate score at all, at 20000 19 do - a higher budget moves the engine INTO the depth range where premature mate
claims appear. S-F35 is withdrawn in the FINAL (its row is now the withdrawal itself), S-C17 records the correction.

REVISED, HONEST RECOMMENDATION: do not rely on a budget - **validate mate PVs in the label pipeline**, because both
2000 and 20000 emit undeliverable mate claims on worst-case boards.
WHAT SURVIVES: the fault is real at both budgets; shallow-depth horizon effect; `go nodes 250000` is the clean
reference; S-F34's two-reasons framing stands as a description of the fault, with its sample caveat attached.

This is the ninth self-correction and the second time tonight a 13-board sample misled me. The lesson is now
explicit in COPYING_RULE.md's scope rule: a recommendation needs a sample sized for the claim, not for the
convenience of the first run.

## 2026-11-16T23:35Z - the self-play label thread is COMPLETE: found, quantified, fixed with a number

S-F33 (found): at `go softnodes 2000` a mate PV can be one ply short of its own claim.
S-F34 (quantified, both reasons): 1 of 13 mate PVs undeliverable and 3 of 13 mate numbers one move pessimistic at
2000 nodes; 0 of 13 at `go nodes 20000`. Worst-case boards, not the average - middlegame 2000-node searches rarely
emit mate scores (1 in 100).
S-F35 (remedy): **run self-play at `go softnodes 20000`** - 0 undeliverable and 0 mate numbers differing from a
`go nodes 250000` reference, versus 1 and 3 at 2000. 20000 is the node order the MATCHES already use, so it is not
a new regime. Anomaly recorded not smoothed: `softnodes 50000` showed 1+1 (one board flipping; likely noise at this
sample size).

FINAL order for the owner: S-F35 (remedy) immediately above S-F34 (the two reasons), then S-F33 (the first case).
Working tree clean; local = remote. Next: keep cycling.

## 2026-11-16T23:35Z - both reasons to raise the self-play budget, now MEASURED (S-F34)

13 mate-scored endgame boards, PC20/Threads 1/Hash 16:
 (1) LABEL VALIDITY: at `go softnodes 2000`, 1 of 13 mate scores has a PV that does not play out (6 plies claimed
     as mate 4, needs 7). At `go nodes 20000`: 0 of 13.
 (2) LABEL MAGNITUDE: 3 of 13 boards report a mate number ONE MOVE LONGER at self-play than at match
     (mate 4 where the match setting says mate 3), the other 10 agree exactly.
So self-play mate labels at 2000 nodes can be both pessimistic by a move and undeliverable by their own line; the
match budget is clean on the same boards. Caveat in the finding line: these are purpose-built Q/Q+R/RR/Q+B vs K
endgames where mates appear at shallow depth; middlegame 2000-node searches rarely emit mate scores (1 in 100), so
real-corpus rates are lower - worst case, not average.

Note on my own process: the coordinator asked me to place this "next to your magnitude finding" - I had no
measured magnitude finding, so I measured one rather than implying it existed. Eighth time tonight that writing
the claim made me check it.

FINAL standing table now has S-F34 immediately before S-F33 so the self-play label argument reads in one place.
Working tree clean; local = remote. Next: keep cycling.

## 2026-11-16T23:34Z - LABEL-QUALITY FINDING on the self-play setting (S-F33)

At `go softnodes 2000` (the owner's self-play budget, depth 6) board 4Q3/8/r2K4/8/2B5/5R2/1k6/8 w reports
**mate 4 with a 6-ply PV that is all-legal but NOT checkmate** (mate 4 needs 7 plies). The same position at
`go nodes 20000` (depth 53) gives the correct **mate 3 with a verified 5-ply checkmate**. Horizon truncation at
shallow depth, NOT a wrong mate number - same family as seat 05's 27 boards and file 6's reclassification.

For training labels: a self-play record can carry (a) a PV that does not play out, so a PV validator flags it, and
(b) a mate distance one move pessimistic (mate 4 where truth is mate 3). Over 100 positions: 0 illegal PVs at
BOTH settings, and 0 wrong mate PVs at `go nodes 20000` - so the match path stays clean (consistent with
S-F30/S-F31). Rare in middlegames, real when it happens, concentrated on endgames where mates appear shallow.

SIXTEEN self-corrections/confirmations of others this window plus nine own findings, all pushed.
Working tree clean; local = remote. FINAL remains the first block of this file.
Next: keep cycling.

## 2026-11-16T23:33Z - FINAL opens with the determinism one-liner; clock regimes S-F32 all safe

TOP OF FINAL now reads: moves stable run to run across every command; scores from a CLOCK search approximate
(6 runs gave cp 55 and cp 67 at depths 16/18); scores from `go nodes` and `go softnodes` exact. A pipeline may
label moves freely from any command, but clock-derived scores are approximate only.

NEW S-F32: every degenerate clock regime returns a legal, stable move - `movestogo 10` (depth 19, 312 ms, by
design heavier per plan_clock_budget's 1/(mtg+1) branch), increment-only, `wtime 50`, and `wtime 0 btime 0
winc 0 binc 0` (depth 1, 25 nodes, 1 ms, legal f1e2). No hang, no crash, no illegal move; move identical in all
3 runs of each regime.

TIMING PICTURE COMPLETE: safe legal moves in every regime; approximate scores from clocks; exact scores from node
limits. Fifty-four findings in FINDINGS.md; working tree clean; local = remote.

Running: nothing. Next: keep cycling - remaining seats' unconfirmed finds against the PC20 harness, and any
owner-relevant behaviour still untested.

## 2026-11-16T23:32Z - SEVENTH self-correction: clock searches are deterministic in the MOVE only (S-C15)

Corrects my own S-F26. Six runs per command (PC20, Threads 1, Hash 16):
  go wtime 6000 winc 60 : score 2 distinct (cp 55 / cp 67), nodes 2 (172,312 / 309,981), depth 2 (16 / 18),
                          MOVE identical in all 6, wall time 6 distinct
  go nodes 20000        : score/nodes/depth/move ALL deterministic
  go softnodes 2000     : score/nodes/depth/move ALL deterministic
So: the match path's MOVES are trustworthy on every command; SCORES from clock-based searches are approximate
(a few centipawns of run-to-run variation) because the stop is wall-clock dependent. My earlier "3/3 reproducible"
was a small sample that happened to land on one depth.

Also clean: `go softnodes 2000 wtime 6000 ...` returns EXACTLY the softnodes answer (2474 nodes, cp 97, depth 8),
so the soft budget wins over the clock with no interaction.

SEVEN self-corrections now, all in the FINAL errors section with the honest grouping: 1-5 = reconstructed data
instead of copying it; 6-7 = conclusion from too small a sample instead of a sweep. The FINAL's S-F26 row carries
the caveat inline so the reassurance is never read without it.

Running: nothing. Next: keep cycling the PC path; look at whether any remaining owner regime (movestogo, increment
only, very short clocks) behaves differently, and confirm other seats where my PC20 harness helps.

## 2026-11-16T23:32Z - both game endings clean (S-F30 repetition, S-F31 mate); FINAL is the top-of-file inventory

Since the previous block: S-F31 (a forced-mate self-play game at the match setting: CHECKMATE at ply 3, 0 illegal
moves, 3/3 completed iterations, 3 mate scores all of whose PVs play out, nodes 0.13x N). With S-F30 (90-ply,
repetition) both ways a match actually ends are covered and both are clean. The FINAL's reassurance section now
says so.

STATE: 52 findings in FINDINGS.md, 412 files in my folder, working tree clean, local tip = remote tip
(73dbad939 at the time of writing). Cadence kept: every finding and every STATUS block pushed immediately.

NEXT: continue the PC path - check remaining seats' unconfirmed finds against my PC20 harness, and look at any
regime the owner uses that I have not yet exercised (e.g. `go softnodes` under a clock rather than a fixed N).

## 2026-11-16T23:31Z - FINAL now opens with the reassurance (S-F30), then the depth headline, then the audit

STATUS.md structure (top to bottom): (1) REASSURANCE FIRST - the 90-ply self-play game at the owner's exact match
setting is clean (0 illegal, 0 missing lines, 90/90 completed iterations, nodes 0.75x N), and none of the defects
in the report fires there; (2) THE HEADLINE - file 6's half-move test needs depth 18 (not 20), with the two boards
that never resolve within 24 being no-mate-in-horizon rather than breakage; (3) FINDINGS THAT STAND (10, each with
build+settings); (4) CONFIRMATIONS OF OTHERS (9, incl. the four-way softnodes agreement); (5) WITHDRAWN / NOT A
DEFECT (4 groups, with reasons); (6) ERRORS OF MINE; (7) FILES THAT MATTER MOST.

SIX SELF-CORRECTIONS tonight, all with reasons and evidence, none edited away:
1. clock-99 zero wrongly called correct (withdrawn)
2. h6h5 typed as a pawn push when it is a capture (corrected)
3. a check comparing regex output to the wrong string (fixed)
4. S-F27 headlined as a match-path defect when the final answer is correct (corrected, exposure 0)
5. S-F27's illegal-PV claim, which was my own typo replayed back at me (withdrawn entirely)
6. S-F7's "64 phantom lines" scoped to terminal roots when it is really "the search resolved before the budget
   was spent" - a non-terminal mate-in-1 root produces it too (scope corrected)
Plus one flagged-not-fixed: the `mate 0` impact control I built was an illegal FEN, so the documented contrast
comes from the mate-in-1 board instead; the file says so.

## 2026-11-16T23:30Z - FINAL carries the four-way agreement; PC path end-to-end is clean (S-F30)

FINAL (top of this file) now states the FOUR-WAY AGREEMENT on softnodes: my S-F25 reproduced by seats 08, 19 and
29, and I reproduced seat 19's budget ratios to a hundredth (S-C12). Agreed cost model: 1.3-2.1x N for
`go softnodes`, ~0.5-0.7x N for `go nodes`.

NEW S-F30 - end-to-end health at the owner's exact match setting (PC r15/PC20/Threads 1/Hash 16, go nodes 20000,
one fresh process per move, 90 plies): 0 illegal moves, 0 missing info lines, 90/90 moves from a COMPLETED
iteration, normal termination by threefold repetition, nodes spent/N median 0.75 (0.34-1.00). So at the setting his
matches use, over a full game, nothing in my findings fires. That is the reassuring half and it is in the FINAL.

NEW S-C13 - checked seat 21's 21-F2 and REFUTED its wrong-side half on the PC build: after a refused FEN,
`go perft 1` = 5 (White's legal-move count) not Black's 44, and the returned move is the retained position's own
correct move. Its other half is TRUE and actionable: a refused FEN still answers `readyok`, so a GUI must watch
for `info string invalid FEN`, not `readyok`. Recorded with a build caveat - refuted in MY scenario, not proof
seat 21 was wrong.

Next: keep cycling the PC path (other seats' unconfirmed finds where my PC20 harness helps; the S-F6/S-F7
terminal-root items under a game that ends by mate rather than repetition).
## 2026-11-16T23:24Z - COPYING_RULE.md written; depth sweep sharpens the file-6 guidance (18, not 20)

COPYING_RULE.md (new, top of the branch for the next swarm): never reconstruct data from memory or notes - copy it
from committed raw output, re-derive over a set in one pass, and let the rows veto the summary. Five cases
tabulated with what caught each. Includes the PV guard I broke twice: slice a PV from the engine's line, never type
it (a typed PV is a hypothesis, not a PV).

APPLYING IT TO MY OWN FINDING sharpened it (S-F29): six mate-rich boards x eight depths. QR vs K, Q+R and my S-F1
board resolve their mate from depth 8; the KQ-vs-K board needs **depth 18** (cp 1359 at 16 -> mate 9 at 18 -> mate 8
at 20). So the real threshold is 18, file 6's "depth 20 or more" is safely above it, and **depth 16 is already
wrong on a board that has a mate**. Two boards never resolve within depth 24 (KQ vs K centred: cp 18-25; KR vs K:
cp 534) - read those as no-mate-in-horizon, not breakage.

STATE OF MY FINDINGS:
STANDING: S-F29 (the depth line above), S-F26 (clock near-miss, DO NOT FIX, four-seat corroboration),
S-F25 (softnodes deterministic / finished-depth / 1.06-1.55x overshoot), S-F1/S-F8/S-F9/S-F10 (mate numbers;
S-F1 and S-F8 repaired on the PC build), S-F6/S-F7 (terminal-root reporting), S-C3, S-C4, S-C6, S-C7.
WITHDRAWN/NOT A DEFECT: S-F3..S-F20 (file 6 reclassification, 0 of 8 survive), S-F19 (my own A/B), S-F22/S-F23
(repair priced at 11-20 plies and a non-defect), S-F27/S-F28 plus S-C9/S-C10 (entirely - my typo).
FIVE ERRORS all recorded in COPYING_RULE.md and pcpath/S-F27_WITHDRAWN.md.
Next: keep cycling on the PC path (softnodes/node-limit/clock regimes) and confirm other seats where my PC20
harness helps.
## 2026-11-16T23:19Z - URGENT: S-F27 WITHDRAWN ENTIRELY (no illegal-PV defect). Use the depth-20 finding instead.

SECOND RETRACTION, and the more serious one. Earlier I told the coordinator the corrected headline was
"intermediate mate PVs can carry an illegal move on constructed endgames at small node budgets". That is FALSE.

Scope sweep (3 mate-rich boards x 10 command settings = 30 cells): 0 intermediate lines with an illegal PV, on
every cell, including the board where I reported one. Replaying that depth-8 PV verbatim: all 12 plies legal.
Ply 3 is `b1a2`; in my correction file I had written `b2a2` from memory and then "verified" my own typo. The
engine was right throughout.

Final truth at `go nodes 20000` on that board: depth 7 cp -2515; depths 8-10 mate lines with PVs shorter than
their mate distance (ordinary horizon behaviour, same as seat 05's 27 boards which file 6 reclassified); the
FINAL depth-11 line is mate -7 with a 14-ply legal verified checkmate at exactly 2*7 plies. CORRECT.

WHAT SHOULD GO IN THE FINAL BLOCK FROM ME:
1. The depth-20 requirement for file 6's inequality, with the depth-14 counter-example (`mate 8` at depth 20 vs
   `cp 1334` at depth 14) - a seat applying the rule shallowly falsely dismisses REAL defects. This stands and is
   the useful finding of the last stretch.
2. The clock near-miss, marked DO NOT FIX: 3% usage is plan_clock_budget's soft limit working (TmSoftDivisor 22);
   `movetime` differs because it is a hard instruction; corroborated by four seats.
3. Still standing: S-F1/S-F8/S-F9/S-F10 (mate numbers; S-F1 and S-F8 repaired on PC), S-F6/S-F7 (terminal-root
   reporting), S-F25 (softnodes deterministic, finished-depth stop, 1.06-1.55x overshoot), S-C3, S-C4, S-C6, S-C7.

FIVE ERRORS OF MINE, all recorded: (1) clock-99 zero wrongly called correct; (2) h6h5 typed as a pawn push, it is
a capture; (3) a check comparing regex output to the wrong string; (4) S-F27 headlined as a match-path defect;
(5) the illegal-PV claim built on my own typo. One cause every time: reconstructing data instead of copying it.
## 2026-11-16T23:18Z - RETRACTION: the nodes-20000 defect does NOT reach the match path (exposure 0)

I sent "LIVE DEFECT on the owner's match setting" earlier. The measurements say the exposure on the match path is
ZERO, and I am retracting that headline rather than letting it stand.

WHAT IS TRUE (S-C9): reading the raw lines instead of trusting my parser -- the FINAL answer at `go nodes 20000`
on 8/8/1p6/8/p3p3/8/2Kpk3/8 w is CORRECT (mate -7, 14-ply legal PV, verified checkmate). The real defect is
narrower: an INTERMEDIATE depth-8 line carries an ILLEGAL move (b2a2) in its PV plus a mate number the finished
depth-8 search never had.

EXPOSURE (S-C10): 100 real game positions, `go nodes 20000`, PC20, Threads 1, Hash 16 -> 0 of 1 final mate scores
wrong, 0 of 48 intermediate mate-scored lines with an illegal PV. Middlegames at 20k nodes rarely emit mate lines
at all. So: a real but narrow STREAMING display defect on endgames at small node budgets, NOT a match-path defect.

THE GUARD (task 1): `FORGE_FIX_ABORT_PUBLISH` exists (src/search.cpp:65-78), is compiled OUT by default
(`#define ... 0`, line 77) because it was measured on 19,800 exact-node stops and found not to be a repair, and
its publish block is gated on `!stopped_by_nodes_` so a node stop never takes it even when enabled.

FOUR ERRORS RECORDED TONIGHT, none edited away (pcpath/EXPOSURE_FINAL.md lists them):
1. clock-99 zero wrongly called correct (withdrawn, debug/CORRECTION.md)
2. h6h5 hand-written as a pawn push, it is a capture (debug/COST_FINAL.md)
3. a check compared a regex match to "cp 0" when it returns "score cp 0" (check_05F14/)
4. S-F27 headlined as a match-path defect when the final answer is correct and exposure is 0 (this block)
The pattern is always the same: a conclusion that does not match my own raw evidence. Reading the raw lines and
playing them out has caught it every time.

Findings that STAND: S-F1/S-F8/S-F9/S-F10 (mate numbers, S-F1/S-F8 repaired on PC), S-F6/S-F7 (terminal-root
reporting), S-F25 (softnodes deterministic), S-F26 (clock near-miss, do not fix), S-C3, S-C4, S-C6, S-C7.
## 2026-11-16T23:16Z - NEW LIVE DEFECT on the owner's match setting (S-F27/S-F28)

`go nodes 20000` is one of the three node limits the owner's matches use, and it produces a WRONG MATE SCORE:
- 8/8/1p6/8/p3p3/8/2Kpk3/8 w -> `mate -7` with a 10-ply PV that is NOT checkmate (needs 14). 5/5 fresh processes.
- Correct at nodes 50000/100000/250000, at go depth 12 (5/5), and at go softnodes 20000 -> specific to the hard
  `go nodes` abort path at that budget.
- RATE (S-F28): 2 of 14 mate scores wrong (14.3%) at nodes 20000 on 41 bare-material endgame boards, versus
  0 of 17 at go depth 12 (clean control). Second board 8/8/7Q/8/8/6k1/K7/R7 w: mate 7 (10-ply, non-mate) at 20000,
  mate 6 (real) at 50000, true mate 4 at 250000 and depth 12.
- Hypothesis with a location: the node limit stops mid-iteration; the source has a guard whose comment says a node
  limit must not publish a partial iteration for exactly this reason. Not proven.
- Caveat: 14.3% is the ENDGAME rate; middlegames rarely produce mate scores at 20k nodes (S-C8 null, 1 in 100).

ALSO DONE: depth-20 requirement with the depth-14 counter-example now explicit in S-C6; clock near-miss marked
DO NOT FIX and corroborated by four seats; HOW_TO_APPLY_FILE6.md written.

Open thread next: instrumented build on the `go nodes` abort path to confirm the partial-publish hypothesis,
same method that worked for the clock thread.
## 2026-11-16T23:15Z - file 6 closed; PC path measured; two confirmations

FILE 6 POSITIVE CONTROL (S-C6): the inequality DOES fire. Board 8/8/8/8/3k4/8/8/K1Q5 w: counter 0 depth 20 =
mate 8 (needs 15 half-moves); counter 91 (budget 9) = cp 0, 15 > 9, correctly not a defect. At counters 0/50/70
(budget 100/50/30) the engine says mate 8 - so it finds mates when they can finish in time. CAUTION: at depth 14
the same board says cp 1334, so the rule needs depth 20+ or it produces false "no mate" answers.

PC PATH (the path file 6 says counts most):
- S-F25 `go softnodes`: deterministic 3/3 (same score, nodes, move), stops at a finished depth, overshoot 1.06-1.55x.
  One position's MOVE changes with budget (g1f2 @2000 vs d1c1 @20000), so 2000-node self-play is weaker search.
- S-F26 node limits and 6s match clock: all 3/3 reproducible -> match results at Threads 1 are trustworthy.
  Low clock usage (178 ms of 6000) is CORRECT: plan_clock_budget soft limit at 6 s is 317 ms (TmSoftDivisor 22).
  Recorded as a NEAR-MISS so nobody "fixes" correct behaviour.

CONFIRMATIONS: S-C7 checks seat 05's S-F14 -> C1 confirmed (my 21-piece board flat cp 0 at counter 99, depths
6..12 on PC20), C2 REFUTED (pawnless variant scores +63..+87 at counter 100, not a draw); caveat: they used the
base tree, I used PC r15, so build may explain it.

THIRD SELF-CAUGHT ERROR, recorded: my check compared a regex match to "cp 0" while it returns "score cp 0", so the
verdict line said NOT flat while the printed rows were flat. Same species as the other two: a conclusion not
matching its own evidence.

Findings still fully standing: S-F1/S-F8/S-F9/S-F10 (wrong mate numbers; S-F1/S-F8 repaired on PC), S-F6/S-F7
(terminal-root reporting), S-F25, S-F26, S-C3, S-C4, S-C6, S-C7.
## 2026-11-16T22:51Z - FILE 6: clock-99 thread RECLASSIFIED (0 of 8 survive); repair priced at 11-20 plies

Read FABLE_TO_swarm_6. Applied its test to all 8 of my clock-99 boards: counter-0 at depth 24 has NO forced mate
on any of them, and at counter 99 the budget is 1 half-move, so only a mate-in-1 could qualify. **0 of 8 survive**
-> S-F3/S-F4/S-F5/S-F11..S-F18/S-F20 reclassified as not-a-defect (S-C5). My "opponent can decline" premise was
the human FIDE claiming rule; the owner's match program ends the game at the 100th half-move, so there is no claim.

Repair price under real clocks (A = PC r15, B = +repair, PC20, Threads 1, Hash 16, 3 runs, 6s/0.06 style):
BUG boards wtime 1000 depth 22->12 (-11); 5000 32->14 (-18); 10000 36->15 (-20, clock 3.6%->8.1%), moves change
d1c1 -> e2c3. RISK boards unchanged (depth 64 saturated). So the repair is NOT nearly free; with file 6 finding no
bug it buys nothing and costs 11-20 plies -> NOT to be pursued.

Merge answer: apply on its own, NEVER inside FORGE_FIX_ROOT_DRAWN - that flag changes only root classification
(search.cpp:2571-2580) while is_draw runs at every interior node; layering would let a root-only flag silently
change per-node behaviour.

STILL OPEN: a positive-control run of file 6's inequality where it can fire (counters 91/85/80, budget 9/15/20)
is running. Then confirmations on the PC's real path (go softnodes 2000, go nodes 20k/50k/250k, 6s+0.06 clocks).
Findings that still stand: S-F1/S-F8/S-F9/S-F10 (wrong mate NUMBERS, unaffected by file 6; S-F1/S-F8 repaired on PC),
S-F6/S-F7 (terminal-root reporting), S-C3 (seat 06 S-F21 exact), S-C4 (file 5 table exact).
## 2026-11-16T22:28Z - COST QUANTIFIED (S-F20); win positions unaffected; repair consequence stated

Task 1 (cost): scanned 17 candidates from G, required the opponent's reply to be a clock-RESETTING move before
counting a cost. 8 of 17 pass: cp 0 at clock 99 where clock-0 is -40..-1039 cp, and the opponent refuses with a
capture or pawn push (verified mechanically: 4 pawns, 4 captures, clock 0 afterwards). WINNING positions are NOT
affected (+2232 -> +1965, +423 -> +417, +2570 -> +2563), so only the losing side is hurt - consistent with the
mechanism, since a 0-valued draw line is attractive only to the side that is worse.
NOT claimed: that a game result changes. In all 8 the side was already worse; I hunted a "real draw thrown away"
case and every candidate I verified had the opponent NOT resetting, i.e. the engine was right there.

Task 2 (repair consequence): remove the fifty-move test from is_draw entirely, do not move it to the root -
terminality tests must be decidable without searching, and a claimable draw is not. Risks stated: quiet lines to
the horizon are re-valued (slightly overvaluing about-to-be-drawn positions, the same direction as the PC's own
root-drawn fix), and 341-node answers become 15k-19k nodes. For the forced case the legitimate predicate is
"clock >= 100 AND neither side has a capture or pawn move". Not implemented; patch unchanged.

Also in this cycle: S-F15/S-F16 mechanism, S-F17 predictions, S-F18/S-F20 cost, S-F19 repair proposal,
S-C3 (seat 06 S-F21, exact), S-C4 (file 5 table, exact). Next: cycle - other seats' unconfirmed finds.
## 2026-11-16T22:27Z - MECHANISM FOUND (instrumented build), and a correction of my own reasoning

Instrumented build done as the coordinator asked: scratch copy, stderr-only prints behind FORGE_CLOCK99_DEBUG,
EXPERIMENT patch committed as text only (debug/FORGE_EXPERIMENT_clock99_debug.patch.txt), never applied to the
repository source. Ran the three cases: breaking@99, non-breaking@99, control@98.

WHAT THE INSTRUMENTATION SHOWED
- NO root shortcut fires: `root_drawn=0`, all 27 candidates present, and `[DBG ROOT ITER SEARCHED] depth=1..6
  score=0 pv_len=1`. So S-F14's "root shortcut" mechanism was wrong (the observation was right). Corrected.
- 109 `is_draw TRUE` lines, every one `clock=100 fifty=1`: the draw test fires on the CHILDREN, not the root.
- Every root move searched alone: 18 quiet moves -> exactly `cp 0` with a 1-ply PV; 9 reset moves -> -212..-488.
  So the root's 0 IS the max of its children - the arithmetic is consistent.

THE RULE, CHECKED (this is where I had been wrong too)
The fifty-move draw is CLAIMABLE, not automatic. python-chess: at clock 100 `is_game_over(claim_draw=False)` is
False, 25 legal moves, and black simply plays h7h6 -> clock 0, game continues. A winning side never claims.
So white's quiet move does NOT secure a draw and `cp 0` at clock 99 IS WRONG (my original S-F3 stands). I had
briefly written the opposite in is_zero_right.py; that line is withdrawn in the same commit (debug/CORRECTION.md).

MECHANISM, ONE SENTENCE
`Worker::is_draw` scores a CLAIMABLE fifty-move draw as if it were FORCED: the clock-100 child returns 0, the root
takes 0 as its maximum, so at clock 99 a position worth -155 cp is reported as a draw and the engine plays a quiet
shuffle the opponent can simply decline by resetting the clock.

THREE FALSIFIABLE PREDICTIONS, ALL CONFIRMED (S-F17)
- clock 100 with resets available -> also cp 0 (251 nodes) - the fault is not specific to 99.
- clock 100 with NO reset possible anywhere (K+R vs K+R): cp 0 in 32 nodes - CORRECT there. This is the
  discriminating control: the clock-100 test is wrong exactly when a reset exists, which is the
  claimable-vs-forced distinction.
- board whose best moves are resets stays non-zero at clock 99 (cp 549 in 3,918 nodes).

NEXT: keep cycling - next area-5 repetition with a new seed, and re-check other seats' unconfirmed finds.
## 2026-11-16T22:23Z - PC build integrated; coordinator's three tasks done

Built PC r15 from FABLE_TO_swarm_5 (patch sha256 matches, no rejects, -DFORGE_MATE_ALPHA_GUARD=1).
All three rows of file 5's honesty table reproduce exactly (312866/862329/3024920/4865609;
242796/656517; 278024/587276). Read files 3, 4, 5.

Coordinator's three tasks, all answered:
1. REACHABILITY: PROVEN by a legal 99-ply list (reach.txt, verify_walk.py replays and asserts every move);
   PC build answers cp 0 in 661 nodes there vs -15 cp in 32,461 at clock 0. (S-F11)
2. BASE vs PC: break is identical on both builds under default/S14/PC20 - predates r15, not one of the six
   options (S-F12). Onset exactly 99 (S-F13: clock alone is not enough - start position at clock 99 is fine).
   Shape is a root shortcut but the mechanism is UNIDENTIFIED: is_draw (>=100), root_drawn (insufficient
   only) and rule50_damped_static (inert) are all refuted by their own source. Recorded, not guessed (S-F14).
3. Cosmetic: mate 0 on a checkmated root vs cp 0 on a stalemated root, and 64 phantom info lines on a
   terminal root - both survive on the PC build, both re-measured with a plant passing (S-F6, S-F7).

Earlier finds re-run on the PC build: S-F1 and S-F8 are REPAIRED there (mate -4 and mate -8, correct).
Next: continue the cycle - check other seats' unconfirmed finds, then the next area-5 job.
## 2026-11-16T22:18:48Z CONTINUE: 12 more hours, ends at 2026-11-17T10:18:48Z

Resuming under the owner's 12-hour continuation. Seat 25 unchanged (area 5, PVs and scores).
All area-5 jobs 1, 2, 3 are done, plus a second and third run of job 1, plus two independent
reproductions of other seats (S-C1 seat 06 S-F10, S-C3 seat 06 S-F21) and one of seat 10's rule (S-C2).

Immediate plan, in this order:
1. Read every unread FABLE_TO_swarm_N.md from the handoff branch, lowest N first (file 5 = the PC build).
2. Build the PC engine as file 5 says (separate copy, -DFORGE_MATE_ALPHA_GUARD=1), check its bench numbers.
3. Re-run my own finds on the PC build under settings PC20, recording build+settings in every finding line.
4. THE CYCLE: check other seats' unconfirmed finds, else the next job.

Results just before this block (already committed):
- S-F10: the wrong mate score is NOT state; a fresh process reproduces it, and it overrides a correct
  deeper result in the same process.
- NEW and important: S-F8's mate score at depth 20 is HASH-DEPENDENT (mate -7 at 64/256 MB, mate -8 at
  smaller sizes), while S-F1's is stable (mate -5 at every size). Evidence: job1c/hash_dependence.txt.
- verify_all.py: 8/8 headline claims re-verified from scratch (verify_all.txt).
## 2026-11-16T22:00:00Z - all area-5 jobs done; this is my complete state

seat: 25 | area: 5 (principal variations and scores) | seed: 2501 (run 2 used 2511)
branch: for-fable-and-opus/swarm-25 | folder: forge-combo29/swarm/25/

ENGINE: build 6b98f217, release /home/ubuntu/build/release/forge,
sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83.
HONESTY all four match: 312866 / 862329 / 3024920 / 4865609 (HONESTY.txt).
Sanitizer build /home/ubuntu/build/asan/forge: 35 __asan_ + 15 __ubsan_ symbols.

FINDINGS (all with a command that shows them again, all in FINDINGS.md):
- S-F1 CRITICAL: 8/8/1p6/8/p3p3/8/2Kpk3/8 w says `mate -12` at depth 12..16. The engine's OWN depth-28 PV
  checkmates in 8 plies (verify_pv_line.py: "checkmate after 8 plies = mate in 4 moves"), so the true answer
  is mate -4 and the shallow score is wrong by 8 moves.
- S-F2: that root's score wanders -12 / -9 / -6 / -5 / -4 with depth.
- S-F3 + S-F4 + S-F5 CRITICAL: at halfmove clock 99 the engine reports cp 0 at every depth and at
  `go nodes 50000`, on boards with 6-11 legal clock-resetting moves; boundary is exactly 98 (good) -> 99 (0);
  EvalRule50Damp, depths 1..30 and UseNNUE false change nothing; and the clock-99 MOVE is -40/-999/-160 cp
  worse than the engine's own clock-0 move.
- S-F6: a checkmated root reports `score mate 0` while a stalemated root reports `cp 0` (inconsistent).
- S-F7: on a terminal root, `go nodes`/`go movetime` emit 64 info lines at 0 nodes.
- S-F8: the mate-PV defect also hits a middlegame position (score mate -9, 15-ply PV, not a mate).
- S-C1: confirms seat 06's S-F10 depth-10 result with the correction that it does not generalise to depth 12.
- S-C2: independently reproduces seat 10's Clear Hash / ucinewgame rule on my build.

PROCESS AUDITS (both coordinator broadcasts answered, evidence committed):
- 19-F12: my harness is SAFE (stdin open, read to bestmove). Pipelined go+quit does fabricate a2a3.
  audit in check_19F12/. No recorded result of mine used that pattern.
- Clear Hash: never used by me. ucinewgame verified cold on this build (18407 x3 = fresh processes).
  No table of mine needs a warm relabel. audit/warm_cold_audit.txt.
- Rule 1 (a zero needs a planted one): done for job 1 (illegal PV 5/5, wrong mate 5/5), job 2 (clock 98 vs 99)
  and job 3 (planted ASan fault counted 120 times by the same runner).
- Checkers now FAIL LOUDLY (exit 3) on empty input or an unparsed score.

MISTAKES OF MINE, RECORDED NOT HIDDEN:
- job3 first root list: 15 of 20 FENs were not terminal; engine was right, my FENs were wrong. Regenerated
  and verified, re-ran, 60/60 bestmove 0000. Both runs kept in job3/real and job3/final.
- mated.py had a double-pop bug; fixed, S-F1 re-verified with the fixed version (still mated in 4).
- dtm_fast.py and true_mate*.py/dt* are NOT correct (dtm_fast says "no mate" on a position with a verified
  mate in 4); kept in the tree, used for nothing.
- rule50_hypothesis.py v1 sent position before ucinewgame and searched startpos; fixed, now has a guard.
- NO PREDICTION was written for job 3 (process failure, stated in REPORT_job3.md).

RUNNING NOW: nothing. No job is mid-run.

NEXT exact command when sent back (area 5 has no 4th job, so this is cycle (c) with the next seed):
  python3 forge-combo29/swarm/25/job1b/make_R.py forge-combo29/swarm/25/job1c/R3_2521.fens 2521 250
