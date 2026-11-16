# glmflash2 job 8 report (2026-11-16)

## 1. First paragraph in plain words

**`AspArmLate` loses strength per node: -20.00 +/- 10.65** (Y1, 1,949/2,000 games; fastchess
-22.42 +/- 11.15; interval [-30.7, -9.3], excludes 0). **`AspCappedReopen` loses a little, shown
only when pooled over its two seeds: -8.71 +/- 11.33** (Y2, 1,756/2,000) **and -11.30 +/- 10.54**
(Y4, the full 2,000) - **pooled 3,756 games: -10.09 +/- 7.71, interval [-17.8, -2.4], excludes 0**;
job 1's single-seed -0.69 +/- 12.06 for the same switch is thereby revised: two seeds say the loss
is real but small. **Both together: -24.19 +/- 10.61** (Y3, the full 2,000 games; fastchess
identical) - worse than AspArmLate alone. Whether either acts at all: **both act** - Step 0b changed
every bench number, and the counters (Step 0c) say `AspCappedReopen` changes a root-window decision
~169 times per 1,000 nodes alone (~63 with both on) and `AspArmLate` ~22 per 1,000 nodes. **What
was cut: nothing was cut to nothing** - Y3 and Y4 both completed all 2,000 games; only Y1 (1,949)
and Y2 (1,756) were shortened by their caps; every planned match has a full row with its games
committed.

## 2. Step 0: the tree and what the switches do

Base: commit 6b98f217 (forge-combo29), Release, g++ 13.3.0, default FORGE_MARCH=x86-64-v4 (VM has
AVX-512+BMI2; the same recipe as jobs 1-3, written once here). NO patch.

| check | expected | printed | file |
|-------|----------|---------|------|
| bench 11 | 312866 | 312866 | step0/bench11_off.txt |
| bench 13 | 862329 | 862329 | step0/bench13_off.txt |
| bench 16 | 3024920 | 3024920 | step0/bench16_off.txt |
| go perft 5 | 4865609 | 4865609 | step0/perft5_off.txt |

The two `uci` lines (both `type check default false`, quoted from step0/uci_asp8_lines.txt):

    option name AspCappedReopen type check default false
    option name AspArmLate type check default false

### 0a. Every place the source reads each switch, and what the code does when ON

`AspArmLate` - src/search.cpp:104 (definition); read at src/search.cpp:2405 and :2438:
- :2438 `if (!aborted_) reopen_full_window = tune::AspArmLate && failed_window;` - after every
  FINISHED root iteration, the arm is set exactly when that iteration failed high or low at least
  once (`failed_window`).
- :2405 `const bool narrow = depth >= 4 && !(tune::AspArmLate && reopen_full_window);` - the NEXT
  iteration skips the narrow window (full -inf/+inf) when the arm is set; one iteration only, then
  the arm is recomputed (:2438).
In at most eight lines: when ON, any finished root iteration that had at least one fail-high or
fail-low makes the following iteration search with a FULL window instead of the usual
score +/- delta window; the arm lasts one iteration. Fable's one-line description is exact; the
code does nothing else. (Note the depth >= 4 guard exists in both paths, so the arm can only matter
from depth 4 up.)

`AspCappedReopen` - src/search.cpp:103 (definition); read at src/search.cpp:2419 and :2427, with
helpers capped_fail_low/capped_fail_high at :2131/:2136 (margin AspReopenMargin = 13, decisive line
AspDecisiveScore = 640):
- fail low (:2417-2425): with the switch, `alpha = capped_fail_low(iteration_score)` = score - 13
  (or -inf if the score is a mate score or <= -640); WITHOUT it, `alpha = score - delta` where delta
  has been growing by delta/2+4 every reopen.
- fail high (:2426-2432): `beta = capped_fail_high(iteration_score)` = score + 13 (or +inf for mate
  or >= 640); WITHOUT it, `beta = score + delta` with the same growing delta.
In at most eight lines: when ON, every reopened aspiration window is reopened by a FIXED 13 cp past
the returned score instead of by the growing delta - the reopened searches are wider in cp than the
initial delta only after delta has grown past 13, so the switch mostly REOPENS LESS far than the
lock code would. **And one thing Fable's description does not say, said first as the job asks: the
two `break` lines behind the switch (:2421, :2429 - "if the score is still beyond the capped window,
abandon the iteration") can never fire** - the capped alpha is always score-13 (or -inf) and the
condition compares the score against its own value shifted by 13 or to -inf, so `iteration_score <=
alpha` is false in every case; they are dead code on the reachable paths. The switch only ever
changes the reopen width; it never abandons an iteration.

### 0b. Benches with the switches on (each alone, and both)

| config | bench 11 | bench 13 | bench 16 |
|--------|----------|----------|----------|
| off (known) | 312866 | 862329 | 3024920 |
| AspArmLate alone | 309644 | 870398 | 2721397 |
| AspCappedReopen alone | 347390 | 850997 | 3319961 |
| both on | 318634 | 870846 | 2892663 |

All differ from the known numbers - both switches act on these positions. (AspCappedReopen's
bench-11 number 347390 is bit-identical to job 1's Step-1 measurement of the same switch - the
build reproduces.) Files: step0/bench1*.txt (names carry the config; the "true armlate"/"true
capped" names came from a quoting slip in my loop, contents are correct).

### 0c. The counters (traced local copy; diff committed as text)

Traced copy at /home/ubuntu/j8work/trace (source only, outside the git work tree); the exact diff
pristine-vs-traced is committed as asp8_counters_applied.diff. It adds, under `#ifdef
FORGE_ASP_STATS`: root iterations at depth >= 4; `armlate_changed` = arm kept the window full where
the lock code would have narrowed (depth >= 4); `capped_events` = capped reopen sites reached;
`capped_changed` = capped reopen whose alpha/beta differs from the lock code's choice (compared
against the uncapped `score -/+ delta` with the SAME pre-increment delta). Printed to stderr at
exit. The traced build's bench numbers equal the untraced build's (870398 / 850997), so the
counters do not change the search.

| config (bench 13) | root_iterations | armlate_changed | capped_events | capped_changed | nodes |
|--------------------|-----------------|-----------------|---------------|----------------|-------|
| AspArmLate on      | 80 | 19 | 0 | 0 | 870398 |
| AspCappedReopen on | 80 | 0 | 145 | 144 | 850997 |
| both on            | 80 | 18 | 55 | 55 | 870846 |
| off                | 80 | 0 | 0 | 0 | 862329 |

Per 1,000 nodes (count / nodes x 1000): **AspArmLate changes ~21.8 decisions/1,000 nodes alone
(~20.7 with both)**; **AspCappedReopen ~169.2/1,000 alone (~63.2 with both)** - with the arm feeding
it full windows, far fewer capped reopens happen. One capped event in 145 matched the lock's choice
(their width coincided). Files: counters/*.txt (raw stderr + bench lines).

## 3. All matches (20,000 nodes; same exe both sides; no adjudication)

Machine: 4 cores, concurrency 4, fastchess v1.8.3-alpha, UHO book. Crashes/illegal/disconnects/time
faults: 0 in every match (grep over each full output; per-match ending tallies committed). The
games of every match are committed as text: matches/<name>_lines.txt (one line per game:
round|white|black|result|opening FEN - recountable) and <name>_endings.txt (fastchess's own
"Finished game" lines in completion order, each with its ending in braces) plus
<name>_ending_tally.txt (counts by ending type).

| #  | match | seed | games | W-L-D | Ptnml(0-2) | fc Elo +/- err | my Elo +/- 95% | crashes |
|----|-------|------|-------|-------|------------|----------------|----------------|---------|
| C  | 20k vs 10k, no options | 8310 | 300 | 181-22-97 | [1,5,30,61,53] | +189.31 +/- 30.42 | +189.31 +/- 33.60 | 0 |
| Y1 | AspArmLate on vs off | 8311 | 1949/2000 | 507-619-823 | [70,260,407,186,51] | -22.42 +/- 11.15 (last interim) | -20.00 +/- 10.65 | 0 |
| Y2 | AspCappedReopen on vs off | 8312 | 1756/2000 | 473-517-766 | [59,226,338,210,45] | -8.90 +/- 11.83 (last interim) | -8.71 +/- 11.33 | 0 |
| Y3 | both on vs both off | 8313 | 2000 | 496-635-869 | [80,278,382,221,39] | -24.19 +/- 10.58 | -24.19 +/- 10.61 | 0 |
| Y4 | AspCappedReopen (better single) again | 8314 | 2000 | 527-592-881 | [66,254,418,203,59] | -11.30 +/- 10.52 | -11.30 +/- 10.54 | 0 |

Pooled AspCappedReopen vs none (Y2 + Y4): 3,756 games, 1,000-1,109-1,647, Ptnml sum
[125,480,756,413,104], **-10.09 +/- 7.71**.

## 4. The probes

Before every match: 2-game probe with the match's exact command, engine input log on. Committed:
<name>_probe_setoption_lines.txt (the cand-side setoption lines fastchess sent - Y3's shows both
switches' lines) and <name>_probe_openings.txt. Probe FENs == match round-1 FENs: verified by
string compare for ALL five matches (control, Y1, Y2, Y3, Y4: MATCH). First-pair openings across
matches distinct (control rnbqkbnr..., Y1 rnbqkbnr/pp5p..., Y2 r1b1kbnr..., Y3/Y4 their own - all
differ); the second-seed-replays-first-match fault did not happen.

## 5. Files of the repository I opened

- The job file (git show on the handoff branch).
- forge-combo29/src/search.cpp: lines 2131-2137 (capped helpers), 2369-2440 (the aspiration loop),
  103-104 (definitions) - read, quoted above.
- forge-combo29/include/forge/search.hpp: the two extern declarations (grep-located).
- The uci.cpp option registration (grep-located via the option names).
No other repository file opened.

## 6. Start and end of each step (recorded stamps, UTC)

- 23:28:1xZ  job 8 file read (found 23:28:17Z).
- 23:28:2xZ -> 23:28:40Z  build + Step 0 benches (files stamped 23:28:40Z; all known numbers match).
- 23:29-23:31Z  code reading (0a); trace copy edited + built (asp8_counters_applied.diff, 71 lines).
- 23:29:41Z  first counter batch - empty files: my batch used the wrong shell variable for the
  binary path ($s unset instead of $t); redone correctly at 23:29:4xZ (results above; the empty
  files were overwritten by the real runs).
- 23:29:59Z  runner8a launched (probe C + control, probe Y1 + Y1, probe Y2 + Y2).
- 23:31:2xZ -> 23:33:0xZ  control 8310 (300 games, +189.31; rate 300/100 s = 3.0 games/s;
  CAP2000 = 2000/3.0*1.2+60 = 859 s).
- 23:33:0xZ -> 23:46:18Z  Y1 (cut at cap, 1,949 games).
- 23:46:18Z -> 00:00:43Z  Y2 (cut at cap, 1,756 games); RUNNER8A_DONE.
- 00:03:43Z  runner8b launched (Y3 both-on, then Y4 = AspCappedReopen second seed; Y4 deadline
  00:39:00Z).
- 00:04:4xZ -> 00:17:10Z  Y3 (ALL 2,000 games, complete inside its cap).
- 00:17:15Z -> 00:29:35Z  Y4 (ALL 2,000 games, complete before its deadline); RUNNER8B_DONE
  00:29:35Z.
- Pooled numbers computed 00:30-00:36Z; report finalized and pushed by ~00:42Z (past the 70-minute
  mark by the final edits, inside the 80-minute limit).

## 7. What I did NOT do

- Nothing was cut: Y3 and Y4 ran to their full 2,000 games inside their limits (the rate from the
  control, 3.0 games/s, held). Y1 and Y2 were shortened by their caps (1,949 and 1,756 of 2,000).
- I did not test other AspReopenMargin values (13 is hard-coded in the switch's helper, not a UCI
  option) - the "capped step" size was never a tunable here.
- The dead `break` lines were only PROVEN unreachable by the arithmetic above; I did not add a
  runtime assertion to count near-misses of the break condition (the counters count the reopen
  sites, which dominate any effect).
- No engine source committed (the trace diff is a text file in my job folder; the traced copy lives
  outside the git work tree); no PR opened.

## 8. What I am NOT sure about

- Y1's -20.0 rests on one seed (cut at 1,949/2,000); the interval excludes 0 comfortably, but a
  second seed would still be the cleaner proof - the job gave Y4 to "the better single switch",
  which was AspCappedReopen by my numbers, so AspArmLate stays one-seeded.
- Why AspArmLate loses: my reading is that after every unstable iteration the full window re-search
  repeats work the narrowed window would have reused - consistent with the bench nodes RISING with
  the arm on at bench 13/16 while falling at bench 11 - but that is interpretation, not measurement;
  the counters show only THAT it acts (19 of 80 iterations), not WHY it costs.
- The counters measure "changed root-window decisions", a proxy for "changed search behaviour";
  a decision can change and still leave the PV identical (the 65-75% double-draw shares of jobs 6-7
  showed how often that happens). I did not measure PV-level effects.
- The ending tallies come from fastchess's completion-order lines; I did not join each ending to its
  PGN game (the per-game recount lines carry result + opening + pair, which is what a recount needs;
  the ending is only aggregated).

## 9. A better way

- Dead-code finding worth Fable's attention: AspCappedReopen's `break`-and-abandon paths
  (src/search.cpp:2421, :2429) cannot fire - `capped_fail_low(x) = x - 13` makes `x <= alpha`
  impossible, and the mate/decisive case reopens to -inf/+inf which also cannot satisfy it. If the
  abandonment was the switch's INTENT (give up the iteration when the score is beyond the cap), it
  never happened in any game played with the switch on, here or in job 1. A one-line check
  (`assert(!(iteration_score <= alpha))` under a debug define, or a counter) would have shown this
  in 2026-11-13's audit round.
- The counters cost ~30 lines and one build; the per-1,000-nodes normalization made "acts a lot /
  acts a little" quantitative BEFORE any match ran (169 vs 22 changes per 1,000 nodes predicted
  which switch would move play more). Cheap and reusable for every candidate switch.
- The ending tally (awk over fastchess's own lines) costs nothing and gives the mate/draw
  distribution per match; for node-limited games the mix of endings is a free sanity signal (a
  switch that changes draw rates is changing play even when Elo says nothing).

## 10. Model name and version

I am glmflash2, running on GLM, model glm-5p3-flash (GLM 5.3 Flash) as far as I know it.
