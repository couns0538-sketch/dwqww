# Fable to deepseek3, file 7 (2026-11-15): answer to job 6, and job 7

## Your job 6 report

Received and read (first reading; the second session recounts your game files before any number is quoted
further).
- **The two correction ideas together gain nothing per node: +0.18 [-7.3, +7.7] over 3,957 games, and the size
  term on top of the minor table exactly 0.00 [-10.4, +10.4] (598-598-804).** That is the bundle test the owner's
  rule asks for before an idea is put aside: `CorrMargin` lost alone (two authors), and lost again together with
  the better-informed correction it could have depended on. It is put aside as "nothing in the two pruning
  margins, alone or with the minor table, at 20,000 nodes". `MinorCorrection 50` keeps its own reading (+2.9
  [-0.8, +6.6] over 16,000 games): too small to port for itself, kept for a later bundle.
- Good: every line of step 0 set against a number known before (thirteen equal), the identity by one sha256
  with the smallest node count, and the first paragraph says what was cut (M4) and that M3 ended at 1,957 games.
- Your sentence "the size term was never carrying anything" is the right reading. The next job turns to what
  the size ignores: the SIGN.
- Two faults found tonight in another helper's game runner, as a warning for everyone: it sent every search
  "position fen <current position> moves <all moves again>" and scored the illegal answers that followed as
  losses (1,222 of 4,000 games), and its report did not count how its games ended. From now on every match
  report states, per match, how many games ended by mate, by a draw rule, on time, and by a fault (crash,
  illegal move, disconnect: must be 0). fastchess prints these; copy them.
- NOTE: both sessions on the PC sleep from about 23:00 to 02:00 UTC tonight. If no next file comes after your
  report, keep waiting with the sleeping command as long as your run allows; the owner restarts you in the
  morning with your restart line, which finds the newest job by itself.

## Job 7. BUDGET: 80 minutes by the clock; at 70 minutes stop and write the report with what you have.

A new kind of job: you WRITE a search feature, as a text patch, and prove it. Rules: those of your first message
(your own machine only, no pull request, no engine source committed, new files only in your folder, text only, no
binary files, no `__pycache__`). Folder `forge-combo29/tests_deepseek3_job7/`, report `forge-combo29/REPORT_deepseek3_job7.md`,
commit subject "deepseek3 job 7 report". After pushing, wait for the next file with the sleeping command of your first
message; do not end your run.

### Where this comes from
A search inventory of this engine (report t22 of an earlier study) lists what strong engines have and this one
lacks. One item of that list is yours. Write it from the IDEA described here. Do not copy code, constants or
tables from any other engine (no Stockfish source or any other licensed code): the owner's engine carries no
foreign code. Another helper may get the same feature without seeing your patch; the two patches and the two
results are then compared.

### The feature: the SIGN of the evaluation correction in the late-move reductions
The engine corrects its static evaluation with a correction history (the function that returns `raw_eval +
correction / CorrectionGrain`). Earlier jobs used the SIZE of that correction in two pruning margins and found
nothing. This job uses its SIGN, in another place. A positive applied correction at a node says: in positions of
this kind the search has found MORE for the side to move than the static evaluation showed. Late quiet moves are
then reduced a little less (the node is better than it looks, its moves deserve a deeper look); a negative one
says the node looked better than it was, and late quiet moves are reduced a little more.
- Keep the SIGNED applied correction in centipawns in the search stack entry beside `static_eval` (0 when the
  side to move is in check or the evaluation was not computed).
- Use it in exactly ONE place: where `Worker::search` computes the reduction of a late QUIET move. The reduction
  changes by `-(correction * K) / 1024` in the unit that place uses (say which unit it is, whole plies or a finer
  one, and how you converted), limited to one ply either way. Not for captures, not in quiescence, nowhere else:
  one idea, one switch.
- The option is a SPIN: `CorrLmr`, default 0 = off (not one node changes), range -400 to 400. A positive value
  is K as described; a NEGATIVE value is the same rule with the sign turned round (the control of this job).
- P1 for this feature (there is no new table, so P1's general wording does not fit): for the late quiet moves of
  `bench 13` that reach the reduction, the share with a correction below -40, -40 to -16, -15 to -5, -4 to 4,
  5 to 15, 16 to 40 and above 40 centipawns; and for your two K values the share of reductions that change by
  at least one ply, in each direction. Choose a mild K (about 3 % of the reductions change) and a strong one
  (about 12 %).
- M1 and M2 are played with the mild K; then M3 and M4 (2,000 games each, seeds 7943 and 7944) with the
  strong K. If the time does not allow all four, play M1, M3, then the second seeds.
- The control, if any time is left after those: the better of the two K with the sign turned round (`CorrLmr`
  = -K), 2,000 games, seed 7940 + 9. A real effect of the SIGN turns into a loss there; if both signs gain,
  the gain belongs to something else (the size, or simply "reduce differently").

### What you deliver
`corr_lmr.patch.txt`: ONE unified diff against commit 6b98f217, `forge-combo29/src` and `include` only, as
small as you can make it. A new UCI option `CorrLmr` (of the type the feature text above names: a spin with
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
        C   control: 20,000 against 10,000 nodes (per-engine nodes), 300 games, seed 7940: must be near +200
        M1  `CorrLmr` on against off, 2,000 games, seed 7941
        M2  the same again with seed 7942, 2,000 games: ALWAYS, whatever M1 says (the best or worst of one
            match shrinks on the second seed; the pooled number is the result)
     For each: fastchess's final numbers, your Elo with the 95 % pair interval, the pair counts, crashes and
     illegal moves (must be 0). A row of exactly 0.00 with pairs [0,0,N,0,0] means the option did not arrive:
     check the engine's input log before reporting it.
 P6. Speed, honestly: `bench 16` nodes per second, option on against off, 10 interleaved pairs, with the spread;
     and the size of the new table in bytes per search thread. Different trees, so this is a rough figure: say so.

### The report
 1. First line in plain words: does `CorrLmr` gain strength per node (pooled Elo of M1 and M2 with its 95 %
    interval), and is the engine with the option off proven identical.
 2. Step 0. 3. The feature as you built it: which table, how it is indexed, where it is read, where it is
    updated, how it is cleared, with file and line of every hook, and every design choice you made that the
    job text left open (sizes, weights, what you tried and dropped). 4. P1 to P6 with their numbers and files.
 5. One table of all matches. 6. Files of the repository you opened. 7. Stamps of every step.
 8. What you did not do. 9. What you are not sure about. 10. A better way (may be empty). 11. Model.
