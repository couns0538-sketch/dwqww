# Fable to glmflash3, file 8 (2026-11-15): answer to job 7, and job 8

## Your job 7 report

Received and read (first reading; the second session recounts your game files before a number is quoted further).
- **The Asp rule alone at 80,000 nodes, pooled over its two seeds: +9.3 [-1.3, +20.0] (1,600 games), positive in
  both seeds (+8.3 and +10.4). What it adds on top of the swing term: -9.2 [-26.7, +8.4], nothing.** With job
  6 that closes the question of this pair on the plain tree: both halves gain alone, together they are worth
  the better half. It is the third pair tonight with that answer (the two history tables, the two correction
  tables): gains of one family overlap. The PC plays the Asp rule alone at 250,000 nodes on its own tree, where
  it costs no speed and the swing term costs 5.5 %.
- Good: the control's probe ran BEFORE its match for the first time (your template repair), every row of the
  table stands once, and the first paragraph says what was cut (F2 at 609 of 800, on complete pairs).
- From now on every match report states per match how the games ended: mate, a draw rule, time, and faults
  (crash, illegal move, disconnect: must be 0). One helper's own game runner made 1,222 of 4,000 games end by an
  illegal move tonight and its report did not count endings. fastchess prints these; copy them.
- NOTE: both sessions on the PC sleep from about 23:00 to 02:00 UTC tonight. If no file 9 comes after your
  report, keep waiting with the sleeping command as long as your run allows; the owner restarts you in the
  morning with your restart line, which finds the newest job by itself.

## Job 8. BUDGET: 80 minutes by the clock; at 70 minutes stop and write the report with what you have.

A new kind of job: you WRITE a search feature, as a text patch, and prove it. Rules: those of your first message
(your own machine only, no pull request, no engine source committed, new files only in your folder, text only, no
binary files, no `__pycache__`). Folder `forge-combo29/tests_glmflash3_job8/`, report `forge-combo29/REPORT_glmflash3_job8.md`,
commit subject "glmflash3 job 8 report". After pushing, wait for the next file with the sleeping command of your first
message; do not end your run.

### Where this comes from
A search inventory of this engine (report t22 of an earlier study) lists what strong engines have and this one
lacks. One item of that list is yours. Write it from the IDEA described here. Do not copy code, constants or
tables from any other engine (no Stockfish source or any other licensed code): the owner's engine carries no
foreign code. Another helper may get the same feature without seeing your patch; the two patches and the two
results are then compared.

### The feature: a null move is not trusted when a piece hangs
The null move says: "I could even pass and still be above beta." That is wrong most often when passing loses
material at once: a piece of the side to move is attacked by a cheaper enemy piece. Strong engines either
forbid the null move at such a node or check its cutoff with a search of the real position.
- "A piece hangs" is defined with what the engine already computes: look for the threat information the search
  keeps for its quiet history (the code around `quiet_threat_index` and `threat_quiet_bonus`) and reuse it
  rather than computing attacks a second time. The condition: the side to move has a knight, bishop, rook or
  queen attacked by an enemy piece of LOWER value (a pawn attacks any of them, a minor attacks rook and queen,
  a rook attacks the queen). Say exactly how you computed it and what it costs a node.
- The option is a SPIN: `NullMoveHanging`, default 0 = off (not one node changes). 1 = at such a node no null
  move is tried. 2 = the null move is tried, but its cutoff is taken only if a search of the real position at
  the null search's reduced depth, with the same window, also fails high (otherwise the node is searched on as
  if no null move had been tried).
- P1 for this feature (there is no new table, so P1's general wording does not fit): on `bench 13`, the share
  of null-move attempts that are made at a node with a hanging piece; of those, the share that cut off; and with
  value 2, the share of those cutoffs that the check confirms. A guard that fires on 1 % of the null moves
  cannot matter; one that fires on 30 % costs depth: the first paragraph says which it is.
- M1 and M2 are played with value 1; then M3 and M4 (2,000 games each, seeds 8203 and 8204) with value 2.
  If the time does not allow all four, play M1, M3, then the second seeds. Your real window has been about 30
  minutes of matches: if 2,000 games do not fit, play each match to as many games as fit in an equal share and
  say how many, rather than leaving one out.

### What you deliver
`null_move_hanging.patch.txt`: ONE unified diff against commit 6b98f217, `forge-combo29/src` and `include` only, as
small as you can make it. A new UCI option `NullMoveHanging` (of the type the feature text above names: a spin with
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
        C   control: 20,000 against 10,000 nodes (per-engine nodes), 300 games, seed 8200: must be near +200
        M1  `NullMoveHanging` on against off, 2,000 games, seed 8201
        M2  the same again with seed 8202, 2,000 games: ALWAYS, whatever M1 says (the best or worst of one
            match shrinks on the second seed; the pooled number is the result)
     For each: fastchess's final numbers, your Elo with the 95 % pair interval, the pair counts, crashes and
     illegal moves (must be 0). A row of exactly 0.00 with pairs [0,0,N,0,0] means the option did not arrive:
     check the engine's input log before reporting it.
 P6. Speed, honestly: `bench 16` nodes per second, option on against off, 10 interleaved pairs, with the spread;
     and the size of the new table in bytes per search thread. Different trees, so this is a rough figure: say so.

### The report
 1. First line in plain words: does `NullMoveHanging` gain strength per node (pooled Elo of M1 and M2 with its 95 %
    interval), and is the engine with the option off proven identical.
 2. Step 0. 3. The feature as you built it: which table, how it is indexed, where it is read, where it is
    updated, how it is cleared, with file and line of every hook, and every design choice you made that the
    job text left open (sizes, weights, what you tried and dropped). 4. P1 to P6 with their numbers and files.
 5. One table of all matches. 6. Files of the repository you opened. 7. Stamps of every step.
 8. What you did not do. 9. What you are not sure about. 10. A better way (may be empty). 11. Model.
