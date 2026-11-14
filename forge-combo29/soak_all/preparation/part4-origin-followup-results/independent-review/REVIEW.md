# Independent review of Part 4 first-pass provenance

This is a read-only review of the frozen first-pass source and existing native output. I ran no engine, compiler, search, or experiment controller, and changed no production source, experiment state, or Git reference. Static parsing and report evidence are confined to this scratch directory. The second-pass producer-subtree investigation is separate and is not certified by this first-pass review.

## Finding

The retained evidence supports the reported target-slot writer/consumer chain. It identifies the exact qsearch return behind this short PV and establishes which stored payload it consumed. It does **not** yet establish where the first target-position mate-valued result originated in its descendants, nor prove an exact mate distance or general mate-score correctness.

The fixture is the fresh White KRK root `8/8/8/8/8/1R6/2k5/5K2 w - - 0 1`, Threads 1, Hash 16, OwnBook false, **UseNNUE false**, depth 13. The baseline and two traced executions all exited 0 without a signal or timeout. All baseline stdout and traced stdout are identical after removing only the numeric `time` and `nps` values. The two complete traces agree after consistently remapping only table addresses. These are checks on this deterministic fixture, not a general proof that logging has no timing effects.

## Independently reconstructed ledger

I parsed all 520 trace events (sequences 1–520, contiguous), including all 28 accepted target writes, rather than relying only on the supplied extracted ledger. The full watched key is `6827293331010548038`, tag `2890330438`, cluster 97021, slot 0, table epoch 5, generation 1 for the search events below. The root iteration is **13** throughout; a writer's entry depth is a different quantity.

| Event | Raw stderr line / sequence | Observation |
|---|---:|---|
| Previous ordinary payload | 359 / 358 | Frame 23216, ply 9, entry depth 6, admitted raw −509, BoundUpper, stored clock 9. |
| First accepted mate-valued payload for the watched key | 369 / 368 | Frame **23225**, ply 9, **entry depth 6**, MAIN_FINAL: return −31973, stored raw **−31982**, BoundUpper, depth 6, clock 9. This means first such payload for this target key/slot, not first upstream mate value in the entire search. |
| Last accepted writer before the endpoint probe | 491 / 490 | Frame **25044**, ply 9, entry depth 9: admitted raw **−31982**, **BoundUpper**, depth 9, clock 9. No accepted target write intervenes before the consumer. |
| Endpoint probe | 497 / 496 | Qsearch frame **25109**, ply 15, reads this depth-9 payload and converts raw −31982 to −31967. The preceding physical slot snapshot is sequence 495. |
| Endpoint substitution | 498 / 497 | The existing static evaluation −440 is replaced by the TT upper-bound score −31967. |
| Endpoint store and return | 501–502 / 500–501 | Attempted depth-0 BoundUpper store is rejected, preserving the depth-9 payload; the actual return is **QS_FINAL −31967**, PV length 0. This is a final qsearch return, not the early QS_TT return. |

The endpoint FEN is `8/8/8/8/8/5R2/1k1K4/8 b - - 15 8`. Writer frames 23225 and 25044 have the same board with clock 9. Their recorded histories contain respectively 10/10 unique keys; the endpoint has 16/16. None of these three recorded ancestry chains contains a null move or same-ply ancestor. Intermediate accepted writes include engine-classified BoundExact entries; the first-pass evidence does not independently prove those classifications or the full upstream search derivation.

Across **196 captured cluster snapshots**, there are zero duplicate target-tag slots and zero other occupied slots. This rules out an observed duplicate/shadow slot in this captured target-cluster history. It does not rule out duplicates in other clusters, other runs, or unobserved history, and it does not generally validate a 32-bit TT tag against collisions.

## Instrumentation and generation

The callbacks themselves do **not** probe the TT or change TT generation. `origin_trace.hpp:145–180` reads a `const TTCluster&`; generation and epoch are copied values. Its callbacks serialize fields. `worker_probe` consumes the existing entry, and `result` returns the original numeric result. `Frame` uses debug-only IDs/TLS and reads const board, stack, and node data. The additional `cluster_for` use only computes a cluster index (`include/forge/search.hpp:199–205`).

The original probe's generation-refresh assignment remains at scratch `search-origin.cpp:312–314` (pinned `src/search.cpp:299–301`). PROBE_BEFORE/AFTER surround this original operation; they do not create an additional refresh. Store admission remains the original predicate at scratch lines 365–372; the added `origin_admitted` flag records whether that body ran. Hooks use the existing locked/exclusive-owned access route. No engine layout or generation assignment was added by the retained diff. The fixture uses the owned single-thread route, so this does not certify SMP instrumentation behavior.

The endpoint path is directly supported by scratch lines 1107–1116 (conversion and early-cutoff conditions), 1129–1133 (TT score substitution), and 1202–1210 (store classification and QS_FINAL return). Bound codes are defined as Upper=1, Lower=2, Exact=3 in `include/forge/search.hpp:75`. The endpoint is a PV-width call; its emitted QS_FINAL record resolves the return site without inferring it merely from the short PV.

## Score meaning and limits

Previously retained independent KRK analysis gives this root DTM 15, chosen `b3f3` DTM 17, and the endpoint board DTM 6. The UCI line prints `mate 17` with **no bound qualifier**: it represents 33 plies, and it must not be called an engine-certified exact mate 17 or advertised upper/lower bound. For this oracle-checked root, it is consistent with the weaker analytical statement that the chosen move can force mate within 33 plies.

At the losing endpoint, exact six-ply remaining mate would be root-relative `−32000 + 15 + 6 = −31979`. The consumed numeric **upper** score bound −31967 is weaker: −31979 ≤ −31967. Equivalently, the position-relative exact value −31994 is at most stored −31982. Negating back to the winning side reverses the score inequality and yields a lower score bound, hence an upper mating-distance deadline. Numeric upper-score bound, upper distance bound, and exact DTM are different claims. The raw payload therefore does not demonstrate a false mating deadline for this position. The first-pass trace also does not prove the soundness of every producer classification or a universal rule for other positions.

The oracle is independently retrograded relative to the selective alpha-beta search, but shares Forge board/attack primitives; it is not an external tablebase. This fresh, short KRK case and its recorded nonrepeating paths do not validate all rule-50/repetition contexts. A short nonterminal PV alone remains insufficient evidence of an incorrect mating deadline.

## Evidence identity and review scope

- Pinned search SHA256: `2b14b62cd675b047478e70b738932ce4c2c699239b3c0de4ec43551464dc8819`.
- Scratch first-pass search: `610d5fc54034d199c938f35ee9544f0aa7be8207f6b4ba9e35b54261a9588cd6`.
- First-pass helper: `32deefc0e3ff8c0f2234c3e556a7c4ac1ef2ded54dbe22b8e75780325402dd5e`.
- Instrumentation diff: `4a59f673078dfebcb9eca8ada7d42313f70ad32055756d5f09aff4def797aaf2`.
- Raw trace-r1 stderr: `14dbd923dc8fd20e7dc1bb54a2201ed3b7473e53070a6f7351a34b65ebee633a`.
- Baseline executable: `e2788a101d11acfca637b14471e2b067ae11e551500cfb0656019a193ec2cb3e`; first-pass executable: `c76fde7dee0cc63a2f22b27b040f3bc4c57a3176da3ff19ee04ca331761e82c9`.

The source directory's preparation README still describes the earlier uncompiled/zero-run preparation stage. Its historical status does not override the later successful `native-logs/00–08` and `runs/` records. Those records identify x86-64-v4 compiler flags. My local evidence includes the complete helper/diff reads, independent event ledger, exact command/output records, source indices, history checks, and supplied run summaries. An exploratory lookup used the wrong header path (`include/search.hpp`) and its real `rg` error is retained; the subsequent `rg --files` lookup found and read `include/forge/search.hpp`. This was a review-command error, not an engine failure.
