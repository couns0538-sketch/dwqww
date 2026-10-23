# Forge 6.4 NNUE pipeline — tested trial, no demonstrated Elo gain

The residual training pipeline now preserves the accepted 768→128×2 SCReLU architecture, HCE offset, side-to-move targets, quantized export compatibility, complete validation and every checkpoint. The supplied standalone-256 tooling conflicted with that contract; this finding does **not** establish the historical network’s training method or explain its past performance. Search code and the accepted default network remain unchanged. Optional evaluation buckets were deferred.

The fixed trial is clean source **`6e9622fd5be18e0155fc3ed5fcf6c4586705cca6`**, differing from baseline `1ab50b2d` only in weights. Network SHA256 is **`a52efa5f7864b04d0e8fceb3b14af4fc4970e0bb0a0a8706be0959b0bbb98df7`**; [FREEZE](full-trained-net-freeze-attempt1/FREEZE.json) SHA256 is **`3d945dc1f0e20d3469791eeb36b9ad5b23a1e70c87f6615703d0fda3442e211c`**. Selection and exact weights were publicly frozen before independent-audit losses.

All 13,500,000 legacy rows across nine files were examined. A declared reservoir plus fresh games produced **1,000,000 training rows: 985,105 legacy + 14,895 fresh**. Selection used 4,149 positions from 56 games. Independent audit used 8,881 positions from 109 represented games, with 111 assigned validation IDs; 18 exact-position overlaps were excluded and its 1,321-row train partition was never trained. Legacy game IDs/teacher provenance remain unknown. Generated outcomes include declared score/max-ply adjudication; these are search-teacher labels, not independently proven optimal play.

Both full 20-epoch jobs actually exited zero; all initial and epoch artifacts survive in the [zero](full-zero20-recovery-attempt1/ARCHIVE-MANIFEST.json) and [warm](full-warm20-recovery-attempt1/ARCHIVE-MANIFEST.json) recovery archives. The preregistered rule selected zero-initialized epoch 3 from 40 trained exports, using only the original selection set. CPU training used four threads, batch 1,024, Adam, cosine learning rate 0.001→0.00001 and result blend 0→0.1. Validation used fixed pure-teacher MSE rather than the changing mixed-target training loss. Fresh-only pilots showed training/held-out divergence; their unsuccessful runs and evidence remain preserved.

| Teacher-probability MSE | Selection: 4,149 | Independent audit: 8,881 |
| --- | ---: | ---: |
| HCE | 0.006660536216 | 0.006741170688 |
| Shipped HCE + residual | 0.006082049056 | 0.005970920200 |
| Frozen HCE + residual | 0.006025381045 | 0.005991080029 |

The [once-only audit](independent-audit-frozen-zeroep3-report-attempt1/REPORT.md) shows **11.127% lower loss than HCE**, 95% whole-game bootstrap interval **5.858%–16.472%**. Against shipped Forge, the candidate point is **0.338% worse**; improvement interval **−5.783% to +4.286%** includes zero. These use 2,000 paired game resamples, seed 20261023. No reselection or retraining followed. **Improvement over shipped Forge and Elo advancement are unproven.** The old default is retained.

[Actual C++ parity](final-net-native-parity-attempt1/parity/RESULT.json) passed 2,048/2,048 exact integer scores with zero feature mismatches. The [unchanged old loader API](legacy-loader-final-net-roundtrip-attempt1/RESULT.json) round-tripped all 394,756 float-binary bytes and 98,689 quantized parameters exactly; this does not claim unsupported CLI zero-epoch export.

[Windows trial evidence](windows-final-net-trial-recovery-index/RECOVERY-INDEX.json) records 14/14 checks through Wine/host tooling, another 2,048 exact scores, and repeated first-observed bench signature 378,596. The tested/delivered executable SHA256 is `2adc0429d238208ae9ae1a7788d6c570d9eb649b58c737bd8358d6004703518e`; package SHA256 is `276598f6ea45eae76cea7016052e00c37e54ccf5c709c48448c1e3aadbf5c3ca`. This is a Zen 5 Windows trial, not native Ryzen speed validation.

**Linux remains pending at this draft’s cutoff:** corrected qualification owner session **10660** is running. Original Release and separate ASan observation each passed 13/14, failing the fragile depth-eight null-pruning coverage assertion. The [test-only `f4a1ed6b` repair](null-pruning-controlled-test-repair-attempt1/REPORT.md) passed old/new-core checks and failed intentionally disabled NMP, preserving detection. It changes no production search. Full corrected Release/ASan closure must be reported separately.

Raw commands, original failures, game JSONL and provenance, per-row losses, source/binary hashes and archive readbacks are retained. The user’s independent crew owns the **1,000-game equal-time strength gate**. No Stockfish, speed or Elo superiority is claimed; native-runtime completion and actual matches remain the next gates.
