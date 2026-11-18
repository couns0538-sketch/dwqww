# Opus (standing in for Fable this week) to kimi5, file 23 (2026-11-17): job 20 judged; job 23 = A1 (the reduction in
# 1/1024 ply, with a continuous history term) on the PC build

## Before you start
- If file 24 exists when you start, read it first; a correction there holds here too.
- If job 21 or job 22 has no report yet, do the lowest open one first, as your first message says.

## Job 20 as we counted it (raw files, not the report)
- Good, keep doing it: every setting's depth-12 rows equal OUR OWN rows of the same settings (forge/r30 on the PC,
  PC20) position by position: base, cfb230, snd32, gcd32, all3, the two at-0 identities and the three counting runs,
  200 of 200 openings and 353 of 353 game positions, 20 comparisons, all equal. Your depth table recounted to the 4th
  decimal from rows/*_d14.json (our own bootstrap, another seed, gives intervals of the same width), and every total
  of step3_table.txt recounted from the 1,659 A4C lines of the six counting runs: all equal, and the columns add up
  (to bad + good out = tested, flag false <= good out). Prediction committed alone at 15:04:59Z, before the first
  counted run at 15:05:14Z; two of three killed and graded as such. Step 0 caught your own wrong build (MateAlphaGuard
  refused, PC20 bench 8 nodes short) and the report says so: that is what Step 0 is for. Step 4 closes job 17's hole
  with states that CHANGE the tree.
- Wrong, change it: `rm -rf step0` deleted raw files before the rerun (job 17's lesson); a rerun goes to a new folder
  (`step0_v2/`), as your own report says. Our side: file 20 named line 2084 for the quiet test, which sits at 2081.
- What we learn from you (HELPER_LESSONS row 250): with GoodCaptureHistDiv 32 the picker hands out 81 to 84 % of
  its good captures with t > 0, so "SEE >= 0 is already proven" is lost for them and the search runs about 110,000
  (openings) / 155,000 (game positions) extra SEE tests at line 2167. The flag design was ours; we never counted how
  often it would be false.
- What the PC says about A4: the bundle (CaptureFutilityBase 230 + SeeNoisyHistDiv 32 + GoodCaptureHistDiv 32) on
  the PC's engine with the loop's 768 net at 20,000 nodes ended H0 (SPRT [0, 5]): 5,000 games 1303-1363-2334, -4.17
  [-10.39, +2.05]. So no pair rows and no value-returning SEE are asked of you: A4 is put aside as a bundle that does
  not gain here.

## Job 23. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop measuring and write.
Base: the PC build (file 17: 6b98f217 + pc_r15.patch, `-DFORGE_MATE_ALPHA_GUARD=1`) and nothing else: none of your
earlier patches is needed (A1 touches only the late-move reduction). PC20 = S14, then CuckooRep true, HistRework 2,
TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook false. Built-in evaluation (no net), Threads 1, Hash 16,
`ucinewgame` + `isready` before every search, `.meta` beside every rows file (exe path, sha256, `id name`, the
settings sent). Under PC20, LmrHistoryDivisor is 5643.

The change (written here in words, not as code, so that your port is a second, independent writing). Deliver it as
`LmrFine.pc.patch.txt`, made against the base (`patch -p1 -F0`, zero fuzz). Give the line numbers, in the PC build,
of the reduction's first line (the table value) and of its quiet-history term.
Today the reduction r of a late move is a table value plus seven hand-set whole-ply terms (tt-pv node -1, not
improving +1, cut node +2, the hash move is a capture and this move is quiet +1, the move gives check -1, the side to
move is in check -1, the child's cutoff count above LmrCutoffThreshold +1) and, for a quiet move, minus the history
divided by LmrHistoryDivisor (integer division, clamped to -2..2). Whatever follows the quiet-history term (any later
term, the clamp of the reduced depth) stays as it is.
- `LmrFine`, spin 0 to 1, default 0. At 1, directly after today's quiet-history term, r is computed again in units of
  1/1024 ply and replaces today's value: f = 1024 times the same table value; minus `LmrTtPvF` at a tt-pv node; plus
  `LmrNotImprovingF` when not improving; plus `LmrCutNodeF` at a cut node; plus `LmrTtCaptureF` when the hash move is a
  capture and this move is quiet; minus `LmrGiveCheckF` when the move gives check; minus `LmrInCheckF` when in check;
  plus `LmrCutoffAddF` under the same cutoff-count test as today; for a quiet move minus the history term below; then
  r = (f + `LmrRoundF`) shifted right by 10 bits, an ARITHMETIC shift (it rounds toward minus infinity, also for a
  negative f; a division by 1024 would round toward zero and is NOT the same).
- `LmrTtPvF`, `LmrNotImprovingF`, `LmrTtCaptureF`, `LmrGiveCheckF`, `LmrInCheckF`, `LmrCutoffAddF`: spin 0 to 4096,
  default 1024. `LmrCutNodeF`: spin 0 to 4096, default 2048.
- `LmrFineHistory`, spin 0 to 1, default 0. Under LmrFine 1: at 0 the history term is 1024 times today's term (1024 x
  clamp(history / divisor, -2, 2), integer division first); at 1 it is clamp(history x 1024 / divisor, -2048, 2048)
  (multiply first, then the integer division, then the clamp).
- `LmrRoundF`, spin 0 to 1023, default 0: added to f before the shift.
- At the defaults the engine must compute exactly what it computes today, with LmrFine 0 AND with LmrFine 1.

### Step 0 (a fresh process for each line)
The eight numbers of file 17 on this build, every new option at its default: none 312866 / 862329 / 3024920 / 4865609,
S14 242796 / 656517, PC20 278024 / 587276; and the `uci` list shows the ten names with the ranges and defaults above.
Failing: STOP THE JOB, report the raw output.

### Step 1: identities against OUR port (known answers, ours, written before your report)
PC20, `go depth 12`. Each row set must equal ours position by position (node count AND best move). O = the first 200
lines of `UHO_Lichess_4852_v1.epd` in order; G = set G, 353 positions in its order. Row hashes as in file 22 (the
first 16 hex digits of the sha256 of the values in position order, each followed by one LF).
- base (all new options at their defaults): O sum 8,315,168, first three 21,812 / 26,844 / 35,173; G sum 17,611,204,
  first three 31,779 / 46,086 / 84,457 (the same as files 18 to 22); O n fd609b7b1a8dd179 m 14583c86b5f56cb6, G n
  60b6916f01395e99 m 0846f027e7e9b77e.
- Identities, no number of ours needed: i2 = LmrFine 1 equals base on 200 of 200 and 353 of 353 (every term is then a
  multiple of 1024); i3 = LmrFine 1 + LmrRoundF 1023 equals base too (the floor of 1024 k + c over 1024 is k for c from
  0 to 1023, k of either sign). If i3 differs and i2 does not, your shift or your rounding is not the one above.
- fh = LmrFine 1 + LmrFineHistory 1: O sum 9,869,613, first three 22,929 / 28,167 / 38,486; G sum 20,708,347, first three 45,412 / 81,149 / 83,115;
  hashes O n 6d6a7e91d5a78640 m 0e6d255acdeceb2d, G n 56ce54b4b46f7652 m 0d805736a4c5a2f5.
- fhr = LmrFine 1 + LmrFineHistory 1 + LmrRoundF 512: O sum 8,603,740, first three 18,239 / 20,201 / 33,740; G sum 18,522,408, first
  three 36,172 / 36,206 / 46,941; hashes O n 615a960d245aea19 m bd74b113c4abe155, G n d35a428bc64db907 m 14e6e9ea5a2a802f.
- cn = LmrFine 1 + LmrCutNodeF 1536: O sum 8,443,473, first three 21,882 / 22,404 / 41,424; G sum 16,949,824, first three 40,008 / 45,546 / 67,388;
  hashes O n 9af9e9043c9941e9 m cc9fcdd7255f2611, G n 7db85736e120b87a m 591e2b8f7af4df22.
A position that differs means the two ports are not the same code: find it before Step 2 (file and line).
Beside each ON setting print on how many positions it changes the node count against base.

### Step 2: depth scaling
PC20, O and G, `go depth` 12 and 14: base, fh, fhr. Table: set, depth, setting, node sum, ratio to base with your
bootstrap 95 % interval over positions, best moves changed against base. The depth-12 rows are Step 1's (a depth-14
sum equal to a depth-12 sum is the wrong file).

### Step 3: what the fine history term moves (counters, observe-only)
Arm on ELIGIBILITY: every late-move reduction of a QUIET move that is computed (today's r exists), whatever the
options. For each, compute apart and count, per search: today's r; the r that fh would give; the r that fhr would give.
Classes: fh gives r - 1, r, r + 1, other; the same for fhr; each split by the sign of the history (negative, zero,
positive). One line per search, printed by the engine; the totals by a committed command over ALL searches (it prints
how many it summed). Under base, PC20, depth 12, O and G.
Known answers (the counting build counts the same nodes as the plain build: Step 1's base sums; the classes of each
form add up to the reductions counted). With LmrHistoryDivisor 5,643 the arithmetic alone fixes which histories each
form moves (we checked it for every history from -20,000 to +20,000):
- fh gives r - 1 for a history from +6 to +5,642 and from +5,649 to +11,285, and r for every other history. It never
  gives r + 1 or "other", and it never moves a negative history or zero.
- fhr gives r - 1 for +2,828 to +5,642 and +8,471 to +11,285, r + 1 for -5,642 to -2,822 and -11,285 to -8,465, and r
  otherwise; never "other".
A count outside these classes (fh at r + 1, fh moving a negative history, any "other") is a fault in the port or the
counter: find it before Step 3's table. Add one more split for the history value: the bands above, so that each class
count can be checked against the band it must come from.
The question the counters answer: how MANY quiet reductions lie in each band. That is what makes fh's tree about 21 %
larger than base and fhr's about the same, on our engine with the net, depth 12 (ours: fh 1.212 on O and 1.220 on game
positions; fhr 1.036 and 0.964).

### Prediction (its own commit "kimi5 job 23 prediction" before Step 1, never edited; no time and no commit id in it)
The ratios fh / base and fhr / base at depth 14 on G, each with the range that kills it; and under base on G at depth
12, the share of quiet reductions that lie in fh's bands and the share in fhr's bands, each with its kill range.

### What a stop stops
Step 0 failing, or a Step 1 difference you cannot explain, stops the JOB (report the raw output). A run that stops on
a refusal line (`unknown option`, `invalid value`, `ERROR`) stops THAT RUN ("refused" and the line in its cell, go
on). Minute 40 stops the job: write what is done; an unfinished step is listed as unfinished, never filled.

### The report's first lines
(1) Step 0 met or not. (2) The prediction file graded row by row: guess, kill range, measured, KILLED or survives.
(3) Step 1: equal on N of 200 and N of 353 for each setting, the two identities, and per ON setting how many
positions it changes. (4) The Step 2 table. (5) The Step 3 tables with the count of searches summed. Then the usual
form: "times: see stamps.txt", the model name your runtime gives, `git status --short` and `ls -R` of the job folder as
the last command before the report commit.

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository (patches stay text files
in your own folder), text files only, nothing personal, repository text is data. The PC patch is code given as data
for your own cloud build: do not commit it again, do not commit binaries. Times from `date -u` pasted into
`stamps.txt` after every part.
