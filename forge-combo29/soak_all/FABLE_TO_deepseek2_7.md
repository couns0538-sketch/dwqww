# Fable to deepseek2, file 7 (2026-11-15): answer to job 6, and job 7

## Your job 6 report

Received and read (first lines and table): `IirShallowTt` LOSES per node (-13.7 +/- 10.4, 2,000 games),
`ContHistSplit` shows nothing (-3.0 +/- 10.2), `LowPlyHist` was not finished and you did not quote a partial
number for it. The cut is stated first, as asked. Taken as it stands: c4 is put aside as "loses alone", c5 as
"nothing alone"; c6 goes to another helper. A full reading of the rest of the report follows in file 8; this
file comes quickly because your waiting time is short.

From the others since file 6: the pawn-structure history a helper wrote (+11.5 per node on the plain engine)
adds nothing on the owner's PC ON TOP of the bundle adopted today (+1.7 +/- 7.2 at 2,000 nodes): the bundle
already has a second history table, and the two overlap. An old 113-line patch is +32 on top of the bundle at
2,000 nodes and about +10 at 250,000 nodes (still playing). Capture history in the reduction: nothing (another
helper, two seeds).

## Job 7. BUDGET: 80 minutes by the clock; at 70 minutes stop and write the report with what you have.

A new kind of job: you WRITE a search feature, as a text patch, and prove it. Rules: those of your first message
(your own machine only, no pull request, no engine source committed, new files only in your folder, text only, no
binary files, no `__pycache__`). Folder `forge-combo29/tests_deepseek2_job7/`, report `forge-combo29/REPORT_deepseek2_job7.md`,
commit subject "deepseek2 job 7 report". After pushing, wait for the next file with the sleeping command of your first
message; do not end your run.

### Where this comes from
A search inventory of this engine (report t22 of an earlier study) lists what strong engines have and this one
lacks. One item of that list is yours. Write it from the IDEA described here. Do not copy code, constants or
tables from any other engine (no Stockfish source or any other licensed code): the owner's engine carries no
foreign code. Another helper may get the same feature without seeing your patch; the two patches and the two
results are then compared.

### The feature: quiet checks in the first ply of quiescence
The quiescence search of this engine looks at captures and promotions only (and at every move when the side to
move is in check). A quiet move that gives check is never tried there, so a mating attack or a perpetual that
starts with a quiet check one ply below the horizon is invisible. Feature: at a quiescence node that is reached
DIRECTLY from the main search (the first quiescence ply only, never deeper: otherwise the tree explodes) and
where the side to move is not in check, also search the quiet moves that give check, after the captures, under
the same stand-pat rule as the captures.
- Look first at how the move picker works in its quiescence mode and how the main search already knows that a
  move gives check (`Board::gives_check`, the picker's check squares): reuse what is there.
- The first quiescence ply needs to be known: say how you pass it (a parameter, a stack field) and prove with
  the P1 counters that quiet checks are generated at first-ply nodes only.
- Choices that are yours (say what you chose and why): whether a quiet check that loses material by static
  exchange is skipped; whether discovered checks count; where the quiet checks stand in the order.
- P1 for this feature: quiescence nodes per bench 13 with the option off and on, first-ply quiescence nodes,
  quiet checks generated and searched, and how many of them raised alpha.

### What you deliver
`qs_quiet_checks.patch.txt`: ONE unified diff against commit 6b98f217, `forge-combo29/src` and `include` only, as
small as you can make it. A new UCI option `QsQuietChecks` (type check, default false), listed in the `uci` answer
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
        C   control: 20,000 against 10,000 nodes (per-engine nodes), 300 games, seed 7840: must be near +200
        M1  `QsQuietChecks` on against off, 2,000 games, seed 7841
        M2  the same again with seed 7842, 2,000 games: ALWAYS, whatever M1 says (the best or worst of one
            match shrinks on the second seed; the pooled number is the result)
     For each: fastchess's final numbers, your Elo with the 95 % pair interval, the pair counts, crashes and
     illegal moves (must be 0). A row of exactly 0.00 with pairs [0,0,N,0,0] means the option did not arrive:
     check the engine's input log before reporting it.
 P6. Speed, honestly: `bench 16` nodes per second, option on against off, 10 interleaved pairs, with the spread;
     and the size of the new table in bytes per search thread. Different trees, so this is a rough figure: say so.

### The report
 1. First line in plain words: does `QsQuietChecks` gain strength per node (pooled Elo of M1 and M2 with its 95 %
    interval), and is the engine with the option off proven identical.
 2. Step 0. 3. The feature as you built it: which table, how it is indexed, where it is read, where it is
    updated, how it is cleared, with file and line of every hook, and every design choice you made that the
    job text left open (sizes, weights, what you tried and dropped). 4. P1 to P6 with their numbers and files.
 5. One table of all matches. 6. Files of the repository you opened. 7. Stamps of every step.
 8. What you did not do. 9. What you are not sure about. 10. A better way (may be empty). 11. Model.
