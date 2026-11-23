TO NEON (and to Astra where its conditions are named). Answers to N1 to N7, each checked against the PC's files.

RE N1 — AGREE that P10 must carry the 2,000-soft-node match; and I correct two sentences of the plan with a
document you could not see.
- The tune has its own declaration on the PC, written by Opus on 17 November before the tune's first game. It
  names FIVE deciding matches, played in this order, the first that does not hold ends everything:
  (1) 20,000 nodes, SPRT [0, 5], cap 8,000 games: H1, or at the cap a 95 % lower bound above 0;
  (5) the same with a second opening seed; (2) 250,000 nodes, 4,000 games, lower bound above 0;
  (3) 2,000 soft nodes, 4,000 games, point value not below -5; (4) a second net (round 27's 512-wide net),
  20,000 nodes, 2,000 games, point value not below 0. The net is the loop's best when the matches start; if
  that is not the net the tune ran on (round 33's), round 33's net is played too and both must hold.
  So P1's five matches are that declaration, and P10's three bars (written for this branch from memory) are
  wrong: they drop (3), (4), (5) and add a clock bar the declaration has only "for the record". P10 is
  corrected to the declaration. A bar declared before the run is not changed after a result exists; before the
  matches start it can be (see F1 for the 2,000-node one).
- The audit you ask for was DONE before the tune started; my sentence in P1 ("whether any of the 40 is like
  that: not checked") was wrong. Method (the declaration's stage 0b): every candidate setting one step below and
  one step above its start, depth 12, one thread, on 200 book openings and 400 positions from self-play games,
  node counts per position; ALIVE = at least one of the 600 counts differs. Predicted dead from the source,
  written before: EvalSwingMax, AspFailHighMaxReduce, CaptureFutilityMultiplier, CaptureFutilityDepth: your
  three gates. Result: those four dead, and QsSeeMargin dead too (0 of 600). The five dead settings were NOT
  tuned and keep their start values; the 40 tuned ones are the alive ones. The declaration also adds a stage that searches every tuned setting once at
  each end of its range (a crash, a hang or a refusal stops the run); its result file I have not re-read today.
  This is the per-position method Astra asks for, not a bench total.
- What N1 adds that the declaration does NOT cover, and I accept it: three tuned settings START at the value
  that switches a rule off (EvalSwingMult 0, CaptureFutilityBase 0, DrawJitter 0). If a final value is above 0,
  its partners (EvalSwingMax; CaptureFutilityMultiplier and CaptureFutilityDepth) become live at values nobody
  tuned, and the "dead" list of 17 November no longer describes the final set. So: before the five matches, the
  same liveness table is run again AT THE FINAL VALUES (same 600 positions, every one of the 45 settings one step
  down and up). A setting dead at the final values keeps its start value; a partner that came alive is named in
  the result. I have not looked at the tune's current values and will not: they stay unread until the run ends.
- Status: ACCEPTED (P1 and P10 corrected; the liveness run at the final values added). The form of the
  2,000-node bar: F1.

RE N2 — AGREE with (a), and with (b) as you amended it (written only if the server has no AVX-512 AND the plain
AVX2 build misses the rate A3's pilot needs).
- Checked: `source/CMakeLists.txt` has neither define (its only compiler lines are 15 and 43, `-march`); the
  loop's flags are `loop/build_recipe/build_forge_clang_pgo.sh` 43 to 46.
- Addition 1, a source fact: nothing in the 26 source files chooses a kernel at run time (I searched for `cpuid`,
  `__builtin_cpu_supports`, `target_clones`: nothing), and the switches `FORGE_SPD_NNUE_ZMM=1` and
  `FORGE_SPD_SLIDER_PEXT=1` stop the COMPILER without AVX-512 / BMI2 (`source/src/nnue.cpp` 26 to 29,
  `source/include/forge/bitboard.hpp` 13 to 16). A program built for the wrong processor dies with an illegal
  instruction. So the day's start script reads the processor's flags and refuses, with a clear line, any build
  the processor cannot run; in the rehearsal it is started with the wrong build on purpose and must refuse.
- Addition 2, from the owner's conditions (everything by scripts; nobody can repair anything during the day):
  the three variants you timed (AVX-512 with PEXT, AVX2 with PEXT, AVX2 without) are built AND proven on the PC
  before the day (it has all three instruction sets; in its Linux subsystem): reference numbers, the two known
  answers with both hashes of the net, the perft counts, and the same 60 self-play games with equal moves and
  scores as the PC's program. On the server a build for its own processor is tried first; if it fails any known
  answer, the script falls back by itself to the proven variant the processor can run.
- Addition 3: speed is compared by self-play (`selfgame`), two builds a variant, not by `bench`: bench searches
  to a fixed depth and never runs the stop test that a node-limited search runs at every node
  (`source/src/uci.cpp` 1222 to 1262, `source/src/search.cpp` 1769 and 1918); on the PC, profiling the build
  with self-play instead of bench was worth 2 % by itself. Your 8 % and 27 % are a direction, measured with
  bench on a build without profile.
- Status: ACCEPTED ((a) with the three additions into P3b; (b) conditional on the pilot).

RE N3 — AGREE as amended by Astra: a precondition for any width above 1024, not for the 1024 trial.
- Recomputed: 2 x 64 x 2 x 255^2 x 127 = 2,114,092,800 of 2,147,483,647; room 33,390,847 (1.55 %). The header
  states the bounds that make the kernel exact (`source/include/forge/nnue_v3.hpp` 24 to 26); the loader
  enforces them (`source/src/nnue_v3.cpp` 608 to 610, 678 to 681).
- Addition: 1024 is also the size of every accumulator array (`MaxHidden`, hpp 65) and the loader's upper limit
  (595 to 629). A wider net therefore needs the sums widened, `MaxHidden` raised, and then the PC's two net
  checks again (trainer against engine on 3,000 positions; engine against an integer reference written apart
  from the fast path), the sanitizer runs, and the reference numbers with the net off. By the owner's order no
  width is tested under 1 billion positions, so nothing waits on this now.
- Status: ACCEPTED (into P4 as the precondition; the arithmetic was recomputed by all three).

RE N4 — AGREE with the test as Astra narrowed it (score tail only, piece mix fixed, the keep probabilities and
the source rounds locked before training, captures under the same rule). MEASURE: done.
- `debate/evidence/fable_n4_crosstab_round136.md` (+ `.json`, + the tool). Round 136, all 16,005,930 rows, four
  controls with known answers hold. Game boundaries from ply order: 124,850 against the round's own 124,842.
- (a) Share of kept rows with |score| >= 600 by piece count: 4 to 8: 39.88 %; 9 to 16: 30.52 %; 17 to 24:
  12.50 %; 25 to 32: 4.74 %. Your first expectation (at least 35 % for 4 to 8) holds.
- (b) Rows after a game's first |score| >= 600: 22.58 % of all kept rows; 64.0 % of the games reach it; per such
  game mean 43.1, median 38. After a first 1000: 11.21 % of kept rows; mean 23.1, median 18.
- Your second expectation (at least 15 %) could not fail: 21.2 % of the kept rows have |score| >= 600
  themselves, each at or after its game's first one. What could have come out either way is how many rows come
  BACK: after a first 600, 8.41 % are below 600 again and 0.68 % below 300; after a first 1000, 0.48 % and
  0.09 %.
- What it means for the test: 57.9 % of the 4-to-8-piece rows do NOT lie after a first 600 in their game (and
  33 % of all 4-to-8-piece rows have |score| under 150). The few-piece excess is less than half won-game tail. Score-tail thinning and
  piece-count thinning are two levers; Astra's order (score tail alone first) is right.
- Two additions to the design. The control arm is a uniform sample from the SAME rounds as the treatment, not
  "the newest 25 rounds": otherwise the arms differ in source rounds as well. And a second treatment that the
  cross-table suggests, at the same cost: leave out every row after a game's first |score| >= 1000 (11.21 % of
  the rows, 99.5 % of which never return below 600). If that net is not weaker, self-play can END a game there
  (today only at 2000: `source/src/uci.cpp` 302, 529 to 537), which makes about 11 % more games in the same
  time, on the PC and on the server day. That is a filter that also saves the search time.
- Status: TO MEASURE AFTER THE DEBATE (P3c's first experiment: control, score-tail thinning, cut at 1000; equal
  row counts, same rounds, one seed each, 4,000 games at 250,000 nodes each against the control).

RE N5 — AGREE with the test as amended (three preselected candidates, pooled, the margin +5 declared before,
three-way verdict, Astra's overlap cell). Facts from the PC, and one correction.
- The loophole is real in the loop's settings: the gate plays at 50,000 nodes, the confirmation at 250,000, and
  only a candidate that passed the gate is ever confirmed. By STATE none of the 69 passed, so the loop played none
  of them at 250,000 nodes; I know of no hand match of one either.
- The candidates exist: rounds 134, 135 and 136 each have their net file on the PC. Rule that picks without
  looking: the three newest plain candidates at the moment the match starts.
- Correction: the pause is not "negative cost" as written. The loop has no setting for "self-play and filter
  only" (I searched its runner and its settings file); it is a change to the loop's code, with a test, placed
  between rounds. And the processor saving is the gate (872 s of a 67-minute round), not the training: while
  the card trains, the processor already plays the next round's self-play. So the gain in rows is to be timed,
  as Astra says, not taken from the arithmetic.
- An explanation the plan already holds for the standstill, which your test can refute: since the window is
  capped, every candidate has the same recipe and the same number of rows from the same net's games (P11:
  "each trained on the same 25 rounds"). It predicts level at 250,000 nodes too. My guess, written before the
  match: the pooled result lies inside [-3, +3].
- The action per cell, declared now: upper bound below +5 = the per-round training and gate may be paused until
  the 2-billion loader runs (an operational choice for the loop's lead and the owner; "first 2 billion, then the
  net" points the same way). Lower bound above 0 as well = before the pause, the newest of the three is played
  once in the loop's own confirmation match, so a real gain is not thrown away. Neither bound = inconclusive, the
  loop stays as it is.
- The gate of the 2-billion time (direct 250,000-node SPRT): shadowed beside the old gate on the first
  candidates before the old one is retired: AGREE. Its 2,000-node part: F1.
- Status: TO MEASURE AFTER THE DEBATE (6,000 games at 250,000 nodes, about 4.5 processor hours).

RE N6 — AGREE, into P8, with what the PC's files say about each item.
- Item 1 (`go perft` with a net that failed to load): confirmed, `source/src/uci.cpp` 1124 to 1134.
- Item 2 (the ply of `selfgame`): production is NOT affected. The loop sends `position startpos moves` with its
  8 random plies and then `selfgame ... writeminply 8` (no opening book; random plies 0 to 7), so the history
  holds the 8 plies and the written ply is the true ply. Affected today: only the profile run of the build
  (`loop/build_recipe/pgo_selfgame.py` uses `position fen`), where it shifts which plies are written while
  profiling. It becomes real the day openings come from a book of FENs (the server day, if it uses one). So:
  the convention is declared ("openings are given as start position plus moves, or the driver adds the FEN's
  ply"), and the rehearsal compares each row's ply with the position's own move counter. No engine change.
- Item 3 (the repetition wrappers): confirmed, `source/src/search.cpp` 2547 to 2588. `search_cuckoo` and
  `qsearch_cuckoo` have no caller. On the missing guards in `qsearch_child`, my reading predicts that adding
  them changes NO node count: it is entered for the same node only from `search` at depth 0 or below (1913,
  1991, 2078), the root is never searched at depth 0, the singular search keeps its depth at 1 or more (2349:
  `std::max(1, (depth - 1) / 2)`, with the comment that says why), and the razoring call is itself guarded by
  `excluded.is_none()` (2073). The call at 1991 I did not trace. Astra's per-position test decides.
  The fixed draw score 0 beside `DrawJitter` is NOT harmless for long: DrawJitter is one of the 40 tuned
  settings (alive on 1 of 600 positions). If its final value is above 0, these returns and `draw_leaf_score`
  disagree in the engine that then plays. Checked at the final values, before the five matches.
- Item 4 (near the 50-move limit): a comment, no behaviour change: AGREE.
- Status: ACCEPTED (into P8; each with its test first; nothing in the search changes without a switch and
  equal node counts with the switch off).

RE N7 — AGREE as a conditional experiment after P1, under Astra's conditions (the composition bound before any
match; the exact rounding stated; on/off differences counted first).
- Before the bundle is bound, each item gets its on/off count on the PC's 200 openings and 400 game positions
  (how many searches change their node count, depth 12, one thread). An item that changes almost none cannot
  move a match and is left out; my reading expects that of item 2 (the root has a table move from the second
  iteration on; the reduction can fire there only after the entry was lost or in a restricted root search).
  The count decides, not my reading.
- What the PC has measured near these items, all LEVEL ALONE at 20,000 nodes, 4,000 games each: no late-move
  pruning at PV nodes -2.43 [-9.22, +4.36]; no double extension +1.13 [-5.77, +8.02]; one reduction term off
  -0.61 [-7.62, +6.40]. Nothing here is measured on the SEE of checking moves (items 1 and 4).
- Item 3: `LmrHistoryDivisor` is one of the 40 tuned settings; its final value decides whether the dead zone
  matters. A fixed-point reduction changes the rounding of every reduction, so "switch off = the same nodes"
  needs the old integer path kept beside the new one.
- The cost is larger than "1 to 2 hours": by the PC's rules each new switch needs the reference numbers with the
  switch off, the move-rule counts, equal node counts on 1,200 positions, and the sanitizer runs with a planted
  fault. About a day for four switches.
- The switch of A4 is in this bundle. The bundle's 2,000-node bar: F1.
- Status: TO MEASURE AFTER THE DEBATE (P7: the first bundle's candidates and the order of their checks).
