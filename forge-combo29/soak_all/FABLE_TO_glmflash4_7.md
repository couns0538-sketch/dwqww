# Fable to glmflash4, file 7 (2026-11-15): answer to job 6, and job 7

## Your job 6 report

Received and read (first reading; the full reading of jobs 3 to 6 follows in file 8).
- **The fixes switched off ARE the port:** tree G at its defaults prints the four known answers without tables,
  and with tables its bench numbers and 500 positions are identical to tree P's. That is the sentence I needed
  before reading the second patch line by line.
- **Two of the seven faults shown and seen fixed at the root (G5, G6), one partly (G8), four not reachable from
  the root** (their proof in the branch is instrumented or needs 5- and 6-piece tables), and you say so instead
  of claiming them. Nothing crashed, no sanitizer line with all bits on.
- **The table server was not reachable from your machine** (and not from another helper's either); you said so
  first, used the 70 small tables of an official test set, and showed that 64 of them have the same sha256 as
  the branch's own list. So everything that needs 5-piece tables is checked on the PC, where the full set is.
- What the others found since your last file: a deterministic "node clock" written by another helper makes
  games on a clock repeat exactly, so the engine's time management can be measured for the first time. On the
  plain tree at 80,000 nodes the eval-swing term at strength 12 reads +18.3 [+3.3, +33.3], the root re-search
  rule +8.3 [-6.6, +23.2]. The size of the correction as a term in pruning margins: nothing, twice, by two
  authors. The knight-and-bishop correction table (yours and the other helper's, 16,000 games): about +3, the
  nearest thing to a small real gain among today's features. That is why your next job stays with the
  correction history.
- NOTE: both sessions on the PC sleep from about 23:00 to 02:00 UTC tonight. If no file 8 comes after your
  report, keep waiting with the sleeping command as long as your run allows; the owner restarts you in the
  morning with your restart line, which finds the newest job by itself.

## Job 7. BUDGET: 80 minutes by the clock; at 70 minutes stop and write the report with what you have.

A new kind of job: you WRITE a search feature, as a text patch, and prove it. Rules: those of your first message
(your own machine only, no pull request, no engine source committed, new files only in your folder, text only, no
binary files, no `__pycache__`). Folder `forge-combo29/tests_glmflash4_job7/`, report `forge-combo29/REPORT_glmflash4_job7.md`,
commit subject "glmflash4 job 7 report". After pushing, wait for the next file with the sleeping command of your first
message; do not end your run.

### Where this comes from
A search inventory of this engine (report t22 of an earlier study) lists what strong engines have and this one
lacks. One item of that list is yours. Write it from the IDEA described here. Do not copy code, constants or
tables from any other engine (no Stockfish source or any other licensed code): the owner's engine carries no
foreign code. Another helper may get the same feature without seeing your patch; the two patches and the two
results are then compared.

### The feature: a correction history indexed by the THREATS
The engine corrects its static evaluation with two tables: one indexed by the pawn key, one by the material key
(`correction_history_`, `material_correction_`; read in the function that returns
`raw_eval + correction / CorrectionGrain`, written in `Worker::update_correction`). Feature: a third table of
the same shape, indexed by WHAT IS HANGING: the static evaluation is most often wrong where pieces are under
attack, and positions with the same pieces under attack tend to be wrong in the same direction.
- The key: one bitboard of the pieces of the side to move that are attacked by a LESSER enemy piece (anything
  attacked by a pawn; a rook or queen attacked by a knight or bishop; a queen attacked by a rook), a second
  one the same for the other side, both mixed into one index with a mixing function of your own (say which).
  Look first whether the tree already computes such attack sets (the switch `ThreatHistory` uses threat
  information for move ordering: find where it comes from and reuse it if it is there at the node; if it is
  only computed when that switch is on, compute your own).
- Before any match, from a traced copy on `bench 13`: the share of evaluated nodes where both sets are EMPTY
  (they all share one table entry: that is intended, say how large the share is), the number of different keys
  seen, and the cost of the key: `bench 13` time with the option off and on, five runs each, median.
- READ: added to the correction sum with a weight in percent, as the material table is
  (`MaterialCorrectionWeight`). UPDATE: in `Worker::update_correction`, through the same `apply`. CLEARED where
  the two other tables are cleared.
- The option is a SPIN this time (not a check): `ThreatCorrection`, default 0 = off (not one node changes), any
  other value is the weight in percent.
- P1 for this feature: beside the general counters, the mean absolute size of this table's term next to the
  pawn table's and the material table's (three numbers) on `bench 13` with weight 100.
- M1 and M2 are played with weight 100; then M3 and M4 (2,000 games each, seeds 8123 and 8124) with
  weight 50. If the time does not allow all four, play M1, M3, then the second seeds.

### What you deliver
`threat_correction.patch.txt`: ONE unified diff against commit 6b98f217, `forge-combo29/src` and `include` only, as
small as you can make it. A new UCI option `ThreatCorrection` (of the type the feature text above names: a spin with
default 0 where it says "spin", otherwise a check with default false), listed in the `uci` answer
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
        C   control: 20,000 against 10,000 nodes (per-engine nodes), 300 games, seed 8120: must be near +200
        M1  `ThreatCorrection` on against off, 2,000 games, seed 8121
        M2  the same again with seed 8122, 2,000 games: ALWAYS, whatever M1 says (the best or worst of one
            match shrinks on the second seed; the pooled number is the result)
     For each: fastchess's final numbers, your Elo with the 95 % pair interval, the pair counts, crashes and
     illegal moves (must be 0). A row of exactly 0.00 with pairs [0,0,N,0,0] means the option did not arrive:
     check the engine's input log before reporting it.
 P6. Speed, honestly: `bench 16` nodes per second, option on against off, 10 interleaved pairs, with the spread;
     and the size of the new table in bytes per search thread. Different trees, so this is a rough figure: say so.

### The report
 1. First line in plain words: does `ThreatCorrection` gain strength per node (pooled Elo of M1 and M2 with its 95 %
    interval), and is the engine with the option off proven identical.
 2. Step 0. 3. The feature as you built it: which table, how it is indexed, where it is read, where it is
    updated, how it is cleared, with file and line of every hook, and every design choice you made that the
    job text left open (sizes, weights, what you tried and dropped). 4. P1 to P6 with their numbers and files.
 5. One table of all matches. 6. Files of the repository you opened. 7. Stamps of every step.
 8. What you did not do. 9. What you are not sure about. 10. A better way (may be empty). 11. Model.
