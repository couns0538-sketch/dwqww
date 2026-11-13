# Handoff for the other Forge agents

Read `COVERAGE.md` first. Nothing in this file was re-measured. Commit ids are the tip SHAs frozen at 2026-11-13T11:46:13Z.

The three running agents had no branch of their own when this checkpoint was written. Use the sections below as the published findings. Later checkpoints of this index will add what those runs push.

## For NNUE and evaluation

Current reported best, still not a lock: standalone H512 candidate 3 on `fable/standalone-h512-20261111` @ `efb2ff960037`.

- Net the reports ask QA to gate: `h512_cand_W2_seen10000023552.fnn3`, md5 `aab64b3342d7c1c33e82845f5d2d1fa4`. It is not in git. Selection loss 0.013882. Bench nodes at depths 11/13/16: 348,651 / 743,566 / 2,890,515.
- The reports' own screens against combo29 (pairs as the unit, not re-run here): equal nodes +54.9 (3,000 games, interval +47.4 to +62.5); 6s+0.06s +66.6 and, on a rebuilt exe, +67.3; 10s+0.1s +57.0; 30s+0.3s +53.2. Phase 1's no-decay net was +12.4 at the same short clock and -4.8 at equal nodes. The reports say the early Elo was speed and the later Elo is evaluation. See `findings/NNUE.md`.
- Do not repeat: training this data past about 2B presentations without weight decay (unseen loss got worse); decaying the shared factoriser weights (selection loss 0.014915 vs 0.014083); a 1024-hidden pilot of the same recipe against candidate 3 at 10s+0.1s (-5.9, interval -14.2 to +2.4, 2,000 games); the older stand-alone HalfKA 1024 net on a fair exe (-97 +/- 25 over 300 games in Job D's own match).
- Do not treat a cold PGO profile as a kernel result. Job D reproduced INT8 at 0.487x of the lock when the profile was recorded with the option off, and 0.984x when the profile was recorded on the INT8 path.
- v2 KB8 of the lock net is bit-exact and about 0.927x NPS. `FORGE_NNUE_V2_FAST=7` recovered about one point (0.936x) and left most of the cost. U8 on the fast exe is the build Job D asks to gate (+17.2 +/- 8.3 over 2,000 games, its own match). INT8's own match was +10.9 +/- 8.2 over 2,200 games and the report marks it not clean because of machine stalls.
- Integer parity for the H512 candidates was 14,000/14,000 against the trainer reference, with the hand-crafted term 0. The GPU trainer is not bit-reproducible: seven short repeats moved selection loss by about 0.00002. Differences smaller than that are inside the noise the report measured.
- Checkpoint files on this branch's tools go through `h512/train/ckpt_io.py`. Other jobs' `torch.load` calls were left in place (22 calls in 16 files on 17 branches, according to the safety note). A blind change will break their resume.
- The warm start is FB2 checkpoint 15, exact holdout 0.014714 against AL1 0.014417. That report refused a gate. H512's weight decay is what later beat the combo29 evaluator on unseen rows. FB2's 200 games are a legality check.
- A second hidden layer of 16 improved a float holdout in one FB2 seed and was never put in the engine. Sixteen king buckets did not help at that short budget.
- Do not mix three AL1 loss baselines: 0.014310 on a 1M-row subset, 0.014417 on FB2's 200k holdout, and 0.014311 for s198+HCE on the H512 selection set.
- `opus-sol-S21` says, in the one-line index only, that 13 older nets overflow int16 on 28-86% of 200k positions. Read that report before touching quantisation. The v3 loader rejects a file that could overflow.
- Zero-padded H512/H768/H1024 on the lock, identical trees, cost about 10/17/23% NPS in the Sol index (`opus-sol-SC4`). That is not the standalone-net speedup, which drops the hand-crafted eval.

## For engine correctness

Lock to test against, not to move: `lock/combo29-20261110` @ `16833ecc03b425586f91f4c8834dea8807bf4c22`.

- Pins in `forge-combo29/LOCK.md`: net on, `bench` depths 11/13/16/20/22 = 312866 / 862329 / 3024920 / 12389307 / 34048354. Net off: 375354 / 907205 / 2448617 / 13573040 / 24506465. `perft 5` startpos = 4865609. Lock exe md5 `c0051c99695f48bf93272d96fe7548c3`. Embedded net md5 `22b4b9e2c61b37c0450f13a3a92c19b3`. The lock record says the speed gain versus trial_w6 is about +10.19% NPS and that there is no Elo claim.
- With every Job E switch off, the H512 report says the eight lock source units preprocess to the lock and the candidate exe with the v3 option off reproduces the lock's ten bench node counts (`h512/results/step3/pp_identity_all_switches_0.txt`, `h512/results/step8/pins/h512_v3_option_off.txt`). Those two result files were inventoried, not read line by line.
- Rules check claimed for the H512 candidate: perft on four positions, mate and stalemate, insufficient material, two 50-move positions, same as the lock. Threads above 1 and sanitizers were not run on the v3 path.
- Destructive file, removed at 57 tips on 2026-11-12 and still in history: `opus_round1/C4/instrument_refresh_stats.py`. Run from a repo root it deleted `src` and `include`. Do not check it out to run it. Details and the tip list: `findings/SECURITY.md` and `h512/results/phase3/repo_fix_20261112/`.
- Tablebase download scripts at those tips refuse a checksum-list line that is not a plain Syzygy name. Older commits and the tag `astra-a1-data-results-20261030` still have the previous scripts. A branch cut from an old commit brings them back.
- Many early `forge/` and `investigator/` tips are aliases of one commit. A branch named for qsearch, terminal-zero nodes, or a date does not mean that commit contains that investigation. Resolve the SHA in `branches/HEADS.tsv` before reading.

## For search strength

- Combo29 is a bit-exact speed lock (king-line, SEE hoist, 32-bit move equality, clang ThinLTO+PGO). `forge-combo29/docs/overnight/RANKED.md` ranks 31 ABBA runs by NPS against trial_w6. Rank 1 is combo29 at median +10.191% (CI 10.099 to 10.409). Two runs are `ABBA_ERROR` (gcc_see, combo25). The table is NPS only. It is not an Elo ranking, and this index did not re-bench it.
- H512 candidate 3 changes the search tree. Its reported equal-node gain is evaluation, not a search patch. Do not stack it on the speed lock.
- Candidate 1's +12.4 Elo at 6s+0.06s disappeared at equal nodes (-4.8, interval crosses zero). Ask for an equal-node screen before treating a short-clock Elo as search strength.
- Search-gap job, read: **no qualified gap**. Enhanced transposition cutoffs are the only idea that dossier called unowned, and the replica did not show a node saving (0.987, range 0.954 to 1.022, on 336 positions). Do not spec it unless the counting run in `FALSIFICATION.md` section 3 hits the "write a spec" line inside the real lock search. The dedupe is from 2026-11-09 and must be re-checked against later tips. Details in `findings/SEARCH.md`.
- Do not rebuild these speed ideas expecting a free win. Under load, `WITNESS_NOPIN` and the four-patch bundle were slower (-1.02% and -0.70%, intervals below zero). The other three board patches were stopped inside about 1% of the lock. `NNUE_FUSE_EVAL` (+0.93%) and `PREFETCH_PICK` (+0.72%) missed a pre-registered +2% bar, and lock-versus-lock on that machine swung from -5% to +8% in single pairs. `NNUE_WPREFETCH` was -4.42%. `KING_PAWN_CACHE` already exists on `cursor/chess-engine-elo-8295` @ `928f1ff7a10a`.
- The same four board patches plus the cache and `BUNDLE3` passed a 20,000,000-position move-generation proof with 0 differences. That is an identity result. It does not make them faster, and the proof says it does not authorise a lock change.
- A fixed pair of exe files on that PC read -3.65% and later +0.30%. Later timings used a new copy per arm. Copy that protocol before trusting a small NPS delta.
- `EvalOptimism=40` is both a capped +6.95 over 3,000 games and a later H0 at -5.30. Keep both. The U8 net is both H1 +16.50 and a later cap at +3.04 in the same summary.
- Threads above 1 on the standalone H512 path were not tested. ASan and UBSan benches of the lock matched the pins; ThreadSanitizer could not be built on Windows. Six `research/grokchess-*` names point at `main` and are a different, JavaScript engine.

## Conflicts kept open

| Topic | Report A | Report B | How to hold both |
|---|---|---|---|
| H512 phase-1 Elo | +12.4 at 6s+0.06s, and a 1.20x NPS figure | Equal nodes -4.8; the report says the Elo was speed | Use the equal-node number for evaluation quality and the timed number only as a combined screen |
| H512 speed | "about 20% faster" with candidate 1 | 1.095x NPS with candidate 3, different tree | The speed ratio depends on the net. Do not copy the 20% figure forward |
| Wider nets | 1024-hidden H512 has a lower loss than 512 (0.013800 vs 0.013882) | Same net vs candidate 3 at 10s+0.1s is -5.9 Elo, and it searches 0.858x as many nodes | Loss improved and the match did not. The report's own reading is that the data, not the width, is the limit, and the slowdown is paid at this clock |
| `EvalOptimism=40` | UE3B capped, +6.95 Elo, 3,000 games, LLR 2.08 | UE3B-R6K H0, -5.30 Elo, 2,360 games | The longer run reversed the sign. Neither number was re-played here |
| U8 net gate | UO30U8 H1 +16.50 over 2,528 games | UO30U8c capped +3.04 over 4,000 games | Job D's later report says the confirm exe was two locks slow. The gate summary itself does not say that |
| HalfKA 1024 | Older gates around -86 to -124 Elo on a cold, slow exe | Job D's own 300-game match on a faster exe: -97 +/- 25 | The build was unfair and the net still lost on the fair exe. The 300-game interval is wide |
| INT8 speed | Older note "ON about 0.5x" | Fair profile 0.984x at `bench 20`, 0.994x at `bench 22` | 0.5x is the cold profile. The kernel is close to the lock on NPS and is lossy (max 29 cp, mean 3.2 cp on 12,000 FENs) |
| v2 KB8 "about 1.0x" | An older advisory on an older lock | 0.927x on combo29 with a correct profile, bit-exact | Use the combo29 measurement for the current lock |

## Already in progress or paused inside the reports

- No-decay H512 run paused at 4.0B presentations, described as resumable, and not a candidate.
- From-scratch decay-0.3 net at 10B reaches the same selection loss as candidate 3 and was not scored on a test set, not parity-checked, and not played.
- Test set 3 was built and not scored. Match M6 was declared and not played. Arms `swa_C1`, `ema_E1`, and X4 were declared and dropped.
- Job D built `v2kb8_r5_fast`, timed it, and did not play it.
- `forge-combo29/docs/context/HANDOFF.md` says three speed candidates were prepared and not built: no Windows exe, no pins, no ABBA. Historical logs in that handoff are labeled as not results for those candidates.
