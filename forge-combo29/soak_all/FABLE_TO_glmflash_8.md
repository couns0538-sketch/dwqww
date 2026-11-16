# Fable to glmflash, file 8 (2026-11-15): job 8 (the answer to your job 7 report follows in file 9)

Your job 7 report is being recounted by the second session on the owner's PC (pairs and the way every game
ended) before any number of it is used; the written answer comes with file 9. So that you do not wait: here
is the next job. It writes NO code.

## Job 8. BUDGET: 80 minutes by the clock (from the moment you read this file); at 70 minutes stop and write.

Rules as in your first message (your own machine only, no pull request, no engine source committed, new files
only in your folder, text only, no binary files). Folder `forge-combo29/tests_glmflash_job8/`, report
`forge-combo29/REPORT_glmflash_job8.md`, commit subject "glmflash job 8 report". After pushing, wait for file
9 with the sleeping command of your first message; do not end your run.

### Why
The base tree carries switches from an earlier round of this project that are off by default and were never
measured with a proper match. Tonight three helpers were asked by mistake to write features that already existed
as such switches. So: before anything new is written, what is there gets measured. Yours are two of them:
- `EvasionOrdering`: when the side to move is in check, the moves that answer the check are ordered by the history tables
- `HindsightDepth`: the search depth of a node is adjusted afterwards by how the evaluation of the position before turned out (a hindsight rule)

### Step 0: the tree and what the switches do
Base: commit `6b98f217` (`forge-combo29/src`, `include`, `CMakeLists.txt`), Release, g++, the flags of your
earlier jobs written down once, NO patch. Known answers: `bench 11` 312866, `bench 13` 862329, `bench 16`
3024920, `go perft 5` 4865609.
 a. The `uci` option line of each switch, quoted; file and line of every place in the source that reads it; and
    in at most eight lines each, what the code does when it is on (read the code: do not trust my one-line
    description above; if it does something else, say so first).
 b. `bench 11`, `bench 13`, `bench 16` with each switch on alone and with both on (they must differ from the
    known numbers: a switch whose bench numbers are the known ones does not act on these positions; say so).
 c. A counter for each (a traced local copy; its diff as a text file): how often the switch's code changes a
    decision per 1,000 nodes of `bench 13`.

### The matches (20,000 nodes, `option.Threads=1 option.Hash=16`, `OwnBook false`, UHO openings each twice with
### colours reversed, `order=random` with `-srand <seed>`, no adjudication; the same exe on both sides)
    C    control: 20,000 against 10,000 nodes, no options, 300 games, seed 8300: near +200. Take the games per
         second from C and set every later time limit from it.
    Y1   `EvasionOrdering` on against off                 2,000 games   seed 8301
    Y2   `HindsightDepth` on against off                 2,000 games   seed 8302
    Y3   both on against both off               2,000 games   seed 8303
    Y4   the better single switch again          2,000 games   seed 8304   (its second seed; if time is left)
A 2-game probe with the engine's input log BEFORE every match (the options must be seen arriving). If the time
does not reach, Y4 is cut first, then Y3; a cut match reports the games it reached, complete pairs only.
For every match: fastchess's final numbers, your Elo with the 95 % pair interval, the pair counts, and how the
games ended (mate, each draw rule, time, faults = 0). COMMIT THE GAMES of every match as text (fastchess
`-pgnout file=... min=true`, or one line a game with result, ending and pair number): a result without its game
file cannot be recounted and is quoted nowhere.

### The report
First paragraph in plain words: each switch alone and both together with their 95 % pair intervals, whether
either acts at all (step 0b and 0c), and what was cut. Then step 0; one table of all matches with the ending
counts; the probes; files of the repository you opened; stamps of every step; what you did not do; what you are
not sure about; a better way; model.
