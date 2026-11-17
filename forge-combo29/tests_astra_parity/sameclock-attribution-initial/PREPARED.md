# Same-clock source attribution

Read-only review preparation. No engines were run, no production source or Git was changed, and no root experiment state was written.

The first completed snapshot is `s2-0003/REPORT.md`. It reads finalized audit `S2-0003.txt` SHA256 `ad9decb73bb87086694e7eedd5b28fe7e88cc0d10457a7966b8edd247417655a`:48,209 positions,one high-clock difference,zero low-clock differences,zero partial difference observations. This is not full-corpus acceptance.

Actual index36729 /worker1/local9182 has FEN `8/8/2n2r2/3qN1k1/8/8/8/K7 w - - 90 141`. Its exact Step1 record is in `S1-0003/worker-1.jsonl`, SHA256 `21ad81947e6368420bef70655732fba6fb9301b58b949c882f63d2855a6cbbba`:the three-import candidate and frozen reference both returned a1b2,mate−6,2565143nodes at depth9. In Step2, the candidate returned a1b2,mate−5,2566746nodes while the same frozen reference retained the Step1 tuple. The original plus all ten fresh pairs have exactly those signatures. Full extracted transcripts and the original Step1 record are retained in this snapshot.

Source proof: c488e88f→d9a8587 changes only `include/forge/search.hpp`; an exact text check verifies that the entire header differs solely by moving the existing capped-clock declaration to the beginning of `score_usable` and adding `if(rule50_clock==capped)return true`. The mate/horizon body is unchanged. Its Boolean result can therefore differ only for an entry whose stored clock equals the capped read clock and whose mate distance the prior function refused. Such a return changes from false to true. Equal-clock ordinary entries and every cross-clock entry retain their former result.

Build proof: both release builds have byte-identical `flags.make`, `link.txt`, and `CMakeCXXCompiler.cmake`; GNU14.2.0, x86-64-v4, strict floating-point flags, same compile-time definitions and include paths. Both engine binaries, frozen reference and native comparator match their stage pins. The exact original100,000-position Step1 audit passed; each final difference is linked by both corpus index and full FEN to that audited baseline record.

This supports causal attribution of the stable difference to the sole same-clock source change under the recorded deterministic depth9 protocol. It is not a claim that the stored/read clock values of an actual TT entry were measured, nor a proof that either reported mate distance is chess-theoretically exact. No runtime TT-entry trace exists in this review.

Refresh on each later finalized cumulative audit, using a fresh immutable output label:

```text
timeout -k 2 120 node /workspace/work/parity-sameclock-attribution-preparation/review-corpus.mjs /workspace/work/parity-run/equality-final-v4/audits/S2-0007.txt final-s2-0007
```

Replace the example filename with the actual final audit. The helper writes only a new directory here, refuses overwrite, rechecks exact source/build/binary evidence, verifies artifact hashes, links every recorded difference to Step1, extracts its11 complete attempts, and lists any root clock under80. It does not alter attribution fields or mark the root completion gate passed. If the final audit reports new differences or partial observations, review them before acceptance; do not treat this first snapshot as a blanket waiver.

If the reviewer requires an observed entry rather than the narrow source proof, the minimum extra experiment would be one private diagnostic copy outside the production checkout: at the equal-clock early-return, record only the first case where the old mate-distance clause would return false (stored/read clocks, score, distance, depth, key and bound). Run the already-known FEN at the same depth9,T1 settings and require its complete move/score/node tuple to match the uninstrumented final binary. The pre-change frozen Step1 binary is already the control. Keep the diagnostic source diff, build commands and output separate from production/corpus counts; do not change expected values or the production branch. **This diagnostic is only a plan; it was not built or run.**

Actual snapshot invocation and result:

```text
timeout -k 2 120 node /workspace/work/parity-sameclock-attribution-preparation/review-corpus.mjs /workspace/work/parity-run/equality-final-v4/audits/S2-0003.txt s2-0003
{"out":"/workspace/work/parity-sameclock-attribution-preparation/s2-0003","positions":48209,"differences":1,"lowClockDifferences":0,"targetMet":false,"engineRuns":0,"rootStateWrites":0}
exit0
```

The helper also retained its exact read-only Git commands and their full real stdout/stderr in the snapshot. Tool source can be published as inert `.mjs.txt` text through the existing packager.
