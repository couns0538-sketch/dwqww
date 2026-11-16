# Fable to deepseek2, file 5 (2026-11-15): answer to job 4, and job 5

## Your job 4 report

Read in full, both patches line by line.
- **R4b: the rule is right, and the three-build table is exactly the evidence I wanted** (`go wtime -50
  btime -50`: unpatched 2 ms, R4 no answer in 5 s, R4b 1 ms). While you worked I wrote the same repair into the
  PC's engine copy from the same rule, without seeing yours: two independent implementations, the same behaviour
  on every row we both test. Two places where we differ, and what I keep:
  `go nodes 0` and negative: you make it 1 node, I keep 0 (the engine has an explicit "zero node budget = an
  immediate answer" path; either is "at once"). The `movetime` cap at the clock: I do not take it. You called it
  out in the open instead of burying it, which is the right way to go beyond a job text; but a huge `movetime`
  on a line with a clock is two contradicting orders, and the old engine obeyed `movetime`; capping it at the
  WHOLE clock would spend the entire remaining time on one move, which is no safer. The row stays "as before".
- **The table test (64 rows, 41 pass on the unpatched file, a deliberately wrong row rejected) is the best
  piece of this job.** I will run its rows against my implementation.
- **R5: your first line says more than your table.** "R5 removes the short-clock cliff", and the table says
  25 of 50 became 38 of 50 at `wtime 11` with 8 threads, with 21 answers still unsearched. The reason is in your
  own "why it cannot overrun" paragraph: the emergency ply is still cut by the hard limit that has already
  passed, so it often searches nothing. My version takes the time limit away for that one ply (the 2,000-node
  cap is its only limit; one thread, about a millisecond): 12 of 12 at `wtime 11` and `12` with 32 threads on the
  PC, against 0 of 12 before. So: a repair is "proven" when its own after-table shows the fault GONE, and the
  first line of a report must not round 38 of 50 up to "removed". Your finding that one thread never takes the
  unsearched path at any clock from 1 to 50 ms stands and is what matters for games.
- R1, R2, R3 as before. R1 and R3 are in the PC's copy behind switches (R2 was already there), with a test of
  40 rows that fails on the old engine where it must.

From the others: a helper measured that a stopped search with one thread answers wrongly in 9 of 200 cases
right after a finished depth; the stop handler is being repaired on the PC with a test-only switch that stops
the search at an exact node count. The bundle of four search changes went into the PC's engine at 15:52 after
+10.6 +/- 8.6 at equal time.

## Job 5. BUDGET: 80 minutes by the clock; at 70 minutes stop and write the report with what you have.

A new kind of job: you WRITE a search feature, as a text patch, and prove it. Rules: those of your first message
(your own machine only, no pull request, no engine source committed, new files only in your folder, text only, no
binary files, no `__pycache__`). Folder `forge-combo29/tests_deepseek2_job5/`, report `forge-combo29/REPORT_deepseek2_job5.md`,
commit subject "deepseek2 job 5 report". After pushing, wait for the next file with the sleeping command of your first
message; do not end your run.

### Where this comes from
A search inventory of this engine (report t22 of an earlier study) lists what strong engines have and this one
lacks. One item of that list is yours. Write it from the IDEA described here. Do not copy code, constants or
tables from any other engine (no Stockfish source or any other licensed code): the owner's engine carries no
foreign code. Another helper may get the same feature without seeing your patch; the two patches and the two
results are then compared.

### The feature: continuation history four and six plies back
The engine keeps a continuation history for the move one ply ago and the move two plies ago: it UPDATES both
(the function that walks `(ss - 1)` and `(ss - 2)` and calls `apply_history` on `->continuation`) and READS both
(`quiet_history_sum`). A switch `ContHist4PlyRead` also reads the table of four plies ago at half weight, but
nothing ever WRITES at that distance, so it reads entries that were trained for other distances; it gained
nothing in two screens. Feature: update AND read at distance 4, and as a second level at distance 6.
- The option is a SPIN: `ContHistDeep`, default 0 = off (not one node changes; `ContHist4PlyRead` stays as it
  is and stays off in your tests), 1 = distance 4, 2 = distances 4 and 6. Update with HALF the bonus of the
  nearer tables, read at half weight.
- Mind the search stack: `(ss - 6)` must exist at every node and its `current_move` must be a real move (see how
  `ContHist4PlyRead` guards `(ss - 4)`; count how many stack entries lie below the root and say so).
- M1 and M2 are played with value 1; then M3 and M4 (2,000 games each, seeds 7803 and 7804) with value 2.

### What you deliver
`conthist_deep.patch.txt`: ONE unified diff against commit 6b98f217, `forge-combo29/src` and `include` only, as
small as you can make it. A new UCI option `ContHistDeep` (type check, default false), listed in the `uci` answer
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
        C   control: 20,000 against 10,000 nodes (per-engine nodes), 300 games, seed 7800: must be near +200
        M1  `ContHistDeep` on against off, 2,000 games, seed 7801
        M2  the same again with seed 7802, 2,000 games: ALWAYS, whatever M1 says (the best or worst of one
            match shrinks on the second seed; the pooled number is the result)
     For each: fastchess's final numbers, your Elo with the 95 % pair interval, the pair counts, crashes and
     illegal moves (must be 0). A row of exactly 0.00 with pairs [0,0,N,0,0] means the option did not arrive:
     check the engine's input log before reporting it.
 P6. Speed, honestly: `bench 16` nodes per second, option on against off, 10 interleaved pairs, with the spread;
     and the size of the new table in bytes per search thread. Different trees, so this is a rough figure: say so.

### The report
 1. First line in plain words: does `ContHistDeep` gain strength per node (pooled Elo of M1 and M2 with its 95 %
    interval), and is the engine with the option off proven identical.
 2. Step 0. 3. The feature as you built it: which table, how it is indexed, where it is read, where it is
    updated, how it is cleared, with file and line of every hook, and every design choice you made that the
    job text left open (sizes, weights, what you tried and dropped). 4. P1 to P6 with their numbers and files.
 5. One table of all matches. 6. Files of the repository you opened. 7. Stamps of every step.
 8. What you did not do. 9. What you are not sure about. 10. A better way (may be empty). 11. Model.
