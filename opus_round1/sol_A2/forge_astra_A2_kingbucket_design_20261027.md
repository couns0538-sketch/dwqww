# Astra A2 — King-bucket feasibility design for the Forge NNUE (2026-10-27)

DESIGN ONLY. UNPROVEN: no strength claim, no speed claim. Every number below is either measured here (the command
and its raw output are in `logs/`, named next to the number) or copied from a named file and line, or labelled
**ESTIMATE** with its method. Engine code: only the counting microbench, a patch behind the compile flag
`FORGE_A2_KBSTATS` (absent = no code; section 10). Branch `opus-sol-A2`.

## 0. Summary

- **Recommendation: layout M4** — mirrored, 4 king buckets, C4's standard half-board map
  `0011 0011 2222 2222 3333 3333 3333 3333` (files a-d, ranks 1-8 of the perspective's own side; a king on files
  e-h uses the mirror image), feature transform `768 x 4`, with the factoriser during training. Reasons (section 8):
  the fewest refreshes of the layouts that see the king's file side (64.8 refreshes per 1000 nodes at bench d20,
  under half of M32's 135.1), the lowest measured NPS cost of a bucket pattern (C4: -4.13% at d20 for M4's refresh
  pattern, on a replica with twice M4's weights, vs -6.65% for M8's), and the best-trained buckets (smallest bucket
  9.8% of all king samples, about 45M samples per epoch on today's 231.9M training rows, against 0.28M for M32).
- **Already done (reused, not redone).** C4 (`opus-C4` 23750a76) implemented king buckets end to end: trainer
  options, file format v2, C++ loader and inference with a per-worker refresh cache, UCI `NNUEKingBuckets`
  (default 0), parity 10000/10000, incremental == refresh on 102,000 plies, measured NPS of lock replicas. C5 added
  8 output buckets, O4 a pure (no HCE) evaluation. A2 adds what C4 lacks: the bucket-crossing counts on the lock's
  bench tree for K = 4/8/16/32 (mirrored and not), the footprint table, the data-per-bucket table, an NPS ESTIMATE
  for the layouts nobody measured, and the recommendation.
- **What stays float** (section 9): accumulators, refresh-cache entries and every layer's arithmetic stay float32;
  int16 is only the storage format of the first-layer weights (x 4096). No int16 or int32 inference path, no FMA,
  no `-ffast-math`, no `-ffp-contract=fast`.

## 1. Inputs read

| input | used for |
|---|---|
| L = lock source `LA/1_source/forge_AL1_s198_src` (`src/nnue.cpp`, `include/forge/nnue.hpp`, `src/search.cpp` `Worker::static_evaluate` / `record_move`, `src/eval.cpp`) | today's accumulator scheme; the microbench hooks |
| `LA/5_nnue/docs/NNUE_NEXT_WEEK_PLAN.md`, `NETS_log_20261025_1240.md` | data size, recipe context (item 7 "buckets8" = output buckets, not king buckets) |
| `LA/5_nnue/trainers/train_resid_v3b.py`, `LA/5_nnue/datagen_and_format/forge-nnue-tools.tgz` | trainer changes (section 5) |
| `LA/5_nnue/nets/history_all_CR_passed/CR_PASS_nnue_h256_e12_lock_net_float_accumulator_analysis.txt`, `CR_HOLD_sol_nnueint16_b425207a_overflow_table.txt` | float exactness, int16 overflow |
| `LA/7_history/rejected_and_shelved/int32_exact_h256e12_20261025/` (`QA_sol_jobA_return_20261025.md`, `forge_sol_jobA_report_20261025.md`) | why the exact-int32 path was slow and why no refresh cache was built then |
| `opus-C4` `opus_round1/C4/REPORT.md` (23750a76), `opus-C5` 57066d2c, `opus-O4` 348d8607 | the implementation, measured NPS, layouts |

## 2. Input layout options

### 2.1 Feature definition (identical to C4's `nnue_v2.hpp`, `forge_nnue_v2.py`)
Per perspective `p` (White = 0, Black = 1), own king on square `k`:
```
r  = s if p is White else s ^ 56          (piece square in the perspective's frame)
kr = k if p is White else k ^ 56          (own king square in the perspective's frame)
flip  = 7 if (mirrored and kr % 8 >= 4) else 0
block = king_map[kr]                       (64-entry map; mirrored maps satisfy map[x] == map[x ^ 7])
index = block * 768 + (relcolour * 6 + type) * 64 + (r ^ flip)      (kings are features, as in the lock)
```
Block 0 without flip is exactly the lock's `feature_index`. A perspective's accumulator depends on its own
**key** = (block, flip); a king move that changes the mover's key invalidates that perspective only.

### 2.2 Layouts compared

| name | weight blocks | refresh keys | map |
|---|---|---|---|
| lock | 1 | 1 | none |
| M1 | 1 | 2 | mirroring alone (key changes only when the king crosses files d/e) |
| M2 / M4 / M8 / M16 / M32 | 2 / 4 / 8 / 16 / 32 | 4 / 8 / 16 / 32 / 64 | C4 half-board rows (files a-d, rank 1 first): M2 `0000 0000 1111 1111 1111 1111 1111 1111`; M4 `0011 0011 2222 2222 3333 3333 3333 3333`; M8 `0123 4455 6666 7777 7777 7777 7777 7777`; M16 `0123 4567 8899 aabb cccc dddd eeee ffff`; M32 every half-board square |
| U4 / U8 / U16 / U32 / U64 (unmirrored) | 4 / 8 / 16 / 32 / 64 | = blocks | the M(K/2) map with files e-h in their own blocks: **U(2n) has exactly the refresh keys of Mn** (C4's lock replicas rm8 = U8 and rm16 = U16 are of this kind) |
| R4 / R8 (unmirrored, files ignored) | 4 / 8 | 4 / 8 | rank zones 1 \| 2 \| 3-4 \| 5-8; single ranks |

So for refresh cost only the key partition matters: M4 and U8 refresh at the same moves, but U8 has twice the
weights and half the training samples per block (sections 4 and 6). Every unmirrored U(2n) is dominated by Mn on
memory and data at equal refresh cost; it only buys left/right asymmetry (queen side vs king side king), which the
mirrored net sees through the (mirrored) piece features anyway.

## 3. Refresh cost and the incremental-update plan

### 3.1 Today (lock)
`Worker::static_evaluate` keeps one float accumulator `[2][256]` per search-stack ply, marks the child stale in
`record_move`, and on evaluation walks back to the nearest valid ancestor and replays the recorded piece changes
(`nnue::update`, 2-4 weight columns per perspective and ply). A full refresh happens only at the root of each
search: 8 per bench (`QA_sol_jobA_return_20261025.md`, verdict paragraph: "only 8 full refreshes per bench ...
a refresh cache cannot pay"); the microbench confirms that no evaluation refreshes from scratch
(`scratch_refresh 0` at every depth, `logs/kbstats_raw.log`).

### 3.2 With king buckets (the plan; C4 implements it)
1. Per perspective, incremental update while its own key is unchanged (any number of plies, king moves inside the
   same key included: the king's own feature is an ordinary remove/add).
2. When the mover's key changes, only that perspective is rebuilt; the other one stays incremental.
3. The rebuild uses a **refresh cache**: per worker, one entry per (perspective, key) = the float accumulator of the
   position it was last brought to + its 12 piece bitboards. Rebuild = subtract the columns of pieces that are in
   the entry but not on the board, add those on the board but not in the entry, copy the entry into the ply. Cold
   entries start as the bias with empty bitboards (= a refresh from scratch).
4. Two ways to place the rebuild in the lazy walk-back: **ply by ply** (C4: every replayed ply is made valid; a
   key change at a replayed ply refreshes there: count `xp`) or **jump** (compare the key at the replay source with
   the key at the evaluated position; if different, rebuild the perspective once at the evaluated position and skip
   its intermediate updates: count `xe`). The jump needs per-perspective validity flags; it needs 3.5-6.2% fewer
   refreshes for the M layouts (xe/xp 0.9382-0.9647 at d20, `logs/kbstats_tables.md`; M4 769,504 vs 802,474) and
   skips the refreshed perspective's intermediate updates. A3 specifies the jump variant.
5. Exactness: section 3.4. Any update order, the cache path and a refresh from scratch give identical bits.

### 3.3 Microbench on L (raw counts)

**Method.** The patch `forge_astra_A2_kbstats_microbench_20261027.patch` adds, under `#ifdef FORGE_A2_KBSTATS`
only, counting hooks to `Worker::record_move`, `Worker::record_null_move`, `Worker::static_evaluate` (before
any change to the accumulator, replaying the lock's own walk-back read-only) and per-position reporting to the
`bench` command. For 8 key partitions (2.2) it counts:
- `xm`: king moves made by the search (every `record_move`, quiescence included) whose own key changes —
  the spec's "king moves that cross buckets";
- `xp`: replayed plies whose mover's key changes (refreshes of a ply-by-ply engine such as C4);
- `xe`: (updated evaluation, perspective) pairs whose key differs between the replay source and the evaluated
  position (refreshes of the jump variant);
- `cache_cols` / `scratch_cols`: weight columns those `xe` refreshes need with a simulated refresh cache (one entry
  per perspective and key, cold at the start of each bench position) or from scratch.
The counters never feed back into the search: the ON build reproduces all lock pins (bench d11-d22, perft,
kiwipete; `logs/identity_on.log`). Run: `bash a2_verify.sh <scratch> logs` (Threads 1, Hash 16, OwnBook false,
nice 19), then `python -I -B a2_kbstats_table.py logs/kbstats_raw.log` (`logs/kbstats_tables.md`).

**Raw totals at bench d20** (`logs/kbstats_raw.log`, verbatim):
```
info string bench depth 20 nodes 12389307 ...
info string a2kb total depth 20 nodes 12389307 evals 6931060 evals_valid 67531 scratch_refresh 0 replayed 8467494 replayed_cols 19796964 moves 11696220 null_moves 332808 king_moves 2986045
info string a2kb total depth 20 layout M1 keys 2 xm 508981 xp 283273 xe 273285 cache_cols 1684010 scratch_cols 3876642
info string a2kb total depth 20 layout M2=U4 keys 4 xm 843288 xp 443487 xe 427271 cache_cols 2603329 scratch_cols 5555329
info string a2kb total depth 20 layout M4=U8 keys 8 xm 1450652 xp 802474 xe 769504 cache_cols 4796585 scratch_cols 11059750
info string a2kb total depth 20 layout M8=U16 keys 16 xm 2242374 xp 1238323 xe 1178464 cache_cols 7449156 scratch_cols 18281457
info string a2kb total depth 20 layout M16=U32 keys 32 xm 2778869 xp 1557333 xe 1465236 cache_cols 8889943 scratch_cols 20380504
info string a2kb total depth 20 layout M32=U64 keys 64 xm 2986045 xp 1673871 xe 1570438 cache_cols 9269740 scratch_cols 21184154
info string a2kb total depth 20 layout R4 keys 4 xm 1331740 xp 700583 xe 663039 cache_cols 4000626 scratch_cols 8900511
info string a2kb total depth 20 layout R8 keys 8 xm 1939993 xp 1047153 xe 971941 cache_cols 5532549 scratch_cols 11196552
```

**Table A — search totals** (`logs/kbstats_tables.md`; "updated evals" replayed >= 1 ply; "inc cols/node" =
2 x replayed_cols / nodes, both perspectives):

| depth | nodes | evals/node | updated evals | plies/updated eval | inc cols/node | king moves/1000 nodes |
|---|---|---|---|---|---|---|
| 16 | 3,024,920 | 0.5963 | 1,788,835 | 1.2335 | 3.4416 | 219.01 |
| 20 | 12,389,307 | 0.5594 | 6,863,529 | 1.2337 | 3.1958 | 241.02 |
| 22 | 34,048,354 | 0.5429 | 18,301,815 | 1.2297 | 3.0499 | 278.24 |

**Table B — bench d20, per layout** (`logs/kbstats_tables.md`; d16 and d22 in the same file):

| layout | keys | xm/1000 nodes | xm/king move | xp/updated eval | xe/updated eval | xe/1000 nodes | cache cols/refresh | scratch cols/refresh | cache refresh cols / inc cols |
|---|---|---|---|---|---|---|---|---|---|
| M1 | 2 | 41.082 | 0.170 | 0.0413 | 0.0398 | 22.058 | 6.16 | 14.19 | 0.0425 |
| M2=U4 | 4 | 68.066 | 0.282 | 0.0646 | 0.0623 | 34.487 | 6.09 | 13.00 | 0.0658 |
| **M4=U8** | 8 | **117.089** | 0.486 | **0.1169** | 0.1121 | 62.110 | 6.23 | 14.37 | 0.1211 |
| M8=U16 | 16 | 180.993 | 0.751 | 0.1804 | 0.1717 | 95.119 | 6.32 | 15.51 | 0.1881 |
| M16=U32 | 32 | 224.296 | 0.931 | 0.2269 | 0.2135 | 118.266 | 6.07 | 13.91 | 0.2245 |
| M32=U64 | 64 | 241.018 | 1.000 | 0.2439 | 0.2288 | 126.758 | 5.90 | 13.49 | 0.2341 |
| R4 | 4 | 107.491 | 0.446 | 0.1021 | 0.0966 | 53.517 | 6.03 | 13.42 | 0.1010 |
| R8 | 8 | 156.586 | 0.650 | 0.1526 | 0.1416 | 78.450 | 5.69 | 11.52 | 0.1397 |

Readings:
- Crossings saturate: M32 refreshes at every king move (xm/king move 1.000) yet needs only 2.1x the
  refreshes of M4 (xp 1,673,871 vs 802,474), because most evaluations sit between king moves.
- The refresh cache cuts a refresh from about 14 to about 6 weight columns (cache 6.23 vs scratch 14.37 for M4);
  the refreshes then add 12% (M4) to 23% (M32) to the incremental column traffic (last column).
- **Cross-check with C4's independent instrumentation** (C4 `REPORT.md` lines 175-178, bench 16, its own engine):
  evaluations per node 0.596 vs 0.5963 here; king-key changes per evaluation 11.3% (rm8) and 16.9% (rm16) vs xp per
  updated evaluation 11.35% (M4=U8) and 17.04% (M8=U16) here (`logs/kbstats_tables.md`, d16 table).

**Table C — bench d20 per position** (xe per updated evaluation; positions are uci.cpp's bench list in order):

| pos | nodes | share of nodes | king moves/1000 nodes | M1 | M4=U8 | M8=U16 | M16=U32 | M32=U64 | R4 |
|---|---|---|---|---|---|---|---|---|---|
| 1 startpos | 1,089,334 | 8.8% | 51.38 | 0.0198 | 0.0509 | 0.0653 | 0.0657 | 0.0657 | 0.0219 |
| 2 kiwipete | 2,229,561 | 18.0% | 156.07 | 0.0576 | 0.1002 | 0.1991 | 0.2023 | 0.2028 | 0.0903 |
| 3 | 1,707,713 | 13.8% | 66.34 | 0.0003 | 0.0480 | 0.0814 | 0.0821 | 0.0826 | 0.0300 |
| 4 rook ending | 719,540 | 5.8% | 439.51 | 0.0753 | 0.1419 | 0.1020 | 0.4762 | 0.5868 | 0.0733 |
| 5 | 998,981 | 8.1% | 53.53 | 0.0088 | 0.0358 | 0.0638 | 0.0640 | 0.0640 | 0.0228 |
| 6 | 93,319 | 0.8% | 107.12 | 0.0044 | 0.0566 | 0.1386 | 0.1410 | 0.1413 | 0.0587 |
| 7 rook ending | 4,302,574 | 34.7% | 462.09 | 0.0955 | 0.2853 | 0.4038 | 0.5038 | 0.5470 | 0.2779 |
| 8 | 1,248,285 | 10.1% | 80.83 | 0.0066 | 0.0519 | 0.0936 | 0.0985 | 0.1018 | 0.0486 |

Endgames dominate: the two rook endings (positions 4 and 7, 5.8% + 34.7% = 40.5% of the d20 nodes) have 440-462
king moves per 1000 nodes and M4 rebuilds 14-29% of their updated evaluations; the other positions stay at
3.6-10.0%. A net's refresh cost therefore depends on how much endgame its games reach; the bench mix is the
measurement basis here.

### 3.4 Exactness (why incremental == refresh == cache refresh, bit for bit)
First-layer weights and biases are integers / 4096 (int16 storage). Every accumulator value and every partial sum
of an update or a cache rebuild is then a multiple of 2^-12; float32 represents all of them exactly while
|sum| < 2^24 / 4096 = 4096. With int16 weights and at most 32 pieces, |bias| + 32 x max|w| <= 33 x 32767 < 2^24,
so float addition is exact in any order and incremental update, cache rebuild and refresh from scratch give the same
bits (argument: `CR_PASS_nnue_h256_e12_lock_net_float_accumulator_analysis.txt` item 3; for the h256_e12 net the CR
computed a worst case of 219,282 q, a margin of 76x). It holds per bucket because each key uses one block. C4 measured it on its
engine: 102,000 plies, 64,625 accumulators compared bit for bit with a refresh, 0 mismatches (C4 REPORT.md
acceptance 4). It needs no extra check at load as long as weights stay int16 / 4096.

## 4. Memory and cache footprint (H = 256; `python -I -B a2_footprint.py 256`, `logs/footprint.log`)

CPU (`logs/cpu_caches.log`): AMD Ryzen 7 9850X3D, 8 cores / 16 threads, L2CacheSize 8192 KB (1 MiB per core),
L3CacheSize 98304 KB.

| layout | weight blocks | W1 float32 in memory | W1 int16 in the file | x L2 per core | x L3 | refresh keys | refresh cache per worker | 16 workers |
|---|---|---|---|---|---|---|---|---|
| lock | 1 | 768.0 KiB | 384.0 KiB | 0.75 | 0.008 | 1 | - | - |
| **M4** | 4 | 3.00 MiB | 1.50 MiB | 3.00 | 0.031 | 8 | 17.5 KiB | 280.0 KiB |
| U8 (= C4 rm8) | 8 | 6.00 MiB | 3.00 MiB | 6.00 | 0.062 | 8 | 17.5 KiB | 280.0 KiB |
| M8 | 8 | 6.00 MiB | 3.00 MiB | 6.00 | 0.062 | 16 | 35.0 KiB | 560.0 KiB |
| U16 (= C4 rm16) | 16 | 12.00 MiB | 6.00 MiB | 12.00 | 0.125 | 16 | 35.0 KiB | 560.0 KiB |
| M16 | 16 | 12.00 MiB | 6.00 MiB | 12.00 | 0.125 | 32 | 70.0 KiB | 1.09 MiB |
| U32 | 32 | 24.00 MiB | 12.00 MiB | 24.00 | 0.250 | 32 | 70.0 KiB | 1.09 MiB |
| M32 | 32 | 24.00 MiB | 12.00 MiB | 24.00 | 0.250 | 64 | 140.0 KiB | 2.19 MiB |
| U64 | 64 | 48.00 MiB | 24.00 MiB | 48.00 | 0.500 | 64 | 140.0 KiB | 2.19 MiB |

- The accumulator per search-stack ply is unchanged (2 x 256 x 4 = 2048 B). One weight column = 1 KiB = 16 cache
  lines; a refresh from scratch reads about 32 KiB per perspective, a cache rebuild about 6 KiB (table B).
- The lock's single block already takes 0.75 of a core's 1 MiB L2; every bucketed layout exceeds L2 and lives
  in L3. What matters is which columns are hot: a perspective uses one block while its
  key holds, and the refresh cache's entries are small (17.5 KiB per worker for M4). The X3D L3 (96 MiB) holds
  every layout up to U64, but the gate runs share it with other processes.
- The C4 calibration replicas hold 6 MiB (rm8) and 12 MiB (rm16) of float weights; a real M4 net has 3 MiB, so the
  rm8 measurement includes a larger weight footprint than M4 will have.

## 5. Trainer changes (v3b and forge-nnue-tools.tgz)

All of these exist on `opus-C4` (`tools/nnue/train_resid_v3b.py`, a copy of the archive's v3b md5 b6758004 with
additions; without the new options it is byte-identical to v3b, C4 acceptance 3):
- `--king-buckets N` (standard mirrored layouts 1/2/4/6/8/16/32), `--king-map` (any 32- or 64-entry map),
  `--king-mirror` (default 1), `--king-factor` (default 1: a shared 768 x H factoriser block added to every bucket
  during training, folded on export, inference cost unchanged);
- feature indices as 2.1 (`king_features`; first own king if a malformed record has several, square 0 if none);
- QAT on q(bucket + factor), so the exported integers are exactly the trained forward's weights;
- export `.fnn2` (format v2: header with king map, output map, flags; FNV-1a trailer); C5 adds `--output-buckets`,
  O4 `--pure`. A3 defines a new stand-alone format for the full net.

forge-nnue-tools.tgz: `forge_selfplay.py` and `convert_training.py` need **no change** (records hold the whole
board, kings included; the FPOS `.pos` format stores all 64 squares). Its streaming `train_nnue.py` is the older
768-input trainer that production no longer uses (v3b reads `.pos`/`.hce`); change it only if it comes back.

GPU memory (`logs/footprint.log`, trainer table): the dense one-hot input that v3b and C4 build per batch grows
with the blocks — at bs 16384, 192 MiB per perspective for M4, 384 MiB for M8, 1.5 GiB for M32. Up to M8 the
dense path is fine on the 20 GB card; from M16 on, a sparse input (index lists + embedding-bag sum) should replace
it. C4's bucketed model was run on CPU only; DirectML needs a few hundred steps first (C4 REPORT.md gate section).

## 6. Data needs (`python -I -B a2_bucket_occupancy.py holdout_013_014_s16.pos`, `logs/bucket_occupancy.log`)

Measured on 1,024,286 real self-play positions (S31's subset of the 013+014 holdout, md5 9ebe2f9c), 2 samples
per position (each side's own king in its own frame): own king on files e-h in 78.11% of the samples; e1 20.81%,
g1 18.98%; rank 1 50.04%, ranks 5-8 9.81%.

| layout | weight blocks | min share | median share | max share | samples/epoch in the smallest block (231.9M rows x 2 x min share) |
|---|---|---|---|---|---|
| M2 | 2 | 29.348% | 50.000% | 70.65% | 136,115,365 |
| **M4** | 4 | 9.807% | 25.827% | 38.54% | 45,484,989 |
| U8 | 8 | 3.559% | 7.018% | 31.13% | 16,508,300 |
| M8 | 8 | 2.161% | 11.946% | 22.03% | 10,024,158 |
| M16 | 16 | 0.485% | 4.764% | 22.03% | 2,248,621 |
| U16 | 16 | 0.230% | 3.918% | 20.81% | 1,066,125 |
| M32 | 32 | 0.061% | 1.475% | 22.03% | 283,681 |
| U64 | 64 | 0.025% | 0.570% | 20.81% | 114,559 |
| R4 | 4 | 9.807% | 20.075% | 50.04% | 45,484,989 |

(231.9M = the live trainer's training rows on 2026-10-27, forge-nnue-data skill; growing about 10M per step.)
- Mirroring doubles the data per block at equal refresh cost (M4 vs U8: 9.8% vs 3.6% in the smallest block).
- With the factoriser every bucket starts from, and keeps sharing, the common 768 x H block, so sparse buckets fall
  back to the unbucketed net instead of to noise; it is the default in C4's trainer and should stay on.
- No new data format, no new labels. The in-distribution self-play data keeps the king on e1/g1 in 40% of the
  samples; endgame buckets (ranks 3-8) are the thin ones.

## 7. NPS estimate WITH method (`python -I -B a2_nps_estimate.py logs/kbstats_raw.log`, `logs/nps_estimate.log`)

**Measured (C4, the only measurement):** C4's engine with lock replicas searches the lock's own tree (node counts
equal on every run), so the cost is the bucket machinery alone. CPU-time NPS vs the AL1 lock exe, 10 ABBA runs per
depth, loaded PC (C4 `REPORT.md` lines 164-166): r1 (v2 path, never refreshes) -1.31% (d16) / -1.60% (d20);
rm8 (= M4 refreshes, 6 MiB) -5.33% / -4.13%; rm16 (= M8 refreshes, 12 MiB) -8.94% / -6.65%; the 95% CIs of rm8 /
rm16 are 2.1-2.5 points wide at d16 and 5.3-5.7 points wide at d20.

**ESTIMATE model:** loss(L, d) = loss(r1, d) + beta x xp(L, d) per 1000 nodes, with beta fitted at the four
calibration points ((loss(rm) - loss(r1)) / rate(rm)): 0.0599 / 0.0757 (d16, rm8 / rm16) and 0.0391 / 0.0505
(d20) % per refresh per 1000 nodes, i.e. 200-388 ns per refresh at 513 ns per node (1/1.95M nps, C4's OFF bench
d20 line 1949230 nps). Point = mean beta of the same
depth; range = smallest .. largest beta of the four points. Raw output:

| layout | weight blocks (M / U) | d16 xp/1000 nodes | d16 ESTIMATE (range) | d20 xp/1000 nodes | d20 ESTIMATE (range) |
|---|---|---|---|---|---|
| M1 | 1 / 2 | 23.49 | -2.9% (-2.2 .. -3.1) | 22.86 | -2.6% (-2.5 .. -3.3) |
| M2=U4 | 2 / 4 | 36.28 | -3.8% (-2.7 .. -4.1) | 35.80 | -3.2% (-3.0 .. -4.3) |
| **M4=U8** | 4 / 8 | 67.11 | -5.9% (-3.9 .. -6.4) | 64.77 | -4.5% (-4.1 .. -6.5) |
| M8=U16 | 8 / 16 | 100.79 | -8.1% (-5.2 .. -8.9) | 99.95 | -6.1% (-5.5 .. -9.2) |
| M16=U32 | 16 / 32 | 130.35 | -10.1% (-6.4 .. -11.2) | 125.70 | -7.2% (-6.5 .. -11.1) |
| M32=U64 | 32 / 64 | 140.28 | -10.8% (-6.8 .. -11.9) | 135.11 | -7.7% (-6.9 .. -11.8) |
| R4 | 4 | 58.04 | -5.2% (-3.6 .. -5.7) | 56.55 | -4.1% (-3.8 .. -5.9) |
| R8 | 8 | 89.83 | -7.4% (-4.8 .. -8.1) | 84.52 | -5.4% (-4.9 .. -8.0) |

Caveats (all ESTIMATE): M4 and M8 are the calibration points themselves; layouts with more than 12 MiB of float
weights (U32, M32, U64) are extrapolated beyond the calibration and may lose more to cache misses; the jump variant
(fewer refreshes, `xe` < `xp`) would cost slightly less; a trained net searches a different tree (C4's smoke nets:
13-15% more evaluations per node); a full NNUE adds hidden layers but drops the HCE (O4 measured the HCE at about
31% of the evaluation cost per ply, 759 vs 526 ns, O4 REPORT.md "NPS"). Speed decides nothing without a gate.

## 8. Recommendation: M4 (mirrored, 4 king buckets, factoriser on)

| criterion | M4 | M8 | M16 | M32 | source |
|---|---|---|---|---|---|
| refreshes per 1000 nodes (xp, d20) | 64.8 | 100.0 | 125.7 | 135.1 | `logs/nps_estimate.log` |
| NPS cost d20 | -4.13% measured on U8 (2x M4's weights) | -6.65% measured on U16 | -7.2% ESTIMATE | -7.7% ESTIMATE | C4 REPORT.md; `logs/nps_estimate.log` |
| float weights | 3 MiB | 6 MiB | 12 MiB | 24 MiB | `logs/footprint.log` |
| smallest block, samples per epoch | 45.5M | 10.0M | 2.2M | 0.28M | `logs/bucket_occupancy.log` |
| dense trainer input per perspective (bs 16384) | 192 MiB | 384 MiB | 768 MiB | 1.5 GiB | `logs/footprint.log` |

M4 is the cheapest layout that knows the king's side of the board and its home rank (the occupancy shows those are
where the data is: rank 1 50.04%, files e-h 78.11%), its smallest bucket still sees about 45M samples per epoch, and
the engine, trainer, format and tests for it exist (C4). Rank-only R4 refreshes about 13% less (xp 56.5 vs 64.8 per
1000 nodes) but cannot tell a castled king from one in the centre of the back rank, which is the main thing a king
bucket should add. M8 is the follow-up if M4 gains in a gate: the same code with another map, 10M samples per epoch
in its smallest bucket. M16/M32 do not fit this data size (0.28-2.2M samples in the thinnest bucket per epoch) and
cost the most. **Next steps (not done here):** train M4 with the lock recipe plus `--king-buckets 4` (C4 gate spec
G-C1), parity, NPS d16/d20 with the real net, then a gate; A3 builds the full-NNUE pipeline on M4.

## 9. What stays float (spec "rule 8" = HANDOFF_PROMPT_FULL_20261025_1743.md rule 6, "H256 stays float"; archive prompt rule 3)

- Accumulators: float32 `[2][H]` per ply, as in the lock. Refresh-cache entries: float32. No int16 accumulators
  (they overflow on every H256 net: `CR_HOLD_sol_nnueint16_b425207a_overflow_table.txt`; for h256_e12 the CR
  analysis item 3 gives a worst-case bound of -219,282 q and an observed maximum of 73.9k q, both beyond int16's
  32,767), no int32 accumulator path.
- Output layer (and A3's hidden layers): float32 with a fixed summation order (the lock's 16-lane association), no
  FMA, no `-ffast-math`, no `-ffp-contract=fast`, built with `-ffp-contract=off -fno-fast-math`.
- int16 remains only the storage of first-layer weights and biases (x 4096, converted to float at load), which is
  what makes the float accumulator exact (3.4). The factoriser is folded and quantised at export; nothing about it
  reaches inference.
- Why not int32 for refreshes: the shelved exact-int32 path was correct but 4-5% slower when ON (int32 -> float
  conversion and scaling of 512 lanes per evaluation, accumulator copies doubled to 4128 B, `evaluate_values` not
  inlined; `QA_sol_jobA_return_20261025.md` finding 1), and at the time refreshes were only 8 per bench so no cache
  could pay. With king buckets refreshes become frequent (table B), so the refresh cache matters — and it works in
  float because the float sums are exact.

## 10. Microbench patch and its Std pass (flag OFF)

`forge_astra_A2_kbstats_microbench_20261027.patch` (sha256 `eb4331fb3952c871d24c4160e78ccf923e2918af8c1c8177fd5e67790e3ccd26`;
3 files: `include/forge/search.hpp` +11, `src/search.cpp` +216, `src/uci.cpp` +13; every added line inside
`#ifdef FORGE_A2_KBSTATS`). Evidence (`bash a2_verify.sh`, logs named):

| check | result | log |
|---|---|---|
| applies to `LA/1_source/forge_AL1_s198_src` with `git apply --check` and `patch -p1 -F0` | OK, OK | `logs/apply_check.log` |
| OFF = no code: OFF exe vs the pristine lock source built with the same recipe | 2 differing bytes (offsets 137 and 217 = PE timestamp / checksum) | `logs/build_and_off_identity.log` |
| OFF exe vs the PC lock exe `forge_h256_s198.exe` (sha256 5d4df7f1...) | 6 differing bytes (offsets 137-139, 217-219 = PE timestamp / checksum) | same |
| preprocessed sources (`g++ -E -P`, OFF flags) of search.cpp, uci.cpp, eval.cpp, nnue.cpp, patched vs pristine | IDENTICAL x4 | same |
| OFF: bench d11/13/16/20/22, perft5, kiwipete (`uci_check.py --full`) | ALL OK (312866 / 862329 / 3024920 / 12389307 / 34048354, 4865609, 193690690) | `logs/identity_off.log` |
| FMA count OFF / ON | 0 / 0 | `logs/identity_off.log`, `logs/identity_on.log` |
| ON (counting) keeps the search: same `uci_check.py --full` | ALL OK | `logs/identity_on.log` |
| ctest, ASan+UBSan for the OFF build | not re-run: the OFF build is the lock (byte-identical apart from the PE header, preprocessed sources identical), so the lock's ctest record applies unchanged | - |

## 11. Open items / UNVERIFIED

- No trained bucketed net exists on real data; every NPS figure for M16/M32/U-layouts is ESTIMATE; trained nets
  search other trees.
- The refresh-cache simulation starts cold at every bench position (bench clears the searcher); in games the cache
  persists across moves and should rebuild with fewer columns.
- The NPS calibration comes from a loaded PC with 2-6 point wide CIs (C4); re-measure on a quiet machine.
- ASan/UBSan of the ON (counting) build not run (MinGW has no ASan; the ON build is a measurement tool only).
