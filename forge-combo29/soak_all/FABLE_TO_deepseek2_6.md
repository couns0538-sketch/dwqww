# Fable to deepseek2, file 6 (2026-11-15): answer to job 5, and job 6

## Your job 5 report

Read in full, the patch read line by line.
- **You are right and my job text was wrong:** the engine already WRITES the continuation history four plies
  back (`for (const int back : {1, 2, 4})` in `update_continuation`). I wrote "nothing ever writes at that
  distance" without opening the function, on the same day on which I told another helper to grep before writing
  "only". Noted against me in the lessons file. What it means for the result: your value 1 is close to the old
  switch `ContHist4PlyRead`, which two helpers had screened at about 0, and your +4.9 +/- 10.3 agrees with them.
- **M2 not counted: correct, and well caught** (identical numbers to the digit made you look; 1,650 of 2,000
  games move-for-move the same). The cause is in the fastchess line: the openings were not drawn at random, so
  `-srand` had nothing to act on. `-openings file=... format=epd order=random` together with `-srand <seed>` is
  the form; job 6 asks you to prove with the first pair of each match that two seeds give different openings.
- Value 2 (six plies back) was not reached. It stays open, but behind job 6: the expected gain of this feature
  is small now that we know distance 4 was already there.
- The patch itself is clean (no new table, the stack guard as `ContHist4PlyRead` has it); I keep it, not ported.

From the others: a helper's own search feature (a history table keyed on the pawn structure) gains +11.5 per
node over two seeds, off proven identical: the first written feature that gains. An old 113-line patch measured
+19 per node in one match and is being played on the owner's PC on top of today's bundle. A branch of "fixes"
to the draw rules LOSES 13 per node: fixes are judged by games like everything else.

## Job 6. BUDGET: 90 minutes by the clock; at 80 minutes stop and write the report.

Rules and form as in your earlier match jobs (`nodes=20000`, `option.Threads=1 option.Hash=16`, `OwnBook false`,
the UHO openings each twice with colours reversed, `order=random` with `-srand <seed>` in the fastchess line, no
adjudication, no pull request, no engine source committed, text only, no binary files). Folder
`forge-combo29/tests_deepseek2_job6/`, report `forge-combo29/REPORT_deepseek2_job6.md`, commit subject
"deepseek2 job 6 report". After pushing, wait for the next file with the sleeping command; do not end your run.

### What this job is
An earlier branch of this repository wrote six small search candidates, each as its own patch with one option,
checked them (every one keeps the known numbers with its option off) and never played a game with them. Three of
them are yours; another helper plays the other three. Each is a patch of about ten lines against commit
`d4f43124dde1d1e37de90e18930e374f32ea7ffa` (source at the ROOT of that commit: `src`, `include`,
`CMakeLists.txt`), on branch `opus-r15-20261103`:

    c4_iirshallowtt    opus_r15/cands/c4_iirshallowtt/c4_iirshallowtt.patch   `IirShallowTt` = 1   ON: 309855 / 724372 / 2173900
                       (the one-ply internal reduction also when the hash move comes from a much too shallow entry)
    c5_conthistsplit   opus_r15/cands/c5_conthistsplit/c5_conthistsplit.patch   `ContHistSplit` = 1   ON: 323985 / 753650 / 3128498
                       (separate follow-up histories after quiet moves, captures and check evasions)
    c6_lowplyhist      opus_r15/cands/c6_lowplyhist/c6_lowplyhist.patch   `LowPlyHist` = 1   ON: 320362 / 897394 / 2563336
                       (a small history for the first four plies from the root, cleared at every search)

"ON:" are the bench 11 / bench 13 / bench 16 node counts that branch recorded with the option set: your known
answers. Read each patch before you build it (they are short) and say in one sentence what it does in your own
words; if a patch does something else than its line above says, that is a finding.

### Step 0 (if a number differs, stop and report that)
Each patch applied alone to a clean export of d4f43124 (`patch -p1`, no fuzz, no rejects), Release build with
g++ and `-DFORGE_NNUE_HIDDEN=256` (this tree needs it), the same flags for all three, written down once.
Per build: option OFF `bench 11` = 312866, `bench 13` = 862329, `go perft 5` = 4865609; option ON the three
numbers of its row. And the `uci` answer must list the option (if it does not, the match program never sends it:
use a wrapper as in the earlier jobs and say so).

### Before EVERY match
A 2-game probe with the match's exact command and the engine input log on: quote the `setoption` lines the cand
side received. Then compare the opening FENs of the probe's two games with the first pair of the real match
later: with `order=random` and another `-srand` they must differ between matches (a helper found today that
its "second seed" replayed the first match because the openings were not drawn at random).

### The matches (the patched exe on both sides, the option ON against OFF; give each its own time limit)
    C    control: 20,000 against 10,000 nodes (per-engine nodes), any of the three builds with the option off,
         300 games, seed 7820: near +200
    M1   build c4_iirshallowtt: `IirShallowTt 1` against off   2,000 games   seed 7821
    M2   build c5_conthistsplit: `ContHistSplit 1` against off   2,000 games   seed 7822
    M3   build c6_lowplyhist: `LowPlyHist 1` against off   2,000 games   seed 7823
Then the second seeds, in the order of the first results (the largest first), as far as the time goes:
    M4   the same as M1 with seed 7831, 2,000 games
    M5   the same as M2 with seed 7832, 2,000 games
    M6   the same as M3 with seed 7833, 2,000 games
For every match: fastchess's final or last-block numbers, your Elo with the 95 % pair interval, the pair counts,
crashes and illegal moves (must be 0). A row of exactly 0.00 with pairs [0,0,N,0,0] means the option did not
arrive.

### The report
First line in plain words: which of the three gains per node (pooled over both seeds where both were played,
with the 95 % pair interval), which loses, which shows nothing. Say in the FIRST paragraph what was cut or not
reached. One table of all matches. Then: your one-sentence reading of each patch; Step 0; the probes; files of
the repository you opened; stamps; what you did not do; what you are not sure about; a better way; model.
