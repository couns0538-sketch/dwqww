# Windows 6.4.16 pin-mask SEE candidate

Frozen source/tests: `553caef144ae2e1b696ba35d7a0eb1a50a03fde9`.
Parent source: `8d303e4ca0428e9750bbf3e2663c64d9fafbd1ad`.
The export contains 69 non-bytecode files, consistently excluding three tracked .pyc files.
Only CMakeLists.txt, src/board.cpp and src/uci.cpp differ from the parent.
Exact board SHA256: `239f1475fd48e9dba3babefe2399b22de5962f42e7a90a775271dbe49f6f6f31`.
Every test and header, plus all NNUE/eval source/weight bytes, match the parent.

One-job strict static LLVM-MinGW23.1.3 Zen5 Windows build succeeded without FMA/LTO/fast-math.
All eight Wine checks passed first attempt: core/perft including unchanged 23 mirrored SEE cases,
TT eight groups, rule50, 18,947 legal-witness comparisons, UCI, ponder, five OwnBook transitions,
and the REQUIRED exact parent15 bench11 signature 382,424 nodes. No expectation was relaxed.
Independent audit passed all 1,151 checks with no engine execution; final ZIP/tree/SHA256SUMS checks passed.
No failed build, runtime or audit attempt occurred.

Artifact: `releases/forge-6.4.16-candidate-windows-zen5.zip` (10560696 bytes).
ZIP SHA256: `b11c5a86b4b5dea3c42b9edc1c3787674b3c9f294e6de908cbe28f53c0e64b11`.
Exact tested PE SHA256: `60ab9a68a448276e3f1e499debbe91ae4603805bb37316729667eb6fd9efaa95`.
Static core SHA256: `1ae3cc354d801aee5af3740b52c805c95140c537b0756360ec556f660b39633f`.
Raw original archive SHA256: `11afa82386e94fe189ddd3a65345bcd26fe4b6f962281b2f236644115f8f98c7`; 158 originals retained.
All 408 preserved parent files (full15validation/archive, release and native/Windows source) remain identical.

Full frozen source, all six built PEs, core, logs and build directories remain retained.
Source: `/workspace/.cloud-setup/forge-pin-mask-windows-source`.
Build: `/workspace/.cloud-setup/forge-pin-mask-windows-build`.
Raw snapshot is immutable; final audit/checkpoint evidence follows separately.
Native gates are reported separately. This Windows stage does not accept the candidate or establish release readiness.
No performance, calibration or match ran. No NPS/Elo/native Windows/physical Ryzen claim is made.
Prior6.4.14 native bench-output anomaly remains qualified separately.
No live Windows build/test job remains. Complete16archive preparation awaits root's next scope/clearance instructions.
