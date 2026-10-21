# Forge 6.4.21 Windows qualification

Frozen source `2e151d019bc58dff2ab4e76e99ef99516af8d222`, parent `fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e`.
Nearest-pawn distance uses three radius queries and empty/singleton fallback to
reduce repeated scanning while preserving exact geometry. This stage establishes
bounded correctness and artifact identity; it measures no new 21 speed or Elo gain.

The first fresh strict LLVM-MinGW 23.1.3 Zen5 C++20 Release build passed, j1/static
with no FMA, fast-math or LTO. Ten actual built PEs, core, runtime/pawn/nearest test
objects, all 73 frozen source files, compile/configuration/flags and original
commands/streams/statuses are retained. The exact five-file delta preserves Board,
NNUE source/weights, search, parameters and all older tests.

All 12 Wine checks passed first attempt: 791680 nearest comparisons across 395840
sets with six compiled constexpr assertions; 37320 pawn-span checks/three constexpr
assertions; 347 runtime PSQT; 54 correction-history; 8 TT groups; rule50; 18947 legal
comparisons; UCI/ponder; 5 OwnBook transitions; and exact preregistered 352313-node
parent signature. Runtime inputs stayed unchanged. AVX2 min/max/multiply/add and
absence of fused operations were verified. The original JSON field is
`nearest_pawn_sets`; root may derive `nearest_target_sets` without modifying it.

Closed-writer packaging and the first independent read-only audit passed all 1615
checks. Actual inventories: 22 distribution members, 21 complete checksum entries,
229 original raw files/230 raw ZIP members, 10 built/nine shipped PEs, and 521
protected parent 20 files unchanged. Both source/proof identity pins and all three
object/source/testedPE/compile identities were verified. All consumed proof hashes
and raw per-file hashes are retained in AUTHORIZATION-PROOFS-REHASH.json and
windows-originals-SHA256.json. Original source/prod/test maps are separate.
No failure, retry, waiver, source edit or Git mutation occurred. No root verifier
was run on root's behalf. Prepared-stage notes remain historical snapshots.

Artifact: `releases/forge-6.4.21-candidate-windows-zen5.zip` (15,445,676 bytes).
ZIP SHA256: `e2af16d497f5c1560d413d601c3af50e364c3dfa30e3a17d49936812ac712227`.
Engine SHA256: `cffc884ebedcce85b3636160b8ed9b74450f99122a185481206fd53729916aa9`.
Core SHA256: `436ada00a2c53a66edc381695c93d6cd42034bf0b8c58fbe5c95e80aa9128f39`.
Raw SHA256: `0eb2bb2b85255110e4793702d635e552e146a04179d5c27760c539419c6a5aff`.
Runtime object SHA256: `fd6e686a6b018e2d1793f77fa82bd36d3b42c369ecb4191059062590fcbd6ec2`.
Pawn object SHA256: `214deb1fec8735bba47ce187270e3b4f5fac6444048c07fcf6b08347f4898a41`.
Nearest object SHA256: `f5e026b5e073d186a36b8f4dc395e29f83841769d3ff67a1d73598f3b4f0bbb9`.

All build/runtime/package/audit CPU/hash/decompression work finished at
00:23:01.454419 UTC. No corresponding job remains active. Frozen original files,
raw archive, expanded bundle and release ZIP remain untouched after audit; only
this final checkpoint was added. Root retains separate archive snapshot clearance.

This is a qualified candidate, not an Elo-accepted release. Native 21 qualification
is separate; original 6.4.16 TSan FAILED 8/9 remains qualified. No new 21 speed/NPS,
playing-strength gain, native Windows/physical Ryzen test or Stockfish superiority
is established. Parent 20 performance does not validate 21. Next: root proof/captures,
archive/preserve/push, then separately calibrated speed and equal-clock strength tests.
