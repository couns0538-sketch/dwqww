# Fable to deepseek2, file 12 (2026-11-15): answer to job 11, and job 12

## Your job 11 report

Received and read (first reading).
- **ThreadSanitizer: 0 reports in 240 searches with the tablebase port, and the 0 is worth something** because
  the same build reported a planted race inside the engine 30,830 times. Your rule ("a sanitizer's 0 means
  nothing until the SAME binary has produced a non-zero on a planted fault"; your first control had silently
  failed to compile) goes into the lesson file under your name.
- **The gaps patch with its three macros at their defaults compiles to a binary with the same sha256 as the
  tree without it.** That is the strongest "off = unchanged" proof anyone has delivered here; the PC repeats it
  with its own compiler before the patch is placed.
- **Byte flips: 18 of 20 refused, 2 accepted, no crash, no sanitizer line, no illegal move.** On the PC every
  one of the 290 table files is checked against the published sha256 list before the engine may open it, so a
  damaged file does not reach the engine there. Your "checksum" needs one more look before it becomes a repair:
  say in three lines, in the report of the NEXT job under "what I am not sure about", what the 16 bytes that
  the port keeps as `f.tail` are in the table format (with the place in the port's source that reads them, and
  where the format's description says what they mean). If they are not a checksum of the file, comparing them
  proves nothing.
- A2 is closed as "PC only": both table servers refuse your machine. No further job will ask for it.
- What your thread caveat says (the search reads a pointer that `load()` would free; only `stop_search()`
  prevents it; TSan cannot see an order kept by the thread lifecycle) is noted as an open point of the port:
  the PC's review will read exactly that path.
- A warning for every helper from tonight: one helper's own game runner sent each search "position fen
  <current position> moves <all moves again>" and scored the illegal answers as losses (1,222 of 4,000 games);
  its report did not count how its games ended. From now on every match report states per match how many games
  ended by mate, by a draw rule, on time, and by a fault (crash, illegal move, disconnect: must be 0). fastchess
  prints these; copy them.
- NOTE: both sessions on the PC sleep from about 23:00 to 02:00 UTC tonight. If no next file comes after your
  report, keep waiting with the sleeping command as long as your run allows; the owner restarts you in the
  morning with your restart line, which finds the newest job by itself.

## Job 12. BUDGET: 80 minutes by the clock; at 70 minutes stop and write the report with what you have.

A new kind of job: you WRITE a search feature, as a text patch, and prove it. Rules: those of your first message
(your own machine only, no pull request, no engine source committed, new files only in your folder, text only, no
binary files, no `__pycache__`). Folder `forge-combo29/tests_deepseek2_job12/`, report `forge-combo29/REPORT_deepseek2_job12.md`,
commit subject "deepseek2 job 12 report". After pushing, wait for the next file with the sleeping command of your first
message; do not end your run.

### Where this comes from
A search inventory of this engine (report t22 of an earlier study) lists what strong engines have and this one
lacks. One item of that list is yours. Write it from the IDEA described here. Do not copy code, constants or
tables from any other engine (no Stockfish source or any other licensed code): the owner's engine carries no
foreign code. Another helper may get the same feature without seeing your patch; the two patches and the two
results are then compared.

### The feature: the evaluation shrinks as the fifty-move counter rises
A position in which no pawn has moved and nothing was captured for many moves drifts toward the draw that the
fifty-move rule will declare. The static evaluation does not know it: the net sees pieces and squares only.
Strong engines scale the evaluation toward 0 as that counter rises. This repository built it once and never
measured it.
- Find the ONE place through which `Worker::search` and the quiescence search take the static evaluation of a
  node (say which function, and whether you scale before or after the correction history is applied, and why).
  There the evaluation is multiplied by `(D - halfmove) / D`, where `halfmove` is the board's fifty-move counter
  in plies (0 to 100) and D is the option's value. Mate scores and scores from a tablebase are never scaled.
- Scale at the node, when the evaluation is USED. What is stored in the hash table as the static evaluation
  stays the unscaled value, because the same position is reached with other counters. Prove it with one test:
  the same position searched as `... 0 1` and as `... 60 1` (the fifth FEN field) with the hash kept between
  the two searches must show two different static evaluations in the right ratio.
- The option is a SPIN: `Rule50Scale`, default 0 = off (not one node changes); a value D from 120 to 400
  switches it on (D = 200: after 100 plies without progress the evaluation is halved).
- P1 for this feature (there is no new table, so P1's general wording does not fit): where the static
  evaluation is taken, the share of nodes with a counter of 0 to 9, 10 to 19, 20 to 39, 40 to 69 and 70 or
  more, on `bench 13` AND on 200 positions taken from real games of this engine after move 60 (play 20 games
  of the unpatched exe against itself at 20,000 nodes first and take ten positions of each). A term whose
  counter is nearly always small cannot matter at this depth: if that is what you find, say it in the first
  paragraph.
- M1 and M2 are played with D = 300 (mild); then M3 and M4 (2,000 games each, seeds 7953 and 7954) with
  D = 150 (strong). If the time does not allow all four, play M1, M3, then the second seeds. For every match
  also report the share of drawn games and the mean number of moves a game, on each side of the pair (a term
  like this one acts through long games).

### What you deliver
`rule50_scale.patch.txt`: ONE unified diff against commit 6b98f217, `forge-combo29/src` and `include` only, as
small as you can make it. A new UCI option `Rule50Scale` (of the type the feature text above names: a spin with
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
        C   control: 20,000 against 10,000 nodes (per-engine nodes), 300 games, seed 7950: must be near +200
        M1  `Rule50Scale` on against off, 2,000 games, seed 7951
        M2  the same again with seed 7952, 2,000 games: ALWAYS, whatever M1 says (the best or worst of one
            match shrinks on the second seed; the pooled number is the result)
     For each: fastchess's final numbers, your Elo with the 95 % pair interval, the pair counts, crashes and
     illegal moves (must be 0). A row of exactly 0.00 with pairs [0,0,N,0,0] means the option did not arrive:
     check the engine's input log before reporting it.
 P6. Speed, honestly: `bench 16` nodes per second, option on against off, 10 interleaved pairs, with the spread;
     and the size of the new table in bytes per search thread. Different trees, so this is a rough figure: say so.

### The report
 1. First line in plain words: does `Rule50Scale` gain strength per node (pooled Elo of M1 and M2 with its 95 %
    interval), and is the engine with the option off proven identical.
 2. Step 0. 3. The feature as you built it: which table, how it is indexed, where it is read, where it is
    updated, how it is cleared, with file and line of every hook, and every design choice you made that the
    job text left open (sizes, weights, what you tried and dropped). 4. P1 to P6 with their numbers and files.
 5. One table of all matches. 6. Files of the repository you opened. 7. Stamps of every step.
 8. What you did not do. 9. What you are not sure about. 10. A better way (may be empty). 11. Model.
