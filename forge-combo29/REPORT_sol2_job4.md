# sol2 — Job 4 warm NNUE evaluation counts

## Step 0 — exact r15d and three pins passed

The Job 2 r15d binary SHA-256 `bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6` reproduced **312,866** bench 11 nodes, **862,329** bench 13 nodes and **4,865,609** startpos perft 5 nodes. These were fresh processes with embedded AL1 s198, Threads 1, Hash 16 MiB, MultiPV 1, OwnBook false and UseNNUE true. [Raw pins](sol2/job4/step0-pins.raw.txt) · [Identity](sol2/job4/step0-identity.raw.txt)

## Step 1 — warm known answer matched

The pinned Carbon2 driver (`c79b95bf45762fa9869d23140ed7f946cfaf0cb6bc4f74325a18d5f934bf1c45`) on the uninstrumented r15d returned **8,612 searches, 29,333,343 last-info nodes and `5c705841c3ea17b4`**. It used **19.649703 s** of total engine CPU. The common warm workload for all following rows was 60 seeded startpos games, eight random plies, seed `20261117`, a 300-ply cap, PC20, Threads 1, Hash 16 MiB and `go softnodes 2000`. The synthetic standalone net768 has SHA-256 `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7` and checksum `30ab43b4ba5db5f3`. Engine and driver were pinned to cloud CPU 2. [Exact command and identity](sol2/job4/step1/inputs.txt) · [Raw baseline result and CPU](sol2/job4/step1/runs.jsonl.txt)

## Step 2 — source paths and prediction

The independently committed source inventory traces root initialization, missing ancestry, bucket and mirror transitions, replayed and fused updates, null-move copies, v3 cache lifetime and TT bypasses. The root seed is eager on eligible v3 searches. A king-key transition refreshes the affected perspective, while the other perspective updates incrementally. The cached accumulator is keyed by perspective, bucket and mirror flag. Its previous placement survives `position` and `ucinewgame` with the same net generation and stack size. [Source inventory](sol2/job4/step2-reading.md)

The prediction was pushed alone at `e337359810f0a157d25a29e8d0a8970ac8f0d202` before the probe. It underestimated refreshes by **3.94×**, overestimated columns per refresh by **1.62×**, and put fused calls per search **4.4%** above the observed count. Bucket-only transitions were the largest event as predicted. No-ancestor and natural forced refreshes were both zero. [Prediction](sol2/job4/prediction.txt) · [Readback rates](sol2/job4/step4-costs.raw.txt)

| Prediction | Predicted | Observed |
|---|---:|---:|
| Refreshes per search | 145 | 571.74 |
| Changed columns per refresh | 8 | 4.94 |
| Fused evaluation calls per search | 1,100 | 1,053.41 |
| Root refresh share | 1.4% | 0.35% |
| No-ancestor share | 0% | 0% |
| Bucket-only share | 74.0% | 80.57% |
| Mirror-only share | 20.0% | 9.49% |
| Bucket-and-mirror share | 4.6% | 9.59% |

## Step 3 — natural counters matched both known answers

The five-file probe and driver diffs were applied in scratch with zero fuzz. Both instrumented builds used the Job 2 GCC 14.2.0/libstdc++ 6.0.33/glibc 2.41 CMake Release flags, x86-64-v4 with v3 AVX-512. Probe SHA-256 `4a36e9bcae45ef5bf9262d91ad6736e841813073fd513ed89fbe21fadd3a7055`. Control SHA-256 `b77ebad8d83d05c5d8148faa54e5267175ee053e29604cfee06f245e2a498387`. [Patches and hashes](sol2/job4/step3-patch-hashes.raw.txt) · [Probe compile/link lines](sol2/job4/probe-build.raw.txt) · [Control compile/link lines](sol2/job4/control-build.raw.txt)

The natural probe reproduced the Step 1 trace. Its **4,923,792** perspective refresh calls matched the sum of exclusive event counters separately for each search and for the full workload. The parser required one `evalcount` line before each bestmove. The initial warm-up is retained separately and excluded from the measured totals. [Engine probe patch](sol2/job4/probe.patch.txt) · [Driver patch](sol2/job4/driver.patch.txt) · [Per-search raw trace](sol2/job4/probe-trace.jsonl.txt) · [Independent readback](sol2/job4/probe-readback.raw.txt)

## Forced-refresh control — exact stride and trace passed

The control replaces every 64th update dispatch with a two-perspective cached refresh. It covers fused, replay-pair and replay-single dispatches, including null-copy subsets. A forced mixed-key dispatch retains the other perspective's original mandatory refresh. The single-thread ordinal includes warm-up for cadence. **301,998** measured forced dispatches matched the expected stride and added exactly **603,996** perspective refreshes, taking the count to **5,527,788**. Natural event counts stayed equal. Both runs had **19,327,924** dispatch opportunities and **15,227,146** network outputs. Their node/score/bestmove trace matched the Step 1 pin. An independent row-by-row compare also matched every recorded last `info` line and full `bestmove` line after removing time and NPS. [Patch](sol2/job4/control.patch.txt) · [Cadence check](sol2/job4/step4-cadence.raw.txt) · [Raw control trace](sol2/job4/control-trace.jsonl.txt) · [Counter and trace readback](sol2/job4/control-readback.raw.txt) · [Normalized UCI comparison](sol2/job4/step5-trace-readback.raw.txt)

## Step 4 — workload counts and estimated CPU costs

A refresh counts one perspective. A replay-pair or fused update counts one dispatch for both perspectives. Null and zero-column rows are subsets. Fused calls include the output layer. [Probe totals](sol2/job4/probe-run.raw.txt) · [Rates and calculation](sol2/job4/step4-costs.raw.txt)

| Operation | Count | Per search |
|---|---:|---:|
| Searches | 8,612 | 1.00 |
| Last-info nodes | 29,333,343 | 3,406.10 |
| All v3 output evaluations | 15,227,146 | 1,768.13 |
| Fused update and evaluate | 9,071,977 | 1,053.41 |
| Fused zero-dirty calls | 76,061 | 8.83 |
| Evaluate valid accumulator | 534,502 | 62.06 |
| Evaluate after reconstruction | 5,620,667 | 652.66 |
| Replay pair updates | 5,349,295 | 621.14 |
| Replay zero-dirty pair | 74,860 | 8.69 |
| Replay single updates | 4,906,652 | 569.75 |
| Perspective refreshes | 4,923,792 | 571.74 |
| Root refreshes | 17,140 | 1.99 |
| Non-root missing ancestry | 0 | 0.00 |
| Bucket-only refreshes | 3,967,217 | 460.66 |
| Mirror-only refreshes | 467,435 | 54.28 |
| Bucket plus mirror refreshes | 472,000 | 54.81 |
| Natural forced refreshes | 0 | 0.00 |
| Zero-column refreshes | 299,245 | 34.75 |
| Changed refresh columns | 24,333,354 | 2,825.52 |

| Estimated exclusive work | Job 3 samples | Job 4 events | CPU µs per event |
|---|---:|---:|---:|
| Perspective refresh | 890 | 4,923,792 | 0.2468 |
| Changed refresh column | 890 | 24,333,354 | 0.0499 |
| Paired replay update | 621 | 5,349,295 | 0.1585 |
| Single-perspective replay update | 306 | 4,906,652 | 0.0852 |
| Fused update and evaluation | 1,169 | 9,071,977 | 0.1760 |

There were **4.942 changed columns per perspective refresh**. For the CPU estimates, I multiplied each exclusive function's share of Job 3's **14,389** samples by the unprofiled Step 1 **19.649703 s** engine CPU and divided by the matching probe count. The samples and CPU time come from different executions. The profiled build also used frame pointers. These are rough allocations of exclusive CPU, including fixed overhead in the per-column estimate. Directly timing individual operations could change the overhead and the shares. [Job 3 function table](sol2/job3/step3/pooled.top15.tsv.txt) · [This run's CPU](sol2/job4/step1/runs.jsonl.txt)

## Step 5 — zero-delta fast path proposal

At `src/nnue_v3.cpp:907–914`, a hit on the exact cached placement can copy the cached accumulator immediately. That would bypass the delta scan and stores on **299,245** requests, or **6.08%** of the probe's refreshes. It retains the destination copy and every weight operation. The equality check also runs on misses, so net CPU effect remains unmeasured. The proposal includes the exact replay, standalone-net oracle and Sol3-style 389-position checks. [Text-only proposal](sol2/job4/step5-zero-delta.md)

## Facts

- A king bucket change without a mirror change accounted for **80.57%** of natural perspective refreshes on the pinned warm workload. The root route contributed **0.35%**.
- The counted control passed the exact known trace and two-refresh delta. Cache column counts changed because the forced requests changed the placement history of cache entries.

## Suspicions

- The zero-delta path can remove preparation work on exact-placement hits. A paired experiment would determine whether the comparison cost on the much more common nonzero path offsets that benefit.

## What I did not do

Only scratch engines ran this workload. The repository contains the text probe and control diffs, the driver diff and raw receipts. The permanent engine, owner-PC build and synthetic weights were outside the changes.

## What I am not sure about

The counters cover one thread, one workload, one net and the pinned build. The owner net's cache-delta distribution remains unmeasured. The canonical pin uses last-info node counts, and this driver leaves final softnodes counts outside that trace.

GPT-6 (Codex), Case A. [Clock stamps](sol2/job4/stamps.txt) · [Publication status and file layout](sol2/job4/publication-layout.raw.txt)
