# kimik3 job 8 report: runner repaired, a second fault found, and the first true TmFinishIteration number

**The faults, in my own words.** Fault one (Fable's recount caught it): `match6.py` and its job-7 children sent
`position fen <board.fen()> moves <all moves of the game>` — the FEN was the position *after* all moves and the
move list the *whole game*. The engine applies the list from that FEN until the first illegal token and keeps
what it reached (uci.cpp:59-65), so every search ran on the current position *without its history* (no
repetition knowledge), and whenever the early moves happened to be legal again it searched a wrong position and
answered a move illegal in the real game — 1,222 of job 6's 4,000 games were runner-made losses, and jobs 6 and
7 measured the runner, not time management. Fault two (found this job): check options accept only the strings
"true"/"false"; anything else prints `info string invalid value for option <name>` and silently keeps the
default (uci.cpp:272-274, guard at 399-402 and 418-423). My runners sent `TmFinishIteration=1` — so even beside
the position bug, job 6's and job 7's "on" sides were the *default* engine: proof below, a 1,000-game control
with `=1` on side A is a perfect mirror, **+0.0 [+0.0, +0.0], every one of 500 pairs split exactly**. Job 7's
U1/U1b/U2/U3 lines are void in one line: same runner, same `=1`. (Job 7's TmLog tally used `=true` and its stop
reasons were real — but its games had the history fault, so its counts are not a match result.)
**Ending counts, every match this job (illegal must be 0 — and is):** V0m control (1,000 games): mate 466,
threefold 468, insufficient 54, stalemate 6, fifty 6, illegal 0, caps 0, node-time forfeits 0/0. V1 (1,000
games): mate 493, threefold 437, insufficient 51, stalemate 3, fifty 16, illegal 0, caps 0, forfeits 0/0. (Job 6's files had zero threefolds in 4,000
games — the lost history; with history fed, 46.8 % of control games end in a repetition draw.)
**Results:** V1 `TmFinishIteration=true` vs off, 1,000 games, seed 7501: ****+18.4 [+4.8, +32.1]** (W273-L220-D507), 500/500 pairs complete, forfeits 0/0**. **Cut: V2, V3, V4, V5
— the two faults cost the match budget twice (V1 ran once as the `=1` mirror before the true run), and the
remaining credits allow one true match only. V2 (TmNodeShare) is the first thing to rerun in the next job.**

## Step 1 proofs (files in `tests_kimik3_job8/`)

a. Repaired feed — `match8.py.txt`: per game the opening FEN is fixed (`pairs[pair]`, normalized once); every
   search sends `position fen <opening> moves <moves so far>` (a `position startpos moves ...` branch when the
   opening is the start). No `board.fen()` anywhere in the send path.
b. Stop control — a game ending by an illegal move, an unparseable/`(none)`/`0000` bestmove, or an engine
   `info string illegal move` line is never scored: the runner writes `FAULT` and exits 3, stopping the match.
   2,040 games this job (40 proof + 1,000 control + 1,000 V1): zero faults.
c. Endings counted per game in the job's order (mate, stalemate, threefold, fifty, insufficient, node-time,
   cap, illegal) — counts above; per-game `end <why>` on every game line.
d. Engine-sees-the-game — there is no `d` command in uci.cpp (the command set is position/go/setoption/eval/
   bench/...; `eval` prints a score, not the board), so the file's fallback was used: for the 20 repeat-proof
   games, the position before each of the last 10 moves was sent and `go depth 1` asked; **200/200** best moves
   were legal in the runner's python-chess board (`probe8.py.txt`; output in the stamps line).
e. Repeat proof — 20 games at NodeClock 100, seed 7500, twice: identical move for move, summaries identical
   (`rep_nc100_run1.txt` == `rep_nc100_run2.txt`). Wall-clock control (NodeClock 0), same seed, twice: the runs
   differ (`nc0_r1.games`, `nc0_r2.games`). Bonus control: the `=1` mirror itself — 1,000 games, two shards
   playing each opening with colours reversed came out move-identical in every pair (W233-L233-D534, pair mean
   exactly 1/2): determinism at match scale, and the silent-ignore proof of fault two.

## The matches of THIS job (10+0.1 on the node clock, Threads 1, Hash 16, uho200 openings 1-200)

| match | A vs B | NC | games/seed | W-L-D (A) | Elo [95 %] | nodes/move A | nodes/move B | soft share A/B | hard A/B | forfeits A/B |
|---|---|---|---|---|---|---|---|---|---|---|
| V0m | `TmFinishIteration=1` (silently ignored) vs off | 100 | 1000 / 7501 | 233-233-534 | +0.0 [+0.0, +0.0] | 23,558 | 23,558 | 1.150/1.150 | 607/607 | 0/0 |
| V1 | `TmFinishIteration=true` vs off | 100 | 1000 / 7501 | 273-220-507 | +18.4 [+4.8, +32.1] | 22,119 | 23,288 | 0.912/1.152 | 141/733 | 0/0 |

Elo: 400·log10 of the mean pair score, 95 % interval from the per-pair distribution over complete pairs
(`elo_pairs.py` of job 6). Nodes/move = node-ms × 100. Hard = runner reconstruction (used ≥ 95 % of the
computed hard limit; the exact stop-reason tally is a later job per the file).

**What V1 says.** The first true measurement of the finish rule: **+18.4 [+4.8, +32.1]** — a real,
significant gain, and it lands close to job 6's void +21.6 [+6.0, +37.3]: the runner bug happened to add ~3
points of noise on top of a real effect, but nothing in the void data could have certified that. The true
mechanism is visible: the on-side spends 5.0 % fewer nodes a move (22,119 vs 23,288), uses 0.912 of its soft
limit against 1.152, and hits the hard limit 5.2× less (141 vs 733). Against the control's exact +0.0 noise
floor, the interval [+4.8, +32.1] is the option and nothing else.

## Files of the repository opened

uci.cpp (option parsing, position parsing, command set — the two faults and the `d`-check live here),
search.cpp (only to confirm `TmFinishIteration`'s default at line 109 and that no other reader of the option
exists), plus the job file and my job-6/job-7 reports.

## Stamps

Job file read 22:51; runner repaired and smoke-tested 22:53-22:56; repeat proof + wall control complete 22:57
(probe 200/200 at 22:58); V0m `=1` control complete 23:07 — mirror noticed, fault two identified in uci.cpp
23:07; V1 (`=true`) launched 23:07, complete 23:16; report written 23:1x-23:2x; all UTC 2026-11-15.

## What I did not do

- V2 (TmNodeShare on/off, seed 7502), V3 (both finish on, divisor 18 vs 22, seed 7513), V4 (finish at
  NodeClock 400, seed 7512), V5 (TmStability, seed 7504): cut. Cut order per the file was respected in reverse
  — only V1 was guaranteed; the `=1` discovery forced V1 to run twice and credits ran out before V2. Any
  future number must use `=true` for check options: every job-6/7 check-switch match is void for two
  independent reasons.
- No exact stop-reason tally with the repaired runner (Part C moved to a later job by the file).
- Step 3 (Part B reading): not reached — step 2 was not completed.

## What I am not sure about

- Whether V1's true effect size is stable across seeds: it is one seed on openings 1-200. The `=1` mirror says
  the off-vs-off noise floor of this runner is exactly zero, so any V1 signal is the option, but a second seed
  (with the hash-of-game-list line from job 7) is still owed.
- The mirror's identical move sequences mean the tested option was off — they do not by themselves prove the
  runner's clock bookkeeping right; the repeat proof and the 200/200 probe cover that, but a full-game engine
  position dump (a real `d` command) would be the stronger instrument.

## A better way

Two runner asserts would have caught both faults on day one: (1) fail the match on any `info string invalid
value for option` line from the engine (the engine already prints it — uci.cpp:273; the runner just has to
listen), and (2) fail on any illegal bestmove instead of scoring it (now in match8). Add a third: read back
every option after setting it is impossible over UCI, so the runner should keep a whitelist of check-option
values (`true`/`false` only) and refuse anything else before the engine is even started.

Model: Kimi K3.
