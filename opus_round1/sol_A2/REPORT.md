# A2 [Astra] King-bucket feasibility design doc — DONE

Branch `opus-sol-A2` = `d4f4312` (AL1 lock) + `1dfb5650` (CI baseline 0d99f02 cherry-picked) + `3da8ece4` "[A2] King-bucket feasibility design doc, OFF-by-default microbench patch, counts, footprint, data, NPS estimate [skip ci]" + the REPORT commit. Job folder `opus_round1/sol_A2/`. Design only; UNPROVEN; no strength or speed claim. Work and results by a sub-agent; this report text is its hand-back.

C4 (`opus-C4` 23750a76) already covers most of A2: it implemented king buckets end to end (trainer options, v2 format, C++ loader with per-worker refresh cache, `NNUEKingBuckets` default 0, parity, incremental == refresh on 102k plies) and measured lock-replica NPS. A2 adds only what C4 lacks:
- the bucket-crossing microbench on L for K = 4/8/16/32, mirrored and unmirrored;
- the footprint table and the data-per-bucket table;
- an NPS ESTIMATE for the layouts nobody measured;
- one recommended layout.

| line | result | evidence |
|---|---|---|
| Doc covers layouts (768×K, mirrored or not, 4/8/16/32), refresh cost + incremental plan + refresh cache, footprint, trainer changes (v3b + tgz), data needs, NPS estimate with method, one layout, what stays float | DONE: `forge_astra_A2_kingbucket_design_20261027.md` sections 2-9 | doc |
| Every number has a command + raw output, or is labelled ESTIMATE with its method | PASS: each table names its command and log; unmeasured NPS figures are labelled ESTIMATE with model and inputs; copied numbers cite file and lines (C4 REPORT.md 164-166 / 175-178, QA_sol_jobA, CR analysis) | `logs/` |
| Microbench on L: king moves crossing buckets per node, bench d20, raw counts | PASS: patch behind `FORGE_A2_KBSTATS`. Bench d20 has 12,389,307 nodes and 2,986,045 king moves. Crossing king moves per layout, with the rate per 1000 nodes: M1 508,981 (41.1); M4=U8 1,450,652 (117.1); M8=U16 2,242,374 (181.0); M16=U32 2,778,869 (224.3); M32=U64 2,986,045 (241.0); R4 1,331,740 (107.5); R8 1,939,993 (156.6). The logs also have replay-refresh (xp) and jump-refresh (xe) counts and cache/scratch columns at d16, d20 and d22 | `logs/kbstats_raw.log`, `logs/kbstats_tables.md` |
| Microbench flag OFF = lock identity / Std pass | PASS: `git apply --check` and `patch -p1 -F0` OK on `LA/1_source/forge_AL1_s198_src`. OFF exe vs a pristine-lock build: 2 differing bytes (PE timestamp/checksum); vs the PC lock exe 5d4df7f1: 6 PE-header bytes. Preprocessed search/uci/eval/nnue.cpp identical. `uci_check.py --full` ALL OK (312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690). FMA 0 | `logs/apply_check.log`, `logs/build_and_off_identity.log`, `logs/identity_off.log` |
| Counting (ON) build leaves the search unchanged | PASS: `uci_check --full` ALL OK, FMA 0; the counter runs reproduce the node pins | `logs/identity_on.log`, `logs/kbstats_run.log` |
| No engine code on the branch | PASS: `git diff --stat 294dbed HEAD -- src include tests tools bench CMakeLists.txt` is empty (run at the repo root). The patch is a file: `forge_astra_A2_kbstats_microbench_20261027.patch`, sha256 eb4331fb… | git |

## Findings
- **Cross-check with C4.** At bench 16 the counters agree with C4's separate instrumentation: evals/node 0.5963 vs 0.596; replay refreshes per updated eval 11.35% (M4) vs 11.3%, and 17.04% (M8) vs 16.9%.
- **Refreshes saturate.** M32 refreshes at every king move but needs only 2.1× M4's refreshes (xp 1,673,871 vs 802,474 at d20).
- **Refresh cache.** It cuts a refresh from about 14 to about 6 weight columns (M4: 14.37 → 6.23). Refreshes then add 12% (M4) to 23% (M32) to the incremental column traffic. The jump variant needs 3.5-6.2% fewer refreshes than ply-by-ply replay.
- **Endgames dominate.** The two rook endings are 40.5% of d20 nodes and make 440-462 king moves per 1000 nodes; M4 rebuilds 14-29% of their updated evals, the other positions 3.6-10.0%.
- **Data** (1,024,286 real holdout positions): 78.11% of own-king samples are on files e-h; e1 20.81%, g1 18.98%. Smallest block per epoch on 231.9M rows: M4 45.5M, M8 10.0M, M16 2.2M, M32 0.28M samples.
- **Footprint** (H256, Ryzen 7 9850X3D with 1 MiB L2 per core and 96 MiB L3): float W1 is 3 / 6 / 12 / 24 MiB for M4 / M8 / M16 / M32. The M4 refresh cache is 17.5 KiB per worker. The trainer's dense one-hot input at bs16384 is 192 MiB per perspective for M4 and 1.5 GiB for M32.
- **NPS ESTIMATE** (model calibrated on C4's measured replicas at 200-388 ns per refresh), d20: M4 -4.5% (range -4.1..-6.5; C4 measured -4.13% on a U8 replica), M8 -6.1% (C4 measured -6.65%), M16 -7.2%, M32 -7.7%.
- **Recommendation: M4** (mirrored, 4 king buckets, C4 standard map, factoriser on); M8 as the follow-up if M4 gains in a gate.
- **What stays float:** accumulators, refresh cache and all layer arithmetic; int16 is only the weight storage. No int16/int32 inference path, no FMA, no fast-math.

## Left / UNVERIFIED
- No bucketed net has been trained on real data; NPS for M16/M32 and the U layouts is ESTIMATE.
- The cache simulation starts cold at every bench position.
- The ON build was not run under ASan/UBSan (MinGW has no ASan).
- ctest was not re-run for OFF, which is byte-identical to the lock apart from the PE header.
- A superseded first patch version (4fb8a637) has its logs in `logs/patch_v1_4fb8a637/`.

Machine exclusive: no.
Supervisor check: 7 "adopted running job" lines before and after (latest 2026-10-27T08:55:34). A2 had no torch or trainer step.
