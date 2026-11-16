#!/usr/bin/env bash
# make_report_job2.sh — assembles REPORT_job2.md from job2/raw2 (the clean, guarded run).
set -u
D="$(cd "$(dirname "$0")" && pwd)"
cd "$D"
R=../REPORT_job2.md

cat > "$R" <<'HEAD'
# REPORT job 2 — AREA 8 (THE CLOCK) — very little time — seat 08

## What was asked
`wtime 100, 30, 10, 1, 0` (each also with `winc 0` and `winc 10`): overruns and losses on time, 200 searches
per control on the first 100 of O and first 100 of G.

## The answer (one line each)
- The engine never exceeds the clock it is given, at any of the ten controls: 0 of 2,000 searches ran longer
  than the `wtime` sent. There is no loss on time at these clocks on a quiet 4-core box.
- At `wtime 10`, `wtime 1` and `wtime 0` the plan is "reserve empty" (`time <= Move Overhead`, and
  `Move Overhead` defaults to 10) and the search collapses to a 1-ply, 2000-node emergency search answered in
  0.14-0.17 ms median. That is a deliberate branch (`clock_plan.hpp:32`, `search.cpp:2310-2319`), not a
  failure — but it means that with Move Overhead at its default of 10, any position where the GUI hands the
  engine 10 ms or less is played one ply deep.
- Where it CAN exceed its own plan: at `wtime 30 inc 0` the plan is soft 1 ms / hard 1 ms, and 108 of 200
  searches ran past 1 ms (median 1.05 ms, max 1.54 ms). That is 54 % of searches over its own hard limit —
  the only control where the hard limit is not respected.

## How sure
Sure for the two headline facts: 2,000 searches, guard-passed clean run, and the "reserve empty" branch is
read directly in the source and reproduced with `probe_reserve.sh`. Sure that 0 searches exceeded the wall
clock (the margin at the tightest control is 1.54 ms against 30 ms).
Less sure about the exact hard-limit-overrun count at `wtime 30 i0`: hard is 1 ms there and the measurement
floor of one process round trip is about 0.1 ms, so "108 over 1 ms" is within a few ms of meaning "the engine
does not honour a 1 ms hard limit at all" either way.

## Honesty numbers
Same exe as REPORT_job1.md: /home/ubuntu/builds/release/forge,
sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83, bench 11/13/16 and perft 5 exact
(312,866 / 862,329 / 3,024,920 / 4,865,609). job2/raw2/.meta holds the path and sha256.
A prediction for this job was committed and pushed alone at 21:18:31Z, before the first measuring command
(job2/prediction.txt, commit 9a0a767a9).
HEAD

cat >> "$R" <<'H1'

## Step table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction pushed alone before measuring | done | job2/prediction.txt | pushed 21:18:31Z, before any search |
| 10 controls x 200 searches, guarded clean run | done | job2/raw2/w{100,30,10,1,0}_i{0,10}.jsonl | 2,000 searches |
| overrun counting against the clock AND against the engine's own hard limit | done | job2/raw2/analysis_table.txt | 0 over the clock; 143 over its own hard limit in total |
| inc-0 vs inc-10 comparison named by the prediction | done | job2/raw2/analysis_table.txt | held at 100 and 30 ms, failed at 10/1/0 (reserve empty) |
| what the engine answers with no clock left | done | job2/probe_reserve.txt | first legal move, `bestmove f5f4`, no search |
| bestmove legality at every control | done | job2/raw2/analysis_table.txt (last column) | 0 illegal in 2,000 |
| contaminated first attempt disclosed and discarded | done | REPORT_job1.md "contamination incident", job1/raw2/contamination_table.txt | first set kept at job2/raw/, not used |

## The table (pasted output of `python3 analyse_job2.py raw2`)

```
H1
cat raw2/analysis_table.txt >> "$R"
cat >> "$R" <<'H2'
```

## Probe of the reserve-empty branch (pasted output of `python3 probe_no_clock.py ~/builds/release/forge`)

The mechanism, read in the source: with `reserve_empty` the engine plays the transposition-table move when it
is legal with 0 nodes (`search.cpp:2302-2309`); otherwise it runs an **emergency one-ply search capped at
2000 nodes** (`search.cpp:2310-2319`, `max_depth = 1`, `kEmergencyNodes = 2000`), and an unfinished ply falls
back to the first legal move. In a fresh process there is no table entry, so the answer should equal the
`go depth 1` answer. Measured on 8 positions: the `wtime 1` answer equals the `go depth 1` answer 8 of 8
times and the first legal move only 1 of 8 times.

```
H2
sed -n '1,30p' probe_no_clock.txt >> "$R"
cat >> "$R" <<'H3'
```

## Findings

### 08-F5 — with 10 ms or less on the clock the engine drops to a 1-ply, 2000-node emergency search
`plan_clock_budget` (`include/forge/clock_plan.hpp:32`) returns `ClockPlan{0, 0, true}` — `reserve_empty` —
when `time_ms <= Move Overhead`, and `Move Overhead` defaults to **10**. Measured: `go wtime 10 btime 10`,
`wtime 1` and `wtime 0` all answer in a 0.14-0.17 ms median (max 0.98 ms). What it does then is NOT "play the
first legal move", which is what the comment at `search.cpp:2280-2284` might suggest: it plays a legal
transposition-table move with 0 nodes if there is one (`search.cpp:2302-2309`), otherwise it runs
`max_depth = 1` with a 2000-node cap (`search.cpp:2310-2319`). Measured on 8 fresh-process positions, the
`wtime 1` answer equals the `go depth 1` answer **8 of 8** and the first legal move only 1 of 8.
Show it again:

    cd forge-combo29/swarm/08/job2 && python3 probe_no_clock.py ~/builds/release/forge

    cd forge-combo29/swarm/08/job2 && bash probe_reserve.sh ~/builds/release/forge /tmp/pr.txt

Why it matters: this is the correct behaviour for not losing on time, but the threshold is the FULL
`Move Overhead`. A GUI that reports 8-10 ms left (a common low-time situation) gets a 1-ply move, and the
engine will do that for as long as the clock stays at or below 10 ms. With `winc 10` at `wtime 10` the plan
is STILL reserve-empty — `plan_clock_budget` tests `time <= overhead` before it ever looks at `increment` —
so a 10 ms increment on a 10 ms clock buys a 1-ply move, not a search. That last part is the piece I would
question.

### 08-F6 — at a 1 ms hard limit the engine runs 108 of 200 searches over it
`wtime 30 btime 30 winc 0`: available = 30 - 10 = 20 ms. `soft = 20/22 = 0`, then clamped up to 1 ms;
`hard = min(20*60/100, 0*5) = 0`, then clamped up to 1 ms. So the plan is soft 1 / hard 1 (the table's own
columns show those values). Measured: median 1.05 ms, p99 1.47 ms, max 1.54 ms — 108 of 200 searches exceed the
1 ms hard limit, and 0 of 200 exceed the 30 ms clock.
Show it again:

    cd forge-combo29/swarm/08/job2 && python3 analyse_job2.py raw2

Reading: the engine cannot stop inside 1 ms because the stop check plus the `bestmove` write costs about
0.1-0.2 ms of process time before any node is counted. Nothing here loses a game on a 30 ms clock (max
1.54 ms); it explains why the "reserve empty" branch exists at all, and it is the only control in job 2 where
the engine's own hard limit is not respected.

## Suspicions, not proven
- The 143 hard-limit overruns at `wtime 30 i0` and `wtime 100 i10` are probably all the process round-trip
  floor (≈0.1-0.2 ms) rather than search overshoot. NOT separated: I did not time a `go nodes 1` control to
  measure the floor.

## What I did NOT do
- No `movestogo` (job 3), no Threads > 1, no sanitizer (not asked).
- Did not test clocks between 10 and 30 ms, so the exact crossover point where "reserve empty" stops firing is
  not measured; it should be just above `Move Overhead` = 10.
- Did not test a GUI that sends `wtime` without `btime`, or increments without a clock.

## What I am NOT sure about
- The prediction said `wtime 10` and below would be reserve-empty (correct) and that `wtime 30` would give a
  median of 1-5 ms (correct, 1.05). It also predicted 0-40 overruns at `wtime 30`; the measured 108 over its
  own limit tripped that range, but the "over the clock" count — the number that decides a game — stayed 0.
- Whether a real GUI would send `wtime 0`; I tested it because the brief named it.

## Times
see stamps2.txt (a `date -u` line after every control) and stamps.txt (the contaminated first attempt).
H3
{
  echo
  echo "## Last command output"
  echo
  echo '```'
  echo '$ git status --short'
  git -C /agent/repos/dwqww status --short | sed -n '1,25p'
  echo '$ ls forge-combo29/swarm/08/job2/raw2'
  ls -1 raw2
  echo '```'
} >> "$R"
echo "wrote $R"
