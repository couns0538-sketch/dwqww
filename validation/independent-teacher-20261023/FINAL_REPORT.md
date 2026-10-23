# Independent-teacher pipeline — main result

Accepted engine remains **Forge 6.4.24**, source
`1ab50b2dd64d9b2f752f7f1285f6968cad2fd792`. No runtime algorithm, accepted
weight, test or integration-branch change was made. Pipeline parent `27070fe`
and failed attempts are preserved. No old training rows or matches were used.

## Data and training

The published, globally deduplicated corpus contains **5,988,335 positions**:

| Partition | Positions |
|---|---:|
| Training | 5,390,457 |
| Original validation | 295,653 |
| Frozen final audit | 302,225 |

Four fresh, game-identified collectors mixed Forge selfplay and both colors
against exact `5101c2529d386b7c3a04ba9156a69ee34df6bb43`. Whole-game partitions
were frozen before training. External **Stockfish 19 depth 3** supplied labels,
blended with **40% game result**. No external engine code, binary, network or
GPL text was copied. Protocol 8 fixes all settings and source identities.
Cross-shard exact-position removal excluded 47,554 duplicates.

Data commit **`442d5647612591a2d5a387c0513f5b482c07d6e8`** passed public
SHA256/size verification for all 27 files, 723,367,402 bytes. Its indexed,
immutable CI dependencies preserve all original inputs. Native dataset replay
currently requires canonical Linux `/workspace` paths. Trainer MIT notice and
checksum mismatch are fixed; all **56 checksum entries pass**.

Exactly **one eight-epoch warm start** completed in 1,459.119 seconds, with
input integrity passing. The preregistered earliest-minimum rule chose epoch 7:
validation blended MSE **0.03154945258561024**, shipped
**0.034083182956426566**. Independent closed-run review passed **178 checks**.

## Frozen final audit

The audit ran once, after numerical export/source/data freeze, on **302,225
positions from 10,781 represented games**. Shipped blended MSE was
**0.03453693078846838**; candidate **0.031588403018465105**: **8.5373% lower**.
The 10,000-draw whole-game bootstrap 95% interval for absolute reduction is
**[0.0025928813212714543, 0.0033175113598455327]**. Input integrity passed.
Teacher-only audit MSE was 0.017071947293679928 shipped versus
0.017036363991417138 candidate. Teacher-only *validation* MSE worsened;
selection was not changed after seeing either audit result.

Selected include SHA256:
`1ffd149bd0b88b0799e448553162945f6884402a9d855337325bc472f95cc03e`.

## Native gate and publication

Release compilation, **10,000-position C++ parity** (zero integer-CP or feature
mismatches), extended perft/UCI and 13 of 14 original CTest groups pass.
**The core group fails two depth-1 rook-underpromotion assertions.** The new
net chooses provably winning king moves but delays the shipped mate-in-2:
promotion-only search finds it at depth 3; unrestricted search by depth 12,
versus shipped depth 3. Tests and the native acceptance gate remain unchanged.

Benchmark: **338,337 nodes, 688 ms, 491,768 NPS**. The changed tree and single
run do not establish a speed improvement. The unchanged shipped benchmark is
292,545 nodes.

Exact weights are preserved only as an explicitly **RESEARCH** checkpoint,
commit **`2b3038f5f1ec61c72f580d4036fda3cda1af97c2`**. Its sole diff from accepted
6.4.24 is `src/nnue_weights.inc`. It is **not an accepted engine or Windows
release**; native acceptance remains blocked. The prepared Windows toolchain
and static wrappers were not used to publish a failing release.

The manifest indexes original data, audit losses, logs, commands, source/binary
hashes, failed tests and semantic proofs in compact archives. Existing skill
was improved without duplication or a global-installation claim. Next:
investigate the evaluation/selectivity interaction behind delayed mate discovery,
then apply the user's PC game gate. **Elo and playing-strength gains are unproven;
zero matches were run.**

## Optional eight-output candidate

The separate experimental branch now contains eight piece-count heads, a QAT
trainer/exporter and regression tests. All heads duplicate the **shipped** net;
this is not the learned epoch-7 candidate. Linux Release **15/15** and separate
**ASan/UBSan 15/15** pass; two 10,000-position C++ parity runs match exactly,
including a distinct-head control. The Windows comparison package passes
**15 regression groups and 10,000-position exact parity under Wine**. Native
Windows/Ryzen testing is pending. Both original 20-pair VM speed studies are
inconclusive, so the ≤5% overhead gate remains **unproven**. Source, original
raw evidence, exact baseline executable and a target-PC comparison helper are
published at `bde3dc9d38c270d6c93193f04660b728e866ef13`. The manifest links every artifact.
No accepted-engine change, matches or Elo claim resulted.
