# NNUE and evaluation findings

Scope of this file: full reads of `h512/STATUS.md`, `h512/REPORT.md`, `h512/REPORT_PHASE2.md`, `fair_eval/STATUS.md`, and `fair_eval/REPORT.md` at `fable/standalone-h512-20261111` @ `efb2ff960037087299332bc6a44baea69441a17a`. Job D's report is the same text as on `fable/fair-eval-builds-20261111` only if the blob matches; the blob read is `e1f86ff992a71788b80bbcc584fb58eb182941e0` at path `fair_eval/REPORT.md` on the H512 tip. Parent-branch identity was not separately diffed.

Confidence: high that these files say what is quoted. Low as an independent measurement. No match, bench, or training run was repeated. Nets and exes are local files on the machine the reports call grok-pc, not objects in git.

## Architecture the H512 line actually trained

Standalone net, hidden 512, 8 mirrored king buckets, 8 output buckets by piece count, SCReLU, int16 inference, QA 255, QB 64, eval scale 400. While the v3 option is on, static eval is the net only. The hand-crafted evaluator remains in the binary and is used if `UseNNUE` is false. Build switch `FORGE_NNUE_V3` defaults to 0.

Source of the port, as the report names it: `nnue_v3.hpp`, `nnue_v3.cpp`, `search_v3.cpp` from `fable-fb2-j1`, placed on combo29. Those parent reports are not read yet.

Warm start: FB2 checkpoint, 761,856,000 positions, best loss 0.014713967976147187. The report checks content (re-score, re-export, status file, 130 data-file hashes) and says no reference hash for the checkpoint itself was published.

Data: 271,830,023 training rows from FB2 shards 001-035 excluding 013/014. Selection set 2,000,000 from shards 013/014. Final tests from other shards. Separation is by shard file and position, not by game id. The report says that is weaker than a game split.

## What failed, with the report's reason

| Attempt | Result in the report | Why it stopped |
|---|---|---|
| Phase-1 recipe, no decay, continued to 4.0B | Unseen selection loss 0.014489 at 1B, 0.014481 at 2B, 0.014506 at 4B. Training-row loss kept falling | Over-fit. Paused with its own stop flag. Not a candidate |
| Phase-1 candidate at equal nodes (MN1) | -4.8 Elo, interval -12.5 to +3.0, 3,000 games | Evaluation was not ahead of combo29. The +12.4 at equal time is attributed to 1.198x NPS |
| Decay on factoriser weights `wf` as well as `w1` (arm X3) | Selection loss 0.014915 | Called harmful. Shared piece-square weights |
| Decay 10 on `w1` | 0.014199, worse than decay 0.3 and 1.0 | Too strong |
| Alpha 0.4 instead of 0.25, with decay (X5) | 0.014127 vs 0.014083 | Kept alpha 0.25 |
| Weight averaging of no-decay checkpoints | At best 0.014443 vs candidate 1 at 0.014480 | Gain about 0.000037, then dropped in favour of decay |
| Averaging nets trained with different decay | 0.014954 and 0.014312 | "do not work" |
| Decay 0.3 continued to 7.4B vs candidate 3 | Best checkpoint 0.000006 below candidate 3 | Under the 0.00002 bar. No candidate 4 |
| From-scratch decay 0.3 to 10B | Selection loss 0.013882, level with candidate 3 | Allowed to become a candidate only if 0.00002 better. It was not. Test set 3 not scored. Not played |
| 1024-hidden, same data and recipe, 10B, random start | Loss 0.013800 vs 512-unit 0.013882. Speed 0.8579x (CI 0.8552 to 0.8606, 16 pairs). Match M9 vs candidate 3: -5.9 Elo, interval -14.2 to +2.4, 2,000 games at 10s+0.1s | Pilot only. Report says the wide net's gap to unseen rows is larger, so data is the limit, and the slowdown is not paid back at this clock |
| HalfKA stand-alone 1024 (`fair_eval/REPORT.md` follow-up) | NPS about 0.49x the lock on a different tree. Own match -97.4 +/- 25 over 300 games | Do not spend a gate on these nets as they are. The previous gate exe was also cold-profiled and two locks behind; that unfairness is not why the net lost |
| v2 refresh-from-bias bit (`FORGE_NNUE_V2_FAST` bit 4) | 0.9255x vs 0.9266x ported | No gain |
| Six phase-1 pilots, one seed, 400M | P2 (lr 5e-4, alpha 0.25) beat the existing recipe by 1.08e-5 | Later called inside trainer noise (~0.00002) once that noise was measured. Phase 2 superseded the recipe |

## What the reports treat as the recipe to build on

Decoupled decay on king-bucketed `w1` only, lambda 0.3 to 1.0, after each step `w1 *= 1 - lr * lambda`. Adam, batch 8192, target 0.75 teacher + 0.25 result, cosine from 5e-4 to 2.5e-5, 500 warmup steps, stage ends at 1B, 2B, 4B, 7.4B, 10B. No warm start required for the loss. More passes on this 271.8M-row set add little after 10B (0.000021 from 7.4B to 10B with decay 1.0). The report's next lever is more self-play data, not more passes and not a wider net on the same data.

Candidate 3 screens, all this job's own, Threads 1, Hash 16, UHO book, 12 games at once, original lock exe md5 `c0051c99695f48bf93272d96fe7548c3`:

| Match | Condition | Games | Elo | 95% interval | Time losses |
|---|---|---:|---:|---|---|
| M5 | 6s+0.06s | 2,000 | +66.6 | +58.0 to +75.4 | 3 / 6 |
| M7 | 6s+0.06s, rebuilt exe, GPU idle | 1,500 | +67.3 | +56.7 to +78.0 | 5 / 3 |
| M3 | 10s+0.1s | 2,000 | +57.0 | +48.3 to +65.7 | 7 / 6 |
| M8 | 30s+0.3s, GPU busy, Hash 16 | 1,000 | +53.2 | +41.9 to +64.6 | 1 / 1 |
| MN2 | 250,000 nodes | 3,000 | +54.9 | +47.4 to +62.5 | none |
| M2 | candidate 2, 6s+0.06s | 3,000 | +41.3 | +33.8 to +48.9 | 19 / 25 |

Time losses are attributed to `resource_guard.ps1` suspending `fastchess` for seconds when a thermal latch trips. The reports recompute without those pairs and stay within about 0.7 Elo. They still call the timed runs not a gate. M8 and M9 notes are in `h512/STATUS.md` after the phase-2 report. M9's three late suspensions overlap an audit the owner ordered; the report says the Elo does not move when those pairs are dropped.

Test set 2, scored once after the candidate list closed: candidate 3 loss 0.014070, combo29 evaluator 0.014527, candidate 1 0.014676. Same ranking as the selection set.

Parity: engine, diagnostic search eval, Python integer reference, and GPU scorer agree on 14,000 positions for candidates 1, 2, and 3. Fake-quantised float vs integer stays within 2 cp. Unquantised float does not (max 89 cp on the phase-1 candidate). That is why training is quantization-aware.

NPS is not like-for-like when the tree changes. With candidate 3, quiet ABBA is 1.0952x the lock (CI 1.0931 to 1.0974) at `bench 20`, nodes 12,389,307 vs 13,407,897. Rebuilt exe vs phase-1 exe on the same net is 0.9985x (CI crosses 1) and the same node counts. Author-line rebuild (`Couns`) vs the exe that played M7/M8 is 0.9980x, same nodes. The author line does not change search by node count.

## Job D path costs (same standard: report text, not a new bench)

| Build | Like-for-like note | Figure |
|---|---|---|
| `base_resid` | same tree as the lock | 1.0000 NPS (CI 0.9982-1.0018) |
| INT8, profiled on its path | different tree | 0.9838 at bench 20; 0.9944 at bench 22 |
| INT8 cold profile | same tree as the fair INT8 | 0.4874 |
| v2 KB8 replica | same tree, bit-exact on 12,000 FENs | 0.9266 |
| v2 KB8 fast=7 | same tree, still bit-exact | 0.9358 |
| v2 code path alone (KB1, 1 output bucket) | same tree | 0.9632 |
| King buckets by rank, extra | | about 3.0 points |
| File split to KB8, extra | | about 0.8 points |
| HalfKA 1024 vs its old gate exe | same tree | 1.446x |
| HalfKA 1024 vs lock | different tree | 0.488x |

INT8 acceptance bounds were fixed before the run and passed: max 29 cp (bound 50), mean 3.207 (bound 5), signed mean +1.032 (bound 2.5), 0.083% of positions at 20 cp or more (bound 0.5%). VNNI equals the scalar int8 reference on 12,000/12,000. The bounds are a regression check, not a strength claim. The match figures are in `HANDOFF.md`.

U8 and run 5 cost the same per evaluation as the replica (within 1.5% on the microbenchmark). U8's lower NPS is the search tree. Output buckets added no NPS cost in the layout test. King-bucket refresh is the part the report could not remove; the eight bench positions include three endgames with active kings, so the bench may overstate that cost in games. That was not measured.

## Where candidate 3's net came from

`FABLE_REPORT.md` (blob `7cb6ce90fe3fe5391cab83d1f491bcc5d6111f4d`) is the same file on `fable-nnue-arch` and `fable-fb2-j1`. `FABLE_REPORT_FB2.md` (blob `cfd5464ac23e1a565f9e035f706be02157e3d113`, md5 `9e40983e6a44ed6283c0110d2df243cd`) is the file the H512 report names. Both were read here. Neither report ran a gate. Both say the PC was loaded, so their NPS figures are advisory.

FB1 built the v3 format: 8 mirrored king buckets, factoriser, int16, QA 255, QB 64, standalone or residual. Parity and a 1,000,000-ply incremental walk passed in that report (0 mismatches). A 5-minute train on one ordered shard overfit: holdout loss rose while the training loss fell. Cross-shard CPU runs beat hand-crafted eval and stayed short of AL1 (residual 0.015194 and standalone 0.015743 against AL1 0.014310 on a 1,024,286-row subset). The report's own per-node ratios versus the AL1 path, different trees, loaded PC: residual H512 about 0.83, residual H1024 about 0.74, standalone H512 about 1.17 to 1.19. Those ratios are not the combo29 measurements in the H512 job.

FB2 then trained a standalone H512 on the 271.8M-row split. The file's opening summary still says the run is in progress. The later "Final net" section says it finished: best checkpoint 15, 714.0M positions, exact b0.6 **0.014714** against AL1 **0.014417** on the 200k holdout (gap +0.000297). On the full subset, 0.014629 against AL1 0.014310. The target was not reached. The report refuses a gate. Final-net NPS versus AL1 was 1.158 at depth 16 and 1.111 at depth 20, different trees, loaded PC. The 200 games (60-48-92) are marked as a legality check, not Elo. This is the warm start H512 continued, and H512's later weight-decay runs are what first went below the combo29 evaluator on unseen rows. Do not describe FB2's net as a strength win.

Other FB2 results that are not strength:

- Four search options (`CorrHistV2`, `SingularV2`, `LmrTableV2`, `TtPruneV2`): 2,500 self-play games, 0 errors, no match against a baseline.
- `TimeManV2`: 0 flag losses in the simulator and in 220 real-clock games. No Elo.
- `SmpV2`: not distinguishable from the lock at 2 or 3 threads. Two Threads-2 repetitions gave geometric-mean wall ratios 0.970 and 0.909. Keep both. No speed claim.
- A second layer of 16 units improved a float holdout at equal positions (0.015759 vs 0.016088 at about 40M; 0.015417 vs 0.015729 at about 82M), one seed, not implemented in the engine. H1024 saw half as many positions per second on that CPU. Sixteen king buckets were slightly behind eight at that budget.

The 200k FB2 holdout (AL1 at 0.014417) and the older 1M-row subset (AL1 at 0.014310) are different sets. The H512 selection loss 0.014311 for s198+HCE is a third set. Do not subtract them from each other.

## October width and int16 notes, from the Sol index only

`opus-summary` @ `e89d2af1c5f3b9268836c8b949fb4f3951de6a29`, `SOL_LEFTOVERS_PROGRESS.md`, was read as an index. Each line points at a job report that was not opened, except where this ledger already names a full read. Treat the numbers as that index's claims.

- `opus-sol-SC4` @ the progress line `25ee3585` (full tip is in `branches/HEADS.tsv`): zero-padded nets, identical trees, CPU NPS versus H256 of about -9.5/-9.8% at H512, -15.7/-17.6% at H768, -22.8/-23.7% at H1024 (depths 16/20). The index says the int16-weight path did not remove that width cost. This is a different measurement from FB1's standalone speedup, which drops the hand-crafted eval, and from the H512 job's 0.858x for a real 1024-unit net versus a 512-unit net.
- `opus-sol-S21` @ `f7731fe8e552740b347996e31303c552b8c13b18`: the index says every one of 13 nets overflows int16 on 28-86% of 200k positions. The v3 loader later rejects a file that could overflow. Read S21 before changing quantisation. This index did not.
- `opus-sol-SA2`: `NnueInt16` on is about 10-13% slower in the index's advisory NPS, and the option-off binary still costs about 0.4-0.5% on a quiet runner. `HistRework` (A1) costs about 0.8-1.0% with the option off. `NetScale` (S41) does not, in that same off-path check.
- `opus-O2` @ `82282b09f606d7919028d54f7118f29897432786`: the summary says bit-identical kernels and +3.3% bench NPS, and that a +10% target was not reached. That sentence is the summary, not O2's report.
- S14 `FORGE_NOZERO_MOVE_BUFFERS`: node-exact, about +1.25% to +2.70% CPU NPS on a quiet runner, and the index says the +2% lower-bound rule was not met.
- S30: the index says loss has not predicted Elo, and that an early H1 (G104) was not repeated by G104c. Same warning as candidate 1's clock Elo versus its equal-node result.

`opus_round1_20261027.tar.xz` (22.2 MB) on `opus-summary` was not opened. `FABLE_REVIEW_OPUS.md` was not read.

## Measurements that are easy to misuse

- Selection loss is not Elo. Candidate 1's loss was worse than combo29 and it still scored +12.4 on the clock.
- A lower loss for the 1024-unit net did not win its match against the 512-unit net.
- PGO coverage of zero entries in the INT8 functions means the profile never ran that path. It does not mean the kernel is slow.
- Builds are not byte-reproducible. Node counts matched on a second INT8 build; the exe md5 did not.
- Linux NPS is not a speed result. `forge-combo29/README.md` says Elo comes only from SPRT on the owner's PC.
- The 200-game FB2 smoke match (+41.9 +/- 31.8) is a pipeline check. The report excludes it from the result.
