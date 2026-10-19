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

### Completed validation checkpoint

Production source is `df5d839a6a03f705310bb958601375fa9411e810`.
The complete Release and TSan engine builds succeeded. All six Release CTest
suites pass, including core/perft, the TT checks, match tools, Windows validator
safety, UCI and pondering. Explicit GCC C++20 compilation/execution and Windows
Clang C++20 object compilation succeeded.

The original first TT stress fixture emitted 311 synthetic null moves in its
20,000-value publication range, violating its correlated-move premise because
same-key stores correctly preserve the previous move for Move::none. That failed
CTest run and source remain preserved. Only its generator was corrected; all
seven TT groups now pass normally and under TSan.

Actual instrumented Forge then completed two independent processes with 38
legality-checked searches and supported lifecycle changes, exit0, complete
stdout/stderr capture, no sanitizer report, and unchanged binary hash
`70ad38a30d6bb38f57bde68a49fd3280bddb4865b878e7d99b462f9f5ea2f163`.
The stream/event hashes were independently checked. These finite workloads are
evidence of the repair; they do not prove absence of all possible races.

ASan/UBSan compilation is in progress. Single-thread parity, comparative speed,
SMP scaling and equal-clock Elo are still pending; accepted branch is unchanged.

### Completed Linux correctness and parity gates

The separate ASan/UBSan configuration built successfully and passed all six
CTest suites. An additional actual-engine ASan/UBSan lifecycle process passed
11 legality-checked searches without a report. Cold/warm one-thread output
parity against the 6.4.2 parent passed for six positions on both repetitions;
both stdin bench11 signatures are419798. No source reset or accepted-branch
update occurred.

`complete-linux-correctness-checkpoint.zip` contains the original raw logs,
compiler/C++20 checks, drivers, failing approaches, complete TSan/ASan traces,
parity inputs/outputs and Windows compile provenance. Its adjacent JSON lists
every archived file hash. The Windows 6.4.3 build succeeded; runtime checks
are held until the performance window is complete.

Speed A/A calibration is currently running with the same 6.4.2 executable in
both slots, six counterbalanced blocks at1/2/4threads. No performance result is
available yet. All throughput work is separate from chess strength; equal-clock
native testing remains pending. Do not infer a running job from an old status
file without checking the actual process and final result.

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
