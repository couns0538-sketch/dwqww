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

The Windows Zen5 research comparison package passes **15 regression groups**
and **10,000-position exact C++ parity under Wine**. A fresh repeat binds
the actual PE, probe, core, sources and tools before/after execution. Windows
bench repeats the shipped Windows **334,752-node** signature; Linux
292,545 is a separate compiler/platform signature. Strict arithmetic, imports
and actual NNUE SIMD code pass inspection. The package includes the exact
accepted Windows baseline and a raw-evidence comparison helper. Its process-wall
diagnostic cannot automatically accept the existing internal bench-NPS gate;
the original misleading label/draft and corrected unit tests are preserved.

**Native Windows/Ryzen speed, ≤5% overhead and Elo remain unproven.**
This is an explicitly experimental comparison artifact, not an accepted release.
The accepted engine remains unchanged. No matches ran. Next: measure the
unchanged bench-NPS gate on stable target hardware, then preregister any
future bucket training and apply the user PC game gate. `WINDOWS-EVIDENCE.zip`
and the manifest retain the original proof and every artifact checksum.
