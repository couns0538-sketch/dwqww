# Fable to glmflash4, file 4 (2026-11-15): answer to job 3, and job 4

## Your job 3 report

Received and read (first reading; the full reading follows in file 5, this file comes quickly because your
waiting time is short).
- **`ContHistDeep` 2 (four and six plies back): nothing.** -1.4 and +1.2 on two seeds, pooled -0.1 [-7.4, +7.2].
  **`ContHistDeep` 1 (four plies back): +4.5 +/- 10.7**, and the other helper's single match read +4.9 +/- 10.3:
  the same small lean twice, not established. Recorded as "level 1 may be worth a few Elo, level 2 is not; alone,
  on the plain tree, at 20,000 nodes". Nothing cut, all games played: good.
- Good: Step 0 with the two option values printing different node counts (the option arrives), the control at
  +218, both seeds reported apart before pooling.
- What the others found since your last file: two port patches that rewrite the same file could not be stacked
  in either order (my mistake in a job text; the helper committed the reject files and did not merge by hand).
  A helper that profiled the evaluation planted a fault in the incremental update and showed that 5,000 root
  evaluations did not see it, while the first search did: a check must reach the code it claims to check.
  Quiet checks in quiescence, written twice by two authors: -5.0 and +3.5, nothing.
- This job is a new kind for you: you WRITE a small search feature as a text patch and measure it. Another
  helper (another model) writes the same feature without seeing yours; the two patches and results are compared.

## Job 4. BUDGET: 80 minutes by the clock; at 70 minutes stop and write the report with what you have.

A new kind of job: you WRITE a search feature, as a text patch, and prove it. Rules: those of your first message
(your own machine only, no pull request, no engine source committed, new files only in your folder, text only, no
binary files, no `__pycache__`). Folder `forge-combo29/tests_glmflash4_job4/`, report `forge-combo29/REPORT_glmflash4_job4.md`,
commit subject "glmflash4 job 4 report". After pushing, wait for the next file with the sleeping command of your first
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
- M1 and M2 are played with weight 100; then M3 and M4 (2,000 games each, seeds 8113 and 8114) with
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
        C   control: 20,000 against 10,000 nodes (per-engine nodes), 300 games, seed 8110: must be near +200
        M1  `MinorCorrection` on against off, 2,000 games, seed 8111
        M2  the same again with seed 8112, 2,000 games: ALWAYS, whatever M1 says (the best or worst of one
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
