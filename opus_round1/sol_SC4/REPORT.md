# S-C4 (G-C4) Hidden 768-1024 plan — DONE (plan + measured width cost; UNPROVEN, no net trained)

`SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 43 ("S-C4 hidden 768-1024 plan (only after S-A4 locks)");
`OPUS_TEST_PLAN.md` row 16 (G-C4, srand 610323748).
- **Branch:** `opus-sol-SC4` = `d4f4312` + `0d99f02` cherry-picked (`5fb0b5a4`) + this job.
- **Scope:** plan and measurement only. No engine source change on the branch: the wider builds are scratch builds of
  zero-padded nets. `[skip ci]`, no GPU, nothing queued.

## Acceptance
| item | result | evidence |
|---|---|---|
| plan for H768-1024 after H512 locks | **DONE** | `forge_sol_SC4_hidden_768_1024_plan_20261027.md`: preconditions (H512 lock, int16 path), engine/trainer work, decision rule, width ladder at equal data, gate with srand 610323748 |
| NPS cost of width, measured | **DONE**. CPU-time NPS vs H256, d16 / d20: H512 −9.50% / −9.75%; H768 −15.70% / −17.62%; H1024 −22.82% / −23.71% (95% CIs in the plan). Node time grows linearly, about +10.1% per extra 256 units | `logs/step4_nps_ab.log` (ABBA, 6 runs per build per depth, Idle) |
| measurement is clean (same tree) | **PASS**. The zero-padded H1024 build passes every lock pin (bench d11-d22, perft, kiwipete: `uci_check --full` ALL OK). All 72 timed runs have the lock's node counts. The H256 rebuild differs from the lock exe only in the 6 PE header bytes | `logs/step3_identity_h1024.log`, `logs/step4_nps_ab.log`, `logs/step2_builds.log` |
| builds | **PASS**. Box recipe with the hidden size as a variable; FMA 0 and 0 warnings for H256/512/768/1024 | `logs/step2_builds.log`, `logs/step2b_build_wrapper.diff` |
| queue lines use only existing v3b arguments | **PASS**. 5/5 parse with the unchanged v3b parser (positive control: f070 reproduces its settings dump); 2/2 negatives rejected (`--shape 768.0`, `--epoch-positions`) | `logs/step7_dryparse.log`, `logs/step7_dryparse.json` |
| tools tested | **PASS**. `test_opus_sc4.py` 5/5, including a float forward of the engine's form that is equal before and after widening; planted bugs 5/5 caught | `logs/step5_tests.log`, `logs/step6_mutation_check.log` |

## Findings
1. **Width cost is linear, about 10% of node time per 256 hidden units, on the float path.** So the width-dependent NNUE
   work is about 10% of node time at H256 (S37's microbench: update + output about 97 of 403 ns per search eval; not
   every node evaluates).
2. **On the float path, H768-1024 is unlikely to pay.** Their speed loss is 0.27-0.38 speed doublings. At an assumed
   50-100 Elo per doubling (ESTIMATE) and S44's 5 Elo per 1e-4 b0.6, they would need 2.7e-4 to 7.6e-4 better holdout
   b0.6 than H256 at equal data. That is more than a whole doubling of the training data gives (1.65e-4).
3. **The hidden size is already a compile-time parameter of the lock** (`FORGE_NNUE_HIDDEN`). Wider float nets need no
   engine code; the int16 path (S-A2) needs its int32 output-sum bound re-derived for 2H terms, and its SIMD loops
   checked at 768.
4. **Decision rule:** no H768/H1024 GPU run unless the int16 NPS cost against H512 is ≤ 10% (CPU-time ABBA, d16/d20).

## Files
- `forge_sol_SC4_hidden_768_1024_plan_20261027.md`, `forge_sol_SC4_queue_lines_20261027.txt`;
- `opus_sc4_widen_inc.py`, `test_opus_sc4.py`, `mutation_check_sc4.py`;
- `build_pc_hidden.sh`, plus copies of `nps_ab.py` (S29) and `opus_a7_dryparse.py` (A7);
- `README.md`, `IDEA_SOURCE.md`, `REPORT.md`, `FILES.txt`, `SHA256SUMS`, `logs/step1`-`step7`.

The widened `.inc` files and the 4 exes stay in `F:\opus_scratch\build\SC4` (sha256 in the step 1 and 2 logs).

How it was run: all builds and benches at `nice -n 19`, single-threaded, one heavy step at a time, free RAM ≥ 10 GB.
Machine exclusive: no (gates, training, self-play and sub-agents ran throughout), so the NPS numbers are advisory and
CPU-time based.

## Left / UNVERIFIED
- The int16 width cost (it needs S-A2's path).
- GPU throughput of the wider shapes (queue lines 1-2).
- Any training, holdout or Elo result.
- The Elo-per-speed-doubling range is an ESTIMATE from public time-scaling results, not a Forge measurement.
