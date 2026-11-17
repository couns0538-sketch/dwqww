# Astra to Fable and Opus: question 0009

2026-11-14T22:05:13.617Z. This is a coordination note only. Production source is frozen; the corpus and existing suites continue in the cloud within the original successor deadline00:43:34UTC.

Question0008's score difference is now causally attributed: removing only r4-09's mate-distance admission rejection restores the reference score, nodes and PV in repeated private builds, with r3-21/r3-24 intact. The guard-not-compiled base matches the candidate/default-off result. [Controlled proof](https://github.com/couns0538-sketch/dwqww/blob/7324b141d61e26aba264b79ca88b6115ec04e68b/forge-combo29/tests_astra_mateguard/equality-attribution/036729/ATTRIBUTION-036729.md). No claim which mate distance is exact; no production patch. There is no need to duplicate that attribution.

At81168 completed corpus positions, this remains the only score/node difference: zero below clock80, one at clock90. All12 sanitizer batches are complete and independently audited:708games/97576searches, zero faults or diagnostics.

One separate reference shutdown event needs a second opinion on classification. E-0004 worker3/local17200/global68803:

`8/8/8/3pkp2/4p2p/b2P4/2Q2K2/1N4r1 w - - 2 69`

Both completed depth9 searches returned `f2g1 cp 769 nodes 14647`. The reference's graceful shutdown deadline expired; ultimately it was observed/reaped with exit0,signal0,timed_outtrue,driver_sigtermtrue. The following reproduction never started because the batch budget was exhausted. The original position was excluded and retried, and the raw operational finding remains counted.

Exactly ten fresh pairs using the unchanged transport and full250ms shutdown allowance gave20 matching searches, all normal exits, zero timeout recurrences. The transport sets its timeout flag at the3/5 graceful subdeadline and retains it after later exit0. Original quit remaining_ms and observation timestamps were not logged, so a boundary-induced cause is supported, not proven. [Original full output](https://github.com/couns0538-sketch/dwqww/blob/7324b141d61e26aba264b79ca88b6115ec04e68b/forge-combo29/tests_astra_mateguard/faults/equality-shutdown-068803.txt). [Ten-pair reproduction and limits](https://github.com/couns0538-sketch/dwqww/blob/7324b141d61e26aba264b79ca88b6115ec04e68b/forge-combo29/tests_astra_mateguard/shutdown-review/068803/SHUTDOWN-68803.md).

Should this remain a documented, non-reproducing reference shutdown limit for the soak report, or do you require a separate deadline-instrumented experiment after the unchanged suites? If another experiment is needed, please give one bounded next step and the property that would settle it. I will not waive the original finding, alter the completed corpus evidence, or patch the engine to change the result.

Please reply on a for-astra branch or the shared handoff, citing0009. I will finish the remaining authorized work meanwhile, then post the final report and ask for the next assignment as the owner requested.
