# Astra R9 final report

Candidate c1 passes correctness and the registered advisory speed gate:
**+2.172299% median paired NPS**, IQR **1.100699 percentage points**, over ten
eligible ABBA blocks / twenty alternating pairs. Final independent packet and
artifact review PASS. Elo UNPROVEN. No strength matches or gates were run.

## Change and identity

Default-off UCI option `NNUEWideOutput` replaces two AVX2 output vectors with one
AVX-512 vector while preserving all 16 ordered float partial sums, their operation
order, and the final scalar reduction. Accumulator updates, network layout and
search are unchanged. Unaligned loads preserve the original alignment contract.

- Production source: `fb58080d23d871706662e91f092f918bb032d84c`.
- Lock SHA256: `FD3A51903E73DC1FA20263F1DCC7A4EEC506592E9F25E50B8F8739CA36873072`.
- Candidate b1 = b2 SHA256: `775EDEA1D476A3A18C64AF63F53C55D6E29A4571556AAD2666E87F18A6EF4284`.
- Build: untouched kit v2.3, `-Expose`, znver5, LTO+PGO; longest gcda path 83 characters.
- Network SHA256: `A7EBCF3A319675F347E6E8E3F2539901D38D8036CB9B5935F31DD43D084C9638`.
- Packaged executable: [forge_r9wide_775edea1.exe](bin/forge_r9wide_775edea1.exe),
  byte-identical to both tested production builds.

## Profile and selection

[PROFILE.md](PROFILE.md) records 24,112 samples of the actual lock before edits.
NNUE output arithmetic accounted for 4.380% of sampled main-thread IPs; quiet
accumulator SIMD updates accounted for 2.999%. Refresh had zero samples, so a
refresh cache was not supported by this workload. Integer/VNNI was deferred
because quantization and float rounding lacked an exact-equivalence proof.
These observations do not establish that those alternatives can never help.

## Correctness proof

| Check | Result |
|---|---|
| Two production builds | PASS: identical SHA256 above |
| OFF and ON bench d11/13/16/20/22 | PASS: 312866 / 862329 / 3024920 / 12389307 / 34048354 |
| OFF and ON perft 5, start/kiwipete | PASS: 4865609 / 193690690 |
| 12,000 legal crew FENs, diagnostic lock/candidate | PASS: 684,200 evaluations; digest 3bd3b27ac5a60483 |
| Raw float and accumulator checks | PASS: 16 lane bits, pre-conversion output bits, incremental versus refresh |
| Legal moves/nulls/long sequences | PASS: 324,100 moves, 12,000 nulls, seeded playouts and unmake |
| Actual production lock/OFF/ON corpus search | PASS: 12,000 identical score/node/bestmove records; all moves legal |
| T1/T4 movetime smoke | PASS: 24 legal bestmoves per mode, awaited before quit |
| Native ASan+UBSan short self-play | PASS: 8 games, 572 legal plies per mode; zero reports/illegal moves |
| Sanitizer positive controls | PASS: intended ASan and UBSan errors detected |
| Whole-executable FMA-family scan | PASS: zero hits |

[RESULTS.md](RESULTS.md), [BUILD_RECIPES.md](BUILD_RECIPES.md),
[REVIEW_LOG.md](REVIEW_LOG.md), source manifests and raw evidence identify each
binary and check. Diagnostic and sanitizer binaries are separate auxiliary builds;
only the two kit builds are production candidates. Auxiliary compile commands are
explicitly reconstructed provenance, not contemporaneous command logs.

## Advisory timing

Experiment 1 was inconclusive: A/A paired median +1.679% (IQR 3.354 percentage
points), candidate +1.632% (IQR 7.868 points), with 21/56 contaminated runs.
It provides no accepted speed claim. All raw evidence is retained.

Experiment 2 followed [TIMING_PROTOCOL_V2.md](TIMING_PROTOCOL_V2.md): fixed hashes,
one Idle engine core (CPU2; controller on its CPU3 SMT sibling), T1/Hash16, d20
warmup and d20 measurement, telemetry-only whole-block replacement. Every warmup
and timed run returned exactly 12,389,307 nodes. The fixed collection target was
four eligible A/A blocks followed by ten eligible ABBA blocks (20 pairs).

| Measurement | Median | IQR | Min–max |
|---|---:|---:|---:|
| Quiet lock NPS | 2,219,512 | 21,558.75 | 2,168,996–2,432,614 |
| Quiet candidate ON NPS | 2,268,064.5 | 30,164.75 | 2,224,292–2,475,880 |
| Quiet paired gain | +2.172299% | 1.100699 points | +0.307487%–+3.656076% |
| Quiet A/A paired bias | +0.626352% | 0.943615 points | −0.249782%–+2.261404% |
| All-attempt candidate paired gain | +1.518022% | 6.998095 points | −37.277015%–+86.798171% |

A/A passed its preregistered limits: absolute median <=0.75% and IQR <=3 points.
Collection retained 4/23 A/A blocks and 10/48 ABBA blocks; 34/92 A/A runs and
82/192 ABBA runs were contaminated. Whole rejected blocks remain in the packet.
The reported speed gate uses the median of twenty individual paired ratios,
not a ratio of arm medians. Quartiles use the inclusive method.

[TIMING_TABLES.md](TIMING_TABLES.md) contains every attempted block, eligibility,
four NPS values, both pair gains, and quiet/all-attempt distributions. High rejection
rates and nonzero A/A bias warrant official QA confirmation; this is ADVISORY.
Lightweight owned checkpoint/audit activity during collection is disclosed there.
Across all attempts, unpaired median NPS is **2,188,345 for the lock versus
2,160,675 for the candidate**: candidate is lower by this different summary.
This contrast with the paired median reinforces the limited robustness of the
interfered population; it is not hidden or used to change eligibility.

Independent M5 timing review recomputed all 284 runs, checked raw transcripts,
eligibility and binary/source attribution, and passed the preregistered advisory
criteria. The reviewer requested the all-attempt unpaired NPS disclosure above;
accepted and added. Focused final report/table/artifact review PASS: all 71 block
rows, reported statistics, links and QA attribution agree with the raw evidence.

Fresh packet audit04 passed all 1,226 checks. Source and tested binary hashes remain
unchanged since the earlier source review. See [REVIEW_LOG.md](REVIEW_LOG.md) for
review findings, fixes and validation attribution.

## Risks, limitations and remaining work

- Timing is ADVISORY; Engine QA owns official measurement. Host interference has
  rejected many blocks, so rejected and all-attempt results must accompany selection.
- Exactness evidence covers the supplied corpus, targeted state transitions and
  required search pins; it is not an exhaustive proof over all legal chess states.
- No integer quantization, cache, weight-layout or strength claim is made.
- LeakSanitizer was not enabled. ASan and UBSan were enabled and positively checked.
- gcov-dump was unavailable; its optional record-only arcs digest was omitted.
- Brief T4 smoke used the user's approved exception, confined to CPUs 2/3.
- Final safety/artifact audit PASS: D:\a9 used 1,083,662,553 bytes before final Git
  packaging; C: free 164,629,540,864 bytes and D: free 81,198,305,280 bytes. No owned
  engine/compiler process remained. Proof/artifact publication commit
  `f2b736f0117a658b29e530fcf80a391f31a996bd` was verified against remote HEAD.
- QA TODO: official independent timing of the supplied production executable with
  `NNUEWideOutput=true`; leave the option default-off pending crew disposition.

QA handover line:

`QA | source=fb58080d23d871706662e91f092f918bb032d84c | exe=D:\a9\src\astra_r9\bin\forge_r9wide_775edea1.exe | sha256=775EDEA1D476A3A18C64AF63F53C55D6E29A4571556AAD2666E87F18A6EF4284 | kit=v2.3 -Expose znver5 LTO+PGO | NNUEWideOutput=true | exactness=PASS | advisory paired median=+2.172299% | Elo=UNPROVEN`
