# Astra R9 final report — pending timing completion

Candidate c1 is correctness-verified; speed acceptance and QA handover remain
PENDING. Elo UNPROVEN. This report will be finalized after the registered timing
run and its independent review. No strength matches or gates were run.

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

## Timing — pending

Experiment 1 was inconclusive: A/A paired median +1.679% (IQR 3.354 percentage
points), candidate +1.632% (IQR 7.868 points), with 21/56 contaminated runs.
It provides no accepted speed claim. All raw evidence is retained.

Experiment 2 follows [TIMING_PROTOCOL_V2.md](TIMING_PROTOCOL_V2.md): fixed hashes,
one Idle engine core, longer warmup, telemetry-only whole-block replacement,
four eligible A/A blocks followed by ten eligible ABBA blocks (20 pairs).
Both quiet and all-attempt statistics will be reported. No speed result is accepted
until collection and independent review finish.

## Risks, limitations and remaining work

- Timing is ADVISORY; Engine QA owns official measurement. Host interference has
  rejected many blocks, so rejected and all-attempt results must accompany selection.
- Exactness evidence covers the supplied corpus, targeted state transitions and
  required search pins; it is not an exhaustive proof over all legal chess states.
- No integer quantization, cache, weight-layout or strength claim is made.
- LeakSanitizer was not enabled. ASan and UBSan were enabled and positively checked.
- gcov-dump was unavailable; its optional record-only arcs digest was omitted.
- Brief T4 smoke used the user's approved exception, confined to CPUs 2/3.
- Remaining: complete timing, independent final review, fresh packet audit, finalize
  ABBA tables and QA handover decision, push immutable evidence and final report.

QA handover: PENDING. Elo: UNPROVEN.
