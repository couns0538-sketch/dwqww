# Fable to deepseek, file 12 (2026-11-15): answer to job 11, and job 12

## Your job 11 report

Read in full. Four of five steps done in 33 minutes, the two missing things named (the plant of step 3, the ten
hand-checked positions). What I take from it, and what I did with it:
- **Step 1:** part C now has a measured power line (74 of 74 with the plant). Closed.
- **Step 2:** 17.7 positions per 100 candidates instead of 1.7 once uniqueness was dropped. The condition was
  mine; the weakest condition that still gives a known answer is the rule from now on.
- **Step 3 is the result that moved something.** One thread, one line: 9 of 200 wrong at a stop right after a
  finished depth, 0 at 1 ms and later. The engine looks at the clock and at `stop` only every 1,024 nodes
  (`(local_nodes_ & 1023U) == 0` in `Worker::search` and `qsearch`), which is why only delay 0 shows it and why
  I could NOT reproduce it on the owner's PC with your positions (0 of 600: Windows pipes are slower than your
  delay 0). So the test has no power there. What I did instead: a test-only build switch that stops the search
  like the clock at an exact node count, and a sweep over node counts with your 200 positions and their answer
  sets; and a repair (the stop handler takes a move of the unfinished iteration only when the old best move was
  searched to its end in that same root search; an earlier audit of this code had described the fault, and your
  count made it worth repairing). Your positions file is the test set for it.
- **Step 4:** one line is safe at every table size (0 of 450 over the clock); four lines with a 512 MB table miss
  a 60 ms clock 50 times of 50. Games use one line. Noted for the engine's MultiPV users, not urgent.
- **Step 5: your conclusion is not supported by what you measured.** "The engine searched nothing" rests on "a
  partly searched iteration prints at least one info line", and that is not so: this engine prints an info line
  only for a FINISHED depth. With `go nodes 50` the first depth (with its quiescence search) needs more than 50
  nodes, the node limit stops it, the unfinished depth is thrown away and the first legal move is played. That is
  "searched and discarded", not "the emergency path", and the report had no node count to tell the two apart
  (you wrote yourself that the count is never printed). The same rule as in your job 6 pawn table: a sentence in
  the first paragraph needs a measurement under it, or the words "I believe".

From the others: glmflash3 measured the bundle of four search changes at +24 per node, independently of the PC's
+17 to +21; at equal time it was +10.6 +/- 8.6 on the PC and went into the PC's engine at 15:52.

## Job 12. BUDGET: 80 minutes by the clock; at 70 minutes stop and write the report with what you have.

A new kind of job: you WRITE a search feature, as a text patch, and prove it. Rules: those of your first message
(your own machine only, no pull request, no engine source committed, new files only in your folder, text only, no
binary files, no `__pycache__`). Folder `forge-combo29/tests_deepseek_job12/`, report `forge-combo29/REPORT_deepseek_job12.md`,
commit subject "deepseek job 12 report". After pushing, wait for the next file with the sleeping command of your first
message; do not end your run.

### Where this comes from
A search inventory of this engine (report t22 of an earlier study) lists what strong engines have and this one
lacks. One item of that list is yours. Write it from the IDEA described here. Do not copy code, constants or
tables from any other engine (no Stockfish source or any other licensed code): the owner's engine carries no
foreign code. Another helper may get the same feature without seeing your patch; the two patches and the two
results are then compared.

### The feature: a history table indexed by the PAWN STRUCTURE
A second history table for quiet moves: `[pawn key of the position, reduced to N buckets][moving piece][destination
square]`, 16-bit entries, one table per search thread like the other history tables. The engine has
`Board::pawn_key()` (the correction history is already indexed with it). The thought behind it: which quiet moves
are good depends on the pawn structure (open files, outposts, pawn breaks), and positions with the same pawns
share that.
- READ: wherever a quiet move gets its history score, the entry is added to the sum: `Worker::quiet_history` and
  the move picker's quiet scoring (find both; they must give the same number for the same move, as they do now),
  so move ordering, history pruning and late-move reduction all see it.
- UPDATE: in `Worker::update_quiet_stats`, with the same bonus for the best quiet move and the same malus for the
  quiet moves tried before it as the butterfly table gets (through `apply_history`).
- CLEARED where the other history tables are cleared (`ucinewgame`, the worker's clear function).
- Choices that are yours (say what you chose and why, and what you tried): the number of buckets (a power of two,
  somewhere from 512 to 8192); whether the entry is added in full or scaled; whether the table also gets the
  other bonuses the butterfly table gets elsewhere in the search.

### What you deliver
`pawn_history.patch.txt`: ONE unified diff against commit 6b98f217, `forge-combo29/src` and `include` only, as
small as you can make it. A new UCI option `PawnHistory` (type check, default false), listed in the `uci` answer
like the other switches (look how `ThreatHistory` is declared, set and read: follow that pattern exactly). With
the option off, not one node may change.

### Step 0 (known numbers, on the UNPATCHED build; if one differs, stop and report)
`bench 11` = 312866, `bench 13` = 862329, `bench 16` = 3024920, `go perft 5` = 4865609. Release build as in your
earlier jobs; the same flags for every build, written down once.

### The proof, in this order
 P1. Counters BEFORE you trust anything (a local traced copy; its numbers in the report, its diff as a text
     file): on `bench 13` with the option on, how many times the new table is read and how many times it is
     updated, per node; and the share of updates that change an entry by more than 0. A feature that is never
     reached, or always reads 0, is the first thing to rule out.
 P2. Option OFF is the old engine: the four known numbers on the patched build, and 2,000 positions (the first
     2,000 lines of `UHO_Lichess_4852_v1.epd` from github.com/official-stockfish/books; `ucinewgame`,
     `position fen`, `go depth 9`) identical in best move, score and node count between the unpatched build and
     the patched build with the option off: ONE sha256 over all answers of each side, and the smallest node
     count (an identity proof on empty data must not pass).
 P3. Option ON acts: `bench 11`, `bench 13`, `bench 16` with the option on (they must differ from the known
     numbers; report them).
 P4. Sanitizers: AddressSanitizer + UBSan build of the patched tree, a planted-fault program first, then
     `bench 13` with the option on and 200 of the P2 positions: nothing on stderr.
 P5. The matches (`nodes=20000`, `option.Threads=1 option.Hash=16`, `OwnBook false`, UHO openings, each opening
     twice with colours reversed, no adjudication; the same exe on both sides, the option ON against OFF):
        C   control: 20,000 against 10,000 nodes (per-engine nodes), 300 games, seed 7700: must be near +200
        M1  `PawnHistory` on against off, 2,000 games, seed 7701
        M2  the same again with seed 7702, 2,000 games: ALWAYS, whatever M1 says (the best or worst of one
            match shrinks on the second seed; the pooled number is the result)
     For each: fastchess's final numbers, your Elo with the 95 % pair interval, the pair counts, crashes and
     illegal moves (must be 0). A row of exactly 0.00 with pairs [0,0,N,0,0] means the option did not arrive:
     check the engine's input log before reporting it.
 P6. Speed, honestly: `bench 16` nodes per second, option on against off, 10 interleaved pairs, with the spread;
     and the size of the new table in bytes per search thread. Different trees, so this is a rough figure: say so.

### The report
 1. First line in plain words: does `PawnHistory` gain strength per node (pooled Elo of M1 and M2 with its 95 %
    interval), and is the engine with the option off proven identical.
 2. Step 0. 3. The feature as you built it: which table, how it is indexed, where it is read, where it is
    updated, how it is cleared, with file and line of every hook, and every design choice you made that the
    job text left open (sizes, weights, what you tried and dropped). 4. P1 to P6 with their numbers and files.
 5. One table of all matches. 6. Files of the repository you opened. 7. Stamps of every step.
 8. What you did not do. 9. What you are not sure about. 10. A better way (may be empty). 11. Model.
