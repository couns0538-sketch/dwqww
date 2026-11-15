# Two bounded TSan response-timeout diagnostics

These are fresh-process diagnostics of the two exact recorded positions and full move histories from question0018, indices4 (HindsightDepth/MateAlphaGuard false) and10 (both true). They cannot reproduce the original warm transposition-table/history state. They receive zero soak credit, cannot resolve a fault automatically and never modify the old raw evidence, expectations, engine source, Git or global experiment state.

The measured UCI transport is copied byte-for-byte from the frozen SMP harness. Each child uses Threads2, Hash16, OwnBookfalse, UseNNUEtrue and MultiPV1. The helper verifies each full history with the frozen Board/bitboard oracle, checks that its resulting FEN exactly equals the trigger, and checks any returned move against that legal list. The setup budget is7seconds; the response budget is an absolute60seconds from `go depth 9`; normal shutdown gets the existing measured250ms transport allowance. The controller bounds the whole native command at75seconds plus2seconds kill grace and has a78-second parent bound.

The outcome is frozen before sending quit. A bestmove or depth9 line received only during shutdown never becomes a completed diagnostic search. Timeout is caught and recorded, then quit is sent. Raw stdin/stdout/stderr transcript prefixes, phase/received-line elapsed times, full shutdown timings and the final result remain in stdout. The controller retains exact argv, UTC start/end, process exit, raw stdout/stderr and hashes. A missing final result remains incomplete. Every sanitizer diagnostic remains in raw output and the read-only audit scan.

Preparation compiled only the new diagnostic helper, using the existing frozen oracle objects. Offline self-tests validated both exact histories and four synthetic completion cases, including timeout/late-result and bounded-score rejection. No engine process was launched. `compile.txt`, `selftest.txt`, `DECLARATION.txt`, `FINAL-VALIDATION.txt` and `FROZEN-PINS.txt` retain commands, outputs and identities. The TSan binary, all26 engine source/header/CMake pins, object pins and measured transport remain unchanged.

Root may run at most the two prepared cases, sequentially, once each. Root's diagnostic authorization is separate from the still-blocked soak state:

```text
node /workspace/work/parity-tsan-timeout-0018-diagnostic/control.mjs 4 --diagnostic-authorized
node /workspace/work/parity-tsan-timeout-0018-diagnostic/audit.mjs 4
node /workspace/work/parity-tsan-timeout-0018-diagnostic/control.mjs 10 --diagnostic-authorized
node /workspace/work/parity-tsan-timeout-0018-diagnostic/audit.mjs 10
```

Use the root command logger for exact command/output retention. Case10 requires finalized case4 metadata. An exclusive runtime lock prevents overlap; existing case directories cannot be reused. A stale lock fails closed and requires explicit recovery. Runtime output: `/workspace/work/parity-run/tsan-response-diagnostic-0018/case-4` and `case-10`. Neither success nor failure clears the global stop or credits any games/searches to soak totals.
