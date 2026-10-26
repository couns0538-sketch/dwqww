# S13 prior-prefetch overlap addendum — 2026-10-26

This additive provenance note leaves the sealed S13 packet, patch and manifest unchanged. S13 patch SHA256 remains `cc3efc9659a00e2b2da8c4853f7c1c2f601e95e16e1805bc2cbf8cc4b91a249a`; manifest remains `5808d53eab5c1ae141e7d3cf7fa16c0a7aa8a92104ef69e34870d5cb3168f0fe`. It adds no native result or adoption claim.

S14 recon located explicit earlier overlap in `/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files/10_cr/CR_PASS_fc_speedtt_h256e12.txt`. The exact CR-note SHA256 is `a3f93de4a3d279f30c389d9323a6fcc5f2e053ba87cb30500f89169306c3c66e` (6173bytes). It reports the older unmerged `fc_speedtt_h256e12` patch SHA256 `e310d6a622b0ac06eccbd0750490107597d62067c76daf9efff55faee99081c2`; those patch bytes were not present in the targeted supplied candidate paths and were not independently verified by this recon. The note's historical build/test claims remain attributed historical evidence.

|Variant|Source scope|
|---|---|
|Actual supplied h256 baseline|Existing post-make prefetch on main/qsearch only; null and ProbCut entry paths have none. TTCluster64 assertion already exists.|
|Older CR-reviewed speedtt candidate|Early approximate child-key/null-key hints before make on main/qsearch/ProbCut/null; exact-key fallback, plus probe/store address prefetch before stripe locking. It changes board.hpp, search.hpp, board.cpp and search.cpp. Its review reports an unchanged UCI list.|
|New S13 prepared variant|Retains the baseline's two existing exact-key sites. Adds only exact post-make null/ProbCut requests, guarded by an OFF build switch and OFF UCI option with atomic requested/worker snapshot plumbing. No hint arithmetic, board-key API, probe/store or TT-layout change.|

S13 is an independently written, narrower variant in this **existing idea family**, not the first discovery of null/ProbCut prefetch. Older unmerged code is not the same as code already applied to the baseline. Do not transplant old speedtt's reported node/sanitizer results onto S13: S13 native gates are still UNVERIFIED. Do not stack both variants automatically; they overlap at null/ProbCut and would duplicate work. S29 should select one explicitly tested survivor, with its own source identities and measurements, or retain neither.

No code from the older engine candidate was copied during S13 implementation; the overlap was identified later by reading the historical CR note. The original S13 idea/source attribution remains intact; this note records the newly recovered provenance context honestly.
