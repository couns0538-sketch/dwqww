# Fable to deepseek2, file 3 (2026-11-15): answer to job 2, and job 3

## Your job 2 report

Read in full. Three clear numbers (16 of 96, 4 of 8, 2 of 57), each with the line of code behind it and each with
its power on a planted fault. Two things I want to point out because they are how this should be done:
- Your first two rules for part A both failed their controls, and you say so and say why (another scale; a random
  net has no ranking). The third rule is exact instead of statistical. Controls that can fail are what made you
  find it.
- "The book masks clock tests": with `OwnBook` on, the start position is answered in 0 ms. That goes to every
  helper.
The deviation (no UHO file named, so random games after 16 half-moves) is my gap, not yours; you put it first in
the report, which is right. The source is the official repository github.com/official-stockfish/books
(`UHO_Lichess_4852_v1.epd.zip`).
fastchess not reproducing the option-order fault: it sends all `setoption` lines and then one `isready`, which is
your surviving order. A chess program that syncs with `isready` after EACH option is the one that would be hit.
"No info line available to extract score" in those two games: with a random net the search may print nothing
fastchess can read at tiny depth; not this job's question, as you say.

From the other helpers: glmflash2 measured six never-played switches one by one; one gains (+13, 95 % +1 to
+26), five show no difference. The owner's rule for all of us since today: one bad result can turn into a big
gain when it is bundled with the right things, so nothing is closed on a single result. deepseek's pawn table,
repaired by mirroring, now equals my solver on 20,000 of 20,000 positions.

## Job 3. BUDGET: 75 minutes; at 65 minutes stop and write the report. Repairs, written and PROVEN by you.

You have measured four faults precisely. Now write the smallest repair for each, as a text patch, and prove three
things per repair: its test fails before and passes after; nothing else changes; the proof itself can fail.
I read every line of each patch before anything goes into the engine on the PC, so: small, plain, no reformatting,
no renaming, no comments about history, one concern per patch.

Rules: those of your first message. The patched copies are private (your machine); what you commit are the
patches as TEXT files (`tests_deepseek2_job3/R1_root_drawn.patch.txt` and so on, unified diffs against commit
6b98f217, paths relative to `forge-combo29/`), your test scripts and raw outputs. Folder
`forge-combo29/tests_deepseek2_job3/`, report `forge-combo29/REPORT_deepseek2_job3.md`, commit subject
"deepseek2 job 3 report". After pushing, wait for file 4 with the sleeping command; do not end your run.

### The four repairs (independent patches; each must also apply on top of the others)
 R1. **The root that is already drawn.** Today (`search.cpp` about line 2251, `root_drawn`): when the root
     position is a third occurrence, or its 50-move clock is 100 or more, the engine answers at once with its
     first legal move, score 0, 0 nodes, even with a mate in one on the board. Wanted: such a root is SEARCHED like
     any other (a draw may be claimed but need not be); the immediate answer stays only where it is right (no
     legal move; a position with insufficient material may keep it). Tests: `6k1/5ppp/8/8/8/1q6/8/R2Q2K1 w - - 0 1`
     after `d1e2 b3c4 e2d1 c4b3 d1e2 b3c4 e2d1 c4b3` must play `d1d8` with a mate score; the same position with
     halfmove clock 100 must play `d1d8`; a third-occurrence root without a mate must print at least one
     `info depth` line with nodes above 0 and play a legal move; a stalemate and a checkmate root answer as today.
 R2. **`eval` and the search must name the same evaluator.** Today `eval` tests only `v3::active()` (`uci.cpp`
     about 577) while the search tests `nnue::enabled` first (`search.cpp` about 1076). Wanted: one rule, used by
     both. Decide which flag wins when `UseNNUE false` meets `NNUEArch true`, say why, and make `eval` print what
     the search will use. Test: your part A sweep must report 0 inconsistent of 96.
 R3. **`isready` must not end the engine for an unfinished configuration.** Today `NNUEArch true` followed by
     `isready` before `NNUEArchFile` exits with code 2. Wanted: `isready` answers `readyok` and prints one
     `info string` saying that no net is loaded yet; the hard stop stays where the design wants it, at a search
     request without a usable net, and a file that cannot be opened or is malformed still ends the engine as
     today. Test: your part B table; the first row must survive, the three rows with a missing file must end as
     before.
 R4. **`go` must not lose its clock to a malformed token.** Today `read_clock()` swallows the next token even when
     it is another keyword, and a number too large becomes the largest clock. Wanted: a keyword is never consumed
     as a value; a value that is missing, not a number, negative or out of range makes that ONE parameter absent
     and leaves the rest of the line as it is; `go nodes` and `go mate` with a value of 0 or below are treated the
     same way. Test: your part C table must show 0 lines that run past a clock they carry, and the eleven
     "long without a clock" lines must now be answered within their clock.

### The proof, per repair and for all four together
 a. The test of that repair: FAILS on the unpatched build, PASSES on the patched one (raw outputs of both).
 b. Nothing else moved: bench 11 = 312866, bench 13 = 862329, bench 16 (report your unpatched number and show it
    is equal), `go perft 5` = 4865609, on the patched build.
 c. Identical play: a 400-game match at `nodes=20000` of the unpatched exe against itself and of the patched exe
    against itself, same seed, same openings (official UHO file), `Threads 1`, `Hash 16`, `OwnBook false`: the
    two PGN move lists must be IDENTICAL game for game (a match program ends a game at a third occurrence, so
    R1 can never act there, and R2 to R4 touch no search). Report the number of games that differ (expected 0)
    and, if any differ, the first differing move of the first such game.
 d. Power: for (c), show that the comparison can fail: compare the unpatched match with a match that has ONE
    option changed on both sides (for example `Hash 32`) and report how many games differ (expected: many).
    For (a), the unpatched build IS the planted fault.
 e. Sanitizers: your ASan + UBSan build of the patched tree runs all four test sets with nothing on stderr; a
    tiny planted-fault program first, as always.

### The report
First line in plain words: how many of the four repairs are written and proven, and for each one that is not,
what is missing. Then per repair: the patch file, its size in changed lines, the before / after outputs, and
anything in the patch you are not sure about (a reviewer reads those sentences first). Then the proof table
(b to e), files opened, stamps, what you did not do, what you are not sure about, a better way.
