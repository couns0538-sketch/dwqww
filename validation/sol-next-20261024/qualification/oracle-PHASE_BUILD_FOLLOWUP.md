# Phase-probe follow-up

This follow-up preserves all prior oracle patches, source and metadata bytes.
`phase-build-commands.json` records the additional commands and prior identities.
`windows-engine-source-sha256.json` contains the original 19 frozen source files
plus the copied `src/uci.cpp`; `windows-uci-source-sha256.json` records the added
file separately. Original 19 files matched the repository before the copy.

The Linux phase probe linked the precondition-approved original H256 lock core.
`linux-phase-functional-result.json` records functional sanity only: every
successful invocation uses --iterations 1. It verifies JSON, the stdin start
gate, CRLF, stable checksum, and argument/EOF/wrong-command rejection. It does
not report a performance result or a whole-engine phase split.

Windows phase OFF/ON and matching engine build results will be recorded in
`phase-windows-exe-manifest.json`. Those helpers use the existing LLVM-MinGW
clang 23.1.3, strict floating point, H256 and -march=znver5, exactly as recorded.
They are not native g++15.2 runtime evidence. Rebuild companion producers with
an engine's exact compiler, source, network and options when qualifying that
engine. The matching Windows engine must first pass bench d11=308972 with all
behavior switches OFF before any Windows helper runtime test.

No Windows executable is run by this subtask. No speed or playing-strength
claim is supported by the functional checks.
