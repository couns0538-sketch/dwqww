# Forge 6.4.24 — experimental eight-output buckets

This isolated branch adds eight output heads selected by total piece count to
the existing 768→128×2 SCReLU residual evaluator. Shared hidden arithmetic is
preserved. The committed weights duplicate the shipped output into every head;
**no new strength network was trained**. The learned epoch-7 research net from
the independent-teacher job is not used here.

The branch includes a bucketed QAT trainer/exporter, legacy include support,
a protocol template, a C++ probe and tests. The trainer requires a fresh protocol
binding its data, initialization and settings. Upstream provenance replay remains
required; a caller-pinned manifest alone does not independently replay raw games.

Release **15/15 CTests** and extended perft/UCI pass. Separate ASan/UBSan
**15/15** pass with leak detection disabled. Trainer tests **15/15** and parity
contract tests **4/4** pass. Two actual **10,000-position** C++ parity runs cover
all eight buckets and both sides to move, with zero integer-score or feature
mismatches. Replicated heads also match the original shipped probe. A distinct
head export verifies selection and detects a forced-head-zero control.

Speed is **inconclusive**. Both original timing studies and every sample are
preserved: 20 single-bench pairs give NPS ratio **0.84094**, 95% interval
**[0.60518,1.03684]**; 20 eight-bench pairs on CPU4 give **1.15723**, interval
**[0.93383,1.50629]**. Every benchmark repeats the shipped **292,545-node**
signature. Large scheduling stalls prevent verification of the ≤5% wall-NPS
overhead gate. The threshold has not been relaxed and no samples were dropped.

The manifest and `NATIVE-EVIDENCE.zip` preserve exact commands, source/binary
hashes, raw probe streams, sanitizer logs, RED/GREEN tests, reviews and all 88
original timing processes in reversible nested archives. Build with CMake Release;
`forge_nnue_probe` and `forge_nnue_bucket_tests` are ordinary build targets.
`FORGE_NNUE_WEIGHTS_FILE` supports an explicit diagnostic export and rejects a
missing path.

A Windows research comparison artifact is being built for the Ryzen 7 9850X3D.
It will require the original runtime checks and will retain the experimental
label. **The accepted engine is unchanged. No matches ran; Elo and strength gains
are unproven.** Next: verify the unchanged speed gate on stable target hardware,
then preregister any future bucket training and apply the user's PC game gate.
