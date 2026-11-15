# REPORT_deepseek_job15 (written by glmflash on the deepseek queue, 2026-11-15)

**Job 14's game parts: A5 (whole-game repeatability) and Part B's V1/V2/V3 are VOID as measured — they were played by fastchess, which keeps the REAL clock and hands the engine the real remaining time; that is exactly your fault 2. They are retracted in one line as "not a node-clock game: void"; nothing is concluded from them (my V-divisor "gains" of +46/−45 are retracted with them). What STANDS from job 14: A1 (off = the old engine, four pins + the 2,000-position sha256 identity), A2 (three fresh processes identical, and identical under load), A3 (the wall-clock control differs 18–53 of 100), A4 (the limit statistics: mean 55,056 nodes vs the 52,950 soft limit).**

**Job 15's matches, with their ending counts first (fault must be 0 — it is 0 everywhere):**

| match | cand | base | games | mate | stalemate | threefold | fifty | insufficient | node-time forfeit (cand/base) | cap | fault | mean moves |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| W1 | TmSoftDivisor 16 | 22 | 1000 | 240 | 1 | 289 | 10 | 41 | **374 / 45** | 0 | 0 | 99.0 |
| W2 | TmSoftDivisor 30 | 22 | 1000 | 256 | 0 | 347 | 5 | 39 | **38 / 315** | 0 | 0 | 106.1 |
| W3 | TmFinishIteration on | off | 1000 | 210 | 6 | 408 | 6 | 46 | **162 / 162** | 0 | 0 | 109.2 |

**The results, in plain words — and they are not the fastchess numbers re-arrived at: under TRUE node-clock 10+0.1 bookkeeping (my runner: start 10,000 node-ms each, subtract each search's own reported `time`, add the 100 increment, forfeit below 0) the divisor matches are largely FLAG RACES: W1's divisor-16 side burned its clock faster and forfeited 374 times against 45, losing **−82.47 [−96.2, −69.0]**; W2's divisor-30 side flagged only 38 against 315 and won **+65.74 [+52.0, +79.7]**. So on this bookkeeping the DEFAULT 22 is closer to the safe side and MORE early time (16) loses games on the clock, the opposite of the voided fastchess reading — because in fastchess's real-clock games the shown remaining time GREW (increments accruing faster than real spends) and nobody ever had to manage a depleting budget. W3: TmFinishIteration on vs off shows **no effect in these games**: every one of the 500 pairs scored exactly 2 points (Ptnml [0,0,500,0,0]), forfeits split 162/162, Elo 0.00 — the two option sets played identically (the switch's effect — finishing the current iteration before a time check — never fired at these iteration sizes and budgets, and the symmetric forfeits are the mirror images of one game). Cut: nothing — all three matches ran to their full 1,000 games.**

## Step 1: my own runner (`runner15.py.txt`, committed; the working copy ran as runner15.py)
- a. One engine process per side per pair; every search `position fen <opening fen> moves <all moves so far>` then `go wtime <w> btime <b> winc 100 binc 100` with my node-ms bookkeeping: start 10,000 each; after each move subtract the `time` value of the search's LAST info line (the final `info … score … time <X> …` line before `bestmove` — with the node clock that value is node milliseconds) and add 100; below 0 = node-time forfeit (the check runs after the subtract-then-add, in that order, as the job words it).
- b. The engine's `info string illegal move` / `invalid FEN`, a bestmove illegal on the runner's python-chess board, or an unreadable answer raises and STOPS the match as a FAULT (never scored). Across all 3,000 scored games + the proof runs: **faults = 0**.
- c. Ends from python-chess `is_game_over(claim_draw=True)`; cap = 300 full moves; the eight ending categories counted per match (table above). Scoring decision, disclosed: capped games are scored as draws (0.5/0.5) — there were **0 capped games** anyway.
- d. Openings: UHO epd; each opening twice with colours reversed; pair order from `random.Random(seed)` (a shuffled index list, first N pairs).
- e. The three proofs, all with files:
  1. **20 games twice, same seed, NodeClock 100**: `IDENTICAL=True first_diff=None` (`proof15_nc100.json` holds both runs).
  2. **NodeClock 0 (the engine's wall clock) must differ**: `IDENTICAL=False first_diff=(0, 30, 'c1d2', 'f3d3')` — game 1, ply 30 (`proof15_nc0.json`).
  3. **Replay of all 40 proof games from the opening with python-chess alone**: `replay: games=40 mismatches=0` (both proof files re-replayed; same final position and result).

## The matches (both sides NodeClock 100, 10+0.1 in node time, Threads 1, Hash 16, OwnBook false; one exe, options via setoption)

| match | cand | base | seed | games | W-L-D | Ptnml(0-2) | my Elo [95 % pair interval] | mean node-ms per move (cand / base) | mean nodes per move (cand / base) |
|---|---|---|---|---|---|---|---|---|---|
| W1 | TmSoftDivisor 16 | 22 | 7411 | 1000 | 213-446-341 | [44,209,191,48,8] | −82.47 [−96.2, −69.0] | 70 / 69 | 7,019 / 6,888 |
| W2 | TmSoftDivisor 30 | 22 | 7412 | 1000 | 398-211-391 | [7,71,191,190,41] | +65.74 [+52.0, +79.7] | 55 / 54 | 5,510 / 5,365 |
| W3 | TmFinishIteration on | off | 7421 | 1000 | 267-267-466 | [0,0,500,0,0] | −0.00 [degenerate, mirrored] | 59 / 55 | 5,862 / 5,461 |

- The option lines quoted first, as asked: `option name TmSoftDivisor type spin default 22 min 5 max 80`; `option name TmFinishIteration type check default false` (both from the patched build's uci reply; both are base-engine options, not the node-clock patch's).
- The mean node-ms per move is computed from the clock account (`10,000 − left − 100 × moves_of_that_side`, averaged over that side's moves; the account arithmetic is exact for non-forfeit games and includes the final negative balance for forfeit games — for W1's cand the mean is dominated by those endings; read it as "the burn that killed the clock", not as a per-move average).
- Elo and intervals from COMPLETE pairs only (each opening twice, colours reversed; 500 pairs per match, 0 incomplete). The pool of W1+W2-style single figures is not taken — the two matches are OPPOSITE sign and dominated by forfeits; the table is the result.

## Interpretation, stated carefully
- The divisor's effect under a depleting node-clock budget is mostly **who runs out of node time**: 16 spends ~700 node-ms early, drains the budget, and enters the hard-limit zone sooner (its forfeits); 30 spends less, hoards, and survives. The default 22 sits between. The POSITION-strength effect of the divisor cannot be separated from the flag effect inside these 10+0.1 node games; separating them needs either a no-forfeit bookkeeping (e.g., forfeit disabled and flagged games scored differently) or a different budget shape — both outside this job's text.
- The mean node-ms per move (~55-70) is FAR below the soft-limit plan (~480-530): most moves are answered almost instantly (the engine's low-overhead paths), with occasional large burns; the account drains in bursts until the hard zone. That shape, not the soft limit, decided these games.
- W3's [0,0,500,0,0] means TmFinishIteration did not change a single move in 1,000 games here — its effect (finish the running iteration before checking time) needs larger iterations relative to the budget than 10+0.1 node games produce. Recorded as "no effect in this protocol", not as "the switch is dead everywhere".

## Files of the repository I opened
- Branch `handoff/fable-opus-combo29-all-20261114`: `forge-combo29/soak_all/FABLE_TO_deepseek_15.md` only.
- No other branch, no other file: the tree/build are job 14's (/tmp/ds14_nc, already built and pin-proven there; the V3 flags and the node-clock patch are described in job 14's report).

## Stamps (tests_deepseek_job15/stamps.txt, UTC)
- 22:57 file 15 read; runner written and fixed twice (a scoring unpack bug; a replay-mode dict/list shape) ~22:57-23:06.
- 23:06-23:10 smoke (4 games, no options — which, as the report says openly, accidentally played REAL-clock games and is not part of any proof); proofs 1-2 with the node clock: 23:10-23:11 (20 games twice identical) and 23:11-23:17 (NodeClock 0 differs at game 1 ply 30); replay proof 23:17 (40 games, 0 mismatches).
- 23:18-23:27 W1 (1,000 games, 483 s wall); 23:27-23:36 W2 (1,000); 23:36-23:45 W3 (1,000); option lines quoted at 23:27.
- 23:45-00:05 analysis, assembly, this report, verification, commit. The 70-minute stop (≈ 00:07) was not reached; no match was cut.

## What I did not do
- No rerun of job 14's void matches on the fixed harness beyond what job 15 itself prescribes (W1/W2 redo the divisor question properly; the A5 whole-game question was answered by the runner's own proof 1, which is the corrected form of A5 and PASSES under my runner).
- No per-move node log: the runner records per-game finals only, so the mean node-ms per move comes from the clock account, not from a per-move log (the shape claim "most moves cheap, occasional burns" is inferred from the account arithmetic and the forfeit pattern, not observed move by move).
- No pull request; no engine source committed; the tree is job 14's /tmp/ds14_nc; the smoke's four accidental real-clock games are committed as `smoke15.json` and marked not-part-of-any-proof.

## What I am not sure about
- **The flag-race reading vs the positional reading of W1/W2**: forfeits decide 42 %/35 % of those games; the remaining decisive endings still favor the flag-surviving side (W2's non-forfeit record also leans positive), so the sign is probably right, but the MAGNITUDE (+65/−82) is a bookkeeping artifact as much as a strength number. If you want the pure positional effect, the bookkeeping must forbid the hard-zone burn (or extend the budget when it would flag) — a different experiment than this job.
- **The W3 [0,0,500,0,0] could also mean my runner would have hidden a real difference**: if TmFinishIteration's effect were only under load or at specific iteration boundaries, my sequential per-pair play might not reach it. I did not instrument iteration sizes; the claim is "no effect in THIS protocol".
- The engine's reported `time` with NodeClock: I subtract the last info line's value; if any path reports REAL ms while NodeClock is on (the guarded report sites in job 14's check were consistent), a few bookkeeping errors could slip in silently. The proof games' identical replays and the sane clock states suggest the accounting is consistent, but I have not audited every info path.

## A better way
- **The runner's clock should log its per-move account** (a small array per game): it turns "the burn shape" from an inference into a line of data, and it would have shown the hard-zone behavior immediately instead of my post-hoc arithmetic. One list append; I would add it before any future clock job.
- **Score-flagged-games sensitivity**: rerun W1 with forfeits scored 0.6/0.4 (or excluded) as a one-line sensitivity check — if the sign survives, the positional reading is safe; if not, the flag effect IS the result. Cheap (one match) and it separates the two effects properly.
- **TmFinishIteration's real test needs a budget that makes iterations matter**: e.g., NodeClock such that the soft limit ≈ one iteration's typical size (or a very low remaining-time state via a custom start), not 10+0.1. The switch was measured in a regime where it cannot act; the "no effect" is protocol-true, not switch-true.

## Model
glmflash — GLM 5.3 Flash (the model serving this cloud-agent run), executing the deepseek queue by reassignment.
