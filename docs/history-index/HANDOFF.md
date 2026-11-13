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
- H512 candidate 3 changes the search tree (different bench node counts from the lock). Its reported equal-node gain is an evaluation result, not a search-patch result. Do not add it to a speed-lock stack.
- Candidate 1's +12.4 Elo at 6s+0.06s disappeared at equal nodes (-4.8, interval crosses zero). A search or speed change that only wins on time can be the same pattern. Ask for an equal-node or fixed-node screen before treating a short-clock Elo as strength.
- `fable52-search-gap-20261109` @ `56a76b153bb8` has `fable_search_gap/NO_QUALIFIED_GAP.md`. Not read yet. Do not start a new search-gap search until that file and `FALSIFICATION.md` are read. They are the next batch in `RESUME.md`.
- Threads above 1 on the standalone H512 path were not tested. SMP conclusions from October GrokChess notes are a different engine (JavaScript, `grokchess_1745_full_source.txt` on `main`). Six GrokChess research branch names point at `main` and contain no newer source.

## Conflicts kept open

| Topic | Report A | Report B | How to hold both |
|---|---|---|---|
| H512 phase-1 Elo | +12.4 at 6s+0.06s, and a 1.20x NPS figure | Equal nodes -4.8; the report says the Elo was speed | Use the equal-node number for evaluation quality and the timed number only as a combined screen |
| H512 speed | "about 20% faster" with candidate 1 | 1.095x NPS with candidate 3, different tree | The speed ratio depends on the net. Do not copy the 20% figure forward |
| Wider nets | 1024-hidden H512 has a lower loss than 512 (0.013800 vs 0.013882) | Same net vs candidate 3 at 10s+0.1s is -5.9 Elo, and it searches 0.858x as many nodes | Loss improved and the match did not. The report's own reading is that the data, not the width, is the limit, and the slowdown is paid at this clock |
| HalfKA 1024 | Older gates around -86 to -124 Elo on a cold, slow exe | Job D's own 300-game match on a faster exe: -97 +/- 25 | The build was unfair and the net still lost on the fair exe. The 300-game interval is wide |
| INT8 speed | Older note "ON about 0.5x" | Fair profile 0.984x at `bench 20`, 0.994x at `bench 22` | 0.5x is the cold profile. The kernel is close to the lock on NPS and is lossy (max 29 cp, mean 3.2 cp on 12,000 FENs) |
| v2 KB8 "about 1.0x" | An older advisory on an older lock | 0.927x on combo29 with a correct profile, bit-exact | Use the combo29 measurement for the current lock |

## Already in progress or paused inside the reports

- No-decay H512 run paused at 4.0B presentations, described as resumable, and not a candidate.
- From-scratch decay-0.3 net at 10B reaches the same selection loss as candidate 3 and was not scored on a test set, not parity-checked, and not played.
- Test set 3 was built and not scored. Match M6 was declared and not played. Arms `swa_C1`, `ema_E1`, and X4 were declared and dropped.
- Job D built `v2kb8_r5_fast`, timed it, and did not play it.
- `forge-combo29/docs/context/HANDOFF.md` says three speed candidates were prepared and not built: no Windows exe, no pins, no ABBA. Historical logs in that handoff are labeled as not results for those candidates.
