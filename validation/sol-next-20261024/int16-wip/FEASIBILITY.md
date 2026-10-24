# H256 int16 feasibility, 2026-10-24

Status: **feasible arithmetic design; no implementation, build, engine execution, measured parity, speed or Elo result**. This report is read-only analysis of the user's Forge source. Production/index ownership remains with the root agent.

## Inputs and scope

- Read `handoff/SOL_PROMPT_next.md`, `REVIEW_3afd230_QA.md`, `CR_PASS_int16_ep10.txt`, `FORGE_IDEA_BOARD_P22_P23.md`, repository `AGENTS.md` and SIMD-validation instructions.
- Current H256 `src/nnue_weights.inc`: MD5 `6d22f612c855e17c62d396d32da99ea4`, SHA256 `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`.
- Supplied user-owned archive: SHA256 `aa9558c29d6617a3976065682d69ada3cbb95dfabff8992b8a15babf817a8b33`; 9 regular members, 62,707 uncompressed bytes. All names/types/sizes were validated before extraction: no absolute paths, `..`, backslashes, symlinks, special files, overwrites, or excessive expansion. Manifest is `archive-manifest.json`.
- Extraction is confined to this review directory. No other engine source was consulted or copied. No network/trainer change is needed.

## Exact H256 number format and bounds

The lock stores `w1`, `b1`, `w2`, `b2` as int16 and divides by 4096; `SigmoidK=2.25`. Preserve both scales and the existing clipping interval [0,1]. The float output uses 16 partial sums in index-modulo-16 order, followed by its ordered scalar tail; AVX-512 and OFF implement that same association.

Let `A` be an integer accumulator and `a=clamp(A,0,4096)`. Reuse the supplied Forge path's `x=a*4` and `q=round(x*x/32768)=round(a*a/2048)`; `q` is in [0,8192]. Then `T=sum(q*w2)`, `out=T/2^25+b2/4096`, and `cp=out*400/2.25`, clamped and truncated toward zero.

Static parsing of the exact lock weights gives:

| Quantity | Bound/value |
| --- | ---: |
| Maximum absolute w1 | 10,323 |
| Maximum absolute b1 | 4,597 |
| `max_h(abs(b1[h])+sum_f abs(w1[f,h]))` | 1,635,680 (lane 47) |
| That bound plus four maximum dirty-column magnitudes | 1,676,972 |
| w2 min / max | -14,727 / +13,650 |
| Positive / negative-magnitude w2 sums | 306,448 / 268,352 |
| Sum absolute w2 | 574,800 |
| b2 | 110 |
| Positive output bound | 2,510,422,016 |
| Negative-magnitude output bound | 2,198,339,584 |
| Maximum actual packed two-product absolute bound | 124,551,168 |
| Maximum signed bound of any complete 16-hidden group, both perspectives | 247,578,624 |
| Maximum signed bound in any combined eight-lane AVX2 accumulator | 518,799,360 |

Both final signed output extremes exceed int32. Merely removing the constructor abort, changing `total` to int64 after the old int32 horizontal reduction, or widening a wrapped horizontal result is incorrect. The current individual SIMD lanes are safe for this exact net; the horizontal int32 reduction is not.

The accumulator and all normal dirty intermediates fit int32 **and** the float exact-integer range below 2^24. Every original weight is an exact multiple of 1/4096. Thus the integer accumulator can reproduce the lock's accumulator exactly, including its intermediate additions/subtractions, for actual Board inputs and the supported dirty transitions. Arbitrary synthetic float accumulators outside that grid are a different contract.

## Recommended original redesign

1. Keep int16 stored weights and int32 accumulators. Keep `Qa=4096`, squared scale 8192, and the supplied Forge lane permutation; these follow from the user's weights and documented pack instructions.
2. For each 16-hidden group, form the two `madd_epi16` vectors and combine their corresponding int32 lanes. **Sign-extend this group into int64 before accumulating across groups.** Finish in int64, including the scalar fallback. No int32 horizontal sum of the full network is permitted.
3. This group widening also has a simple type-level bound independent of the current w2 values: one madd pair is at most `2*8192*32768=536870912` in magnitude; combining ours and theirs is at most `1073741824`, safely int32. Accumulating the resulting signed64 values handles H256 comfortably. The SIMD signed `-32768 * -32768` exceptional overflow case cannot occur because the activation operand is nonnegative and at most 8192.
4. A smaller lock-specific alternative is to retain the existing safe eight-lane accumulation, store eight int32 lanes, and add each as int64. This requires retaining/checking the actual per-lane signed bounds when changing nets. Group widening is easier to audit for future nets.
5. Do not lower the squared scale to 4096 to force an int32 total: that doubles the square-rounding error bound to about 3.05 cp and needlessly sacrifices the present error margin. Do not remove overflow checks.

No new AVX-512 integer kernel is necessary to fix this arithmetic. The provided AVX2 int16 instructions are valid on the target Zen5, while the current `FORGE_AVX512` / `FORGE_NNUE_ALIGN64` float paths can remain intact. Preserve `-ffp-contract=off -fno-fast-math` and inspect the actual emitted functions later.

## Runtime OFF default and fallback

The supplied H128 implementation is a compile-time replacement of `Accumulator` and the inference functions. That alone does **not** implement the requested runtime option or fallback.

- Add `option name NnueInt16 type check default false`; route refresh/update/evaluate consistently by the accepted runtime mode. Preserve the existing float algorithms with it OFF.
- The simplest safe first implementation uses distinct float and int32 accumulator storage; it increases stack memory by 2,048 bytes per H256 accumulator, or 278,528 bytes across the existing 136 SearchStack entries per worker. That is a performance tradeoff to measure, not a correctness blocker. An overlapping union can avoid the footprint but adds lifetime/tagging complexity and should not be rushed to save this small amount of memory. Reinterpreting the float array as int32 violates the required C++ object/aliasing discipline.
- `setoption` already stops/joins search before handling options. Accept/reject the mode there, clear the TT as `UseNNUE` already does, and begin the next search with fresh accumulator state; search initialization already invalidates every accumulator and refreshes the root. Never switch representation during a search or silently fall back inside evaluate after an integer refresh.
- Make representability inspection return a status/reason, without `abort`, exceptions for representability failures, or printing before `main`. On an invalid request, emit an `info string` and leave the effective mode float. Retain a scalar int64 path on builds without AVX2.
- Validate scale, architecture/group divisibility, accumulator/transient bounds and every chosen SIMD intermediate bound before enabling. If exact accumulator equivalence is part of the contract, also require its 2^24 float-exact bound. Do not make an int32-final-total check reject a design that uses int64 there.

## Error expectation and analytical ceiling

Square rounding changes each q by at most 0.5. Consequently the exact-real centipawn error is at most:

`0.5 * 574800 / 2^25 * 400 / 2.25 = 1.522699991862 cp`.

On grid accumulators, the initial float square is exact: its integer numerator is at most 4096^2=2^24. Conservatively allowing 36 float roundings along a term's path (weighted product, paired term, 16 lane additions, 16 tail additions and two cp scaling operations), with `u=2^-24` and `gamma36=36*u/(1-36*u)`, bounds float-reference rounding by:

`gamma36 * ((574800+110)/4096) * 400/2.25 = 0.053542781028 cp`.

The integer path's double tail adds negligible error. Combined real difference is below 1.57625 cp. Clamping is nonexpansive and integer truncation therefore gives **at most 2 cp** final network/residual difference under these assumptions. This is an analytical bound, not the required 100k-FEN parity measurement. It predicts that the fixed max<=30 and mean<=2 gates should be readily feasible.

For scale only, an independent uniform square-rounding model with every output active gives RMS 0.06677 cp and mean absolute real error about 0.0533 cp; integer truncation usually produces a similar order of mean absolute integer error when fractional parts are well spread. Actual clipped activations are correlated with the weights, so this is **not** a measured or guaranteed mean. A plausible measured outcome is mean in hundredths of a cp, most differences zero, and max 1–2 cp. Do not report those as parity numbers.

Strict sign flips of the raw NNUE correction are precluded by the <2 real-cp difference bound, because opposite nonzero truncated integers require at least 2 real cp separation. Full static residual+handcrafted sign flips are a different statistic and must be measured: adding the same integer handcrafted score can move a two-cp integer difference across zero. Report both definitions clearly, plus zero-vs-nonzero cases if convenient.

## Work gate and remaining verification

The arithmetic abort fix is small enough for the one-hour budget. Runtime integration, oracle updates, and required evidence are the larger risk. Start implementation only after root completes buffer work then the PowerShell task, and only while at least 1.5 hours remain. If measured parity numbers do not exist by **17:11:09 UTC**, stop int16 and take authorized P22; hard new-code stop is **17:46:09 UTC**. No partially verified int16 candidate should be handed off.

After implementation, root must still run the d11 all-OFF precondition before any other test of each build, all five OFF lock benches, 100k+ FEN max/mean/p99 and sign counts, incremental/refresh oracle comparisons, scalar/SIMD equality, d13/d16 ON nodes, a stated depth13 bestmove subset, paired WAC300, ON ASan/UBSan bench, full required ctest with exact FAIL lines, FMA=0 in actual `forge::nnue` functions, the SIMD checker, runtime UCI/fallback smoke, and the paired timing protocol. The inherited checker only gates lane consistency in several modes, so the new 100k corpus must explicitly fail on the fixed mean/max limits. The existing `lanes` mode's H128 <=1 cp gate must be parameterized to the H256 <=2 analytic ceiling rather than mistaken for a regression.

No search-strength, NPS, Elo, or candidate-acceptance claim follows from this report. Any eventual immutable patch is against `f4911f2` with `-p1`, owned by root, and must preserve the prior AVX-512/alignment switches.
