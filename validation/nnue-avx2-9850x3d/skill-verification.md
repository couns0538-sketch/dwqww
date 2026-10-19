# Reference skill verification

This is a reference skill. No behavior-shaping wording microbenchmark was needed.

- [x] Baseline retrieval scenario: Windows Ryzen target, SIMD semantic preservation, timing, strength and publication requirements; no new skill supplied.
- [x] Observed retrieval gap: the agent reported, “Neither a usable toolchain path nor a current Windows build recipe was established here,” and identified the missing differential harness. It correctly rejected unsupported Elo claims; no discipline failure is claimed.
- [x] Minimal reference added with a concrete differential driver, emitted-instruction control, explicit flags, target/platform distinctions, and links to tested build instructions.
- [x] Name/frontmatter/description: lowercase letters and hyphens; required name and description; description starts “Use when” and describes triggering situations.
- [x] Reference keywords cover SIMD, NNUE, Windows, UCI, floating-point, clocks and Elo. Main skill is approximately 450 words; detailed project evidence lives outside it.
- [x] Agent application test found all referenced tools and verified Windows build configuration.
- [x] Positive control: candidate Windows executable has 256-bit clamp/multiply/add, without fused output arithmetic.
- [x] Negative control: baseline SSE object fails the 256-bit instruction check.
- [x] Agent independently compared the pre-existing baseline/candidate snapshot files and hashes. This is an application test, not an independent regeneration of those files.
- [x] Application scenarios: faster/equivalent outputs without games do not establish Elo; Wine does not establish native Ryzen performance; limited Stockfish results do not establish unrestricted superiority.
- [x] Review gap corrected: example now includes `-fno-fast-math`. Detailed reproduction commands and pinned toolchain checksum are linked.
- [x] Tool review exposed a counterbalancing error in `benchmark_compare.py`; the real initial run demonstrates fixed order, and a corrected 11-run experiment demonstrates alternating order and equal search signatures.
- [x] No new rule-violation loopholes appeared; prohibition/rationalization tables are not applicable to this reference.
- [x] Skill, evidence and supporting tools are being preserved in the candidate branch. No unrelated upstream contribution is required.

An independent source review found no blocking candidate regressions. It explicitly limited the snapshot evidence to accumulator bits and integer outputs. No CodeRabbit or SonarQube review is claimed.
