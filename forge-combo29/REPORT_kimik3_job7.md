# kimik3 job 7 report: the finish rule at a second seed, at 4× depth, with a smaller divisor — and exact stop reasons

**Headline.** `TmFinishIteration`: the honest replication shrinks the gain, and 4× the nodes inverts it.
U1 on the "second seed" *replayed T1's games exactly* (W341-L279-D380, digit-identical: in my runner the seed
only reorders pairs; the 200 opening pair contents are fixed by the book — itself a 1,000-game determinism
proof, but not a replication). U1b, my fix with disjoint openings 201-400 of the same UHO book, seed 7511:
**−3.8 [−19.0, +11.3]** — T1's +21.6 does not replicate at that size. Pooled T1+U1b (2,000 independent games,
openings 1-400): **+8.9 [−2.0, +19.8]**. At four times the nodes a move (`NodeClock 400`, mean ~94k nodes a
move) the gain **inverts: −22.0 [−40.9, −3.3]** (600 games). On top of the rule, `TmSoftDivisor 18` vs 22
(both sides finish on): **−13.2 [−29.5, +3.0]**, zero forfeits either side. U4 was cut. Part C's `TmLog`
prints the exact stop reason per search behind a switch (off = unchanged, proven); its first use counts
A 61 / B 338 exact hard-cap stops per 100 games against the runner reconstruction's 8/55 on the same games —
**my job-6 "hard stops" column undercounts ~6×** (the 5×-less claim survives: exact ratio 5.5×).
Node-time forfeits this job: U1 0/0, U1b 0/0, U2 0/0, U3 0/0 (on-side/off-side).

## The one table (jobs 6 and 7, all 10+0.1 on the node clock, Threads 1, Hash 16)

| match | A vs B | NC | games/seed | W-L-D (A) | Elo [95 %] | nodes/move A | nodes/move B | hard A/B | forfeits A/B |
|---|---|---|---|---|---|---|---|---|---|
| T1 | TmFinishIteration | 100 | 1000 / 7501 | 341-279-380 | +21.6 [+6.0, +37.3] | 23,315 | 24,924 | 104/534 | 0/0 |
| T2 | TmNodeShare | 100 | 1000 / 7502 | 298-326-376 | −9.7 [−24.8, +5.3] | 24,763 | 25,368 | 367/476 | 0/0 |
| T3 | both | 100 | 1000 / 7503 | 294-294-412 | +0.0 [−15.9, +15.9] | 22,863 | 25,291 | 93/413 | 0/2 |
| T4 | TmStability | 100 | 1000 / 7504 | 289-312-399 | −8.0 [−21.8, +5.8] | 26,093 | 25,818 | 623/334 | 0/0 |
| U1 | TmFinishIteration | 100 | 1000 / 7511 | 341-279-380 | +21.6 [+6.0, +37.3] | 23,315 | 24,924 | 104/534 | 0/0 |
| U1b | TmFinishIteration, openings 201-400 | 100 | 1000 / 7511 | 304-315-381 | −3.8 [−19.0, +11.3] | 23,950 | 25,864 | 100/427 | 0/0 |
| U2 | TmFinishIteration | 400 | 600 / 7512 | 156-194-250 | −22.0 [−40.9, −3.3] | 90,240 | 97,261 | 22/79 | 0/0 |
| U3 | finish+divisor18 vs finish+divisor22 | 100 | 1000 / 7513 | 282-320-398 | −13.2 [−29.5, +3.0] | 24,386 | 23,468 | 202/117 | 0/0 |
| U4 | share on, both sides finish on | 100 | cut | — | — | — | — | — | — |

U1's row equals T1's because U1 replayed T1's games (see headline); U1b is the true second seed. The
pooled T1+U1 line sometimes quoted (+21.6 [+10.5, +32.6] over 2,000 games) double counts the same games and
is not reported as a result. The `hard A/B` column is the runner's ≥ 95 %-of-hard reconstruction everywhere,
including U1-U3 — per Part C it undercounts the true hard-cap stops by roughly 6×; only the tally below is
exact. U2 detail: soft share 0.78 (A) vs 0.98 (B). U3 detail: option line
`option name TmSoftDivisor type spin default 22 min 5 max 80`; soft share 1.02 (div18) vs 0.88 (div22);
the "handful of forfeits" watch: zero.

## Part B (reading): why the two switches cancel

`TmFinishIteration` alone +21.6, `TmNodeShare` alone −9.7, together 0.0. From the code of the job-6 tree
(search.cpp): the finish rule samples iteration durations (lines 2409-2411, recorded 2571-2574) and at each
iteration end asks `iteration_will_not_finish(prev, last, left_ms)` (line 2630), where `left_ms` is the
distance to the *current* soft deadline (lines 2627-2628). `TmNodeShare` replaces that deadline's basis every
iteration: `soft_basis` starts as `soft_limit_ms_` (line 2604), and with the switch on it becomes
`decision.soft_ms` from `decide_node_share_timing(...)` (lines 2613-2623) — lengthened up to 1.5× when the best
move holds under half of the root-node share, shortened down to 0.5× over half (tm_node_share.hpp:40-53), and
capped at `hard_ms`. Three effects follow. (1) In contested positions the share rule stretches the deadline, so
`left_ms` grows and the finish rule's "cannot finish" test stops firing — the doomed iterations the finish rule
would have banked are now started, and the banked time is spent: that is exactly the +21.6 mechanism being
switched off where it pays. (2) In one-sided positions the share rule shortens the deadline, so the plain
`elapsed >= soft_basis*factor` stop (line 2625) fires before the finish rule is consulted — the rule never sees
those iterations. (3) The finish rule's duration pair (prev, last) is measured across iterations that ended at
*different* share-adjusted deadlines, so its growth estimate is no longer a property of depth alone. Lowest
nodes a move of all matches (22,863) is the visible sum of (1) and (2). No patch.

## Part C: the stop reason (`tmlog.patch.txt`, against the job-6 tree)

New check option `TmLog` (default false). With it on, every finished search prints one line
`info string stop <soft|hard|finish|nodes|depth|other>`. Changed places by file and line (job-6 tree):
- `src/search.cpp`: `bool TmLog = false;` (line 109); `const char* stop_reason = "depth";` declared with the
  loop state (line 2212); the reserve-exhausted emergency entry sets "other" (line 2335); reasons at the loop
  exits — mid-iteration abort after the aspiration window (lines 2458-2460: nodes/hard/other from
  `stopped_by_nodes_` and the hard-limit comparison), the MultiPV abort (lines 2563-2565, same rule),
  mate-found (line 2578, "other"), soft node limit (line 2581, "nodes"), `should_stop()` (lines 2583-2588,
  nodes/hard/other), the soft clock stop (line 2644, "soft"), the finish-rule hold (line 2658, "finish");
  the print guarded by `tune::TmLog && emit_info` after the loop (lines 2666-2670).
- `include/forge/search.hpp`: extern (line 309). `src/uci.cpp`: option line (line 235), parse branch
  (lines 441-444).

Proof off = unchanged: bench 11/13/16 = 312,866 / 862,329 / 3,024,920 on the patched build; 20 games at
`NodeClock 100`, seed 7500, patched(off) vs the job-6 build — identical move for move (`logoff20.txt` ==
job 6 `base20_run1.txt`). Functional spot checks: `go nodes 20000` → "stop nodes", a clock search → "stop
soft", `go depth 5` → "stop depth". With the switch on, the only added work is one line of output after the
search loop has ended, so it cannot change play under the node clock.

Use once: 100 games of T1's form (A: TmFinishIteration on, B: off; both sides TmLog on, seed 7511, openings
1-200). Per-search stop reasons, summed over the four shards; each side's reasons sum to its move count
exactly (A 6,042, B 6,038), so every search is accounted for:

| side | soft | finish | hard | depth | nodes | other |
|---|---|---|---|---|---|---|
| A (finish on) | 3,727 (61.7 %) | 2,186 (36.2 %) | 61 (1.0 %) | 68 (1.1 %) | 0 | 0 |
| B (finish off) | 5,641 (93.4 %) | — | 338 (5.6 %) | 59 (1.0 %) | 0 | 0 |

What this says, and the correction it carries:
- The finish rule fires on 36.2 % of A's searches; B, denied the rule, ends 93.4 % of searches on the plain
  soft stop and slams the hard cap 5.5× as often (338 vs 61). This is the +21.6 mechanism counted exactly.
- **Correction to job 6:** its "hard stops" column was a runner-side reconstruction (used ≥ 95 % of the
  computed hard limit). On these same 100 games that reconstruction counts 8 (A) and 55 (B); the exact
  mechanism counts 61 and 338 — a 6-8× undercount, and the T1-T4 hard column (e.g. T1's 104/534 per 1,000
  games) should be read with that factor. The job-6 ratio claim survives the exact count (5.5× less).
- `depth` means the loop ran to `max_depth` = `clamp(min(limits.depth, mate_depth), 1, 64)` (search.cpp:2230)
  with no stop rule firing — dead endgames whose whole tree to depth 64 fits the budget, ~1 % of searches.
  My mid-job suspicion that these were reserve-exhausted depth-1 emergencies was wrong: the emergency path
  now sets "other" at entry (line 2335) and it fired zero times, as did mate breaks and external stops.
  `nodes` is zero because clock play carries no node limit.

## Files of the repository opened

search.cpp, search.hpp, uci.cpp, tm_node_share.hpp, tm_finish.hpp (forge-combo29/), plus the job file and my
job-6 report.

## Stamps

Job file read 22:10; U1 launched 22:07, complete 22:15; U2 launched 22:16, complete 22:32; TmLog patched and
off-identity proven 22:16 (built g++; the default c++ is clang and cannot link -lstdc++ here), emergency-path
relabel rebuilt 22:49; U1b complete 22:39; U3 complete 22:49; TmLog tally complete 22:50; report written
22:52-23:0x; all UTC 2026-11-15.

## What I did not do

- U4 (TmNodeShare with both sides on the finish rule): cut — U1's exact-replay discovery cost a match slot,
  and U1b/U2/U3 took the budget; no games were run for it.
- No second seed for U2/U3; U2's inversion is one 600-game seed.
- The pooled T1+U1 interval is mentioned only to be disclaimed (U1 replayed T1's games); the reported pool is
  T1+U1b, independent openings.

## What I am not sure about

- Whether `NodeClock 400`'s inversion is about depth itself or about budget shape: at NC400 the average move
  is ~94k nodes and the finish rule still fires, but the iterations it skips are worth more; one seed of 600
  games cannot separate "the rule misprices deep iterations" from "openings 1-200 at NC400 favour the off
  side". A second U2 seed and a NC200 point would settle the shape.
- The divisor-18 bundle could not gain by mechanism (the bank is small next to 4 % of remaining per move), so
  its −13.2 [−29.5, +3.0] says more about the divisor than about the bundle.
- The U1b openings (201-400) are disjoint from T1's but from the same book; a different book could move both
  estimates.

## A better way

Match runners should derive the opening set from the seed too (my pair contents were seed-invariant: the seed
shuffled only the order, so a "second seed" replayed the first match game-for-game — caught only because the
W-L-D came out digit-identical). One line in the report of every future seed should be a hash of the game
list; identical hashes mean identical games, whatever the seed says. And log the stop reason always-on in the
engine: the exact counts above cost one patch and immediately caught a 6× reconstruction error.

Model: Kimi K3.
