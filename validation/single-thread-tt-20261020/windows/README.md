Frozen Forge 6.4.12 Windows correctness evidence

Source and tests: `8865666cc0ab4961cd507bae40ff6ce44e9319df`.
Build: LLVM-MinGW 23.1.3, C++20 Release, znver5, strict float and static linking, two jobs.
All eight Wine checks passed: core/reference perft, coherent TT (eight groups), rule50,
legal witness (18,947 comparisons), UCI, ponder, OwnBook (five transitions), and
bench11 node signature 351,063. Output-layer SIMD and no-fused-arithmetic checks passed.

UCI go/bench explicitly request exclusive TT access, activated only for one worker.
A coarse gate and atomic request protect a sequential 1,024-stripe drain, followed by
table-bound owner TLS bypass; foreign entry calls retain synchronized access.
Default library callers and multiworker searches retain the shared stripe path.
Clear/resize/new_search/destruction still require every accessor to be quiescent.
This change does not alter NNUE, evaluation weights, search/replacement policy or
the rule50 heuristic. The unchanged NNUE/eval hashes are compared with frozen 6.4.11;
no new large snapshot differential was needed or run.

The originals directory retains every built Windows executable, the actual static core
and frozen build input tree. Runtime logs, exact commands, source/test manifests,
compiler/link records, disassembly and wrapper/OwnBook adapter provenance remain here.
windows-originals.zip and its per-file manifest preserve these bytes in the release.

Full candidate ASan/UBSan and TSan status is pending separately at packaging.
Wine establishes bounded correctness; speed, Elo, native Windows, physical Ryzen and
Stockfish superiority remain unproven. No timed trial or new NPS measurement was run.
