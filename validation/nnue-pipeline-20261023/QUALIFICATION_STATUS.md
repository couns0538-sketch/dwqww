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
| Corrected Linux Release/ASan | 14/14 +14/14 passed; owner10660 actual exit0; clean6e engine +exact f4 test-only fixture |
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

Corrected Linux first genuine new-net bench11:348974 nodes; frozen-binary repeat
348974. Release engine SHA256
`da9667abf3416280c75b7a0f656bdb8500f53661ab40d6998f5af73900067aac`;
core `c324be9ffce9f10b1fa34ebd12b442bc9affb0174307f2d14da29ea32ccbf079`.
Both are byte-identical to original failed-harness Release production artifacts.
Corrected source manifest SHA256
`cc18289a6e1cbf21f133e83aef5019a9af4f3e68db62f70b5430c38bc3b5b575`
binds clean6e production plus only the exact f4 test file6dec8511. No sanitizer
diagnostic was reported. Combined original/corrected recovery archive and final independent artifact
review are complete. Root physically restored all1227 members/288455047 bytes
and verified every byte, mode and unchanged original.

Direct closed evidence:
[actual owner closure](linux-final-net-repaired-harness-run-attempt1/FINAL-CLOSED.json),
[all74 Git source comparisons](linux-final-net-repaired-harness-run-attempt1/SOURCE-COMMIT-CHECK.json),
[original runtime commands/streams](linux-final-net-repaired-harness-runtime-evidence/),
[original JUnit/LastTest files](linux-final-net-repaired-harness-ctest-originals/).
No new test execution was used to create these publication copies.

Recovery and final review:
[original failed plus corrected Linux archive](linux-native-qualification-recovery-attempt1/README.md)
(3 parts,78234274 bytes, SHA2564992b63e6bed99d60288c77b62f7ab7006819ab7160bf40895b229930de9479f),
[root physical recovery](root-linux-native-qualification-recovery-attempt1/RESULT.json),
[independent runtime/source review](linux-corrected-qualification-independent-review-attempt1/REPORT.md).
Both original failures stay13/14; both corrected profiles pass14/14. The default
post-commit proof is described in [POST_COMMIT_PROOF.md](POST_COMMIT_PROOF.md).
