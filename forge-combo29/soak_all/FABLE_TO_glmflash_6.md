# Fable to glmflash, file 6 (2026-11-15): answer to job 5, and job 6

## Your job 5 report

Received and read (first reading; the full reading follows in file 7, this file comes quickly because your
waiting time is short).
- **Step 0 failed for a reason that was mine, not yours:** the two port patches rewrite the same parts of
  `src/search.cpp`, and my job text gave you no combined patch. You did the right thing: both orders tried, the
  reject files committed, no hand merge. Your "better way" (list the files two patches touch BEFORE ordering a
  double tree) goes into our lessons with your name on it.
- **What you measured instead is useful.** The Asp pair, two seeds pooled: +15.3 [5.5, 25.2]. The EvalSwing pair,
  two seeds pooled: +8.4 [-1.6, 18.4]. The four together, two seeds: +18.8 [11.3, 26.4]. The complete-pairs
  correction is right: keep it in every later report.
- **Your three questions.** (1) No third Asp seed: the decision is taken on the PC, on the four options together,
  at EQUAL TIME on top of today's bundle (2,000 games, running now). (2) EvalSwing stays inside the four for that
  decision; on the PC, alone, on top of today's bundle at 2,000 nodes it read +20.1 +/- 7.1, so your two seeds
  (+19.2 and +1.1) are not the whole story. (3) Yes: the PC's own measurement replaces your Part A. No re-port.
- What the others found since your last file: a pawn-structure history written by two helpers gave +11.5, +13.4
  and +14.4 per node on the plain tree and only +1.7 +/- 7.2 on top of today's bundle at 2,000 nodes. A feature
  can be real on the plain tree and vanish on top of the others: that is why the counters of P1 matter in the
  job below (they show WHERE the feature acts), and why a result is reported with the tree it was measured on.
- This job is a new kind for you: you WRITE a small search feature as a text patch and measure it. Its idea
  comes from a study the owner gave us today.

## Job 6. BUDGET: 80 minutes by the clock; at 70 minutes stop and write the report with what you have.

A new kind of job: you WRITE a search feature, as a text patch, and prove it. Rules: those of your first message
(your own machine only, no pull request, no engine source committed, new files only in your folder, text only, no
binary files, no `__pycache__`). Folder `forge-combo29/tests_glmflash_job6/`, report `forge-combo29/REPORT_glmflash_job6.md`,
commit subject "glmflash job 6 report". After pushing, wait for the next file with the sleeping command of your first
message; do not end your run.

### Where this comes from
A search inventory of this engine (report t22 of an earlier study) lists what strong engines have and this one
lacks. One item of that list is yours. Write it from the IDEA described here. Do not copy code, constants or
tables from any other engine (no Stockfish source or any other licensed code): the owner's engine carries no
foreign code. Another helper may get the same feature without seeing your patch; the two patches and the two
results are then compared.

### The feature: the SIZE of the evaluation correction widens pruning margins
The engine corrects its static evaluation with a correction history (two tables, one indexed by the pawn key and
one by the material key; the function that returns `raw_eval + correction / CorrectionGrain`). A LARGE correction,
in either direction, says: in positions of this kind the static evaluation has been wrong before. Pruning that
trusts the static evaluation should then ask for a wider margin. (Stockfish has this in its futility margin; it
was never measured on this engine.)
- Keep the size of the applied correction in centipawns, `abs(correction / CorrectionGrain)`, in the search stack
  entry beside `static_eval` (0 when the side to move is in check or the evaluation was not computed).
- Use it in exactly two places of `Worker::search`: the reverse futility test (the line with
  `tune::RfpMargin * depth`: the margin grows by `size * K / 64`) and the futility pruning of quiet moves in the
  move loop (the test with `tune::FutilityDepth`, `FutilityBase` and `FutilityMultiplier`: the same term is
  added to its margin). Nowhere else in this job: one idea, one switch.
- The option is a SPIN this time (not a check): `CorrMargin`, default 0 = off (not one node changes), any other
  value is K.
- P1 for this feature (there is no new table, so P1's general wording does not fit): for the nodes of `bench 13`
  where the reverse futility test is reached, the share with size 0, 1 to 4, 5 to 15, 16 to 40 and above 40
  centipawns, and how many reverse futility cutoffs and quiet futility skips each of your two K values removes.
  Choose a mild K (removes about 2 % of the reverse futility cutoffs) and a strong one (about 8 %).
- M1 and M2 are played with the mild K; then M3 and M4 (2,000 games each, seeds 7163 and 7164) with the
  strong K. If the time does not allow all four, play M1, M3, then the second seeds.

### What you deliver
`corr_margin.patch.txt`: ONE unified diff against commit 6b98f217, `forge-combo29/src` and `include` only, as
small as you can make it. A new UCI option `CorrMargin` (type check, default false), listed in the `uci` answer
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
        C   control: 20,000 against 10,000 nodes (per-engine nodes), 300 games, seed 7160: must be near +200
        M1  `CorrMargin` on against off, 2,000 games, seed 7161
        M2  the same again with seed 7162, 2,000 games: ALWAYS, whatever M1 says (the best or worst of one
            match shrinks on the second seed; the pooled number is the result)
     For each: fastchess's final numbers, your Elo with the 95 % pair interval, the pair counts, crashes and
     illegal moves (must be 0). A row of exactly 0.00 with pairs [0,0,N,0,0] means the option did not arrive:
     check the engine's input log before reporting it.
 P6. Speed, honestly: `bench 16` nodes per second, option on against off, 10 interleaved pairs, with the spread;
     and the size of the new table in bytes per search thread. Different trees, so this is a rough figure: say so.

### The report
 1. First line in plain words: does `CorrMargin` gain strength per node (pooled Elo of M1 and M2 with its 95 %
    interval), and is the engine with the option off proven identical.
 2. Step 0. 3. The feature as you built it: which table, how it is indexed, where it is read, where it is
    updated, how it is cleared, with file and line of every hook, and every design choice you made that the
    job text left open (sizes, weights, what you tried and dropped). 4. P1 to P6 with their numbers and files.
 5. One table of all matches. 6. Files of the repository you opened. 7. Stamps of every step.
 8. What you did not do. 9. What you are not sure about. 10. A better way (may be empty). 11. Model.
