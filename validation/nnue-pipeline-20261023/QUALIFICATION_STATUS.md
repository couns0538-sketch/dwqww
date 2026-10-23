# Frozen NNUE trial qualification — 2026-10-23

Source: clean net-only6e9622fd5be18e0155fc3ed5fcf6c4586705cca6 off1ab50b2d.
Only `src/nnue_weights.inc` changes. Pipeline branch keeps the shipped net.

| Gate | Verified result |
| --- | --- |
| Main trainer/data/tool suite | 86 passed; original failures retained |
| Post-commit default CTest/bench | 14 passed /292545; engine/core unchanged |
| Full zero/warm training | 20+20 epochs closed0;1M train /4149 selection |
| Original selection loss | Candidate0.006025381045, shipped0.006082049056, HCE0.006660536216 |
| Independent frozen audit | 8881 positions/109 games; candidate0.005991080029, shipped0.005970920200, HCE0.006741170688 |
| Independent relative loss | 11.127% below HCE (95%CI5.858..16.472%); vs shipped -0.338% improvement (95%CI-5.783..+4.286%) |
| Final actual native NNUE parity | 2048 exact scores;0 feature mismatches |
| Original C++ loader API | 394756 bytes and98689 quantized parameters roundtrip exact |
| Windows Zen5/Wine | Original14 checks passed;2048 exact parity; bench378596 repeated |
| Original Linux Release/ASan | Each13/14; fragile NMP coverage assertion only; no sanitizer diagnostics |
| Corrected Linux Release/ASan | Running in fresh output/source paths; no PASS claimed |
| Test-only fixture repair | f4a1ed6; old/new real cores pass; NMP-disabled negative control fails |
| Equal-time games/Elo | 0 / not measured; QA owns1000-game gate |

The independent audit was evaluated once after public freeze. It does not select
another model. Candidate is not a demonstrated shipped-net improvement. Default
net and accepted integration are retained. Teacher is Forge's own5000-node search,
not an independent strength oracle. Legacy game IDs are unknown; exact-position
exclusion does not certify legacy game-level independence. Windows tests use Wine,
not physical Ryzen execution. Bench node counts show repeatability, not NPS gain.

Original per-row losses/whole-game intervals are in
`full-selected-original-report-attempt1/` and
`independent-audit-frozen-zeroep3-report-attempt1/`; the latter controller's
`INTERPRETATION.md` states the independent freeze contract. Raw Windows evidence
is recoverable from the release ZIP plus `windows-final-net-trial-recovery-index/`.
