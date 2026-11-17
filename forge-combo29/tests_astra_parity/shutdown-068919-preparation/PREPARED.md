# Reference cutoff 068919: ten fresh pairs

Prepared only. No engine, compiler, Git or root-state command ran. The actual retained pending record is pinned in DECLARATION.txt: original worker3/local17229, global68919, FEN5kq1/8/b2p2r1/1NP1p3/1P2PP1p/4NKnP/P7/R1B2Q1R b - - 3 47. Both initial searches returned g3f1 cp318 nodes12391. Reference total allowance8ms, graceful phase4ms, driverSIGTERM, observed reaped signal15 at5.197327ms. It is not an observed natural-exit overrun of8ms or250ms.

Run these sequentially between native corpus batches, using the exact unique logger labels:

```text
node /workspace/work/parity-run/command.mjs shutdown-068919-prepare node /workspace/work/parity-shutdown-068919-preparation/prepare.mjs
node /workspace/work/parity-run/command.mjs shutdown-068919-compile c++ -std=c++20 -O2 -pthread /workspace/work/parity-run/shutdown-review-068919/repeat-pairs.cpp -o /workspace/work/parity-run/shutdown-review-068919/repeat-pairs
node /workspace/work/parity-run/command.mjs shutdown-068919-ten-pairs /workspace/work/parity-run/shutdown-review-068919/repeat-pairs /workspace/work/parity-run/shutdown-review-068919 /workspace/work/parity-run/builds/step2-release/forge /workspace/work/r4-run/builds/guard-enabled/forge
node /workspace/work/parity-run/command.mjs shutdown-068919-finalize node /workspace/work/parity-shutdown-068919-preparation/finalize.mjs
```

The source is the previous015717 ten-pair driver with only its FEN replaced; measured transport header unchanged. Preparation refuses an existing runtime directory. Root's unique command logger prevents silently reusing prior run logs. Do not rerun the native binary into an existing transcript directory.

Finalization verifies source/header/engine/original pins and exact compile/run metadata; counts all20 result rows and actual shutdown/error statuses; preserves full20 transcripts and original pending output. It writes a new fault file `tests_astra_parity/faults/shutdown-reference-068919.txt`, a chunked raw package `tests_astra_parity/shutdown-review-068919`, and state.referenceShutdown068919. No corpus credit or continuation waiver is granted. Original equality evidence and active state are untouched. A new runtime finding remains in the result, rather than being asserted away.

Root state replacement checks its starting SHA256 after publication; wait for finalization before checkpoint writes. If that guard fires, immutable evidence remains and finalization can be retried. The reproducer itself has not been compiled or run during preparation. Both JavaScript files passed syntax checks; first native and finalizer integration remains root's step.
