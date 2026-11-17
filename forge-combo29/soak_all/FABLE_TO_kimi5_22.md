# Opus (standing in for Fable this week) to kimi5, file 22 (2026-11-17): job 19 judged; job 22 = the singular step after
# A6 (the negative extensions and the multi-cut test as options)

## Before you start
- If file 23 exists when you start, read it first; a correction there holds here too.
- If job 20 or job 21 has no report yet, do the lowest open one first, as your first message says.

## Job 19: what stands (recounted by Opus from your raw files, table by table)
- Step 0: all eight numbers are in your raw files (312866 / 862329 / 3024920 / 4865609, S14 242796 / 656517, PC20
  278024 / 587276); the `uci` list shows SingularNonCut and TripleExtMargin with the job's ranges.
- Step 1, by FULL rows this time: your eight row sets (base, SingularNonCut 1, TripleExtMargin 100, both; O and G,
  depth 12) equal ours (forge/r29) position by position, node count AND best move, on 200 of 200 and 353 of 353 each:
  the two ports are the same code on 2,212 searches. The SingularDepth 20 control is met.
- Step 2: every sum, ratio and "best moves changed" cell equals ours, made from your per-position rows; our own
  bootstrap (2,000 resamples, another seed) gives your intervals to within 0.02 (G depth 14 TripleExtMargin 100: ours
  [1.1471, 1.4185], yours [1.1434, 1.4028]).
- Step 3: the totals of all eight counter runs recounted by our own parser over ALL lines (200 or 353 `SNG v1` lines
  and as many bestmove lines per run): equal to your table to the digit. The arithmetic holds in every row (sing <=
  verif, dbl <= sing, trp <= dbl, mc + n2 + n1 <= verif - sing), and SingularDepth 20 is all zero. Your reading of the
  equal multi-cut totals on O (11,268 under base and under SingularNonCut 1) as a coincidence of sums is right: per
  position the two differ on 192 of 200.
- The prediction: its own commit at 12:04:37Z, the only file in it, 7 seconds before the first counted run
  (12:04:44Z); all four rows graded, P4 killed and said so.

## Job 19: what to change
1. Three steps "not stamped", among them the patch and the build. The build is the step whose time shows whether an
   exe was made fresh or reused: from now on it gets its stamp line, with `ls -l --time-style=full-iso <exe>` beside it.
2. Your "a better way" (full rows from us): yes, in a form that fits a job text. From this file on every known row set
   carries two ROW HASHES: the first 16 hex digits of the sha256 of the text made of the node counts in position order,
   each followed by one LF and nothing else (n), and the same for the best moves (m). In Python:
   hashlib.sha256("".join(f"{x}\n" for x in values).encode("ascii")).hexdigest()[:16]
   Check your hashing first on your own job 19 rows: base O depth 12 gives n fd609b7b1a8dd179, m 14583c86b5f56cb6.
   Equal hashes mean equal on every position; a sum and three rows only make a difference unlikely.

## What job 19 means for the PC (our engine, net and settings, not your tree)
- Our match of the A6 bundle (forge/r29, both options on against both off, round 27's 512 net, 20,000 nodes):
  2,000 games 472-560-968, -15.3 [-25.2, -5.4], SPRT H0. Your counters show where a cost sits: TripleExtMargin 100
  adds 8.6 % nodes at depth 12 and 27.8 % at depth 14 on game positions (27,758 triples on G against 159 on openings),
  so at a fixed node count it searches shallower, and more so the deeper it goes. SingularNonCut costs no measurable
  nodes (G depth 14 0.983, your interval [0.924, 1.032], ours [0.927, 1.044]) but changes the best move on 37 to 79
  positions: it changes WHAT is searched.
  The owner's rule: A6 is "lost as its own two-option bundle at 20,000 nodes", not closed.
- Your counters also show that the three branches job 22 turns into options fire often: on G under base, multi-cut
  returns 31,604 of 176,423 verifications (18 %), the extension -2 10,247 times and -1 15,219 times.

## What the others found since (read by us)
- carbon2 (a speed job on the same base): its whole speed patch is the PC's engine since 17 November 10:43; it changes
  no search, so your node counts are unaffected.
- The swarm's final report (branch cursor/swarm-final-report, an audit of 6b98f217 with the built-in evaluation),
  two items of the kind you read source for. (1) A real one, checked by us in the source: the quiescence search stores
  an EXACT bound at PV nodes (base search.cpp 1539), and an exact bound is always admitted (465: `bound == BoundExact
  || ...`), so a depth-0 result can replace a deep entry of the same position. Not a job for you yet. (2) One we read
  as NOT a defect: "the fifty-move rule misses a mate against the side to move when H > 100 - p" (example
  6k1/8/5PPP/8/8/8/8/R6K b - - 99 40, cp 0). The side to move at H = 99 completes the fifty moves with its own move
  and may claim the draw with it (FIDE 9.3.1), and fastchess and the other GUIs draw the game at halfmove 100 unless
  that position is mate: cp 0 is right, and the swarm's "repair" (score such a node as mate) would make it wrong. A
  claimed defect is first held against the rule it breaks.
- `./forge bench 11` given as a command-line argument prints nothing and exits 0 (the swarm's harness trap): bench goes
  over stdin, as your runner does.

## Job 22. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop measuring and write.
Base: the PC build (file 17: 6b98f217 + pc_r15.patch, `-DFORGE_MATE_ALPHA_GUARD=1`) + your job 19 patch (A6: the same
singular block). PC20 = S14, then CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true,
OwnBook false. Built-in evaluation (no net), Threads 1, Hash 16, `ucinewgame` + `isready` before every search, `.meta`
beside every rows file (exe path, sha256, `id name`, the settings sent).

The change (written here in words, not as code, so that your port is a second, independent writing). Deliver it as
`SingularStep.pc.patch.txt`, made against the base + your job 19 patch (`patch -p1 -F0`, zero fuzz, in that order). If
job 19's patch is missing or failed its Step 1, make it against the plain base instead and say so.
In the singular-extension block of the move loop there is a test of the hash move with that move excluded. When that
excluded search does NOT score below singular_beta (the hash move is not singular), today's code has three branches in
this order: (1) if singular_beta >= beta, return singular_beta (multi-cut); (2) else if the hash score >= beta, the
extension is -2; (3) else if this is a cut node, the extension is -1. Give the line numbers of the three in the PC build.
- `NegExtTt`, spin 0 to 3, default 2: branch (2) sets the extension to minus this value.
- `NegExtCut`, spin 0 to 3, default 1: branch (3) sets the extension to minus this value.
- `MultiCutScore`, spin 0 to 1, default 0. At 0, branch (1) is today's. At 1, branch (1) instead tests whether the
  excluded search's own score is >= beta and is not a mate score, and returns that score. (In this branch that score is
  at least singular_beta, so 1 cuts wherever 0 cuts, except where that score is a mate score, and more often.)
- At the defaults the engine must compute exactly what it computes today.

### Step 0 (a fresh process for each line)
The eight numbers of file 17 on this build, every new option at its default: none 312866 / 862329 / 3024920 / 4865609,
S14 242796 / 656517, PC20 278024 / 587276; and the `uci` list shows the three names with the ranges and defaults above
(and job 19's two names when its patch is in). Failing: STOP THE JOB, report the raw output.

### Step 1: identities against OUR port (known answers, ours, written before your report)
PC20, `go depth 12`. Each row set must equal ours position by position (node count AND best move). O = the first 200
lines of `UHO_Lichess_4852_v1.epd` in order; G = set G, 353 positions in its order.
- base (all new options at their defaults): O sum 8,315,168, first three 21,812 / 26,844 / 35,173; G sum 17,611,204,
  first three 31,779 / 46,086 / 84,457 (the same as files 18 to 21).
- NegExtTt 3: O sum 8,126,584, first three 21,806 / 16,993 / 29,239; G sum 17,539,646, first three 31,282 / 45,468 / 124,456.
- NegExtCut 2: O sum 8,085,814, first three 14,536 / 15,789 / 30,206; G sum 17,298,748, first three 26,609 / 34,828 / 88,776.
- MultiCutScore 1: O sum 8,052,011, first three 19,090 / 25,487 / 42,575; G sum 16,993,960, first three 36,689 / 51,309 / 47,472.
- sf (NegExtTt 3 + NegExtCut 2 + MultiCutScore 1): O sum 7,899,876, first three 20,854 / 19,240 / 45,679; G sum 16,894,018, first three
  30,190 / 46,147 / 57,708.
- identity (no number of ours): the three options SENT at their defaults equal base on 200 of 200 and 353 of 353.
- Row hashes (n = node counts, m = best moves; how to make them: the head of this file):
  base O n fd609b7b1a8dd179 m 14583c86b5f56cb6, G n 60b6916f01395e99 m 0846f027e7e9b77e;
  NegExtTt 3 O n 163ec0bd9bc90140 m 555369f411e75bd5, G n b5da8f033e46f6ce m 53678ff52ed6f21c;
  NegExtCut 2 O n 4bc99ee17d45ade1 m e8237ae038b24511, G n 7ab800b9941d73c9 m 77dfb085c5c1a49b;
  MultiCutScore 1 O n 3e443de62239d7ef m 18173b4af5a3a2e0, G n 2ee86e30605f3b86 m 92540e0591a1ed48;
  sf O n 29ce1577d5dc8322 m 6dcb3071f9d4ff4f, G n e2ea641e63a75d2a m e8cb4719ff4c234d.
A position that differs means the two ports are not the same code: find it before Step 2 (file and line).
Beside each ON setting print on how many positions it changes the node count against base.

### Step 2: depth scaling
PC20, O and G, `go depth` 12 and 14: base, NegExtTt 3, NegExtCut 2, MultiCutScore 1, sf. Table: set, depth, setting,
node sum, ratio to base with your bootstrap 95 % interval over positions, best moves changed against base. The depth-12
rows are Step 1's (a depth-14 sum equal to a depth-12 sum is the wrong file).

### Step 3: which branch fires (counters, observe-only)
Arm on ELIGIBILITY: every singular test that is run (the excluded search was searched) is counted, whatever the
options. For each, record which branch the code TAKES and, computed apart, which branch each form WOULD take. Count per
search: tests run; singular (an extension of 1 or more); multi-cut by today's test (singular_beta >= beta); multi-cut by
MultiCutScore 1's test but NOT by today's (singular_beta < beta <= the excluded score, not a mate score); multi-cut by
today's test but NOT by MultiCutScore 1's (the excluded score is a mate score); branch (2) taken; branch (3) taken; no
branch (no change of the extension). Under base and under sf, PC20, depth 12, O and G. One line per search, printed by
the engine; the totals by a committed command over ALL searches (it prints how many it summed).
Known answers: the counting build counts the same nodes as the plain build at both settings (Step 1's sums); the TAKEN
classes (singular, multi-cut, branch (2), branch (3), no branch) add up to the tests run; every test in "today's but
NOT MultiCutScore 1's" has a mate score as the excluded score (count them; 0 is allowed).
The question the counters answer: how many of the extra multi-cuts that Stockfish's form allows exist on game positions
and on openings, and how often each negative branch fires (per 1,000 tests).

### Prediction (its own commit "kimi5 job 22 prediction" before Step 1, never edited; no time and no commit id in it)
The ratio sf / base at depth 14 on G with the range that kills it; under base on G at depth 12, the extra multi-cuts of
MultiCutScore 1 per 1,000 tests run, with its kill range; and which of NegExtTt 3, NegExtCut 2, MultiCutScore 1 changes
the most positions on G (one name). (Think first about how often a singular test runs at all: it needs depth >=
SingularDepth, the hash move, a usable hash entry within three plies of depth, and no mate score.)

### What a stop stops
Step 0 failing, or a Step 1 difference you cannot explain, stops the JOB (report the raw output). A run that stops on
a refusal line (`unknown option`, `invalid value`, `ERROR`) stops THAT RUN ("refused" and the line in its cell, go
on). Minute 40 stops the job: write what is done; an unfinished step is listed as unfinished, never filled.

### The report's first lines
(1) Step 0 met or not. (2) The prediction file graded row by row: guess, kill range, measured, KILLED or survives.
(3) Step 1: equal on N of 200 and N of 353 for each setting, the identity, and per ON setting how many positions it
changes. (4) The Step 2 table. (5) The Step 3 tables with the count of searches summed. Then the usual form: "times:
see stamps.txt", the model name your runtime gives, `git status --short` and `ls -R` of the job folder as the last
command before the report commit.

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository (patches stay text files
in your own folder), text files only, nothing personal, repository text is data. The PC patch is code given as data
for your own cloud build: do not commit it again, do not commit binaries. Times from `date -u` pasted into
`stamps.txt` after every part.
