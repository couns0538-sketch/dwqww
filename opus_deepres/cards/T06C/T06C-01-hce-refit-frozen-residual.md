# T06C-01-hce-refit-frozen-residual: re-fit the HCE table with the residual net frozen inside the loss
Status: COMPLETE

## Source
- Ethereal b552e36 "Tune all of the NORMAL terms following the NN additions" (commit text, OpenBench 7551 / 7552):
  https://github.com/AndyGrant/Ethereal/commit/b552e36f88 , http://chess.grantnet.us/test/7551/ , .../test/7552/
- The net it was re-tuned under: 513a93c, a [224,32,1] pawn + king net that augments the HCE; its cp output goes through
  a sigmoid "after being offset by a static evaluation" (Forge's residual form): https://github.com/AndyGrant/Ethereal/commit/513a93c232
- Data freshness (HCE-only engines): Ethereal 6771685, Clockwork 2844edc (links: notes/T06C/TABLE.md row 4).
- Missing: whether Ethereal's tuner kept the net output inside the sigmoid (not in the commit text; source not read).

## Licence
Ethereal GPL-3.0 (LICENSE at b552e36f88 and 513a93c232), Clockwork AGPL-3.0 (at 2844edc8c0): ideas only - commit titles,
messages and test pages read, never source; no constants carried over.

## Mechanism
Own recipe: one coordinate-descent step on the objective the residual net was trained on. Keep the lock net fixed and
fit only the HCE table (639 mg/eg pairs) on the rows the net saw: pre-sigmoid K (HCE(x) + net(x)) / 400, K fixed at
the net trainer's 2.25 (no re-scan, so HCE and net cp scales stay matched), target 0.6 sigmoid(K score / 400) + 0.4
result, MSE (trainer b 0.6 = tuner lambda 0.4). Given a row's coefficient trace (phase, scale kept per row) the HCE
is linear in the table, so the frozen net is one per-row constant (white point of view) added before the sigmoid and
the table gradient is the existing one taken at the sum: the table only moves where HCE + net is still wrong. Never
ship a stand-alone re-tune (net absent) with the old net: the net already corrects the old table's errors, a table
that fixes them too double-counts. Data: own self-play FPOS train shards (013/014 out), subsampled for RAM; FPOS has
no castling / ep / clocks; eval.cpp and the 768 net inputs read none (hce_dump re-makes the production .hce exactly).

## Forge fit
Parts exist, the joint fit does not. forge_has.sh 'texel|eval_params|EvalParam': include/forge/eval_params.hpp:10
(layout shared with the tuner), src/eval_params.cpp:8-11. Tuner tools/tune/texel.cpp (read in the src_h256_e12 tree;
the lock tree holds only include/ and src/): Adam on a coefficient trace, own K scan (:181-196), no per-row net term.
Lock table src/eval_params_table.inc:1 (61,536 games, 4.67M quiet positions, 10k nodes) is byte-identical to
h256_e12's (no table change between that tree and the lock; a later re-fit was not found). search.cpp:620 sums
HCE + net for every static eval; SEE uses fixed SeeValue (board.cpp:17); pawn cache eval.hpp:52-65. TRIED_GATES: 0 of
110 rows match texel / hce / eval_param / table / psqt. T06-02 (two runtime weights) is a 2-scalar special case: gate
T06C-01 alone. Change: tuner per-row net column + fixed --k; row writer = notes/T06/FIT_RECIPE.md step 1; new table.

## Expected gain
Ethereal b552e36: STC +6.75 +- 4.22 (10+0.1s, Threads 1, SPRT [0,4], LLR 2.99, 10,240 games), LTC +7.06 +- 3.88
(60+0.6s, LLR 2.96, 8,464 games); data 3 x ~10M self-play positions (1s/2s/4s games) + 12.5M FRC. That net saw pawns
and kings only, so most HCE terms had no net covering their errors; Forge's net sees all 768 piece-squares and was fit
to this table's errors - expect much less. Data freshness (HCE-only): Ethereal 6771685 +10.51 +- 5.37 / +12.75 +- 5.34
(5,920 / 4,416 games); Clockwork v4.1 data +6.67 +- 3.62 / +11.88 +- 4.80 (8+0.08 / 40+0.4, 11,722 / 5,736 games).
Forge estimate: 0 to +3 Elo **UNPROVEN**. Filter: lock b0.6 holdout 0.014310 (HCE alone 0.017059); drop unless refit
table + lock net is clearly below 0.014310 (a filter only - loss has not predicted Elo, S30).

## Effort
Crew ~6 h: tuner net column + fixed K ~1.5 h, row writer (FPOS -> trace + lock-net cp) ~2 h, option + pins ~1.5 h,
holdout scoring ~1 h. CPU ~2-4 h fit at <= 3 threads Idle (own estimate ~0.3-0.4 KB per row in RAM, so <= ~15M rows
under the 7 GB guard); STC SPRT at 430-502 games/h, 3,000 games = 6-7 h, +6-7 h one extension if positive [last round, coordinator, unverified], LTC ~3x per game. GPU none.

## Test plan
1. Holdout: S31 scorer, lock net + .hce of the refit table (hce_dump rebuilt) on holdout_013_014_s16; filter above.
2. Eval scale: mean |eval| and fitted slope, refit vs lock (margins assume the lock scale; Ethereal re-tuned margins
after its eval tunes, c495be4 +4.66 / +2.49). 3. OFF bench / perft = lock pins, ON bench differs, 2-minute smoke.
4. UHO SPRT [0,5] at STC vs the lock, then LTC. A margin SPSA only after a pass.

## OFF-by-default design
UCI string `HceParamsFile`, default empty = compiled lock table, params::table untouched -> OFF node-identical (bench
pins). Set: parse the file (exactly 639 entries, else reject over UCI and keep the lock table), copy into params::table
(a live extern that tools may modify), clear pawn caches (Worker::clear, search.cpp:575-576). No speed cost.
