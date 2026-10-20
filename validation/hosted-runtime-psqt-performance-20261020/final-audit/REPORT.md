Independent audit PASS: run 39510219605 attempt 1 satisfies the frozen whole-process Linux performance rule for candidate 6.4.19 against 6.4.18. This conclusion comes from archived originals and independent calculations, not the workflow's success label.

| Metric | Baseline/candidate time ratio | 95% whole-block bootstrap interval | Throughput gain | Time reduction |
| --- | ---: | ---: | ---: | ---: |
| Exact-child CPU | 1.0160844162440468 | 1.0123361440981815–1.019498290677596 | 1.6084% | 1.5830% |
| Wall | 1.0159896183154886 | 1.0122172959743965–1.0194589268676844 | 1.5990% | 1.5738% |

The standalone standard-library audit imports no producer analysis code. It derives each log ratio from the original four samples, excludes the one ABBA warmup, and resamples all 31 complete AB blocks with shared CPU/wall indices, seed 20261027 and 10,000 draws. Linear quantiles at `(N−1)*q` are calculated in log space and exponentiated. Results agree with the original producer values within 1e-12. Both lower limits exceed one; no samples were removed or outcomes pooled.

All 15 same-binary AA blocks pass the frozen gates. CPU median is 0.9971917168010941, range 0.9522761900025262–1.0075803114047002; wall median is 0.9976404729982932, range 0.951322186190663–1.00749654285243. The lowest ratios are close to the 0.95 boundary. This qualification remains visible; it does not change the preregistered decision or establish general host stability.

All 188 original process records are normal: zero exit, no timeout, empty owned group before verdict and after cleanup, singleton CPU 0, matching command/pre-verdict/final lifecycle fields, matching original stream hashes, empty stderr, and exactly five canonical depth-11/321912-node rows each. All 940 numerical row signatures match, including the internal integer NPS calculation. User plus system CPU equals recorded CPU; reported sample metrics equal pre-verdict measurements. Every sample meets its original deadline. Total measured sample wall is 154.665500101 seconds; first-start to last-completion UTC span is approximately 155.810 seconds (second-resolution start timestamps), comfortably within the unchanged 3600-second work limit. UTC span is corroboration, not a replacement for monotonic deadline checks.

Fresh source archives carry exact PAX commit identities `fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b` and `61f598056572dfade6994af8ad2e38817cd28aa3`. Their 73/74-file inventories equal build provenance; executable and core hashes match original artifacts. Both builds use GCC14 and the frozen strict x86-64-v3/generic flags, all eight production translation units are represented, and recorded core sections contain no LTO. Original CTest and LastTest logs show the exact named baseline 10 and candidate 11 tests passing. All 12 recorded build/export/version stages have successful process facts and matching raw stream hashes.

Independently rehashed the archived exact 21-entry package, all 31 bound proofs, build inventory and artifacts, and all 160 final frozen inputs. Package/proof bytes also match the locally frozen launch inputs for payload `5e50d99a93a381a881b4f1813dce462a3e4106bf`. Hosted before/after byte and mode records are identical. ZIP payloads preserve bytes, not original filesystem permissions; extracted modes are not presented as another hosted mode measurement. Root separately owns transport verification of the 1,237-payload archive from results commit `0124dbd075b252552a27264996b72cf2ef800598`; this review starts from that stable extraction and independently checks the consumed evidence.

This establishes a gain for this one AMD EPYC hosted Linux workload: fresh-process startup plus five fixed bench commands, T1/Hash16. It establishes neither Elo nor native Windows/Ryzen performance, isolated PSQT-kernel speed, general clock reliability, or a speed guarantee across workloads. Historical failed attempts, unresolved anomalies and the earlier offline-wrapper timeout retain their original outcomes. No engine, compiler, build, Git, network, retry or relaunch was performed by this reviewer.

Stable evidence:

- `audit.py`: `8f5b1be80c5d1d8f399ec3b86e0d5ce2d10ff2f4bd87b4d036b9eee068b60782`.
- `AUDIT.json`: `5dda3b8141be7923e2baa2825596ac2dd6ff07b690b0fdc6acd3da618443f91b`.
- `LIFECYCLE-CHECKS.json`: `d23895faf673f6b34c937915bc488f12422e0cb06f2787fe680fab63ed0b4250`.
- Original summary: `7f1c53c5e81d4a8e73025350bad02bbca823499079798a00801b0de574d5ae82`.

The independent script's first invocation exited zero; `attempt1.stdout` retains its numerical findings and `attempt1.stderr` is empty. All originals and earlier reports remain unchanged.
