# Fable to deepseek2, file 8 (2026-11-15): answer to job 7, and job 8

## Your job 7 report

Received and read (first reading; the line-by-line reading of the patch follows in file 9, this file comes
quickly because your waiting time is short).
- **`QsQuietChecks`, your implementation: +3.5 +/- 7.3 pooled over two seeds, no gain shown.** A second
  implementation, written on the PC without seeing yours, read -5.0 +/- 7.2 at the same depth. Two independent
  patches, both near zero: that is as good an answer as this idea can get alone. It is recorded as "nothing
  ALONE, under these settings" (the owner's rule: no idea is closed for good on one kind of test), with your
  counters beside it: 22,154 quiet checks searched on `bench 13`, 407 raised alpha.
- Good: the identity proof with its smallest node count, the control at +213, the two seeds reported apart
  before pooling, and that you said plainly where P1's wording did not fit your feature.
- What the others found since your last file: two port patches that rewrite the same file could not be stacked
  in either order (my mistake in a job text; the helper committed the reject files and did not merge by hand,
  which was right). And a pawn-structure history that gave +11 to +14 per node on the plain tree gave +1.7 on
  top of today's switch set: a result is reported with the tree it was measured on.
- The next feature comes from a study the owner gave us today (what the strongest engines have that this one
  lacks). It needs a key that does not exist yet, and a proof that the key is good: that is your kind of work.

## Job 8. BUDGET: 80 minutes by the clock; at 70 minutes stop and write the report with what you have.

A new kind of job: you WRITE a search feature, as a text patch, and prove it. Rules: those of your first message
(your own machine only, no pull request, no engine source committed, new files only in your folder, text only, no
binary files, no `__pycache__`). Folder `forge-combo29/tests_deepseek2_job8/`, report `forge-combo29/REPORT_deepseek2_job8.md`,
commit subject "deepseek2 job 8 report". After pushing, wait for the next file with the sleeping command of your first
message; do not end your run.

### Where this comes from
A search inventory of this engine (report t22 of an earlier study) lists what strong engines have and this one
lacks. One item of that list is yours. Write it from the IDEA described here. Do not copy code, constants or
tables from any other engine (no Stockfish source or any other licensed code): the owner's engine carries no
foreign code. Another helper may get the same feature without seeing your patch; the two patches and the two
results are then compared.

### The feature: a correction history indexed by the MINOR PIECES
The engine corrects its static evaluation with two tables: one indexed by the pawn key, one by the material key
(`correction_history_`, `material_correction_`; read in the function that returns
`raw_eval + correction / CorrectionGrain`, written in `Worker::update_correction`). Feature: a third table of
the same shape, indexed by WHERE THE KNIGHTS AND BISHOPS of both sides stand (Stockfish keeps such a table; its
first form also had the kings in the key and they were later taken out: leave them out).
- The key: the board has no such key. Compute it at the node from the four bitboards (white knights, white
  bishops, black knights, black bishops) with a mixing function of your own (say which, and show that two
  positions that differ in one minor piece get different keys in a sample of 100,000 positions: count the
  collisions in the table index). Measure what the key costs: `bench 13` time with the option off and on, five
  runs each, median.
- READ: added to the correction sum with a weight in percent, as the material table is
  (`MaterialCorrectionWeight`). UPDATE: in `Worker::update_correction`, through the same `apply`. CLEARED where
  the two other tables are cleared.
- The option is a SPIN: `MinorCorrection`, default 0 = off (not one node changes), any other value is the
  weight in percent.
- M1 and M2 are played with weight 100; then M3 and M4 (2,000 games each, seeds 7853 and 7854) with
  weight 50. If the time does not allow all four, play M1, M3, then the second seeds.

### What you deliver
`minor_correction.patch.txt`: ONE unified diff against commit 6b98f217, `forge-combo29/src` and `include` only, as
small as you can make it. A new UCI option `MinorCorrection` (type check, default false), listed in the `uci` answer
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
        C   control: 20,000 against 10,000 nodes (per-engine nodes), 300 games, seed 7850: must be near +200
        M1  `MinorCorrection` on against off, 2,000 games, seed 7851
        M2  the same again with seed 7852, 2,000 games: ALWAYS, whatever M1 says (the best or worst of one
            match shrinks on the second seed; the pooled number is the result)
     For each: fastchess's final numbers, your Elo with the 95 % pair interval, the pair counts, crashes and
     illegal moves (must be 0). A row of exactly 0.00 with pairs [0,0,N,0,0] means the option did not arrive:
     check the engine's input log before reporting it.
 P6. Speed, honestly: `bench 16` nodes per second, option on against off, 10 interleaved pairs, with the spread;
     and the size of the new table in bytes per search thread. Different trees, so this is a rough figure: say so.

### The report
 1. First line in plain words: does `MinorCorrection` gain strength per node (pooled Elo of M1 and M2 with its 95 %
    interval), and is the engine with the option off proven identical.
 2. Step 0. 3. The feature as you built it: which table, how it is indexed, where it is read, where it is
    updated, how it is cleared, with file and line of every hook, and every design choice you made that the
    job text left open (sizes, weights, what you tried and dropped). 4. P1 to P6 with their numbers and files.
 5. One table of all matches. 6. Files of the repository you opened. 7. Stamps of every step.
 8. What you did not do. 9. What you are not sure about. 10. A better way (may be empty). 11. Model.
