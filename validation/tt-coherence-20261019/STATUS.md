# Checkpoint: actual-engine TT race reproduced

Work continues from published `842c02ef432f730d7083e3c22d36a5f3cc5d5184`,
with production source `f6f0a00b2f98a7a9f117790e2c8f19a340b6769f`.
The accepted branch remains `forge/6.4-hourly-20261019` at
`9108d012526be80c6d163f7cab684e6acd9abf8d`. No engine was reset or replaced.

Current context usage and maximum context window are not exposed to this
session. Neither value has been estimated.

## Build availability verified in this running environment

`build-tools-current.json` records actual version commands: GCC14.2.0,
GNU Make4.4.1, local CMake3.31.6, Windows LLVM-MinGW Clang23.1.3. A complete
fresh TSan-instrumented Forge and test executable build succeeded here.
These observations concern the running machine; editing an environment's
installation script does not by itself prove it ran in this instance.

## Saved failure and approaches

`baseline-and-proposals-checkpoint.zip` preserves source export hashes,
configure/build logs, startup check, actual four-thread race input/output and
original TSan report; fetched checkpoint provenance/research inventory; the
unvalidated snapshot proposal and review; the superseded store-time-reselection
approach and its explicitly superseded syntax logs. Its SHA256 is beside it.
Some external driver/test files were still being completed when this snapshot
was made; final integration evidence will be saved separately.

Actual engine settings were Threads4, Hash1, OwnBook=false, startpos and
`go nodes 200000`. TSan reported a worker write at search.cpp222 against another
worker read at search.cpp199, then halted with exit66 in 4.5445 seconds before
bestmove. This is the required failing control, not a completed search/match.

The user ZIP source and all previous validated candidates and failed match
attempts remain in prior commits. The fixed-node 6.4.1/original-ZIP SPRT ended
H0 after178 normal games; no equal-clock or Stockfish gain is accepted. The
6.4.2 underpromotion candidate is a correctness candidate only.

## Next actions

The coherent snapshot implementation and seven TT regression groups have now
been applied on this isolated branch as a **not-yet-validated 6.4.3 candidate**.
Both build directories are configured; compile/test results will be recorded
separately. Do not promote this source checkpoint based on compilation plans.

1. Finish the corrected Windows bundle's fresh Wine A/A readiness check and
   preserve both manifest-inventory attempts. No native Windows/Ryzen result
   exists yet; no timed Wine/VM pilots will be repeated.
2. Integrate opaque coherent TT snapshots, keeping probe-time replacement
   destinations and all accepted underpromotion/clock/SIMD changes.
3. Port regression tests; add correlated-tuple concurrent stress, immutable
   snapshots, delayed stores and invalid/lifecycle handle checks.
4. Run normal CTest, actual-engine TSan lifecycle searches, storage sanitizers,
   exact single-thread output/node parity and repeated Release overhead/scaling
   checks. Save all failures. Promote only with sufficient evidence.
5. Continue the next source-grounded experiment, maintaining the root ledger.

Original proposals, builds and live work are also retained under
`/workspace/.cloud-setup/tt-investigation`. A checkpoint does not imply an
ongoing process will survive disconnection or that automatic restarts exist.
