# Fable to glmflash3, file 2 (2026-11-15): answer to job 1, and job 2

## Your job 1 report

Read in full; the 15 known numbers, the three controls and the match table checked against your files.
What I take from it:
- **B4 per node: +24 (95 % 16 to 34, 3,000 games).** On the owner's PC the same bundle, ported into today's
  engine, gave +17 at 250,000 nodes and +21 at 2,000 nodes, and today, at EQUAL TIME (it gets 7.6 % fewer nodes
  for its slower speed), +10.6 +/- 8.6 over 2,000 games. It went into the engine the PC plays with at 15:52.
  Your number was one of the independent measurements behind that decision.
- **LmrTableV2 on top of B4: -1.4 (95 % -11.5 to +8.7).** That closes my open question; it is not added.
- B2 and B3 stronger than the base per node, with the mechanism named (18 % and 32 % fewer nodes at the same
  depth, which a clock test pays for and a node test does not): the right reading, and you said yourself that
  the cut B3 row closes nothing.
- Done well: you found your own mistake in M1 (`-rounds 3000` instead of 1500), kept the prescribed 3,000 games
  as the primary row and the surplus as a cross-check, instead of quietly reporting the larger number.
- One thing to keep an eye on: M5 and M6 were not started. Say in the first paragraph next time what was not
  reached, not only in the table.

From the others: a helper's speed patch was bit-exact and gained nothing, and it measured why before anyone
asked (counters first, patch second): that is P1 of the job below. A repair written to MY rule turned out wrong
when I read it line by line; known-answer rows now come with every rule.

## Job 2. BUDGET: 80 minutes by the clock; at 70 minutes stop and write the report with what you have.

A new kind of job: you WRITE a search feature, as a text patch, and prove it. Rules: those of your first message
(your own machine only, no pull request, no engine source committed, new files only in your folder, text only, no
binary files, no `__pycache__`). Folder `forge-combo29/tests_glmflash3_job2/`, report `forge-combo29/REPORT_glmflash3_job2.md`,
commit subject "glmflash3 job 2 report". After pushing, wait for the next file with the sleeping command of your first
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
        C   control: 20,000 against 10,000 nodes (per-engine nodes), 300 games, seed 7600: must be near +200
        M1  `PawnHistory` on against off, 2,000 games, seed 7601
        M2  the same again with seed 7602, 2,000 games: ALWAYS, whatever M1 says (the best or worst of one
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
