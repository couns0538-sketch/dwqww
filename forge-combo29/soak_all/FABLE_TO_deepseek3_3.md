# Fable to deepseek3, file 3 (2026-11-15): answer to job 2, and job 3

## Your job 2 report

Read in full; the control (+223), the option-delivery check and the bench table per bundle looked at in your
files. What I take from it:
- **No bundle of these switches is stronger than its best single part.** The three small positives together:
  +9.1 (95 % -4.4 to +22.6); the same three on top of the two the PC plays with: +9.5 (-4.0 to +23.1). Two
  independent matches that agree on about +9 is more than either says alone, and still not "shown".
- **The losers stay losers in company:** the two aspiration switches together -22.5, the 50-move damping on
  top of eight others -28.7. By the owner's rule they had their bundle test; they are put aside now, with
  "lost alone AND in a bundle, at 20,000 nodes with the built-in net" written next to them.
- Done well: the option delivery checked with a trace log because the job warned about it, not assumed; every
  cut match marked as cut, with its real game count.

On the owner's PC the same three switches are queued on top of the bundle that went into the engine today
(+10.6 +/- 8.6 at equal time, 2,000 games); your +9 is what I hold that result against.

From the others: an expensive helper measured that a feature's speed cost was half "tree shape" and half real
work, by doing all the work and multiplying its effect by a zero the compiler cannot know (the tree stays the
same): if you ever need the cost of a switch, that is the method. Two helpers are writing the same new search
feature independently right now; you get a different one.

## Job 3. BUDGET: 80 minutes by the clock; at 70 minutes stop and write the report with what you have.

A new kind of job: you WRITE a search feature, as a text patch, and prove it. Rules: those of your first message
(your own machine only, no pull request, no engine source committed, new files only in your folder, text only, no
binary files, no `__pycache__`). Folder `forge-combo29/tests_deepseek3_job3/`, report `forge-combo29/REPORT_deepseek3_job3.md`,
commit subject "deepseek3 job 3 report". After pushing, wait for the next file with the sleeping command of your first
message; do not end your run.

### Where this comes from
A search inventory of this engine (report t22 of an earlier study) lists what strong engines have and this one
lacks. One item of that list is yours. Write it from the IDEA described here. Do not copy code, constants or
tables from any other engine (no Stockfish source or any other licensed code): the owner's engine carries no
foreign code. Another helper may get the same feature without seeing your patch; the two patches and the two
results are then compared.

### The feature: capture history in the late-move reduction
The late-move reduction of a QUIET move is corrected by its history
(`if (quiet) r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);` in `Worker::search`); a CAPTURE gets no
such term, although the engine keeps a capture history (`capture_history_value`, already fetched into the same
`history` variable for captures). Feature: captures with a good capture history are reduced less, with a bad one
more: `r -= clamp(history / D, -2, 2)` for captures too, with its own divisor D.
- The option is a SPIN this time: `LmrCaptureHistory`, default 0 = off (not one node changes), any other value is
  the divisor D. Look at the range of the capture history entries first (the limit used by `apply_history`) and
  choose two divisors from it: one that moves the reduction by a ply for about a tenth of the captures that reach
  the reduction, one for about a third. P1's counters tell you: of the captures that reach the reduction, how
  many get -2, -1, 0, +1, +2 for each divisor.
- M1 and M2 are played with the first divisor; then M3 and M4 (2,000 games each, seeds 7903 and 7904) with
  the second. If the time does not allow all four, play M1, M3, then the second seeds.

### What you deliver
`lmr_capture_history.patch.txt`: ONE unified diff against commit 6b98f217, `forge-combo29/src` and `include` only, as
small as you can make it. A new UCI option `LmrCaptureHistory` (type check, default false), listed in the `uci` answer
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
        C   control: 20,000 against 10,000 nodes (per-engine nodes), 300 games, seed 7900: must be near +200
        M1  `LmrCaptureHistory` on against off, 2,000 games, seed 7901
        M2  the same again with seed 7902, 2,000 games: ALWAYS, whatever M1 says (the best or worst of one
            match shrinks on the second seed; the pooled number is the result)
     For each: fastchess's final numbers, your Elo with the 95 % pair interval, the pair counts, crashes and
     illegal moves (must be 0). A row of exactly 0.00 with pairs [0,0,N,0,0] means the option did not arrive:
     check the engine's input log before reporting it.
 P6. Speed, honestly: `bench 16` nodes per second, option on against off, 10 interleaved pairs, with the spread;
     and the size of the new table in bytes per search thread. Different trees, so this is a rough figure: say so.

### The report
 1. First line in plain words: does `LmrCaptureHistory` gain strength per node (pooled Elo of M1 and M2 with its 95 %
    interval), and is the engine with the option off proven identical.
 2. Step 0. 3. The feature as you built it: which table, how it is indexed, where it is read, where it is
    updated, how it is cleared, with file and line of every hook, and every design choice you made that the
    job text left open (sizes, weights, what you tried and dropped). 4. P1 to P6 with their numbers and files.
 5. One table of all matches. 6. Files of the repository you opened. 7. Stamps of every step.
 8. What you did not do. 9. What you are not sure about. 10. A better way (may be empty). 11. Model.
