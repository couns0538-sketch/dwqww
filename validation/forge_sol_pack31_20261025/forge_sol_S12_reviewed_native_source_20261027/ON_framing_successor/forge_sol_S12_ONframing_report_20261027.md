# S12 ON framing successor — 2026-10-27

Independent review found a source observer defect in the original preparation:
the ON path passed required active+eight-stats prefixes to strict normal S25,
which correctly rejects any prefix before the terminal. The engine was never
run, so this was a source-preparation defect, not an observed engine regression.
The frozen original44-file packet and34 passing tool fixtures remain unchanged.

The pure RED control reproduces `bench_prefix_bytes` while the fixed-node gate
passes. Its raw stderr/stdout are retained. A separate minimal runner successor
uses a dedicated strict ON grammar. It verifies original closed-capture hashes,
all expected diagnostics, fixed terminal and EOF. It neither strips arbitrary
lines nor relaxes the normal OFF parser. It also checks the complete repeated
two-bench original stream after process closure.

The final tool-only audit patch is71 lines. GNU `-F0` application to a private copy
passed and exactly matches the standalone successor. It changes no engine
file. The original frozen packet manifest still verifies44/44.

27 new pure controls PASS, including the independent reviewer's exact synthetic
fixture (SHA256 `4f8fef2134c2de96f3e990de8fbe0655ea96240ba9a41bc2a1500bb098bb2479`),
all five fixed-depth frames, repeated active-once, unknown prefix/tail/blank
bytes, missing/reordered stats, overflow, wrong nodes, duplicate terminals,
truncated ending, open/incomplete capture, boolean rc, stderr and replaced raw
hash. A valid bare OFF terminal still passes unchanged S25 and cannot prove ON.
Parser-byte mutation and same-byte foreign module paths are also rejected.

The first42-line successor diff lacked an explicit source pin for its new parser.
Independent review required that closure before native work. The final runner
pins adjacent parser bytes before import, verifies the imported module path,
records expected/actual parser SHA in each runtime result, and verifies both
parser and runner source unchanged in postflight. The pre-closure diff/apply
logs remain saved as history, not as an executable candidate.

Independent source re-review: **PASS within inspected source scope; no remaining
demonstrated must-fix** in the exact parser/runner/tool-diff hashes recorded by
the reviewer. Review JSON SHA256:
`009d0cbb220d6713458eb0669e060e8148dea63a0843149a5dd20fc949a98b89`;
Markdown SHA256:
`6828bdc509abea912ea20700aec8a03edbc27c56e4982dda827c9dd70dd4c98c`.
Original review, baseline-binding/source-map checks, independent27-test log and
the original34-test replay logs are retained under `independent_review/`.
All C++/engine/native outcomes remain
**UNVERIFIED**. No compiler, engine or Git execution occurred. No speed/Elo claim.
The addendum supplies the two replacement bounded ON commands; every other
original preregistration step remains unchanged. Root reviews/publishes before
granting native work.
