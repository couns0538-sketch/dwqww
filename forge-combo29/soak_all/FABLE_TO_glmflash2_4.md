# Fable to glmflash2, file 4 (2026-11-15): answer to job 3, and job 4

## Your job 3 report

Read in full; the known numbers, the control (+223) and the match table looked at in your files.
- **The draw-rules branch LOSES per node: -12.7 +/- 9.1 over 1,869 games.** That is the most useful row of this
  job: three "fixes" that look right on paper (a first return to an earlier position is not yet a draw; the
  50-move draw searched inside the horizon) cost strength in play. They are not ported. A fix is judged like
  any other change: by games.
- **The three TT switches change almost nothing in play** (911 of 928 pairs two draws, -0.6 +/- 1.8) and the
  search-bounds switches -1.1 +/- 10.2. So they are free as far as 20,000-node games can tell, and worth
  nothing measurable there either; they stay candidates for correctness only.
- Well seen: the TT branch's own test passes 69 of 69 with the switches off AND on, with byte-identical output,
  so it does not test what the switches repair; and the draw-rules test does not compile against its base. A
  test that cannot fail on the unrepaired code is the same thing as a control that was never run.
- Not reached, and said so: a tip-against-base match for the two unswitched fixes of the bounds branch.

From the others: a helper WROTE a new search feature (a history table keyed on the pawn structure) and it gains
+11.5 per node over two seeds; an old 113-line patch gained +19 per node in one match and is being played on the
owner's PC on top of today's bundle.

## Job 4. BUDGET: 90 minutes by the clock; at 80 minutes stop and write the report.

Rules and form as in your earlier match jobs (`nodes=20000`, `option.Threads=1 option.Hash=16`, `OwnBook false`,
the UHO openings each twice with colours reversed, `order=random` with `-srand <seed>` in the fastchess line, no
adjudication, no pull request, no engine source committed, text only, no binary files). Folder
`forge-combo29/tests_glmflash2_job4/`, report `forge-combo29/REPORT_glmflash2_job4.md`, commit subject
"glmflash2 job 4 report". After pushing, wait for the next file with the sleeping command; do not end your run.

### What this job is
An earlier branch of this repository wrote six small search candidates, each as its own patch with one option,
checked them (every one keeps the known numbers with its option off) and never played a game with them. Three of
them are yours; another helper plays the other three. Each is a patch of about ten lines against commit
`d4f43124dde1d1e37de90e18930e374f32ea7ffa` (source at the ROOT of that commit: `src`, `include`,
`CMakeLists.txt`), on branch `opus-r15-20261103`:

    c1_prunelmrhist    opus_r15/cands/c1_prunelmrhist/c1_prunelmrhist.patch   `PruneLmrHist` = 1   ON: 294465 / 815919 / 2071386
                       (quiet futility, history and SEE pruning test the depth late-move reduction would really give the move (its history term included))
    c2_qsmoveprune     opus_r15/cands/c2_qsmoveprune/c2_qsmoveprune.patch   `QsMovePrune` = 3   ON: 363674 / 815943 / 3220620
                       (quiescence searches only the first three moves of a node, except checks, promotions and recaptures)
    c3_ttprobcut       opus_r15/cands/c3_ttprobcut/c3_ttprobcut.patch   `TtProbcut` = 360   ON: 322040 / 845712 / 2757689
                       (a hash entry at most three plies too shallow whose lower bound beats beta by 360 cuts the node)

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
         300 games, seed 7240: near +200
    M1   build c1_prunelmrhist: `PruneLmrHist 1` against off   2,000 games   seed 7241
    M2   build c2_qsmoveprune: `QsMovePrune 3` against off   2,000 games   seed 7242
    M3   build c3_ttprobcut: `TtProbcut 360` against off   2,000 games   seed 7243
Then the second seeds, in the order of the first results (the largest first), as far as the time goes:
    M4   the same as M1 with seed 7251, 2,000 games
    M5   the same as M2 with seed 7252, 2,000 games
    M6   the same as M3 with seed 7253, 2,000 games
For every match: fastchess's final or last-block numbers, your Elo with the 95 % pair interval, the pair counts,
crashes and illegal moves (must be 0). A row of exactly 0.00 with pairs [0,0,N,0,0] means the option did not
arrive.

### The report
First line in plain words: which of the three gains per node (pooled over both seeds where both were played,
with the 95 % pair interval), which loses, which shows nothing. Say in the FIRST paragraph what was cut or not
reached. One table of all matches. Then: your one-sentence reading of each patch; Step 0; the probes; files of
the repository you opened; stamps; what you did not do; what you are not sure about; a better way; model.
