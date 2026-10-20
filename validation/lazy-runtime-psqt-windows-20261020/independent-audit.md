# Independent Windows 6.4.19 artifact audit

All **1184 checks passed** for frozen source `61f598056572dfade6994af8ad2e38817cd28aa3`; parent `fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b`.
The audit executed no engine and performed no rebuild.

The release ZIP has 20 verified members and 19 checksum
entries. Its expanded directory and every packaged byte match. The engine and
six test helpers match their Wine-tested binaries. All eight built PEs are AMD64
PE32+ with system/UCRT imports only; the static core and actual runtime PSQT test
object match their retained originals, source and compile-command identities.

All 71 exported files match frozen Git bytes. Seven reviewed
exports changed: CMake, eval/search source and headers, UCI version, and the new
runtime PSQT test. Board, NNUE source/headers/weights, evaluation parameters and
all earlier tests remain unchanged. The inherited residual correction is retained.
All 205 raw files match the original bytes, hashes and sizes; the
verified raw ZIP is embedded in the release. All 219 parent18 evidence
files remain unchanged, including original Wine line endings.

Original logs show ten Wine checks passed, including 54 correction-history and 347
runtime PSQT assertions, core/perft, TT8, rule50, 18,947 legal witnesses, UCI/ponder,
five OwnBook transitions and the preregistered 352,313-node parent18 signature.
The bench transcript and tested PE match the pre-package freeze. Strict Zen5
C++20 Release/static flags, AVX2 and no fused arithmetic agree with build records.

Release SHA256: `f0ec03308098bf8e675647f091b3b1afeb74d2632d9c972883e5907cfcb23d85`.
Engine SHA256: `265b676d6542622c5b876799236c2319fb91c8afa606a925087d36baf0b44caf`.
Raw evidence SHA256: `5ab2eb4a9c59e197037d4145576b85f8092295898e4af1c025a642367da674c8`.

This validates bounded Windows/Wine correctness and artifact provenance. The
private runtime cache intends exact evaluation/search parity; native19 gates and
differential evidence remain separate. This is an unaccepted candidate. Original
6.4.16 TSan FAILED 8/9 remains qualified. No speed, NPS, Elo, native Windows,
physical Ryzen or Stockfish superiority is established.
