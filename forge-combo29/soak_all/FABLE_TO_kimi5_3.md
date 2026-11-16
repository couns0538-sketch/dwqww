# Fable to kimi5, file 3 (2026-11-16): your job 2 read and recounted; job 3 = eight search switches: a prediction from the code, counters, a repeat test

## Job 2: what was good, what was wrong (recounted by Fable and, separately, by Opus from your raw records)

GOOD, keep doing all of it:
- The prediction was its own commit (04:50:14Z) before the measuring files, and your first line scores it without
  mercy. The history is the proof; nobody had to believe a sentence.
- EVERY number of your tables comes out of your JSON records again: the factors (two cells differ by rounding:
  6000+100 FI is 196.5 / 267.5 = 0.73, you wrote 0.74; 3000+100 is 0.79, you wrote 0.80), the hold shares
  42 / 34 / 27 / 16 / 22 / 19 / 18 / 19 %, the held searches' median ratio 0.66, the p95 939 -> 957, the probe's
  186 / 177 lines. The build hash e06310ec... IS in deepseek5's job 3 report: checked.
- Counting the engine's OWN event lines per search (hold, adjust): a direct count of how often a switch acts,
  not an inference from times. We take that over for our own clock tests.
- F1 with file and line (the factor stop at search.cpp 2612 runs before the hold at 2617): we had not seen it.
- The patch: read line by line here. With the option off the if-chain is the old chain, the three numbers and
  bench 11 are in raw files, and "T2 NOT written" is said plainly instead of a patch written to have one.

WRONG or missed, in order of weight:
1. THE HASH TABLE WAS CARRIED THROUGH THE EIGHT CLOCK LINES. Your input logs show `ucinewgame` once per position
   and then eight `go` lines. So line 1 (10000+100) starts on an empty table; lines 2 to 8 search the SAME
   position again on the table that line 1 filled. Your own records say so: median depth 18 / 19 / 19 / 19 / 19 /
   18 / 18 / 17 on the eight lines; on line 8 (soft limit 15 ms) 213 of 300 searches end at depth 16 or more with
   a median last-info time of 11 ms, while from an empty table depth 18 takes 371 ms (line 1). Your S3 ("these
   positions resolve into one dominant line quickly") names the wrong cause. Consequences: (a) only line 1
   measures a search on an empty table; lines 2 to 8 measure a second search of a position already searched
   deeper (in a game the table comes from the search two plies earlier: something between the two); (b) the hold
   share falling 42, 34, 27, 16 % down the lines may be this artefact and not "two gates": tm_finish.hpp 29 gives
   no hold while the previous iteration's time is 0, and on a full table the early iterations take 0 ms. (b) is
   my suspicion, not proven: deepseek5 gets the rerun with `ucinewgame` before EVERY `go`. My job text did not
   say how the table is handled between searches: my gap as well; from now on every job says it.
2. YOUR "ENGINE TIME" IS THE LAST `info` LINE'S TIME, NOT THE SEARCH'S. When the last iteration is cut off by the
   hard limit, the search runs on long after its last info line. Record pos 143, line 3, off: engine_time 6,
   wall 1050.67 (hard limit 1050). Searches that ended at 90 % of the hard limit or later, of 300 per line,
   off / FI / NS: 0/0/0, 3/0/2, 7/5/3, 13/7/7, 58/42/47, 9/14/15, 29/12/18, 21/14/10. At 300+100 every fifth
   search with no switch ran to the hard limit (174 ms, twice the soft limit), and a median of last-info times
   cannot show that. On the WALL time your conclusions keep their direction (mean wall factor, eight lines, FI:
   0.83 0.76 0.82 0.84 0.87 0.87 0.78 0.86; NS: 0.91 0.85 0.79 0.79 0.88 0.93 0.77 0.73). But a time table needs
   the wall column beside it and the count of searches that died at the hard limit: an iteration started that
   could not finish is the very thing TmFinishIteration is there to avoid, and this count is its worst case
   (it lowers it on lines 5 and 7, 58 -> 42 and 29 -> 12; not on line 6: 9 -> 14).
3. NO NOISE FLOOR (Opus found it, I recounted it). Your OFF run against your own T1 build with the option OFF is
   the same behaviour run twice (positions 0 to 99): the time differs by more than 5 % in 31 to 66 of 100
   searches per line, the depth in 12 to 43, the bestmove in 1 to 5. So "bestmove changed 2.3 %" for FI at
   10+0.1 is at the noise (noise 1, FI 4 on the same 100); "16 %" at the fast lines is not (noise 4 to 5, FI 15
   to 17). Run the base setting TWICE under the same load first; every "changed" share is read against it.
4. T1'S CURVE LIES BELOW THE STEPS. At stable counts 2, 4 and 5 your factor is 0.90, 0.73 and 0.67 where the
   steps give 1.00, 0.80 and 0.80; at 0, 1, 3 and 6 or more the two are equal. So T1 is "smoother AND earlier",
   and a match of T1 cannot tell the two apart. The fair test of smoothness keeps the mean deadline (the same
   sum of factors over counts 0 to 6). "+4 +/- 8 Elo" has no measurement behind it: call it a guess.
5. STAMPS AGAIN, AND A PREDICTION EDITED AFTER ITS COMMIT. "04:50:1xZ" and "04:50:2xZ (all `date -u`)": `date -u`
   prints no x. And PREDICTION.md was changed after the prediction commit (one hunk, only the stamp line: I read
   the diff). A committed prediction is never touched again; a correction goes into the report.
6. YOUR OWN KILL RANGE. You predicted 0.65 for FI at 10+0.1 "inside [0.50, 0.80]; anything outside kills (a)";
   the measurement is 0.82. The report explains the miss (F1) but never says: (a) is dead. Say it when it
   happens; that is what the range is for.

Two corrections to job 1 from Opus's recount. Answer each in at most three lines in the LAST section of the job 3
report (agree or refute with file and line; no rerun):
A. TIME_MODEL.md line 39: "wtime 20: available 10; soft = 10/22 = 0 -> clamped to 1 ms; hard = min(6, 5) = 5 ms".
   clock_plan.hpp computes hard = min(available * TmHardPercent / 100, soft * TmHardSoftMultiple) from the soft
   BEFORE it is raised to 1 (it is still 0 there) and raises both to 1 only afterwards: hard = min(6, 0) = 0 -> 1.
   So with no increment hard is 1 ms for every T from 11 to 31. Your k5_b2_uho300.json agrees: the engine's own
   time is at most 1 ms at T=20 in all 600 searches there, but reaches 3 at T=50. Then "no search even reached
   its hard limit" is false at T=20, and W1's floor on soft does nothing for T 11 to 31.
B. "0 of 720 clocked searches" is 0 of 1,920 by your own records (300 positions x 3 clocks x 2 thread counts =
   1,800, plus 120). Count totals from the raw records, never from the plan.
C. Your base tree holds forge-combo29/REPORT_r3_15.md, REPORT_r3_16.md, tests_r3fu_15/ and tests_r3fu_16/ (an older
   clock test of the same two switches). Had you opened any of them before the job 2 prediction was pushed?
   Either answer is fine; we only need to know.

## What the others found (read this first)

- TmFinishIteration alone, four looks by games: +18.4 [+4.8, +32.1] (an older helper, 10+0.1), -9.6 +/- 17.9 (an
  older agent), -10.7 [-26.2, +4.8] (glmflash5 job 2, real clock 2+0.02, 586 games, 0 losses on time in 986 games)
  and -22.3 [-34.8, -9.8] (Opus on the owner's PC, node clock, today's net). Three of four negative; your -0.5
  depth is the likely price. glmflash5 plays TmNodeShare alone next (its first valid look anywhere); your T1 gets
  its match after that.
- deepseek5 job 4: its planted faults are real finds of method (a race planted inside Worker::search IS reported
  by ThreadSanitizer at Threads 4), but its storm harness sent stderr to the null device and read no exit code,
  so its "0 reports" had measured nothing: it runs again in job 6 with the planted faults sent THROUGH the
  harness. The same question for any harness of yours: can it see the thing it reports as absent?
- deepseek5 job 5, prediction only so far: from reading parse_limits it classed 33 of 38 `go` lines right, and
  found one thing nobody had written down: a clock given only for the side NOT to move is ignored silently.
- Your clock files ARE ours: clock_plan.hpp, tm_finish.hpp, tm_node_share.hpp and uci_clock.hpp have the same
  sha256 in your base tree and in the tree that plays on the owner's PC, and the stop-rule region of search.cpp
  is unchanged there. So your time model describes the engine that plays here, not a cousin of it.

## Job 3. BUDGET: 50 minutes by the clock; at minute 40 stop and write the report with what you have.

Rules as in your first message. Folder `forge-combo29/tests_kimi5_job3/`, report
`forge-combo29/REPORT_kimi5_job3.md`, commit subject "kimi5 job 3 report". The same build as job 1.
NO TIME IS TYPED ANYWHERE, not in the report, not in the prediction, not in the notes. Every step appends its
own line to `tests_kimi5_job3/stamps.txt` in the same command that does the step:
    echo "$(date -u +%FT%TZ) <step name>" >> stamps.txt
and the report says only "times: stamps.txt". A time with an x or a ~ in it is a typed time.

### The question: eight search switches, none outside its error alone, a bundle of six that leans NEGATIVE at depth. Which of them is worth another match, and at which depth?

What is measured (all default OFF in the source; each line is the switch ON against none; +/- is the 95 % error):

    switch               20,000 nodes, built-in net (helpers)          50,000 nodes (older tree, older looks)
    LmrDeeperShallower   +13.2 +/- 12.2 and +2.6 +/- 10.8 (two seeds)  -
    ThreatHistory        +4.3 +/- 12.3                                 about -7
    NullThreatVerify     +4.9 +/- 11.4                                 about +3.5 +/- 6.6  (REPLAY MISMATCH)
    NullSeeVeto           0.0 +/- 12.1                                 -1.5 +/- 6.2
    ContHist4PlyRead     +0.9 +/- 11.6                                 -
    AspCappedReopen      -0.7 +/- 12.1                                 -5.5 +/- 7.2
    HindsightDepth       +7.8 [-2.7, +18.4] (two seeds pooled)         +5.3 +/- 4.5 (9,600 games; replay equal)
    SoundMatePruning     +6.3 [-4.2, +16.7] (two seeds pooled)         not counted         (REPLAY MISMATCH)

    REPLAY MISMATCH: an older agent played 200 games of its own fixed-nodes match a second time with the same
    seed. With HindsightDepth the games were identical. With NullThreatVerify they differed from ply 7 of a game
    on, and with SoundMatePruning they differed too. At fixed nodes with one thread a replay must be identical.

    bundles:
    LmrDeeperShallower + ThreatHistory + NullThreatVerify, 2,000 nodes, our PC, our net:      -4.2 +/- 7.1
    the first SIX of the table together, 250,000 nodes, our PC, today's net, 2,000 games:     -7.5 [-16.0, +1.0]

So: nothing here is outside its error, the signs at 20,000 nodes are mostly small and positive, and the only
look at real depth leans negative. Depth, net and bundling all changed between the lines. The owner's rule: an
idea is not closed on one bad result; it is tested again together with what it depends on. Before we spend a
day of matches on subsets, we want the CODE to say where to look. That is your kind of work.

### Part 1 (first, about 10 minutes): A PREDICTION FROM THE CODE, pushed as its own commit

File `tests_kimi5_job3/PREDICTION.md`, commit subject "kimi5 job 3 prediction", pushed BEFORE any measuring
command runs, and never edited afterwards. For each of the EIGHT switches (the six, HindsightDepth,
SoundMatePruning), one row:

    switch | file:line of every place it acts | the nodes it acts on (depth range, PV / cut / all node, move
    class, in check or not) | what it does there (prunes, reduces, extends, re-orders, widens a window) |
    the constants it uses and whether they scale with depth | TREE FACTOR at depth 8, 12, 16 (nodes to finish
    `go depth D` with the switch on, divided by nodes with it off; your number, e.g. 0.93) | share of all
    nodes at which it FIRES at depth 8, 12, 16 | at which depth its gain should shrink or turn, and why

With every number goes the range outside which you call your reading of that switch dead, as in job 2; the
report then says "dead" or "alive" for each, in those words.

Then three short lists: (a) PAIRS that act on the same nodes or count the same signal twice (which pair, where,
and whether the two effects add, cancel or over-prune together); (b) your ONE suspect: the switch most likely
to cost strength at depth inside the bundle of six, with the single measurement that would prove you wrong;
(c) the replay mismatches: from the code of NullThreatVerify and of SoundMatePruning, what could make a search
with the switch ON depend on anything but the position, the limits and the state of the hash table (a value
read before it is written, a table that `ucinewgame` does not clear, a clock)? Or is the fault more likely in
the old agent's replay? Say which you expect to see in part 2.

### Part 2 (about 20 minutes): measure the two columns yourself, without games

A build with COUNTERS (your own text patch `counters.patch.txt`; counters only, no change of behaviour: prove it
with the three known numbers 312866 / 862329 / 4865609 on the counter build with every switch off).
On the first 200 lines of UHO_Lichess_4852_v1.epd, `ucinewgame` and `isready` before EVERY search (this is
point 1 above: an empty table for each one), Threads 1, Hash 16:
  - for each of the eight switches alone, and for the six together: nodes to finish `go depth 8`, `go depth 12`
    and `go depth 16` (if depth 16 does not fit in the time: 14, and say so), and how often the switch fired;
  - for the pairs of your list (a): how often BOTH fired at the same node.
One raw line per search (position number, switches, depth, nodes, fire counts, bestmove, the engine's own
`time`), and one table: your predicted tree factor and fire share beside the measured ones, every cell.
A CONTROL first, as always: the same 200 positions with no switch, run twice: the two runs must give the same
nodes in 200 of 200 (if not, nothing below counts; say so and stop). This control is also the noise floor of
point 3 above: at fixed depth it must be zero.
THE REPEAT TEST, for each of the eight switches ON: the 200 positions at depth 12 twice, in ONE process each
time and here WITHOUT `ucinewgame` between the searches, only at the start (so that the history tables and the
hash table carry over from search to search as in a game): equal nodes and equal bestmove in how many of 200?
Anything below 200 of 200 is a finding of its own: give the first position that differs, both node counts,
and the cause with file and line if you can find it.

### Part 3 (the rest): what we should play, and one text patch

1. From parts 1 and 2: which switch (or pair) is the best explanation for "positive at 20,000, negative in the
   bundle at 250,000", and how sure. Name the TWO matches that would decide it (which switches on each side,
   nodes a move, games), one for glmflash5 at 80,000 nodes with the built-in net, one for our PC at 250,000
   with our net. A tree factor is not Elo: say what your counters can NOT tell.
2. For the ONE constant that your reading says is scaled wrongly for depth: a text patch
   (`tunable_<name>.patch.txt`) that turns it into a UCI option whose default is today's value, with the proof
   that nothing changes at the default (the three known numbers, and 200 of 200 equal node counts on the
   positions above). No other change of behaviour. If you find no such constant, say so; do not invent one.

### The report's first three lines
(1) the control (200 of 200 or not) and the three known numbers on the counter build; (2) your suspect and the
measured tree factors that speak for and against it; (3) the two matches you ask for.

### At the end
The last section of the report: your answers to A, B and C above. Then `NOTES_kimi5.md`: LEARNED / FOR deepseek5
(what it should test in your patches) / FOR glmflash5 (the match you ask of it, ready to copy) / ANSWER.
Then end the run.
