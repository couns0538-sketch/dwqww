# Windows 6.4.15 pin-aware SEE candidate

Frozen source/tests: `8d303e4ca0428e9750bbf3e2663c64d9fafbd1ad`.
Parent source: `21538ec5416c909fc98a08688242a0b3b9710b25`.
The exact export contains 69 non-bytecode files; the three tracked .pyc files are excluded consistently with 6.4.14.
Only CMakeLists.txt, src/board.cpp, src/uci.cpp and tests/tests.cpp differ from the parent.
All NNUE/eval source/header/weight bytes are identical to the parent.

One-job strict static Zen5 Windows build succeeded. All eight Wine checks passed on the first attempt,
including permanent mirrored SEE regressions, TT eight groups, rule50, 18,947 legal-witness comparisons,
UCI, ponder, five OwnBook transitions and observed bench11 signature 382,424 nodes.
The signature is not an expected-parent parity result. No failed build or runtime attempt occurred.
Independent audit passed all 929 checks with no engine execution; final ZIP/tree/SHA256SUMS checks passed.

Artifact: `releases/forge-6.4.15-candidate-windows-zen5.zip` (10541371 bytes).
ZIP SHA256: `1eb3a128e4e905921e0440482076b0fd47bf0194e08a91eb099efe7fbce5df42`.
Exact tested PE SHA256: `9e5335f917decbdc9ef6ee76e71ec85d5ff7695d5078e90e76c3dac8498bc5dc`.
Static core SHA256: `98f3353add91681967a357048a302166d34a8cf852fcdc2b08f42b9cd3b83ed1`.
Raw original archive SHA256: `451a2a71b7da77136cce8041c5f4db463a4e0617811f0b4c192f8b46956652e3`; 158 originals retained.
All 190 parent Windows files remain byte-identical.

Full frozen source, all six built executables, core, original logs and build directories remain retained.
Source: `/workspace/.cloud-setup/forge-pin-see-windows-source`.
Build: `/workspace/.cloud-setup/forge-pin-see-windows-build`.
Raw snapshot and package logs are immutable; final audit and checkpoint evidence follows separately.
No performance, calibration or match was run. No NPS/Elo/native Windows/physical Ryzen claim is made.
The prior 6.4.14 native bench-output anomaly remains qualified in its separate evidence.
No live Windows build/test job remains. Native sanitizer evidence belongs to the parent task.
